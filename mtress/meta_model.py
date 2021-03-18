# -*- coding: utf-8 -*-
import numbers

import numpy as np
import pandas as pd

from oemof.solph import (Bus, EnergySystem, Flow, Sink, Source, Transformer,
                         Model, Investment, constraints,
                         GenericStorage, NonConvex)

from .layered_heat import (HeatLayers, LayeredHeatPump, MultiLayerStorage,
                           HeatExchanger)
from .physics import (HHV_WP, H2O_HEAT_FUSION, H2O_DENSITY)

HIGH_VIRTUAL_COSTS = 1000


def _array(data, length):
    if isinstance(data, numbers.Number):
        data = np.full(length, fill_value=data)
    elif isinstance(data, list) and len(data) == length:
        data = np.array(data)
    elif isinstance(data, pd.Series) and len(data) == length:
        data = data.to_numpy()
    elif isinstance(data, np.ndarray):
        pass
    else:
        raise ValueError

    return data


class MetaModel:
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
        if st and st["area"] <= 0:
            del st
            st = None
        self.spec_co2 = kwargs.get('co2')
        self.allow_missing_heat = kwargs.get('allow_missing_heat', False)
        self.exclusive_grid_connection = kwargs.get(
            'exclusive_grid_connection', True)

        # Create relevant temperature list
        temperature_levels = temps.get('additional', list())
        temperature_levels.append(temps['forward_flow'])
        temperature_levels.append(temps['backward_flow'])

        # Ensure unique temperatures
        temperature_levels = list(set(temperature_levels))
        temperature_levels.sort()
        self.temperature_levels = temperature_levels

        # Time range of the data (in a)
        index = demand['heating'].index
        self.number_of_time_steps = len(index)
        index.freq = pd.infer_freq(index)
        self.time_range = ((index[-1] - index[0] + index.freq)
                           / pd.Timedelta('365D'))

        energy_cost["electricity"]["market"] = _array(
            data=energy_cost["electricity"]["market"],
            length=self.number_of_time_steps)

        for quantity in ["el_in", "el_out"]:
            self.spec_co2[quantity] = _array(data=self.spec_co2[quantity],
                                             length=self.number_of_time_steps)

        ############################
        # Create energy system model
        ############################
        energy_system = EnergySystem(timeindex=demand['electricity'].index)

        # list of flows to identify different sources and sinks later
        # which use units of power
        self.demand_th_flows = list()
        self.demand_el_flows = list()

        self.fossil_gas_import_flows = list()
        self.biomethane_import_flows = list()
        self.pellet_import_flows = list()
        self.electricity_import_flows = list()
        self.electricity_export_flows = list()

        self.pv_el_flows = list()
        self.wt_el_flows = list()
        self.chp_gas_flows = list()
        self.chp_th_flows = list()
        self.chp_el_flows = list()
        self.chp_el_funded_flow = None
        self.chp_el_unfunded_flow = None
        self.bhp_th_flow = list()
        self.bhp_el_flow = list()
        self.p2h_th_flows = list()
        self.p2h_el_flows = list()
        self.boiler_th_flows = list()
        self.pellet_th_flows = list()
        self.solar_thermal_th_flows = list()
        self.geothermal_input_flows = list()

        self.th_storage_inflows = dict()
        self.th_storage_outflows = dict()
        self.th_storage_content = dict()

        self.virtual_costs_flows = list()
        self.wood_pellets_flows = list()
        self.missing_heat_flow = list()

        ###############################################################
        # Create main buses
        b_eldist = Bus(label="b_eldist")  # Local distribution network
        b_elprod = Bus(label="b_elprod",  # local production network
                       outputs={b_eldist: Flow(
                           variable_costs=energy_cost['electricity']['eeg_levy'])})
        b_elxprt = Bus(label="b_elxprt")  # electricity export network
        b_elgrid = Bus(label="b_elgrid")

        energy_system.add(b_eldist, b_elprod, b_elxprt, b_elgrid)

        # (unidirectional) grid connection

        # RLM customer for district and larger buildings
        m_el_in = Source(label='m_el_in',
                         outputs={b_elgrid: Flow()})

        self.electricity_import_flows.append((m_el_in.label, b_elgrid.label))

        b_grid_connection_in = Bus(
            label="b_grid_connection_in",
            inputs={b_elgrid: Flow(
                variable_costs=(
                        energy_cost['electricity']['surcharge']
                        + energy_cost['electricity']['market']
                        + self.spec_co2['el_in']
                        * self.spec_co2['price']),
                investment=Investment(
                    ep_costs=energy_cost['electricity'][
                                 'demand_rate'] * self.time_range))},
            outputs={b_eldist: Flow(nonconvex=NonConvex(),
                                    nominal_value=1e5,
                                    grid_connection=True)})

        # create external market to sell electricity to
        b_grid_connection_out = Bus(
            label="b_grid_connection_out",
            inputs={b_elxprt: Flow(nonconvex=NonConvex(),
                                   nominal_value=1e5,
                                   grid_connection=True)})

        energy_system.add(m_el_in, b_grid_connection_in, b_grid_connection_out)

        co2_costs = np.array(self.spec_co2['el_out']) * self.spec_co2['price']
        m_el_out = Sink(label='m_el_out',
                        inputs={b_grid_connection_out: Flow(variable_costs=co2_costs)})
        self.electricity_export_flows.append((b_grid_connection_out.label,
                                              m_el_out.label))

        # Create gas buses if needed
        if boiler or (chp and self.biomethane_fraction < 1):
            b_fossil_gas = Bus(label="b_fossil_gas")

            gas_price = energy_cost['gas']['fossil_gas'] \
                        + self.spec_co2['fossil_gas'] * self.spec_co2['price']
            m_fossil_gas = Source(label='m_fossil_gas',
                                  outputs={b_fossil_gas: Flow(variable_costs=gas_price)})

            self.fossil_gas_import_flows.append((m_fossil_gas.label, b_fossil_gas.label))

            energy_system.add(b_fossil_gas, m_fossil_gas)

        if chp and self.biomethane_fraction > 0:
            b_biomethane = Bus(label='b_biomethane')

            biomethane_price = (energy_cost['gas']['biomethane']
                                + self.spec_co2['biomethane']
                                * self.spec_co2['price'])
            m_biomethane = Source(label='m_biomethane',
                                  outputs={b_biomethane: Flow(variable_costs=biomethane_price)})
            energy_system.add(m_biomethane, b_biomethane)

            self.biomethane_import_flows.append((m_biomethane.label, b_biomethane.label))

        # Create wood pellet buses if needed
        if pellet_boiler:
            b_pellet = Bus(label="b_pellet")
            m_pellet = Source(
                label='m_pellet',
                outputs={b_pellet: Flow(
                    variable_costs=energy_cost['wood_pellet']
                                   + self.spec_co2['wood_pellet']
                                   * self.spec_co2['price']
                                   * HHV_WP)})
            self.pellet_import_flows.append((m_pellet.label, b_pellet.label))

            energy_system.add(b_pellet, m_pellet)

        ###################################################################
        # Thermal components
        heat_layers = HeatLayers(energy_system=energy_system,
                                 temperature_levels=temperature_levels,
                                 reference_temperature=temps['reference'])

        if hs:
            self._thermal_storage = MultiLayerStorage(
                diameter=hs['diameter'],
                volume=hs['volume'],
                insulation_thickness=hs['insulation_thickness'],
                ambient_temperature=meteo['temp_air'],
                heat_layers=heat_layers)
            self.th_storage_inflows = self._thermal_storage.in_flows
            self.th_storage_outflows = self._thermal_storage.out_flows
            self.th_storage_content = self._thermal_storage.content
        else:
            self._thermal_storage = None

        ####################################################################
        # Heat pump
        if bhp:
            heat_sources = dict()
            if ihs:
                heat_sources["ice"] = 0
            if shp:
                heat_sources["soil"] = meteo['temp_soil']
            if ghp:
                heat_sources["sonde"] = ghp['temperature']
            if tgs:
                heat_sources["pit_storage"] = tgs["temperature"]

            if len(heat_sources) > 0:
                b_el_bhp = Bus(
                    label='b_el_bhp',
                    inputs={
                        b_eldist: Flow(nominal_value=bhp['electric_input'])})
                energy_system.add(b_el_bhp)
                if 'thermal_output' not in bhp:
                    bhp['thermal_output'] = None
                heat_pump = LayeredHeatPump(
                    energy_system=energy_system,
                    heat_layers=heat_layers,
                    electricity_source=b_el_bhp,
                    thermal_power_limit=bhp['thermal_output'],
                    heat_sources=heat_sources,
                    cop_0_35=bhp["cop_0_35"],
                    label="heat_pump")

                self.bhp_th_flow.extend(heat_pump.heat_out_flows)
                self.bhp_el_flow.append((b_eldist.label,
                                         b_el_bhp.label))
            else:
                heat_pump = None
            self.heat_pump = heat_pump
            # heat pump sources
            # near surface source
            if shp:
                b_shp = Bus(label="b_bhp",
                            outputs={heat_pump.b_th_in["soil"]: Flow()})
                s_shp = Source(
                    label="s_shp",
                    outputs={b_shp: Flow(nominal_value=shp['thermal_output'])})

                self.geothermal_input_flows.append((s_shp.label, b_shp.label))
                energy_system.add(s_shp, b_shp)

            # deep geothermal
            if ghp:
                b_ghp = Bus(label="b_ghp",
                            outputs={heat_pump.b_th_in["sonde"]: Flow()})
                s_ghp = Source(
                    label="s_ghp",
                    outputs={b_ghp: Flow(nominal_value=ghp['thermal_output'])})

                self.geothermal_input_flows.append((s_ghp.label, b_ghp.label))
                energy_system.add(s_ghp, b_ghp)

            ###################################################################
            # Ice storage
            if ihs:
                b_ihs = Bus(label='b_ihs',
                            inputs={heat_layers.b_th_lowest: Flow()},
                            outputs={heat_pump.b_th_in["ice"]: Flow()})

                s_ihs = GenericStorage(
                    label='s_ihs',
                    inputs={b_ihs: Flow()},
                    outputs={b_ihs: Flow()},
                    nominal_storage_capacity=(H2O_HEAT_FUSION
                                              * H2O_DENSITY
                                              * ihs['volume']))

                energy_system.add(b_ihs, s_ihs)

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
        else:
            self.heat_pump = None

        ###############################################################
        # Solar thermal
        if st:
            b_st = Bus(label="b_st")
            s_st = Source(label="s_st",
                          outputs={b_st: Flow(nominal_value=1)})

            energy_system.add(s_st, b_st)

            for temp in heat_layers.temperature_levels:
                # Naming of new temperature bus
                temp_str = "{0:.0f}".format(temp)

                b_th_in_level = heat_layers.b_th_in[temp]
                st_level_label = 't_st_' + temp_str
                t_st_level = Transformer(
                    label=st_level_label,
                    inputs={b_st: Flow(nominal_value=st["area"])},
                    outputs={b_th_in_level: Flow(nominal_value=1)},
                    conversion_factors={
                        b_st: (1 / st['spec_generation']
                        ['ST_' + str(temp)]).to_list()})

                self.solar_thermal_th_flows.append((st_level_label,
                                                    b_th_in_level.label))
                energy_system.add(t_st_level)

        # electricity demands covered of the local electricity network
        d_el_local = Sink(
            label='d_el_local',
            inputs={b_eldist: Flow(fix=demand['electricity'],
                                   nominal_value=1)})

        self.demand_el_flows.append((b_eldist.label,
                                     d_el_local.label))

        # electricity not covered of the local electricity network,
        # always created as there might be a booster but no explicit demand
        b_el_adjacent = Bus(
            label="b_el_adjacent",
            inputs={b_elgrid: Flow(
                variable_costs=energy_cost['electricity']['slp_price'])})

        # electricity demands not covered of the local electricity network
        if 'electricity_adjacent' in demand:
            d_el_adjacent = Sink(
                label='d_el_adjacent',
                inputs={b_el_adjacent: Flow(fix=demand['electricity_adjacent'],
                                            nominal_value=1)})

            self.demand_el_flows.append((b_el_adjacent.label,
                                         d_el_adjacent.label))

            energy_system.add(d_el_local, b_el_adjacent, d_el_adjacent)

        # create building heat
        b_th_buildings = Bus(label="b_th_buildings")
        energy_system.add(b_th_buildings)

        self.heat_exchanger_buildings = HeatExchanger(
            heat_layers=heat_layers,
            heat_demand=b_th_buildings,
            label="heat_exchanger",
            forward_flow_temperature=temps['forward_flow'],
            backward_flow_temperature=(temps['backward_flow']))

        d_sh = Sink(label='d_sh',
                    inputs={b_th_buildings: Flow(
                        fix=demand['heating'],
                        nominal_value=1)})
        self.demand_th_flows.append((b_th_buildings.label,
                                     d_sh.label))
        energy_system.add(d_sh)

        if sum(demand['dhw'] > 0):
            b_th_dhw_local = Bus(label="b_th_dhw_local")

            d_dhw = Sink(label='d_dhw',
                         inputs={b_th_dhw_local: Flow(
                             fix=demand['dhw'],
                             nominal_value=1)})
            self.demand_th_flows.append((b_th_dhw_local.label,
                                         d_dhw.label))

            energy_system.add(b_th_dhw_local, d_dhw)

            # We assume a heat drop but no energy loss due to the heat exchanger.
            heater_ratio = (max(heat_layers.temperature_levels)
                            - temps['heat_drop_exchanger_dhw']
                            - temps['reference']) / (temps['dhw']
                                                     - temps['reference'])

            if 0 < heater_ratio < 1:
                dhw_booster = Transformer(label="dhw_booster",
                                          inputs={b_eldist: Flow(),
                                                  b_th_buildings: Flow()},
                                          outputs={b_th_dhw_local: Flow()},
                                          conversion_factors={
                                              b_eldist: 1 - heater_ratio,
                                              b_th_buildings: heater_ratio,
                                              b_th_dhw_local: 1})
                self.p2h_el_flows.append((b_eldist.label,
                                          dhw_booster.label))
                self.p2h_th_flows.append((dhw_booster.label,
                                          b_th_dhw_local.label))
            else:
                dhw_booster = Bus(label="dhw_booster",
                                  inputs={b_th_buildings: Flow()},
                                  outputs={b_th_dhw_local: Flow()})

            energy_system.add(dhw_booster)

        if 'dhw_adjacent' in demand and sum(demand['dhw_adjacent'] > 0):
            b_th_dhw_adjacent = Bus(label="b_th_dhw_local")

            d_dhw_adjacent = Sink(label='d_dhw',
                                  inputs={b_th_dhw_adjacent: Flow(
                                      fix=demand['dhw_adjacent'],
                                      nominal_value=1)})
            self.demand_th_flows.append((b_th_dhw_adjacent.label,
                                         d_dhw_adjacent.label))

            energy_system.add(b_th_dhw_adjacent, d_dhw_adjacent)

            # We assume a heat drop but no energy loss due to the heat exchanger.
            heater_ratio = (max(heat_layers.temperature_levels)
                            - temps['heat_drop_exchanger_dhw']
                            - temps['reference']) / (temps['dhw']
                                                     - temps['reference'])

            if 0 < heater_ratio < 1:
                dhw_booster = Transformer(label="dhw_booster",
                                          inputs={b_el_adjacent: Flow(),
                                                  b_th_buildings: Flow()},
                                          outputs={b_th_dhw_adjacent: Flow()},
                                          conversion_factors={
                                              b_el_adjacent: 1 - heater_ratio,
                                              b_th_buildings: heater_ratio,
                                              b_th_dhw_adjacent: 1})

                self.p2h_el_flows.append((b_eldist.label,
                                          dhw_booster.label))
                self.p2h_th_flows.append((dhw_booster.label,
                                          b_th_dhw_adjacent.label))
            else:
                dhw_booster = Bus(label="dhw_booster",
                                  inputs={b_th_buildings: Flow()},
                                  outputs={b_th_dhw_adjacent: Flow()})

            energy_system.add(dhw_booster)

        # create expensive source for missing heat to ensure model is solvable
        if self.allow_missing_heat:
            missing_heat = Source(
                label='missing_heat',
                outputs={heat_layers.b_th_in_highest: Flow(
                    variable_costs=HIGH_VIRTUAL_COSTS)})
            energy_system.add(missing_heat)
            self.missing_heat_flow.append((missing_heat.label,
                                           heat_layers.b_th_in_highest.label))

        if boiler:
            # boiler
            t_boiler = Transformer(
                label='t_boiler',
                inputs={b_fossil_gas: Flow()},
                outputs={
                    heat_layers.b_th_in_highest:
                        Flow(nominal_value=boiler['thermal_output'])},
                conversion_factors={
                    heat_layers.b_th_in_highest:
                        boiler['efficiency']})

            self.boiler_th_flows.append((t_boiler.label,
                                         heat_layers.b_th_in_highest.label))
            energy_system.add(t_boiler)

        if pellet_boiler:
            # wood pellet boiler
            t_pellet = Transformer(
                label='t_pellet',
                inputs={b_pellet: Flow()},
                outputs={
                    heat_layers.b_th_in_highest:
                        Flow(nominal_value=pellet_boiler['thermal_output'])},
                conversion_factors={
                    b_pellet: HHV_WP,
                    heat_layers.b_th_in_highest:
                        pellet_boiler['efficiency']})

            self.pellet_th_flows.append((t_pellet.label,
                                         heat_layers.b_th_in_highest.label))
            energy_system.add(t_pellet)

        if chp:
            # CHP
            b_gas_chp = Bus(label='b_gas_chp')

            if self.biomethane_fraction == 1:
                t_gas_chp = Transformer(label="t_gas_chp",
                                        inputs={b_biomethane: Flow()},
                                        outputs={b_gas_chp: Flow()})
            elif self.biomethane_fraction == 0:
                t_gas_chp = Transformer(label="t_gas_chp",
                                        inputs={b_fossil_gas: Flow()},
                                        outputs={b_gas_chp: Flow()})
            else:
                t_gas_chp = Transformer(label="t_gas_chp",
                                        inputs={b_fossil_gas: Flow(),
                                                b_biomethane: Flow()},
                                        outputs={b_gas_chp: Flow()},
                                        conversion_factors={b_fossil_gas: 1 - self.biomethane_fraction,
                                                            b_biomethane: self.biomethane_fraction})
            energy_system.add(t_gas_chp, b_gas_chp)

            b_el_chp_fund = Bus(
                label="b_el_chp_fund",
                outputs={
                    b_elxprt: Flow(
                        variable_costs=-(energy_cost['electricity']['market']
                                         + chp['feed_in_subsidy'])),
                    b_elprod: Flow(
                        variable_costs=-chp['own_consumption_subsidy'])})

            b_el_chp_unfund = Bus(
                label="b_el_chp_unfund",
                outputs={
                    b_elxprt: Flow(
                        variable_costs=-energy_cost['electricity']['market']),
                    b_elprod: Flow()})

            b_el_chp = Bus(label="b_el_chp",
                           outputs={
                               b_el_chp_fund: Flow(
                                   summed_max=chp['funding_hours_per_year'],
                                   nominal_value=chp['electric_output']),
                               b_el_chp_unfund: Flow()})
            self.chp_el_funded_flow = (b_el_chp.label, b_el_chp_fund.label)
            self.chp_el_unfunded_flow = (b_el_chp.label, b_el_chp_unfund.label)
            energy_system.add(b_el_chp_fund, b_el_chp_unfund, b_el_chp)

            t_chp = Transformer(
                label='t_chp',
                inputs={b_gas_chp: Flow(
                    nominal_value=chp['gas_input'],
                    variable_costs=-energy_cost['gas']['energy_tax'])},
                outputs={
                    b_el_chp: Flow(nominal_value=chp['electric_output']),
                    heat_layers.b_th_in_highest:
                        Flow(nominal_value=chp['thermal_output'])},
                conversion_factors={
                    b_el_chp: chp['electric_efficiency'],
                    heat_layers.b_th_in_highest:
                        chp['thermal_efficiency']})

            self.chp_el_flows.append((t_chp.label, b_el_chp.label))
            self.chp_th_flows.append((t_chp.label,
                                      heat_layers.b_th_in_highest.label))
            self.chp_gas_flows.append((b_gas_chp.label, t_chp.label))

            energy_system.add(t_chp)

        # PV
        if pv:
            b_el_pv = Bus(
                label="b_el_pv",
                outputs={
                    b_elxprt: Flow(variable_costs=-pv['feed_in_subsidy']),
                    b_elprod: Flow()})

            t_pv = Source(
                label='t_pv',
                outputs={
                    b_el_pv: Flow(nominal_value=pv["nominal_power"],
                                  max=pv['spec_generation'])})
            self.pv_el_flows.append((t_pv.label, b_el_pv.label))

            energy_system.add(t_pv, b_el_pv)

        # power to heat
        if p2h:
            t_p2h = Transformer(
                label='t_p2h',
                inputs={b_eldist: Flow()},
                outputs={
                    heat_layers.b_th_in_highest:
                        Flow(nominal_value=p2h['thermal_output'])},
                conversion_factors={
                    b_eldist: 1,
                    heat_layers.b_th_in_highest: 1})
            energy_system.add(t_p2h)

            self.p2h_el_flows.append((b_eldist.label, t_p2h.label))
            self.p2h_th_flows.append((t_p2h.label, heat_layers.b_th_in_highest.label))

        # wind turbine
        if wt:
            b_el_wt = Bus(
                label="b_el_wt",
                outputs={
                    b_elxprt: Flow(variable_costs=-wt['feed_in_subsidy']),
                    b_elprod: Flow()})

            t_wt = Source(
                label='t_wt',
                outputs={
                    b_el_wt: Flow(
                        nominal_value=wt["nominal_power"],
                        max=wt['spec_generation'])})
            self.wt_el_flows.append((t_wt.label, b_el_wt.label))

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

        if self._thermal_storage:
            self._thermal_storage.add_shared_limit(model=model)

        if self.exclusive_grid_connection:
            constraints.limit_active_flow_count_by_keyword(
                model,
                "grid_connection",
                lower_limit=0,
                upper_limit=1)

        self.production_el_flows = self.wt_el_flows + self.pv_el_flows + self.chp_el_flows
        self.gas_flows = self.fossil_gas_import_flows + self.biomethane_import_flows
        self.demand_el_flows = self.demand_el_flows + self.p2h_el_flows + self.bhp_el_flow

        self.energy_system = energy_system
        self.model = model

    def aggregate_flows(self, flows_to_aggregate):
        """
        In the initialisation several lists are created which contain energy flows
        of certain kinds (e.g. self.pv_flows or self.th_demand_flows). To aggregate
        those timeseries to a joint timeseries you can use this function.

        :param flows_to_aggregate: List of string tuples describing the flows to aggregate
        :return: Aggregates timeseries
        """
        res = np.zeros(self.number_of_time_steps)
        for flow in flows_to_aggregate:
            res += self.energy_system.results['main'][flow][
                'sequences']['flow']

        return res

    def operational_costs(self):
        """
        Extracts costs from the optimiser
        """
        costs = self.energy_system.results["meta"]['objective']

        for flow in self.virtual_costs_flows:
            costs -= HIGH_VIRTUAL_COSTS * self.energy_system.results['main'][flow][
                'sequences']['flow'].sum()

        return costs

    def co2_emission(self):
        """
        Calculates the CO2 Emission acc. to
        https://doi.org/10.3390/en13112967

        :return: CO2 emission in operation as timeseries
        """
        fossil_gas_import = self.aggregate_flows(self.fossil_gas_import_flows)
        biomethane_import = self.aggregate_flows(self.biomethane_import_flows)
        pellet_import = self.aggregate_flows(self.pellet_import_flows)
        el_import = self.aggregate_flows(self.electricity_import_flows)
        el_export = self.aggregate_flows(self.electricity_export_flows)

        co2_import_fossil_gas = fossil_gas_import * self.spec_co2['fossil_gas']
        co2_import_biomethane = biomethane_import * self.spec_co2['biomethane']
        co2_import_pellet = pellet_import * HHV_WP * self.spec_co2['wood_pellet']
        co2_import_el = el_import * self.spec_co2['el_in']
        co2_export_el = el_export * self.spec_co2['el_out']

        co2_emission = (co2_import_fossil_gas.sum() +
                        co2_import_biomethane.sum() +
                        co2_import_el.sum() +
                        co2_import_pellet.sum() +
                        co2_export_el.sum())

        return np.round(co2_emission, 1)

    def own_consumption(self):
        """
        Calculates the own consumption of distributed generation

        :return: Own consumption
        """
        el_production = self.aggregate_flows(self.production_el_flows).sum()
        el_export = self.aggregate_flows(self.electricity_export_flows).sum()

        if el_production > 0:
            oc = 1 - (el_export / el_production)
        else:
            oc = 1
        return np.round(oc, 3)

    def self_sufficiency(self):
        """
        Calculates the self sufficiency of the district

        :return: Self sufficiency
        """
        el_import = self.aggregate_flows(self.electricity_import_flows).sum()
        el_demand = self.aggregate_flows(self.demand_el_flows).sum()

        res = 1 - (el_import / el_demand)
        return np.round(res, 3)
