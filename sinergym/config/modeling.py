"""Class and utilities for backend modeling in Python with Sinergym (extra params, weather_variability, building model modification and files management)"""
import json
import os
import random
import xml.etree.cElementTree as ElementTree
from abc import ABC, abstractmethod
from copy import deepcopy
from shutil import rmtree
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
from eppy.modeleditor import IDF
from opyplus import WeatherData

from sinergym.utils.common import eppy_element_to_dict, get_delta_seconds
from sinergym.utils.constants import CWD, PKG_DATA_PATH, WEEKDAY_ENCODING, YEAR


class Model(ABC):
    """Class to determine the Sinergym models' structure.
    """

    def __init__(self):
        pass

    # ---------------------------------------------------------------------------- #
    #                  Variables and Building model adaptation                     #
    # ---------------------------------------------------------------------------- #

    @abstractmethod
    def update_weather_path(self) -> None:
        pass

    @abstractmethod
    def adapt_building_to_epw(
            self,
            summerday: str = 'Ann Clg .4% Condns DB=>MWB',
            winterday: str = 'Ann Htg 99.6% Condns DB') -> None:
        pass

    @abstractmethod
    def apply_extra_conf(self) -> None:
        pass

    @abstractmethod
    def save_building_model(self) -> str:
        pass

    @abstractmethod
    def get_schedulers(self) -> Dict[str, Dict[str, Any]]:
        pass

    # ---------------------------------------------------------------------------- #
    #                        EPW and Weather Data management                       #
    # ---------------------------------------------------------------------------- #

    @abstractmethod
    def apply_weather_variability(
            self,
            columns: List[str],
            variation: Optional[Tuple[float, float, float]]) -> str:
        pass

    # ---------------------------------------------------------------------------- #
    #                        Model and Config Functionality                        #
    # ---------------------------------------------------------------------------- #

    @abstractmethod
    def _get_eplus_runperiod(
            self) -> Dict[str, int]:
        pass

    @abstractmethod
    def _get_one_epi_len(self) -> float:
        pass

    # ---------------------------------------------------------------------------- #
    #                  Working Folder for Simulation Management                    #
    # ---------------------------------------------------------------------------- #

    @abstractmethod
    def set_experiment_working_dir(self, env_name: str) -> str:
        pass

    @abstractmethod
    def set_episode_working_dir(self) -> str:
        pass

    @abstractmethod
    def _get_working_folder(
            self,
            directory_path: str,
            base_name: str) -> str:
        pass

    @abstractmethod
    def _rm_past_history_dir(
            self,
            episode_path: str,
            base_name: str) -> None:
        pass

    # ---------------------------------------------------------------------------- #
    #                             Config class checker                             #
    # ---------------------------------------------------------------------------- #

    @abstractmethod
    def _check_eplus_config(self) -> None:
        pass


class ModelJSON(object):
    """Class to manage backend models (building, weathers...) and folders in Sinergym (JSON version).

        :param _json_path: JSON path origin for apply extra configuration.
        :param weather_files: weather available files for each episode
        :param _weather_path: EPW path origin for apply weather to simulation in current episode.
        :param _ddy_path: DDY path origin for get DesignDays and weather Location
        :param _idd: IDD opyplus object to set up Epm
        :param experiment_path: Path for Sinergym experiment output
        :param episode_path: Path for Sinergym specific episode (before first simulator reset this param is None)
        :param max_ep_store: Number of episodes directories will be stored in experiment_path
        :param config: Dict config with extra configuration which is required to modify building model (may be None)
        :param building: Building model (Dictionary extracted from JSON)
        :param ddy_model: opyplus Epm object with DDY model
        :param weather_data: opyplus WeatherData object with EPW data
        :param zone_names: List of the zone names available in the building
        :param schedulers: Information in Dict format about all building schedulers.
        :param runperiod: Information in Dict format about runperiod that determine an episode.
        :param episode_length: Time in seconds that an episode has.
        :param step_size: Time in seconds that an step has.
    """

    def __init__(
            self,
            env_name: str,
            json_file: str,
            weather_files: List[str],
            max_ep_store: int,
            extra_config: Dict[str, Any]):

        self.pkg_data_path = PKG_DATA_PATH

        # ----------------------- Transform filenames in paths ----------------------- #

        # JSON
        self._json_path = os.path.join(
            self.pkg_data_path, 'buildings', json_file)

        # EPW
        self.weather_files = weather_files

        # IDD
        self._idd = os.path.join(os.environ['EPLUS_PATH'], 'Energy+.idd')

        # Select one weather randomly (if there are more than one)
        self._weather_path = os.path.join(
            self.pkg_data_path, 'weather', random.choice(self.weather_files))

        # DDY path is deducible using weather_path (only change .epw by .ddy)
        self._ddy_path = self._weather_path.split('.epw')[0] + '.ddy'

        # -------------------------------- File Models ------------------------------- #

        # Building model object (Python dictionaty from epJSON file)
        with open(self._json_path) as json_f:
            self.building = json.load(json_f)

        # DDY model (eppy object)
        IDF.setiddname(self._idd)
        self.ddy_model = IDF(self._ddy_path)

        # Weather data (opyplus object)
        self.weather_data = WeatherData.from_epw(self._weather_path)

        # ----------------------------- Other attributes ----------------------------- #

        self.experiment_path = self._set_experiment_working_dir(env_name)
        self.episode_path: Optional[str] = None
        self.max_ep_store = max_ep_store
        self.config = extra_config

        # Extract building zones
        self.zone_names = list(self.building['Zone'].keys())
        # Extract schedulers available in building model
        self.schedulers = self.get_schedulers()

        # Runperiod information
        self.runperiod = self._get_eplus_runperiod()
        self.episode_length = self._get_runperiod_len()
        self.step_size = 3600 / self.runperiod['n_steps_per_hour']

        # ------------------------ Checking config definition ------------------------ #

        # Check config definition
        self._check_eplus_config()

    # ---------------------------------------------------------------------------- #
    #                 Variables and Building model adaptation                      #
    # ---------------------------------------------------------------------------- #

    def update_weather_path(self) -> None:
        """When this method is called, weather file is changed randomly and building model is adapted to new one.
        """
        self._weather_path = os.path.join(
            self.pkg_data_path, 'weather', random.choice(self.weather_files))
        self._ddy_path = self._weather_path.split('.epw')[0] + '.ddy'
        self.ddy_model = IDF(self._ddy_path)
        self.weather_data = WeatherData.from_epw(self._weather_path)

    def adapt_building_to_epw(
            self,
            summerday: str = 'Ann Clg .4% Condns DB=>MWB',
            winterday: str = 'Ann Htg 99.6% Condns DB') -> None:
        """Given a summer day name and winter day name from DDY file, this method modify Location and DesingDay's in order to adapt building model to EPW.

        Args:
            summerday (str): Design day for summer day specifically (DDY has several of them).
            winterday (str): Design day for winter day specifically (DDY has several of them).
        """

        # Getting the new location and designdays based on ddy file (Records
        # must be converted to dictionary)

        # LOCATION
        new_location = self.ddy_model.idfobjects['Site:Location'][0]
        new_location = eppy_element_to_dict(new_location)

        # DESIGNDAYS
        ddy_designdays = self.ddy_model.idfobjects['SizingPeriod:DesignDay']
        summer_designdays = list(
            filter(
                lambda designday: summerday in designday.Name,
                ddy_designdays))[0]
        winter_designdays = list(
            filter(
                lambda designday: winterday in designday.Name,
                ddy_designdays))[0]
        new_designdays = {}
        new_designdays.update(eppy_element_to_dict(winter_designdays))
        new_designdays.update(eppy_element_to_dict(summer_designdays))

        # Addeding new location and DesignDays to Building model
        self.building['Site:Location'] = new_location
        self.building['SizingPeriod:DesignDay'] = new_designdays

    def apply_extra_conf(self) -> None:
        """Set extra configuration in building model
        """
        if self.config is not None:

            # Timesteps processed in a simulation hour
            if self.config.get('timesteps_per_hour'):
                list(self.building['Timestep'].values())[
                    0]['number_of_timesteps_per_hour'] = self.config['timesteps_per_hour']

            # Runperiod datetimes --> Tuple(start_day, start_month, start_year,
            # end_day, end_month, end_year)
            if self.config.get('runperiod'):
                runperiod = list(self.building['RunPeriod'].values())[0]
                runperiod['begin_day_of_month'] = int(
                    self.config['runperiod'][0])
                runperiod['begin_month'] = int(self.config['runperiod'][1])
                runperiod['begin_year'] = int(self.config['runperiod'][2])
                runperiod['end_day_of_month'] = int(
                    self.config['runperiod'][3])
                runperiod['end_month'] = int(self.config['runperiod'][4])
                runperiod['end_year'] = int(self.config['runperiod'][5])

    def save_building_model(self) -> str:
        """Take current building model and save as epJSON in current env_working_dir episode folder.

        Returns:
            str: Path of epJSON file stored (episode folder).
        """

        # If no path specified, then use json_path to save it.
        if self.episode_path is not None:
            episode_json_path = os.path.join(self.episode_path,
                                             os.path.basename(self._json_path))
            with open(episode_json_path, "w") as outfile:
                json.dump(self.building, outfile, indent=4)

            return episode_json_path
        else:
            raise RuntimeError(
                '[Simulator Modeling] Episode path should be set before saving building model.')

    def get_schedulers(self) -> Dict[str,
                                     Dict[str, Union[str, Dict[str, str]]]]:
        """Extract all schedulers available in the building model to be controlled.

        Returns:
            Dict[str, Dict[str, Any]]: Python Dictionary: For each scheduler found, it shows type value and where this scheduler is present (table, object and field).
        """
        result = {}
        schedules = {}
        # Mount a dict with only building schedulers
        if 'Schedule:Compact' in self.building:
            schedules.update(self.building['Schedule:Compact'])
        if 'Schedule:Year' in self.building:
            schedules.update(self.building['Schedule:Year'])

        for sch_name, sch_info in schedules.items():
            # Write sch_name and data type in output
            result[sch_name] = {
                'Type': sch_info['schedule_type_limits_name'],
            }
            # We are going to search where that scheduler appears in whole
            # building model
            for table, elements in self.building.items():
                # Don't include themselves
                if table != 'Schedule:Compact' and table != 'Schedule:Year':
                    # For each object of a table type
                    for element_name, element_fields in elements.items():
                        # For each field in a object
                        for field_key, field_value in element_fields.items():
                            # If a field value is the schedule name
                            if field_value == sch_name:
                                # We annotate the object name as key and the
                                # field name where sch name appears and the
                                # table where belong to
                                result[sch_name][element_name] = {
                                    'field_name': field_key,
                                    'table_name': table
                                }
        return result

    # ---------------------------------------------------------------------------- #
    #                        EPW and Weather Data management                       #
    # ---------------------------------------------------------------------------- #

    def apply_weather_variability(
            self,
            columns: List[str] = ['drybulb'],
            variation: Optional[Tuple[float, float, float]] = None) -> str:
        """Modify weather data using Ornstein-Uhlenbeck process.

        Args:
            columns (List[str], optional): List of columns to be affected. Defaults to ['drybulb'].
            variation (Optional[Tuple[float, float, float]], optional): Tuple with the sigma, mean and tau for OU process. Defaults to None.

        Returns:
            str: New EPW file path generated in simulator working path in that episode or current EPW path if variation is not defined.
        """
        # deepcopy for weather_data
        weather_data_mod = deepcopy(self.weather_data)
        filename = self._weather_path.split('/')[-1]

        # Apply variation to EPW if exists
        if variation is not None:

            # Get dataframe with weather series
            df = weather_data_mod.get_weather_series()

            sigma = variation[0]  # Standard deviation.
            mu = variation[1]  # Mean.
            tau = variation[2]  # Time constant.

            T = 1.  # Total time.
            # All the columns are going to have the same num of rows since they are
            # in the same dataframe
            n = len(df[columns[0]])
            dt = T / n
            # t = np.linspace(0., T, n)  # Vector of times.

            sigma_bis = sigma * np.sqrt(2. / tau)
            sqrtdt = np.sqrt(dt)

            x = np.zeros(n)

            # Create noise
            for i in range(n - 1):
                x[i + 1] = x[i] + dt * (-(x[i] - mu) / tau) + \
                    sigma_bis * sqrtdt * np.random.randn()

            for column in columns:
                # Add noise
                df[column] += x

            # Save new weather data
            weather_data_mod.set_weather_series(df)

            # Change name filename to specify variation nature in name
            filename = filename.split('.epw')[0]
            filename += '_Random_%s_%s_%s.epw' % (
                str(sigma), str(mu), str(tau))

        episode_weather_path = self.episode_path + '/' + filename
        weather_data_mod.to_epw(episode_weather_path)
        return episode_weather_path

    # ---------------------------------------------------------------------------- #
    #                        Model and Config Functionality                        #
    # ---------------------------------------------------------------------------- #

    def _get_eplus_runperiod(
            self) -> Dict[str, int]:
        """This method reads building runperiod information and returns it.

        Returns:
            Dict[str,int]: A Dict with: the start month, start day, start year, end month, end day, end year, start weekday and number of steps in a hour simulation.
        """
        # Get runperiod object inner building model
        runperiod = list(self.building['RunPeriod'].values())[0]

        # Extract information about runperiod
        start_month = int(
            0 if runperiod['begin_month'] is None else runperiod['begin_month'])
        start_day = int(
            0 if runperiod['begin_day_of_month'] is None else runperiod['begin_day_of_month'])
        start_year = int(
            YEAR if runperiod['begin_year'] is None else runperiod['begin_year'])
        end_month = int(
            0 if runperiod['end_month'] is None else runperiod['end_month'])
        end_day = int(0 if runperiod['end_day_of_month']
                      is None else runperiod['end_day_of_month'])
        end_year = int(
            YEAR if runperiod['end_year'] is None else runperiod['end_year'])
        start_weekday = WEEKDAY_ENCODING[runperiod['day_of_week_for_start_day'].lower(
        )]
        n_steps_per_hour = list(self.building['Timestep'].values())[
            0]['number_of_timesteps_per_hour']

        return {
            'start_day': start_day,
            'start_month': start_month,
            'start_year': start_year,
            'end_day': end_day,
            'end_month': end_month,
            'end_year': end_year,
            'start_weekday': start_weekday,
            'n_steps_per_hour': n_steps_per_hour}

    def _get_runperiod_len(self) -> float:
        """Gets the length of runperiod (an EnergyPlus process run to the end) depending on the config of simulation.

        Returns:
            float: The simulation time in which the simulation ends (seconds).
        """
        # Get runperiod object inner building model
        runperiod_info = self._get_eplus_runperiod()

        return get_delta_seconds(
            runperiod_info['start_year'],
            runperiod_info['start_month'],
            runperiod_info['start_day'],
            runperiod_info['end_year'],
            runperiod_info['end_month'],
            runperiod_info['end_day'])

    # ---------------------------------------------------------------------------- #
    #                  Working Folder for Simulation Management                    #
    # ---------------------------------------------------------------------------- #

    def set_episode_working_dir(self) -> str:
        """Set episode working dir path like config attribute for current simulation execution.

        Raises:
            Exception: If experiment path (parent folder) has not be created previously.

        Returns:
            str: Episode path for directory created.
        """
        # Generate episode dir path if experiment dir path has been created
        # previously
        if self.experiment_path is None:
            raise Exception
        else:
            episode_path = self._get_working_folder(
                directory_path=self.experiment_path,
                base_name='-sub_run')
            # Create directoy
            os.makedirs(episode_path)
            # set path like config attribute
            self.episode_path = episode_path

            # Remove redundant past working directories
            self._rm_past_history_dir(episode_path, '-sub_run')
            return episode_path

    def _set_experiment_working_dir(self, env_name: str) -> str:
        """Set experiment working dir path like config attribute for current simulation.

        Args:
            env_name (str): simulation env name to define a name in directory

        Returns:
            str: Experiment path for directory created.
        """
        # Generate experiment dir path
        experiment_path = self._get_working_folder(
            directory_path=CWD,
            base_name='-%s-res' %
            (env_name))
        # Create dir
        os.makedirs(experiment_path)
        # set path like config attribute
        self.experiment_path = experiment_path
        return experiment_path

    def _get_working_folder(
            self,
            directory_path: str,
            base_name: str = '-run') -> str:
        """Create a working folder path from path_folder using base_name, returning the absolute result path.
           Assumes folders in parent_dir have suffix <env_name>-run{run_number}. Finds the highest run number and sets the output folder to that number + 1.

        Args:
            path_folder (str): Path when working dir will be created.
            base_name (str, optional): Base name used to name the new folder inner path_folder. Defaults to '-run'.

        Returns:
            str: Path to the working directory.

        """

        # Create de rute if not exists
        os.makedirs(directory_path, exist_ok=True)
        experiment_id = 0
        # Iterate all elements inner path
        for folder_name in os.listdir(directory_path):
            if not os.path.isdir(os.path.join(directory_path, folder_name)):
                continue
            try:
                # Detect if there is another directory with the same base_name
                # and get number at final of the name
                folder_name = int(folder_name.split(base_name)[-1])
                if folder_name > experiment_id:
                    experiment_id = folder_name
            except BaseException:
                pass
        # experiment_id number will be +1 from last name found out.
        experiment_id += 1

        working_dir = os.path.join(directory_path, 'Eplus-env')
        working_dir = working_dir + '%s%d' % (base_name, experiment_id)
        return working_dir

    def _rm_past_history_dir(
            self,
            episode_path: str,
            base_name: str) -> None:
        """Removes the past simulation results from episode

        Args:
            episode_path (str): path for the current episide output
            base_name (str): base name for detect episode output id
        """

        cur_dir_name, cur_dir_id = episode_path.split(base_name)
        cur_dir_id = int(cur_dir_id)
        if cur_dir_id - self.max_ep_store > 0:
            rm_dir_id = cur_dir_id - self.max_ep_store
            rm_dir_full_name = cur_dir_name + base_name + str(rm_dir_id)
            rmtree(rm_dir_full_name)

    @ property
    def start_year(self) -> int:  # pragma: no cover
        """Returns the EnergyPlus simulation year.

        Returns:
            int: Simulation year.
        """

        return YEAR

    # ---------------------------------------------------------------------------- #
    #                             Config class checker                             #
    # ---------------------------------------------------------------------------- #

    def _check_eplus_config(self) -> None:
        """Check Eplus Environment config definition is correct.
        """

        # COMMON
        # Check weather files exist
        for w_file in self.weather_files:
            w_path = os.path.join(
                self.pkg_data_path, 'weather', w_file)
            assert os.path.isfile(
                w_path), 'Weather files: {} is not a weather file available in Sinergym.'.format(w_file)

        # EXTRA CONFIG
        if self.config is not None:
            for config_key in self.config.keys():
                # Check config parameters values
                # Timesteps
                if config_key == 'timesteps_per_hour':
                    assert self.config[config_key] > 0, 'Extra Config: timestep_per_hour must be a positive int value.'
                # Runperiod
                elif config_key == 'runperiod':
                    assert isinstance(
                        self.config[config_key], tuple) and len(
                        self.config[config_key]) == 6, 'Extra Config: Runperiod specified in extra configuration has an incorrect format (tuple with 6 elements).'
                else:  # pragma: no cover
                    raise KeyError(
                        F'Extra Config: Key name specified in config called [{config_key}] has no support in Sinergym.')
        # ACTION DEFINITION
        if self.action_definition is not None:
            for original_sch_name, new_sch in self.action_definition.items():
                # Check action definition format
                assert isinstance(
                    original_sch_name, str), 'Action definition: Keys must be str.'
                assert isinstance(
                    new_sch, dict), 'Action definition: New scheduler definition must be a dict.'
                assert set(
                    new_sch.keys()) == set(
                    ['name', 'initial_value']), 'Action definition: keys in new scheduler definition must be name and initial_value.'
                assert isinstance(
                    new_sch['name'], str), 'Action definition: Name field in new scheduler must be a str element.'
                # Check action definition component is in schedulers available
                # in building model
                assert original_sch_name in self.schedulers.keys(
                ), 'Action definition: Object called {} is not an existing component in building model.'.format(original_sch_name)
                # Check new variable is present in action variables
                assert new_sch['name'] in self.variables['action'], 'Action definition: {} external variable should be in action variables.'.format(
                    new_sch['name'])

    def _check_observation_variables(self) -> None:
        """This method checks whether observation variables are available in building model definition (Checking variable type definition too).
        """
        for obs_var in self.variables['observation']:
            # Name of the observation variable and element (Zone or HVAC
            # element name)
            obs_name = obs_var.split('(')[0]
            obs_element_name = obs_var.split('(')[1][:-1]

            # Check observarion variables names
            assert obs_name in list(self.rdd_variables.keys(
            )), 'Observation variables: Variable called {} in observation variables is not valid for the building model'.format(obs_name)
            # Check observation variables about zones (if variable type is
            # Zone)
            if self.rdd_variables[obs_name] == 'Zone':
                # Check that obs zone is not Environment or Whole building tag
                if obs_element_name.lower() != 'Environment'.lower(
                ) and obs_element_name.lower() != 'Whole Building'.lower():
                    # zones names with people 1 or lights 1, etc. The second name
                    # is ignored, only check that zone is a substr from obs
                    # zone
                    assert any(list(map(lambda zone: zone.lower() in obs_element_name.lower(), self.zone_names))
                               ), 'Observation variables: Zone called {} in observation variables does not exist in the building model.'.format(obs_element_name)
            # Check observation variables about HVAC
            elif self.rdd_variables[obs_name] == 'HVAC':
                pass
