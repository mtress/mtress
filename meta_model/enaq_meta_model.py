# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd

from oemof.solph import (Bus, EnergySystem, Flow, Sink, Source, Transformer,
                         Model, Investment, constraints, custom,
                         GenericStorage)
from oemof.thermal import stratified_thermal_storage as sts

from .physics import (celsius_to_kelvin, kelvin_to_celsius, HHV_WP,
                      TC_CONCRETE, H2O_HEAT_FUSION, H2O_DENSITY,
                      HS_PER_HI_GAS, kJ_to_MWh, H2O_HEAT_CAPACITY,
                      TC_INSULATION, kilo_to_mega, calc_cop)


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
        if chp and chp["electric_output"] <= 0:
            del chp
            chp = None
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
        if st and st["nominal_power"] <= 0:
            del st
            st = None

        # Create relevant temperature list
        temperature_levels = temps['intermediate']
        temperature_levels.append(temps['heating'])

        # Temperature might have to be boosted for DHW.
        if temps['dhw'] > max(temperature_levels):
            boost_dhw = True
        else:
            boost_dhw = False
            # Ensure that DHW temperature is considered
            temperature_levels.append(temps['dhw'])

        temperature_levels = list(set(temperature_levels))  # Ensure unique temperatures
        temperature_levels.sort()

        # Time range of the data (in a)
        demand['electricity'].index.freq = pd.infer_freq(demand['electricity'].index)
        time_range = (demand['electricity'].index[-1] -
                      demand['electricity'].index[0]) \
                      / pd.Timedelta('365D')

        ############################
        # Create energy system model
        ############################
        energy_system = EnergySystem(timeindex=demand['electricity'].index)

        # list of flows to identify different sources and sinks later
        # which use units of power
        self.chp_flows = list()
        self.pellet_flows = list()
        self.gt_input_flows = list()
        self.st_input_flows = list()
        self.th_demand_flows = list()

        # Create main buses
        b_eldist = Bus(label="b_eldist")  # Local distribution network
        b_elprod = Bus(label="b_elprod",  # local production network
                       outputs={b_eldist: Flow()})
        b_elxprt = Bus(label="b_elxprt")  # electricity export network
        b_gas = Bus(label="b_gas")

        energy_system.add(b_eldist, b_elprod, b_elxprt, b_gas)
        ###################################################################
        # Solar Thermal
        b_st = Bus(label="b_st", )
        s_st = Source(label="s_st",
                            outputs={b_st: Flow(nominal_value=1)})

        energy_system.add(s_st, b_st)

        ####################################################################
        # heat pump
        if bhp:
            b_el_bhp = Bus(label='b_el_bhp',
                           inputs={b_eldist: Flow(nominal_value=bhp['electric_input'])})
            energy_system.add(b_el_bhp)

            # heat pump sources
            # near surface source
            if shp:
                b_shp = Bus(label="b_bhp")
                s_shp = Source(label="s_shp",
                               outputs={b_shp: Flow(nominal_value=shp['thermal_output'])})

                self.gt_input_flows.append((s_shp.label, b_shp.label))
                energy_system.add(s_shp, b_shp)

            # deep geothermal
            if ghp:
                b_ghp = Bus(label="b_ghp")
                s_ghp = Source(label="s_ghp",
                               outputs={b_ghp: Flow(nominal_value=ghp['thermal_output'])})

                self.gt_input_flows.append((s_ghp.label, b_ghp.label))
                energy_system.add(s_ghp, b_ghp)

            ####################################################################
            # Ice storage
            if ihs:
                b_ihs = Bus(label='b_ihs')  # bus for interconnections

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
                s_ihs_excess = Sink(label="ihs_excess",
                                    inputs={b_ihs: Flow()})

                energy_system.add(b_ihs, s_ihs, s_ihs_excess)

        ####################################################################
        # Create object collections for temperature dependent technologies
        b_th = dict()
        b_th_in = dict()
        h_storage_comp = list()

        # ...and know what was the temperature level before.
        temp_low = None
        for temp in temperature_levels:
            # Naming of new temperature bus
            temp_str = "{0:.0f}".format(kelvin_to_celsius(temp))
            b_th_label = 'b_th_' + temp_str
            b_th_in_label = 'b_th_in_' + temp_str

            if temp_low is None:
                if bhp and ihs:
                    b_th_level = Bus(label=b_th_label,
                                     outputs={b_ihs: Flow()})
                else:
                    b_th_level = Bus(label=b_th_label)
                b_th_in_level = Bus(label=b_th_in_label,
                                    outputs={b_th_level: Flow()})
            else:  # connects to the previous temperature level
                b_th_level = Bus(label=b_th_label)
                b_th_in_level = Bus(label=b_th_in_label,
                                    outputs={b_th_in[temp_low]: Flow(),
                                             b_th_level: Flow()})

            b_th[temp] = b_th_level
            b_th_in[temp] = b_th_in_level

            energy_system.add(b_th_level, b_th_in_level)

            if tgs and bhp:
                # thermal ground storage as source for heat pumps
                thp_label = 't_thp_' + temp_str

                if temp_low is None:
                    b_thp = Bus(label='b_ehp', inputs={b_th[temp]: Flow()})

                    s_tgs = GenericStorage(label='s_tgs',
                                           nominal_storage_capacity=tgs['heat_capacity'],
                                           inputs={b_thp: Flow()},
                                           outputs={b_thp: Flow()})
                    energy_system.add(s_tgs, b_thp)

                thp_cop = calc_cop(tgs['temperature'], temp)
                t_thp = Transformer(label=thp_label,
                                    inputs={b_el_bhp: Flow(),
                                            b_thp: Flow()},
                                    outputs={b_th_in_level: Flow()},
                                    conversion_factors={
                                        b_el_bhp: 1 / thp_cop,
                                        b_thp: (thp_cop - 1) / thp_cop,
                                        b_th_in_level: 1})

                energy_system.add(t_thp)

            # ice storage as source for heat pumps
            if bhp and ihs:
                ihp_label = 't_ihp_' + temp_str
                ihp_cop = calc_cop(celsius_to_kelvin(0), temp)
                t_ihp = Transformer(label=ihp_label,
                                    inputs={b_el_bhp: Flow(),
                                            b_ihs: Flow()},
                                    outputs={b_th_in_level: Flow()},
                                    conversion_factors={b_el_bhp: 1 / ihp_cop,
                                                        b_ihs: (ihp_cop - 1) / ihp_cop,
                                                        b_th_in_level: 1})
                energy_system.add(t_ihp)

            # (deep) geothermal source heat pump
            if bhp and ghp:
                ghp_label = 't_ghp_' + temp_str
                ghp_cop = calc_cop(ghp['temperature'], temp)
                t_ghp = Transformer(label=ghp_label,
                                    inputs={b_el_bhp: Flow(),
                                            b_ghp: Flow()},
                                    outputs={b_th_in_level: Flow()},
                                    conversion_factors={b_el_bhp: 1 / ghp_cop,
                                                        b_ghp: (ghp_cop - 1) / ghp_cop,
                                                        b_th_in_level: 1})
                energy_system.add(t_ghp)

            # (near surface) geothermal source heat pump
            if bhp and shp:
                bhp_label = 't_shp_' + temp_str
                shp_cop = calc_cop(meteo['temp_soil'], temp)
                t_shp = Transformer(label=bhp_label,
                                    inputs={b_el_bhp: Flow(),
                                            b_shp: Flow()},
                                    outputs={b_th_in_level: Flow()},
                                    conversion_factors={
                                        b_el_bhp: 1 / shp_cop,
                                        b_shp: (shp_cop - 1) / shp_cop,
                                        b_th_in_level: 1})
                energy_system.add(t_shp)

            ###############################################################
            # solar thermal sources
            if st:
                st_level_label = 't_st_' + temp_str
                t_st_level = Transformer(
                    label=st_level_label,
                    inputs={b_st: Flow(nominal_value=1)},
                    outputs={b_th_in_level: Flow(nominal_value=1)},
                    conversion_factors={b_st: 1 / st['generation']['ST_' + str(temp)]})

                self.st_input_flows.append((st_level_label, b_th_in_label))
                energy_system.add(t_st_level)

            ###########################################################
            # thermal storage
            if hs:
                storage_label = 's_heat_' + temp_str

                hs_capacity = hs['volume'] * \
                              kJ_to_MWh((temp - temps['reference']) *
                                        H2O_DENSITY *
                                        H2O_HEAT_CAPACITY)

                hs_loss_rate, hs_fixed_losses_relative, hs_fixed_losses_absolute = \
                    sts.calculate_losses(
                        u_value=TC_INSULATION / hs['insulation_thickness'],
                        diameter=hs['diameter'],
                        temp_h=temp,
                        temp_c=temps['reference'],
                        temp_env=meteo['temp_air'])

                s_heat = GenericStorage(
                    label=storage_label,
                    inputs={b_th_level: Flow()},
                    outputs={b_th_level: Flow()},
                    nominal_storage_capacity=hs_capacity,
                    loss_rate=hs_loss_rate,
                    fixed_losses_absolute=hs_fixed_losses_absolute,
                    fixed_losses_relative=hs_fixed_losses_relative
                )

                h_storage_comp.append(s_heat)

                energy_system.add(s_heat)

            ################################################################
            # Temperature risers
            if temp_low is not None:
                temp_low_str = "{0:.0f}".format(kelvin_to_celsius(temp_low))
                temp_high_str = "{0:.0f}".format(kelvin_to_celsius(temp))
                heater_label = 'rise_' + temp_low_str + '_' + temp_high_str
                heater_ratio = (temp_low - temps['reference']) / \
                               (temp - temps['reference'])
                heater = Transformer(label=heater_label,
                                     inputs={b_th_in_level: Flow(),
                                             b_th[temp_low]: Flow()},
                                     outputs={b_th[temp]: Flow()},
                                     conversion_factors={b_th_in_level:
                                                             1 - heater_ratio,
                                                         b_th[temp_low]:
                                                             heater_ratio,
                                                         b_th[temp]: 1})

                energy_system.add(heater)
            temp_low = temp

        ###########################################################################

        b_grid = Bus(label="b_grid")
        b_pregrid = Bus(label="b_pregrid",
                        inputs={b_elxprt: Flow()},
                        outputs={b_eldist: Flow()})

        # create external markets
        # RLM customer for district and larger buildings
        m_el_in = Source(label='m_el_in',
                         outputs={b_grid: Flow(
                             variable_costs=energy_cost['electricity']['AP'],
                             investment=Investment(
                                 ep_costs=energy_cost['electricity']['LP']))})

        m_el_out = Sink(label='m_el_out', inputs={b_grid: Flow()})

        grid_connection = custom.Link(
            label="grid_connection",
            inputs={b_grid: Flow(), b_pregrid: Flow()},
            outputs={b_grid: Flow(), b_pregrid: Flow()},
            conversion_factors={(b_pregrid, b_grid): 1,
                                (b_grid, b_pregrid): 1})

        m_gas = Source(label='m_gas',
                       outputs={b_gas: Flow(
                           variable_costs=energy_cost['natural_gas'])})

        energy_system.add(m_el_in, m_el_out, m_gas,
                          b_grid, b_pregrid, grid_connection)

        # create local energy demand
        d_el = Sink(label='d_el',
                    inputs={b_eldist: Flow(fix=demand['electricity'],
                                           nominal_value=1)})

        d_heat = Sink(label='d_heat',
                      inputs={b_th[temps['heating']]: Flow(
                          nominal_value=1,
                          fix=demand['heating'])})
        self.th_demand_flows.append((b_th[temps['heating']].label,
                                     d_heat.label))

        if boost_dhw:
            b_th[temps['dhw']] = Bus(label="b_th_dhw")
            temp_max = max(temperature_levels)
            heater_ratio = (temp_max - temps['heat_drop_exchanger_dhw']
                            - temps['reference']) / (temps['dhw']
                                                     - temps['reference'])

            heater = Transformer(label="dhw_booster",
                                 inputs={b_eldist: Flow(),
                                         b_th[temp_max]: Flow()},
                                 outputs={b_th[temps['dhw']]: Flow()},
                                 conversion_factors={
                                     b_eldist: 1 - heater_ratio,
                                     b_th[temp_low]: heater_ratio,
                                     b_th[temps['dhw']]: 1})
            energy_system.add(b_th[temps['dhw']], heater)

        d_dhw = Sink(label='d_dhw',
                     inputs={b_th[temps['dhw']]: Flow(
                         nominal_value=1,
                         fix=demand['dhw'])})

        self.th_demand_flows.append((b_th[temps['dhw']].label,
                                     d_dhw.label))

        energy_system.add(d_el, d_heat, d_dhw)

        if boiler:
            # boiler
            t_boiler = Transformer(
                label='t_boiler',
                inputs={b_gas: Flow()},
                outputs={
                    b_th_in[temperature_levels[-1]]:
                        Flow(nominal_value=boiler['thermal_output'])},
                conversion_factors={
                    b_gas: HS_PER_HI_GAS,
                    b_th_in[temperature_levels[-1]]:
                        boiler['efficiency']})
            energy_system.add(t_boiler)

        if pellet_boiler:
            # wood pellet boiler
            b_pellet = Bus(label="b_pellet")
            m_pellet = Source(label='m_pellet',
                              outputs={b_pellet:
                                           Flow(variable_costs=energy_cost['wood_pellet'])})

            t_pellet = Transformer(label='t_pellet',
                                   inputs={b_pellet: Flow()},
                                   outputs={
                                       b_th_in[temperature_levels[-1]]:
                                           Flow(nominal_value=pellet_boiler['thermal_output'])},
                                   conversion_factors={
                                       b_pellet: HHV_WP,
                                       b_th_in[temperature_levels[-1]]:
                                           pellet_boiler['efficiency']})

            self.pellet_flows.append((t_pellet.label,
                                      b_th_in[temperature_levels[-1]].label))
            energy_system.add(b_pellet, m_pellet, t_pellet)

        if chp:
            # CHP
            b_gas_chp = Bus(label="b_gas_chp")

            m_gas_chp = Source(label='m_gas_chp',
                               outputs={b_gas_chp: Flow(
                                   variable_costs=
                                   (1 - chp['biomethane_fraction'])
                                   * energy_cost['natural_gas']
                                   + chp['biomethane_fraction']
                                   * energy_cost['biomethane'])})

            b_el_chp_fund = Bus(label="b_el_chp_fund",
                                outputs={b_elxprt:
                                             Flow(variable_costs=
                                                  -chp['feed_in_tariff_funded']),
                                         b_elprod:
                                             Flow(variable_costs=
                                                  -chp['own_consumption_tariff_funded'])})

            b_el_chp_unfund = Bus(label="b_el_chp_unfund",
                                  outputs={b_elxprt: Flow(variable_costs=
                                                          -chp['feed_in_tariff_unfunded']),
                                           b_elprod: Flow(variable_costs=
                                                          energy_cost['eeg_levy'])})

            b_el_chp = Bus(label="b_el_chp",
                           outputs={b_el_chp_fund: Flow(summed_max=chp['funding_hours_per_year'],
                                                        nominal_value=chp['electric_output']),
                                    b_el_chp_unfund: Flow()})

            t_chp = Transformer(label='t_chp',
                                inputs={b_gas_chp: Flow(
                                    nominal_value=chp['gas_input'])},
                                outputs={
                                    b_el_chp: Flow(nominal_value=chp['electric_output']),
                                    b_th_in[temperature_levels[-1]]:
                                        Flow(nominal_value=chp['thermal_output'])},
                                conversion_factors={
                                    b_el_chp: chp['electric_output'] / chp['gas_input'],
                                    b_th_in[temperature_levels[-1]]:
                                        chp['thermal_output'] / chp['gas_input']})

            self.chp_flows.append((t_chp.label,
                                   b_th_in[temperature_levels[-1]].label))
            energy_system.add(m_gas_chp, b_gas_chp, b_el_chp, t_chp,
                              b_el_chp_fund, b_el_chp_unfund)

        # PV
        if pv:
            b_el_pv = Bus(label="b_el_pv",
                          outputs={
                              b_elxprt: Flow(variable_costs=-pv['feed_in_tariff']),
                              b_elprod: Flow(variable_costs=energy_cost['eeg_levy'])})

            t_pv = Source(label='t_pv',
                          outputs={b_el_pv: Flow(nominal_value=1.0, max=pv['generation'])})

            energy_system.add(t_pv, b_el_pv)

        # power to heat
        if p2h:
            t_p2h = Transformer(label='t_p2h',
                                inputs={b_eldist: Flow()},
                                outputs={
                                    b_th_in[temperature_levels[-1]]:
                                        Flow(nominal_value=p2h['thermal_output'])},
                                conversion_factors={
                                    b_eldist: 1,
                                    b_th_in[temperature_levels[-1]]: 1})
            energy_system.add(t_p2h)

        # wind turbine
        if wt:
            b_el_wt = Bus(label="b_el_wt",
                          outputs={
                              b_elxprt: Flow(variable_costs=-wt['feed_in_tariff']),
                              b_elprod: Flow(variable_costs=energy_cost['eeg_levy'])})

            t_wt = Source(label='t_wt',
                          outputs={b_el_wt: Flow(nominal_value=1.0, max=wt['generation'])})

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
                outflow_conversion_factor=battery['efficiency_outflow'],
                initial_storage_level=0,
                balanced=False)

            energy_system.add(s_battery)

        model = Model(energy_system)

        if hs:
            # Heat Storage Constraints
            w_factor = [1 / kilo_to_mega(H2O_HEAT_CAPACITY
                                         * H2O_DENSITY * (temp - temps['reference']))
                        for temp in temperature_levels]

            constraints.shared_limit(
                model, model.GenericStorageBlock.storage_content,
                'storage_limit', h_storage_comp, w_factor,
                upper_limit=hs['volume'])

        self.energy_system = energy_system
        self.model = model

    def heat_chp(self):
        """
        Calculates and returns thermal energy from chp

        :return: integrated chp power
        """
        e_chp_th = 0
        for res in self.chp_flows:
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
        for res in self.pellet_flows:
            e_pellet_th += self.energy_system.results['main'][res][
                'sequences']['flow'].sum()

        return e_pellet_th

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
