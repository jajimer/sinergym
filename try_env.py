import gymnasium as gym
import numpy as np

import sinergym
from sinergym.utils.wrappers import (
    LoggerWrapper,
    NormalizeAction,
    NormalizeObservation,
    IncrementalWrapper,
    RoundActionWrapper,
    ExtremeFlowControlWrapper,
    ReduceObservationWrapper)

# Creating environment and applying wrappers for normalization and logging
env = gym.make(
    'Eplus-radiant_pump_flow_heating-stockholm-continuous-stochastic-v1')
# env = RoundActionWrapper(env)
env = ExtremeFlowControlWrapper(env)
env = NormalizeAction(env)
env = NormalizeObservation(env)
env = LoggerWrapper(env)
env = ReduceObservationWrapper(env, obs_reduction=[
    'radiant_hvac_outlet_temperature_living',
    'radiant_hvac_outlet_temperature_kitchen',
    'radiant_hvac_outlet_temperature_bed1',
    'radiant_hvac_outlet_temperature_bed2',
    'radiant_hvac_outlet_temperature_bed3',
    'surface_internal_source_location_temperature_living',
    'surface_internal_source_location_temperature_kitchen',
    'surface_internal_source_location_temperature_bed1',
    'surface_internal_source_location_temperature_bed2',
    'surface_internal_source_location_temperature_bed3',
    'surface_internal_user_specified_location_temperature_living',
    'surface_internal_user_specified_location_temperature_kitchen',
    'surface_internal_user_specified_location_temperature_bed1',
    'surface_internal_user_specified_location_temperature_bed2',
    'surface_internal_user_specified_location_temperature_bed3',
    'people_occupant_living',
    'people_occupant_kitchen',
    'people_occupant_bed1',
    'people_occupant_bed2',
    'people_occupant_bed3',
    'thermal_comfort_mean_radiant_temperature_living',
    'thermal_comfort_mean_radiant_temperature_kitchen',
    'thermal_comfort_mean_radiant_temperature_bed1',
    'thermal_comfort_mean_radiant_temperature_bed2',
    'thermal_comfort_mean_radiant_temperature_bed3',
    'thermal_comfort_clothing_value_living',
    'thermal_comfort_clothing_value_kitchen',
    'thermal_comfort_clothing_value_bed1',
    'thermal_comfort_clothing_value_bed2',
    'thermal_comfort_clothing_value_bed3',
    'thermal_comfort_fanger_model_ppd_living',
    'thermal_comfort_fanger_model_ppd_kitchen',
    'thermal_comfort_fanger_model_ppd_bed1',
    'thermal_comfort_fanger_model_ppd_bed2',
    'thermal_comfort_fanger_model_ppd_bed3',
    'people_air_temperature_living',
    'people_air_temperature_kitchen',
    'people_air_temperature_bed1',
    'people_air_temperature_bed2',
    'people_air_temperature_bed3',
    'aquarea9kw_plr_performance_curve_output_value',
    'eeraquarea9kw_performance_curve_output_value',
    'coolcapaquarea9kw_performance_curve_output_value',
    'heat_pump_load_side_heat_transfer_rate',
    'heat_pump_load_side_mass_flow_rate'
])

# Execute interactions during 3 episodes
for i in range(1):
    # Reset the environment to start a new episode
    obs, info = env.reset()
    truncated = terminated = False

    while not (terminated or truncated):
        # Random action control
        a = env.action_space.sample()
        # Read observation and reward
        obs, reward, terminated, truncated, info = env.step(a)


# Close the environment
env.close()
