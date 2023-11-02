import filecmp
import fnmatch
import os
import shutil
import stat
from abc import ABC
from datetime import datetime, timedelta
from os.path import exists
from pathlib import Path

from cumulusci.core.config import UniversalConfig
from cumulusci.core.tasks import BaseTask

from qbrix.tools.health.qbrix_project_checks import (
    check_and_update_nodejs,
    check_python_library_dependencies,
    check_scratch_org_files,
    cumulusci_update_check,
    update_salesforce_cli,
)
from qbrix.tools.shared.qbrix_project_tasks import (
    download_and_unzip,
    replace_file_text,
    upsert_gitignore_entries,
)

# UPDATE CONFIGURATION - CHANGE ITEMS HERE
#
# Q BRANCH UPDATE LOCATION - URL FOR GETTING THE LATEST TEMPLATE UPDATE
Q_BRANCH_LOCATION = "https://qbrix-core.herokuapp.com/qbrix/q_update_package.zip"

# QBRIX CUSTOM TASKS - THESE ARE INSERTED INTO THE CUMULUSCI.YML OF THE TARGET PROJECT
# PARAM1 = The name of the task
# PARAM2 = The class path of the task
Q_BRIX_CUSTOM_TASKS = {
    "qbrix_preflight": "qbrix.tools.utils.qbrix_preflight.RunPreflight",
    "qbrix_landing": "qbrix.tools.utils.qbrix_landing.RunLanding",
    "analytics_manager": "qbrix.tools.data.qbrix_analytics.AnalyticsManager",
    "user_manager": "qbrix.salesforce.qbrix_salesforce_tasks.CreateUser",
    "qbrix_installer_tracking": "qbrix.tools.utils.qbrix_installtracking.InstallRecorder",
    "qbrix_metadata_checker": "qbrix.tools.utils.qbrix_metadata_checker.MetadataChecker",
    "dustpan": "qbrix.tools.utils.qbrix_orgconfig_hydrate.NGBroom",
    "flow_wrapper": "qbrix.tools.utils.qbrix_deploy.Deploy",
    "qbrix_sfdx": "cumulusci.tasks.sfdx.SFDXOrgTask",
    "deploy_dx": "cumulusci.tasks.sfdx.SFDXOrgTask",
    "qbrix_cache_add": "qbrix.tools.utils.qbrix_orgconfig_hydrate.NGCacheAdd",
    "abort_install": "qbrix.tools.utils.qbrix_orgconfig_hydrate.NGAbort",
    "qbrix_shell_deploy_metadeploy": "qbrix.tools.utils.qbrix_deploy.Deploy",
    "health_check": "qbrix.tools.utils.qbrix_health_check.HealthChecker",
    "update_qbrix": "qbrix.tools.utils.qbrix_update.QBrixUpdater",
    "setup_qbrix": "qbrix.tools.utils.qbrix_project_setup.InitProject",
    "list_qbrix": "qbrix.salesforce.qbrix_salesforce_tasks.ListQBrix",
    "q_update_dependencies": "qbrix.salesforce.qbrix_salesforce_tasks.QUpdateDependencies",
    "mass_qbrix_update": "qbrix.tools.utils.qbrix_mass_ops.MassFileOps",
    "precommit_check": "qbrix.git.hooks_ext.pre_commit.PreCommit",
    "qbrix_robot_test": "qbrix.tools.utils.qbrix_launch_test_robot.QRobotTestCapture",
    "experience_manager": "qbrix.tools.utils.qbrix_experience_manager.ExperienceManager",
    "experience_file_asset_manager": "qbrix.tools.utils.qbrix_experience_manager.ExperienceFileAssetManager",
    "qbrix_download_files": "qbrix.salesforce.qbrix_salesforce_tasks.DownloadFiles",
}

# Entires which are needed in .gitignore
Q_BRIX_GITIGNORE_ENTRIES = [
    "qbrix/*",
    "qbrix/__pycache__",
    "qbrix/core/__pycache__",
    "qbrix/robot/__pycache__",
    "qbrix/git/hooks_ext/__pycache__",
    "qbrix/salesforce/__pycache__",
    "qbrix/tools/__pycache__",
    "qbrix/tools/bundled/__pycache__",
    "qbrix/tools/bundled/sam/__pycache__",
    "qbrix/tools/utils/__pycache__",
    "qbrix/tools/shared/__pycache__",
    "qbrix/tools/data/__pycache__",
    "qbrix/tools/industry/__pycache__",
    "qbrix/tools/health/__pycache__",
    "qbrix/tools/testing/__pycache__",
    "qbrix/tools/shared/__pycache__/*",
    "*.pyc",
    ".idea/*",
    "validationresult.json",
    "*_results.xml",
]

# Required Directories for Q Brix
QBRIX_REQUIRED_DIRECTORIES = [".vscode", ".qbrix", ".git", "qbrix"]


class QBrixUpdater(BaseTask, ABC):

    """Updates Q Brix Scripts along with any optional, custom updates"""

    task_docs = """
    Updated the Q brix Extension Library and other Q Brix related bundles like GitHub Actions and VSCode Extensions in line with the XDO-Template (main branch).

    Can also be used to update custom scripts and other custom directories from a .zip file which needs to be hosted somewhere (by setting the URL of the .zip file as the UpdateLocation option), in addition the .zip files can also have a password set and you can specify the password using the ArchivePassword option when running the task.
    """

    task_options = {
        "UpdateLocation": {
            "description": "String URL for the location where the update package .zip file is located",
            "required": False,
        },
        "ArchivePassword": {
            "description": "String password for the .zip file",
            "required": False,
        },
        "IgnoreOptionalUpdates": {
            "description": "When set to True, will ignore updates defined as 'Optional' from the Q Branch Updates. Default is False.",
            "required": False,
        },
        "SkipDependencyChecks": {
            "description": "When set to True, will ignore updates to cli and apps.",
            "required": False,
        },
    }

    def _init_options(self, kwargs):
        super(QBrixUpdater, self)._init_options(kwargs)
        self.ArchivePassword = (
            self.options["ArchivePassword"]
            if "ArchivePassword" in self.options
            else None
        )
        self.UpdateLocation = (
            self.options["UpdateLocation"] if "UpdateLocation" in self.options else None
        )
        self.IgnoreOptionalUpdates = (
            self.options["IgnoreOptionalUpdates"]
            if "IgnoreOptionalUpdates" in self.options
            else False
        )
        self.SkipDependencyChecks = (
            self.options["SkipDependencyChecks"]
            if "SkipDependencyChecks" in self.options
            else False
        )

    def _check_and_deploy_class(self):
        """Checks the CumulusCI.yml file for custom task definitions and adds them if missing"""

        if not os.path.exists("cumulusci.yml"):
            self.logger.error(
                "ERROR: No Cumulusci.yml file found in project. Please check project directory."
            )
            return

        # Read Cumulus File
        with open("cumulusci.yml", "r", encoding="utf-8") as cci_file:
            cci_file.seek(0)
            cci_data = cci_file.read()

        # Check for Placeholder
        legacy_placeholder = cci_data.find("# CUSTOM TASKS ADDED FOR Q BRIX")
        new_placeholder = cci_data.find("# CUSTOM TASKS ADDED FOR Q BRIX DEVELOPMENT")

        if legacy_placeholder == -1 and new_placeholder == -1:
            self.logger.error(
                "Unable to update cumulusci.yml file. Missing placeholder for Q Brix Tasks."
            )
        else:
            # Check for Legacy Placeholder
            use_legacy_placeholder = (
                True if legacy_placeholder >= 0 and new_placeholder == -1 else False
            )

            # Check and update custom tasks
            for custom_task_name, custom_task_class in Q_BRIX_CUSTOM_TASKS.items():
                # Check for task name
                task_name_index = cci_data.find(f"{custom_task_name}:")
                task_class_index = cci_data.find(custom_task_class)

                # Check if Task Name Defined with incorrect class
                if task_name_index > 0 and task_class_index == -1:
                    self.logger.error(
                        " -X WARNING: Task '%s' is defined in the cumulusci.yml file with the incorrect class. Please update manually.",
                        custom_task_name,
                    )
                    continue

                # Check if default name for task has been missed
                if task_name_index == -1 and task_class_index > 0:
                    self.logger.error(
                        " -X WARNING: Custom task class '%s' has been defined although the expected task name was not found. Please update manually.",
                        custom_task_class,
                    )
                    continue

                # Check if task class and name is missing
                if task_name_index == -1 and task_class_index == -1:
                    self.logger.info(
                        " -> Adding Missing Custom Task '%s' to Cumulusci.yml",
                        custom_task_name,
                    )

                    replacement_text = f"# CUSTOM TASKS ADDED FOR Q BRIX DEVELOPMENT\n\n  {custom_task_name}:\n    class_path: {custom_task_class}"

                    if use_legacy_placeholder:
                        replace_file_text(
                            "cumulusci.yml",
                            "# CUSTOM TASKS ADDED FOR Q BRIX",
                            replacement_text,
                        )
                    else:
                        replace_file_text(
                            "cumulusci.yml",
                            "# CUSTOM TASKS ADDED FOR Q BRIX DEVELOPMENT",
                            replacement_text,
                        )

    def _update_folder(self, folder_path, update_dir, remove_existing):
        """Copies Files and Directories from the downloaded update to the corresponding location within the project"""

        if exists(folder_path) and remove_existing:
            shutil.rmtree(folder_path)
        update_path = os.path.join(update_dir, folder_path)
        shutil.copytree(src=update_path, dst=folder_path, dirs_exist_ok=True)

    def _update_file(self, source_file_path, target_file_path):
        """Updates an individual file"""

        shutil.copy(source_file_path, target_file_path)

    def _update_folder_indirect_source(self, folder_path, update_dir, remove_existing):
        """Copies content from an different source root to target"""

        if exists(folder_path) and remove_existing:
            shutil.rmtree(folder_path)

        shutil.copytree(src=update_dir, dst=folder_path, dirs_exist_ok=True)

    def _ensure_required_dirs(self):
        """Ensures that required directories are created"""

        for directory in QBRIX_REQUIRED_DIRECTORIES:
            os.makedirs(directory, exist_ok=True)

    def _replace_string_in_files(
        self, directory, extension, search_string, replace_string
    ):
        """Replaces strings in any file within a directory"""

        if not os.path.exists(directory):
            return

        for root, _, filenames in os.walk(directory):
            for filename in fnmatch.filter(filenames, f"*.{extension}"):
                file_path = os.path.join(root, filename)
                with open(file_path, "r", encoding="utf-8") as file:
                    content = file.read()

                if search_string in content:
                    content = content.replace(search_string, replace_string)

                    with open(file_path, "w", encoding="utf-8") as file:
                        file.write(content)

                    self.logger.info(
                        " -> Replaced '%s' with '%s' in %s",
                        search_string,
                        replace_string,
                        file_path,
                    )

    def _remove_pycache(self, start_path: str = "."):
        for dirpath, dirnames, _ in os.walk(start_path):
            if "__pycache__" in dirnames:
                pycache_path = os.path.join(dirpath, "__pycache__")
                shutil.rmtree(pycache_path)
                self.logger.info("Removed %s", pycache_path)

    def _rebuild_timestamp_file(self, timestamp_file_path):
        if os.path.exists(timestamp_file_path):
            os.remove(timestamp_file_path)
        with open(timestamp_file_path, "w", encoding="utf-8") as stamp_file:
            stamp_file.write(datetime.now().isoformat())
        return True

    def _run_infrequent_checks(self):
        timestamp_file_path = os.path.join(
            UniversalConfig.default_cumulusci_dir(), "qbrix_update_timestamp"
        )

        if os.path.exists(timestamp_file_path):
            # Read the timestamp from the file
            try:
                with open(timestamp_file_path, "r", encoding="utf-8") as stamp_file:
                    timestamp_str = stamp_file.read()
                    timestamp = datetime.fromisoformat(timestamp_str)
            except Exception as e:
                self.logger.info(
                    " - [ERROR] Unable to read timestamp file. Recreating the time stamp file. Error detail: %s",
                    e,
                )
                self._rebuild_timestamp_file(timestamp_file_path)
                return False

            # Calculate the time delta since the timestamp
            delta = datetime.now() - timestamp

            # Check if the delta is greater than 5 days
            if delta > timedelta(days=5):
                self._rebuild_timestamp_file(timestamp_file_path)
                return True
            return False

        self._rebuild_timestamp_file(timestamp_file_path)
        return False

    def _run_task(self):
        """ " Updates the Q brix Project with the latest files from xDO-Template main branch"""

        self.logger.info("STARTING QBRIX UPDATE\n")

        # UPDATE PREFLIGHT
        self.logger.info("Update Preflight:")

        self.logger.info(" -> Ensuring all required directories exist")
        self._ensure_required_dirs()
        self.logger.info(" -> Creating backup copy of update class file")
        if os.path.exists("qbrix/tools/utils/qbrix_update.py"):
            shutil.copyfile(
                "qbrix/tools/utils/qbrix_update.py", ".qbrix/qbrix_update.py"
            )
        self.logger.info(" -> Downloading Latest version of Q Brix Extensions...")
        if download_and_unzip(Q_BRANCH_LOCATION, self.ArchivePassword, False, True):
            # ADD FOLDERS HERE WHICH YOU WANT TO UPDATE IN PROJECT DIRECTORIES
            # PARAM1 = The folder as if it was from the root path
            # PARAM2 = The location where the source files should be located
            # PARAM3 = If True, it will delete the whole directory in project before updating
            self.logger.info(" -> Download Complete!")
            self.logger.info(" -> Patching project")
            self._update_file(
                ".qbrix/Update/xDO-Template-main/playwright.config.ts",
                "./playwright.config.ts",
            )
            self._update_folder("qbrix", ".qbrix/Update/xDO-Template-main", False)
            self._update_folder(".vscode", ".qbrix/Update/xDO-Template-main", False)
            self._update_folder(".github", ".qbrix/Update/xDO-Template-main", False)
            self._update_folder_indirect_source(
                ".git/hooks", ".qbrix/Update/xDO-Template-main/qbrix/git/hooks", False
            )
            self.logger.info(" -> Patching Complete!")

            # we are injecting pre-commit to use our cci extension but we need to make executable
            commit_file = Path(".git/hooks/pre-commit")
            commit_file.chmod(commit_file.stat().st_mode | stat.S_IEXEC)
        self.logger.info(" -> Update Preflight Complete!")

        # FILE CHECKS
        self.logger.info("\nStarting File Checks:\n")
        self.logger.info(" -> Checking custom task classes in cumulusci.yml file")
        self._check_and_deploy_class()
        self.logger.info(" -> Updating robot legacy references in CumulusCI.yml...")
        replace_file_text("cumulusci.yml", "qbrix/robot/tests", "qbrix/robot", False)
        self.logger.info(" -> cumulusci.yml file checks complete!")
        if os.path.exists("robot"):
            self.logger.info(
                " -> Updating robot legacy references in robot/*.robot files..."
            )
            self._replace_string_in_files(
                "robot", "robot", "QRobot.robot", "QRobot.resource"
            )
        if os.path.exists("qbrix_local"):
            self.logger.info(
                " -> Updating robot legacy references in qbrix_local/*.robot files..."
            )
            self._replace_string_in_files(
                "qbrix_local", "robot", "QRobot.robot", "QRobot.resource"
            )
        self.logger.info(" -> Checking .gitignore file")
        upsert_gitignore_entries(Q_BRIX_GITIGNORE_ENTRIES)
        self.logger.info(" -> Checking Trialforce Template IDs in scratch org files:")
        check_scratch_org_files()
        self.logger.info(" -> File Checks Complete!")

        # CUSTOM UPDATE
        self.logger.info("\nStarting Custom Update:\n")
        if self.UpdateLocation:
            self.logger.info(
                " -> Running custom update from %s...", self.UpdateLocation
            )
            download_and_unzip(
                self.UpdateLocation, self.ArchivePassword, self.IgnoreOptionalUpdates
            )
            self.logger.info(" -> Custom update complete!")
        else:
            self.logger.info(" -> No custom updates defined. Check Complete!")

        # CLEANUP
        self.logger.info("\nStarting Cleanup:\n")
        self.logger.info(" -> Cleaning Python Cache")

        # Remove PyCache directories
        self._remove_pycache()

        # Check and Remove any security issues
        if os.path.exists(os.path.join("scripts", "qbrix", "UpdateVSCodeTasks.sh")):
            self.logger.info(" -> Removing old update script")
            os.remove(os.path.join("scripts", "qbrix", "UpdateVSCodeTasks.sh"))
        if os.path.exists(
            os.path.join("config", "user", ".sfdx-hardis.stewart.anderson.yml")
        ):
            self.logger.info(" -> Removing invalid file")
            os.remove(
                os.path.join("config", "user", ".sfdx-hardis.stewart.anderson.yml")
            )

        # Clear CCI Cache
        if os.path.exists(".cci/projects"):
            shutil.rmtree(".cci/projects")

        if os.path.exists(".qbrix/Update"):
            shutil.rmtree(".qbrix/Update")

        # Checking for Updates to CumulusCI and other tooling - no more than once every 7 days
        if not self.SkipDependencyChecks and self._run_infrequent_checks():
            # Run Dependency Updates
            self.logger.info(" -> Checking for required QBrix Project dependencies")
            check_and_update_nodejs()
            update_salesforce_cli()
            cumulusci_update_check()

            # Checking for required py libraries for QBrix
            self.logger.info(" -> Checking for required QBrix Python libraries")
            check_python_library_dependencies()
        self.logger.info(" -> Cleaning Complete!")

        self.logger.info("\nUpdate Complete!")

        if not filecmp.cmp(
            ".qbrix/qbrix_update.py", "qbrix/tools/utils/qbrix_update.py"
        ):
            self.logger.info(
                "\n\n*** THE UPDATE TASK FILE HAS CHANGED - PLEASE RERUN THE UPDATE TASK ***"
            )
            os.remove(".qbrix/qbrix_update.py")
