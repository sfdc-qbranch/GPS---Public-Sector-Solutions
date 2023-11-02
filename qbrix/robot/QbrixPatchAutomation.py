from time import sleep

from robot.api.deco import library

from qbrix.core.qbrix_robot_base import QbrixRobotTask
from qbrix.robot.QbrixFieldServiceKeywords import QbrixFieldServiceKeywords


@library(scope='GLOBAL', auto_keywords=True, doc_format='reST')
class QbrixPatchAutomation(QbrixRobotTask):

    def __init__(self):
        super().__init__()
        self._field_service_keywords = None

    @property
    def field_service_keywords(self):

        """Loads Q Robot Field Service Keywords and Methods"""

        if self._field_service_keywords is None:
            self._field_service_keywords = QbrixFieldServiceKeywords()
        return self._field_service_keywords

    def disable_field_service(self):
        self.field_service_keywords.enable_field_service(turn_off=True)

    def deactivate_flow(self, flow_name: str):
        if not flow_name:
            return

        toolingapi = self.cumulusci._init_api("tooling/")
        result = toolingapi.query(f"SELECT Id from Flow where MasterLabel = '{flow_name}' AND Status = 'Active'")

        if result['totalSize'] > 0:
            self.browser.go_to(f"{self.cumulusci.org.instance_url}/builder_platform_interaction/flowBuilder.app?flowId={result['records'][0]['Id']}")
            sleep(3)
            self.browser.click("button:text-is('Deactivate')")
            sleep(2)


    def update_sdo_service_omniflow(self):
        pass