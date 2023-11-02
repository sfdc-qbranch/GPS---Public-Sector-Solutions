import datetime
import filecmp
import glob
import logging
import os
import re
import shutil
import subprocess
import xml
import xml.etree.ElementTree as ET
from io import BytesIO
from os.path import exists
from typing import Optional
from urllib.request import urlopen
from xml.dom import minidom
from zipfile import ZipFile

import yaml

from qbrix.tools.shared.qbrix_cci_tasks import rebuild_cci_cache
from qbrix.tools.shared.qbrix_console_utils import init_logger
from qbrix.tools.shared.qbrix_io_tasks import QBrixDirectoryTask, QbrixFileTask
from qbrix.tools.shared.qbrix_json_tasks import JsonFileTask, OrgConfigFileTask
from qbrix.tools.shared.qbrix_shared_checks import is_github_url
from qbrix.tools.utils.qbrix_fart import FART

DEFAULT_UPDATE_LOCATION = "https://qbrix-core.herokuapp.com/qbrix/q_update_package.zip"

log = init_logger()

def replace_file_text(file_location, search_string, replacement_string, show_info=False, number_of_replacements=-1, search_regex=False):
    """ Replaces a string value within a given file

    Args:
        file_location (str): Relative path and file name of the file you want to replace text within
        search_string (str): The string value to find and replace within the given file content
        replacement_string (str): The replacement String value
        show_info (bool): When True, this will output information about the string value being modified.
        number_of_replacements (int): The total number of replacements to process, for example 1 would only replace the first instance of the search string in the file. Default is -1 which means replace all.
        search_regex (bool): When True, it will do regex replace instead of plain string replace, with this set to be True, the number_of_replacements will be a bit different, coz in re.sub, the count 0 (instead of -1) means replace all
    """

    if show_info:
        log.info("Checking %s...", file_location)

    file_task = QbrixFileTask(file_location=file_location)
    file_contents = file_task.get_file_contents()

    if not file_contents:
        return

    # only do the pre replace check if it's not regex search
    if (not search_regex) and (search_string not in file_contents):
        return

    if show_info:
        log_info = f" -> Searching for all references to '{search_string}' and replacing with '{replacement_string}'."
        if search_regex:
            log_info = log_info[:-1] + ", using regex."
        log.info(log_info)

    if search_regex:
        # notice the last arg, re.sub use count 0 instead of -1 for "replace all", so we need to do a bit tweak here
        updated_file_contents = re.sub(search_string, replacement_string, file_contents, number_of_replacements if number_of_replacements > 0 else 0)
    else:
        updated_file_contents = file_contents.replace(search_string, replacement_string, number_of_replacements)

    return file_task.update_file(updated_file_contents=updated_file_contents)


def get_qbrix_repo_url() -> str:
    """
    Get Repo URL for current Q Brix. If no .git has been linked to the given project, then user is prompted for url.

    Returns:
        str: GitHub repo url for the current Q Brix.
    """

    result = None
    try:
        result = subprocess.run("git config --get remote.origin.url", shell=True, capture_output=True).stdout
    except Exception as e:
        log.error(f"Unable to access GitHub Repository connected to this project. Please check that you have an internet connection and access to the GitHub Repository and you have git installed on your device. Error Detail: {e}")

    if not result:
        repo_url = input("Please Enter the complete URL for the Q brix Repo which should be linked to this project (e.g. https://www.github.com/sfdc-qbranch/Qbrix-1-repo): ")

        if repo_url == "" or repo_url is None:
            raise ValueError("No GitHub Repo URL was found or entered into the prompt.")

        if not is_github_url(repo_url):
            raise ValueError("URL Must be a valid Github.com URL to a Github repo.")
    else:
        repo_url = result.decode('utf-8').rstrip().replace(".git", "")

    return repo_url

def check_and_delete_dir(dir_path):
    """Deletes a directory (and all contents) if it exists. Returns True if folder has been deleted.

    Args:
        dir_path (str): Relative path to the directory within the project

    Returns:
        bool: True when directory is deleted or the directory does not exist. False if there has been an issue.
    """

    # Run initial Checks
    if not os.path.exists(dir_path):
        log.info("Directory already appears to have been removed or does not exist.")
        return True

    return QBrixDirectoryTask(dir_path).delete_directory()


def check_and_delete_file(file_path):
    """Deletes a File if it exists. Returns True if File has been removed.

    Args:
        file_path (str): The relative path to the file you want to delete.

    Returns:
        bool: True if file has been deleted or did not exist, False if there was an issue.
    """

    # If File already Removed return True
    if not os.path.exists(file_path):
        return True

    return QbrixFileTask(file_path).delete_file()

def check_org_config_files(auto=False):
    """Checks the orgs/dev.json and orgs/dev_preview.json file for key parameters

        Args:
            auto (bool): Optional parameter to set the checker to automatically update errors when they are found.

    """

    org_config_files = [
        "orgs/dev.json",
        "orgs/dev_preview.json"
    ]

    log.info("Scratch Org File Check: Checking your org config files for issues")

    for config_file in org_config_files:
        current_file = JsonFileTask(config_file)

        file_edition = current_file.get_json_value("edition") or ""
        file_instance = current_file.get_json_value("instance") or ""

        # Edition Check
        if file_edition != "" and "enterprise" in file_edition.lower():
            edition_update = None
            if not auto:
                edition_update = input("Edition not set to 'Enterprise'. Would you like to fix it? (Y/n) ") or 'y'
            if (edition_update and edition_update.lower() == 'y') or auto:
                current_file.update_value("edition", "Enterprise")

        # NA135 Instance Check (Preview Only)
        if file_instance != "" and "preview" in config_file.lower() and "NA135" not in file_instance:
            instance_update = None
            if not auto:
                instance_update = input("Preview file found using an instance other than NA135. Would you like to fix it? (Y/n) ") or 'y'
            if (instance_update and instance_update.lower() == 'y') or auto:
                current_file.update_value("instance", "NA135")


def check_api_versions(project_api_version):
    """
    Checks API Versions within the project are all in sync with cumulusci.yml file api version

    Args:
        project_api_version (str): Current Project API version, defined in cumulusci.yml file.

    """

    log.info("API Version Check: Checking File API Versions are set to v%s", project_api_version)

    sfdx_file = JsonFileTask("sfdx-project.json")
    if sfdx_file.get_json_value("sourceApiVersion") != project_api_version:
        sfdx_file.update_value("sourceApiVersion", project_api_version)
        log.info(" -> Updated sfdx-project.json File")

def source_org_feature_checker():
    """Check all source project org config files for missing features from current project config files"""

    org_config_files = [
        ("orgs/dev.json", "dev"),
        ("orgs/dev_preview.json", "dev_preview")
    ]

    build_cache_skip = False
    for org_file, org_name in org_config_files:
        log.info(" -> Checking that all source %s.json file features are listed in the current orgs/%s.json file", org_name, org_name)
        if os.path.exists(org_file):
            OrgConfigFileTask(org_file, org_name, build_cache_skip).merge_source_features()
        build_cache_skip = True

def org_feature_checker():
    """ Checks and updates the dev_preview.json file with missing features from the dev.json file """

    current_file = OrgConfigFileTask("orgs/dev_preview.json")
    current_file.merge_features_from("orgs/dev.json")
    current_file.merge_settings_from("orgs/dev.json")


def check_for_missing_files():
    """ Checks for essential files within the current project folder """

    if not exists("cumulusci.yml"):
        log.error("[ERROR] Missing File: cumulusci.yml")
    if not exists("orgs/dev.json"):
        log.error("[ERROR] Missing File: orgs/dev.json")
    if not exists("sfdx-project.json"):
        log.error("[ERROR] Missing File: sfdx-project.json")
    if not exists("orgs/dev_preview.json"):
        log.error("[ERROR] Missing File: orgs/dev_preview.json")


def download_and_unzip(url: Optional[str] = DEFAULT_UPDATE_LOCATION, archive_password: Optional[str] = None, ignore_optional_updates: Optional[bool] = False, q_update: Optional[bool] = False) -> bool:
    """
    Downloads a .zip file and extracts all contents to the root project directory in the same structure they are within the zip file.

    Args:
        url (str): The URL where the .zip file is located. Note that this must be publicly accessible. If none is specified it will default to the QBrix Update Location
        archive_password (str): Optional password for the .zip file
        ignore_optional_updates (bool): Set to True to ignore anything flagged as optional. Applies only to the Q Brix Updates. Defaults to False
        q_update (bool): This is set to True to generate additional folders in the project directory when a Q Brix update is running. Defaults to False

    Returns:
        bool: Returns True when the process has completed and False if there has been an issue.

    """

    try:
        zipfile = ZipFile(BytesIO(urlopen(url).read()))

        # Set Password if given
        if archive_password:
            zipfile.setpassword(pwd=bytes(archive_password, 'utf-8'))

        # Set Extraction Path
        extract_path = "."

        # When Q Brix Update, Ensure all paths are created and clear old download
        if q_update:

            extract_path = os.path.join(".qbrix", "Update")

            if not exists(extract_path):
                os.makedirs(name=extract_path, exist_ok=True)

            if exists(os.path.join(".qbrix", "Update", "xDO-Template-main")):
                shutil.rmtree(os.path.join(".qbrix", "Update", "xDO-Template-main"))

        # Ensure Extract Paths
        dir_check_list = [x for x in zipfile.namelist() if x.endswith('/')]
        for d in dir_check_list:
            if not exists(os.path.join(extract_path, d)):
                os.makedirs(name=os.path.join(extract_path, d), exist_ok=True)

        # Extract Files
        zipfile.extractall(path=extract_path)

        # Clean Up
        dirs = glob.glob(".qbrix/Update/**/__pycache__/", recursive=True)
        for folder in dirs:
            shutil.rmtree(folder)
        if exists("__MACOSX"):
            shutil.rmtree("__MACOSX")
        if exists("q_update_package"):
            shutil.rmtree("q_update_package")
        if ignore_optional_updates:
            if exists(".qbrix/OPTIONAL_UPDATES"):
                shutil.rmtree(".qbrix/OPTIONAL_UPDATES")

        return True
    except Exception as e:
        log.error(f"[ERROR] Update Failed! Error Message: {e}")
        if exists("q_update_package"):
            shutil.rmtree("q_update_package")
    return False


def check_and_update_old_class_refs():
    """
    Scans the cumulusci.yml file and ensures that any old class references have been updated to the new locations.
    """

    # Health Check
    replace_file_text("cumulusci.yml", "tasks.custom.qbrix_utils.HealthChecker", "qbrix.tools.utils.qbrix_health_check.HealthChecker")

    # Q Brix Update
    replace_file_text("cumulusci.yml", "tasks.custom.qbrix_utils.QBrixUpdater", "qbrix.tools.utils.qbrix_update.QBrixUpdater")

    # FART
    replace_file_text("cumulusci.yml", "tasks.custom.fart.FART", "qbrix.tools.utils.qbrix_fart.FART")

    # Batch Apex
    replace_file_text("cumulusci.yml", "tasks.custom.batchanonymousapex.BatchAnonymousApex", "qbrix.tools.utils.qbrix_batch_apex.BatchAnonymousApex")

    # Org Generator
    replace_file_text("cumulusci.yml", "tasks.custom.orggenerator.Spin", "qbrix.tools.utils.qbrix_org_generator.Spin")

    # Init Project
    replace_file_text("cumulusci.yml", "tasks.custom.qbrix_utils.Initialise_Project", "qbrix.tools.utils.qbrix_project_setup.InitProject")
    replace_file_text("cumulusci.yml", "tasks.custom.qbrix_utils.InitProject", "qbrix.tools.utils.qbrix_project_setup.InitProject")

    # List Q Brix
    replace_file_text("cumulusci.yml", "tasks.custom.qbrix_sf.ListQBrix", "qbrix.salesforce.qbrix_salesforce_tasks.ListQBrix")

    # Banner
    replace_file_text("cumulusci.yml", "tasks.custom.announce.CreateBanner", "qbrix.tools.shared.qbrix_console_utils.CreateBanner")

    # Mass File Ops
    replace_file_text("cumulusci.yml", "tasks.custom.qbrix_utils.MassFileOps", "qbrix.tools.utils.qbrix_mass_ops.MassFileOps")

    # SFDMU
    replace_file_text("cumulusci.yml", "tasks.custom.sfdmuload.SFDMULoad", "qbrix.tools.data.qbrix_sfdmu.SFDMULoad")

    # TESTIM
    replace_file_text("cumulusci.yml", "tasks.custom.testim.RunTestim", "qbrix.tools.testing.qbrix_testim.RunTestim")


def clean_project_files():
    """
    Removes known directories and files from a Q Brix Project folder which can be safely removed.
    """

    # Add Directory Paths to this list to have them removed by cleaner
    dirs_to_remove = [
        ".cci/projects",
        "src",
        "browser"
    ]

    # Add File Paths to this list to have them removed by cleaner
    files_to_remove = [
        "log.html",
        "playwright-log.txt",
        "output.xml",
        "report.html",
        "validationresult.json"
    ]

    if dirs_to_remove:
        for d in dirs_to_remove:
            check_and_delete_dir(d)

    if files_to_remove:
        for f in files_to_remove:
            check_and_delete_file(f)


def delete_standard_fields():
    """
    Removes Core/Standard Fields from Project Source. These are fields which are often pulled down when a standard Object is changed, like Account. Only custom fields need to be stored in the project, so this cleans up the other fields.
    """
    object_fields = glob.glob("force-app/main/default/objects/**/*.field-meta.xml", recursive=True)
    if object_fields and len(object_fields) > 0:
        for of in object_fields:
            if not os.path.basename(of).endswith("__c.field-meta.xml"):
                os.remove(of)


def update_file_api_versions(project_api_version) -> bool:
    """
    Scans specific files in the project which specify their own API version and updates them to be the same as the provided version

    Args:
        project_api_version: Target API Version you want to update the files to. e.g. 56

    Returns:
        bool: Returns True when complete. False if there was an issue.
    """

    if not project_api_version:
        return False

    # Init FART
    second_wind = FART()

    # File Locations To Check
    file_pattern_locations = [
        "force-app/main/default/classes/**/*.cls-meta.xml",
        "force-app/main/default/aura/**/*.cmp-meta.xml",
        "force-app/main/default/lwc/**/*.js-meta.xml",
        "files/package.xml",
        "sfdx-project.json"
    ]

    file_list = []
    if file_pattern_locations and len(file_pattern_locations) > 0:
        for pattern in file_pattern_locations:
            file_list += glob.glob(pattern, recursive=True)

        if len(file_list) > 0:
            for f in file_list:
                if not os.path.exists(f):
                    continue

                left_side = "<apiVersion>"
                right_side = "</apiVersion>"

                if f == "files/package.xml":
                    left_side = "<version>"
                    right_side = "</version>"
                elif f == "sfdx-project.json":
                    left_side = "<sourceApiVersion>"
                    right_side = "</sourceApiVersion>"

                second_wind.fartbetween(srcfile=f, left=left_side, right=right_side, replacewith=project_api_version, formatval=None)

    return True


def update_project_api_versions(new_api_version, old_api_version, target_org_alias, skip_deploy):

    """Automates the update project process"""

    if not new_api_version:
        log.error("No new API version provided. Skipping task.")
        return False

    # deploy qbrix to scratch org, well if skip deploy is not "y"
    if skip_deploy.lower() != "y":
        log.info(f" ... deploying qbrix to org {target_org_alias}, please be patient, results will show when it's done, depends on how large your qbrix is, this process could take mintues to hours")
        deploy_output, deploy_error = run_command(f"cci flow run deploy_qbrix --org {target_org_alias}")
        log.info(deploy_output)

    log.info(f" ... retrieving metadata in api version {new_api_version}, please be patient, results will show when it's done, this should be much quicker than the deploy command")
    pull_output, pull_error = run_command(f"cci task run dx --command 'force:source:retrieve -p force-app -a {new_api_version}' --org {target_org_alias}")
    log.info(pull_output)
    replace_file_text("cumulusci.yml", f"api_version: \"{old_api_version}\"", f"api_version: \"{new_api_version}\"")

    check_api_versions(new_api_version)


def upsert_gitignore_entries(list_entries) -> bool:
    """
    Upserts a list of given gitignore patterns in the .gitignore file within the project. Each pattern is checked and if it is missing, it is added. If it exists but has been commented out, it will uncomment it.

    Args:
        list_entries (list(str)): List of strings which represent the gitignore patterns to check and upsert.

    Returns:
        bool: Returns True when completed, else False if there was an issue.
    """

    if len(list_entries) == 0:
        return False

    if not os.path.exists(".gitignore"):
        return False

    with open(".gitignore", 'a+', encoding="utf-8") as git_file:
        git_file.seek(0)
        content = git_file.read()

        for entry in list_entries:
            if entry not in content or f"#{entry}" in content:
                git_file.write(f"{entry}\n")

    return True


def check_permset_group_files():
    """
    Checks Permission Set Group Metadata Files and ensures they are set as 'Outdated'. This ensures they are recalculated upon deployment to an org.
    """

    logger = logging.getLogger(__name__)
    psg_files = glob.glob(os.path.normpath("force-app/main/default/permissionsetgroups/*.permissionsetgroup-meta.xml"), recursive=False)
    if len(psg_files) > 0:
        logger.info("Checking Permission Set Group File(s)")
        for psg in psg_files:
            logger.info(" -> Checking %s file configuration.", psg)
            FART.fartbetween(FART, psg, "<status>", "</status>", "Outdated", None)


def add_prefix(path, prefix):
    parts = os.path.split(path)
    return os.path.join(parts[0], prefix + parts[1])


def update_references(old_value, new_value, prefix=''):
    """
    Walks through project folders and updates all references to a new prefixed reference

    Args:
        old_value (str): The previous reference string to search for
        new_value (str): The updated reference string to search for
        prefix (str): The prefix to add
    """

    if old_value == 'All':
        return

    if old_value == new_value:
        return

    reference_pattern = re.compile(rf'(?<!{prefix})\b{old_value}\b')

    for project_path in ["force-app/main/default", "unpackaged/pre", "unpackaged/post"]:
        for root, _, files in os.walk(project_path):
            for file_name in files:
                if "external_id" in os.path.basename(file_name).lower() or os.path.basename(file_name).lower().startswith("sdo_") or os.path.basename(file_name).lower().startswith("xdo_") or os.path.basename(file_name).lower().startswith("db_"):
                    continue

                if os.path.basename(root) in {"standardValueSets", "roles", "corsWhitelistOrigins"}:
                    continue

                file_path = os.path.join(root, file_name)
                with open(file_path, 'r', encoding='utf-8') as f:
                    f.seek(0)
                    file_contents = f.read()

                new_contents = reference_pattern.sub(new_value, file_contents)
                if new_contents != file_contents:
                    try:
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(new_contents)
                            print(f'Updated references for {old_value} in {file_path}')
                    except Exception as e:
                        log.debug(e)
                        pass


def assign_prefix_to_files(prefix, parent_folder='force-app/main/default', interactive_mode=False):
    """
    Assigns a given prefix like 'FINS_' to custom items within the project folder.

    Args:
        prefix (str): The prefix you want to assign to items
        parent_folder (str): The relative path to the folder containing the project files. Defaults to force-app/main/default
        interactive_mode (bool): If True, this will ask the end user if a file should be updated or not.

    """

    # Validation
    if not prefix:
        raise Exception("Error: No prefix provided to the Mass Rename Tool. You must provide a prefix.")

    if not os.path.exists(parent_folder):
        raise Exception("Parent folder doesn't exist. Please correct the folder path and try again.")

    # Generate Prefix Variations
    prefix = prefix.replace("_", "")
    under_prefix = str(prefix).upper() + "_"
    open_prefix = str(prefix).upper() + " "

    # Set Matching Pattern for Cumstom API references
    PATTERN = re.compile(r'^.+$')
    FILE_PATTERN = re.compile(r'^.+.')

    paths_to_rename = []

    # Find and Update Custom Object Folder Names
    for root, dirs, files in os.walk(os.path.join(parent_folder, 'objects')):
        for dir_name in dirs:
            # no need to ask for standard object, or any sub folders (like fields, recordTypes folder) in each object folder
            if not dir_name.lower().endswith('__c'):
                log.debug(f"Ignoring {dir_name}")
                continue

            # no need to ask for anything comes from managed package
            if re.match(r'^[a-zA-Z]+__', dir_name):
                log.debug(f"Ignoring {dir_name}")
                continue

            if PATTERN.match(dir_name) and not dir_name.lower().startswith(prefix.lower()):
                old_path = os.path.join(root, dir_name)
                new_path = add_prefix(old_path, under_prefix)
                print(f'CUSTOM OBJECT DIRECTORY FOUND:\n    Current Path: {old_path}\n    Updated Path: {new_path}')
                approve_change = False
                if interactive_mode:
                    confirmation = input("Are you happy to make this change? (Y/n) : ") or 'y'
                    if confirmation.lower() == 'y':
                        approve_change = True
                    else:
                        approve_change = False
                else:
                    approve_change = True
                if approve_change:
                    paths_to_rename.append((old_path, new_path))
                    update_references(os.path.basename(old_path), os.path.basename(new_path), prefix)

        if root.endswith('compactLayouts') or root.endswith('recordTypes') or root.endswith('businessProcesses') or root.endswith('fields'):
            for file_name in files:
                if root.endswith('listViews') and "All.listView" in file_name:
                    continue

                if not file_name.lower().startswith(prefix.lower()) and not file_name.lower().startswith('sdo_') and not file_name.lower().startswith('xdo_'):
                    old_path = os.path.join(root, file_name)
                    if root.endswith('businessProcesses'):
                        new_path = add_prefix(old_path, open_prefix)
                    else:
                        new_path = add_prefix(old_path, under_prefix)
                    # os.rename(old_path, new_path)
                    print(f'CUSTOM OBJECT FILE FOUND:\n    Current Path: {old_path}\n    Updated Path: {new_path}')

                    old_value = os.path.splitext(os.path.basename(old_path))[0].split('.')[0]
                    new_value = os.path.splitext(os.path.basename(new_path))[0].split('.')[0]

                    approve_change = False
                    if interactive_mode:
                        confirmation = input("Are you happy to make this change? (Y/n) : ") or 'y'
                        if confirmation.lower() == 'y':
                            approve_change = True
                        else:
                            approve_change = False
                    else:
                        approve_change = True
                    if approve_change:
                        paths_to_rename.append((old_path, new_path))
                        update_references(old_value, new_value, prefix)

    # Update Custom File Names
    file_list = glob.glob(f'{parent_folder}/**/*.*-meta.xml', recursive=True)

    for current_file in file_list:
        file_name = os.path.basename(current_file)
        directory_name = os.path.dirname(current_file)

        if os.path.basename(directory_name) in {"settings", "standardValueSets", "roles", "corsWhitelistOrigins", "layouts", "quickActions"} or "objects" in directory_name:
            continue

        if "external_id" in file_name.lower() or file_name.lower().startswith("sdo_") or file_name.lower().startswith("xdo_") or file_name.lower().startswith(f"{prefix}") or file_name.lower().startswith("db_") or file_name.lower().startswith("standard-"):
            continue

        old_path = current_file
        new_path = add_prefix(old_path, under_prefix)
        print(f'PROJECT CUSTOM FILE FOUND:\n    Current Path: {old_path}\n    Updated Path: {new_path}')

        old_value = os.path.splitext(os.path.basename(old_path))[0].split('.')[0]
        new_value = os.path.splitext(os.path.basename(new_path))[0].split('.')[0]

        approve_change = False
        if interactive_mode:
            confirmation = input("Are you happy to make this change? (Y/n) : ") or 'y'
            if confirmation.lower() == 'y':
                approve_change = True
            else:
                approve_change = False
        else:
            approve_change = True
        if approve_change:
            paths_to_rename.append((old_path, new_path))
            update_references(old_value, new_value, prefix)

    # Rename all files and Folders where matches were located
    sorted_list = sorted(paths_to_rename, key=lambda x: len(x[1]), reverse=True)
    for path_to_update, new_updated_path in sorted_list:
        os.rename(path_to_update, new_updated_path)
        print(f"FILE OR FOLDER RENAMED:\n    Previous Path: {path_to_update}\n    New Path: {new_updated_path}")


def create_external_id_field(file_path: str = None, object_list = None):
    """
    Creates External ID Fields for a given list of Object Names. If no file is provided, this will generate External ID fields on all objects within the current project directory.

    Args:
        file_path (str): Relative Path within Project to a .txt file containing a list of objects to process. If not provided, will generate a list of objects from the current project.
    """

    if not object_list:
        object_list = set()

    if file_path and os.path.exists(file_path):
        with open(file_path, encoding="utf-8") as object_file:
            object_list = set(line.strip() for line in object_file if line.strip())
    else:
        object_path = os.path.normpath("force-app/main/default/objects")
        if os.path.exists(object_path):
            object_list = set(obj for obj in os.listdir(object_path) if os.path.isdir(os.path.join(object_path, obj)))

    if len(object_list) > 0:
        for project_object in object_list:
            object_dir = os.path.join("force-app", "main", "default", "objects", project_object)
            os.makedirs(object_dir, exist_ok=True)
            fields_dir = os.path.join(object_dir, "fields")
            os.makedirs(fields_dir, exist_ok=True)
            field_file = os.path.join(fields_dir, "External_ID__c.field-meta.xml")
            if not os.path.exists(field_file):
                with open(field_file, "w", encoding="utf-8") as f:
                    f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
                    f.write('<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">\n')
                    f.write('    <fullName>External_ID__c</fullName>\n')
                    f.write('    <externalId>true</externalId>\n')
                    f.write('    <label>External ID</label>\n')
                    f.write('    <length>50</length>\n')
                    f.write('    <required>false</required>\n')
                    f.write('    <trackTrending>false</trackTrending>\n')
                    f.write('    <type>Text</type>\n')
                    f.write('    <unique>false</unique>\n')
                    f.write('</CustomField>\n')


def run_command(command, cwd="."):
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, text=True, cwd=cwd)
    output, error = process.communicate()

    if error:
        raise Exception(error)
    return output, error


def compare_directories(dcmp):
    new_or_changed = []
    for name in dcmp.right_only:
        new_or_changed.append(os.path.join(dcmp.right, name))
    for name in dcmp.diff_files:
        new_or_changed.append(os.path.join(dcmp.right, name))
    for sub_dcmp in dcmp.subdirs.values():
        new_or_changed.extend(compare_directories(sub_dcmp))
    return new_or_changed


def compare_metadata(target_org_alias):
    # Default Org Command
    if os.path.exists('src'):
        shutil.rmtree('src')

    if os.path.exists('mdapipkg'):
        shutil.rmtree('mdapipkg')

    if os.path.exists('upgrade_src'):
        shutil.rmtree('upgrade_src')

    run_command("cci task run dx_convert_from")

    # Retrieve metadata from the target org
    log.info(f"Retrieving metadata from the target org with alias {target_org_alias} (This can take a few minutes..)")
    retrieve_command = f"cci task run dx --command \"force:mdapi:retrieve -r mdapipkg -k src/package.xml\" --org {target_org_alias}"
    run_command(retrieve_command)

    # Unzip the retrieved metadata
    log.info("Unpacking Metadata")
    unzip_command = f"unzip -o mdapipkg/unpackaged.zip -d mdapipkg/unpackaged"
    run_command(unzip_command)

    # Compare the local and target org's metadata
    log.info("Comparing Metadata")
    dcmp = filecmp.dircmp('mdapipkg/unpackaged/unpackaged', 'src')
    new_or_changed = compare_directories(dcmp)

    changes = []

    if len(new_or_changed) > 0:
        log.info(f"{len(new_or_changed)} changes found")
        log.info("Generating new update package in directory: upgrade_src")

        for file_path in new_or_changed:
            if os.path.basename(os.path.dirname(file_path)) in {'settings', 'labels'}:
                log.info(f"Skipping {file_path} as it contains a high risk metadata type. Review the contents individually.")
                continue

            changes.append(file_path)

            # Determine the destination path of the metadata file to copy
            dst_file_path = os.path.join('upgrade_src', file_path.replace('src/', ''))

            # Create the destination directory if it does not exist
            dst_directory = os.path.dirname(dst_file_path)
            if not os.path.exists(dst_directory):
                os.makedirs(dst_directory)

            # Copy the metadata file to the destination directory
            shutil.copy2(file_path, dst_file_path)

        run_command("sfdx force:source:manifest:create --sourcepath upgrade_src --manifestname upgrade_src/package")

    return changes


def push_changes(target_org_alias):
    # Push Changes
    push_command = f"cci task run deploy --path upgrade_src --org {target_org_alias}"
    push_output, push_error = run_command(push_command)

    log.info("Upgrade Pushed!")
    return push_output

def get_existing_entries(permission_set_file_path):

    ET.register_namespace('', "http://soap.sforce.com/2006/04/metadata")

    # Define a dictionary to track existing entries
    existing_entries = {
        "applicationVisibilities": [],
        "classAccesses": [],
        "customMetadataTypeAccesses": [],
        "customPermissions": [],
        "customSettingAccesses": [],
        "externalDataSourceAccesses": [],
        "fieldPermissions": [],
        "flowAccesses": [],
        "objectPermissions": [],
        "pageAccesses": [],
        "recordTypeVisibilities": [],
        "tabSettings": [],
        "userPermissions": []
    }

    # Parse the existing XML file if it exists
    if os.path.exists(permission_set_file_path):
        print("Existing File Mode")
        with open(permission_set_file_path, "rb") as file:
            try:
                existing_tree = xml.etree.ElementTree.parse(file)
                salesforce_namespace_map = {'': "http://soap.sforce.com/2006/04/metadata"}
                for entry in existing_entries.keys():
                    elements = existing_tree.findall('.//'+entry, namespaces=salesforce_namespace_map)
                    for element in elements:
                        existing_entries[entry].append(element)
            except Exception as e:
                print(e)
                print("Ignoring Error and rebuilding Permission Set File")
        os.remove(permission_set_file_path)

    return existing_entries


def create_permission_set_file(name, label, permission_set_path=None, run_as_upsert=True):
    """
    Creates or updates a Permission Set in the XML file.

    Args:
        name (str): The Name for the Permission Set File
        label (str): The label for the Permission Set
    """

    if not permission_set_path:
        permissionset_path = os.path.join("force-app", "main", "default", "permissionsets", f"{name}.permissionset-meta.xml")
    else:
        permissionset_path = os.path.join(permission_set_path, f"{name}.permissionset-meta.xml")

    if not run_as_upsert and os.path.exists(permissionset_path):
        os.remove(permissionset_path)

    ET.register_namespace('', "http://soap.sforce.com/2006/04/metadata")

    # Get Dict of Access Types
    # Note for developers, Permission Sets require all types of access, e.g. customMetadataTypeAccesses to be grouped together in the resulting file
    existing_entries = get_existing_entries(permission_set_file_path=permissionset_path)

    # Create or update the root element
    root = ET.Element("PermissionSet")

    # Set the label
    # Adjust long labels to the max length
    if len(label) > 80:
        log.info("Adjusted label length as you have passed in a permission set label name which is more than 80 characters.")
        label = label[:80]
    label_element = ET.SubElement(root, "label")
    label_element.text = label



    # APPLICATION ACCESS

    # Handle Existing Access if any
    if len(existing_entries["applicationVisibilities"]) > 0:
        for existing_app_permission in existing_entries["applicationVisibilities"]:
            root.append(existing_app_permission)

    # Handle New or Additional Access
    apps_path = "force-app/main/default/applications"
    if os.path.exists(apps_path):
        for apps_file in sorted(os.listdir(apps_path)):
            if apps_file.endswith(".app-meta.xml"):
                app_name = apps_file[:-13]
                app_permissions_element = find_existing_entry(existing_entries["applicationVisibilities"], "application", app_name)
                if app_permissions_element is None:
                    app_permissions_element = ET.SubElement(root, "applicationVisibilities")
                    ET.SubElement(app_permissions_element, "application").text = app_name
                    ET.SubElement(app_permissions_element, "visible").text = "true"



    # APEX Class Access

    # Handle Existing Access if any
    if len(existing_entries["classAccesses"]) > 0:
        for existing_ac_permission in existing_entries["classAccesses"]:
            root.append(existing_ac_permission)

    # Handle New or Additional Access
    classes_path = "force-app/main/default/classes"
    if os.path.exists(classes_path):
        for class_file in sorted(os.listdir(classes_path)):
            if class_file.endswith(".cls"):
                class_name = class_file[:-4]
                class_permissions_element = find_existing_entry(existing_entries["classAccesses"], "apexClass", class_name)
                if class_permissions_element is None:
                    class_permissions_element = ET.SubElement(root, "classAccesses")
                    ET.SubElement(class_permissions_element, "apexClass").text = class_name
                    ET.SubElement(class_permissions_element, "enabled").text = "true"



    # CUSTOM METADATA ACCESS

    # Handle Existing Access if any
    if len(existing_entries["customMetadataTypeAccesses"]) > 0:
        for existing_permission in existing_entries["customMetadataTypeAccesses"]:
            root.append(existing_permission)

    # Handle New or Additional Access
    custom_md_path = "force-app/main/default/customMetadata"
    if os.path.exists(custom_md_path):
        for custom_md_file in sorted(os.listdir(custom_md_path)):
            if custom_md_file.endswith(".md-meta.xml"):
                md_file_name = os.path.basename(custom_md_file)
                md_name = md_file_name.split(".")[0]
                md_name += "__mdt"
                md_permissions_element = find_existing_entry(existing_entries["customMetadataTypeAccesses"], "name", md_name)
                if md_permissions_element is None:
                    md_permissions_element = ET.SubElement(root, "customMetadataTypeAccesses")
                    ET.SubElement(md_permissions_element, "name").text = md_name
                    ET.SubElement(md_permissions_element, "enabled").text = "true"



    # CUSTOM PERMISSIONS

    # Handle Existing Access if any
    if len(existing_entries["customPermissions"]) > 0:
        for existing_permission in existing_entries["customPermissions"]:
            root.append(existing_permission)

    # Handle New or Additional Access
    # TODO



    # CUSTOM SETTING ACCESS

    # Handle Existing Access if any
    if len(existing_entries["customSettingAccesses"]) > 0:
        for existing_permission in existing_entries["customSettingAccesses"]:
            root.append(existing_permission)

    # Handle New or Additional Access
    # TODO



    # EXTERNAL DATASOURCE ACCESS

    # Handle Existing Access if any
    if len(existing_entries["externalDataSourceAccesses"]) > 0:
        for existing_permission in existing_entries["externalDataSourceAccesses"]:
            root.append(existing_permission)

    # Handle New or Additional Access
    # TODO



    # object path needed later for field, object and recordtype
    objects_path = os.path.join("force-app", "main", "default", "objects")



    # FIELD PERMISSIONS

    # Add Existing Entries, if any
    if len(existing_entries["fieldPermissions"]) > 0:
        for existing_field_permission in existing_entries["fieldPermissions"]:
            root.append(existing_field_permission)

    # Check for New or Additional Entries and add them
    if os.path.exists(objects_path):
        for object_folder in sorted(os.listdir(objects_path)):
            object_folder_path = os.path.join(objects_path, object_folder)
            if os.path.isdir(object_folder_path):
                fields_folder_path = os.path.join(object_folder_path, "fields")
                if os.path.isdir(fields_folder_path):
                    for field_file in sorted(os.listdir(fields_folder_path)):

                        # Read File and skip MasterDetail and Formula Fields
                        with open(os.path.join(fields_folder_path, field_file), "r") as file:
                            contents = file.read()
                            formula_reference_to_start = contents.find("<formula>")
                            md_reference_to_start = contents.find("<type>MasterDetail</type>")
                            req_reference_to_start = contents.find("<required>true</required>")

                        if formula_reference_to_start > -1 or md_reference_to_start > -1 or req_reference_to_start > -1:
                            continue

                        field_name = field_file[:-15]
                        field_key = f"{object_folder}.{field_name}"
                        field_permissions_element = find_existing_entry(existing_entries["fieldPermissions"], "field", field_key)
                        if field_permissions_element is None:
                            field_permissions_element = ET.SubElement(root, "fieldPermissions")
                            ET.SubElement(field_permissions_element, "editable").text = "true"
                            ET.SubElement(field_permissions_element, "field").text = field_key
                            ET.SubElement(field_permissions_element, "readable").text = "true"

    # FLOW ACCESS

    # Handle Existing Access if any
    if len(existing_entries["flowAccesses"]) > 0:
        for existing_permission in existing_entries["flowAccesses"]:
            root.append(existing_permission)

    # Handle New or Additional Access
    flows_path = "force-app/main/default/flows"
    if os.path.exists(flows_path):
        for flow_file in sorted(os.listdir(flows_path)):
            if flow_file.endswith(".flow-meta.xml"):
                flow_name = flow_file[:-14]
                flow_permissions_element = find_existing_entry(existing_entries["flowAccesses"], "flow", flow_name)
                if flow_permissions_element is None:
                    flow_permissions_element = ET.SubElement(root, "flowAccesses")
                    ET.SubElement(flow_permissions_element, "flow").text = flow_name
                    ET.SubElement(flow_permissions_element, "enabled").text = "true"



    # OBJECT PERMISSIONS

    # Handle Any Existing Entries
    if len(existing_entries["objectPermissions"]) > 0:
        for existing_object_permission in existing_entries["objectPermissions"]:
            root.append(existing_object_permission)

    # Check for additional or new entries
    objects_set = set()
    if os.path.exists(objects_path):
        for object_name in sorted(os.listdir(objects_path)):

            if object_name == '.DS_Store':
                continue

            # Add Object Dir to Set
            objects_set.add(object_name)

            # Add object permissions for lookup fields that reference objects not in the project
            fields_folder_path = os.path.join(objects_path, object_name, "fields")
            if os.path.isdir(fields_folder_path):
                for field_file in sorted(os.listdir(fields_folder_path)):
                    field_path = os.path.join(fields_folder_path, field_file)
                    with open(field_path, "r") as file:
                        contents = file.read()
                        reference_to_start = contents.find("<referenceTo>")
                        reference_to_end = contents.find("</referenceTo>")
                        if reference_to_start != -1 and reference_to_end != -1:
                            reference_object = contents[reference_to_start + 13:reference_to_end]
                            objects_set.add(reference_object)

        # Create Entries for any missing ObjectPermissions
        for obj in objects_set:
            object_permissions_element = find_existing_entry(existing_entries["objectPermissions"], "object", obj)
            if object_permissions_element is None:
                print(f" -> Adding New Entry for {obj}")
                object_permissions_element = ET.SubElement(root, "objectPermissions")
                ET.SubElement(object_permissions_element, "allowCreate").text = "true"
                ET.SubElement(object_permissions_element, "allowDelete").text = "true"
                ET.SubElement(object_permissions_element, "allowEdit").text = "true"
                ET.SubElement(object_permissions_element, "allowRead").text = "true"
                ET.SubElement(object_permissions_element, "modifyAllRecords").text = "true"
                ET.SubElement(object_permissions_element, "object").text = obj
                ET.SubElement(object_permissions_element, "viewAllRecords").text = "true"



    # APEX PAGE VISUALFORCE PERMISSIONS

    # Handle Existing Access if any
    if len(existing_entries["pageAccesses"]) > 0:
        for existing_permission in existing_entries["pageAccesses"]:
            root.append(existing_permission)


    # Handle New or Additional Access
    pages_path = "force-app/main/default/pages"
    if os.path.exists(pages_path):
        for page_file in os.listdir(pages_path):
            if page_file.endswith(".page-meta.xml"):
                page_file = page_file[:-14]
                page_permissions_element = find_existing_entry(existing_entries["pageAccesses"], "apexPage", page_file)
                if page_permissions_element is None:
                    page_permissions_element = ET.SubElement(root, "pageAccesses")
                    ET.SubElement(page_permissions_element, "apexPage").text = page_file
                    ET.SubElement(page_permissions_element, "enabled").text = "true"



    # RECORD TYPE ACCESS

    # Handle Existing Access if any
    if len(existing_entries["recordTypeVisibilities"]) > 0:
        for existing_rt_permission in existing_entries["recordTypeVisibilities"]:
            root.append(existing_rt_permission)

    # Handle New or Additional Access
    if os.path.exists(objects_path):
        for object_folder in sorted(os.listdir(objects_path)):
            object_folder_path = os.path.join(objects_path, object_folder)
            if os.path.isdir(object_folder_path):
                record_types_folder_path = os.path.join(object_folder_path, "recordTypes")
                if os.path.isdir(record_types_folder_path):
                    for record_type_file in sorted(os.listdir(record_types_folder_path)):
                        if record_type_file.endswith(".recordType-meta.xml"):
                            record_type_name = record_type_file[:-20]
                            record_type_key = f"{object_folder}.{record_type_name}"
                            record_type_permissions_element = find_existing_entry(existing_entries["recordTypeVisibilities"], "recordType", record_type_key)
                            if record_type_permissions_element is None:
                                record_type_permissions_element = ET.SubElement(root, "recordTypeVisibilities")
                                ET.SubElement(record_type_permissions_element, "recordType").text = record_type_key
                                ET.SubElement(record_type_permissions_element, "visible").text = "true"



    # TAB PERMISSIONS

    # Handle Existing Access if any
    if len(existing_entries["tabSettings"]) > 0:
        for existing_ts_permission in existing_entries["tabSettings"]:
            root.append(existing_ts_permission)

    # Handle New or Additional Access
    tabs_path = "force-app/main/default/tabs"
    if os.path.exists(tabs_path):
        for tab_file in sorted(os.listdir(tabs_path)):
            if tab_file.endswith(".tab-meta.xml"):
                tab_name = tab_file[:-13]
                tab_permissions_element = find_existing_entry(existing_entries["tabSettings"], "tab", tab_name)
                if tab_permissions_element is None:
                    tab_permissions_element = ET.SubElement(root, "tabSettings")
                    ET.SubElement(tab_permissions_element, "tab").text = tab_name
                    ET.SubElement(tab_permissions_element, "visibility").text = "Visible"



    # USER PERMISSIONS

    # Handle Existing Access if any
    if len(existing_entries["userPermissions"]) > 0:
        for existing_permission in existing_entries["userPermissions"]:
            root.append(existing_permission)

    # Handle New or Additional Access
    # TODO - Unlikely we can find these within the project

    # Create or update the Permission Set file directory
    os.makedirs("force-app/main/default/permissionsets", exist_ok=True)

    # Check if the xmlns attribute is already present
    if "xmlns" not in root.attrib:
        root.set("xmlns", "http://soap.sforce.com/2006/04/metadata")

    with open(permissionset_path, "wb") as file:
        xml_string = ET.tostring(root, encoding="unicode")

        # Clean Up XML String
        # This is needed for updates as ET parses files weirdly and doesnt handle namespaces
        xml_string = re.sub(r">\s+<", "><", xml_string)
        xml_string = xml_string.replace('xmlns="http://soap.sforce.com/2006/04/metadata" xmlns="http://soap.sforce.com/2006/04/metadata"', 'xmlns="http://soap.sforce.com/2006/04/metadata"')

        # Write Permission Set File
        xml_dom = minidom.parseString(xml_string)
        formatted_xml = xml_dom.toprettyxml(indent="    ", encoding="utf-8")
        file.write(formatted_xml)

def find_existing_entry(existing_entries, child_tag, child_text):
    """
    Find an existing entry by comparing child tag and text.

    Args:

        existing_entries (list): List of existing child elements.
        child_tag (str): Child element tag name.
        child_text (str): Child element text.

    Returns:
        element: Existing element if found, else None.
    """

    nsmap = {'': "http://soap.sforce.com/2006/04/metadata"}
    for entry in existing_entries:
        child_element = entry.find(f"{child_tag}", namespaces=nsmap)
        if child_element is not None and child_element.text == child_text:
            return entry
    return None

def get_packages_in_stack(skip_cache_rebuild=False, whole_stack=True):

    """
    Finds all package references within the current stack or locally within the current project.
    """

    package_list = []

    # Regenerate cci cache
    if not skip_cache_rebuild:
        rebuild_cci_cache()

    if whole_stack:
        qbrix_dirs = sorted(os.listdir(".cci/projects"))
        for qbrix in qbrix_dirs:
            cci_yml = glob.glob(f"{os.path.join('.cci', 'projects', qbrix)}/**/cumulusci.yml", recursive=True)
            if len(cci_yml) > 0:
                with open(cci_yml[0], 'r') as f:
                    config = yaml.safe_load(f)

                dependencies = config['project'].get("dependencies")
                if dependencies:
                    for d in dependencies:
                        if d.get("version_id"):
                            package_list.append((d.get("version_id"), qbrix))

    with open('cumulusci.yml', 'r') as f:
        local_config = yaml.safe_load(f)

        local_dependencies = local_config['project'].get("dependencies")
        if local_dependencies:
            for d in local_dependencies:
                if d.get("version_id"):
                    package_list.append((d.get("version_id"), 'LOCAL'))

    return package_list


def generate_stack_view(parent_directory_path='.cci/projects', output="terminal"):
    # Regenerate cci cache
    rebuild_cci_cache()

    if not os.path.exists('.cci/projects'):
        print("No Sources to traverse. Skipping")
        return

    # Get Stack folder locations and order
    sub_directory_names_sorted = sorted(os.listdir(parent_directory_path))
    sub_directory_names_sorted.append("LOCAL")

    files_list = []
    overwritten_files_list = []

    if output == "terminal":
        print("Sending outputs to the Terminal")
        print("\n***SOURCE QBRIX FILES***")
    else:
        now = datetime.datetime.now()
        log_file_name = "stack_log_" + now.strftime("%Y%m%d%H%M%S") + ".txt"
        log_file = open(log_file_name, "w")
        print(f"Sending output to log file, located at {log_file_name}")
        log_file.write("\n***SOURCE QBRIX FILES***")

    for i, qbrix in enumerate(sub_directory_names_sorted):
        if qbrix != "LOCAL":
            if output == "terminal":
                print(f"\n{qbrix}")
                print("-" * len(qbrix))
            else:
                log_file.write(f"\n\n{qbrix}\n")
                log_file.write("-" * len(qbrix))

            cci_yml = glob.glob(f"{os.path.join('.cci', 'projects', qbrix)}/**/cumulusci.yml", recursive=True)

            if cci_yml:
                with open(cci_yml[0], 'r') as f:
                    config = yaml.safe_load(f)

                api_version = config['project']['package']['api_version']
                if api_version:
                    if output == "terminal":
                        print(f"\nAPI Version: {api_version}")
                    else:
                        log_file.write(f"\nAPI Version: {api_version}")
                else:
                    if output == "terminal":
                        print("\nAPI Version: ERROR MISSING!!!")
                    else:
                        log_file.write("\nAPI Version: ERROR MISSING!!!")

                repo_url = config['project']['git']['repo_url']
                if repo_url:
                    if output == "terminal":
                        print(f"\nREPO URL: {repo_url}")
                    else:
                        log_file.write(f"\nREPO URL: {repo_url}")
                else:
                    print("\nREPO URL: ERROR MISSING!!!")

                dependencies = config['project'].get("dependencies")
                if dependencies and len(dependencies) > 0:
                    if output == "terminal":
                        print("\nPACKAGES:")
                    else:
                        log_file.write("\nPACKAGES:")

                    for d in dependencies:
                        if d.get("namespace"):
                            if output == "terminal":
                                print(f" - Managed Package: {d.get('namespace')}")
                            else:
                                log_file.write(f"\n - Managed Package: {d.get('namespace')}")
                        if d.get("version_id"):
                            if output == "terminal":
                                print(f" - Unmanaged Package Version ID: {d.get('version_id')}")
                            else:
                                log_file.write(f"\n - Unmanaged Package Version ID: {d.get('version_id')}")
                        if d.get("github"):
                            if output == "terminal":
                                print(f" - Github Repo: {d.get('github')}")
                            else:
                                log_file.write(f"\n - Github Repo: {d.get('github')}")
            if output == "terminal":
                print("\nFILES:")
            else:
                log_file.write(f"\nFILES:")
            for root, dirs, files in os.walk(os.path.join(".cci", "projects", qbrix)):
                if "force-app/main/default" in root:
                    for file_name in files:
                        file_path = os.path.join(root, file_name)
                        force_app_index = file_path.find("force-app/main/default/")
                        if force_app_index != -1:
                            file_path = os.path.join(file_path[force_app_index + len("force-app/main/default/"):])
                            if output == "terminal":
                                print(f" - {file_path}")
                            else:
                                log_file.write(f"\n - {file_path}")
                            if i == 0:
                                files_list.append((file_path, qbrix))
                            else:
                                if len([t for t in files_list if t[0] == file_path]) >= 1:
                                    overwritten_files_list.append((file_path, qbrix))
                                else:
                                    files_list.append((file_path, qbrix))

        else:
            if output == "terminal":
                print(f"\nLOCAL QBRIX")
                print("-" * len("LOCAL QBRIX"))
            else:
                log_file.write(f"\n\nLOCAL QBRIX\n")
                log_file.write("-" * len("LOCAL QBRIX"))

            for root, dirs, files in os.walk("force-app/main/default"):
                for file_name in files:
                    file_path = os.path.join(root, file_name)
                    force_app_index = file_path.find("force-app/main/default/")
                    if force_app_index != -1:
                        file_path = os.path.join(file_path[force_app_index + len("force-app/main/default/"):])
                        if output == "terminal":
                            print(f" - {file_path}")
                        else:
                            log_file.write(f"\n - {file_path}")
                        if i == 0:
                            files_list.append((file_path, qbrix))
                        else:
                            if len([t for t in files_list if t[0] == file_path]) >= 1:
                                overwritten_files_list.append((file_path, qbrix))
                            else:
                                files_list.append((file_path, qbrix))

    if output == "terminal":
        print("\n***STACK FILES WHICH ARE REDEPLOYED***")
    else:
        log_file.write("\n\n***STACK FILES WHICH ARE REDEPLOYED***")

    for f, q in files_list:
        overwrite_matches = [t for t in overwritten_files_list if t[0] == f]

        if len(overwrite_matches) > 0:
            if output == "terminal":
                print(f"\n{f} (Deployed By {q})")
            else:
                log_file.write(f"\n\n{f} (Deployed By {q})")

            for o in list(set(overwrite_matches)):
                if o[1] != q:
                    if output == "terminal":
                        print(f" > Updated in: {o[1]}")
                    else:
                        log_file.write(f"\n > Updated in: {o[1]}")
    if output == "terminal":
        print("\n***STACK STATS***")
        print(f"\nTotal Files in Stack: {len(files_list)}")
        print(f"Total Files updated within stack: {len(overwritten_files_list)}")
    else:
        log_file.write(f"\n***STACK STATS***\n\nTotal Files in Stack: {len(files_list)}\nTotal Files updated within stack: {len(overwritten_files_list)}")

    if output != "terminal":
        log_file.close()

def remove_empty_translations():

    """
    Removes empty translations from the project directory. Defaults to the force-app/main/default/objectTranslations directory.
    """

    # Define the path to the objectTranslations directory
    obj_trans_dir = os.path.join('force-app', 'main', 'default', 'objectTranslations')

    # Loop through all subdirectories in the objectTranslations directory
    for obj_dir in os.listdir(obj_trans_dir):
        obj_dir_path = os.path.join(obj_trans_dir, obj_dir)
        if not os.path.isdir(obj_dir_path):
            continue

        # Check if all label tags have no value

        for trans_file in os.listdir(obj_dir_path):
            if not trans_file.endswith('.xml'):
                continue

            trans_file_path = os.path.join(obj_dir_path, trans_file)
            tree = ET.parse(trans_file_path)
            root = tree.getroot()
            has_translation = False
            for child in root:
                if child.find('label') is not None and child.find('label').text != '':
                    has_translation = True
                    break

            if not has_translation:
                print(f"No translation found in {trans_file_path}")
                os.remove(trans_file_path)
                remove_obj_dir = True
            else:
                remove_obj_dir = False

        # Remove object directory if all files within have no translations
        if remove_obj_dir:
            os.rmdir(obj_dir_path)

    # Remove objectTranslations directory if empty
    if not os.listdir(obj_trans_dir):
        os.rmdir(obj_trans_dir)

def pretty_print(elem, level=0):
    indent = '    ' * level
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = '\n' + indent + '    '
        if not elem.tail or not elem.tail.strip():
            elem.tail = '\n' + indent
        for elem in elem:
            pretty_print(elem, level + 1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = '\n' + indent
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = '\n' + indent

def check_and_update_setting(xml_file, settings_name, setting_name, setting_value):
    # Ensure the directories exist
    os.makedirs(os.path.dirname(xml_file), exist_ok=True)

    namespace = "http://soap.sforce.com/2006/04/metadata"
    nsmap = {'ns': namespace}

    if not os.path.isfile(xml_file):
        # File doesn't exist, create a new one with the settings element as the root
        root = ET.Element(settings_name)
        root.set("xmlns", namespace)
    else:
        # Parse the existing XML file
        ET.register_namespace('', namespace)
        tree = ET.parse(xml_file)
        root = tree.getroot()

    # Find the settings element
    setting_element = root.find('.//ns:'+setting_name, namespaces=nsmap)
    if setting_element is None:
        setting_element = ET.SubElement(root, setting_name)
        setting_element.text = str(setting_value)
    elif setting_element.text != str(setting_value):
        setting_element.text = str(setting_value)

    # Write the modified XML back to the file with formatting
    pretty_print(root)
    # Add XML declaration manually
    xml_content = '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(root, encoding="unicode")
    with open(xml_file, "w", encoding="utf-8") as file:
        file.write(xml_content)

def convert_to_18_char(sf_id):

    """Converts a 15 character salesforce ID to 18 Characters"""

    if len(sf_id) == 18:
        return sf_id
    if len(sf_id) != 15:
        raise ValueError("Salesforce ID must be either 15 or 18 characters in length.")

    chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"

    def calculate_position(segment):
        position = 0
        for idx, char in enumerate(segment):
            if 'A' <= char <= 'Z':
                position += 2 ** idx
        return chars[position]

    suffix = ''.join(calculate_position(sf_id[i:i+5]) for i in range(0, 15, 5))

    return sf_id + suffix
