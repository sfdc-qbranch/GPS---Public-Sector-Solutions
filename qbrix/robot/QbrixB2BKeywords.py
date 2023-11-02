from time import sleep

from robot.api.deco import library

from qbrix.core.qbrix_robot_base import QbrixRobotTask


@library(scope="GLOBAL", auto_keywords=True, doc_format="reST")
class QbrixB2BKeywords(QbrixRobotTask):
    """Commerce Cloud Keywords"""

    def get_store_id(self, store_name: str = None):
        """
        Gets the Store Id for a given Store Name
            Args:
                store_name (str): The name of the store

            Returns:
                (str) Store Id Value if found, else None
        """

        if store_name is None:
            raise ValueError("Store Name must be specified")

        results = self.salesforceapi.soql_query(
            f"SELECT Id FROM WebStore WHERE Name = '{store_name}' LIMIT 1"
        )

        if results["totalSize"] == 1:
            result_id = results["records"][0]["Id"]
            self.builtin.log_to_console(
                f"\n -> Found Id [{result_id}] for the Web Store [{store_name}]."
            )
            return result_id

        self.builtin.log_to_console(
            f"\n -> No Id for the Web Store Name provided [{store_name}] was found."
        )
        return None

    def start_reindex(self, store_name: str = None):
        """
        Starts the Reindex for a given store

        Args:
            store_name (str): The name of the store
        """

        # Go To Index Page
        store_id = self.get_store_id(store_name)
        if store_id:
            self.builtin.log_to_console(
                f"\n -> Starting reindex of Store ID: {store_id}"
            )
            self.browser.go_to(
                f"{self.cumulusci.org.instance_url}/lightning/page/commerceSearch?lightning__webStoreId={store_id}&ws=%2Flightning%2Fr%2FWebStore%2F{store_id}%2Fview"
            )
            self.shared.wait_for_page_to_load()
            self.shared.wait_and_click(
                ":nth-match(button.slds-button:text-is('Rebuild Index'):visible, 1)"
            )
            self.shared.wait_and_click(
                "div.slds-visual-picker >> span.slds-text-heading_medium:text-is('Full Reindex')"
            )
            self.shared.wait_and_click(
                selector=":nth-match(button.slds-button:text-is('Rebuild'):visible, 1)",
                post_click_sleep=3,
            )
            self.builtin.log_to_console(
                "\n -> Reindex requested! It may take a few minutes for products to appear in the experience cloud site, depending on how many products you have."
            )

    def enable_b2b2c_for_sdo(self, store_name):
        """
        Enables integrations for a given Store Name

        Args:
            store_name (str): The name of the store.
        """

        self.builtin.log_to_console(
            f"\nRunning automation to check and enable demo integrations for store called [{store_name}]..."
        )

        integration_button_selector = (
            ":nth-match(button.slds-button:text-is('Link Integration'):visible, 1)"
        )
        dialog_row_selector = (
            "tr.slds-hint-parent:has-text('Standard Tax') >> label.slds-checkbox_faux"
        )
        next_button_selector = (
            "div.modal-footer >> button.nextButton:text-is('Next'):visible"
        )
        confirm_button_selector = (
            "div.modal-footer >> button.nextButton:text-is('Confirm'):visible"
        )

        store_id = self.get_store_id(store_name)
        if store_id:
            # Go To Tax Page and enable Tax Integration
            self.builtin.log_to_console("\n -> Checking and enabling Tax Integration")
            self.browser.go_to(
                f"{self.cumulusci.org.instance_url}/lightning/page/storeDetail?lightning__webStoreId={store_id}&ws=%2Flightning%2Fr%2FWebStore%2F{store_id}%2Fview&storeDetail__selectedTab=store_tax"
            )
            sleep(2)
            if self.shared.wait_on_element(
                selector=integration_button_selector, timeout=5
            ):
                self.shared.wait_and_click(
                    selector=integration_button_selector, post_click_sleep=2
                )
                self.shared.wait_and_click(dialog_row_selector)
                self.shared.wait_and_click(
                    selector=next_button_selector, post_click_sleep=2
                )
                self.shared.wait_and_click(confirm_button_selector)
            self.builtin.log_to_console("\n -> Tax Integration Complete!")

            # Go To Shipping Calculation Page and Apply Integration
            self.builtin.log_to_console(
                "\n -> Checking and enabling Shipping Calculation Integration"
            )
            self.browser.go_to(
                f"{self.cumulusci.org.instance_url}/lightning/page/storeDetail?lightning__webStoreId={store_id}&ws=%2Flightning%2Fr%2FWebStore%2F{store_id}%2Fview&storeDetail__selectedTab=store_shipping"
            )
            sleep(2)
            if self.shared.wait_on_element(
                selector=integration_button_selector, timeout=5
            ):
                self.shared.wait_and_click(
                    selector=integration_button_selector, post_click_sleep=2
                )
            self.builtin.log_to_console(
                "\n -> Shipping Calculation Integration Complete!"
            )

            # Go To Card Payment Gateway Page and Apply Integration
            self.builtin.log_to_console(
                "\n -> Checking and enabling Card Payments Gateway Integration"
            )
            self.browser.go_to(
                f"{self.cumulusci.org.instance_url}/lightning/page/storeDetail?lightning__webStoreId={store_id}&ws=%2Flightning%2Fr%2FWebStore%2F{store_id}%2Fview&storeDetail__selectedTab=store_payment"
            )
            sleep(2)
            if self.shared.wait_on_element(
                selector=integration_button_selector, timeout=5
            ):
                self.shared.wait_and_click(
                    selector=integration_button_selector, post_click_sleep=2
                )
            self.builtin.log_to_console(
                "\n -> Card Payments Gateway Integration Complete!"
            )

    def enable_salesforce_payments(self):
        """Checks that Salesforce Payments has been enabled in the Salesforce Org"""

        self.builtin.log_to_console(
            "\nRunning automation to check that Salesforce Payments has been enabled..."
        )

        self.shared.go_to_setup_admin_page("PaymentsSettings/home", 2)
        sleep(5)
        if "visible" in self.browser.get_element_states("button:text-is('Enable')"):
            select_button_locator = (
                f"{self.shared.iframe_handler()} button:text-is('Enable')"
            )
            self.browser.click(select_button_locator)
            sleep(5)
            self.builtin.log_to_console("\n -> Salesforce Payments is now enabled.")
        else:
            self.builtin.log_to_console(
                "\n -> Salesforce Payments appears to already be enabled."
            )
