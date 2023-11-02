import json
import os
import time
from time import sleep

from Browser import ElementState, SelectAttribute
from robot.api.deco import library

from qbrix.core.qbrix_robot_base import QbrixRobotTask


@library(scope="GLOBAL", auto_keywords=True, doc_format="reST")
class QbrixCMS(QbrixRobotTask):

    """Qbrix Salesforce CMS and Digital Experiences Keywords Library"""

    def go_to_digital_experiences(self):
        """Go to the Digital Experiences App"""

        self.shared.go_to_app("Digital Experiences")
        self.shared.wait_for_page_to_load()
        self.builtin.log_to_console("\nDigital Experiences App Loaded")

    def download_all_content(self):
        """Triggers an Export of all Workspaces within the target Salesforce Org. Note that the export emails go to the admin user."""

        self.builtin.log_to_console(
            "\nRunning Automation to export content for ALL WORKSPACES in the org. Please ensure the System Administrator is aware as they will get the exported content emails with the download links."
        )

        # Get Workspace Names
        results = self.salesforceapi.soql_query(
            "SELECT Name FROM ManagedContentSpace WHERE IsDeleted=False"
        )
        if results["totalSize"] == 0:
            self.builtin.log_to_console(
                "\nThere are no CMS Workspaces in the org. Skipping task."
            )
            return

        # Download content from each workspace
        self.builtin.log_to_console(
            f"\n{len(results['records'])} CMS Workspaces in the org. Running export automation..."
        )
        for workspace in results["records"]:
            self.download_cms_content(workspace["Name"])

    def upload_cms_workspace_directories(self):
        """Create a directory within ./datasets/cms_workspaces for each workspace you want to upload files into. The name of the sub-directory needs to match the workspace name and inside the directory you can store the export .zip files, which will be uploaded in order"""

        directory_path = os.path.join("datasets", "cms_workspaces")

        if not os.path.exists(directory_path):
            self.builtin.log_to_console(
                f"\nNo Directories Found to Upload. Sub-directories expected within {directory_path}"
            )
            return

        subdirectories = []

        # Get a list of all subdirectories in the given directory
        for item in os.listdir(directory_path):
            item_path = os.path.join(directory_path, item)
            if os.path.isdir(item_path):
                subdirectories.append(item)

        # Sort subdirectories alphabetically
        subdirectories.sort()

        # Process each subdirectory
        for subdirectory in subdirectories:
            self.builtin.log_to_console(
                f"\nProcessing Workspace Subdirectory: {subdirectory}"
            )

            # Check Workspace
            self.create_workspace(subdirectory, enhanced_workspace=False)

            # Get a list of all files in the subdirectory
            subdirectory_path = os.path.join(directory_path, subdirectory)
            files = [
                f
                for f in os.listdir(subdirectory_path)
                if os.path.isfile(os.path.join(subdirectory_path, f))
            ]
            files.sort(key=lambda x: int(x.split("-")[0]))

            # Print the list of files
            for file_name in files:
                self.builtin.log_to_console(
                    f"\n -> Uploading  {os.path.join(subdirectory_path, file_name)}"
                )
                self.upload_cms_import_file(
                    os.path.join(subdirectory_path, file_name), subdirectory
                )
                self.builtin.log_to_console("\n -> File Upload Complete!")

        self.builtin.log_to_console("\nAll directories processed!")

    def enable_all_channels_for_all_workspaces(self):
        """Ensures that all channels have been applied for all workspaces"""

        self.builtin.log_to_console(
            "\nStarting Q Robot check to ensure that all workspaces have all channels enabled for content..."
        )

        # Get All Workspaces
        results = self.salesforceapi.soql_query(
            "SELECT Id, Name FROM ManagedContentSpace ORDER BY Name"
        )
        if results["totalSize"] == 0:
            self.builtin.log_to_console(
                "\nThere are no CMS Collections currently within the org. Skipping task."
            )
            return

        self.go_to_digital_experiences()

        # Loop through Workspaces
        for workspace in results["records"]:
            self.builtin.log_to_console(
                f"\nLoading Workspace with name [{workspace['Name']}] and Id [{workspace['Id']}]:"
            )

            # Go To Workspace Publishing Targets Page
            self.browser.go_to(
                f"{self.cumulusci.org.instance_url}/lightning/cms/spaces/{workspace['Id']}/publishingTargets?ws=%2Flightning%2Fcms%2Fspaces%2F{workspace['Id']}",
                timeout="30s",
            )
            self.shared.wait_for_page_to_load()

            self.builtin.log_to_console("\n -> Checking Related Channels for Content")

            # Check for Unselected Channels and Enable them

            self.shared.wait_and_click(
                f"{self.shared.iframe_handler()} button:has-text('Add Channel')"
            )

            sleep(2)

            checkbox_elements = self.browser.get_elements(
                "div.slds-checkbox_add-button"
            )

            final_element_list = [
                x
                for x in checkbox_elements
                if not "disabled"
                in self.browser.get_element_states(f"{x} >> input[type='checkbox']")
            ]

            if len(final_element_list) == 0:
                self.builtin.log_to_console("\n -> No additional channels to add.")
                self.browser.click("button.slds-button[title='Close this window']")
            else:
                self.builtin.log_to_console(
                    f"\n -> Checking and enabling {len(final_element_list)} Channels..."
                )

                for check in self.browser.get_elements("div.slds-checkbox_add-button"):
                    self.browser.click(check)

                self.browser.click(
                    f"{self.shared.iframe_handler()} div.modal-footer >> button:has-text('Add')"
                )

                self.shared.wait_and_click(
                    "div.forceModalActionContainer >> button:has-text('Got It')"
                )

                self.builtin.log_to_console("\n -> Additional Channels Enabled!")

                sleep(2)

            close_buttons = self.browser.get_elements(
                "li.tabItem >> div.close >> svg[data-key='close']:visible"
            )

            if len(close_buttons) > 0:
                try:
                    for button in close_buttons:
                        self.shared.wait_and_click(button, "2")
                except Exception as e:
                    # This will error as sub-tabs are also found but then get lost when parent tabs are closed. False positive in a way.
                    continue

            sleep(1)

        self.builtin.log_to_console("\nWorkspace Channel Check Complete!")

    def get_workspace_id(self, workspace_name=None):
        """Returns the ID for a given workspace"""

        if not workspace_name:
            self.builtin.log_to_console(
                "\nError: No workspace name was provided although Robot was requesting the ID. Please check your code."
            )

        self.builtin.log_to_console(
            f"\nLooking up ID for Workspace called [{workspace_name}]"
        )

        results = self.salesforceapi.soql_query(
            f"SELECT Id FROM ManagedContentSpace where Name = '{workspace_name}' LIMIT 1"
        )
        if results["totalSize"] == 1:
            record_id = results["records"][0]["Id"]
            self.builtin.log_to_console(f"\n -> ID Found [{record_id}]")
            return record_id

        self.builtin.log_to_console(
            f"\n -> No workspace found with name [{workspace_name}] in the Salesforce Org"
        )
        return None

    def upload_cms_import_file(self, file_path, workspace):
        """
        Uploads the Content from the CMS import .zip file to a given workspace. If the workspace is not found, then one will be created.

        Args:
            file_path: Relative path to the .zip file containing the export
            workspace: Name of the workspace to upload the content to
        """

        if not file_path:
            raise ValueError("A File Path Must be provided.")

        if not os.path.exists(file_path):
            raise ValueError("The file path provided does not exist")

        if not workspace:
            raise ValueError("No workspace name was provided")

        if not self.get_workspace_id(workspace):
            self.create_workspace(workspace_name=workspace, enhanced_workspace=False)

        # Ensure we are using Digital Experiences App
        self.go_to_digital_experiences()

        # Go To Workspace Page
        workspace_id = self.get_workspace_id(workspace)
        if workspace_id:
            # Go To Workspace
            self.browser.go_to(
                f"{self.cumulusci.org.instance_url}/lightning/cms/spaces/{workspace_id}",
                timeout="30s",
            )
            sleep(2)

            # Import File
            iframe_handler = self.shared.iframe_handler()
            self.shared.wait_and_click(
                f"{iframe_handler} div.slds-page-header__row >> button.slds-button:has-text('Show menu')"
            )
            sleep(2)
            self.browser.promise_to_upload_file(file_path)
            self.browser.click(
                f"{iframe_handler} div.slds-page-header__row >> span.slds-truncate:text-is('Import content'):visible"
            )
            self.browser.wait_for_all_promises()

            # Wait for Confirmation
            wait_counter = 0
            while wait_counter <= 60:
                error_message_selector = "div.modal-body >> div.slds-p-around_medium:has-text('Error encountered during import')"
                confirm_checkbox_selector = (
                    "div.modal-body >> span.slds-checkbox >> span.slds-checkbox_faux"
                )
                import_button_selector = "button.slds-button:has-text('Import')"

                if self.browser.get_element_count(error_message_selector) > 0:
                    raise Exception(
                        "Error Occurred During File Upload. CMS Import Failed"
                    )

                if (
                    self.browser.get_element_count(confirm_checkbox_selector) > 0
                    or self.browser.get_element_count(import_button_selector) > 0
                ):
                    self.builtin.log_to_console(f"\nFile {file_path} - Uploaded OK")
                    break

                wait_counter += 1
                sleep(1)

            # Complete Final Steps
            self.shared.wait_and_click(
                "div.modal-body >> span.slds-checkbox >> span.slds-checkbox_faux"
            )
            self.shared.wait_and_click("button.slds-button:has-text('Import')")
            self.shared.wait_and_click("button.slds-button:text('ok')")
        else:
            self.builtin.log_to_console("\nWorkspace cannot be None. Skipping")
            return

    def download_cms_content(self, workspace):
        """
        Initiate the export of a workspace to a content .zip file (which is emailed to the admin)
        @param workspace: Name of workspace
        @return:
        """

        if not workspace:
            self.builtin.log_to_console("\nWorkspace cannot be None. Skipping")
            return

        self.builtin.log_to_console(
            f"\nRunning automation to export CMS Content from workspace called [{workspace}]...\n Ensure that Salesforce Admin is aware as they will receive the export file email with the download link."
        )

        self.go_to_digital_experiences()

        # Go To Workspace Page
        if workspace:
            workspace_id = self.get_workspace_id(workspace_name=workspace)

            if not workspace_id:
                return

            # Go to the Workspace Page
            self.browser.go_to(
                f"{self.cumulusci.org.instance_url}/lightning/cms/spaces/{workspace_id}",
                timeout="30s",
            )
            self.builtin.log_to_console(
                f"\n -> Loaded workspace called [{workspace}] with ID [{workspace_id}]..."
            )

            # Enhanced workspace handler
            if (
                self.browser.get_element_count(
                    f"{self.shared.iframe_handler()} lightning-badge.slds-badge:has-text('Enhanced'):visible"
                )
                > 0
            ):
                self.builtin.log_to_console(
                    "\n -> Enhanced Workspace Detected! These are not currently supported using this method. Skipping workspace export."
                )
                return

            # Check that the workspace has items
            sleep(2)
            total_cms_elements = self.browser.get_element(
                f"{self.shared.iframe_handler()} p.slds-page-header__meta-text"
            )
            innertext_for_total = self.browser.get_property(
                f"{self.shared.iframe_handler()} p.slds-page-header__meta-text",
                "innerText",
            )
            if innertext_for_total == "0 item(s)":
                self.builtin.log_to_console(
                    "\n -> Workspace was loaded although no items were detected. Skipping this workspace export."
                )
                return

            # Ensure that all items on the page are selected

            self.builtin.log_to_console(
                "\n -> Ensuring that all CMS items are loaded on the page..."
            )
            robot_checkbox_attempts = 0
            iframe_handler = self.shared.iframe_handler()
            while robot_checkbox_attempts <= 10:
                robot_checkbox_attempts += 1

                total_cms_elements = self.browser.get_element(
                    f"{iframe_handler} p.slds-page-header__meta-text"
                )

                if total_cms_elements:
                    innertext_for_total = self.browser.get_property(
                        f"{iframe_handler} p.slds-page-header__meta-text",
                        "innerText",
                    )

                    if innertext_for_total == "0 item(s)":
                        break

                    if innertext_for_total and "+" not in str(innertext_for_total):
                        break

                    if innertext_for_total and "+" in str(innertext_for_total):
                        elements = self.browser.get_elements(
                            f"{iframe_handler} table.slds-table >> sfdc_cms-content-check-box-button"
                        )
                        for elem in elements:
                            self.browser.scroll_to_element(elem)
                else:
                    break

            self.builtin.log_to_console("\n -> Selecting all items on the page...")
            elements = self.browser.get_elements(
                f"{self.shared.iframe_handler()} table.slds-table >> sfdc_cms-content-check-box-button"
            )
            for elem in elements:
                self.browser.scroll_to_element(elem)
                self.browser.click(elem)

            # Request Export
            self.builtin.log_to_console("\n -> Requesting Export of CMS Content...")
            self.browser.click(
                f"{self.shared.iframe_handler()} div.slds-page-header__row >> button.slds-button:has-text('Show menu')"
            )
            self.shared.wait_and_click(
                f"{self.shared.iframe_handler()} div.slds-page-header__row >> div.slds-dropdown__list >> span.slds-truncate:has-text('Export Content')"
            )
            self.shared.wait_and_click(
                f"{self.shared.iframe_handler()} button.slds-button:has-text('Export')"
            )
            self.builtin.log_to_console(
                "\n -> REQUEST SENT! Please check the Salesforce Admin emails for the export email with the download link for the file(s) which contain the content for this workspace."
            )

    def create_workspace(self, workspace_name, channels=None, enhanced_workspace=True):
        """
        Creates a new Digital Experience workspace

        Args:
            workspace_name: Name of the workspace. This must be unique from other workspaces
            channels: (Optional) Channels you want to target. Defaults to all available channels
            enhanced_workspace: (Optional) Set to True if you are creating an Enhanced workspace, otherwise set to False. Defaults to True.
        """

        # Default Channels
        if not channels:
            channels = []

        # Check for existing workspace
        if self.get_workspace_id(workspace_name=workspace_name):
            self.builtin.log_to_console(
                f"The workspace with name {workspace_name} already exists, skipping."
            )
            return

        # Go to Digital Experience Home and initiate Workspace creation
        self.go_to_digital_experiences()

        sleep(3)
        self.builtin.log_to_console("\nCreating New Workspace...")
        self.browser.go_to(
            f"{self.cumulusci.org.instance_url}/lightning/cms/home/", timeout="30s"
        )
        self.builtin.log_to_console("\n -> Loaded CMS Home Page")
        self.shared.wait_and_click(
            f"{self.shared.iframe_handler()} span.label:text-is('Create a CMS Workspace'):visible"
        )
        self.builtin.log_to_console(
            "\n -> Clicked new button to create new CMS Workspace"
        )

        # Enter initial information
        self.shared.wait_and_click(
            "lightning-input:has-text('Name') >> input.slds-input"
        )
        self.browser.fill_text(
            "lightning-input:has-text('Name') >> input.slds-input", workspace_name
        )
        self.builtin.log_to_console(f"\n -> Set name to [{workspace_name}]")

        # Handle enhanced workspace option
        if enhanced_workspace:
            self.builtin.log_to_console("\n -> Setting to Enhanced CMS Workspace")
            self.browser.click(
                "span.slds-text-heading_medium:text-is('Enhanced CMS Workspace')"
            )
        else:
            self.builtin.log_to_console("\n -> Setting to legacy CMS Workspace")
        self.browser.click("button.nextButton:visible")

        # Handle Channel Selection
        self.builtin.log_to_console("\n -> Assigning Channels")
        sleep(3)
        if len(channels) > 0:
            for channel in channels:
                self.builtin.log_to_console(f"\n -> Assigning channel [{channel}]")
                if self.browser.get_element_count(
                    f"tr.slds-hint-parent:has-text('{channel}')"
                ):
                    self.browser.click(
                        f"tr.slds-hint-parent:has-text('{channel}') >> div.slds-checkbox_add-button"
                    )
        else:
            self.builtin.log_to_console("\n -> Assigning ALL Channels")
            channel_count = 0
            for checkbox_add_button in self.browser.get_elements(
                "div.slds-checkbox_add-button"
            ):
                self.browser.click(checkbox_add_button)
                channel_count += 1
            self.builtin.log_to_console(f"\n -> Assigned to {channel_count} channel(s)")
        self.browser.click("button.nextButton:visible")

        # Handle Contributors
        # self.builtin.log_to_console("\n -> Assigning Contributors")
        # sleep(2)
        # for checkbox_add_button in self.browser.get_elements(
        #     "div.forceSelectableListViewSelectionColumn"
        # ):
        #     self.browser.click(checkbox_add_button)

        # # Handle Contributor Access Levels
        # self.browser.click("button.nextButton:visible")
        # sleep(2)
        # for combo_box in self.browser.get_elements("lightning-picklist:visible"):
        #     self.browser.click(combo_box)
        #     sleep(1)
        #     self.browser.click(
        #         "span.slds-listbox__option-text:has-text('Content Admin'):visible"
        #     )
        # self.browser.click("button.nextButton:visible")

        # Handle Language
        sleep(2)
        self.builtin.log_to_console(
            "\n -> Setting Default Language to English (United States)"
        )
        self.browser.click(
            "lightning-combobox.slds-form-element:has-text('Default Language'):visible"
        )
        sleep(1)
        self.browser.click(
            "lightning-base-combobox-item:has-text('English (United States)'):visible"
        )

        # Complete Screen
        self.browser.click("button.nextButton:visible")
        sleep(1)

    def generate_product_media_file(self):
        """
        Generates a Product Media Mapping File, which stores information about Product List Images, Product Detail Images and Attachments related to the products.

        Returns:
            .json file is created within the project and stored at this path: cms_data/product_images.json
        """

        # Get All Active Products which have attached ElectronicMedia
        results = self.salesforceapi.soql_query(
            "SELECT Id, External_ID__c, Name from Product2 WHERE Id IN (Select ProductId from ProductMedia)"
        )
        if results["totalSize"] == 0:
            self.builtin.log_to_console("No Products found with attached media")
            return

        result_dict = {}
        self.shared.go_to_app("Commerce - Admin")

        for product in results["records"]:
            product_dict = {}

            # Set External ID
            product_dict.update({"External_ID__c": product["External_ID__c"]})

            self.browser.go_to(
                f"{self.cumulusci.org.instance_url}/lightning/r/Product2/{product['Id']}/view",
                timeout="30s",
            )
            sleep(4)

            self.browser.click(f"div.uiTabBar >> span.title:text-is('Media')")
            sleep(10)

            # Get Product Detail Images (Max. 8)
            if (
                self.browser.get_element_count(
                    f"article.slds-card:has-text('Product Detail Images'):visible >> img.fileCardImage:visible"
                )
                > 0
            ):
                product_detail_image_list = []
                product_detail_images = self.browser.get_elements(
                    f"article.slds-card:has-text('Product Detail Images'):visible >> img.fileCardImage:visible"
                )
                if product_detail_images:
                    for prod in product_detail_images:
                        prod_property = self.browser.get_property(prod, "alt")
                        if prod_property:
                            print(prod_property)
                            product_detail_image_list.append(prod_property)

                if len(product_detail_image_list) > 0:
                    product_dict.update(
                        {"ProductDetailImages": product_detail_image_list}
                    )

            # Get Product List Image (Max. 1)
            if (
                self.browser.get_element_count(
                    f"article.slds-card:has-text('Product List Image'):visible >> img.fileCardImage:visible"
                )
                > 0
            ):
                product_image_list = []
                product_images = self.browser.get_elements(
                    f"article.slds-card:has-text('Product List Image'):visible >> img.fileCardImage:visible"
                )
                if product_images:
                    for prod in product_images:
                        prod_property = self.browser.get_property(prod, "alt")
                        if prod_property:
                            print(prod_property)
                            product_image_list.append(prod_property)

                if len(product_image_list) > 0:
                    product_dict.update({"ProductImages": product_image_list})

            # Get Attachments (Max. 5)
            if (
                self.browser.get_element_count(
                    f"article.slds-card:has-text('Attachments'):visible >> span.slds-file__text"
                )
                > 0
            ):
                attachment_list = []
                attachment_images = self.browser.get_elements(
                    f"article.slds-card:has-text('Attachments'):visible >> span.slds-file__text"
                )
                if attachment_images:
                    for prod in attachment_images:
                        prod_property = self.browser.get_property(prod, "title")
                        if prod_property:
                            print(prod_property)
                            attachment_list.append(prod_property)

                if len(attachment_list) > 0:
                    product_dict.update({"Attachments": attachment_list})

            self.browser.click(
                f"li.oneConsoleTabItem:has-text('{product['Name']}'):visible >> div.close"
            )

            result_dict.update({f"Product_{product['External_ID__c']}": product_dict})

        # Save dict to file
        if not os.path.exists("cms_data"):
            os.makedirs("cms_data", exist_ok=True)

        with open("cms_data/product_images.json", "w", encoding="utf-8") as save_file:
            json.dump(result_dict, save_file, indent=2)

    def reassign_product_media_files(self):
        """
        Assigns Media Files stored in Salesforce CMS to the relevant Products in the target org.
        """

        # Check for default file
        if not os.path.exists("cms_data/product_images.json"):
            self.builtin.log_to_console(
                "Missing CMS Definition File. Location: cms_data/product_images.json"
            )
            raise Exception(
                "Required file for robot is missing: cms_data/product_images.json. Please check the file and try again."
            )

        # Process Mapping File
        with open("cms_data/product_images.json", "r", encoding="utf-8") as cms_file:
            product_dict = json.load(cms_file)

        if product_dict:
            # Go to Admin Console
            self.shared.go_to_app("Commerce - Admin")

            # Setup Selectors
            media_tab_selector = "div.uiTabBar >> span.title:text-is('Media')"

            # Process Product Records
            for product in dict(product_dict).items():
                results = self.salesforceapi.soql_query(
                    f"SELECT Id, External_ID__c, Name from Product2 WHERE External_ID__c = '{product[1]['External_ID__c']}' LIMIT 1"
                )

                if results["totalSize"] == 0:
                    self.builtin.log_to_console(
                        f"No Products found for the External ID Provided {product[1]['External_ID__c']}. Skipping..."
                    )
                    continue

                try:
                    # Go To Record Page for Product and select Media tab
                    self.browser.go_to(
                        f"{self.cumulusci.org.instance_url}/lightning/r/Product2/{results['records'][0]['Id']}/view",
                        timeout="30s",
                    )
                    self.browser.wait_for_elements_state(
                        media_tab_selector, ElementState.visible, timeout="10s"
                    )
                    self.browser.click(media_tab_selector)
                    sleep(8)
                except TimeoutError:
                    self.builtin.log_to_console(
                        f"\nUnable to access the Media tab for the current Product record with Id ({results['records'][0]['Id']}). Skipping..."
                    )
                    continue
                except Exception as e:
                    raise e

                # Process Product Detail Images
                if (
                    "ProductDetailImages" in dict(product[1]).keys()
                    and self.browser.get_element_count(
                        "article.slds-card:has-text('Product Detail Images'):visible >> img.fileCardImage:visible"
                    )
                    < 8
                ):
                    for product_detail_image in list(product[1]["ProductDetailImages"]):
                        # Check Max. Number of Product Detail Images has not been reached
                        if (
                            self.browser.get_element_count(
                                "article.slds-card:has-text('Product Detail Images'):visible >> img.fileCardImage:visible"
                            )
                            == 8
                        ):
                            self.builtin.log_to_console(
                                "The maximum number of images have already been assigned to the Product. Skipping..."
                            )
                            continue

                        # Check that CMS content has not already been assigned
                        skip = False
                        if (
                            self.browser.get_element_count(
                                "article.slds-card:has-text('Product Detail Images'):visible >> img.fileCardImage:visible"
                            )
                            > 0
                        ):
                            product_detail_images = self.browser.get_elements(
                                "article.slds-card:has-text('Product Detail Images'):visible >> img.fileCardImage:visible"
                            )
                            if product_detail_images:
                                for prod in product_detail_images:
                                    prod_property = self.browser.get_property(
                                        prod, "alt"
                                    )
                                    self.builtin.log_to_console(
                                        f"Found alt text: {prod_property}"
                                    )
                                    if prod_property:
                                        if prod_property in list(
                                            product[1]["ProductDetailImages"]
                                        ):
                                            self.builtin.log_to_console(
                                                "Skipping duplicate..."
                                            )
                                            skip = True
                        if skip:
                            continue

                        # Assign New Image

                        self.browser.click(
                            "article.slds-card:has-text('Product Detail Images'):visible >> :nth-match(button.slds-button:text-is('Add Image'), 1)"
                        )
                        self.browser.wait_for_elements_state(
                            "sfdc_cms-content-uploader-header.slds-col:visible >> input.slds-input",
                            ElementState.visible,
                            timeout="10s",
                        )
                        self.browser.fill_text(
                            "sfdc_cms-content-uploader-header.slds-col:visible >> input.slds-input",
                            product_detail_image,
                        )

                        # Handle Search Results
                        try:
                            sleep(2)
                            search_results = self.browser.get_elements(
                                f"tr.slds-hint-parent:has-text('{product_detail_image}'):visible"
                            )
                            if len(search_results) == 0:
                                self.browser.click(
                                    "button.slds-button:text-is('Cancel')"
                                )
                                continue
                            if len(search_results) > 0:
                                self.browser.click(
                                    "tr:has(span:text-matches('^{}$')) >> th >> span.slds-checkbox_faux".format(
                                        product_detail_image
                                    )
                                )
                                self.browser.click("button.slds-button:text-is('Save')")
                                self.browser.wait_for_elements_state(
                                    media_tab_selector,
                                    ElementState.visible,
                                    timeout="15s",
                                )
                                self.browser.click(media_tab_selector)
                        except TimeoutError:
                            self.builtin.log_to_console(
                                "\nUnable to find any matches for search results. Skipping..."
                            )
                            self.browser.click("button.slds-button:text-is('Cancel')")
                            continue
                else:
                    self.builtin.log_to_console(
                        "\nThe maximum number of images have already been assigned to the Product or there are no Product Detail Images to process. Skipping..."
                    )

                # Process Product List Image

                if (
                    "ProductImages" in dict(product[1]).keys()
                    and self.browser.get_element_count(
                        "article.slds-card:has-text('Product List Image'):visible >> img.fileCardImage:visible"
                    )
                    < 1
                ):
                    for product_image in list(product[1]["ProductImages"]):
                        # Check Max. Number of Product List Images has not been reached
                        if (
                            self.browser.get_element_count(
                                "article.slds-card:has-text('Product List Image'):visible >> img.fileCardImage:visible"
                            )
                            == 1
                        ):
                            self.builtin.log_to_console(
                                "The maximum number of images have already been assigned to the Product. Skipping..."
                            )
                            continue

                        # Check that CMS content has not already been assigned
                        skip = False
                        if (
                            self.browser.get_element_count(
                                "article.slds-card:has-text('Product List Image'):visible >> img.fileCardImage:visible"
                            )
                            > 0
                        ):
                            product_images = self.browser.get_elements(
                                "article.slds-card:has-text('Product List Image'):visible >> img.fileCardImage:visible"
                            )
                            if product_images:
                                for prod in product_images:
                                    prod_property = self.browser.get_property(
                                        prod, "alt"
                                    )
                                    self.builtin.log_to_console(
                                        f"Found alt text: {prod_property}"
                                    )
                                    if prod_property:
                                        if prod_property in list(
                                            product[1]["ProductImages"]
                                        ):
                                            self.builtin.log_to_console(
                                                "Skipping duplicate..."
                                            )
                                            skip = True
                        if skip:
                            continue

                        # Assign New Image

                        self.browser.click(
                            "article.slds-card:has-text('Product List Image'):visible >> :nth-match(button.slds-button:text-is('Add Image'), 1)"
                        )
                        self.browser.wait_for_elements_state(
                            "sfdc_cms-content-uploader-header.slds-col:visible >> input.slds-input",
                            ElementState.visible,
                            timeout="10s",
                        )
                        self.browser.fill_text(
                            "sfdc_cms-content-uploader-header.slds-col:visible >> input.slds-input",
                            product_image,
                        )

                        # Handle Search Results
                        try:
                            sleep(2)
                            search_results = self.browser.get_elements(
                                f"tr.slds-hint-parent:has-text('{product_image}'):visible"
                            )
                            if len(search_results) == 0:
                                self.browser.click(
                                    "button.slds-button:text-is('Cancel')"
                                )
                                continue
                            if len(search_results) > 0:
                                self.browser.click(
                                    "tr:has(span:text-matches('^{}$')) >> td >> span.slds-radio".format(
                                        product_image
                                    )
                                )
                                self.browser.click("button.slds-button:text-is('Save')")
                                self.browser.wait_for_elements_state(
                                    media_tab_selector,
                                    ElementState.visible,
                                    timeout="15s",
                                )
                                self.browser.click(media_tab_selector)
                        except TimeoutError:
                            self.builtin.log_to_console(
                                "Unable to find any matches for search results. Skipping..."
                            )
                            self.browser.click("button.slds-button:text-is('Cancel')")
                            continue
                else:
                    self.builtin.log_to_console(
                        "\nThe maximum number of images have already been assigned to the Product or there are no Product List Images to process. Skipping..."
                    )

                # Process Attachments

                if (
                    "Attachments" in dict(product[1]).keys()
                    and self.browser.get_element_count(
                        "article.slds-card:has-text('Attachments'):visible >> span.slds-file__text"
                    )
                    < 5
                ):
                    for product_attachment in list(product[1]["Attachments"]):
                        # Check Max. Number of Attachments has not been reached
                        if (
                            self.browser.get_element_count(
                                "article.slds-card:has-text('Attachments'):visible >> span.slds-file__text"
                            )
                            == 5
                        ):
                            self.builtin.log_to_console(
                                "The maximum number of attachments have already been assigned to the Product. Skipping..."
                            )
                            continue

                        # Check that CMS content has not already been assigned
                        skip = False
                        if (
                            self.browser.get_element_count(
                                "article.slds-card:has-text('Attachments'):visible >> span.slds-file__text"
                            )
                            > 0
                        ):
                            product_attachments = self.browser.get_elements(
                                "article.slds-card:has-text('Attachments'):visible >> span.slds-file__text"
                            )
                            if product_attachments:
                                for prod in product_attachments:
                                    prod_property = self.browser.get_property(
                                        prod, "title"
                                    )
                                    self.builtin.log_to_console(
                                        f"Found title text: {prod_property}"
                                    )
                                    if prod_property:
                                        if prod_property in list(
                                            product[1]["Attachments"]
                                        ):
                                            self.builtin.log_to_console(
                                                "Skipping duplicate..."
                                            )
                                            skip = True
                        if skip:
                            continue

                        # Assign New Attachment

                        self.browser.click(
                            "article.slds-card:has-text('Attachments'):visible >> :nth-match(button.slds-button:text-is('Add Attachment'), 1)"
                        )
                        self.browser.wait_for_elements_state(
                            "sfdc_cms-content-uploader-header.slds-col:visible >> input.slds-input",
                            ElementState.visible,
                            timeout="10s",
                        )
                        self.browser.fill_text(
                            "sfdc_cms-content-uploader-header.slds-col:visible >> input.slds-input",
                            product_attachment,
                        )

                        # Handle Search Results
                        try:
                            sleep(2)
                            search_results = self.browser.get_elements(
                                f"tr.slds-hint-parent:has-text('{product_attachment}'):visible"
                            )
                            if len(search_results) == 0:
                                self.browser.click(
                                    "button.slds-button:text-is('Cancel')"
                                )
                                continue
                            if len(search_results) > 0:
                                self.browser.click(
                                    "tr:has(span:text-matches('^{}$')) >> th >> span.slds-checkbox_faux".format(
                                        product_attachment
                                    )
                                )
                                self.browser.click("button.slds-button:text-is('Save')")
                                self.browser.wait_for_elements_state(
                                    media_tab_selector,
                                    ElementState.visible,
                                    timeout="15s",
                                )
                                self.browser.click(media_tab_selector)
                        except TimeoutError:
                            self.builtin.log_to_console(
                                "Unable to find any matches for search results. Skipping..."
                            )
                            self.browser.click("button.slds-button:text-is('Cancel')")
                            continue
                else:
                    self.builtin.log_to_console(
                        "\nThe maximum number of attachments have already been assigned to the Product or there are no Product Attachments to process. Skipping..."
                    )

                # Close Tab
                try:
                    self.browser.click(
                        f"li.oneConsoleTabItem:has-text('{results['records'][0]['Name']}'):visible >> div.close"
                    )
                except:
                    continue

    def open_experience_cloud_collections_page(self, experience_cloud_name):
        """Browses to the Collections Page of an Experience Cloud Site"""
        self.shared.go_to_setup_admin_page("SetupNetworks/home", 2)
        self.browser.wait_for_elements_state(
            "iframe >>> table.zen-data", ElementState.visible, "15s"
        )
        if (
            self.browser.get_element_count(
                f"{self.shared.iframe_handler()} div.pbBody >> table.zen-data >> tr.dataRow:has-text('{experience_cloud_name}')"
            )
            > 0
        ):
            self.browser.click(
                f"{self.shared.iframe_handler()} div.pbBody >> table.zen-data >> tr.dataRow:has-text('{experience_cloud_name}') >> a.networkManageLink"
            )
            sleep(2)
            self.browser.switch_page("NEW")
            self.browser.wait_for_elements_state(
                "a.js-workspace-contentManager", ElementState.visible, "15s"
            )
            self.browser.click("a.js-workspace-contentManager")
            self.browser.wait_for_elements_state(
                "a[id=cmcNodeItem-managedContentCollections]",
                ElementState.visible,
                "15s",
            )
            self.browser.click("a[id=cmcNodeItem-managedContentCollections]")
            sleep(1)

    def generate_managed_content_collection_file(self, experience_cloud_name):
        """Generate json file with details of collections"""
        self.open_experience_cloud_collections_page(experience_cloud_name)
        self.browser.wait_for_elements_state(
            "table.slds-table", ElementState.visible, "15s"
        )

        collection_data_dict = dict({})

        # Gather Current Details
        tr_elements = self.browser.get_elements("table.slds-table >> tr:has(a)")

        for elem in tr_elements:
            self.browser.new_page(self.browser.get_property(f"{elem} >> a", "href"))
            self.browser.wait_for_elements_state(
                "h1.slds-page-header__title", ElementState.visible, "15s"
            )

            # Scrape Details
            collection_name = self.browser.get_property(
                "h1.slds-page-header__title", "innerText"
            )
            content_type = self.browser.get_property(
                "li:has(p[title='Content Type']) >> :nth-match(p, 2)", "innerText"
            )

            listview_name = ""
            collection_type = ""
            collection_content_name_list = []

            if (
                self.browser.get_element_count(
                    "li:has(p[title='Content Source']):visible"
                )
                > 0
            ):
                collection_type = "SALESFORCE"
                listview_name = self.browser.get_property(
                    "li:has(p[title='List View']) >> :nth-match(p, 2)", "innerText"
                )
            else:
                collection_type = "CMS"
                sleep(1)
                if self.browser.get_element_count("table.slds-table >> tr:has(a)") > 0:
                    for table_row in self.browser.get_elements(
                        "table.slds-table >> tr:has(a)"
                    ):
                        collection_content_name_list.append(
                            self.browser.get_property(f"{table_row} >> a", "innerText")
                        )

            # Add Details to Dict
            collection_data_dict.update(
                {
                    collection_name: {
                        "collection_type": collection_type,
                        "content_type": content_type,
                        "related_cms_content": collection_content_name_list,
                        "object_name": content_type,
                        "listview": listview_name,
                    }
                }
            )

            self.browser.close_page()

        if collection_data_dict and len(collection_data_dict):
            save_location = os.path.join("datasets", "cms_collection_data")
            os.makedirs(save_location, exist_ok=True)

            if os.path.exists(
                os.path.join(save_location, "cms_collection_dataset.json")
            ):
                os.remove(os.path.join(save_location, "cms_collection_dataset.json"))

            with open(
                os.path.join(save_location, "cms_collection_dataset.json"),
                "w",
                encoding="utf-8",
            ) as save_file:
                save_file.write(json.dumps(collection_data_dict, indent=4))

    def _get_create_collection_button(self):
        """When Uploading CMS Collections, the 'create' button changes depending on number of existing collections. This returns the selector for the correct button"""

        count = 0
        while count <= 10:
            table_button_count = self.browser.get_element_count(
                "button.slds-button:text('New')"
            )
            no_table_button_count = self.browser.get_element_count(
                "button.slds-button:has-text('Create Collection')"
            )

            if table_button_count > 0:
                return "button.slds-button:text('New')"

            if no_table_button_count > 0:
                return "button.slds-button:has-text('Create Collection')"

            count += 1
            sleep(1)

    def reset_cms_collections(
        self,
        site_name,
        upload_file_location=os.path.join(
            "datasets", "cms_collection_data", "cms_collection_dataset.json"
        ),
    ):
        """Deletes collections which match the collections we can upload. Then re-upload the collections"""

        if not os.path.exists(upload_file_location):
            raise Exception("No CMS Collection Data Found. Unable to run the reset.")

        with open(upload_file_location, "r", encoding="utf-8") as dataset_file:
            file_data = json.load(dataset_file)

        if file_data:
            self.enable_all_channels_for_all_workspaces()

            self.open_experience_cloud_collections_page(site_name)

            # Loop Through Collections from the file
            break_loop = False
            for collection, _ in file_data.items():
                self.builtin.log_to_console(f"\nLooking for Collection {collection}")

                counter = 1
                while counter < 1:
                    sleep(1)
                    create_button_count = self.browser.get_element_count(
                        "button.newcollection:has-text('Create Collection')"
                    )
                    table_count = self.browser.get_element_count("table.slds-table")

                    if create_button_count > 0:
                        break_loop = True
                        break

                    if table_count > 0:
                        break_loop = False
                        break

                if break_loop:
                    break

                sleep(1)
                for table_row in self.browser.get_elements(
                    "table.slds-table >> tr:has(a)"
                ):
                    selection_text = self.browser.get_property(
                        f"{table_row} >> a", "innerText"
                    )
                    if selection_text == collection:
                        self.builtin.log_to_console(
                            "\n -> Found Collection... Deleting..."
                        )
                        self.browser.click(
                            f"{table_row} >> lightning-button-menu.slds-dropdown-trigger"
                        )
                        self.shared.wait_and_click(
                            "span.slds-truncate:text-is('Delete')"
                        )
                        self.shared.wait_and_click(
                            "div.modal-footer >> button.slds-button:text-is('Delete')"
                        )
                        self.browser.reload()
                        break

            # Start New Upload
            self.upload_cms_collections(site_name, upload_file_location)

    def upload_cms_collections(
        self,
        site_name,
        upload_file_location=os.path.join(
            "datasets", "cms_collection_data", "cms_collection_dataset.json"
        ),
    ):
        """Uploads the CMS Collections based on the data held within the upload file. By default this is stored within datasets/cms_collection_data/cms_collection_dataset.json"""

        # it's possible that it takes a long time to upload if there are a lot of contents, let's increase the timeout time
        self.browser.set_browser_timeout("1440s")

        if not os.path.exists(upload_file_location):
            raise Exception("No CMS Collection Data Found. Unable to upload.")

        with open(upload_file_location, "r", encoding="utf-8") as dataset_file:
            file_data = json.load(dataset_file)

        if file_data:
            self.open_experience_cloud_collections_page(site_name)

            # Wait for Collections to Load
            no_collection_mode = False
            found_element = False
            counter = 1
            while counter < 10:
                sleep(1)
                create_button_count = self.browser.get_element_count(
                    "button.newcollection:has-text('Create Collection')"
                )
                table_count = self.browser.get_element_count("table.slds-table")

                if create_button_count > 0:
                    no_collection_mode = True
                    found_element = True
                    self.builtin.log_to_console("\nFound Create Collection button...")
                    break

                if table_count > 0:
                    no_collection_mode = False
                    found_element = True
                    self.builtin.log_to_console("\nFound Table button...")
                    break

                counter += 1

            if not found_element:
                self.builtin.log_to_console("\nNo Supported Elements Found")
                return

            # Set Defaults for Robot

            modal_next_button = "div.modal-footer >> button.nextButton"
            collections_to_add = set()

            # Add Content

            if no_collection_mode:
                self.builtin.log_to_console("\n>>> Adding All Collections")

            for collection, collection_details in file_data.items():
                # Check if Collection Exists
                if no_collection_mode:
                    self.builtin.log_to_console(
                        f"\n>>> Adding Create Collection Task for {collection}"
                    )
                    collections_to_add.add(collection)
                else:
                    self.builtin.log_to_console(
                        f"\n>>> Checking Collection {collection}"
                    )
                    collection_found = False
                    for table_row in self.browser.get_elements(
                        "table.slds-table >> tr:has(a)"
                    ):
                        selection_text = self.browser.get_property(
                            f"{table_row} >> a", "innerText"
                        )
                        if selection_text == collection:
                            collection_found = True
                            break

                    if collection_found:
                        self.builtin.log_to_console(
                            f"\n>>> {collection} Found. Skipping"
                        )
                    else:
                        self.builtin.log_to_console(
                            f"\n>>> {collection} will be created"
                        )
                        collections_to_add.add(collection)

            if len(collections_to_add) > 0:
                # Check That Salesforce CRM Connections Have Approved Objects
                salesforce_objects = set()
                for key, collection_detail in file_data.items():
                    if collection_detail.get("collection_type") == "SALESFORCE":
                        salesforce_objects.add(collection_detail.get("content_type"))

                if len(salesforce_objects) > 0:
                    # Check Object is Approved
                    self.shared.wait_and_click("a[id=cmcNodeItem-content]")
                    self.shared.wait_and_click("a[id=cmcNodeItem-managedContentTypes]")
                    sleep(3)

                    for obj in salesforce_objects:
                        self.builtin.log_to_console(f"\nChecking Object: {obj}")
                        object_exists = False
                        if (
                            self.browser.get_element_count("table.slds-table:visible")
                            > 0
                        ):
                            if (
                                self.browser.get_element_count(
                                    f"table.slds-table:visible >> tbody >> tr >> th:has-text('{obj}')"
                                )
                                > 0
                            ):
                                object_exists = True

                        if not object_exists:
                            # Add Object
                            self.shared.wait_and_click(
                                "button:has-text('Add CRM Connections')"
                            )
                            self.browser.fill_text(
                                "div.communitySetupManagedContentMultiSelectTable >> input.slds-input",
                                obj,
                            )
                            sleep(5)
                            if (
                                self.browser.get_element_count(
                                    f"div.listContainer >> table >> tbody >> tr:has-text('{obj}')"
                                )
                                < 1
                            ):
                                self.builtin.log_to_console(
                                    f"\nUnable to find Object called '{obj}'. Skipping"
                                )
                                continue
                            self.browser.click(
                                f"div.listContainer >> table >> tbody >> :nth-match(tr:has-text('{obj}'), 1) >> th >> div.slds-truncate"
                            )
                            self.shared.wait_and_click("button.saveButton")
                            sleep(1)

                    self.shared.wait_and_click(
                        "a[id=cmcNodeItem-managedContentCollections]"
                    )
                    sleep(1)

                for collection_add in collections_to_add:
                    # Create Collection
                    self.shared.wait_and_click(self._get_create_collection_button())

                    # Add Collection Details
                    self.browser.wait_for_elements_state(
                        "div.stepContainer", ElementState.visible, "15s"
                    )
                    collection_data = file_data.get(collection_add)

                    collection_type = collection_data.get("collection_type")
                    content_type = collection_data.get("content_type")
                    cms_collection_content = collection_data.get("related_cms_content")
                    sf_list_view = collection_data.get("listview")

                    self.builtin.log_to_console(
                        f"\nTYPE: {collection_type} - CONTENT_TYPE: {content_type} - LISTVIEW: {sf_list_view}"
                    )

                    # Set Name
                    self.browser.fill_text(
                        "div.stepContainer >> div.slds-form-element__control >> input.slds-input:visible",
                        collection_add,
                    )
                    self.browser.press_keys(
                        "div.stepContainer >> div.slds-form-element__control >> input.slds-input:visible",
                        "Enter",
                    )

                    # Set Type
                    if collection_type == "SALESFORCE":
                        # Add Salesforce Details
                        self.builtin.log_to_console(
                            "\nAdding Salesforce CMS Collection"
                        )
                        self.shared.wait_and_click(
                            "div.stepContainer >> div.slds-visual-picker >> label.crm"
                        )
                        self.shared.wait_and_click(modal_next_button)
                        self.shared.wait_and_click(
                            "div.stepContainer >> button.slds-combobox__input"
                        )
                        self.shared.wait_and_click(
                            f"div.activeStep >> div.slds-listbox >> lightning-base-combobox-item:has-text('{content_type}')"
                        )
                        sleep(5)
                        if (
                            self.browser.get_element_count(
                                f"div.activeStep >> table >> tbody >> tr:has-text('{sf_list_view}')"
                            )
                            < 1
                        ):
                            self.builtin.log_to_console(
                                f"\nUnable to Find List View '{sf_list_view}'"
                            )
                            continue
                        self.shared.wait_and_click(
                            f"div.activeStep >> table >> tbody >> tr:has-text('{sf_list_view}') >> span.slds-radio"
                        )
                        self.shared.wait_and_click(modal_next_button)

                    elif collection_type == "CMS":
                        # Add CMS Content
                        self.builtin.log_to_console("\nAdding CMS Collection")
                        self.shared.wait_and_click(
                            "div.stepContainer >> div.slds-visual-picker >> label.cms"
                        )
                        self.shared.wait_and_click(modal_next_button)
                        self.browser.wait_for_elements_state(
                            "div.slds-select_container >> select.slds-select",
                            ElementState.visible,
                            "20s",
                        )
                        sleep(1)
                        if not any(
                            entry.get("label") == content_type
                            for entry in self.browser.get_select_options(
                                "div.slds-select_container >> select.slds-select"
                            )
                        ):
                            self.builtin.log_to_console(
                                f"\n{content_type} was not found. Check managed content types have been deployed"
                            )
                            self.browser.click("button[title='Close this window']")
                            sleep(1)
                            continue
                        self.browser.select_options_by(
                            "div.slds-select_container >> select.slds-select",
                            SelectAttribute.label,
                            content_type,
                        )
                        self.browser.click(
                            "div.activeStep >> div.slds-visual-picker >> label.manual"
                        )
                        self.shared.wait_and_click(modal_next_button)
                        sleep(2)
                        for cms_content_item in cms_collection_content:
                            cms_content = cms_content_item.replace("'", "\\u2019")

                            self.browser.fill_text(
                                "div.activeStep >> input.slds-input", cms_content
                            )
                            sleep(3)
                            if (
                                self.browser.get_element_count(
                                    f"div.listContainer >> table >> tbody >> tr:has-text('{cms_content}')"
                                )
                                < 1
                            ):
                                self.builtin.log_to_console(
                                    f"\nUnable to find CMS Content called '{cms_content}'. Skipping"
                                )
                                continue
                            self.browser.click(
                                f"div.listContainer >> table >> tbody >> :nth-match(tr:has-text('{cms_content}'), 1) >> th >> :nth-match(div.slds-truncate, 1)"
                            )
                        self.shared.wait_and_click(modal_next_button)
                        sleep(2)

                    else:
                        self.builtin.log_to_console("TYPE NOT FOUND")

                    self.browser.wait_for_elements_state(
                        "a[id=cmcNodeItem-managedContentCollections]",
                        ElementState.visible,
                        "15s",
                    )
                    self.browser.click("a[id=cmcNodeItem-managedContentCollections]")
                    sleep(2)

    def upload_featured_topic_image(
        self, file_path, topic_name, experience_cloud_site, reload_page=True
    ):
        """Uploads the related file image for a featured topic within an experience cloud site.

        Args:
            file_path (str): The relative file path to the image file.
            topic_name (str): The name (label) of the Featured Topic
            experience_cloud_site (str): The label for the Experience Cloud site where the Featured Topics are located.
            reload_page (bool): Defaults to True and loads the Featured Topics page from the setup area. Set to false if uploading multiple images in the same test, after the first image.
        """

        if reload_page:
            self.open_experience_cloud_collections_page(experience_cloud_site)
            self.browser.wait_for_elements_state(
                "a[id='cmcNodeItem-topics']", ElementState.visible, "5s"
            )
            self.browser.click("a[id='cmcNodeItem-topics']")
            self.browser.wait_for_elements_state(
                "a[id='cmcNodeItem-featuredTopics']", ElementState.visible, "5s"
            )
            self.browser.click("a[id='cmcNodeItem-featuredTopics']")

        sleep(5)
        if (
            self.browser.get_element_count(
                f"div.topicRowDefaultContent:has-text('{topic_name}')"
            )
            == 1
        ):
            self.browser.click(
                f"div.topicRowDefaultContent:has-text('{topic_name}') >> a.communitySetupPencilButton"
            )
            sleep(3)
            if (
                self.browser.get_element_count(
                    "span.uploadImageTextBlock:text-is('Upload thumbnail image'):visible"
                )
                == 1
            ):
                upload_promise = self.browser.promise_to_upload_file(file_path)
                self.browser.click("input.topicFileInput:visible")
                self.browser.wait_for(upload_promise)
                sleep(10)
                self.browser.click("button:has-text('Save')")
                sleep(3)
        else:
            self.builtin.log_to_console(
                f"Featured Topic called {topic_name} not found on page, skipping..."
            )
