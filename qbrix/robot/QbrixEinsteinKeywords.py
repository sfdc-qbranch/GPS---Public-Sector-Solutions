from time import sleep

from Browser import ElementState
from robot.api.deco import library

from qbrix.core.qbrix_robot_base import QbrixRobotTask


@library(scope="GLOBAL", auto_keywords=True, doc_format="reST")
class QbrixEinsteinKeywords(QbrixRobotTask):

    """Keywords for Qbrix Einstein"""

    def enable_einstein_analytics_crm(self):
        """
        Enable Einstein Analytics CRM within Salesforce Org
        """

        self.builtin.log_to_console("\nChecking Einstein Analytics CRM is enabled")

        # Go To Setup Page
        self.shared.go_to_setup_admin_page("InsightsSetupGettingStarted/home", 5)

        # Check if already enabled
        if self.browser.get_element_count("button.disable-analytics:visible") > 0:
            self.builtin.log_to_console("\nEinstein Analytics CRM is already enabled")
            return

        # Enable Analytics
        self.shared.wait_and_click("button.enable-analytics:visible", 10, 2)

        # Validate Analytics has enabled
        if not self.shared.wait_on_element("button.disable-analytics:visible", 60):
            self.browser.take_screenshot()
            raise Exception(
                "Unable to validate that CRM Analytics has been enabled. Setting was clicked although did not get expected result."
            )

        self.builtin.log_to_console("\nEinstein Analytics CRM is now enabled")

    def check_and_enable_campaign_insights(self):
        """Checks and enabled Campaign Insights"""

        self.builtin.log_to_console("\nChecking Campaign Insights...")

        # Go To Setup Page
        self.go_to_campaign_insights_setup_page()
        toggle_input_selector = f"{self.shared.iframe_handler()} div.box:has-text('Einstein Campaign Insights') >> input[type='checkbox']"

        # Raise error if unable to confirm status
        if not self.shared.wait_on_element(
            toggle_input_selector, 30
        ) and "enabled" not in self.browser.get_element_states(toggle_input_selector):
            self.browser.take_screenshot()
            raise Exception(
                "Error enabling Campaign Insights. Unable to find expected toggle on page or toggle is not enabled."
            )

        self.builtin.log_to_console("\nSetup page loaded")

        # Enable toggle if not already enabled
        if "checked" not in self.browser.get_element_states(toggle_input_selector):
            self.builtin.log_to_console("\nNot enabled yet. Clicking toggle...")
            self.browser.click(
                f"{self.shared.iframe_handler()} div.box:has-text('Einstein Campaign Insights') >> span.slds-checkbox_faux_container"
            )
            sleep(1)
            if "checked" not in self.browser.get_element_states(toggle_input_selector):
                raise Exception(
                    "Error enabling Campaign Insights. Toggle was found and clicked but is not showed as checked."
                )
                self.browser.take_screenshot()
            self.builtin.log_to_console("\nCampaign Insights are now enabled")
        else:
            self.builtin.log_to_console(
                "\nCampaign Insights already enabled. Skipping."
            )

    def check_and_enable_opportunity_insights(self):
        """Checks and enables Opportunity Insights"""

        self.builtin.log_to_console("\nChecking Opportunity Insights...")

        # Go To Setup Page
        self.go_to_opportunity_insights_setup_page()
        toggle_input_selector = f"{self.shared.iframe_handler()} div.slds-box:has-text('Einstein Opportunity Insights') >> input[type='checkbox']"

        # Raise error if unable to confirm status
        if not self.shared.wait_on_element(
            toggle_input_selector, 30
        ) and "enabled" not in self.browser.get_element_states(toggle_input_selector):
            self.browser.take_screenshot()
            raise Exception(
                "Error enabling Opportunity Insights. Unable to find expected toggle on page or toggle is not enabled."
            )

        self.builtin.log_to_console("\nSetup page loaded")

        # Enable toggle if not already enabled
        if "checked" not in self.browser.get_element_states(toggle_input_selector):
            self.builtin.log_to_console("\nNot enabled yet. Clicking toggle...")
            self.browser.click(
                f"{self.shared.iframe_handler()} div.slds-box:has-text('Einstein Opportunity Insights') >> span.slds-checkbox--faux"
            )
            sleep(1)
            if "checked" not in self.browser.get_element_states(toggle_input_selector):
                self.browser.take_screenshot()
                raise Exception(
                    "Error enabling Opportunity Insights. Toggle was found and clicked but its not showing as enabled."
                )
            self.builtin.log_to_console("\nOpportunity Insights Enabled")
        else:
            self.builtin.log_to_console(
                "\nOpportunity Insights already enabled. Skipping."
            )

    def check_and_enable_account_insights(self):
        """Checks and enables Account Insights"""

        self.builtin.log_to_console("\nChecking Account Insights...")

        # Go To Setup Page
        self.go_to_account_insights_setup_page()
        toggle_input_selector = f"{self.shared.iframe_handler()} div.box:has-text('Einstein Account Insights') >> input[type='checkbox']"

        # Raise error if unable to confirm status
        if not self.shared.wait_on_element(
            toggle_input_selector, 30
        ) and "enabled" not in self.browser.get_element_states(toggle_input_selector):
            self.browser.take_screenshot()
            raise Exception(
                "Error enabling Account Insights. Unable to find expected toggle on page or toggle is not enabled."
            )

        self.builtin.log_to_console("\nSetup page loaded")

        # Enable toggle if not already enabled
        if "checked" not in self.browser.get_element_states(toggle_input_selector):
            self.builtin.log_to_console("\nNot enabled yet. Clicking toggle...")
            self.browser.click(
                f"{self.shared.iframe_handler()} div.box:has-text('Einstein Account Insights') >> span.slds-checkbox--faux"
            )
            sleep(1)
            if "checked" not in self.browser.get_element_states(toggle_input_selector):
                self.browser.take_screenshot()
                raise Exception(
                    "Error enabling Account Insights. Toggle was found and clicked but is not showed as checked."
                )
            self.builtin.log_to_console("\nAccount Insights Enabled")
        else:
            self.builtin.log_to_console("\nAccount Insights already enabled. Skipping.")

    def check_and_enable_relationship_insights(self):
        """Checks and enables Relationship Insights"""

        self.builtin.log_to_console("\nChecking Relationship Insights...")

        # Go To Setup Page
        self.go_to_relationship_insights_setup_page()
        toggle_input_selector = f"{self.shared.iframe_handler()} div.slds-card__body:has-text('Einstein Relationship Insights') >> input[type='checkbox']"

        # Raise error if unable to confirm status
        if not self.shared.wait_on_element(
            toggle_input_selector, 30
        ) and "enabled" not in self.browser.get_element_states(toggle_input_selector):
            self.browser.take_screenshot()
            raise Exception(
                "Error enabling Relationship Insights. Unable to find expected toggle on page or toggle is not enabled."
            )

        self.builtin.log_to_console("\nSetup page loaded")

        # Enable toggle if not already enabled
        if "checked" not in self.browser.get_element_states(toggle_input_selector):
            self.builtin.log_to_console("\nNot enabled yet. Clicking toggle...")
            self.browser.click(
                f"{self.shared.iframe_handler()} div.slds-card__body:has-text('Einstein Relationship Insights') >> span.slds-checkbox_faux_container"
            )
            sleep(1)
            if "checked" not in self.browser.get_element_states(toggle_input_selector):
                self.browser.take_screenshot()
                raise Exception(
                    "Error enabling Relationship Insights. Toggle was found and clicked but is not showed as checked."
                )
            self.builtin.log_to_console("\nRelationship Insights Enabled")
        else:
            self.builtin.log_to_console(
                "\nRelationship Insights already enabled. Skipping."
            )

    def check_and_enable_key_accounts(self):
        """Checks and enables Key Account Insights"""

        self.builtin.log_to_console("\nChecking Key Account Insights...")

        # Go To Setup Page
        self.go_to_key_account_insights_setup_page()
        toggle_input_selector = f"{self.shared.iframe_handler()} div.slds-media:has-text('Turn On Einstein Key Accounts Identification') >> input[type='checkbox']"

        # Raise error if unable to confirm status
        if not self.shared.wait_on_element(
            toggle_input_selector, 30
        ) and "enabled" not in self.browser.get_element_states(toggle_input_selector):
            self.browser.take_screenshot()
            raise Exception(
                "Error enabling Key Account Insights. Unable to find expected toggle on page or toggle is not enabled."
            )

        self.builtin.log_to_console("\nSetup page loaded")

        # Enable toggle if not already enabled
        if "checked" not in self.browser.get_element_states(toggle_input_selector):
            self.builtin.log_to_console("\nNot enabled yet. Clicking toggle...")
            self.browser.click(
                f"{self.shared.iframe_handler()} div.slds-media:has-text('Turn On Einstein Key Accounts Identification') >> span.slds-checkbox_faux"
            )
            sleep(1)
            if "checked" not in self.browser.get_element_states(toggle_input_selector):
                self.browser.take_screenshot()
                raise Exception(
                    "Error enabling Key Account Insights. Toggle was found and clicked but is not showed as checked."
                )
            self.builtin.log_to_console("\nKey Account Insights are now enabled.")
        else:
            self.builtin.log_to_console("\nKey Account Insights are already enabled.")

    def check_and_enable_all_insights(self):
        """Runs all core non-industry Insights related keywords"""

        self.builtin.log_to_console("\nEnabling all core Insights...")

        self.check_and_enable_account_insights()
        self.check_and_enable_campaign_insights()
        self.check_and_enable_key_accounts()
        self.check_and_enable_opportunity_insights()

        self.builtin.log_to_console("\nAll Insights enabled!")

    def go_to_campaign_insights_setup_page(self):
        """
        Go directly to the Campaign Insights setup page
        """
        self.shared.go_to_setup_admin_page("CampaignInsights/home", 3)
        self.shared.wait_for_page_to_load()

    def go_to_opportunity_insights_setup_page(self):
        """
        Go directly to the Opportunity Insights setup page
        """
        self.shared.go_to_setup_admin_page("OpportunityInsights/home", 3)
        self.shared.wait_for_page_to_load()

    def go_to_account_insights_setup_page(self):
        """
        Go directly to the Account Insights setup page
        """
        self.shared.go_to_setup_admin_page("AccountInsights/home", 3)
        self.shared.wait_for_page_to_load()

    def go_to_relationship_insights_setup_page(self):
        """
        Go directly to the Relationships Insights setup page
        """
        self.shared.go_to_setup_admin_page("EinsteinSmartTags/home", 3)
        self.shared.wait_for_page_to_load()

    def go_to_key_account_insights_setup_page(self):
        """
        Go directly to the Key Accounts Insights setup page
        """
        self.shared.go_to_setup_admin_page("EKAI/home", 5)
        self.shared.wait_for_page_to_load()

    def go_to_lead_scoring_setup_page(self):
        """
        Go directly to the Lead Scoring setup page and check its enabled
        """
        self.shared.go_to_setup_admin_page("LeadIQ/home", 3)
        self.browser.wait_for_elements_state(
            "h1:has-text('Einstein Lead Scoring')", ElementState.visible, "30s"
        )
        self.builtin.log_to_console("\nLoaded Setup Page")

        if (
            self.browser.get_element_count("h3:text-is('Einstein Lead Scoring is off')")
            > 0
        ):
            self.builtin.log_to_console(
                "\nEinstein Lead Scoring is not currently enabled."
            )
            self.browser.click(":nth-match(span.slds-checkbox_faux, 1)")
            self.shared.wait_and_click("label:has-text('Default')")
            self.shared.wait_and_click(".slds-button:has-text('Save')")

        if not self.shared.wait_on_element(
            "h3:text-is('Einstein Lead Scoring is on')", 30
        ):
            raise Exception("Lead Scoring failed to enable. Checked script.")

        self.builtin.log_to_console("\nLead Scoring Enabled")

    def go_to_oppty_scoring_setup_page(self):
        """
        Check and Enable Opportunity Scoring
        """

        # Go To Setup Page
        self.shared.go_to_setup_admin_page("OpportunityIQSetupHome/home")
        self.browser.wait_for_elements_state(
            "h1:has-text('Einstein Opportunity Scoring')", ElementState.visible, "30s"
        )
        self.builtin.log_to_console("\nLoaded Setup Page")

        if self.shared.wait_on_element(".slds-button:has-text('Set Up')", 3):
            self.builtin.log_to_console("\nOpportunity Scoring is not yet enabled...")
            self.browser.click(".slds-button:has-text('Set Up')")
            self.shared.wait_and_click(".slds-button:has-text('Next')")
            self.shared.wait_and_click(".slds-button:has-text('Next')")
            self.shared.wait_and_click(".slds-button:has-text('Next')")
            self.shared.wait_and_click(".slds-button:has-text('Next')")
            self.shared.wait_and_click(".slds-button:has-text('Start')")
            sleep(5)
            self.shared.go_to_setup_admin_page("OpportunityIQSetupHome/home")
            if not self.shared.wait_on_element(
                "button.slds-button:has-text('Review Settings')"
            ):
                raise Exception("Opportunity Scoring did not enable as expected.")

        self.builtin.log_to_console("\nOpportunity Scoring Enabled")

    def enable_automated_data_capture(self):
        """Check and Enable Automated Data Capture"""

        # Load Setup Page
        self.shared.go_to_setup_admin_page("AutomatedDataCapture/home")
        self.browser.wait_for_elements_state(
            "h1:has-text('Einstein Automated Contacts')", ElementState.visible, "30s"
        )
        self.shared.wait_on_element(":nth-match(span.slds-checkbox--faux,1)")
        self.builtin.log_to_console("\nLoaded Setup Page")

        # Ensure All Toggles are On
        self.builtin.log_to_console("\nChecking all toggles are on")
        for toggle in self.browser.get_elements("span.slds-checkbox--faux"):
            if "checked" not in self.browser.get_element_states(toggle):
                self.browser.click(toggle)

        sleep(2)
        self.shared.go_to_setup_admin_page(
            setup_page_url="AutomatedDataCapture/home", force_reload=True
        )

        # Validate All Checkboxes are Toggled ON
        for toggle in self.browser.get_elements("span.slds-checkbox--faux"):
            if "checked" not in self.browser.get_element_states(toggle):
                raise Exception(
                    "Not all settings were enabled when switching on Automated Data Capture. Please check configuration."
                )

        self.builtin.log_to_console("\nAutomated Data Capture enabled!")

    def enable_einstein_prediction_builder(self):
        """Enable Einstein Prediction Builder"""

        # Go To Setup Page
        self.shared.go_to_setup_admin_page("EinsteinBuilder/home")
        self.builtin.log_to_console("\nLoaded Setup Page ")

        # While There is a Get Started button, click it
        attempt_counter = 1
        while attempt_counter <= 10:
            self.builtin.log_to_console(
                f"\n Attempt {attempt_counter} to enable Einstein Prediction Builder"
            )

            if (
                self.browser.get_element_count("button:has-text('Get Started'):visible")
                > 0
            ):
                self.builtin.log_to_console("\nClicking Get Started ")
                self.browser.click("button:has-text('Get Started')")
                if not self.shared.wait_on_element(
                    "li.statusColumn >> input[name='einsteinBuilderPrefSwitch']", 30
                ):
                    self.builtin.log_to_console(
                        "\nPrediction Builder has not yet loaded... waiting 10 seconds before trying again "
                    )
                    sleep(10)
                else:
                    if "checked" in self.browser.get_element_states(
                        "li.statusColumn >> input[name='einsteinBuilderPrefSwitch']"
                    ):
                        self.builtin.log_to_console(
                            "\nPrediction Builder is now enabled!"
                        )
                        break
                    else:
                        self.builtin.log_to_console(
                            "\nPrediction Builder is turned off... turning back on"
                        )
                        self.browser.click(
                            "li.statusColumn >> span.slds-checkbox_faux_container"
                        )
                        sleep(3)
                        if "checked" in self.browser.get_element_states(
                            "li.statusColumn >> input[name='einsteinBuilderPrefSwitch']"
                        ):
                            self.builtin.log_to_console(
                                "\nPrediction Builder is now enabled!"
                            )
                            break

            if (
                self.browser.get_element_count(
                    "li.statusColumn >> input[name='einsteinBuilderPrefSwitch']"
                )
                > 0
            ):
                if "checked" in self.browser.get_element_states(
                    "li.statusColumn >> input[name='einsteinBuilderPrefSwitch']"
                ):
                    self.builtin.log_to_console("\nPrediction Builder is now enabled!")
                    break
                else:
                    self.builtin.log_to_console(
                        "\nPrediction Builder is turned off... turning back on"
                    )
                    self.browser.click(
                        "li.statusColumn >> span.slds-checkbox_faux_container"
                    )
                    sleep(3)
                    if "checked" in self.browser.get_element_states(
                        "li.statusColumn >> input[name='einsteinBuilderPrefSwitch']"
                    ):
                        self.builtin.log_to_console(
                            "\nPrediction Builder is now enabled!"
                        )
                        break

            self.shared.go_to_setup_admin_page(
                setup_page_url="EinsteinBuilder/home", force_reload=True
            )
            attempt_counter += 1
            sleep(1)

    def enable_einstein_key_accounts_identification(self):
        """No Longer Used"""

        # Replacement Keyword added for legacy requests
        self.check_and_enable_key_accounts()

    def enable_einstein_activity_capture(self):
        """
        Enables Einstein Activity Capture with Office 365 and oAuth 2.0
        SE Setup Guide: https://salesforce.quip.com/JTI7AfkGt4DM
        """

        # Go To Setup Page
        self.shared.go_to_setup_admin_page("ActivitySyncEngineSettingsMain/home", 3)
        self.builtin.log_to_console("\nLoaded Setup Page ")

        if (
            self.browser.get_element_count(
                "li.datasource-entry:has-text('Microsoft Office 365')"
            )
            > 0
        ):
            self.builtin.log_to_console(
                "\nEAC Already Enabled for Microsoft Office 365"
            )
            return

        # Enable.. yep there 3 variations for the setup button

        if self.shared.wait_on_element(
            "button.slds-button:has-text('Turn On Einstein Activity Capture')", 1
        ):
            self.shared.wait_and_click(
                "button.slds-button:has-text('Turn On Einstein Activity Capture')"
            )
            self.builtin.log_to_console(
                "\n EAC was already setup but turned off. Turning back on."
            )
            return

        if self.shared.wait_on_element("button.slds-button:has-text('Get Started')", 2):
            self.shared.wait_and_click("button.slds-button:has-text('Get Started')")

        if self.shared.wait_on_element(
            "button.slds-button:has-text('Add Contact and Event Sync')", 2
        ):
            self.shared.wait_and_click(
                "button.slds-button:has-text('Add Contact and Event Sync')"
            )

        # Set Email and Calendar Service
        self.builtin.log_to_console("\nConnecting Email and Calendar Service ")
        self.shared.wait_and_click("div.slds-radio:has-text('Microsoft Office 365')")
        self.shared.wait_and_click(
            "footer >> button.slds-button:has-text('Next'):visible"
        )

        # Set Authentication Type
        self.builtin.log_to_console("\n Configuring default authentication type")
        self.shared.wait_and_click(
            "div.slds-visual-picker:has-text('User-Level OAuth 2.0') >> span.slds-visual-picker__figure"
        )
        self.shared.wait_and_click(
            "footer >> button.slds-button:has-text('Next'):visible"
        )

        # Name Configuration
        self.builtin.log_to_console("\n Finalizing addition settings")
        sleep(1)
        self.browser.fill_text(
            "lightning-input:has-text('Name') >> input", "Demo O365 EAC Configuration"
        )
        self.shared.wait_and_click(
            "footer >> button.slds-button:has-text('Next'):visible"
        )

        # Sync Settings
        self.shared.wait_and_click(
            "footer >> button.slds-button:has-text('Next'):visible"
        )

        # Advanced Settings
        self.shared.wait_and_click(
            "footer >> button.slds-button:has-text('Next'):visible"
        )

        # Add All Users
        self.builtin.log_to_console("\nAdding all Users with an EAC licence ")
        sleep(1)
        total_elements = len(
            self.browser.get_elements(
                "div.slds-dueling-list__column:has-text('Available') >> li.slds-listbox__item"
            )
        )
        while total_elements > 0:
            self.browser.click(
                "div.slds-dueling-list__column:has-text('Available') >> :nth-match(li.slds-listbox__item, 1)"
            )
            self.browser.click("button[title='Add']")
            total_elements -= 1

        # Add System Admin Profile
        self.builtin.log_to_console("\nAdding System Administrator Profile ")
        self.browser.click("lightning-base-combobox:visible")
        self.browser.click("lightning-base-combobox-item:has-text('Profiles')")
        sleep(1)
        self.browser.click("li.slds-listbox__item:has-text('System Administrator')")
        self.browser.click("button[title='Add']")

        self.shared.wait_and_click(
            "footer >> button.slds-button:has-text('Next'):visible"
        )

        try:
            # These Settings Only Come up for the first one. So we quietly fail on these if they are not there

            # Exclude Addresses
            self.shared.wait_and_click(
                "footer >> button.slds-button:has-text('Next'):visible", 1
            )

            # Default Sharing
            self.browser.click(
                "div.emailStreamIconLabel:has-text('Share with Everyone')", 1
            )
            self.shared.wait_and_click(
                "footer >> button.slds-button:has-text('Next'):visible", 1
            )
        except:
            pass

        # Finish
        self.builtin.log_to_console("\nCompleting Setup ")
        self.shared.wait_and_click(
            "footer >> button.slds-button:has-text('Finish'):visible"
        )

        # Validate it Complete
        self.builtin.log_to_console(
            "\nWaiting for confirmation that EAC is enabled... "
        )
        if not self.shared.wait_on_element(
            "li.datasource-entry:has-text('Microsoft Office 365')", 120
        ):
            raise Exception(
                "Einstein Activity Capture Error - Could not confirm if EAC enabled correctly."
            )

        self.builtin.log_to_console("\nEAC is now enabled")

    def enable_einstein_forecasting(self):
        """Checks and Enabled Einstein Forecasting in the target Salesforce Org"""

        self.builtin.log_to_console("\nChecking Einstein Forecasting is enabled...")

        # Loaded Forecasting Setup Page
        self.shared.go_to_setup_admin_page(
            setup_page_url="ForecastingPrediction/home", force_reload=True
        )
        self.browser.wait_for_elements_state(
            "h1:has-text('Einstein Forecasting')", ElementState.visible, "30s"
        )
        sleep(2)
        self.builtin.log_to_console("\nLoaded Setup Page...")

        # Check if already enabled
        if self.shared.wait_on_element(".slds-button:has-text('Disable')", 2):
            self.builtin.log_to_console("\nEinstein Forecasting already enabled")
            return

        # Enable
        if self.shared.wait_on_element(".slds-button:has-text('Enable')", 2):
            self.builtin.log_to_console("\nEnabling Einstein Forecasting...")
            self.shared.wait_and_click(".slds-button:has-text('Enable')")
            if not self.shared.wait_on_element(".slds-button:has-text('Disable')", 60):
                raise Exception(
                    "Attempted to enable Einstein Forecasting but unable to confirm."
                )
            else:
                self.builtin.log_to_console("\nEinstein Forecasting is now enabled.")

    def enable_call_coaching_eci(self):
        """Check and Enable Call Coaching"""

        # Load Setup Page
        self.shared.go_to_setup_admin_page("CallCoachingSettings/home")
        if not self.shared.wait_on_element(
            "header:has-text('Conversation Insights Are Here!')", 30
        ):
            raise Exception("Unexpected Page format. Unable to enable Call Coaching")

        # Check if enabled
        if not self.shared.wait_on_element("button:has-text('Enable ECI')", 3):
            self.builtin.log_to_console("\nCall Coaching is already enabled.")
        else:
            self.builtin.log_to_console(
                "\nCall Coaching is NOT enabled. Clicking button to enable."
            )
            self.browser.click("button:has-text('Enable ECI')")

            while (
                self.browser.get_element_count("button:has-text('Enable ECI'):visible")
                > 0
            ):
                sleep(2)

            self.builtin.log_to_console("\nCall Coaching is now enabled.")

    def enable_einstein_classification(self):
        """Enable Einstein Case Classification"""

        self.shared.go_to_setup_admin_page(
            setup_page_url="EinsteinCaseClassification/home", force_reload=True
        )
        self.browser.wait_for_elements_state(
            "h1:has-text('Einstein Classification')", ElementState.visible, "15s"
        )
        self.shared.wait_on_element("div.case-classification-pref", 10)
        self.builtin.log_to_console("\nEinstein Case Classification setup page loaded.")

        if (
            self.browser.get_element_count(
                "div.case-classification-pref >> span.slds-checkbox_on:visible"
            )
            > 0
        ):
            self.builtin.log_to_console("\nEinstein Case Classification is enabled.")
            return

        if (
            self.browser.get_element_count(
                "div.case-classification-pref >> span.slds-checkbox_off:visible"
            )
            > 0
        ):
            self.builtin.log_to_console(
                "\nEinstein Case Classification is NOT enabled."
            )
            self.browser.click(
                "div.case-classification-pref >> label.slds-checkbox_toggle:has-text('Einstein Classification Apps')"
            )

        # Assign Permission Set to Admin User
        self.cumulusci.run_task(
            task_name="assign_permission_sets", api_names="EinsteinAgent"
        )

        if not self.shared.wait_on_element(
            "div.case-classification-pref >> span.slds-checkbox_on:visible", 30
        ):
            raise Exception("Einstein Case Classification failed to enable.")

        sleep(3)
        self.builtin.log_to_console("\nEinstein Case Classification is now enabled.")

    def einstein_case_classification_post_setup(self):
        """Complete Additional Setup for Case Classification for SDO"""

        # Check that Classification is Enabled
        self.enable_einstein_classification()
        iframe_handle = self.shared.iframe_handler()

        # Get All Listed Models (Which should now be at Ready to Activate Status)
        self.browser.wait_for_elements_state(
            f"{iframe_handle} :nth-match(#modelTable, 1)", ElementState.visible, "15s"
        )
        models = self.browser.get_elements(
            f"{iframe_handle} #modelTable >> tbody >> tr"
        )

        # Check Models - If any of the models are not Ready to Active status, rebuild is needed
        rebuild_needed = False
        for model in models:
            model_status = self.browser.get_property(
                f"{model} >> td.modelStatus", "innerText"
            )
            if model_status and model_status not in ("Ready to Activate", "Active"):
                rebuild_needed = True
                break

        if rebuild_needed:
            # Disable Classification - Yes I know, this is the way...
            self.browser.click(
                "label.slds-checkbox_toggle:has-text('Einstein Classification Apps')"
            )
            self.shared.wait_and_click("button.slds-button:has-text('Turn Off')")

            # Enable Classification... AGAIN (This is by design...)
            self.enable_einstein_classification()

            self.browser.wait_for_elements_state(
                f"{iframe_handle} :nth-match(#modelTable, 1)",
                ElementState.visible,
                "15s",
            )

        for model in models:
            model_status = self.browser.get_property(
                f"{model} >> td.modelStatus", "innerText"
            )

            # Handle Ready to Activate
            if model_status == "Ready to Activate":
                self.browser.click(f"{model} >> td.modelName >> button")
                sleep(2)
                self.browser.click(
                    "div.ccProgressStepButtons >> button.slds-button:has-text('Activate')"
                )
                sleep(2)
                self.browser.click(
                    "div.modal-footer >> button.slds-button:has-text('Activate')"
                )
                sleep(1)

            # Return to main setup page
            self.shared.go_to_setup_admin_page(
                setup_page_url="EinsteinCaseClassification/home", force_reload=True
            )
            sleep(1)

    def eac_enabled_enhanced_email_pane(self):
        """
        Creates a new default Application Pane for Outlook Integration with EAC. Note that this assumes that EAC and Salesforce Inbox features have been enabled.
        """

        # Enable Enhanced Application Pane
        self.shared.go_to_setup_admin_page("LightningForOutlookAndSyncSettings/home")
        sleep(1)

        iframe_handler = self.shared.iframe_handler()

        if "visible" not in self.browser.get_element_states(
            f"{iframe_handler} h2:text-is('Give Users the Integration in Outlook')"
        ):
            self.browser.click(
                f"{iframe_handler} button.slds-button:text-is('Let users access Salesforce records from Outlook')"
            )
            sleep(1)

        self.browser.click(
            f"{iframe_handler} button.slds-button:has-text('Create New Pane')"
        )
        self.browser.click(
            f"{iframe_handler} span.slds-truncate:has-text('With Inbox Features (License Required)')"
        )
        sleep(5)
        self.browser.switch_page("NEW")
        self.browser.click("button.slds-button:has-text('Save')")
        sleep(1)
        self.browser.click("button.slds-button:has-text('Activate')")
        sleep(3)
        self.browser.click("button.slds-button:has-text('Next')")
        sleep(1)
        self.browser.click("button.slds-button:has-text('Activate')")
        sleep(2)

    def eac_outlook_integration_setup(self):
        """
        Runs the initial setup for the Einstein Activity Capture Outlook Integration
        """

        # Check that initial settings have been activated
        self.shared.go_to_setup_admin_page("LightningForOutlookAndSyncSettings/home")
        sleep(1)

        iframe_handler = self.shared.iframe_handler()

        if "checked" not in self.browser.get_element_states(
            f"{iframe_handler} div.slds-card__header:has-text('Outlook Integration') >> input"
        ):
            self.browser.click(
                f"{iframe_handler} div.slds-card__header:has-text('Outlook Integration') >> input"
            )
            sleep(1)

        if "visible" not in self.browser.get_element_states(
            f"{iframe_handler} h2:text-is('Give Users the Integration in Outlook')"
        ):
            self.browser.click(
                f"{iframe_handler} button.slds-button:text-is('Let users access Salesforce records from Outlook')"
            )
            sleep(1)

        if "checked" not in self.browser.get_element_states(
            f"{iframe_handler} div.slds-card__header:has-text('Use Enhanced Email with Outlook') >> input"
        ):
            self.browser.click(
                f"{iframe_handler} div.slds-card__header:has-text('Use Enhanced Email with Outlook') >> input"
            )
            sleep(1)

        if "checked" not in self.browser.get_element_states(
            f"{iframe_handler} div.slds-card__header:has-text('Customize Content with App Builder') >> input"
        ):
            self.browser.click(
                f"{iframe_handler} div.slds-card__header:has-text('Customize Content with App Builder') >> input"
            )
            sleep(1)

        # Check and enable Salesforce Inbox Settings
        self.shared.go_to_setup_admin_page("EmailIqSetupPage/home")
        sleep(1)

        iframe_handler = self.shared.iframe_handler()

        if "checked" not in self.browser.get_element_states(
            f"{iframe_handler} div.slds-card__header:has-text('Make Inbox Available to Users') >> input"
        ):
            self.browser.click(
                f"{iframe_handler} div.slds-card__header:has-text('Make Inbox Available to Users') >> span.slds-checkbox--faux"
            )
            sleep(1)

        if "checked" not in self.browser.get_element_states(
            f"{iframe_handler} div.emailStreamEmailIqSetupRow:has-text('External Email Tracking') >> input"
        ):
            self.browser.click(
                f"{iframe_handler} div.emailStreamEmailIqSetupRow:has-text('External Email Tracking') >> span.slds-checkbox--faux"
            )
            sleep(1)

        if "checked" not in self.browser.get_element_states(
            f"{iframe_handler} div.emailStreamEmailIqSetupRow:has-text('Internal Email Tracking') >> input"
        ):
            self.browser.click(
                f"{iframe_handler} div.emailStreamEmailIqSetupRow:has-text('Internal Email Tracking') >> span.slds-checkbox--faux"
            )
            sleep(1)

        # Assign Required Permissions to running user
        self.cumulusci.run_task(
            task_name="assign_permission_sets",
            api_names="InboxWithEinsteinActivityCapture",
        )
        sleep(3)

    def einstein_article_recommendations_setup(self):
        """
        Runs the Einstein Article Recommendations Setup
        """
        iframe_handler = self.shared.iframe_handler()

        # Make sure we are on Einstein Article Recommendations page
        self.shared.go_to_setup_admin_page("EinsteinArticleRecommendations/home")
        self.browser.wait_for_elements_state(
            "h1:has-text('Einstein Article Recommendations')",
            ElementState.visible,
            "30s",
        )
        sleep(2)

        # Make sure Einstein Article Recommendations is turned on
        if not "checked" in self.browser.get_element_states(
            "label:has-text('Einstein Article Recommendations')"
        ):
            self.browser.click("label:has-text('Off')")
            sleep(3)

        if self.shared.wait_on_element("h2:has-text('Your model is active!')"):
            self.builtin.log_to_console("\nEinstein Article Recommendations Activated")
            return

        # Finish if Einstein Article Recommendations model is already active
        if not "visible" in self.browser.get_element_states(
            "button:has-text('Let\\'s go')"
        ):
            print("already done setup")
            return

        # If not, let's active the model
        self.shared.click_button_with_text("Let\\'s go")
        self.shared.click_button_with_text("Next")
        self.shared.click_button_with_text("Next")

        # Select primary field for Case
        self.browser.click("lightning-combobox:has-text('Choose a primary field')")
        self.browser.click(
            "lightning-combobox:has-text('Choose a primary field') lightning-base-combobox-item >> span.slds-truncate:text-is('Subject')"
        )
        sleep(1)

        # Choose supporting fields
        if 1 == self.browser.get_element_count(
            "div.slds-dueling-list__column_responsive:has-text('Available Fields') li span:text-is('Description')"
        ):
            self.browser.click(
                "div.slds-dueling-list__column_responsive:has-text('Available Fields') li span:text-is('Description')"
            )
            self.browser.click("button[title='Move selection to Selected Fields']")
            sleep(1)
        else:
            return

        self.shared.click_button_with_text("Next")

        # Select knowledge title field
        self.browser.click("lightning-combobox:has-text('Knowledge Title Field')")
        self.browser.click(
            "lightning-combobox:has-text('Knowledge Title Field') lightning-base-combobox-item >> span.slds-truncate:text-is('Title')"
        )
        sleep(1)

        # Select knowledge summary field
        self.browser.click("lightning-combobox:has-text('Knowledge Summary Field')")
        self.browser.click(
            "lightning-combobox:has-text('Knowledge Summary Field') lightning-base-combobox-item >> span.slds-truncate:text-is('Summary')"
        )
        sleep(1)

        # Choose additional fields
        if 1 == self.browser.get_element_count(
            "div.slds-dueling-list__column_responsive:has-text('Available Fields') li span:text-is('Details')"
        ):
            self.browser.click(
                "div.slds-dueling-list__column_responsive:has-text('Available Fields') li span:text-is('Details')"
            )
            # somehow, the button[title='Move selection to Selected Fields'] came back with two results, the 2nd is the true button to click
            self.browser.click(
                ":nth-match(button[title='Move selection to Selected Fields'],2)"
            )
            sleep(1)
        if 1 == self.browser.get_element_count(
            "div.slds-dueling-list__column_responsive:has-text('Available Fields') li span:text-is('Question')"
        ):
            self.browser.click(
                "div.slds-dueling-list__column_responsive:has-text('Available Fields') li span:text-is('Question')"
            )
            # somehow, the button[title='Move selection to Selected Fields'] came back with two results, the 2nd is the true button to click
            self.browser.click(
                ":nth-match(button[title='Move selection to Selected Fields'],2)"
            )
            sleep(1)

        self.shared.click_button_with_text("Save")

        # wait extra 3 seconds since the "save" could take a bit time
        sleep(3)
        self.browser.click(f"{iframe_handler} Button:text-is('Build')")
        sleep(2)
        self.browser.click(
            f":nth-match({iframe_handler} Button:text-is('Build Model'),2)"
        )

        # it will take sometime to do the model building, and it seems doesn't show us the "activate" button automatically after it's done, so let's refresh the page after 30 seconds and click the activate button.
        sleep(30)
        self.shared.go_to_setup_admin_page("EinsteinArticleRecommendations/home")
        sleep(2)
        self.browser.click(f"{iframe_handler} Button:text-is('Activate')")
        sleep(2)
        self.browser.click(f":nth-match({iframe_handler} Button:text-is('Activate'),2)")
        sleep(4)
