from time import sleep

from Browser import ElementState, SelectAttribute
from robot.api.deco import library

from qbrix.core.qbrix_robot_base import QbrixRobotTask


@library(scope="GLOBAL", auto_keywords=True, doc_format="reST")
class QbrixToolingKeywords(QbrixRobotTask):
    """Shared Q Branch Tooling Keywords"""

    def go_to_connected_app_page(self, connected_app_name: str):
        """
        Go to the Detail Page for a Connected App

        Args:
            connected_app_name (str): The label for the Connected App
        """
        if connected_app_name:
            self.builtin.log_to_console(
                f"\nBrowsing to Connected App Details page for connected app called [{connected_app_name}]"
            )
            self.shared.go_to_setup_admin_page("ConnectedApplication/home")
            iframe_selector = self.shared.iframe_handler()
            self.browser.wait_for_elements_state(
                f"{iframe_selector} h1:text-is('Connected Apps')",
                ElementState.visible,
                "30s",
            )

            attempt_counter = 0
            while attempt_counter < 6:
                if not self.shared.wait_on_element(
                    f"{iframe_selector} a:text-is('{connected_app_name}')", 2
                ):
                    self.builtin.log_to_console(
                        "\nConnected App not found...extending the list of apps..."
                    )
                    if self.browser.get_element_count("img.moreArrow:visible") > 0:
                        self.browser.click("img.moreArrow")
                        sleep(1)
                        self.shared.wait_on_element("img.fewerArrow")
                else:
                    break

                attempt_counter += 1

            self.builtin.log_to_console(
                "\nFound Connected App in List! Opening app details..."
            )
            self.browser.click(f"{iframe_selector} a:text-is('{connected_app_name}')")
            self.browser.wait_for_elements_state(
                f"{iframe_selector} h2.mainTitle:text-is('Connected App Detail')",
                ElementState.visible,
                "30s",
            )
            self.builtin.log_to_console("\nLoaded Details Page")
        else:
            self.builtin.log_to_console("\nERROR: No Connected App!")

    def enable_admin_auth_for_connected_app(
        self, connected_app_name, browse_to_app_page: bool = True, waittime: str = "15s"
    ):
        """
        Updates the User Policy for a connected up to 'Admin approved users are pre-authorized'

        Args:
            connected_app_name (str): The label for the Connected App
            browse_to_app_page (bool): Set to true (The Default) when you want this function to browse to the connected app page. This can be set to False if it is assumed the browser will be on the connected app page, when its run.
            waittime override for orgs that are a little slower
        """
        try:
            if browse_to_app_page:
                self.go_to_connected_app_page(connected_app_name)

            self.builtin.log_to_console(
                "\nUpdating User Policy setting for connected app to allow admin users to be pre-approved..."
            )
            iframe_selector = self.shared.iframe_handler()
            if (
                self.browser.get_element_count(
                    f"{iframe_selector} td.dataCol:text-is('Admin approved users are pre-authorized')"
                )
                == 0
            ):
                self.browser.click(f"{iframe_selector} .btn:has-text('Edit Policies')")
                self.browser.wait_for_elements_state(
                    f"{iframe_selector} h2.mainTitle:text-is('Connected App Edit')",
                    ElementState.visible,
                    waittime,
                )
                self.browser.select_options_by(
                    f"{iframe_selector} #userpolicy",
                    SelectAttribute.text,
                    "Admin approved users are pre-authorized",
                )
                self.builtin.log_to_console("\nPolicy Option Changed...")
                sleep(4)
                if "visible" in self.browser.get_element_states(
                    "iframe >>> .btn:has-text('Ok')"
                ):
                    self.browser.click("iframe >>> .btn:has-text('Ok')")
                    sleep(2)
                self.browser.wait_for_elements_state(
                    f"{iframe_selector} .btn:has-text('Save')",
                    ElementState.visible,
                    waittime,
                )
                self.browser.click(f"{iframe_selector} .btn:has-text('Save')")
                self.browser.wait_for_elements_state(
                    f"{iframe_selector} h2.mainTitle:text-is('Connected App Detail')",
                    ElementState.visible,
                    waittime,
                )
                self.builtin.log_to_console("\nChanges saved and applied!")
        except Exception as e:
            self.browser.take_screenshot()
            raise e

    def enable_system_admin_profile_for_connected_app(
        self,
        connected_app_name: str,
        browse_to_app_page: bool = True,
        waittime: str = "15s",
    ):
        """
        Enables the System Administrator Profile for a connected app

        Args:
            connected_app_name (str): The label for the Connected App
            browse_to_app_page (bool): Set to true (The Default) when you want this function to browse to the connected app page. This can be set to False if it is assumed the browser will be on the connected app page, when its run.
            waittime override for orgs that are a little slower
        """
        try:
            if browse_to_app_page:
                self.go_to_connected_app_page(connected_app_name)

            self.builtin.log_to_console("\nUpdating approved Profiles for the app...")
            iframe_selector = self.shared.iframe_handler()
            self.browser.wait_for_elements_state(
                f"{iframe_selector} .btn:has-text('Manage Profiles')",
                ElementState.visible,
                waittime,
            )
            self.browser.click(f"{iframe_selector} .btn:has-text('Manage Profiles')")
            self.browser.wait_for_elements_state(
                f"{iframe_selector} h1:text-is('Application Profile Assignment')",
                ElementState.visible,
                waittime,
            )
            if not "checked" in self.browser.get_element_states(
                f"{iframe_selector} tr:has-text('System Administrator') >> input"
            ):
                self.browser.click(
                    f"{iframe_selector} tr:has-text('System Administrator') >> input"
                )
                self.browser.click(f"{iframe_selector} .btn:has-text('Save')")
                sleep(2)
            self.builtin.log_to_console(
                "\nAdded System Administrator to approved Profiles!"
            )
        except Exception as e:
            self.browser.take_screenshot()
            raise e

    def enable_vbt_passport(self):
        """Enables VBT (PostSpin) Connected App Settings"""
        connected_app_name = "VBT Connected"
        self.enable_admin_auth_for_connected_app(connected_app_name, True, "40s")
        self.enable_system_admin_profile_for_connected_app(
            connected_app_name, False, "40s"
        )

    def enable_q_passport(self):
        """Enables Q Passport Connected App Settings"""
        self.enable_admin_auth_for_connected_app("Q_Passport")

    def enable_demo_boost(self):
        """Enables Demo Boost Connected App Settings"""
        self.enable_admin_auth_for_connected_app("Demo Boost")

    def enable_demo_wizard(self):
        """Enables Demo Wizard Connected App Settings"""
        self.enable_admin_auth_for_connected_app("Demo Wizard")

    def enable_data_tool(self):
        """Enables Data Tool Connected App Settings"""
        connected_app_name = "NXDO Data Tool"
        self.enable_admin_auth_for_connected_app(connected_app_name)
        self.enable_system_admin_profile_for_connected_app(connected_app_name, False)

    def enable_app_track(self):
        """Enables App Track Connected App Settings"""
        connected_app_name = "Q Demo Tracker Prod"
        self.enable_admin_auth_for_connected_app(connected_app_name)
        self.enable_system_admin_profile_for_connected_app(connected_app_name, False)
