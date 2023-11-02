from time import sleep

from Browser import ElementState
from robot.api.deco import library

from qbrix.core.qbrix_robot_base import QbrixRobotTask


@library(scope='GLOBAL', auto_keywords=True, doc_format='reST')
class QbrixRCGKeywords(QbrixRobotTask):

    """Shared Keywords for RCG"""
    def enable_retail_execution(self):
        """Enables Enable Retail Execution for CG Cloud"""

        self.shared.go_to_setup_admin_page("RetailExecutionSettings/home")
        self.browser.wait_for_elements_state("div:text-is('Retail Execution')", ElementState.visible, '30s')
        checked = "checked" in self.browser.get_element_states(
            ":nth-match(label:has-text('Off'), 1)")
        if not checked:
            toggle_switch = self.browser.get_element(
                ":nth-match(label:has-text('Off'), 1)")
            self.browser.click(toggle_switch)
            sleep(1)
        sleep(3)
        checked2 = "checked" in self.browser.get_element_states(
            ":nth-match(label:has-text('Off'), 2)")
        if not checked2:
            toggle_switch = self.browser.get_element(
                ":nth-match(label:has-text('Off'), 2)")
            self.browser.click(toggle_switch)
            sleep(1)
