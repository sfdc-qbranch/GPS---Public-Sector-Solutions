from cumulusci.tasks.salesforce import BaseSalesforceApiTask
import subprocess

class QRobotTestCapture(BaseSalesforceApiTask):

    salesforce_task = True

    task_options = {
        "start_url": {
            "description": "Start URL for the session",
            "required": False
        },
        "org": {
            "description": "org alias",
            "required": False
        }
    }

    def _run_task(self):

        start_url = "/lightning/setup/SetupOneHome/home"

        if "start_url" in self.options:
            start_url = self.options["start_url"]

        try:
            print("Launching Q Robot Sandbox...")
            command = f"npx playwright codegen {self.org_config.instance_url}/secur/frontdoor.jsp\?sid\={self.org_config.access_token}\&retURL\={start_url} --viewport-size '1920,1080'"
            #print(command)
            subprocess.run(command, shell=True)
        except Exception as e:
            print(e)
