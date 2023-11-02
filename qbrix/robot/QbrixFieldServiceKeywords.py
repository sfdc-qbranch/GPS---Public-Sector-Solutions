from time import sleep

from Browser import ElementState, SelectAttribute
from robot.api.deco import library

from qbrix.core.qbrix_robot_base import QbrixRobotTask


@library(scope="GLOBAL", auto_keywords=True, doc_format="reST")
class QbrixFieldServiceKeywords(QbrixRobotTask):

    """Keywords for Qbrix Field Service"""

    def enable_field_service(self, turn_off: bool = False):
        """
        Enables Field Service Setting in Salesforce Setup
        """

        # Go To Field Service Setup
        self.shared.go_to_setup_admin_page("FieldServiceSettings/home", 10)

        self.builtin.log_to_console("\nLoaded Field Service Settings Page")

        # Enable Field Service Setting
        field_service_toggle_selector = (
            "span.slds-form-element__label:has-text('Field Service')"
        )
        self.browser.wait_for_elements_state(
            field_service_toggle_selector, ElementState.visible, "30s"
        )

        self.builtin.log_to_console("\nChecking Field Service Setting")

        if (
            not "checked"
            in self.browser.get_element_states(field_service_toggle_selector)
            and turn_off == False
        ) or (
            "checked" in self.browser.get_element_states(field_service_toggle_selector)
            and turn_off
        ):
            self.browser.click(field_service_toggle_selector)
            sleep(10)

            if turn_off:
                self.builtin.log_to_console("\n -> Disabled")
            else:
                self.builtin.log_to_console("\n -> Enabled")

    def go_to_field_service_admin_page(self):
        """Go directly to the Field Service admin page"""
        self.shared.go_to_app("Field Service Admin")
        # Go To Field Service Package Settings Page
        self.browser.go_to(
            f"{self.cumulusci.org.instance_url}/lightning/n/FSL__Field_Service_Settings",
            timeout="30s",
        )
        iframe_selector = self.shared.iframe_handler()
        self.browser.wait_for_elements_state(
            f"{iframe_selector} h1:has-text('Getting Started'):visible",
            ElementState.visible,
            "120s",
        )
        self.builtin.log_to_console("\nLoaded Field Service App Settings Page")

    def field_service_sdo_config(self):
        """Go to Field Service Settings and configure additional settings for demo use"""

        self.builtin.log_to_console("\nConfiguring SDO Configuration for Field Service")

        # Go to Field Service Settings
        self.go_to_field_service_admin_page()
        iframe_selector = self.shared.iframe_handler()

        # Enable Schedule Bundling
        self.builtin.log_to_console("\n -> Enabling Schedule Bundling")
        self.builtin.log_to_console("\nEnabling Scheduling")
        menu_scheduling_selector = f"{iframe_selector} id=SettingsMenu >> div.menuItem >> span:text-is('Scheduling'):visible"
        tabs_bundling_selector = (
            f"{iframe_selector} div.settings-tab:has-text('Bundling')"
        )
        tabs_routing_selector = (
            f"{iframe_selector} div.settings-tab:has-text('Routing')"
        )
        checkbox_bundling_selector = f"{iframe_selector} div.setting-row-container:has-text('Bundle your service appointments') >> div.slds-checkbox"
        checkbox_streetlevel_selector_status = f"{iframe_selector} div.setting-row-container:has-text('Enable Street Level Routing') >> label.slds-checkbox__label >> input"
        checkbox_pointtopoint_selector_status = f"{iframe_selector} div.setting-row-container:has-text('Enable Point-to-Point Predictive Routing') >> label.slds-checkbox__label >> input"
        checkbox_streetlevel_selector = f"{iframe_selector} div.setting-row-container:has-text('Enable Street Level Routing') >> div.slds-checkbox"
        checkbox_pointtopoint_selector = f"{iframe_selector} div.setting-row-container:has-text('Enable Point-to-Point Predictive Routing') >> div.slds-checkbox"
        save_button_selector = (
            f"{iframe_selector} div.save-footer >> div.save-button:visible"
        )

        scheduling_changes_made = False
        self.browser.click(menu_scheduling_selector)
        sleep(2)
        self.browser.click(tabs_bundling_selector)
        sleep(5)

        bundle_activation_selector_state = self.browser.get_element_states(
            f"{iframe_selector} div.bundle-settings >> p:text-is('Service appointment bundles are active.')"
        )

        if "visible" not in bundle_activation_selector_state:
            self.browser.click(checkbox_bundling_selector)
            self.browser.click(save_button_selector)
            sleep(2)

        self.browser.click(tabs_routing_selector)
        sleep(2)

        if "checked" in self.browser.get_element_states(
            checkbox_pointtopoint_selector_status
        ):
            self.browser.click(checkbox_pointtopoint_selector)
            sleep(2)
            scheduling_changes_made = True

        if "checked" in self.browser.get_element_states(
            checkbox_streetlevel_selector_status
        ):
            self.browser.click(checkbox_streetlevel_selector)
            sleep(2)
            scheduling_changes_made = True

        if scheduling_changes_made:
            self.browser.click(save_button_selector)
            sleep(2)

        # Setup Dispatcher UI - Custom Actions
        self.builtin.log_to_console("\nEnabling Dispatcher UI > Custom Actions")
        menu_dispatcher_ui_selector = f"{iframe_selector} #SettingsMenu >> div.menuItem >> span:text-is('Dispatcher Console UI'):visible"
        drag_jumps_selector = f"{iframe_selector} div.setting-row-container:has-text('Drag jumps on gantt') >> div.select-container >> input.input-settings"
        gantt_settings_selector = (
            f"{iframe_selector} div.settings-tab:has-text('Updating the Gantt')"
        )
        gantt_refresh_selector = f"{iframe_selector} div.setting-row-container:has-text('Seconds between Gantt refreshes') >> input.input-settings"
        tabs_custom_actions_selector = (
            f"{iframe_selector} div.settings-tab:has-text('Custom Actions')"
        )
        action_cat_selector = (
            f"{iframe_selector} #CA-GanttSection >> div:text-is('Mass Actions')"
        )
        new_action_btn_selector = f"{iframe_selector} #CA-newAction"
        new_action_label_selector = f"{iframe_selector} div.CA-field-container:has-text('Label in Dispatcher Console') >> input.CA-input-label"
        vf_page_selector = f"{iframe_selector} div.CA-field-container:has-text('Visualforce') >> select.select-setting"
        custom_perm_selector = f"{iframe_selector} div.CA-field-container:has-text('Required Custom Permission') >> select.select-setting"

        self.browser.click(menu_dispatcher_ui_selector)

        # Configure Gantt Jumps
        self.builtin.log_to_console("\nConfiguring Gantt Jumps")
        self.browser.fill_text(drag_jumps_selector, "15")
        self.browser.click(save_button_selector)
        sleep(5)

        # Gantt Updates
        self.builtin.log_to_console("\nConfiguring Gantt Updates")
        self.browser.click(gantt_settings_selector)
        sleep(1)
        self.browser.fill_text(gantt_refresh_selector, "10")
        self.browser.click(save_button_selector)
        sleep(5)

        # Check and Enable Custom Actions
        self.builtin.log_to_console("\nConfiguring Custom Actions")
        self.browser.click(tabs_custom_actions_selector)
        sleep(15)
        self.browser.click(action_cat_selector)
        sleep(2)

        custom_actions_added = False

        # Create Demo Bundle
        self.builtin.log_to_console("\nConfiguring Demo Bundle Flow Integrations")
        if (
            self.browser.get_element_count(
                f"{iframe_selector} #CA-ActionsList >> div.singleCustomAction:has-text('Create Demo Bundle')"
            )
            == 0
        ):
            self.browser.click(new_action_btn_selector)
            sleep(1)
            self.browser.click(
                f"{iframe_selector} #CA-ActionsList >> div.singleCustomAction:has-text('My Action')"
            )
            sleep(1)
            self.browser.fill_text(new_action_label_selector, "Create Demo Bundle")
            self.browser.select_options_by(
                vf_page_selector,
                SelectAttribute.text,
                "SDO_FSL_Launch_Create_Bundles_Flow",
            )
            self.browser.select_options_by(
                custom_perm_selector,
                SelectAttribute.text,
                "Gantt and List - Bundle and Unbundle",
            )
            custom_actions_added = True

        # Create Sliding Demo Data
        self.builtin.log_to_console("\nCreating sliding Demo Data")
        if "visible" not in self.browser.get_element_states(
            f"{iframe_selector} div.singleCustomAction:has-text('Create Sliding Demo Data')"
        ):
            self.browser.click(new_action_btn_selector)
            sleep(1)
            self.browser.click(
                f"{iframe_selector} #CA-ActionsList >> div.singleCustomAction:has-text('My Action')"
            )
            sleep(1)
            self.browser.fill_text(
                new_action_label_selector, "Create Sliding Demo Data"
            )
            self.browser.select_options_by(
                vf_page_selector,
                SelectAttribute.text,
                "SDO_FSL_Launch_Sliding_Flow_Launch_Slide",
            )
            self.browser.select_options_by(
                custom_perm_selector, SelectAttribute.text, "Bulk Schedule"
            )
            custom_actions_added = True

        if custom_actions_added:
            self.browser.click(save_button_selector)
            sleep(5)

        # Setup Optimization
        self.builtin.log_to_console("\nConfiguring Optimization")
        menu_optimize_selector = f"{iframe_selector} id=SettingsMenu >> div.menuItem >> span:text-is('Optimization'):visible"
        optimization_checkbox_selector = f"{iframe_selector} div.slds-media:has-text('Optimization Insights') >> div.transitions-checkbox >> span.toggled-label:text-is('OFF')"

        self.browser.click(menu_optimize_selector)
        sleep(1)
        if self.browser.get_element_count(optimization_checkbox_selector) == 1:
            self.browser.click(optimization_checkbox_selector)
            self.browser.click(save_button_selector)
            sleep(5)

        sleep(5)

    def enable_all_field_service_permission_sets(self):
        """
        Enables all Field Service Permission Sets and also updates Permissions Sets if there are updates waiting
        """

        self.builtin.log_to_console("\nConfiguring Field Service Permissions")

        self.go_to_field_service_admin_page()
        iframe_selector = self.shared.iframe_handler()
        self.browser.click(
            f"{iframe_selector} div.settings-tab:has-text('Permission Sets')"
        )
        sleep(30)
        self.builtin.log_to_console("\n -> Loading Permission Sets")

        create_permission_selector = (
            f"{iframe_selector} div:text-is('Create Permissions')"
        )
        update_permission_selector = (
            f"{iframe_selector} div:text-is('Update Permissions')"
        )

        current_selector = None
        for x in range(0, 4):
            self.builtin.log_to_console(f"\n -> [DEBUGGING] Variable X = [{x}]")

            if x == 0 or x == 1:
                current_selector = create_permission_selector

            if x == 2 or x == 3:
                current_selector = update_permission_selector

            permission_button_elements = self.browser.get_elements(current_selector)

            if permission_button_elements is None:
                self.builtin.log_to_console(
                    "\n -> Current selector has not found any Permission Set buttons. Adjusting selector..."
                )
                continue

            self.builtin.log_to_console("\n -> Applying Permissions")
            for permission_button in permission_button_elements:
                if "visible" in self.browser.get_element_states(permission_button):
                    self.browser.click(permission_button)
                    sleep(30)

        self.builtin.log_to_console("\n -> Permissions Applied!")

    def disable_field_service_status_transitions(self):
        """
        Disables Field Service Status Transitions
        """
        self.go_to_field_service_admin_page()

        self.builtin.log_to_console("\nDisabling Field Service Status Transistions...")

        iframe_selector = self.shared.iframe_handler()
        self.browser.click(
            f"{iframe_selector} span:text-is('Service Appointment Life Cycle')"
        )
        self.browser.wait_for_elements_state(
            f"{iframe_selector} h1:text-is('Service Appointment Life Cycle')",
            ElementState.visible,
            "15s",
        )
        self.browser.click(
            f"{iframe_selector} div.settings-tab:has-text('Status Transitions')"
        )
        self.browser.wait_for_elements_state(
            f"{iframe_selector} div:text-is('Service Appointment Status Transitions')",
            ElementState.visible,
            "15s",
        )
        visible = "visible" in self.browser.get_element_states(
            f"{iframe_selector} :nth-match(span.innerCheckboxValue.unchecked, 1)"
        )
        if not visible:
            toggle_switch = self.browser.get_element(
                f"{iframe_selector} :nth-match(span.innerCheckboxValue.checked, 1)"
            )
            self.browser.click(toggle_switch)
            self.browser.click(
                f"{iframe_selector} .ng-scope:nth-child(2) >> #SettingContainer .save-button"
            )
            self.browser.wait_for_elements_state(
                f"{iframe_selector} .ng-scope:nth-child(2) >> span:text-is('Your changes were saved.')",
                ElementState.visible,
                "10s",
            )
        self.builtin.log_to_console(
            "\nConfiguring Field Service Permissions -> Complete!"
        )

    def disable_field_service_integration(self):
        """
        Disables Field Service Integration
        """
        self.builtin.log_to_console("\nDisabling Field Service Integration...")
        self.shared.go_to_setup_admin_page("FieldServiceSettings/home", 5)
        checked = "checked" in self.browser.get_element_states(
            "label:has-text('Permissions to access data needed for optimization, automatic scheduling, and service appointment bundling.')"
        )
        if checked:
            toggle_switch = self.browser.get_element(
                "label:has-text('Permissions to access data needed for optimization, automatic scheduling, and service appointment bundling.')"
            )
            self.browser.click(toggle_switch)
            sleep(5)
            self.browser.click("button:text-is('Save')")
            sleep(5)
            self.builtin.log_to_console("\n -> Complete!")

    def relax_security_on_fs_apps(self, connected_app_label):
        """
        Relaxes Security Options on the Fields Service Mobile Apps. Should only be used for demo purposes.
        """

        self.builtin.log_to_console(
            f"\nConfiguring Security on Field Service Connected App with name [{connected_app_label}]..."
        )

        self.shared.go_to_setup_admin_page("ConnectedApplication/home")
        iframe_selector = self.shared.iframe_handler()
        self.browser.wait_for_elements_state(
            f"{iframe_selector} h1:text-is('Connected Apps')",
            ElementState.visible,
            "15s",
        )

        self.builtin.log_to_console("\n -> Loaded Connected Apps main page")

        # click on the label column to filter descending - reduce pages and pages
        self.browser.click(f"{iframe_selector} a:text-is('Master Label')")
        if self.shared.wait_on_element(
            f"{iframe_selector} a:text-is('{connected_app_label}')", 15
        ):
            self.builtin.log_to_console(
                "\n -> Found Connected app. Loading configuration..."
            )
            self.browser.click(f"{iframe_selector} a:text-is('{connected_app_label}')")
            self.browser.wait_for_elements_state(
                f"{iframe_selector} h2.mainTitle:text-is('Connected App Detail')",
                ElementState.visible,
                "15s",
            )

            self.builtin.log_to_console("\n -> Applying policy changes...")
            self.browser.click(f"{iframe_selector} .btn:has-text('Edit Policies')")
            self.browser.wait_for_elements_state(
                f"{iframe_selector} h2.mainTitle:text-is('Connected App Edit')",
                ElementState.visible,
                "15s",
            )
            self.browser.select_options_by(
                f"{iframe_selector} #ippolicy",
                SelectAttribute.text,
                "Relax IP restrictions",
            )
            sleep(10)
            self.browser.select_options_by(
                f"{iframe_selector} #MobileSessionTimeout",
                SelectAttribute.text,
                "--None--",
            )
            sleep(10)
            self.browser.select_options_by(
                f"{iframe_selector} #PinLength", SelectAttribute.text, "--None--"
            )
            sleep(10)
            self.browser.click(f"{iframe_selector} .btn:has-text('Save')")
            self.builtin.log_to_console("\n -> Saving...")
            self.browser.wait_for_elements_state(
                f"{iframe_selector} h2.mainTitle:text-is('Connected App Detail')",
                ElementState.visible,
                "15s",
            )
            self.builtin.log_to_console("\n -> Configuration Complete!")
        else:
            self.builtin.log_to_console(
                f"\n -> The connected app with name [{connected_app_label}] was not found. Moving onto the next (if any)"
            )

    def relax_security_for_connected_apps(self):
        self.relax_security_on_fs_apps("Salesforce Field Service for iOS")
        self.relax_security_on_fs_apps("Salesforce Field Service for Android")

    def select_default_territory(self, territory=None):
        """
        Sets the Default Territory for the Field Service Dispatcher Console
        """

        self.builtin.log_to_console("\nSetting Default Territory for Field Service")

        # Set to Default Territory if None passed
        if not territory:
            territory = "*San Francisco"

        self.builtin.log_to_console(f"\n -> Territory will be set to [{territory}]")

        # Go to Field Service App and load Field Service Tab
        self.shared.go_to_app("Field Service")
        sleep(2)
        self.browser.go_to(
            f"{self.cumulusci.org.instance_url}/lightning/n/FSL__FieldService",
            timeout="90s",
        )
        self.builtin.log_to_console("\n -> Loaded Field Service Configuration Page")

        # Ensure we are viewing territories
        self.builtin.log_to_console("\n -> Checking current territory configuration...")
        self.browser.wait_for_elements_state(
            f"iframe >>> #LeftLocationFilteringButton", ElementState.visible, "120s"
        )

        iframe_selector = self.shared.iframe_handler()

        self.browser.click(f"{iframe_selector} #LeftLocationFilteringButton")
        sleep(1)

        # Load list of current locations
        locations_count = self.browser.get_element_count(
            f"{iframe_selector} div.locationFilterRow"
        )

        if not locations_count:
            locations_count = 0

        self.builtin.log_to_console(f"\n -> Found {locations_count} locations on page.")

        if locations_count > 0:
            # Select Location as Favorite and switch to it
            territory_location_row_selector = f"{iframe_selector} #TF-TerritoriesTree >> div.locationFilterRow:has-text('{territory}')"

            self.browser.click(
                "{} >> label:text-matches('^{}$')".format(
                    territory_location_row_selector, territory.replace("*", ".")
                )
            )
            self.browser.click(
                "{} >> svg.slds-icon.favorite-territory".format(
                    territory_location_row_selector
                )
            )
            self.browser.click(
                "{} >> span.switch-location".format(territory_location_row_selector)
            )

            sleep(1)
            self.builtin.log_to_console("\n -> Loaded new configuration!")
        else:
            self.builtin.log_to_console("\n -> No locations loaded. Skipping.")

    def go_to_field_service_mobile_settings_page(self):
        """Goes to the Field Service Mobile Settings Page"""

        self.browser.go_to(
            f"{self.cumulusci.org.instance_url}/lightning/setup/FieldServiceMobileSettings/home",
            timeout="90s",
        )
        sleep(1)
        self.builtin.log_to_console("\n -> Loaded Field Service Mobile Settings Page")

        self.browser.click(
            f"{self.shared.iframe_handler()} tr:has-text('Field Service Mobile Settings') >> lightning-button-menu"
        )
        sleep(1)
        self.browser.click(
            f"{self.shared.iframe_handler()} lightning-menu-item .slds-dropdown__item:has-text('Show Details')"
        )
        self.builtin.log_to_console("\n -> Loaded Details")

    def create_mobile_app_extension(
        self,
        label,
        type,
        name,
        launch_value,
        object_scope=None,
        install_url=None,
        pageReload=True,
    ):
        """
        Creates a mobile app extension
        """

        self.builtin.log_to_console(
            f"\nRunning automation to create Mobile App Extension for Field Service.\nConfiguration:\n-> Label: {label}\n-> Type: {type}\n-> Name: {name}\n-> Launch Value: {launch_value}\n-> Object Scope: {object_scope}"
        )

        # Handle Page Reloads (i.e. If the mobile settings page needs to be reopened)
        if pageReload:
            self.go_to_field_service_mobile_settings_page()
            sleep(2)
        else:
            sleep(2)

        # Setup Common Selectors
        new_button_selector = f"{self.shared.iframe_handler()} div.slds-card__header.slds-grid:has-text('App Extensions') >> button.slds-button:text-is('New')"
        self.browser.scroll_to_element(new_button_selector)

        # Check for Existing Configuration
        self.builtin.log_to_console("\n -> Checking for an existing configuration...")
        if (
            self.browser.get_element_count(
                f"{self.shared.iframe_handler()} th >> div.slds-truncate >> lightning-base-formatted-text:text-is('{label}')"
            )
            == 0
        ):
            self.builtin.log_to_console(
                "\n -> No existing configuration found. Continuing to create a new one..."
            )

            # Open New App Extension Modal
            self.browser.click(new_button_selector)
            sleep(1)

            # Enter Details

            # Assign Label
            self.browser.click("lightning-input:has-text('Label') >> input.slds-input")
            self.browser.fill_text(
                "lightning-input:has-text('Label') >> input.slds-input", label
            )

            # Assign Name
            self.browser.click("lightning-input:has-text('Name') >> input.slds-input")
            self.browser.fill_text(
                "lightning-input:has-text('Name') >> input.slds-input", name
            )

            # Assign Launch Value
            self.browser.click(
                "lightning-input:has-text('Launch Value') >> input.slds-input"
            )
            self.browser.fill_text(
                "lightning-input:has-text('Launch Value') >> input.slds-input",
                launch_value,
            )

            # Assign Object Scope (If any)
            if object_scope:
                self.browser.click(
                    "lightning-input:has-text('Scoped To Object Types') >> input.slds-input"
                )
                self.browser.fill_text(
                    "lightning-input:has-text('Scoped To Object Types') >> input.slds-input",
                    object_scope,
                )

            # Assign Installation URL (If any)
            if install_url:
                self.browser.click(
                    "lightning-input:has-text('Installation URL') >> input.slds-input"
                )
                self.browser.fill_text(
                    "lightning-input:has-text('Installation URL') >> input.slds-input",
                    install_url,
                )

            # Assign Type
            self.browser.click("lightning-combobox.type")
            self.browser.click(
                f"lightning-base-combobox-item >> span.slds-truncate:text-is('{type}')"
            )

            # Save Changes
            sleep(1)
            self.browser.click("button.slds-button:text-is('Save')")
            sleep(1)
            self.builtin.log_to_console("\n -> Saving Changes...")
            if (
                self.browser.get_element_count(
                    "div.slds-modal__footer >> lightning-helptext.slds-m-right_small >> button.slds-button_icon-error >> span.slds-assistive-text:has-text('Help')"
                )
                == 1
            ):
                self.builtin.log_to_console(
                    f"\n{label} Failed to create. Invalid details."
                )
                self.browser.click("button.slds-button:text-is('Cancel')")

        else:
            self.builtin.log_to_console(f"\n{label} Already Exists... Skipping")
