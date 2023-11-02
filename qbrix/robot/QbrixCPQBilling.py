from time import sleep

from Browser import ElementState, SelectAttribute
from robot.api.deco import library

from qbrix.core.qbrix_robot_base import QbrixRobotTask


@library(scope="GLOBAL", auto_keywords=True, doc_format="reST")
class QbrixCPQBilling(QbrixRobotTask):
    """Keywords for CPQ and Billing"""

    def go_to_cpq_settings_page(self):
        """Navigate to the CPQ settings page"""
        self.shared.click_link_for_installed_package("Salesforce CPQ", "Configure")
        self.browser.wait_for_elements_state(
            f"{self.shared.iframe_handler()} div.sbTitles >> h1:text-is('Salesforce CPQ')",
            ElementState.visible,
            "300s",
        )
        self.builtin.log_to_console("\n -> Loaded CPQ Settings Page")

    def get_cpq_setting_element(
        self, tab_name, setting_name, setting_element_type="input"
    ):
        """Assumes you are on the CPQ Settings Page. This returns the td element where the setting value element is stored. The setting value is likely to be an input or select."""

        self.builtin.log_to_console(
            f"\n -> Looking for setting called [{setting_name}], type of [{setting_element_type}], on tab [{tab_name}]..."
        )

        # Go To Tab
        self.browser.click(
            f"{self.shared.iframe_handler()} td.rich-tab-header:text-is('{tab_name}')"
        )

        # Return Setting if Found
        setting_selector = f"{self.shared.iframe_handler()} table.detailList:visible >> tr >> :nth-match(td.dataCol:right-of(th.labelCol:has-text('{setting_name}')), 1) >> :nth-match({setting_element_type}, 1)"
        if (
            self.browser.get_element_count(
                f"{self.shared.iframe_handler()} table.detailList:visible >> tr >> th.labelCol:has-text('{setting_name}')"
            )
            > 0
        ):
            self.builtin.log_to_console("\n -> Found setting!")
            return self.browser.get_element(setting_selector)

        self.builtin.log_to_console(
            "\n -> Unable to find setting. Moving onto the next setting (if any)"
        )
        return None

    def enable_cpq_setting(self, tab_name, setting_label):
        """Enables a toggle setting"""
        self.builtin.log_to_console(
            f"\n -> Checking setting [{setting_label}] on tab [{tab_name}] is enabled..."
        )
        temp_setting = self.get_cpq_setting_element(tab_name, setting_label)
        if not self.shared.check_state(temp_setting, "checked"):
            self.browser.click(temp_setting)
            self.builtin.log_to_console(
                f"\n -> [{setting_label}] on tab [{tab_name}] enabled!"
            )

    def disable_cpq_setting(self, tab_name, setting_label):
        """Disables a toggle setting"""
        self.builtin.log_to_console(
            f"\n -> Checking setting [{setting_label}] on tab [{tab_name}] is disabled..."
        )
        temp_setting = self.get_cpq_setting_element(tab_name, setting_label)
        if self.shared.check_state(temp_setting, "checked"):
            self.browser.click(temp_setting)
            self.builtin.log_to_console(
                f"\n -> [{setting_label}] on tab [{tab_name}] disabled!"
            )

    def set_cpq_setting_select(self, tab_name, setting_label, setting_value):
        """Set a select to the provided value"""
        self.builtin.log_to_console(
            f"\n -> Checking setting [{setting_label}] on tab [{tab_name}] is set to value [{setting_value}]..."
        )
        temp_select_setting = self.get_cpq_setting_element(
            tab_name, setting_label, "select"
        )
        if not self.shared.is_option_selected(temp_select_setting, setting_value):
            self.browser.select_options_by(
                temp_select_setting, SelectAttribute.label, setting_value
            )
            self.builtin.log_to_console(
                f"\n -> [{setting_label}] on tab [{tab_name}] is set to value [{setting_value}]!"
            )

    def set_cpq_text_setting(self, tab_name, setting_label, setting_value):
        """Set a text input to a given value"""
        self.builtin.log_to_console(
            f"\n -> Checking setting [{setting_label}] on tab [{tab_name}] is set to value [{setting_value}]..."
        )
        temp_setting = self.get_cpq_setting_element(tab_name, setting_label)
        self.browser.fill_text(temp_setting, setting_value)
        self.builtin.log_to_console(
            f"\n -> [{setting_label}] on tab [{tab_name}] is set to value [{setting_value}]!"
        )

    def save_cpq_settings_changes(self):
        """Clicks the save button on the CPQ settings page"""
        self.browser.click(
            f"{self.shared.iframe_handler()} div.sbButtons >> input.btn:text-is('Save')"
        )
        self.builtin.log_to_console("\nSaved CPQ Settings")

    def go_to_billing_settings_page(self):
        """Navigate to the Billings settings page"""

        self.shared.click_link_for_installed_package("Salesforce Billing", "Configure")
        self.browser.wait_for_elements_state(
            f"{self.shared.iframe_handler()} span.slds-text-heading--label:text-is('Billing Configuration')",
            ElementState.visible,
            "300s",
        )
        self.builtin.log_to_console("\nLoaded Billing Settings Page")

    def set_demo_configuration_for_billing(self):
        """Goes to the Billing Setup Page and ensures the demo configuration, used by the SDO, is applied"""

        self.go_to_billing_settings_page()

        # Disable General > Disable Triggers Setting
        self.shared.wait_and_click(
            f"{self.shared.iframe_handler()} ul.slds-tabs--scoped__nav >> li.slds-tabs--scoped__item >> a:text-is('General')"
        )
        if "checked" in self.browser.get_element_states(
            f"{self.shared.iframe_handler()} table.slds-table:visible >> tbody >> tr.slds-hint-parent:has-text('Disable triggers') >> label.slds-checkbox--toggle >> input[type='checkbox']"
        ):
            self.browser.click(
                f"{self.shared.iframe_handler()} table.slds-table:visible >> tbody >> tr.slds-hint-parent:has-text('Disable triggers') >> label.slds-checkbox--toggle"
            )
            self.builtin.log_to_console("\n -> Disabled the Disable Triggers Setting")

        # Enable Payment > Save Credit Card Details
        self.shared.wait_and_click(
            f"{self.shared.iframe_handler()} ul.slds-tabs--scoped__nav >> li.slds-tabs--scoped__item >> a:text-is('Payment')"
        )
        sleep(1)
        if "checked" not in self.browser.get_element_states(
            f"{self.shared.iframe_handler()} table.slds-table:visible >> tbody >> tr.slds-hint-parent:has-text('Save credit card details') >> label.slds-checkbox--toggle >> input[type='checkbox']"
        ):
            self.browser.click(
                f"{self.shared.iframe_handler()} table.slds-table:visible >> tbody >> tr.slds-hint-parent:has-text('Save credit card details') >> label.slds-checkbox--toggle"
            )
            self.builtin.log_to_console(
                "\n -> Enabled the Save Credit Card details setting"
            )

        # Save Changes
        self.browser.click(
            f"{self.shared.iframe_handler()} div[id='payNow'] >> button:text-is('Save')"
        )
        self.shared.wait_and_click(
            f"{self.shared.iframe_handler()} button:text-is('Yes')"
        )
        self.builtin.log_to_console("\n -> Saved Changes")
