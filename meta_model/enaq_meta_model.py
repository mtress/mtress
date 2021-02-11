# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd

from oemof.solph import (Bus, EnergySystem, Flow, Sink, Source, Transformer,
                         Model, Investment, custom,
                         GenericStorage)

from .layered_heat import (HeatLayers, LayeredHeatPump, MultiLayerStorage,
                           HeatDemands)
from .physics import (HHV_WP, TC_CONCRETE, H2O_HEAT_FUSION, H2O_DENSITY)


class ENaQMetaModel:
    def __init__(self, **kwargs):
        """
        :param kwargs: parameters for the energy system, see example.py

        :return: Oemof energy system and model,
                 as well as a dict containing all used technology classes
        """

        # Unpack kwargs
        meteo = kwargs.get('meteorology')
        temps = kwargs.get('temperatures')
        energy_cost = kwargs.get('energy_cost')
        demand = kwargs.get('demand')

        bhp = kwargs.get('heat_pump')
        if bhp and bhp["electric_input"] <= 0:
            del bhp
            bhp = None
        shp = kwargs.get('near_surface_heat_source')
        if shp and shp["thermal_output"] <= 0:
            del shp
            shp = None
        ghp = kwargs.get('geothermal_heat_source')
        if ghp and ghp["thermal_output"] <= 0:
            del ghp
            ghp = None
        ihs = kwargs.get('ice_storage')
        if ihs and ihs["volume"] <= 0:
            del ihs
            ihs = None
        tgs = kwargs.get('thermal_ground_storage')
        if tgs and tgs["volume"] <= 0:
            del tgs
            tgs = None
        boiler = kwargs.get('gas_boiler')
        if boiler and boiler["thermal_output"] <= 0:
            del boiler
            boiler = None
        pellet_boiler = kwargs.get('pellet_boiler')
        if pellet_boiler and pellet_boiler["thermal_output"] <= 0:
            del pellet_boiler
            pellet_boiler = None
        chp = kwargs.get('chp')
        self.biomethane_fraction = 0
        if chp and chp["electric_output"] <= 0:
            del chp
            chp = None
        if chp and chp["electric_output"] > 0:
            self.biomethane_fraction = chp['biomethane_fraction']
        pv = kwargs.get('pv')
        if pv and pv["nominal_power"] <= 0:
            del pv
            pv = None
        p2h = kwargs.get('power_to_heat')
        if p2h and p2h["thermal_output"] <= 0:
            del p2h
            p2h = None
        wt = kwargs.get('wind_turbine')
        if wt and wt["nominal_power"] <= 0:
            del wt
            wt = None
        battery = kwargs.get('battery')
        if battery and battery["capacity"] <= 0:
            del battery
            battery = None
        hs = kwargs.get('heat_storage')
        if hs and hs["volume"] <= 0:
            del hs
            hs = None
        st = kwargs.get('solar_thermal')
        if st and st["generation"].sum().max() <= 0:
            del st
            st = None

        self.spec_co2 = kwargs.get('co2')

        # Create relevant temperature list
        temperature_levels = temps['intermediate']
        temperature_levels.append(temps['heating'])
        temperature_levels.append(temps['heating']
                                  - temps['heat_drop_heating'])

        # Temperature might have to be boosted for DHW.
        if temps['dhw'] > max(temperature_levels):
            boost_dhw = True
        else:
            boost_dhw = False
            # Ensure that DHW temperature is considered
            temperature_levels.append(temps['dhw'])

        # Ensure unique temperatures
        temperature_levels = list(set(temperature_levels))
        temperature_levels.sort()

        # Time range of the data (in a)
        index = demand['electricity'].index
        index.freq = pd.infer_freq(index)
        time_range = (index[-1] - index[0] + index.freq) / pd.Timedelta('365D')
        ############################
        # Create energy system model
        ############################
        energy_system = EnergySystem(timeindex=demand['electricity'].index)

        # list of flows to identify different sources and sinks later
        # which use units of power
        self.th_demand_flows = list()
        self.pv_flows = list()
        self.wt_flows = list()
        self.chp_el_flows = list()
        self.chp_heat_flows = list()
        self.hp_flows = list()
        self.p2h_flows = list()
        self.boiler_flows = list()
        self.pellet_heat_flows = list()
        self.gt_input_flows = list()
        self.st_input_flows = list()
        self.fossil_gas_flows = list()
        self.biomethane_flows = list()
        self.chp_gas_flows = list()
        self.electricity_import_flows = list()
        self.electricity_export_flows = list()
        self.wood_pellets_flows = list()

        # Create main buses
        b_eldist = Bus(label="b_eldist")  # Local distribution network
        b_elprod = Bus(label="b_elprod",  # local production network
                       outputs={b_eldist: Flow(
                           variable_costs=energy_cost['eeg_levy'])})
        b_elgrid = Bus(label="b_elgrid")
        b_elxprt = Bus(label="b_elxprt")  # electricity export network
        b_gas = Bus(label="b_gas")

        energy_system.add(b_eldist, b_elprod, b_elxprt, b_gas, b_elgrid)

        ###################################################################
        # unidirectional grid connection
        grid_connection = custom.Link(
            label="grid_connection",
            inputs={b_elgrid: Flow(),
                    b_elxprt: Flow()},
            outputs={b_eldist: Flow(),
                     b_elgrid: Flow()},
            conversion_factors={(b_elxprt, b_elgrid): 1,
                                (b_elgrid, b_eldist): 1}
        )

        energy_system.add(grid_connection)

        ###################################################################
        # Thermal components
        heat_layers = HeatLayers(energy_system=energy_system,
                                 temperature_levels=temperature_levels,
                                 reference_temperature=temps['reference'])

        if hs:
            thermal_storage = MultiLayerStorage(
                diameter=hs['diameter'],
                volume=hs['volume'],
                insulation_thickness=hs['insulation_thickness'],
                ambient_temperature=meteo['temp_air'],
                heat_layers=heat_layers)
        else:
            thermal_storage = None

        ####################################################################
        # Heat pump
        if bhp:
            b_el_bhp = Bus(
                label='b_el_bhp',
                inputs={b_eldist: Flow(nominal_value=bhp['electric_input'])})
            energy_system.add(b_el_bhp)
            heat_pump = LayeredHeatPump(energy_system=energy_system,
                                        heat_layers=heat_layers,
                                        electricity_source=b_el_bhp,
                                        heat_sources={
                                            "ice": 0,
                                            "soil": meteo['temp_soil'],
                                            "sonde": ghp['temperature'],
                                            "pit_storage": tgs["temperature"]},
                                        label="heat_pump")
            # heat pump sources
            # near surface source
            if shp:
                b_shp = Bus(label="b_bhp",
                            outputs={heat_pump.b_th_in["soil"]: Flow()})
                s_shp = Source(label="s_shp",
                               outputs={b_shp: Flow(nominal_value=shp['thermal_output'])})

                self.gt_input_flows.append((s_shp.label, b_shp.label))
                energy_system.add(s_shp, b_shp)

            # deep geothermal
            if ghp:
                b_ghp = Bus(label="b_ghp",
                            outputs={heat_pump.b_th_in["sonde"]: Flow()})
                s_ghp = Source(label="s_ghp",
                               outputs={b_ghp: Flow(nominal_value=ghp['thermal_output'])})

                self.gt_input_flows.append((s_ghp.label, b_ghp.label))
                energy_system.add(s_ghp, b_ghp)

            ####################################################################
            # Ice storage
            if ihs:
                b_ihs = Bus(label='b_ihs',
                            inputs={heat_layers.b_th_lowest: Flow()},
                            outputs={heat_pump.b_th_in["ice"]: Flow()})

                # Calculate dimensions for loss/gain estimation
                ihs_surface_top = ihs['volume'] / ihs['height']
                ihs_radius = np.sqrt(ihs_surface_top) / np.pi
                ihs_surface_side = 2 * np.pi * ihs_radius * ihs['height']

                ihs_gains_air = (meteo['temp_air']  # °C = delta in K
                                 * TC_CONCRETE  # W / (m * K)
                                 * ihs_surface_top  # m²
                                 / ihs['ceil_thickness'])  # m
                ihs_gains_ground = (meteo['temp_soil']
                                    * TC_CONCRETE
                                    * (ihs_surface_side + ihs_surface_top)
                                    / ihs['wall_thickness'])

                s_ihs = GenericStorage(
                    label='s_ihs',
                    inputs={b_ihs: Flow()},
                    outputs={b_ihs: Flow()},
                    fixed_losses_relative=-(ihs_gains_air + ihs_gains_ground) / 1e6,
                    nominal_storage_capacity=H2O_HEAT_FUSION * H2O_DENSITY * ihs['volume']
                )

                # For most ambient temperatures,
                # the ice storage will melt (gain energy).
                # So we add excess heat to allow not using it.
                # We charge money for this to make it unattractive to use
                s_ihs_excess = Sink(label="ihs_excess",
                                    inputs={b_ihs: Flow(variable_costs=100)})

                energy_system.add(b_ihs, s_ihs, s_ihs_excess)

            if tgs:
                b_thp = Bus(label='b_ehp',
                            inputs={heat_layers.b_th_lowest: Flow()},
                            outputs={heat_pump.b_th_in["pit_storage"]: Flow()})

                s_tgs = GenericStorage(
                    label='s_tgs',
                    nominal_storage_capacity=tgs['heat_capacity'],
                    inputs={b_thp: Flow()},
                    outputs={b_thp: Flow()})
                energy_system.add(s_tgs, b_thp)

        ###############################################################
        # Solar thermal
        if st:
            b_st = Bus(label="b_st")
            s_st = Source(label="s_st",
                          outputs={b_st: Flow(nominal_value=1)})

            energy_system.add(s_st, b_st)

            for temp in heat_layers.TEMPERATURE_LEVELS:
                # Naming of new temperature bus
                temp_str = "{0:.0f}".format(temp)

                b_th_in_level = heat_layers.b_th_in[temp]
                st_level_label = 't_st_' + temp_str
                t_st_level = Transformer(
                    label=st_level_label,
                    inputs={b_st: Flow(nominal_value=1)},
                    outputs={b_th_in_level: Flow(nominal_value=1)},
                    conversion_factors={
                        b_st: (1 / st['generation'][
                            'ST_' + str(temp)]).to_list()})

                self.st_input_flows.append((st_level_label,
                                            b_th_in_level.label))
                energy_system.add(t_st_level)

        ###########################################################################

        # create external markets
        # RLM customer for district and larger buildings
        m_el_in = Source(label='m_el_in',
                         outputs={b_elgrid: Flow(
                             variable_costs=energy_cost['electricity']['AP'] +
                                            self.spec_co2['el_in'] * self.spec_co2['price'],
                             investment=Investment(
                                 ep_costs=energy_cost['electricity']['LP']
                                          * time_range))})
        self.electricity_import_flows.append((m_el_in.label, b_elgrid.label))

        m_el_out = Sink(label='m_el_out',
                        inputs={b_elgrid: Flow(variable_costs=self.spec_co2['el_out']
                                                              * self.spec_co2['price'])})
        self.electricity_export_flows.append((b_elgrid.label, m_el_out.label))

        gas_price = energy_cost['fossil_gas'] \
                    + self.spec_co2['fossil_gas'] * self.spec_co2['price']
        m_gas = Source(label='m_gas',
                       outputs={b_gas: Flow(variable_costs=gas_price)})

        energy_system.add(m_el_in, m_el_out, m_gas)

        # create local energy demand
        d_el = Sink(label='d_el',
                    inputs={b_eldist: Flow(fix=demand['electricity'],
                                           nominal_value=1)})

        heat_demand = HeatDemands(
            heat_layers=heat_layers,
            heat_demands=demand['heating'],
            label="heating",
            forward_flow_temperature=temps['heating'],
            backward_flow_temperature=(temps['heating']
                                       - temps['heat_drop_heating']))

        # create expensive source for missing heat to ensure model is solvable
        missing_heat = Source(
            label='missing_heat',
            outputs={heat_layers.b_th_in_highest: Flow(variable_costs=1000)})
        energy_system.add(missing_heat)

        if boost_dhw:
            b_th_dhw = Bus(label="b_th_dhw")
            temp_max = max(temperature_levels)
            heater_ratio = (temp_max - temps['heat_drop_exchanger_dhw']
                            - temps['reference']) / (temps['dhw']
                                                     - temps['reference'])

            heater = Transformer(
                label="dhw_booster",
                inputs={b_eldist: Flow(),
                        heat_demand.thermal_sink_bus: Flow()},
                outputs={b_th_dhw: Flow()},
                conversion_factors={
                    b_eldist: 1 - heater_ratio,
                    heat_demand.thermal_sink_bus: heater_ratio,
                    b_th_dhw: 1})
            self.p2h_flows.append((heater.label,
                                   b_th_dhw.label))
            energy_system.add(b_th_dhw, heater)

            d_dhw = Sink(label='d_dhw',
                         inputs={b_th_dhw: Flow(
                             nominal_value=1,
                             fix=demand['dhw'])})
            self.th_demand_flows.append((b_th_dhw.label,
                                         d_dhw.label))
        else:
            d_dhw = Sink(label='d_dhw',
                         inputs={heat_demand.thermal_sink_bus: Flow(
                             nominal_value=1,
                             fix=demand['dhw'])})
            self.th_demand_flows.append((heat_demand.thermal_sink_bus.label,
                                         d_dhw.label))

        energy_system.add(d_el, d_dhw)

        if boiler:
            # boiler
            t_boiler = Transformer(
                label='t_boiler',
                inputs={b_gas: Flow()},
                outputs={
                    heat_layers.b_th_in_highest:
                        Flow(nominal_value=boiler['thermal_output'])},
                conversion_factors={
                    heat_layers.b_th_in_highest:
                        boiler['efficiency']})

            self.boiler_flows.append((t_boiler.label,
                                      heat_layers.b_th_in_highest.label))
            self.fossil_gas_flows.append((m_gas.label, b_gas.label))
            energy_system.add(t_boiler)

        if pellet_boiler:
            # wood pellet boiler
            b_pellet = Bus(label="b_pellet")
            m_pellet = Source(
                label='m_pellet',
                outputs={b_pellet: Flow(
                    variable_costs=energy_cost['wood_pellet']
                                   + self.spec_co2['wood_pellet']
                                   * self.spec_co2['price']
                                   * HHV_WP)})

            t_pellet = Transformer(label='t_pellet',
                                   inputs={b_pellet: Flow()},
                                   outputs={
                                       heat_layers.b_th_in_highest:
                                           Flow(nominal_value=pellet_boiler['thermal_output'])},
                                   conversion_factors={
                                       b_pellet: HHV_WP,
                                       heat_layers.b_th_in_highest:
                                           pellet_boiler['efficiency']})

            self.pellet_heat_flows.append((t_pellet.label,
                                           heat_layers.b_th_in_highest.label))
            self.wood_pellets_flows.append((m_pellet.label, b_pellet.label))
            energy_system.add(b_pellet, m_pellet, t_pellet)

        if chp:
            # CHP
            b_gas_chp = Bus(label="b_gas_chp")

            biomethane_price = energy_cost['biomethane'] \
                               + self.spec_co2['biomethane'] * self.spec_co2['price']
            m_gas_chp = Source(label='m_gas_chp',
                               outputs={b_gas_chp: Flow(
                                   variable_costs=
                                   (1 - chp['biomethane_fraction'])
                                   * gas_price
                                   + chp['biomethane_fraction']
                                   * biomethane_price)})
            self.chp_gas_flows.append((m_gas_chp.label, b_gas_chp.label))

            b_el_chp_fund = Bus(
                label="b_el_chp_fund",
                outputs={
                    b_elxprt: Flow(
                        variable_costs=-chp['feed_in_tariff_funded']),
                    b_elprod: Flow(
                        variable_costs=-chp['own_consumption_tariff_funded'])})

            b_el_chp_unfund = Bus(label="b_el_chp_unfund",
                                  outputs={b_elxprt: Flow(variable_costs=-energy_cost['electricity']['market']),
                                           b_elprod: Flow()})

            b_el_chp = Bus(label="b_el_chp",
                           outputs={b_el_chp_fund: Flow(summed_max=chp['funding_hours_per_year'],
                                                        nominal_value=chp['electric_output']),
                                    b_el_chp_unfund: Flow()})

            t_chp = Transformer(label='t_chp',
                                inputs={b_gas_chp: Flow(
                                    nominal_value=chp['gas_input'])},
                                outputs={
                                    b_el_chp: Flow(nominal_value=chp['electric_output']),
                                    heat_layers.b_th_in_highest:
                                        Flow(nominal_value=chp['thermal_output'])},
                                conversion_factors={
                                    b_el_chp: chp['electric_efficiency'],
                                    heat_layers.b_th_in_highest:
                                        chp['thermal_efficiency']})

            self.chp_heat_flows.append((t_chp.label,
                                        heat_layers.b_th_in_highest.label))
            self.chp_el_flows.append((t_chp.label, b_el_chp.label))
            energy_system.add(m_gas_chp, b_gas_chp, b_el_chp, t_chp,
                              b_el_chp_fund, b_el_chp_unfund)

        # PV
        if pv:
            b_el_pv = Bus(label="b_el_pv",
                          outputs={
                              b_elxprt: Flow(variable_costs=-pv['feed_in_tariff']),
                              b_elprod: Flow()})

            t_pv = Source(label='t_pv',
                          outputs={b_el_pv: Flow(nominal_value=1.0, max=pv['generation'])})
            self.pv_flows.append((t_pv.label, b_el_pv.label))

            energy_system.add(t_pv, b_el_pv)

        # power to heat
        if p2h:
            t_p2h = Transformer(label='t_p2h',
                                inputs={b_eldist: Flow()},
                                outputs={
                                    heat_layers.b_th_in_highest:
                                        Flow(nominal_value=p2h['thermal_output'])},
                                conversion_factors={
                                    b_eldist: 1,
                                    heat_layers.b_th_in_highest: 1})
            energy_system.add(t_p2h)
            self.p2h_flows.append((t_p2h.label,
                                   heat_layers.b_th_in_highest.label))

        # wind turbine
        if wt:
            b_el_wt = Bus(label="b_el_wt",
                          outputs={
                              b_elxprt: Flow(variable_costs=-wt['feed_in_tariff']),
                              b_elprod: Flow()})

            t_wt = Source(label='t_wt',
                          outputs={b_el_wt: Flow(nominal_value=1.0, max=wt['generation'])})
            self.pv_flows.append((t_wt.label, b_el_wt.label))

            energy_system.add(t_wt, b_el_wt)

        if battery:
            # Battery
            s_battery = GenericStorage(
                label='s_battery',
                inputs={
                    b_elprod: Flow(nominal_value=battery['power'])},
                outputs={
                    b_elprod: Flow(nominal_value=battery['power'])},
                loss_rate=battery['self_discharge'],
                nominal_storage_capacity=battery['capacity'],
                inflow_conversion_factor=battery['efficiency_inflow'],
                outflow_conversion_factor=battery['efficiency_outflow'])

            energy_system.add(s_battery)

        model = Model(energy_system)

        if thermal_storage:
            thermal_storage.add_shared_limit(model=model)

        self.energy_system = energy_system
        self.model = model

    def heat_chp(self):
        """
        Calculates and returns thermal energy from chp

        :return: integrated chp power
        """
        e_chp_th = 0
        for res in self.chp_heat_flows:
            e_chp_th += self.energy_system.results['main'][res][
                'sequences']['flow'].sum()

        return e_chp_th

    def heat_geothermal(self):
        """
        Calculates and returns geothermal energy

        :return: integrated geothermal power
        """
        e_gt_th = 0
        for res in self.gt_input_flows:
            e_gt_th += self.energy_system.results['main'][res][
                'sequences']['flow'].sum()

        return e_gt_th

    def heat_heat_pump(self):
        """
        Calculates and returns heat pump heat

        :return: integrated het pump power
        """
        e_hp_th = 0
        for res in self.hp_flows:
            e_hp_th += self.energy_system.results['main'][res][
                'sequences']['flow'].sum()

        return e_hp_th

    def heat_solar_thermal(self):
        """
        Calculates and returns solar thermal energy

        :return: integrated solar thermal power
        """
        e_st_th = 0
        for res in self.st_input_flows:
            e_st_th += self.energy_system.results['main'][res][
                'sequences']['flow'].sum()

        return e_st_th

    def heat_pellet(self):
        """
        Calculates and returns thermal energy from pallet boiler

        :return: integrated pallet power
        """
        e_pellet_th = 0
        for res in self.pellet_heat_flows:
            e_pellet_th += self.energy_system.results['main'][res][
                'sequences']['flow'].sum()

        return e_pellet_th

    def heat_boiler(self):
        """
        Calculates and returns thermal energy from pallet boiler

        :return: integrated pallet power
        """
        e_boiler_th = 0
        for res in self.boiler_flows:
            e_boiler_th += self.energy_system.results['main'][res][
                'sequences']['flow'].sum()

        return e_boiler_th

    def heat_p2h(self):
        """
        Calculates and returns thermal energy from pallet boiler

        :return: integrated pallet power
        """
        e_p2h_th = 0
        for res in self.p2h_flows:
            e_p2h_th += self.energy_system.results['main'][res][
                'sequences']['flow'].sum()

        return e_p2h_th

    def thermal_demand(self):
        """
        Calculates and returns thermal demand

        :return: integrated thermal demand
        """
        d_th = 0
        for res in self.th_demand_flows:
            d_th += self.energy_system.results['main'][res][
                'sequences']['flow'].sum()

        return d_th

    def el_pv(self):
        """
        Calculates the energy yield from pv

        :return: integrated pv electricity generation
        """
        e_pv_el = 0
        for res in self.pv_flows:
            e_pv_el += self.energy_system.results['main'][res][
                'sequences']['flow'].sum()

        return e_pv_el

    def el_wt(self):
        """
        Calculates the energy yield from wind

        :return: integrated wind turbine electricity generation
        """
        e_wt_el = 0
        for res in self.wt_flows:
            e_wt_el += self.energy_system.results['main'][res][
                'sequences']['flow'].sum()

        return e_wt_el

    def el_chp(self):
        """
        Calculates the electricity generation from chp

        :return: integrated chp electricity generation
        """
        e_chp_el = 0
        for res in self.chp_el_flows:
            e_chp_el += self.energy_system.results['main'][res][
                'sequences']['flow'].sum()

        return e_chp_el

    def el_production(self):
        """
        Electricity generated on site by distributed generation

        :return: integrated distributed electricity generation
        """
        return self.el_chp() + self.el_pv() + self.el_wt()

    def el_demand(self):
        """
        Energy demand calculated as balance of production, import and export

        :return: integrated electricity demand
        """
        return self.el_production().sum() + self.el_import().sum() - self.el_export().sum()

    def el_import(self):
        """
        Electricity imported from the public grid

        :return: Electricity import
        """
        el_in = 0
        for res in self.electricity_import_flows:
            el_in += self.energy_system.results['main'][res][
                'sequences']['flow']

        return el_in

    def el_import_peak(self):
        """
        Maximum electricity import

        :return: Peak electricity import
        """
        return self.el_import().max()

    def el_export(self):
        """
        Electricity exported to the public grid

        :return: Electricity export
        """
        el_out = 0
        for res in self.electricity_export_flows:
            el_out += self.energy_system.results['main'][res][
                'sequences']['flow']

        return el_out

    def pellet_import(self):
        """
        Imported wood pellets from some supplier

        :return: Wood pellet import
        """
        wp_in = 0
        for res in self.wood_pellets_flows:
            wp_in += self.energy_system.results['main'][res][
                'sequences']['flow'].sum()

        return wp_in

    def chp_gas_import(self):
        """
        Imported gas for use in the chp which can be fossil or biomethane or mixtures

        :return: Gas import for chp
        """
        chp_gas_in = 0
        for res in self.chp_gas_flows:
            chp_gas_in += self.energy_system.results['main'][res][
                          'sequences']['flow'].sum()

        return chp_gas_in

    def chp_fossil_gas_import(self):
        """
        Share of fossil gas for chp import

        :return: Fossil Gas import for chp
        """
        return self.chp_gas_import() * (1 - self.biomethane_fraction)

    def chp_biomethane_import(self):
        """
        Share of biomethane for chp import

        :return: Biomethane import for chp
        """
        return self.chp_gas_import() * self.biomethane_fraction

    def fossil_gas_import(self):
        """
        Overall import of natural gas from the public grid

        :return: Import fossil gas
        """
        fg_in = 0
        for res in self.fossil_gas_flows:
            fg_in += self.energy_system.results['main'][res][
                'sequences']['flow'].sum()
        fg_in += self.chp_fossil_gas_import()

        return fg_in

    def biomethane_import(self):
        """
        Overall import of biomethane from the public grid

        :return: Import biomethane
        """
        bm_in = 0
        for res in self.biomethane_flows:
            bm_in += self.energy_system.results['main'][res][
                'sequences']['flow'].sum()
        bm_in += self.chp_biomethane_import()

        return bm_in

    def gas_import(self):
        """
        Overall import of gas from the public grid
        which is the sum of fossil gas and biomethane

        :return: Import gas
        """
        return self.fossil_gas_import() + self.biomethane_import()

    def co2_emission(self):
        """
        Calculates the CO2 Emission acc. to
        https://doi.org/10.3390/en13112967

        :return: Integrated CO2 emission in operation
        """
        CO2_import_natural_gas = self.fossil_gas_import() * self.spec_co2['fossil_gas']
        CO2_import_biomethane = self.biomethane_import() * self.spec_co2['biomethane']
        CO2_import_pellet = self.pellet_import() * self.spec_co2['wood_pellet'] * HHV_WP
        CO2_import_el = (self.el_import() * self.spec_co2['el_in']).sum()
        CO2_export_el = (-self.el_export() * self.spec_co2['el_out']).sum()
        res = (CO2_import_natural_gas + CO2_import_biomethane
               + CO2_import_el + CO2_import_pellet
               - CO2_export_el)
        return np.round(res, 1)

    def own_consumption(self):
        """
        Calculates the own consumption of distributed generation

        :return: Own consumption
        """
        if self.el_production().sum() > 0:
            oc = 1 - (self.el_export().sum()
                      / self.el_production().sum())
        else:
            oc = 1
        return np.round(oc, 3)

    def self_sufficiency(self):
        """
        Calculates the self sufficiency of the district

        :return: Self sufficiency
        """
        res = 1 - (self.el_import().sum()
                   / self.el_demand().sum())
        return np.round(res, 3)
