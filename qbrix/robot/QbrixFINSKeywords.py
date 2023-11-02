from time import sleep

from Browser import ElementState
from robot.api.deco import library

from qbrix.core.qbrix_robot_base import QbrixRobotTask


@library(scope="GLOBAL", auto_keywords=True, doc_format="reST")
class QbrixFINSKeywords(QbrixRobotTask):

    """Shared Keywords for FINs"""

    def enable_interest_tagging(self):
        """
        Enables Interest Tagging for FINS Cloud
        """
        self.builtin.log_to_console("\n[FINS] Enabling Interest Tagging...")

        # Load Interest Tagging Setup Page
        self.shared.go_to_setup_admin_page("InterestTaggingSettings/home")
        self.builtin.log_to_console("\n[FINS] -> Loaded Setup Page...")

        self.browser.wait_for_elements_state(
            "p:text-is('Let users access interest tags feature')",
            ElementState.visible,
            "30s",
        )

        if not "checked" in self.browser.get_element_states(
            ":nth-match(label:has-text('Off'), 1)"
        ):
            self.browser.click(":nth-match(label:has-text('off'), 1)")
            sleep(1)
        self.builtin.log_to_console("\n[FINS] -> Interest Tagging Enabled!")

    def enable_record_alert_access(self):
        """
        Enables Record Alert Access for Financial Services
        """
        self.builtin.log_to_console("\n[FINS] Enabling Record Alert Access...")
        self.shared.go_to_setup_admin_page("RecordAlertOrgSettings/home")
        self.browser.wait_for_elements_state(
            "p:text-is('Record Alert Preferences')", ElementState.visible, "30s"
        )
        checked = "checked" in self.browser.get_element_states(
            ":nth-match(label:has-text('Off'), 1)"
        )
        if not checked:
            toggle_switch = self.browser.get_element(
                ":nth-match(label:has-text('off'), 1)"
            )
            self.browser.click(toggle_switch)
            sleep(1)
        checked2 = "checked" in self.browser.get_element_states(
            ":nth-match(label:has-text('Off'), 2)"
        )
        if not checked2:
            toggle_switch2 = self.browser.get_element(
                ":nth-match(label:has-text('off'), 2)"
            )
            self.browser.click(toggle_switch2)
            sleep(1)
        self.builtin.log_to_console("\n[FINS] -> Record Alert Access Enabled...")

    def enable_business_rules_engine(self):
        """
        Enables Business Rules Engine for Financial Services
        """
        self.builtin.log_to_console(
            "\n[FINS] Enabling Business Rules Engine for Financial Services..."
        )
        self.shared.go_to_setup_admin_page("BREDecisionTableAccess/home")
        self.browser.wait_for_elements_state(
            "span:text-is('Business Rules Engine Settings')",
            ElementState.visible,
            "30s",
        )
        checked = "checked" in self.browser.get_element_states(
            ".toggle:has-text('Disabled')"
        )
        if not checked:
            self.browser.click(".toggle:has-text('Disabled')")
            sleep(5)
            self.browser.wait_for_elements_state(
                "button:has-text('Enable')", ElementState.visible, "30s"
            )
            self.browser.click("button:has-text('Enable')")
            sleep(5)
        self.builtin.log_to_console("\n[FINS] -> Enabled!")

    def enable_financial_account_setting(self):
        """
        Enables Financial Services Account Setting
        """
        self.builtin.log_to_console(
            "\n[FINS] Enabling Financial Services Account setting..."
        )
        self.shared.go_to_setup_admin_page("FscServiceExcellenceSettings/home")
        self.browser.wait_for_elements_state(
            "p:text-is('Datasource Preferences')", ElementState.visible, "30s"
        )
        checked = "checked" in self.browser.get_element_states(
            ":nth-match(label:has-text('Off'), 1)"
        )
        if not checked:
            toggle_switch = self.browser.get_element(
                ":nth-match(label:has-text('Off'), 1)"
            )
            self.browser.click(toggle_switch)
            sleep(1)
        self.builtin.log_to_console("\n[FINS] -> Enabled!")

    def enable_actionable_segmentation_settings(self):
        """
        Enables Segmentation Settings for Financial Services
        """
        self.builtin.log_to_console(
            "\n[FINS] Enabling Segmentation Settings for Financial Services..."
        )
        self.shared.go_to_setup_admin_page("ActionableSegmentationSettings/home")
        self.browser.wait_for_elements_state(
            "span:text-is('Actionable Segmentation Settings')",
            ElementState.visible,
            "20s",
        )

        toogle_button = "label:has-text('Disabled')"
        if self.shared.wait_on_element(toogle_button):
            checked = "checked" in self.browser.get_element_states(
                "label:has-text('Disabled')"
            )
            if not checked:
                self.browser.click("label:has-text('Disabled')")
                sleep(5)
                self.browser.click("button:has-text('Enable')")
                sleep(5)
        self.builtin.log_to_console("\n[FINS] -> Enabled!")
