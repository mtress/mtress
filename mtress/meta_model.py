# -*- coding: utf-8 -*-

"""
Generic model to be used to model residential energy supply systems

SPDX-FileCopyrightText: Deutsches Zentrum für Luft und Raumfahrt
SPDX-FileCopyrightText: kehag Energiehandel GMbH
SPDX-FileCopyrightText: Patrik Schönfeldt
SPDX-FileCopyrightText: Lucas Schmeling
SPDX-FileCopyrightText: Steffen Wehkamp

SPDX-License-Identifier: MIT
"""

import numbers

from copy import deepcopy
import pprint
import numpy as np
import pandas as pd

from oemof.solph import (Bus, EnergySystem, Flow, Sink, Source, Transformer,
                         Model, Investment, constraints, GenericStorage,
                         NonConvex, views)
from oemof.solph.processing import meta_results, results

from mtress.layered_heat import (HeatLayers, LayeredHeatPump,
                                 MultiLayerStorage, HeatExchanger)
from mtress.physics import (HHV_WP, H2O_HEAT_FUSION, H2O_DENSITY)

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

        ## Unpack non-technology kwargs
        self.meteo = kwargs.pop('meteorology')
        self.temps = kwargs.pop('temperatures')
        self.energy_cost = kwargs.pop('energy_cost')
        self.demand = kwargs.pop('demand')
        self.spec_co2 = kwargs.pop('co2')
        self.allow_missing_heat = kwargs.pop('allow_missing_heat', False)
        self.exclusive_grid_connection = kwargs.pop(
            'exclusive_grid_connection', True)

        # Create relevant temperature list
        temperature_levels = self.temps.get('additional', list())
        temperature_levels.append(self.temps['forward_flow'])
        temperature_levels.append(self.temps['backward_flow'])

        # Ensure unique temperatures
        temperature_levels = list(set(temperature_levels))
        temperature_levels.sort()
        self.temperature_levels = temperature_levels

        # Time range of the data (in a)
        index = self.demand['heating'].index
        self.number_of_time_steps = len(index)
        index.freq = pd.infer_freq(index)
        self.time_range = ((index[-1] - index[0] + index.freq)
                           / pd.Timedelta('365D'))

        self.energy_cost["electricity"]["market"] = _array(
            data=self.energy_cost["electricity"]["market"],
            length=self.number_of_time_steps)

        for quantity in ["el_in", "el_out"]:
            self.spec_co2[quantity] = _array(data=self.spec_co2[quantity],
                                             length=self.number_of_time_steps)

        ############################
        # Create energy system model
        ############################
        energy_system = EnergySystem(timeindex=self.demand['heating'].index)

        # list of flows to identify different sources and sinks later
        # which use units of power
        self.demand_th_flows = list()
        self.demand_el_flows = list()

        self.fossil_gas_import_flows = list()
        self.biomethane_import_flows = list()
        self.pellet_import_flows = list()
        self.electricity_import_flows = list()
        self.electricity_export_flows = list()

        self.grid_el_flows = list()
        self.adjacent_renewable_flows = list()
        self.pv_el_flows = list()
        self.pv_export_flows = list()
        self.wt_el_flows = list()
        self.wt_export_flows = list()
        self.chp_gas_flows = list()
        self.chp_th_flows = list()
        self.chp_el_flows = list()
        self.chp_el_funded_flows = list()
        self.chp_export_funded_flows = list()
        self.chp_el_unfunded_flows = list()
        self.chp_export_unfunded_flows = list()
        self.ahp_th_flows = list()
        self.ahp_el_flows = list()
        self.bhp_th_flows = list()
        self.bhp_el_flows = list()
        self.p2h_th_flows = list()
        self.p2h_el_flows = list()
        self.boiler_th_flows = list()
        self.pellet_th_flows = list()
        self.solar_thermal_th_flows = list()
        self.geothermal_input_flows = list()

        self.battery_inflows = list()
        self.battery_outflows = list()
        self.battery_content = list()

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
                           variable_costs=self.energy_cost[
                               'electricity']['eeg_levy'])})
        b_elxprt = Bus(label="b_elxprt")  # electricity export network
        b_elgrid = Bus(label="b_elgrid")

        # bus for adjacent renewable sources
        b_el_adjacent = Bus(
            label="b_el_adjacent",
            inputs={b_elgrid: Flow()},
            outputs={b_elgrid: Flow()}
        )

        energy_system.add(b_eldist, b_elprod, b_elxprt, b_elgrid,
                          b_el_adjacent)

        m_el_in = Source(
            label='m_el_in',
            outputs={b_el_adjacent: Flow(
                variable_costs=1e-9,
            )})
        self.grid_el_flows.append((m_el_in.label, b_el_adjacent.label))

        energy_system.add(m_el_in)

        if 'adjacent_renewables' in kwargs:
            s_el_adjacent = Source(
                label='s_el_adjacent',
                outputs={b_el_adjacent: Flow(
                    max=kwargs.pop('adjacent_renewables'),
                    nominal_value=1
                )}
            )
            self.adjacent_renewable_flows.append(
                (s_el_adjacent.label, b_el_adjacent.label)
            )
            energy_system.add(s_el_adjacent)

        if 'electricity_adjacent' in self.demand:
            d_el_adjacent = Sink(
                label='d_el_adjacent',
                inputs={b_el_adjacent: Flow(
                    fix=self.demand['electricity_adjacent'],
                    nominal_value=1
                )}
            )
            energy_system.add(d_el_adjacent)

        # (unidirectional) grid connection
        # RLM customer for district and larger buildings
        self.grid_connection_in_costs = (
                self.energy_cost['electricity']['surcharge']
                + self.energy_cost['electricity']['eeg_levy']
                + self.energy_cost['electricity']['market']
                + self.spec_co2['el_in']
                * self.spec_co2['price_el'])

        b_grid_connection_in = Bus(
            label="b_grid_connection_in",
            inputs={b_el_adjacent: Flow(
                variable_costs=self.grid_connection_in_costs,
                investment=Investment(
                    ep_costs=self.energy_cost['electricity'][
                                 'demand_rate'] * self.time_range))},
            outputs={b_eldist: Flow(nonconvex=NonConvex(),
                                    nominal_value=1e5,
                                    grid_connection=True)})

        self.electricity_import_flows.append((b_el_adjacent.label,
                                              b_grid_connection_in.label))

        # create external market to sell electricity to
        b_grid_connection_out = Bus(
            label="b_grid_connection_out",
            inputs={b_elxprt: Flow(nonconvex=NonConvex(),
                                   nominal_value=1e5,
                                   grid_connection=True)})

        energy_system.add(b_grid_connection_in, b_grid_connection_out)

        m_el_out = Sink(label='m_el_out',
                        inputs={b_grid_connection_out: Flow()})
        self.electricity_export_flows.append((b_grid_connection_out.label,
                                              m_el_out.label))

        # Create gas buses if needed
        b_fossil_gas = Bus(label="b_fossil_gas")
        if ('gas_boiler' in kwargs
                or ('chp' in kwargs
                    and kwargs['chp']['biomethane_fraction'] < 1)):

            gas_price = (self.energy_cost['gas']['fossil_gas']
                         + self.spec_co2['fossil_gas']
                         * self.spec_co2['price_gas'])
            m_fossil_gas = Source(
                label='m_fossil_gas',
                outputs={b_fossil_gas: Flow(variable_costs=gas_price)})

            self.fossil_gas_import_flows.append((m_fossil_gas.label,
                                                 b_fossil_gas.label))

            energy_system.add(b_fossil_gas, m_fossil_gas)

        if 'chp' in kwargs and kwargs['chp']['biomethane_fraction'] > 0:
            b_biomethane = Bus(label='b_biomethane')

            biomethane_price = self.energy_cost['gas']['biomethane']
            m_biomethane = Source(
                label='m_biomethane',
                outputs={b_biomethane: Flow(variable_costs=biomethane_price)})
            energy_system.add(m_biomethane, b_biomethane)

            self.biomethane_import_flows.append((m_biomethane.label,
                                                 b_biomethane.label))

        # Create wood pellet buses if needed
        if 'pellet_boiler' in kwargs:
            b_pellet = Bus(label="b_pellet")
            m_pellet = Source(
                label='m_pellet',
                outputs={b_pellet: Flow(
                    variable_costs=self.energy_cost['wood_pellet'])})
            self.pellet_import_flows.append((m_pellet.label, b_pellet.label))

            energy_system.add(b_pellet, m_pellet)

        ###################################################################
        # Thermal components
        heat_layers = HeatLayers(energy_system=energy_system,
                                 temperature_levels=temperature_levels,
                                 reference_temperature=self.temps['reference'])

        # Heat Storage
        if 'heat_storage' in kwargs and kwargs["heat_storage"]["volume"] > 0:
            hs = kwargs.pop('heat_storage')
            self._thermal_storage = MultiLayerStorage(
                diameter=hs['diameter'],
                volume=hs['volume'],
                insulation_thickness=hs['insulation_thickness'],
                ambient_temperature=self.meteo['temp_air'],
                heat_layers=heat_layers)
            self.th_storage_inflows = self._thermal_storage.in_flows.values()
            self.th_storage_outflows = self._thermal_storage.out_flows.values()
            self.th_storage_content = self._thermal_storage.content.values()
        else:
            self._thermal_storage = None

        ####################################################################

        if "air_source_heat_pump" in kwargs:
            ahp = kwargs.pop("air_source_heat_pump")
            assert ahp['electric_input'] >= 0

            b_el_ahp = Bus(
                label='b_el_ahp',
                inputs={b_eldist: Flow(nominal_value=ahp['electric_input'])})
            energy_system.add(b_el_ahp)
            if 'thermal_output' not in ahp:
                ahp['thermal_output'] = None
            air_heat_pump = LayeredHeatPump(
                heat_layers=heat_layers,
                electricity_source=b_el_ahp,
                thermal_power_limit=ahp['thermal_output'],
                heat_sources={"air": self.meteo['temp_air']},
                cop_0_35=ahp["cop_0_35"],
                label="air_heat_pump")

            b_ahp = Bus(label="b_ahp",
                        outputs={air_heat_pump.b_th_in["air"]: Flow()})
            s_shp = Source(label="s_ahp", outputs={b_ahp: Flow()})

            energy_system.add(s_shp, b_ahp)

            self.ahp_th_flows.extend(air_heat_pump.heat_out_flows)
            self.ahp_el_flows.append((b_eldist.label,
                                      b_el_ahp.label))
        else:
            air_heat_pump = None

        # Heat pump
        if "heat_pump" in kwargs:
            bhp = kwargs.pop("heat_pump")
            assert bhp['electric_input'] >= 0
            heat_sources = dict()
            if 'ice_storage' in kwargs:
                heat_sources["ice"] = 0
            if 'near_surface_heat_source' in kwargs:
                heat_sources["soil"] = self.meteo['temp_soil']
            if 'geothermal_heat_source' in kwargs:
                heat_sources["sonde"] = kwargs[
                    'geothermal_heat_source']['temperature']
            if 'thermal_ground_storage' in kwargs:
                heat_sources["pit_storage"] = kwargs[
                    'thermal_ground_storage']['temperature']

            if len(heat_sources) > 0:
                b_el_bhp = Bus(
                    label='b_el_bhp',
                    inputs={
                        b_eldist: Flow(nominal_value=bhp['electric_input'])})
                energy_system.add(b_el_bhp)
                if 'thermal_output' not in bhp:
                    bhp['thermal_output'] = None
                heat_pump = LayeredHeatPump(
                    heat_layers=heat_layers,
                    electricity_source=b_el_bhp,
                    thermal_power_limit=bhp['thermal_output'],
                    heat_sources=heat_sources,
                    cop_0_35=bhp["cop_0_35"],
                    label="brine_heat_pump")

                self.bhp_th_flows.extend(heat_pump.heat_out_flows)
                self.bhp_el_flows.append((b_eldist.label,
                                          b_el_bhp.label))
            else:
                heat_pump = None
            self.heat_pump = heat_pump
            # heat pump sources
            # near surface source
            if 'near_surface_heat_source' in kwargs:
                shp = kwargs.pop('near_surface_heat_source')
                b_shp = Bus(label="b_bhp",
                            outputs={heat_pump.b_th_in["soil"]: Flow()})
                s_shp = Source(
                    label="s_shp",
                    outputs={b_shp: Flow(nominal_value=shp['thermal_output'])})

                self.geothermal_input_flows.append((s_shp.label, b_shp.label))
                energy_system.add(s_shp, b_shp)

            # deep geothermal
            if ('geothermal_heat_source' in kwargs
                    and kwargs[
                        'geothermal_heat_source']['thermal_output'] > 0):
                ghp = kwargs.pop('geothermal_heat_source')
                b_ghp = Bus(label="b_ghp",
                            outputs={heat_pump.b_th_in["sonde"]: Flow()})
                s_ghp = Source(
                    label="s_ghp",
                    outputs={b_ghp: Flow(nominal_value=ghp['thermal_output'])})

                self.geothermal_input_flows.append((s_ghp.label, b_ghp.label))
                energy_system.add(s_ghp, b_ghp)

            ###################################################################
            # Ice storage
            if 'ice_storage' in kwargs and kwargs['ice_storage']['volume'] > 0:
                ihs = kwargs.pop('ice_storage')
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
            else:
                ihs = None

            if ('thermal_ground_storage' in kwargs
                    and kwargs['thermal_ground_storage']['volume'] > 0):
                tgs = kwargs.pop('thermal_ground_storage')
                b_tgs = Bus(label='b_tgs',
                            inputs={heat_layers.b_th_lowest: Flow()},
                            outputs={heat_pump.b_th_in["pit_storage"]: Flow()})
                s_tgs = GenericStorage(
                    label='s_tgs',
                    nominal_storage_capacity=tgs['heat_capacity'],
                    inputs={b_tgs: Flow()},
                    outputs={b_tgs: Flow()})
                energy_system.add(s_tgs, b_tgs)
            else:
                tgs = None
        else:
            self.heat_pump = None
            tgs = None
            ihs = None

        ###############################################################
        # Solar thermal

        if 'solar_thermal' in kwargs and kwargs['solar_thermal']['area'] > 0:
            st = kwargs.pop('solar_thermal')
            b_st = Bus(label="b_st")
            s_st = Source(label="s_st",
                          outputs={b_st: Flow(nominal_value=1)})

            energy_system.add(s_st, b_st)

            if (tgs and tgs["temperature"]
                    not in heat_layers.temperature_levels):
                temp = tgs["temperature"]
                temp_str = "{0:.0f}".format(temp)
                st_level_label = 't_st_' + temp_str
                t_st_level = Transformer(
                    label=st_level_label,
                    inputs={b_st: Flow(nominal_value=st["area"])},
                    outputs={b_tgs: Flow(nominal_value=1)},
                    conversion_factors={
                        b_tgs: (st['spec_generation'][
                            'ST_' + str(temp)]).to_list()})

                self.solar_thermal_th_flows.append((st_level_label,
                                                    b_tgs.label))
                energy_system.add(t_st_level)

            if ihs and 0 not in heat_layers.temperature_levels:
                temp = 0
                temp_str = "{0:.0f}".format(temp)
                st_level_label = 't_st_' + temp_str
                t_st_level = Transformer(
                    label=st_level_label,
                    inputs={b_st: Flow(nominal_value=st["area"])},
                    outputs={b_ihs: Flow(nominal_value=1)},
                    conversion_factors={
                        b_ihs: _array(
                            st['spec_generation']['ST_' + str(temp)],
                            self.number_of_time_steps)})

                self.solar_thermal_th_flows.append((st_level_label,
                                                    b_ihs.label))
                energy_system.add(t_st_level)

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
                        b_th_in_level: _array(
                            st['spec_generation']['ST_' + str(temp)],
                            self.number_of_time_steps)})

                self.solar_thermal_th_flows.append((st_level_label,
                                                    b_th_in_level.label))
                energy_system.add(t_st_level)

        # electricity demands covered of the local electricity network
        d_el_local = Sink(
            label='d_el_local',
            inputs={b_eldist: Flow(fix=self.demand['electricity'],
                                   nominal_value=1)})

        self.demand_el_flows.append((b_eldist.label,
                                     d_el_local.label))

        # create building heat
        b_th_buildings = Bus(label="b_th_buildings")
        energy_system.add(b_th_buildings)

        self.heat_exchanger_buildings = HeatExchanger(
            heat_layers=heat_layers,
            heat_demand=b_th_buildings,
            label="heat_exchanger",
            forward_flow_temperature=self.temps['forward_flow'],
            backward_flow_temperature=(self.temps['backward_flow']))

        d_sh = Sink(label='d_sh',
                    inputs={b_th_buildings: Flow(
                        fix=self.demand['heating'],
                        nominal_value=1)})
        self.demand_th_flows.append((b_th_buildings.label,
                                     d_sh.label))
        energy_system.add(d_sh)

        if sum(self.demand['dhw'] > 0):
            b_th_dhw_local = Bus(label="b_th_dhw_local")

            d_dhw = Sink(label='d_dhw',
                         inputs={b_th_dhw_local: Flow(
                             fix=self.demand['dhw'],
                             nominal_value=1)})
            self.demand_th_flows.append((b_th_dhw_local.label,
                                         d_dhw.label))

            energy_system.add(b_th_dhw_local, d_dhw)

            # We assume a heat drop but no energy loss
            # due to the heat exchanger.
            heater_ratio = ((max(heat_layers.temperature_levels)
                             - self.temps['heat_drop_exchanger_dhw']
                             - self.temps['reference'])
                            / (self.temps['dhw'] - self.temps['reference']))

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
                # The following flow marks the heat added by the booster.
                # Assuming 100 % efficiency fo the (electric) booster.
                self.p2h_th_flows.append((b_eldist.label,
                                          dhw_booster.label))
            else:
                dhw_booster = Bus(label="dhw_booster",
                                  inputs={b_th_buildings: Flow()},
                                  outputs={b_th_dhw_local: Flow()})

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

        # gas_boiler
        if ('gas_boiler' in kwargs
                and kwargs['gas_boiler']["thermal_output"] > 0):
            gas_boiler = kwargs.pop('gas_boiler')
            t_boiler = Transformer(
                label='t_boiler',
                inputs={b_fossil_gas: Flow()},
                outputs={
                    heat_layers.b_th_in_highest:
                        Flow(nominal_value=gas_boiler['thermal_output'])},
                conversion_factors={
                    heat_layers.b_th_in_highest:
                        gas_boiler['efficiency']})

            self.boiler_th_flows.append((t_boiler.label,
                                         heat_layers.b_th_in_highest.label))
            energy_system.add(t_boiler)

        # wood pellet gas_boiler
        if ('pellet_boiler' in kwargs
                and kwargs['pellet_boiler']['thermal_output'] > 0):
            pellet_boiler = kwargs.pop('pellet_boiler')
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

        # CHP
        if 'chp' in kwargs and kwargs['chp']['electric_output'] > 0:
            chp = kwargs.pop('chp')
            # According to § 7 Abs. 6 KWKG
            subsidised_timesteps = deepcopy(
                self.energy_cost['electricity']['market'])
            subsidised_timesteps[subsidised_timesteps > 0] = 1
            subsidised_timesteps[subsidised_timesteps <= 0] = 0

            self.chp_revenue_funded = (
                self.energy_cost['electricity']['market']
                + subsidised_timesteps * chp['feed_in_subsidy'])
            self.chp_revenue_unfunded = self.energy_cost[
                'electricity']['market']

            b_gas_chp = Bus(label='b_gas_chp')

            if chp['biomethane_fraction'] == 1:
                t_gas_chp = Transformer(label="t_gas_chp",
                                        inputs={b_biomethane: Flow()},
                                        outputs={b_gas_chp: Flow()})
            elif chp['biomethane_fraction'] == 0:
                t_gas_chp = Transformer(label="t_gas_chp",
                                        inputs={b_fossil_gas: Flow()},
                                        outputs={b_gas_chp: Flow()})
            else:
                t_gas_chp = Transformer(
                    label="t_gas_chp",
                    inputs={b_fossil_gas: Flow(),
                            b_biomethane: Flow()},
                    outputs={b_gas_chp: Flow()},
                    conversion_factors={
                        b_fossil_gas: 1 - chp['biomethane_fraction'],
                        b_biomethane: chp['biomethane_fraction']})
            energy_system.add(t_gas_chp, b_gas_chp)

            b_el_chp_fund = Bus(
                label="b_el_chp_fund",
                outputs={
                    b_elxprt: Flow(
                        variable_costs=-(self.chp_revenue_funded)),
                    b_elprod: Flow(
                        variable_costs=-(subsidised_timesteps
                                         * chp['own_consumption_subsidy']))})

            self.chp_export_funded_flows.append((b_el_chp_fund.label,
                                                 b_elxprt.label))

            b_el_chp_unfund = Bus(
                label="b_el_chp_unfund",
                outputs={
                    b_elxprt: Flow(
                        variable_costs=-self.chp_revenue_unfunded),
                    b_elprod: Flow()})
            self.chp_export_unfunded_flows.append((b_el_chp_unfund.label,
                                                   b_elxprt.label))

            b_el_chp = Bus(label="b_el_chp",
                           outputs={
                               b_el_chp_fund: Flow(
                                   summed_max=chp['funding_hours_per_year'],
                                   nominal_value=chp['electric_output']),
                               b_el_chp_unfund: Flow()})
            self.chp_el_funded_flows.append((b_el_chp.label,
                                             b_el_chp_fund.label))
            self.chp_el_unfunded_flows.append((b_el_chp.label,
                                               b_el_chp_unfund.label))
            energy_system.add(b_el_chp_fund, b_el_chp_unfund, b_el_chp)

            t_chp = Transformer(
                label='t_chp',
                inputs={b_gas_chp: Flow(
                    nominal_value=chp['gas_input'],
                    variable_costs=-self.energy_cost['gas']['energy_tax'])},
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
        else:
            self.chp_revenue_funded = 0
            self.chp_revenue_unfunded = 0

        # PV
        if 'pv' in kwargs and kwargs['pv']['nominal_power'] > 0:
            pv = kwargs.pop('pv')
            self.pv_revenue = pv['feed_in_subsidy']
            b_el_pv = Bus(
                label="b_el_pv",
                outputs={
                    b_elxprt: Flow(variable_costs=-self.pv_revenue),
                    b_elprod: Flow()})

            self.pv_export_flows.append((b_el_pv.label, b_elxprt.label))

            t_pv = Source(
                label='t_pv',
                outputs={
                    b_el_pv: Flow(nominal_value=pv["nominal_power"],
                                  max=pv['spec_generation'])})
            self.pv_el_flows.append((t_pv.label, b_el_pv.label))

            energy_system.add(t_pv, b_el_pv)
        else:
            self.pv_revenue = 0

        # Power to Heat
        if ('power_to_heat' in kwargs
                and kwargs['power_to_heat']['thermal_output'] > 0):
            p2h = kwargs.pop('power_to_heat')
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
            self.p2h_th_flows.append((t_p2h.label,
                                      heat_layers.b_th_in_highest.label))

        # Wind Turbine
        if 'wind_turbine' in kwargs \
                and kwargs['wind_turbine']['nominal_power'] > 0:
            wind_turbine = kwargs.pop('wind_turbine')
            self.wt_revenue = wind_turbine['feed_in_subsidy']
            b_el_wt = Bus(
                label="b_el_wt",
                outputs={
                    b_elxprt: Flow(variable_costs=-self.wt_revenue),
                    b_elprod: Flow()})

            self.wt_export_flows.append((b_el_wt.label, b_elxprt.label))

            t_wt = Source(
                label='t_wt',
                outputs={
                    b_el_wt: Flow(
                        nominal_value=wind_turbine["nominal_power"],
                        max=wind_turbine['spec_generation'])})
            self.wt_el_flows.append((t_wt.label, b_el_wt.label))

            energy_system.add(t_wt, b_el_wt)
        else:
            self.wt_revenue = 0

        # Battery
        if 'battery' in kwargs and kwargs['battery']['capacity'] > 0:
            battery = kwargs.pop('battery')
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
            self.battery_content.append((s_battery.label, None))
            self.battery_inflows.append((b_elprod.label, s_battery.label))
            self.battery_outflows.append((s_battery.label, b_elprod.label))

        model = Model(energy_system)

        if self._thermal_storage:
            self._thermal_storage.add_shared_limit(model=model)

        if self.exclusive_grid_connection:
            # Check if simultaneous  feed in
            # and feed out might occur due to expediencies
            expendency_pv = max(self.pv_revenue
                                - self.grid_connection_in_costs)
            expendency_wt = max(self.wt_revenue
                                - self.grid_connection_in_costs)
            expendency_chp = max(self.chp_revenue_funded
                                 - self.grid_connection_in_costs)
            max_expendency = max([expendency_chp,
                                  expendency_pv,
                                  expendency_wt])

            # Only activate exclusive grid connection
            # if such situations might occur
            if max_expendency >= 0:
                constraints.limit_active_flow_count_by_keyword(
                    model,
                    "grid_connection",
                    lower_limit=0,
                    upper_limit=1)

        self.production_el_flows = (self.wt_el_flows
                                    + self.pv_el_flows
                                    + self.chp_el_flows)
        self.gas_flows = (self.fossil_gas_import_flows
                          + self.biomethane_import_flows)
        self.demand_el_flows = (self.demand_el_flows
                                + self.p2h_el_flows
                                + self.ahp_el_flows
                                + self.bhp_el_flows)

        self.energy_system = energy_system
        self.model = model
        if len(kwargs) > 0:
            print(10*"#")
            print("Unhandled arguments while initialising MTRESS:")
            pprint.pprint(kwargs)
            print(10 * "#")

        # variables for net import/export
        self._raw_electricity_import = None
        self._raw_electricity_export = None
        self._electricity_export = None
        self._electricity_import = None

    def aggregate_flows(self, flows_to_aggregate):
        """
        In the initialisation several lists are created which contain
        energy flows of certain kinds (e.g. self.pv_flows or
        self.th_demand_flows). To aggregate those timeseries to a joint
        timeseries you can use this function.

        :param flows_to_aggregate: List of string tuples describing the
               flows to aggregate
        :return: numpy array with aggregated time series
        """
        res = np.zeros(self.number_of_time_steps)
        for flow in flows_to_aggregate:
            res += self.energy_system.results['main'][flow][
                'sequences']['flow'].to_numpy()

        return res

    def _calc_energy_balance(self):
        """
        calculate exclusive export or import
        """
        self._raw_electricity_import = self.aggregate_flows(
            self.electricity_import_flows)
        self._raw_electricity_export = self.aggregate_flows(
            self.electricity_export_flows)
        electricity_balance = (self._raw_electricity_export
                               - self._raw_electricity_import)
        self._electricity_export = electricity_balance.copy()
        self._electricity_export[electricity_balance < 0] = 0
        self._electricity_import = -electricity_balance
        self._electricity_import[electricity_balance >= 0] = 0

    def operational_costs(self, feed_in_order=None):
        """
        Extracts costs from the optimiser

        :param feed_in_order: list of dicts
                    [{"revenue": revenue for feed-in,
                      "flows": lists of respective flows}]
        """
        costs = self.energy_system.results["meta"]['objective']

        for flow in self.virtual_costs_flows:
            costs -= HIGH_VIRTUAL_COSTS * self.energy_system.results[
                'main'][flow]['sequences']['flow'].sum()

        if feed_in_order is not None:
            self._calc_energy_balance()
            # calculate wrong numbers (selling not only excess electricity)
            wrong_import_costs = np.multiply(self._raw_electricity_import,
                                             self.grid_connection_in_costs)
            wrong_wt_revenue = self.wt_revenue * self.aggregate_flows(
                self.wt_export_flows)
            wrong_pv_revenue = self.pv_revenue * self.aggregate_flows(
                self.pv_export_flows)
            wrong_chp_revenue = (
                    self.chp_revenue_funded
                    * self.aggregate_flows(self.chp_export_funded_flows)
                    + self.chp_revenue_unfunded
                    * self.aggregate_flows(self.chp_export_unfunded_flows))
            wrong_export_revenue = (wrong_wt_revenue
                                    + wrong_pv_revenue
                                    + wrong_chp_revenue)

            # subtract wrong costs
            costs = (costs
                     - wrong_import_costs.sum()
                     + wrong_export_revenue.sum())

            import_costs = (self._electricity_import
                            * self.grid_connection_in_costs)

            electricity_export = deepcopy(self._electricity_export)
            export_revenue = 0.0
            for feed_in in feed_in_order:
                feed_in_flows = feed_in["flows"]
                export_flow = self.aggregate_flows(feed_in_flows)
                export_revenue += sum(feed_in["revenue"] * np.minimum(
                    electricity_export, export_flow))
                electricity_export -= export_flow
                electricity_export[electricity_export < 0] = 0

            # add correct costs
            costs = costs + import_costs.sum() - export_revenue

        return costs

    def co2_emission(self, accuracy=1):
        """
        Calculates the CO2 Emission acc. to
        https://doi.org/10.3390/en13112967

        :return: CO2 emission in operation as timeseries
        """
        self._calc_energy_balance()

        fossil_gas_import = self.aggregate_flows(self.fossil_gas_import_flows)
        biomethane_import = self.aggregate_flows(self.biomethane_import_flows)
        pellet_import = self.aggregate_flows(self.pellet_import_flows)

        co2_import_fossil_gas = fossil_gas_import * self.spec_co2['fossil_gas']
        co2_import_biomethane = biomethane_import * self.spec_co2['biomethane']
        co2_import_pellet = (pellet_import * HHV_WP
                             * self.spec_co2['wood_pellet'])

        electricity_from_grid = self.aggregate_flows(self.grid_el_flows)
        electricity_from_adjacent = self.aggregate_flows(
            self.adjacent_renewable_flows)
        grid_electricity_fraction = (
            electricity_from_grid
            / (electricity_from_adjacent
               + electricity_from_grid
               + 1e-10)
        )
        co2_import_el = (self._electricity_import
                         * grid_electricity_fraction
                         * self.spec_co2['el_in'])
        co2_export_el = (self._electricity_export
                         * grid_electricity_fraction
                         * self.spec_co2['el_out'])

        co2_emission = (co2_import_fossil_gas.sum()
                        + co2_import_biomethane.sum()
                        + co2_import_el.sum()
                        + co2_import_pellet.sum()
                        - co2_export_el.sum())

        return np.round(co2_emission, accuracy)

    def own_consumption(self):
        """
        Calculates the own consumption of distributed generation

        :return: Own consumption
        """
        self._calc_energy_balance()
        el_production = sum(self.aggregate_flows(self.production_el_flows))

        own_consumption = 1 - sum(self._electricity_export)/el_production

        return np.round(own_consumption, 3)

    def self_sufficiency(self):
        """
        Calculates the self sufficiency of the district

        :return: Self sufficiency
        """
        self._calc_energy_balance()
        el_demand = sum(self.aggregate_flows(self.demand_el_flows))

        self_sufficiency = 1 - sum(self._electricity_import)/el_demand

        return np.round(self_sufficiency, 3)

    def solve(self,
              solver="cbc",
              solve_kwargs=None,
              cmdline_options=None):
        """
        solves the model and puts results to expected locations
        """
        if cmdline_options is None:
            cmdline_options = {'ratio': 0.01}
        if solve_kwargs is None:
            solve_kwargs = {'tee': False}
        self.model.solve(solver=solver,
                         solve_kwargs=solve_kwargs,
                         solver_io='lp',
                         cmdline_options=cmdline_options)

        # store result data in common positions
        self.energy_system.results['meta'] = meta_results(self.model)
        self.energy_system.results['main'] = results(self.model)
        self.energy_system.results['main'] = views.convert_keys_to_strings(
            self.energy_system.results['main'])
