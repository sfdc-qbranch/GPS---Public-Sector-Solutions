from time import sleep

from Browser import ElementState
from robot.api.deco import library

from qbrix.core.qbrix_robot_base import QbrixRobotTask


@library(scope="GLOBAL", auto_keywords=True, doc_format="reST")
class QbrixDPAKeywords(QbrixRobotTask):

    """Keywords for DPA"""

    def activate_omnistudio_metadata(self):
        self.go_to_lightning_setup_omnistudio_settings()
        self.enable_omnistudio_metadata()

    def activate_standard_omnistudio_runtime(self):
        self.go_to_lightning_setup_omnistudio_settings()
        self.enable_standard_omnistudio_runtime()
        self.builtin.log_to_console("\n -> Activated OmniStudio Runtime")

    def deactivate_standard_omnistudio_runtime(self):
        self.go_to_lightning_setup_omnistudio_settings()
        self.disable_standard_omnistudio_runtime()
        self.builtin.log_to_console("\n -> Deactivated OmniStudio Runtime")

    def activate_dataraptor_versioning(self):
        self.go_to_lightning_setup_omnistudio_settings()
        self.enable_dataraptor_versioning()
        self.builtin.log_to_console("\n -> Activated Dataraptor Versioning")

    def deactivate_dataraptor_versioning(self):
        self.go_to_lightning_setup_omnistudio_settings()
        self.disable_dataraptor_versioning()
        self.builtin.log_to_console("\n -> Deactivated Dataraptor Versioning")

    def go_to_lightning_setup_omnistudio_settings(self):
        """
        Goes directly to set up OmniStudio Settings Settings in Lightning UI
        """
        self.browser.go_to(
            f"{self.cumulusci.org.instance_url}/lightning/setup/OmniStudioSettings/home"
        )
        self.browser.wait_for_elements_state(
            "h1:has-text('OmniStudio Settings')", ElementState.visible, "30s"
        )
        self.builtin.log_to_console("\n -> Loaded OmniStudio Settings Page")

    def enable_omnistudio_metadata(self):
        """
        Enable once. Toggle will be disabled after that.
        """
        sleep(10)
        # 1 = OmniStudio Metadata - index 0
        # 2 = Standard OmniStudio Runtime - index 1
        # 3 = DataRaptor Versioning - index 2

        checked = "checked" in self.browser.get_element_states(
            ":nth-match(label:has-text('OmniStudio Metadata'), 1)"
        )
        if not checked:
            toggle_switch = self.browser.get_element(
                ":nth-match(label:has-text('OmniStudio Metadata'), 1)"
            )
            self.browser.click(toggle_switch)
            sleep(1)
        sleep(15)
        try:
            self.shared.click_button_with_text("OK")
            sleep(10)
            self.builtin.log_to_console("\n -> Enabled OmniStudio Metadata")
        except Exception as e:
            self.builtin.log_to_console(
                f"\n -> [SILENT FAILURE] Unable to enable OmniStudio Metadata.\nError Details: {e}"
            )

        self.go_to_lightning_setup_omnistudio_settings()

    def enable_standard_omnistudio_runtime(self):
        sleep(10)
        # 1 = OmniStudio Metadata - index 0
        # 2 = Standard OmniStudio Runtime - index 1
        # 3 = DataRaptor Versioning - index 2

        js_var = self.build_toggle_on_js(1)
        self.browser.evaluate_javascript(
            ":nth-match(runtime_omnistudio-pref-toggle,2)", js_var
        )
        sleep(15)
        self.go_to_lightning_setup_omnistudio_settings()

    def disable_standard_omnistudio_runtime(self):
        sleep(10)
        # 1 = OmniStudio Metadata - index 0
        # 2 = Standard OmniStudio Runtime - index 1
        # 3 = DataRaptor Versioning - index 2

        checked = "checked" in self.browser.get_element_states(
            ":nth-match(label:has-text('Managed Package Runtime'), 1)"
        )
        if checked:
            toggle_switch = self.browser.get_element(
                ":nth-match(label:has-text('Managed Package Runtime'), 1)"
            )
            self.browser.click(toggle_switch)
            sleep(1)
        sleep(15)
        self.go_to_lightning_setup_omnistudio_settings()

    def enable_dataraptor_versioning(self):
        sleep(10)
        # 1 = OmniStudio Metadata - index 0
        # 2 = Standard OmniStudio Runtime - index 1
        # 3 = DataRaptor Versioning - index 2

        js_var = self.build_toggle_on_js(2)
        self.browser.evaluate_javascript(
            ":nth-match(runtime_omnistudio-pref-toggle,3)", js_var
        )
        sleep(15)

        self.go_to_lightning_setup_omnistudio_settings()

    def disable_dataraptor_versioning(self):
        sleep(10)
        # 1 = OmniStudio Metadata - index 0
        # 2 = Standard OmniStudio Runtime - index 1
        # 3 = DataRaptor Versioning - index 2

        js_var = self.build_toggle_off_js(2)
        self.browser.evaluate_javascript(
            ":nth-match(runtime_omnistudio-pref-toggle,3)", js_var
        )
        sleep(15)
        self.go_to_lightning_setup_omnistudio_settings()

    def build_toggle_on_js(self, toggleindex: int):
        # use replace over format to get around { field error on multiple line string
        return """(elements)=>
                {
                    isDisabled=document.querySelectorAll('runtime_omnistudio-pref-toggle')[{toggleindex}].shadowRoot.querySelector('lightning-input').shadowRoot.querySelector('input').getAttribute('disabled');
                    if(isDisabled==null)
                    {
                        isChecked =document.querySelectorAll('runtime_omnistudio-pref-toggle')[{toggleindex}].shadowRoot.querySelector('lightning-input').getAttribute('checked');
                        if(isChecked==null)
                        {
                            document.querySelectorAll('runtime_omnistudio-pref-toggle')[{toggleindex}].shadowRoot.querySelector('lightning-input').shadowRoot.querySelector('input').click();
                        }
                    }
                }""".replace(
            "{toggleindex}", str(toggleindex)
        )

    def build_toggle_off_js(self, toggleindex: int):
        # use replace over format to get around { field error on multiple line string
        return """(elements)=>
                {
                    isDisabled=document.querySelectorAll('runtime_omnistudio-pref-toggle')[{toggleindex}].shadowRoot.querySelector('lightning-input').shadowRoot.querySelector('input').getAttribute('disabled');
                    if(isDisabled==null)
                    {
                        isChecked =document.querySelectorAll('runtime_omnistudio-pref-toggle')[{toggleindex}].shadowRoot.querySelector('lightning-input').getAttribute('checked');
                        if(isChecked!=null)
                        {
                            document.querySelectorAll('runtime_omnistudio-pref-toggle')[{toggleindex}].shadowRoot.querySelector('lightning-input').shadowRoot.querySelector('input').click();
                        }
                    }
                }""".replace(
            "{toggleindex}", str(toggleindex)
        )
