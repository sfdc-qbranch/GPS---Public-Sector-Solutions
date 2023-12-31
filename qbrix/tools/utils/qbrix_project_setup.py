import glob
import os
from abc import ABC
from datetime import datetime
from os.path import exists

from cumulusci.core.tasks import BaseTask

from qbrix.tools.shared.qbrix_json_tasks import update_json_file_value
from qbrix.tools.shared.qbrix_project_tasks import (download_and_unzip,
                                                    get_qbrix_repo_url,
                                                    replace_file_text)


class InitProject(BaseTask, ABC):

    """Initializes a Q Brix Project"""

    task_docs = """
    Used to setup the initial project based on the connected Q Brix Repo. Must be run at initial project setup time before you start developing, although can be run anytime there after to update files and settings related to this project.
    """

    task_options = {
        "TestMode": {
            "description": "When in test mode, no files are updated.",
            "required": False
        }
    }

    def _init_options(self, kwargs):
        super(InitProject, self)._init_options(kwargs)
        self.qbrix_owner = self.project_config.project__custom__qbrix_owner_name
        self.qbrix_owner_team = self.project_config.project__custom__qbrix_owner_team
        self.qbrix_publisher_name = self.project_config.project__custom__qbrix_publisher_name
        self.qbrix_publisher_team = self.project_config.project__custom__qbrix_publisher_team
        self.qbrix_documentation_url = self.project_config.project__custom__qbrix_documentation_url or 'https://confluence.internal.salesforce.com/pages/viewpage.action?pageId=487362018'
        self.qbrix_description = self.project_config.project__custom__qbrix_description
        self.project_name = self.project_config.project__name
        self.repo_url = self.project_config.project__git__repo_url
        self.template_file_location = "force-app/main/default/customMetadata/xDO_Base_QBrix_Register.xDO_Template.md-meta.xml"

        self.run_in_test_mode = False
        if "TestMode" in self.options:
            self.run_in_test_mode = self.options["TestMode"]
            if self.run_in_test_mode:
                self.logger.info("Test Mode Enabled. No Files will be updated.")

    def update_create_qbrix_register(self, file_location):

        """Updates the Q Brix Register Detail File"""

        now = datetime.now()

        xml = f"""<?xml version="1.0" encoding="UTF-8"?>
        <CustomMetadata xmlns="http://soap.sforce.com/2006/04/metadata" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema">
            <label>{self.project_name}</label>
            <protected>true</protected>
            <values>
                <field>xDO_Content_Type__c</field>
                <value xsi:type="xsd:string">Metadata_and_Record_Data</value>
            </values>
            <values>
                <field>xDO_Description__c</field>
                <value xsi:type="xsd:string">
                    WHO: {self.qbrix_owner_team} | {self.qbrix_owner}
                    WHAT: {self.qbrix_description}
                    WHEN: {now.strftime("%B %Y")}
                </value>
            </values>
            <values>
                <field>xDO_Documentation_Link__c</field>
                <value xsi:type="xsd:string">{self.qbrix_documentation_url}</value>
            </values>
            <values>
                <field>xDO_Publisher__c</field>
                <value xsi:type="xsd:string">{self.qbrix_publisher_team} | {self.qbrix_publisher_name}</value>
            </values>
            <values>
                <field>xDO_Repository_URL__c</field>
                <value xsi:type="xsd:string">{self.repo_url}</value>
            </values>
            <values>
                <field>xDO_Type__c</field>
                <value xsi:type="xsd:string">Base xDO Component</value>
            </values>
            <values>
                <field>xDO_Version__c</field>
                <value xsi:type="xsd:string">1.0</value>
            </values>
      </CustomMetadata>"""

        if self.run_in_test_mode:
            print(xml)
        else:
            with open(file_location, "w", encoding="utf-8") as qbrix_details_file:
                qbrix_details_file.write(xml)

    def _run_task(self):

        self.logger.info("\nRunning Q Brix Setup Tasks")

        self.logger.info("\nChecking for Q Brix Extension updates...")
        download_and_unzip(q_update=True)

        self.logger.info("\nConfirming Q Brix Repo Address...")
        repo_url = get_qbrix_repo_url()
        if repo_url != "":
            qbrix_name = repo_url.rsplit('/', 1)[-1]
            if qbrix_name is not None and qbrix_name != "":
                self.repo_url = repo_url
                self.project_name = qbrix_name
                self.logger.info(" -> Found Q Brix Name: %s located on GitHub at %s", qbrix_name, repo_url)
        else:
            raise Exception("Unable to determine linked Github Repo. Ensure you are running this command within a CumulusCI project and that you have completed the prerequisites to install and configure Git and GitHub Desktop.")

        # YAML File Update

        self.logger.info("\nConfirming Template Names have been replaced")
        if self.project_config.project__name == "xDO-Template" or self.project_config.project__name != qbrix_name:
            replace_file_text("cumulusci.yml", "xDO-Template", f"{qbrix_name}")
            replace_file_text("cumulusci.yml", f"name: {self.project_name}", f"name: {qbrix_name}")

        replace_file_text("README.md", "Q Brix Title", self.project_name)

        # Registration File Update

        self.logger.info("\nQ Brix Details Check")

        if "OWNER NAME HERE" in self.qbrix_owner:
            self.qbrix_owner = input("\n\nEnter the owner name for this Q Brix (i.e. Who is the contact for issues?): ") or "OWNER NAME HERE"
            replace_file_text("cumulusci.yml", "OWNER NAME HERE", self.qbrix_owner)

        if "OWNER TEAM HERE" in self.qbrix_owner_team:
            self.qbrix_owner_team = input("\n\nEnter the owners team for this Q Brix (e.g. Q Branch): ") or "OWNER TEAM HERE"
            replace_file_text("cumulusci.yml", "OWNER TEAM HERE", self.qbrix_owner_team)

        if "OWNER OR PUBLISHER NAME HERE" in self.qbrix_publisher_name or "OWNER OR PUBLISHER TEAM HERE" in self.qbrix_publisher_team:
            same_person_check = input("\n\nIs the Owner the same person as the publisher? (Default y/n) ") or 'y'
            if same_person_check.lower() == "y":
                replace_file_text("cumulusci.yml", "OWNER OR PUBLISHER NAME HERE", self.qbrix_owner)
                replace_file_text("cumulusci.yml", "OWNER OR PUBLISHER TEAM HERE", self.qbrix_owner_team)
                self.qbrix_publisher_name = self.qbrix_owner
                self.qbrix_publisher_team = self.qbrix_owner_team
            else:

                if "OWNER OR PUBLISHER NAME HERE" in self.qbrix_publisher_name:
                    self.qbrix_publisher_name = input("\n\nEnter the publishers name for this Q Brix (i.e. Who is the contact for publishing updates?): ") or "OWNER OR PUBLISHER NAME HERE"
                    replace_file_text("cumulusci.yml", "OWNER OR PUBLISHER NAME HERE", self.qbrix_publisher_name)

                if "OWNER OR PUBLISHER TEAM HERE" in self.qbrix_publisher_team:
                    self.qbrix_publisher_team = input("\n\nEnter the publisher's team name for this Q Brix (e.g. Q Branch): ") or "OWNER OR PUBLISHER TEAM HERE"
                    replace_file_text("cumulusci.yml", "OWNER OR PUBLISHER TEAM HERE", self.qbrix_publisher_team)

        default_docs_location = "https://confluence.internal.salesforce.com/pages/viewpage.action?pageId=487362018"
        if self.qbrix_documentation_url == "" or self.qbrix_documentation_url == default_docs_location:
            self.qbrix_documentation_url = input("\n\nEnter the URL for documentation related to this Q Brix: ") or default_docs_location
            replace_file_text("cumulusci.yml", default_docs_location, self.qbrix_documentation_url)

        if self.qbrix_description == "" or self.qbrix_description == "SHORT DESCRIPTION OF QBRIX HERE":
            self.qbrix_description = input("\n\nEnter a short description for this Q Brix (e.g. Deploys base configuration for Commerce Cloud): ") or "SHORT DESCRIPTION OF QBRIX HERE"
            replace_file_text("cumulusci.yml", "SHORT DESCRIPTION OF QBRIX HERE", self.qbrix_description)
            if self.qbrix_description != "" and self.qbrix_description != "SHORT DESCRIPTION OF QBRIX HERE":
                replace_file_text("README.md", "Write a few words describing your Q Brix.", self.qbrix_description)

        self.logger.info("Q Brix Details Updated")

        file_name = self.project_name.replace("-", "_")
        final_file_name = f"force-app/main/default/customMetadata/xDO_Base_QBrix_Register.{file_name}.md-meta.xml"

        if exists(final_file_name):
            self.update_create_qbrix_register(final_file_name)
            self.logger.info("Q Brix Registration: Updated Q Brix Register File")
        else:

            # Create Folder and File if they are missing
            if not exists("force-app/main/default/customMetadata"):
                os.mkdir("force-app/main/default/customMetadata")
            else:

                # Clean Up any existing files which would cause issues
                if not exists(self.template_file_location) and not exists(final_file_name):
                    register_files = glob.glob(
                        "force-app/main/default/customMetadata/xDO_Base_QBrix_Register.*.md-meta.xml",
                        recursive=True)
                    for file_to_delete in register_files:
                        os.remove(file_to_delete)
                        self.logger.info("Q Brix Registration: Removed old or incorrect file %s", file_to_delete)

                if exists(self.template_file_location):
                    os.rename(self.template_file_location, final_file_name)
                    self.logger.info("Q Brix Registration: Renamed Q Brix Register File")

                self.update_create_qbrix_register(final_file_name)
                self.logger.info("Q Brix Registration: Updated Q Brix Register File")

        # UPDATE SCRATCH ORG TEMPLATE FILES

        if exists("orgs/dev.json"):
            update_json_file_value("orgs/dev.json", "orgName", f"{self.project_name} - Dev org")
        if exists("orgs/dev_preview.json"):
            update_json_file_value("orgs/dev_preview.json", "orgName", f"{self.project_name} - Dev Preview org")

        self.logger.info("Q Brix Setup: Scratch Org Files Updated")

        self.logger.info(
            "[Q Brix Setup Complete!]\n\n***Remember to update the Readme.md file and check in your changes.***")
