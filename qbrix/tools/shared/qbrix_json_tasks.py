import glob
import json
import os

from qbrix.tools.shared.qbrix_cci_tasks import rebuild_cci_cache
from qbrix.tools.shared.qbrix_console_utils import init_logger


class JsonFileTask:

    """Class for working with JSON Files"""

    ENCODING = "utf-8"

    def __init__(self, file_path: str = None):
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Error: File Path does not exist. Check the file {file_path}")

        if not str(file_path).endswith(".json"):
            raise ValueError(f"Error: File provided is not a json file. Check the file {file_path}")

        self.file_path = os.path.normpath(file_path)
        self.logger = init_logger()
        self.json = self._open_json_file()

    def _open_json_file(self):
        try:
            with open(self.file_path, 'r', encoding=self.ENCODING) as json_file:
                return json.load(json_file)
        except Exception as json_file_exception:
            self.logger.error("Unable to load JSON file data. Detail: %s", json_file_exception)
            return None

    def _write_file_data(self, file_data = None):

        """Writes the given JSON data to the file location"""

        if file_data:
            with open(self.file_path, 'w', encoding=self.ENCODING) as json_file:
                json.dump(file_data, json_file, indent=2)

    def remove_key(self, target_key: str = None) -> bool:

        """Removes a key:value from the JSON for the given key"""

        if self.json and target_key and dict(self.json).get(target_key):
            del self.json[target_key]
            self._write_file_data(self.json)
            return True
        return False

    def get_json(self) -> any:

        """Returns the JSON from the file"""

        return self.json

    def get_json_value(self, target_key: str = None) -> any:

        """Returns a given value for a given key"""

        if not target_key:
            raise ValueError("Error: No key provided for JsonFileTask get value function.")

        return dict(self.json).get(target_key)

    def update_value(self, target_key: str = None, new_value = None) -> bool:

        """Updates a given value for a given key"""

        if not target_key:
            raise ValueError("Error: No key provided for JsonFileTask update function.")

        if self.json and dict(self.json).get(target_key):
            self.json[target_key] = new_value
            self._write_file_data(self.json)
            return True
        return False


def remove_json_entry(file_location: str, key_name: str):
    """
    Removes an entry from a json file.

    Args:
        file_location (str): The path to the json file
        key_name (str): Text Json Key which identifies the key, value pair
    """

    return JsonFileTask(file_location).remove_key(key_name)


def get_json_file_value(file_location: str, key_name: str):
    """
    Reads a value from a json file based on key name. Returns None if nothing is found or error.

    Args:
        file_location (str): Relative File Path to the file you want to read.
        key_name (str): Key name for entry in json file

    Returns:
        (str) Value from json file identified by key name
    """

    return JsonFileTask(file_location).get_json_value(key_name)


def update_json_file_value(file_location: str, key_name: str, new_value):
    """
    Updates a scratch org json file key value with a new value. Not designed to be used with a list.

    Args:
        file_location (str): Relative path and file name of the file you want to update
        key_name (str): Key for the value you want to update
        new_value (str): New value to be inserted for the given key
    """

    return JsonFileTask(file_location).update_value(key_name, new_value)

class OrgConfigFileTask:

    """Class for working with Salesforce Scratch org Configuration Files"""

    def __init__(self, parent_file_path, org_file_name: str = None, skip_cache_rebuild: bool = False):
        self._parent_file = JsonFileTask(parent_file_path)
        self._org_reference = "dev" if not org_file_name else org_file_name
        self.logger = init_logger()
        self.skip_cache_rebuild = skip_cache_rebuild

        self.logger.info("Loaded %s JSON File", parent_file_path)

    def de_duplicate_feature_list(self, key: str = "features"):

        """De-duplicates the features list for the referenced scratch org config file"""
        self.logger.info("Checking current scratch org file for duplicate features...")
        feature_list = self._parent_file.get_json_value(key) or []
        if feature_list:
            self._parent_file.update_value(target_key=key, new_value=self._deduplicate_list(feature_list))
            self.logger.info(" -> Feature check complete!")
        else:
            self.logger.info(" -> No features to de-duplicate!")

    def _get_all_source_member_features(self):

        """Returns a list of all features for all scratch org definition files with the same org reference e.g. dev in all source directories"""

        self.logger.info("Gathering features from all sources...")
        source_features_list = []
        if not self.skip_cache_rebuild:
            rebuild_cci_cache()
        for source_file in glob.glob(f".cci/projects/**/orgs/{self._org_reference}.json", recursive=True):
            self.logger.info(" -> Checking for features in %s...", source_file)
            source_file_features = JsonFileTask(source_file).get_json_value("features") or []
            if source_file_features:
                self.logger.info(" -> Found %i features", len(source_file_features))
                source_features_list.extend(source_file_features)
            else:
                self.logger.info(" -> No Features defined")
        self.logger.info("Gathered %i features from all sources. (These will be de-duplicated)", len(source_features_list))
        return source_features_list

    def merge_source_features(self):

        """Merges the features from all current project sources scratch org definition files with same org reference (e.g. dev) to the current project scratch org definition file"""
        self.logger.info("Merging features from all sources...")
        parent_feature_list = []
        current_project_features = self._parent_file.get_json_value("features") or []
        parent_feature_list.extend(current_project_features)
        parent_feature_list.extend(self._get_all_source_member_features())
        if len(parent_feature_list) > 0:
            self._parent_file.update_value("features", self._deduplicate_list(parent_feature_list))
            self.logger.info("Source features merged!")
        else:
            self.logger.info(" -> No Features to merge.")

    def merge_source_settings(self):

        """Merges Settings for all current project sources to the current org config file"""

        self.logger.info("Merging Settings from all sources...")
        current_settings = self._parent_file.get_json_value("settings") or {}
        if not self.skip_cache_rebuild:
            rebuild_cci_cache()
        for source_file in glob.glob(f".cci/projects/**/orgs/{self._org_reference}.json", recursive=True):
            given_settings = JsonFileTask(source_file).get_json_value("settings") or {}
            for key, value in given_settings.items():
                if key not in current_settings:
                    current_settings[key] = value
        if len(current_settings) > 0:
            self._parent_file.update_value("settings", current_settings)
            self.logger.info(" -> Settings Merged!")
        else:
            self.logger.info(" -> No Settings to merge.")

    def merge_all(self):
        self.skip_cache_rebuild = False
        self.merge_source_features()
        self.skip_cache_rebuild = True
        self.merge_source_settings()

    def merge_features_from(self, org_config_file):

        """Merges features from a given scratch org configuration file to the current scratch org configuration file"""

        parent_feature_list = []
        current_project_features = self._parent_file.get_json_value("features") or []
        parent_feature_list.extend(current_project_features)
        comparison_file_features = JsonFileTask(org_config_file).get_json_value("features") or []
        parent_feature_list.extend(comparison_file_features)
        if len(comparison_file_features) > 0:
            self._parent_file.update_value("features", self._deduplicate_list(parent_feature_list))
        else:
            self.logger.info(" -> No Features to merge.")

    def merge_settings_from(self, org_config_file):

        """Merges settings defined in org config file with the current org config file"""

        self.logger.info("Merging settings to this file from %s...", org_config_file)
        current_settings = self._parent_file.get_json_value("settings") or {}
        given_settings = JsonFileTask(org_config_file).get_json_value("settings") or {}
        for key, value in given_settings.items():
            if key not in current_settings:
                current_settings[key] = value
        if len(current_settings) > 0:
            self._parent_file.update_value("settings", current_settings)
            self.logger.info(" -> Settings Merged!")
        else:
            self.logger.info(" -> No Settings to merge.")

    def _deduplicate_list(self, input_list):
        unique_set = set()
        deduplicated_list = []

        for item in input_list:
            item = item.lower()
            item_for_list = item
            if ":" in item:
                item = item.split(":")[0]

            if item not in unique_set:
                unique_set.add(item)
                deduplicated_list.append(item_for_list)

        deduplicated_list.sort()
        return deduplicated_list
