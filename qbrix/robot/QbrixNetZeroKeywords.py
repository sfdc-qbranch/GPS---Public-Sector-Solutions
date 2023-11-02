from robot.api.deco import library

from qbrix.core.qbrix_robot_base import QbrixRobotTask


@library(scope='GLOBAL', auto_keywords=True, doc_format='reST')
class QbrixNetZeroKeywords(QbrixRobotTask):

    """Keywords for Net Zero Cloud"""

    def enable_net_zero(self, enable_demo_config=True):
        """
        Enables NetZero Cloud and Optionally additional demo configuration settings
        """
        self.builtin.log_to_console("\nEnabling Net Zero Cloud...")
        self.shared.go_to_setup_admin_page("NetZeroPrefs/home", 5)
        self.builtin.log_to_console("\n -> Loaded Setup Page")
        # Check and Click Main Net Zero Button/Toggle
        selector_main_toggle = "div.slds-grid:has-text('Allow users to turn on Net Zero Cloud in this org.') >> span.slds-checkbox_faux"
        main_toggle_checked = "checked" in self.browser.get_element_states(selector_main_toggle)
        self.builtin.log_to_console("\n -> Checking configuration")
        if not main_toggle_checked:
            self.builtin.log_to_console("\n -> Main toggle off. Clicking now...")
            self.browser.click(selector_main_toggle)
            main_toggle_checked = True
        if main_toggle_checked:
            self.builtin.log_to_console("\n -> NetZero Cloud Enabled")

            if enable_demo_config:
                self.builtin.log_to_console("\n -> Checking recommended demo settings...")

                # Check and Enable Carbon Emissions
                selector_carbon_emissions_toggle = "div.slds-grid:has-text('Calculate carbon emissions related to the energy use data.') >> span.slds-checkbox_faux"
                carbon_emissions_checked = "checked" in self.browser.get_element_states(selector_carbon_emissions_toggle)
                if not carbon_emissions_checked:
                    self.builtin.log_to_console("\n -> Enabling setting to calculate carbon emissions related to energy use data")
                    self.browser.click(selector_carbon_emissions_toggle)
                    carbon_emissions_checked = True
                if carbon_emissions_checked:
                    # Check and Enable Building Data
                    selector_building_data = "div.slds-grid:has-text('Search for and calculate building energy intensities and use them to fill data gaps.') >> span.slds-checkbox_faux"
                    building_data_checked = "checked" in self.browser.get_element_states(selector_building_data)
                    if not building_data_checked:
                        self.builtin.log_to_console("\n -> Enabling setting to search for and calculate calculate building energy intensities")
                        self.browser.click(selector_building_data)

                self.builtin.log_to_console("\n -> Checks complete!")
