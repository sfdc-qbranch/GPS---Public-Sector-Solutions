import re
import time
from datetime import datetime
from time import sleep
from typing import Optional

from Browser import ElementState, SelectAttribute
from Browser.utils.data_types import MouseButtonAction
from cumulusci.robotframework.CumulusCI import CumulusCI
from cumulusci.robotframework.SalesforceAPI import SalesforceAPI
from robot.api.deco import library
from robot.libraries.BuiltIn import BuiltIn

from qbrix.tools.shared.qbrix_authentication import get_secure_setting


@library(scope="GLOBAL", auto_keywords=True, doc_format="reST")
class QbrixSharedKeywords:

    """Shared Keywords for Robot"""

    def __init__(self):
        super().__init__()
        self._browser = None
        self._salesforceapi = None
        self._builtin = None
        self._cumulusci = None

    @property
    def builtin(self):
        """Loads Builtin Methods"""

        if getattr(self, "_builtin", None) is None:
            self._builtin = BuiltIn()
        return self._builtin

    @property
    def browser(self):
        if self._browser is None:
            self._browser = self.builtin.get_library_instance("Browser")
        return self._browser

    @property
    def salesforceapi(self):
        if self._salesforceapi is None:
            self._salesforceapi = SalesforceAPI()
        return self._salesforceapi

    @property
    def cumulusci(self):
        """Loads Keyword Library for working with CumulusCI from Robot"""

        if getattr(self, "_cumulusci", None) is None:
            self._cumulusci = CumulusCI()
        return self._cumulusci

    # ---------------------------------
    # BROWSING AND NAVIGATION FUNCTIONS
    # ---------------------------------

    def get_signup_email(self):
        """Returns the email address for the user who created the org"""

        return self.cumulusci.get_org_info().get("userinfo").get("email")

    def go_to_lightning_setup_home(self, wait_for_text: str = "Home"):
        """
        Browses to the Lightning Setup Home Page.

        Args:
            wait_for_text (str): Defaults to 'Home" but can be set to other text which resides within an H1 element.
        """

        SETUP_ADMIN_LOCATION = "/lightning/setup/SetupOneHome/home"

        if not str(self.browser.get_url()).endswith(SETUP_ADMIN_LOCATION):
            self.browser.go_to(
                f"{self.cumulusci.org.instance_url}{SETUP_ADMIN_LOCATION}",
                timeout="90s",
            )
            self.wait_for_page_to_load()

        start_time = time.time()
        timeout = 30
        while True:
            if self.browser.get_element_count(f"h1:has-text('{wait_for_text}')") > 0:
                break

            try:
                self.browser.go_to(
                    f"{self.cumulusci.org.instance_url}{SETUP_ADMIN_LOCATION}",
                    timeout="90s",
                )
                self.wait_for_page_to_load()
                self.browser.wait_for_elements_state(
                    f"h1:has-text('{wait_for_text}')", ElementState.visible, "10s"
                )
                break
            except Exception as e:
                print(e)

            elapsed_time = time.time() - start_time
            if elapsed_time >= timeout:
                self.builtin.log_to_console("\nTIMEOUT EXCEEDED")
                print(
                    f"Q Robot was unable to get to the Setup Admin Home page, using URL {self.cumulusci.org.instance_url}{SETUP_ADMIN_LOCATION}"
                )
                self.browser.take_screenshot()
                break

            time.sleep(3)

    def go_to_app(self, app_name: str):
        """
        Browses to the given app within the browser. For example "Sales" app.

        Args:
            app_name (str): Name of the Lightning App. Not the API Name.
        """

        if not app_name:
            self.builtin.log_to_console("\nNo App Name Provided")
            return

        # Browse to the App if found
        application_id = self.find_id(
            object_api_name="AppDefinition",
            where_clause=f"Label = '{app_name}'",
            id_column_name="DurableId",
        )
        if application_id:
            self.browser.go_to(
                f"{self.cumulusci.org.instance_url}/lightning/app/{application_id}",
                timeout="30s",
            )
            self.wait_for_page_to_load()

    def go_to_setup_admin_page(
        self, setup_page_url: str, sleep_length: Optional[int] = 2, force_reload=False
    ):
        """
        Browses to a lightning setup URL, provide everything after lightning/setup/ in the URL

        Args:
            setup_page_url (str): Requires the section of the URL Path which comes after lightning/setup.
            sleep_length (int): (Optional) Set the length of time (in seconds) which the robot will wait for the page to load. Defaults to 2 seconds.
            force_reload (bool): (Optional) Set to true to ensure that page is reloaded
        """

        # Handle empty URL
        if not setup_page_url:
            raise Exception("URL Text must be specified")

        # Handle full url being passed in
        if "lightning/setup" in setup_page_url:
            startpos = setup_page_url.find("lightning/setup/") + len("lightning/setup/")
            endpos = len(setup_page_url)
            setup_page_url = setup_page_url[startpos:endpos]

        # Go To Page
        try:
            if force_reload or not str(self.browser.get_url()).endswith(
                f"/lightning/setup/{setup_page_url}"
            ):
                self.browser.go_to(
                    f"{self.cumulusci.org.instance_url}/lightning/setup/{setup_page_url}",
                    timeout="90s",
                )
                self.wait_for_page_to_load()

            # Handle Disabled Feature
            if (
                self.browser.get_element_count("h2:has-text('Page not found'):visible")
                > 0
            ):
                raise Exception(
                    "Page not found. This could mean you are missing a feature licence."
                )

            # Handlers for help messages and new feature modals
            if (
                self.browser.get_element_count(
                    "button:has-text('Dismiss'):visible:enabled"
                )
                > 0
            ):
                for elem in self.browser.get_elements(
                    "button:has-text('Dismiss'):visible:enabled"
                ):
                    try:
                        self.browser.click(elem)
                    except:
                        pass

            if self.browser.get_element_count("div.modal-container:visible") > 0:
                for elem in self.browser.get_elements(
                    "div.modal-container:visible >> button:has-text('Close this window')"
                ):
                    try:
                        self.browser.click(elem)
                    except:
                        pass

            # Allow time for page load to complete
            sleep(sleep_length)

        except Exception as e:
            self.browser.take_screenshot()
            raise e

    def wait_for_page_to_load(self, timeout: str = "5"):
        """Waits for the network activity on the page to become idle or a timeout of 5s is reached"""

        try:
            self.browser.wait_until_network_is_idle(timeout=f"{timeout}s")
        except Exception as e:
            print(e)
            pass

    def iframe_handler(self):
        """
        Add to the start of selector statements to handle iframes within Lightning Pages. Note that it will return >>> at the end of the statement so account for that in your selector.
        """

        self.wait_for_page_to_load()

        # This is a double check to ensure that once the page has finished loading elements, no iframes have appeared.
        if self.browser.get_element_count("iframe") == 0:
            retries = 1
            while retries < 3:
                if self.browser.get_element_count("iframe") == 0 and retries == 2:
                    return ""
                if self.browser.get_element_count("iframe") > 0:
                    break

                retries += 1
                sleep(1)

        # Handles Console Layouts and Setup Pages where guidance prompts have opened
        if self.browser.get_element_count("div.mainContentMark") == 1:
            return "div.mainContentMark >> iframe >>>"

        # Handles LEX Setup Pages with embedded Classic UI Settings Pages or older LEX Setup Pages
        if self.browser.get_element_count("div.oneAlohaPage") == 1:
            return "div.oneAlohaPage >> iframe >>>"

        # Handles other situations
        if self.browser.get_element_count("iframe") == 1 and (
            self.browser.get_element_count("div.oneAlohaPage") < 1
            or self.browser.get_element_count("div.mainContentMark") < 1
        ):
            return "iframe >>>"

        if self.browser.get_element_count("iframe") > 1 and (
            self.browser.get_element_count("div.oneAlohaPage") < 1
            or self.browser.get_element_count("div.mainContentMark") < 1
        ):
            return "nth-match(iframe, 1) >>>"

        return ""

    # ------------------
    # SECURITY FUNCTIONS
    # ------------------

    def disable_mfa(self):
        """
        Disables MFA/2FA in the target org
        """

        self.go_to_setup_admin_page("SecuritySession/home")
        if "checked" in self.browser.get_element_states(
            f"{self.iframe_handler()} td:has(label:text-is('Require identity verification during multi-factor authentication (MFA) registration')) >> input"
        ):
            self.browser.click(
                f"{self.iframe_handler()} td:has(label:text-is('Require identity verification during multi-factor authentication (MFA) registration')) >> input"
            )
        existing_list = self.browser.get_select_options(
            f"{self.iframe_handler()} #duel_select_1"
        )
        if len(existing_list) > 0 and any(
            d["label"] == "Multi-Factor Authentication" for d in existing_list
        ):
            self.browser.select_options_by(
                f"{self.iframe_handler()} #duel_select_1",
                SelectAttribute.text,
                "Multi-Factor Authentication",
            )
            self.browser.click(
                f"{self.iframe_handler()} div.duelingListBox >> img.leftArrowIcon"
            )
        self.browser.click(f"{self.iframe_handler()} input.btn:has-text('Save')")
        self.wait_for_page_to_load()

    def disable_browser_caching(self):
        """
        Uncheck "Enable secure and persistent browser caching to improve performance" in the target org
        Somehow, this is the only checkbox in the caching section that is not in Security setting metadata file
        """

        self.go_to_setup_admin_page("SecuritySession/home")
        my_iframe_handler = self.iframe_handler()
        if "checked" in self.browser.get_element_states(
            f"{my_iframe_handler} td:has(label:text-is('Enable secure and persistent browser caching to improve performance')) >> input"
        ):
            self.browser.click(
                f"{my_iframe_handler} td:has(label:text-is('Enable secure and persistent browser caching to improve performance')) >> input"
            )
            self.wait_and_click(f"{self.iframe_handler()} input.btn:has-text('Save')")

    def get_secure_setting(self, secure_setting_name):
        """Returns the value for a secure setting held in Q Labs, returns None if not found"""

        return get_secure_setting(secure_setting_name)

    def login_as_user(
        self, first_name=None, last_name=None, external_id=None, user_id=None
    ):
        """Logs In as a given User. Provide the firstname and lastname or the External ID"""

        if not user_id:
            soql_query = "SELECT Id FROM USER WHERE "

            if external_id:
                soql_query += f" External_Id__c = '{external_id}' LIMIT 1"
            else:
                soql_query += (
                    f" Firstname = '{first_name}' and Lastname = '{last_name}' LIMIT 1"
                )

            user_lookup = self.salesforceapi.soql_query(soql_query)

            if user_lookup.get("totalSize") > 0:
                if user_lookup.get("records")[0].get("Id"):
                    user_id = user_lookup.get("records")[0].get("Id")

        if user_id:
            self.browser.go_to(
                f"{self.cumulusci.org.instance_url}/lightning/setup/ManageUsers/page?address=%2F{user_id}%3Fnoredirect%3D1%26isUserEntityOverride%3D1",
                timeout="90s",
            )
            self.wait_for_page_to_load()
            self.wait_and_click(
                f"{self.iframe_handler()} td.pbButton >> input.btn:text-is('Login')"
            )
            sleep(2)
            self.wait_for_page_to_load()

            if self.wait_on_element("h2:has-text('Canvas - Q_Passport')", 2):
                self.browser.click("button[title='Close this window']")

        else:
            self.builtin.log_to_console("\nNo User Found for that selection")

    def undo_login_as_user(self):
        """Reverts the login as user"""

        if self.browser.get_element_count("a.action-link:has-text('Log out as')") > 0:
            self.browser.click("a.action-link:has-text('Log out as')")
            sleep(2)
            self.wait_for_page_to_load()

    # ------------------
    # LEX FUNCTIONS
    # ------------------

    def set_org_wide_email(
        self, org_wide_email_address: Optional[str] = "sdo@salesforce.com"
    ):
        """
        Sets and org wide email address for the target org, defaulting to the sdo address

        Args:
            org_wide_email_address (str): (Optional) Email Address to use as new org wide email, although this parameter will default to sdo@salesforce.com
        """
        try:
            self.go_to_setup_admin_page("OrgWideEmailAddresses/home", 3)
            iframe_handler = self.iframe_handler()
            self.browser.wait_for_elements_state(
                f"{iframe_handler} h2:text-is('Organization-Wide Email Addresses for User Selection and Default No-Reply Use')",
                ElementState.visible,
                "15s",
            )
            if (
                self.browser.get_element_count(
                    f"{iframe_handler} td:has-text('{org_wide_email_address}')"
                )
                == 0
            ):
                self.browser.click(
                    f"{iframe_handler} div.pbHeader >> input.btn:text-is('Add')"
                )
                self.browser.wait_for_elements_state(
                    f"{iframe_handler} tr:has-text('Display Name')",
                    ElementState.visible,
                    "5s",
                )
                self.browser.fill_text(
                    f"{iframe_handler} tr:has-text('Display Name') >> input",
                    "Default Email",
                )
                self.browser.fill_text(
                    f"{iframe_handler} tr:has-text('Email Address') >> input",
                    org_wide_email_address,
                )
                self.browser.select_options_by(
                    f"{iframe_handler} tr:has-text('Purpose') >> select",
                    SelectAttribute.text,
                    "User Selection and Default No-Reply Address",
                )
                self.browser.click(
                    f"{iframe_handler} :nth-match(.btn:text-is('Save'), 1)"
                )
                sleep(1)
        except Exception as e:
            self.browser.take_screenshot()
            raise e

    def set_lightning_toggle(self, new_state: str):
        """
        Toggles a Salesforce Lightning Toggle either on or off

        Args:
            new_state (str): Define a new state for the lightning toggle. Options are "on" or "off" as a string.
        """
        if new_state is None or new_state.lower() not in ("on", "off"):
            raise Exception(
                "State for the lightning toggle must be specified. State should be 'on' or 'off'."
            )

        visible = "visible" in self.browser.get_element_states("label:has-text('Off')")
        if visible and new_state.lower() == "on":
            toggle_switch = self.browser.get_element("label:has-text('Off')")
            self.browser.click(toggle_switch)
            sleep(1)
        if not visible and new_state.lower() == "off":
            visible = "visible" in self.browser.get_element_states(
                "label:has-text('On')"
            )
            if visible:
                toggle_switch = self.browser.get_element("label:has-text('On')")
                self.browser.click(toggle_switch)
                sleep(2)

    def click_button_with_text(
        self,
        button_text,
        uses_iframe: Optional[bool] = False,
        sleep_length: Optional[int] = 1,
    ):
        """
        Finds a button using the button text and clicks it providing it is visible on the page. You must define the text for the label on the button.

        Args:
            button_text (str): Exact text for the button you want to click
            uses_iframe (str): Set to True to add iframe support to the button selector
            sleep_length (str): (Optional) Set the length of time (in seconds) which the robot will wait for the page to load after button is clicked. Defaults to 1 second.
        """

        if not button_text:
            raise ValueError("Button Text must be specified")

        button_selector = f"button:has-text('{button_text}')"
        if uses_iframe:
            button_selector = (
                f":nth-match(iframe,1) >>> button:has-text('{button_text}')"
            )

        self.wait_and_click(button_selector)

    def click_button_in_frame_with_text(self, button_text: str):
        """
        NO LONGER USED, use click_button_with_text and set the uses_iframe parameter to True.

        Finds a button using the button text and clicks it providing it is visible on the page within an iframe.
        You must define the text for the label on the button.

        """

        if not button_text:
            raise Exception("Button Text must be specified")

        iframe_handler = self.iframe_handler()
        visible = "visible" in self.browser.get_element_states(
            f"{iframe_handler} button:has-text('{button_text}')"
        )
        if visible:
            button_to_click = self.browser.get_element(
                f"{iframe_handler} button:has-text('{button_text}')"
            )
            self.browser.click(button_to_click)
            sleep(1)

    def click_input_button_in_iframe_with_text(self, button_text: str):
        """
        Finds a button using the button text and clicks it providing it is visible on the page within an iframe.
        You must define the text for the label on the button.

        Args:
            button_text: The text of the button you want to click
        """
        if not button_text:
            raise Exception("Button Text must be specified")

        if "visible" in self.browser.get_element_states(
            f":nth-match(iframe,1) >>> input:has-text('{button_text}')"
        ):
            button_to_click = self.browser.get_element(
                f":nth-match(iframe,1) >>> input:has-text('{button_text}')"
            )
            self.browser.click(button_to_click)
            sleep(1)

    def wait_for_page_title(
        self,
        page_title: str,
        title_element_type: Optional[str] = "h1",
        wait_time: Optional[str] = "10s",
        uses_iframe: Optional[bool] = True,
    ):
        """
        Waits for a title on a lightning page to be loaded based on title text and optional element type.

        Args:
            page_title (str): Text of the title or text you want to wait on to know if the page has loaded.
            title_element_type (str): (Optional) Type of element where the text is contained. Expects an HTML element and defaults to 'h1'
            wait_time (str): (Optional) Length of time which you want to wait on the title to load, defaults to '10s'.
            uses_iframe (bool): (Optional) Set to True if the element is within an iframe. Defaults to True
        """

        if not page_title:
            raise Exception("No page title specified")

        iframe_selector = ":nth-match(iframe,1) >>> " if uses_iframe else ""
        self.browser.wait_for_elements_state(
            f"{iframe_selector}{title_element_type}:text-is('{page_title}')",
            ElementState.visible,
            wait_time,
        )

    def wait_and_click(
        self, selector: str = None, timeout: str = "30", post_click_sleep: int = 1
    ):
        """Waits for an element to become visible and enabled. Then clicks the element.

        Args:
            selector (str): Playwright selector for the element
            timeout (str): (Optional) Duration in seconds as a string. Defaults to 30 seconds
            post_click_sleep (int): (Optional) The amount of time in seconds to wait after the element is clicked. The default is 1 second.
        """

        if not selector:
            return

        self.wait_for_page_to_load()
        self.browser.wait_for_elements_state(
            selector, ElementState.visible, f"{timeout}s"
        )
        self.browser.wait_for_elements_state(
            selector, ElementState.enabled, f"{timeout}s"
        )
        self.browser.click(selector)
        sleep(post_click_sleep)

    def wait_and_fill_text(
        self,
        selector: str = None,
        text: str = "",
        timeout: str = "30",
        post_click_sleep: int = 1,
    ):
        """Waits for an element to become visible and enabled. Then fill text into the element, this is used for text box and textarea.

        Args:
            selector (str): Playwright selector for the element
            timeout (str): (Optional) Duration in seconds as a string. Defaults to 30 seconds
            post_click_sleep (int): (Optional) The amount of time in seconds to wait after the element is clicked. The default is 1 second.
        """

        if not selector:
            return

        self.wait_for_page_to_load()
        self.browser.wait_for_elements_state(
            selector, ElementState.visible, f"{timeout}s"
        )
        self.browser.wait_for_elements_state(
            selector, ElementState.enabled, f"{timeout}s"
        )
        self.browser.fill_text(selector, text)
        sleep(post_click_sleep)

    def check_state(self, selector: str = None, state: str = "visible"):
        """Checks if an element state is equal to a given state within a certain timeout

        Args:
            selector (str): Playwright selector for the element
            state (str): (Optional) Element state you are checking for. Defaults to 'visible'
        Returns:
            bool: True if given state is in element states, False if not or on error.
        """

        self.wait_for_page_to_load()
        try:
            return state in self.browser.get_element_states(selector)
        except Exception as e:
            print(e)
            return False

    def wait_on_element(self, selector: str = None, timeout: int = 15):
        """Waits on a given element to be in the page
        Args:
            selector (str): Playwright selector for the element
            timeout (int): (Optional) Total seconds until wait times out. Defaults to 15 seconds.
        Returns:
            bool: True when element is found on page, False when timeout is reached and element is not found.
        """

        self.wait_for_page_to_load()
        count = 0
        self.builtin.log_to_console(f"\nWaiting on element selector {selector}...")
        while count <= timeout:
            if self.browser.get_element_count(selector) >= 1:
                self.builtin.log_to_console("\nElement Found!")
                return True
            if "visible" in self.browser.get_element_states(selector):
                self.builtin.log_to_console("\nElement found via state 'visible'!")
                return True
            sleep(1)
            count += 1
        self.builtin.log_to_console("\nElement Was Not Found")
        return False

    # ------------------
    # SHARED FUNCTIONS
    # ------------------

    def compile_all_apex(self, wait_time=600):
        """
        Does an Apex Recompile of all Classes

        Args:
            wait_time: Max wait time for the compile to run in seconds. Default is 600 seconds.
        """

        self.go_to_setup_admin_page("ApexClasses/home", 15)
        self.browser.click(
            f"iframe >>> id=all_classes_page:theTemplate:messagesForm:compileAll"
        )

        itcnt = 0
        while itcnt < wait_time:
            try:
                completed_element_states = self.browser.get_element_states(
                    "iframe >>> h4:has-text('Compilation Complete')"
                )

                if (
                    "visible" in completed_element_states
                    and "enabled" in completed_element_states
                ):
                    sleep(2)
                    break

            except Exception as e:
                self.browser.take_screenshot()
                self.log_to_file(e)
                break

            itcnt += 1
            sleep(5)

    def enable_omnichannel_for_bot(self, button_name: str, queue_name: str):
        """
        Sets a given Live Chat Button to Omni-Channel Routing with an associated Queue

        :param button_name: Name of the Live Chat Button
        :param queue_name: Name of the Queue you want to assign to the Live Chat Button. Note this must be an exact match as it is case sensitive.
        """

        if button_name == "" or queue_name == "":
            raise Exception("Button Name and Queue Name must be specified")

        self.go_to_setup_admin_page("LiveChatButtonSettings/home")
        self.browser.click(f"iframe >>> a:text-is('{button_name}')")
        sleep(2)
        self.browser.click("iframe >>> .btn:has-text('Edit')")
        sleep(2)
        self.browser.select_options_by(
            "iframe >>> tr:has-text('Routing Type') >> select",
            SelectAttribute.text,
            "Omni-Channel",
        )
        sleep(2)
        self.browser.fill_text(
            "iframe >>> tr:has-text('Queue') >> span.lookupInput >> input",
            f"{queue_name}",
        )
        sleep(2)
        self.browser.click("iframe >>> :nth-match(.btn:has-text('Save'), 1)")
        sleep(2)

    def create_chat_button_and_automated_invitations(self):
        """
        Creates the Chat Button and Invitations with Defaults of *Standard Chat Button and SDO_Service_Chat
        """
        self.create_a_chat_button_and_automated_invitations(
            "*Standard Chat Button", "SDO_Service_Chat"
        )

    def create_a_chat_button_and_automated_invitations(
        self, buttonName: str, buttonAPIName: str
    ):
        """
        Creates the Chat Button and Invitations
        :param buttonName: Name of the Chat Button
        :param buttonAPIName: API Name for the Chat Button
        """
        sleep(3)
        if buttonName is None:
            raise Exception("buttonName must be specified")
        if buttonAPIName is None:
            raise Exception("buttonAPIName must be specified")
        self.go_to_setup_admin_page("LiveChatButtonSettings/home")
        self.browser.wait_for_elements_state(
            "iframe >>> h1:has-text('Chat Buttons')", ElementState.visible, "60s"
        )
        sleep(10)

        visible = "visible" in self.browser.get_element_states(
            f"iframe >>> .custom-alert-checkbox-label:has-text('legacy chat')"
        )
        if visible:
            checked = "checked" in self.browser.get_element_states(
                f"iframe >>> .custom-alert-checkbox-label:has-text('legacy chat')"
            )
            if not checked:
                self.browser.click(
                    f"iframe >>> .custom-alert-checkbox-label:has-text('legacy chat')"
                )
                sleep(2)
                self.browser.click(
                    f"iframe >>> .custom-alert-button:has-text('Legacy chat')"
                )
                sleep(2)

        sleep(5)
        visible = "visible" in self.browser.get_element_states(
            f"iframe >>> .listRelatedObject:has-text('{buttonName}')"
        )
        if not visible:
            sleep(5)
            self.click_input_button_in_iframe_with_text("New")
            self.browser.wait_for_elements_state(
                "iframe >>> h3:has-text('Basic Information')",
                ElementState.visible,
                "45",
            )
            sleep(5)
            self.browser.select_options_by(
                "iframe >>> select[name='j_id0:theForm:thePageBlock:editDataSection:editTypeItem:editType']",
                SelectAttribute.text,
                "Chat Button",
            )
            sleep(1)
            self.browser.fill_text(
                "iframe >>> input[name='j_id0:theForm:thePageBlock:editDataSection:nameSection:editMasterLabel']",
                buttonName,
            )
            self.browser.fill_text(
                "iframe >>> input[name='j_id0:theForm:thePageBlock:editDataSection:developerNameSection:editDeveloperName']",
                "",
            )
            sleep(1)
            self.browser.fill_text(
                "iframe >>> input[name='j_id0:theForm:thePageBlock:editDataSection:developerNameSection:editDeveloperName']",
                buttonAPIName,
            )
            sleep(2)
            if not "checked" in self.browser.get_element_states(
                "iframe >>> id=j_id0:theForm:thePageBlock:editDataSection:hasChasitorIdleTimeout:hasChasitorIdleTimeout"
            ):
                self.browser.click(
                    "iframe >>> id=j_id0:theForm:thePageBlock:editDataSection:hasChasitorIdleTimeout:hasChasitorIdleTimeout"
                )
                sleep(1)
                # Customer Timeout
                self.browser.fill_text(
                    "iframe >>> id=j_id0:theForm:thePageBlock:editDataSection:j_id76:editChasitorIdleTimeout",
                    "300",
                )
                sleep(1)
                # Customer Timeout Warning
                self.browser.fill_text(
                    "iframe >>> id=j_id0:theForm:thePageBlock:editDataSection:j_id79:editChasitorIdleTimeoutWarning",
                    "250",
                )
                sleep(1)
            self.browser.select_options_by(
                "iframe >>> id=j_id0:theForm:thePageBlock:editRoutingSection:rountingTypeSection:editRoutingType",
                SelectAttribute.text,
                "Omni-Channel",
            )
            sleep(2)
            self.browser.click(
                "iframe >>> id=j_id0:theForm:thePageBlock:editRoutingSection:queueSection:editQueue_lkwgt"
            )
            sleep(5)
            mainpage = self.browser.switch_page("NEW")
            sleep(2)
            self.browser.fill_text(
                ':nth-match(frame,1) >>> xpath=//*[@id="lksrch"]', "Chat"
            )
            sleep(1)
            button_to_click = self.browser.get_element(
                f":nth-match(frame,1) >>> input:has-text('Go!')"
            )
            self.browser.click(button_to_click)
            sleep(6)
            search_header = self.browser.get_element(
                ':nth-match(frame,2) >>> xpath=//*[@id="new"]/div/div[3]/div/div[2]/table/tbody/tr[2]/th'
            )
            self.browser.click(search_header)
            sleep(5)
            self.browser.switch_page(mainpage)
            if "checked" not in self.browser.get_element_states(
                "iframe >>> id=j_id0:theForm:thePageBlock:editRoutingSection:j_id192:editHasQueue"
            ):
                self.browser.click(
                    "iframe >>> id=j_id0:theForm:thePageBlock:editRoutingSection:j_id192:editHasQueue"
                )
                sleep(1)
                self.browser.fill_text(
                    "iframe >>> id=j_id0:theForm:thePageBlock:editRoutingSection:j_id195:editPerAgentQueueLength",
                    "5",
                )
                sleep(1)
            self.browser.click("iframe >>> :nth-match(.btn[value='Save'], 1)")
            sleep(8)

    def add_service_presence_statuses_to_profile(
        self, profilename: str, servicestatus: str
    ):
        """Adds a specified service presence to the specified profile
        :param profilename: Name of Salesforce Profile
        :param servicestatus: Service Status to be defined for the Profile
        """
        if profilename is None:
            raise Exception("Profile Name must be specified")
        if servicestatus is None:
            raise Exception("Service Status must be specified")

        self.go_to_setup_admin_page("EnhancedProfiles/home", 12)

        profileid = self.find_profileid_by_name(profilename)
        if profileid is None:
            raise Exception(f"The Profile Name: {profilename} cannot be located.")

        if profileid is None:
            raise Exception("Unable to locate the Profile ID by name")

        profileediturl = f"EnhancedProfiles/page?address=%2F{profileid}%3Fs%3DServicePresenceStatusAccess"

        self.go_to_setup_admin_page(profileediturl)
        sleep(5)
        self.browser.click("iframe >>> a:has-text('Edit')")
        sleep(10)
        if not "checked" in self.browser.get_element_states(
            f"iframe >>>  :nth-match(tr:has-text('{servicestatus}') > td > input, 1)"
        ):
            self.browser.click(
                f"iframe >>>  :nth-match(tr:has-text('{servicestatus}') > td > input, 1)"
            )
            sleep(1)
        self.browser.click("iframe >>> .btn:text-is('Save')")

    def remove_service_presence_statuses_to_profile(
        self, profilename: str, servicestatus: str
    ):
        """emoves a specified service presence to the specified profile
        :param profilename: Name of Salesforce Profile
        :param servicestatus: Service Status to be defined for the Profile
        """
        if profilename is None:
            raise Exception("Profile Name must be specified")
        if servicestatus is None:
            raise Exception("Service Status must be specified")

        self.go_to_setup_admin_page("EnhancedProfiles/home", 12)

        profileid = self.find_profileid_by_name(profilename)
        if profileid is None:
            raise Exception(f"The Profile Name: {profilename} cannot be located.")

        if profileid is None:
            raise Exception("Unable to locate the Profile ID by name")

        profileediturl = f"EnhancedProfiles/page?address=%2F{profileid}%3Fs%3DServicePresenceStatusAccess"

        self.go_to_setup_admin_page(profileediturl)
        sleep(5)
        self.browser.click("iframe >>> a:has-text('Edit')")
        sleep(10)
        if "checked" in self.browser.get_element_states(
            f"iframe >>>  :nth-match(tr:has-text('{servicestatus}') > td > input, 1)"
        ):
            self.browser.click(
                f"iframe >>>  :nth-match(tr:has-text('{servicestatus}') > td > input, 1)"
            )
            sleep(1)
        self.browser.click("iframe >>> .btn:text-is('Save')")

    def enable_custom_help_in_user_engagement(self):
        """
        Enables the Customize Help Option under User Engagement Help Menu
        """
        self.go_to_setup_admin_page("HelpMenu/home", 4)
        toggle_span_count = self.browser.get_element_count(
            f"{self.iframe_handler()} span.slds-checkbox_off:visible"
        )
        if toggle_span_count and toggle_span_count > 0:
            self.browser.click(
                f"{self.iframe_handler()} ol.slds-setup-assistant:has-text('Customize the Help Menu') >> .slds-checkbox_faux"
            )

    def enable_data_pipelines(self):
        """
        Enables the Data Pipeline Toggle
        """
        self.go_to_setup_admin_page("SonicGettingStarted/home")
        self.browser.wait_for_elements_state(
            "h2:text-is('Data Pipelines')", ElementState.visible, "30s"
        )
        if not "checked" in self.browser.get_element_states(
            "label:has-text('Disabled')"
        ):
            self.browser.click("label:has-text('Disabled')")
            sleep(3)

    def check_package_id_version(self, package_id=None, wait_for_upgrade=True):
        if not package_id:
            raise Exception("No Package ID Provided")

        # PACKAGE INSTALL URL
        package_install_url = f"{self.cumulusci.org.instance_url}/packagingSetupUI/ipLanding.app?apvId={package_id}"

        # Extend Current Browser Timeout
        self.browser.set_browser_timeout("1000s")

        # Load Package Page and Check for Update
        self.browser.go_to(package_install_url, timeout="90s")
        self.browser.wait_for_elements_state(
            ":nth-match(button.slds-button, 1)", ElementState.visible, "240s"
        )

        if self.browser.get_element_count("h1.upgradeHeader:visible") > 0:
            sleep(2)
            version_regex = r"\((.*?)\)"

            # Get Current Version
            current_version_header = self.browser.get_property(
                "h2.upgradeSubHeader:has-text('Installed')", "innerText"
            )

            # Get new version
            new_version_header = self.browser.get_property(
                "h2.upgradeSubHeader:has-text('New Version')", "innerText"
            )
            old_match = re.search(version_regex, current_version_header)
            new_match = re.search(version_regex, new_version_header)

            # Check Versions
            if old_match and new_match:
                new_version = new_match.group(1)
                old_version = old_match.group(1)

                if new_version != old_version:
                    # Complete Upgrade Request
                    self.browser.click(
                        "div.radioTextContainer:has-text('Install for All Users')"
                    )
                    sleep(1)
                    self.browser.click(
                        "div.securityReviewAcknowledgmentContainer >> input"
                    )
                    sleep(3)
                    self.browser.click("button.installButton")
                    sleep(3)

                    # Check for API Permissions
                    if (
                        self.browser.get_element_count(
                            "div.grantAccessCheckbox >> input:visible"
                        )
                        > 0
                    ):
                        self.browser.click("div.grantAccessCheckbox >> input")
                        sleep(1)

                    # Check for Final Button
                    if (
                        self.browser.get_element_count(
                            "div.packagingSetupUIRssDialogFooter >> button.slds-button:has-text('Continue')"
                        )
                        > 0
                    ):
                        self.browser.click(
                            "div.packagingSetupUIRssDialogFooter >> button.slds-button:has-text('Continue')"
                        )
                        sleep(1)

                    # Wait for Update
                    if wait_for_upgrade:
                        pass

                        # TODO
                        # This needs to lookup the name of the app based on the package id
                        # and then wait for the app to be installed

                        # Lookup Name for the package Id
                        # app_name = TODO

                        # Wait for the app to be installed
                        # while True:
                        #     self.shared.go_to_setup_admin_page("ImportedPackage/home")
                        #     sleep(2)
                        #     current_version = self.browser.get_property(f"iframe >>> tr.dataRow:has-text('{app_name}') >> :nth-match(td.dataCell, 2)", "innerText")

                        #     if not current_version:
                        #         break

                        #     if current_version == new_version:
                        #         break
                        #     else:
                        #         sleep(10)

    def add_profile_to_chat_configuration(
        self, liveagentconfigname: str, profilename: str
    ):
        """
        Adds a specified profile to the specified Chat User Config
        :param liveagentconfigname: Live Chat User Config Name
        :param profilename: Salesforce Profile Name
        """

        if profilename is None:
            raise Exception("Profile Name must be specified")

        if liveagentconfigname is None:
            raise Exception("Live Chat User Config Name must be specified")

        self.go_to_setup_admin_page("EnhancedProfiles/home", 12)
        liveagentconfig = self.find_livechatuserconfig_by_name(liveagentconfigname)
        editurl = f"LiveChatUserConfigSettings/page?address=%2F{liveagentconfig}"
        self.go_to_setup_admin_page(editurl)
        sleep(5)
        self.browser.click("iframe >>> .btn:text-is('Edit')")
        sleep(10)

        self.browser.select_options_by(
            f"iframe >>> td.selectCell:has-text('{profilename}') >> select",
            SelectAttribute.text,
            profilename,
        )
        # there are 5 dueling lists. second one is profiles
        self.browser.click("iframe >>> :nth-match(img.rightArrowIcon, 2)")
        sleep(1)
        # button at top and one on the bottom. dealer's choice
        self.browser.click("iframe >>> :nth-match(.btn:text-is('Save'), 1)")

    # ------------------
    # LOOKUP FUNCTIONS
    # ------------------

    def find_id(
        self,
        object_api_name: str,
        where_clause: str,
        id_column_name: str = "Id",
        enable_logging: bool = False,
    ):
        """
        Queries the target Salesforce Org for an ID based on a given object name and where clause.

        Args:
            object_api_name (str): The API name for the sObject within Salesforce
            where_clause (str): The filter which is applied after the "where" within the query statement
            id_column_name (str): Optional string which defines the Id column name, which is not always Id but this will default to Id if not specified.
            enable_logging (bool): Set to True if you want to log the SOQL Query and Results to a local file. Defaults to False.

        Returns:
            If a record is found, then the Id value is returned. Otherwise None is returned
        """

        # Error Control
        if " " in object_api_name:
            raise Exception("Invalid object api name specified")

        if " " in id_column_name:
            raise Exception("Invalid ID Column name specified")

        if where_clause.lower().startswith("where"):
            where_clause = where_clause.replace("where", "")

        try:
            soql_query = f"SELECT {id_column_name} FROM {object_api_name} where {where_clause} LIMIT 1"

            if enable_logging:
                self.log_to_file(soql_query)

            lookup_result = self.salesforceapi.soql_query(soql_query)

            if enable_logging:
                self.log_to_file(lookup_result)

            if lookup_result["totalSize"] == 1:
                return lookup_result["records"][0][id_column_name]

            return None
        except Exception as e:
            self.log_to_file(e)
            raise e

    def find_profileid_by_name(self, profile_name: str):
        """
        Locates the ID of a profile by friendly name

        Args:
            profile_name: Name of the Salesforce Profile

        Returns:
            Returns Salesforce ID for the Profile Name (If Found) otherwise returns None.
        """
        if not profile_name:
            raise Exception("Profile Name must be specified")

        return self.find_id("Profile", f"Name ='{profile_name}'")

    def find_livechatuserconfig_by_name(self, config_name: str):
        """
        Locates the ID of a Live Chat User Config by Master Label. See: select id, MasterLabel from LiveChatUserConfig

        Args:
            configname (str): Live Chat User Configuration Name (Use the Master Label not the api name)

        Returns:
            Returns Salesforce ID for the Live Chat User Configuration, if found. Otherwise, returns None.
        """
        if not config_name:
            raise Exception("Live Chat User Config Name must be specified")

        return self.find_id("LiveChatUserConfig", f"MasterLabel ='{config_name}'")

    # ------------------
    # LOGGING FUNCTIONS
    # ------------------

    def log_to_file(self, data):
        """
        Use this for local debugging to write data to a temp file

        Args:
            data: Data which you want to log to file. File defaults to ./temp.log
        """
        now = datetime.now()
        dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
        with open("temp.log", "a", encoding="utf-8") as tmpFile:
            tmpFile.write(f"{dt_string}::{data}\n")
            tmpFile.close()

    def move_app_to_start_of_app_menu(self, app_name):
        """Moves a given app to the start of the app menu"""

        # Increase Browser Viewport Size
        # We do this as playwright thinks all tiles are visible even when they are not
        self.browser.set_viewport_size(1440, 2560)

        # Go To Known App which is not Console Layout
        self.go_to_app("Sales")

        # Open App Launcher - Sleep Needed to Allow Tiles to load
        self.browser.wait_for_elements_state(
            "div.slds-icon-waffle", ElementState.visible, "10s"
        )
        self.browser.click("div.slds-icon-waffle")
        self.browser.wait_for_elements_state(
            "button.slds-button:text-is('View All')", ElementState.visible, "10s"
        )
        self.browser.click("button.slds-button:text-is('View All')")
        sleep(3)

        # Click on the App Tile for the given App
        app_tile_selector = (
            f"div.slds-app-launcher__tile-body >> p.slds-truncate:text-is('{app_name}')"
        )
        self.browser.hover(app_tile_selector)
        self.browser.mouse_button(MouseButtonAction.down)

        # Move to place of first tile
        self.browser.mouse_move_relative_to(
            ":nth-match(div.slds-app-launcher__tile-body, 1)"
        )
        self.browser.mouse_button(MouseButtonAction.up)

        # Reset Viewport size
        self.browser.set_viewport_size(1920, 1080)

    def click_link_for_installed_package(self, package_name, link_label):
        """Loads the Installed Packages table for the connected Salesforce Org and then clicks the link next to the package name"""

        self.go_to_setup_admin_page("ImportedPackage/home")
        self.wait_for_page_to_load()
        self.wait_on_element(f"{self.iframe_handler()} table.list", 30)

        if (
            self.browser.get_elements(
                f"{self.iframe_handler()} table.list >> tr.dataRow"
            )
            == 0
        ):
            raise ValueError("No Packages Installed in the target Salesforce Org")

        action_selector = f"{self.iframe_handler()} table.list >> :nth-match(tr.dataRow:has-text('{package_name}'), 1) >> td.actionColumn >> a:text-is('{link_label}')"

        if self.browser.get_element_count(action_selector) == 0:
            raise ValueError("Package and Action Combination not found")

        self.browser.click(action_selector)

    def is_option_selected(self, select_element, target_label):
        """Returns True if the given target label for the selected option matches the label of the selected option"""

        existing_list = self.browser.get_select_options(select_element)
        if len(existing_list) == 0:
            return False
        return any(d["label"] == target_label and d["selected"] for d in existing_list)

    def enable_notification_delivery_setting_ios(self):
        pass
