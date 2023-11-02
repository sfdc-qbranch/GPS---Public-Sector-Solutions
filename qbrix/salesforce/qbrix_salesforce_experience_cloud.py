import glob
import os
from qbrix.tools.shared.qbrix_xml_tasks import find_value_in_sfdx_file
from qbrix.tools.shared.qbrix_console_utils import run_command
from qbrix.tools.shared.qbrix_json_tasks import get_json_file_value


def pre_deploy_all_project_communities(org_alias):

    """Checks that all Experience Cloud bundles have been pre-deployed into the target org"""

    network_files = glob.glob("force-app/main/default/networks/*.network-meta.xml")
    for file_path in network_files:

        # Get Network Information
        site_api_name = None
        site_api_name = find_value_in_sfdx_file(file_path, "picassoSite")
        url_prefix = None
        url_prefix = find_value_in_sfdx_file(file_path, "urlPathPrefix")

        # Get Template
        template = None
        new_template = None

        digital_experience_location = os.path.join(f"force-app/main/default/digitalExperiences/site/{site_api_name}/sfdc_cms__appPage/mainAppPage/content.json")
        experience_bundle_location = os.path.join(f"force-app/main/default/experiences/{site_api_name}/config/mainAppPage.json")
        if os.path.exists(digital_experience_location):
            content_body = get_json_file_value(digital_experience_location, "contentBody")
            new_template = content_body.get("templateName")
        if os.path.exists(experience_bundle_location):
            new_template = get_json_file_value(experience_bundle_location, "templateName")
        if new_template:
            template = new_template

        # Get Site Label Name
        site_name = None
        digital_experience_bundle_location  = os.path.join(f"force-app/main/default/digitalExperiences/site/{site_api_name}/sfdc_cms__site/{site_api_name}/content.json")
        experience_cloud_bundle_location = f"force-app/main/default/experiences/{site_api_name}.site-meta.xml"
        if os.path.exists(experience_cloud_bundle_location):
            site_name = find_value_in_sfdx_file(experience_cloud_bundle_location, "label")
        if os.path.exists(digital_experience_bundle_location):
            site_name = get_json_file_value(digital_experience_bundle_location, "title")

        try:
            resultcode = run_command(f"cci task run create_community --org {org_alias} --timeout 600 --name '{site_name}' --url_path_prefix {url_prefix} --skip_existing True --retries 2 --template '{template}'")

            if resultcode == 0:
                print(f"Create initial site for: {site_name}")
            else:
                print(f"Initial Site Creation Failed for site: {site_name}")
        except Exception as e:
            print(e)
            continue
