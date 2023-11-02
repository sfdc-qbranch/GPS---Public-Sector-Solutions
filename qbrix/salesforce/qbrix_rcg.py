from abc import ABC
import json
from cumulusci.tasks.salesforce import BaseSalesforceApiTask

class RefreshCache(BaseSalesforceApiTask, ABC):

    """Refreshes B2B Cache"""

    salesforce_task = True
    task_docs = "Refreshes the B2B Cache"

    def _run_task(self):
        """Runs the refresh B2B cache task"""

        self.logger.info("Sending Request to reset B2B Cache...")

        headers = {
            "Content-Type": "application/json; charset=utf-8",
            "Authorization": f"Bearer {self.org_config.access_token}"
            }

        endpoint = f"{self.org_config.instance_url}/services/apexrest/b2b/refresh-cache"

        try:
            self.sf.restful(
            endpoint,
            method="POST",
            headers=headers,
        )
        except Exception as e:
            self.logger.error(e)
            return

class RefreshDecisionTree(BaseSalesforceApiTask, ABC):

    """Refreshes B2B Decision Tree"""

    salesforce_task = True
    task_docs = "Refreshes the B2B Decision Tree"

    def _refresh_tree(self, tree_name):

        try:
            self.sf.restful(
            "actions/standard/refreshDecisionTable",
            method="POST",
            data=json.dumps({
                'inputs': [
                    {
                        'decisionTableApiName': tree_name ,
                    },
                ],
            })
        )
        except Exception as e:
            self.logger.error(e)
            return

    def _run_task(self):
        """Runs the refresh B2B Decision Tree task"""

        self.logger.info("Checking Decision Tree Cache for RCG")
        decision_table_results = self.sf.query("SELECT DeveloperName FROM DecisionTable where status = 'Active'")
        if decision_table_results and decision_table_results["totalSize"] > 0:
            for table in decision_table_results["records"]:
                self._refresh_tree(table["DeveloperName"])
            self.logger.info("Complete!")
        else:
            self.logger.info("No Active Decision Tables in org. Skipping Task")

class RebuildStoreIndex(BaseSalesforceApiTask, ABC):

    """Refreshes B2B Store Index"""

    salesforce_task = True
    task_docs = "Refreshes the B2B Store Index"

    def _request_rebuild(self, store_id):
        try:
            self.sf.restful(
            f"commerce/management/webstores/{store_id}/search/indexes",
            method="POST",
        )
        except Exception as e:
            self.logger.error(e)
            return

    def _run_task(self):
        """Runs the refresh B2B Store Index task"""

        self.logger.info("Checking for Stores in Org...")

        store_results = self.sf.query("Select Id From Webstore")
        if store_results and store_results["totalSize"] > 0:
            self.logger.info("Sending reindex requests...")
            for store in store_results["records"]:
                self._request_rebuild(store["Id"])
        self.logger.info("Complete!")

class FixEinsteinVisionDatasets(BaseSalesforceApiTask, ABC):

    """Refreshes B2B Store Index"""

    salesforce_task = True
    task_docs = "Refreshes the B2B Store Index"

    EINSTEIN_VISION_DATASET = [
        {
            "attributes": { type: "AiDataset" },
            "Name": "Alpine Cereal Dataset",
            "ContentType": "Object Detection",
            "DatasetType": "Training",
            "FileUrl": "https://sfdc-ckz-b2b.s3.amazonaws.com/RCG/Einstein/AlpineCereal.zip",
        },
        {
            "attributes": { type: "AiDataset" },
            "Name": "Alpine Energy Bars Dataset",
            "ContentType": "Object Detection",
            "DatasetType": "Training",
            "FileUrl": "https://sfdc-ckz-b2b.s3.amazonaws.com/RCG/Einstein/AlpineEnergyBars-Compressed.zip",
        },
        {
            "attributes": { type: "AiDataset" },
            "Name": "Alpine Energy Voids Dataset",
            "ContentType": "Object Detection",
            "DatasetType": "Training",
            "FileUrl": "https://sfdc-ckz-b2b.s3.amazonaws.com/RCG/Einstein/voids.zip",
        },
        {
            "attributes": { type: "AiDataset" },
            "Name": "Alpine Energy Out-of-Stock Dataset",
            "ContentType": "Object Detection",
            "DatasetType": "Training",
            "FileUrl": "https://sfdc-ckz-b2b.s3.amazonaws.com/RCG/Einstein/out-of-stock.zip",
        },
    ]

    def _request_rebuild(self, records):
       try:
            self.sf.restful(
                method="PATCH", path="composite/sobjects", json=dict(records=records)
            )
       except Exception as e:
            self.logger.error(e)
            return

    def _request_upload_datasets(self):
        try:
            self.sf.restful(
                method="POST", path="composite/sobjects", json=dict(records=self.EINSTEIN_VISION_DATASET)
            )
        except Exception as e:
            self.logger.error(e)
            return

    def _run_task(self):
        """Runs the refresh B2B Store Index task"""

        self.logger.info("Checking for Stores in Org...")

        try:
            ai_dataset_results = self.sf.query("Select Id From AiDataset")
            if ai_dataset_results and ai_dataset_results["totalSize"] > 0:
                self.logger.info("Sending reindex requests...")
                self._request_rebuild(ai_dataset_results["records"])
                self._request_upload_datasets()
        except Exception as e:
            self.logger.info("AiDatasets Object not enabled in target org. Skipping task")
