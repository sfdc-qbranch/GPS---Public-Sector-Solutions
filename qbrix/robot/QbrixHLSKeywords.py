from time import sleep

from Browser import ElementState
from robot.api.deco import library

from qbrix.core.qbrix_robot_base import QbrixRobotTask


@library(scope="GLOBAL", auto_keywords=True, doc_format="reST")
class QbrixHLSKeywords(QbrixRobotTask):

    """Shared Keywords for HLS"""

    def enable_care_plans(self):
        """
        Enables Care Plans for HLS
        """
        self.builtin.log_to_console("\n[HLS] Enabling Care Plans...")
        self.shared.go_to_setup_admin_page("CarePlanSettings/home")
        self.browser.wait_for_elements_state(
            "p:text-is('Care Plans')", ElementState.visible, "30s"
        )
        if "checked" not in self.browser.get_element_states(
            ":nth-match(label:has-text('Disabled'), 1)"
        ):
            self.browser.click(":nth-match(label:has-text('Disabled'), 1)")
            sleep(1)
        self.builtin.log_to_console("\n[HLS] -> Care Plans Enabled!")

    def enable_assessments(self):
        """
        Enables Assessments for HLS
        """
        self.builtin.log_to_console("\n[HLS] Enabling Assessments...")
        self.shared.go_to_setup_admin_page("AssessmentSettings/home")
        self.browser.wait_for_elements_state(
            "h3:text-is('Guest User Assessments')", ElementState.visible, "30s"
        )
        if "checked" not in self.browser.get_element_states(
            ".toggle:has-text('Disabled')"
        ):
            self.browser.click(".toggle:has-text('Disabled')")
            self.shared.wait_and_click("button:has-text('Turn On')", post_click_sleep=5)
        self.builtin.log_to_console("\n[HLS] -> Enabled!")

    def enable_care_plans_grantmaking(self):
        """
        Enables Care Plans Grantmaking for HLS
        """
        self.builtin.log_to_console("\n[HLS] Enabling Care Plan Grantmaking...")
        self.shared.go_to_setup_admin_page("CarePlanSettings/home")
        self.browser.wait_for_elements_state(
            "p:text-is('Care Plans')", ElementState.visible, "30s"
        )
        if "checked" not in self.browser.get_element_states(
            ":nth-match(label:has-text('Disabled'), 1)"
        ):
            self.browser.click(":nth-match(label:has-text('Disabled'), 1)")
            sleep(1)

        if "checked" not in self.browser.get_element_states(
            ":nth-match(label:has-text('Disabled'), 2)"
        ):
            self.browser.click(":nth-match(label:has-text('Disabled'), 2)")
            sleep(2)
            if "visible" in self.browser.get_element_states(
                "button:has-text('Enable')"
            ):
                self.shared.click_button_with_text("Enable")
                sleep(5)
        self.builtin.log_to_console("\n[HLS] -> Enabled!")
