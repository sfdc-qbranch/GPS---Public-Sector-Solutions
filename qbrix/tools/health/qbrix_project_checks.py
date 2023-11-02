import subprocess
import requests
import os
import json
from qbrix.tools.shared.qbrix_cci_tasks import run_cci_task
from qbrix.tools.shared.qbrix_project_tasks import check_and_update_setting
from qbrix.tools.shared.qbrix_console_utils import init_logger
from cumulusci.cli.utils import (get_cci_upgrade_command,
                                 get_installed_version,
                                 get_latest_final_version, timestamp_file)
from qbrix.tools.shared.qbrix_cci_tasks import run_cci_task
from qbrix.tools.shared.qbrix_authentication import *


# Einstein Checks
def run_einstein_checks():
    # Check Bot Settings Exist in force-app folder
    check_and_update_setting(
        "force-app/main/default/settings/Bot.settings-meta.xml",
        "BotSettings",
        "enableBots",
        "true"
    )


# Experience Cloud Checks
def run_experience_cloud_checks():
    # Check Experience Cloud Settings Exist in force-app folder
    check_and_update_setting(
        "force-app/main/default/settings/Communities.settings-meta.xml",
        "CommunitiesSettings",
        "enableNetworksEnabled",
        "true"
    )
    check_and_update_setting(
        "force-app/main/default/settings/ExperienceBundle.settings-meta.xml",
        "ExperienceBundleSettings",
        "enableExperienceBundleMetadata",
        "true"
    )


def run_crm_analytics_checks(org_name):

    """Runs the Analytics Manager in download mode to download related datasets"""

    # Check that datasets are downloaded
    if org_name:
        run_cci_task("analytics_manager", org_name, mode="d", generate_metadata_desc=True)

def cumulusci_update_check():

    """Checks that CumulusCI is up to date and installed"""

    log = init_logger()
    log.info(" -> Checking for updates to CumulusCI")
    try:
        latest_version = get_latest_final_version()
    except requests.exceptions.RequestException:
        log.error("There was an issue retrieving the latest CumulusCI version. Skipping task")

    result = latest_version > get_installed_version()
    if result:
        try:
            subprocess.run(get_cci_upgrade_command(), shell=True, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as update_error:
            error_output = update_error.stderr.strip()
            log.error(" -X Error executing command to update CumulusCI: %s", error_output)

def update_salesforce_cli():

    """Checks that the Salesforce CLi is up to date and installed"""

    log = init_logger()
    log.info(" -> Checking for salesforce CLI Updates")

    subprocess.run(["npm", "install", "-g", "npm@latest"], check=True)
    try:
        # Check if @salesforce/cli is installed globally
        subprocess.run(["npm", "list", "-g", "@salesforce/cli"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

        # If the command above completes without errors, @salesforce/cli is installed
        log.info("@salesforce/cli is installed. Updating...")
        subprocess.run(["npm", "install", "--global", "@salesforce/cli"], check=True)
    except subprocess.CalledProcessError:
        # If @salesforce/cli is not installed, run sfdx update
        log.info("@salesforce/cli is not installed. Running sfdx update...")
        # Uninstall sfdx-cli
        subprocess.run(["npm", "uninstall", "sfdx-cli", "--global"], check=True)
        # Install @salesforce/cli
        subprocess.run(["npm", "install", "@salesforce/cli", "--global"], check=True)

def check_python_library_dependencies():

    """Checks that all python libraries are up to date and installed"""

    log = init_logger()
    log.info(" -> Checking for required QBrix Python libraries")
    run_cci_task("command", org_name=None, command="pip install --upgrade pandas pandasql robotframework-browser")

def check_and_update_nodejs():

    """Checks that you are using the latest LTS version of NodeJS"""

    log = init_logger()
    try:
        # Check if Node.js is installed
        result = subprocess.run(["node", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True, text=True)
        installed_version = result.stdout.strip().replace('v','')

        log.info(f" -> Node.js is installed. Installed version: {installed_version}")

        # Check the latest LTS version from the Node.js website
        latest_lts_version_cmd = subprocess.run(["npm", "view", "node", "dist-tags.lts"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True, text=True)
        latest_lts_version = latest_lts_version_cmd.stdout.strip()

        log.info(f" -> Latest LTS version: {latest_lts_version}")

        if installed_version < latest_lts_version:
            log.info(" -> Updating Node.js to the latest LTS version...")
            subprocess.run(["npm", "install", "--global", f"node@{latest_lts_version}"], check=True)
            log.info(" -> Node.js updated successfully!")
        else:
            log.info(" -> Node.js is already on the latest LTS version.")
    except (subprocess.CalledProcessError, FileNotFoundError):
        log.info(" -> Node.js is not installed or an error occurred while checking/updating.")

def get_template_info(template_id):

    """Checks the given Trialforce Template ID against known templates and returns the latest template ID if known """

    try:
        base_url = qbrix_services_endpoint()
        check_template_url = f"{base_url}/postspin/isknowntemplate/?templateid={template_id}"

        response = requests.get(check_template_url, timeout=60)
        response_json = response.json()

        if "result" in response_json and response_json["result"] == True:
            template_info_url = f"{base_url}/postspin/latesttemplate/?templateid={template_id}"
            template_info_response = requests.get(template_info_url, timeout=60)
            template_info = template_info_response.json()
            if "TemplateId" in template_info and template_info["TemplateId"]:
                return template_info["TemplateId"]
            else:
                return None
    except Exception:
        #fail open - don't impeded
        pass 
    
    return None


def check_scratch_org_files():

    """Checks the scratch org definition files within the qbrix project for Trialforce template IDs. If found, it checks they are the latest"""

    log = init_logger()
    for root, _, files in os.walk("orgs"):
        for file_name in files:
            if file_name.endswith('.json'):
                file_path = os.path.join(root, file_name)
                with open(file_path, 'r+', encoding="utf-8") as file:
                    data = json.load(file)
                    if "template" in data and data["template"]:
                        template_id = data["template"]
                        template_info = get_template_info(template_id)
                        if template_info and template_id != template_info:
                            data["template"] = template_info
                            file.seek(0)
                            json.dump(data, file, indent=2)
                            file.truncate()
                            log.info(f" -> Updated template ID in {file_name}")
