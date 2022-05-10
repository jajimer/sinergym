import pkg_resources
import os
import gym
import numpy as np

# ---------------------------------------------------------------------------- #
#                               Generic constants                              #
# ---------------------------------------------------------------------------- #
# Sinergym Data path
PKG_DATA_PATH = pkg_resources.resource_filename(
    'sinergym', 'data/')
# Weekday encoding for simulations
WEEKDAY_ENCODING = {'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
                    'friday': 4, 'saturday': 5, 'sunday': 6}
# Default start year (Non leap year please)
YEAR = 1991
# cwd
CWD = os.getcwd()

# ---------------------------------------------------------------------------- #
#                               Config class keys                              #
# ---------------------------------------------------------------------------- #
# Extra config keys (add keys in this list in order to assert them)
CONFIG_KEYS = ['timesteps_per_hour', 'runperiod', 'action_definition']
# Extra config action definition keys (add keys in this list in order to
# assert new controller types)
ACTION_DEFINITION_COMPONENTS = ['ThermostatSetpoint:DualSetpoint']

# ---------------------------------------------------------------------------- #
#                          Normalization dictionaries                          #
# ---------------------------------------------------------------------------- #
RANGES_5ZONE = {'Facility Total HVAC Electricity Demand Rate (Whole Building)': [173.6583692738386,
                                                                                 32595.57259261767],
                'People Air Temperature (SPACE1-1 PEOPLE 1)': [0.0, 30.00826655379267],
                'Site Diffuse Solar Radiation Rate per Area (Environment)': [0.0, 588.0],
                'Site Direct Solar Radiation Rate per Area (Environment)': [0.0, 1033.0],
                'Site Outdoor Air Drybulb Temperature (Environment)': [-31.05437255409474,
                                                                       60.72839186915495],
                'Site Outdoor Air Relative Humidity (Environment)': [3.0, 100.0],
                'Site Wind Direction (Environment)': [0.0, 357.5],
                'Site Wind Speed (Environment)': [0.0, 23.1],
                'Space1-ClgSetP-RL': [21.0, 30.0],
                'Space1-HtgSetP-RL': [15.0, 22.49999],
                'Zone Air Relative Humidity (SPACE1-1)': [3.287277410867238,
                                                          87.60662171287048],
                'Zone Air Temperature (SPACE1-1)': [15.22565264653451, 30.00826655379267],
                'Zone People Occupant Count (SPACE1-1)': [0.0, 11.0],
                'Zone Thermal Comfort Clothing Value (SPACE1-1 PEOPLE 1)': [0.0, 1.0],
                'Zone Thermal Comfort Fanger Model PPD (SPACE1-1 PEOPLE 1)': [0.0,
                                                                              98.37141259444684],
                'Zone Thermal Comfort Mean Radiant Temperature (SPACE1-1 PEOPLE 1)': [0.0,
                                                                                      35.98853496778508],
                'Zone Thermostat Cooling Setpoint Temperature (SPACE1-1)': [21.0, 30.0],
                'Zone Thermostat Heating Setpoint Temperature (SPACE1-1)': [15.0,
                                                                            22.49999046325684],
                'comfort_penalty': [-6.508266553792669, -0.0],
                'day': [1, 31],
                'done': [False, True],
                'hour': [0, 23],
                'month': [1, 12],
                'year': [1, 2022],
                'reward': [-3.550779087370951, -0.0086829184636919],
                'time (seconds)': [0, 31536000],
                'timestep': [0, 35040],
                'total_power_no_units': [-3.259557259261767, -0.0173658369273838]}

RANGES_IW = {
    "Site Outdoor Air Drybulb Temperature": [-13.0, 26.0],
    "Site Outdoor Air Relative Humidity": [0.0, 100.0],
    "Site Wind Speed": [0.0, 11.0],
    "Site Wind Direction": [0.0, 360.0],
    "Site Diffuse Solar Radiation Rate per Area": [0.0, 378.0],
    "Site Direct Solar Radiation Rate per Area": [0.0, 1000.0],
    "IW Hot Water System OA Enable Flag OA Setpoint": [-30.0, 30.0],
    "IW Average PPD": [0.0, 100.0],
    "IW Effective Zone Air Temperature Setpoint": [18.0, 25.0],
    "IW North Zone Average Temperature": [18.0, 25.0],
    "IW Effective IAT Setpoint by Logics": [18.0, 25.0],
    "IW Occupy Mode Flag": [0.0, 1.0],
    "IW Calculated Heating Demand": [0.0, 85.0],
    'day': [1.0, 31.0],
    'done': [False, True],
    'hour': [0.0, 23.0],
    'month': [1.0, 12.0],
    'year': [1.0, 2022.0],
}

RANGES_DATACENTER = {
    'East-ClgSetP-RL': [21.0, 30.0],
    'East-HtgSetP-RL': [15.0, 22.499973],
    'Facility Total HVAC Electricity Demand Rate (Whole Building)': [1763.7415,
                                                                     76803.016],
    'People Air Temperature (East Zone PEOPLE)': [0.0, 30.279287],
    'People Air Temperature (West Zone PEOPLE)': [0.0, 30.260946],
    'Site Diffuse Solar Radiation Rate per Area (Environment)': [0.0, 588.0],
    'Site Direct Solar Radiation Rate per Area (Environment)': [0.0, 1033.0],
    'Site Outdoor Air Drybulb Temperature (Environment)': [-16.049532, 42.0],
    'Site Outdoor Air Relative Humidity (Environment)': [3.0, 100.0],
    'Site Wind Direction (Environment)': [0.0, 357.5],
    'Site Wind Speed (Environment)': [0.0, 17.5],
    'West-ClgSetP-RL': [21.0, 30.0],
    'West-HtgSetP-RL': [15.0, 22.499998],
    'Zone Air Relative Humidity (East Zone)': [1.8851701, 67.184616],
    'Zone Air Relative Humidity (West Zone)': [1.8945858, 66.7946],
    'Zone Air Temperature (East Zone)': [21.003511, 30.279287],
    'Zone Air Temperature (West Zone)': [21.004263, 30.260946],
    'Zone People Occupant Count (East Zone)': [0.0, 7.0],
    'Zone People Occupant Count (West Zone)': [0.0, 11.0],
    'Zone Thermal Comfort Clothing Value (East Zone PEOPLE)': [0.0, 0.0],
    'Zone Thermal Comfort Clothing Value (West Zone PEOPLE)': [0.0, 0.0],
    'Zone Thermal Comfort Fanger Model PPD (East Zone PEOPLE)': [0.0, 66.75793],
    'Zone Thermal Comfort Fanger Model PPD (West Zone PEOPLE)': [0.0, 59.53962],
    'Zone Thermal Comfort Mean Radiant Temperature (East Zone PEOPLE)': [0.0,
                                                                         29.321169],
    'Zone Thermal Comfort Mean Radiant Temperature (West Zone PEOPLE)': [0.0,
                                                                         29.04933],
    'Zone Thermostat Cooling Setpoint Temperature (East Zone)': [21.0, 30.0],
    'Zone Thermostat Cooling Setpoint Temperature (West Zone)': [21.0, 30.0],
    'Zone Thermostat Heating Setpoint Temperature (East Zone)': [15.0, 22.499973],
    'Zone Thermostat Heating Setpoint Temperature (West Zone)': [15.0, 22.499998],
    'comfort_penalty': [-13.264959140712048, -0.0],
    'day': [1.0, 31.0],
    'done': [False, True],
    'hour': [0.0, 23.0],
    'month': [1.0, 12.0],
    'year': [1.0, 2022.0],
    'power_penalty': [-7.68030164869835, -0.1763741508343818],
    'reward': [-9.090902680780722, -0.0881870754171909],
    'time (seconds)': [0, 31536000],
    'timestep': [0, 35040]
}

# ---------------------------------------------------------------------------- #
#                       Default Eplus Environments values                      #
# ---------------------------------------------------------------------------- #

# -------------------------------------5ZONE---------------------------------- #

DEFAULT_5ZONE_OBSERVATION_VARIABLES = [
    'Site Outdoor Air Drybulb Temperature(Environment)',
    'Site Outdoor Air Relative Humidity(Environment)',
    'Site Wind Speed(Environment)',
    'Site Wind Direction(Environment)',
    'Site Diffuse Solar Radiation Rate per Area(Environment)',
    'Site Direct Solar Radiation Rate per Area(Environment)',
    'Zone Thermostat Heating Setpoint Temperature(SPACE1-1)',
    'Zone Thermostat Cooling Setpoint Temperature(SPACE1-1)',
    'Zone Air Temperature(SPACE1-1)',
    'Zone Thermal Comfort Mean Radiant Temperature(SPACE1-1 PEOPLE 1)',
    'Zone Air Relative Humidity(SPACE1-1)',
    'Zone Thermal Comfort Clothing Value(SPACE1-1 PEOPLE 1)',
    'Zone Thermal Comfort Fanger Model PPD(SPACE1-1 PEOPLE 1)',
    'Zone People Occupant Count(SPACE1-1)',
    'People Air Temperature(SPACE1-1 PEOPLE 1)',
    'Facility Total HVAC Electricity Demand Rate(Whole Building)'
]

DEFAULT_5ZONE_ACTION_VARIABLES = [
    'Space1-HtgSetP-RL',
    'Space1-ClgSetP-RL'
]

DEFAULT_5ZONE_OBSERVATION_SPACE = gym.spaces.Box(
    low=-5e6,
    high=5e6,
    shape=(len(DEFAULT_5ZONE_OBSERVATION_VARIABLES) + 4,),
    dtype=np.float32)

DEFAULT_5ZONE_ACTION_MAPPING = {
    0: (15, 30),
    1: (16, 29),
    2: (17, 28),
    3: (18, 27),
    4: (19, 26),
    5: (20, 25),
    6: (21, 24),
    7: (22, 23),
    8: (22, 22),
    9: (21, 21)
}

DEFAULT_5ZONE_ACTION_SPACE_DISCRETE = gym.spaces.Discrete(10)

DEFAULT_5ZONE_ACTION_SPACE_CONTINUOUS = gym.spaces.Box(
    low=np.array([15.0, 22.5]),
    high=np.array([22.5, 30.0]),
    shape=(2,),
    dtype=np.float32
)

DEFAULT_5ZONE_CONFIG_PARAMS = {
    'action_definition': {
        'ThermostatSetpoint:DualSetpoint': [{
            'name': 'Space1-DualSetP-RL',
            'heating_name': 'Space1-HtgSetP-RL',
            'cooling_name': 'Space1-ClgSetP-RL',
            'zones': ['space1-1']
        }]
    }
}
# ----------------------------------DATACENTER--------------------------------- #
DEFAULT_DATACENTER_OBSERVATION_VARIABLES = [
]

DEFAULT_DATACENTER_ACTION_VARIABLES = [
    'West-HtgSetP-RL',
    'West-ClgSetP-RL',
    'East-HtgSetP-RL',
    'East-ClgSetP-RL'
]

DEFAULT_DATACENTER_OBSERVATION_SPACE = gym.spaces.Box()

DEFAULT_DATACENTER_ACTION_MAPPING = {
}

DEFAULT_DATACENTER_ACTION_SPACE_DISCRETE = gym.spaces.Discrete()

DEFAULT_DATACENTER_ACTION_SPACE_CONTINUOUS = gym.spaces.Box(
)

DEFAULT_DATACENTER_CONFIG_PARAMS = {
}