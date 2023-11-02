import atexit
import json
import os
import socket
import subprocess
import sys
import uuid
from abc import abstractmethod
from datetime import datetime

import requests
from cumulusci.core.config import ScratchOrgConfig
from cumulusci.core.exceptions import CommandException
from cumulusci.tasks.sfdx import SFDXBaseTask
from cumulusci.cli.runtime import CliRuntime
from qbrix.tools.shared.qbrix_authentication import * 
from qbrix.tools.shared.qbrix_project_tasks import replace_file_text, run_command

LOAD_COMMAND = "sfdx force:apex:execute "


class InstallRecorder(SFDXBaseTask):
    task_options = {
        "org": {
            "description": "Target org instance installing the qbrix",
            "required": False,
        },
        "context": {
            "description": "Additional context to add as part of the install record.",
            "required": False,
        },
        "explicitexit": {
            "description": "When set to true, indicates tracking is flagged as done and telemetry should be sent",
            "required": False,
        },
    }

    def _setprojectdefaults(self, instanceurl):
        subprocess.run(
            [f"sfdx config:set instanceUrl={instanceurl}"],
            shell=True,
            capture_output=True,
        )

    def _init_options(self, kwargs):
        super(SFDXBaseTask, self)._init_options(kwargs)

        try:
            self._trackingdata = None
            self.qbrixname = None
            self.context = None

            self._starttimestamp = datetime.utcnow()
            self._hooks = ExitHooks()
            self._hooks.hook()

            if not self.org_config is None and self.org_config.tracking_data is None:
                self.org_config.tracking_data = {}

            if (
                not self.org_config is None
                and self.org_config.genesis_qbrixname is None
                and not self.project_config.project__name is None
            ):
                self.org_config.genesis_qbrixname = self._get_qbrixname()
                self.logger.info(
                    f"Setting Genesis QBrix::{self.org_config.genesis_qbrixname}"
                )

            if (
                not self.org_config is None
                and self.org_config.qbrix_ambient_tracking_id is None
            ):
                self.org_config.qbrix_ambient_tracking_id = str(uuid.uuid4())
                self.logger.info(
                    f"Generated Ambient Transient Key::{self.org_config.qbrix_ambient_tracking_id}"
                )
            else:
                self.logger.info(
                    f"Existing Ambient Transient Key Found::{self.org_config.qbrix_ambient_tracking_id}"
                )

            atexit.register(self._exithandler)
        except:
            print("No Tracking")

    @property
    def trackingdata(self):
        if not self.org_config is None and self.org_config.tracking_data is None:
            self.org_config.tracking_data = {}

        if (
            not self.project_config.project__name
            in self.org_config.tracking_data.keys()
        ):
            self.org_config.tracking_data[self.project_config.project__name] = {}

        return self.org_config.tracking_data[self.project_config.project__name]

    @property
    def keychain_cls(self):
        klass = self.get_keychain_class()
        return klass or self.keychain_class

    @abstractmethod
    def get_keychain_class(self):
        return None

    @property
    def keychain_key(self):
        return self.get_keychain_key()

    @abstractmethod
    def get_keychain_key(self):
        return None

    def _load_keychain(self):
        if self.keychain is not None:
            return

        keychain_key = self.keychain_key if self.keychain_cls.encrypted else None

        if self.project_config is None:
            self.keychain = self.keychain_cls(self.universal_config, keychain_key)
        else:
            self.keychain = self.keychain_cls(self.project_config, keychain_key)
            self.project_config.keychain = self.keychain

    def _prepruntime(self):
        if (
            "org" in self.options and not self.options["org"] is None
        ) and self.keychain is None:
            self._load_keychain()
            self.logger.info("Org passed in but no keychain found in runtime")

        if "qbrixname" in self.options and not self.options["qbrixname"] is None:
            self.qbrixname = self.options["qbrixname"]

        if "explicitexit" in self.options and not self.options["explicitexit"] is None:
            self.trackingdata["explicitexit"] = bool(self.options["explicitexit"])
        else:
            # death is the exit
            self.trackingdata["explicitexit"] = False

        tmp = self.trackingdata["explicitexit"]
        self.logger.info(f"************explicitexit is {tmp}****************")

        if self.org_config.access_token is not None:
            self.accesstoken = self.org_config.access_token

        if self.org_config.instance_url is not None:
            self.instanceurl = self.org_config.instance_url

    def _run_task(self):
        self._prepruntime()
        self.run()

    def run(self):
        # if we are explicit done, we are
        if self.trackingdata["explicitexit"]:
            self.trackingdata["status"] = "Completed"
            self.trackingdata["lasterror"] = ""
            self.trackingdata["endtimestamp"] = (
                datetime.utcnow() - datetime(1970, 1, 1)
            ).total_seconds()

            if "starttimestamp" in self.trackingdata.keys():
                self.trackingdata["elapsedseconds"] = (
                    self.trackingdata["endtimestamp"]
                    - self.trackingdata["starttimestamp"]
                )

            self.__writertrackingtofile()
            self._recordtracking()

        else:
            # embeded _update_qbrix_version in the starting of installation tracking, return qbrix_commit_info so we can include these info in tracking too, in the future
            qbrix_commit_info = self._update_qbrix_version()

            self.trackingdata["genesis_qbrixname"] = self.org_config.genesis_qbrixname
            self.trackingdata[
                "ambient_tracking_id"
            ] = self.org_config.qbrix_ambient_tracking_id
            self.trackingdata["qbrixname"] = self._get_qbrixname()
            self.trackingdata["trackingid"] = str(uuid.uuid4())
            self.trackingdata["status"] = "Started"
            self.trackingdata["username"] = self.org_config.username
            self.trackingdata["os"] = sys.platform
            self.trackingdata["qbrix_system_id"] = os.environ.get(
                "QBRIX_SYSTEM_ID", "UNKNOWN"
            )
            self.trackingdata["instance"] = self.instanceurl
            self.trackingdata["hostname"] = socket.gethostname()
            self.trackingdata["starttimestamp"] = (
                datetime.utcnow() - datetime(1970, 1, 1)
            ).total_seconds()

            self.trackingdata["qbrix_sha"] = (
                qbrix_commit_info["sha"]
                if qbrix_commit_info and "sha" in qbrix_commit_info
                else ""
            )
            self.trackingdata["qbrix_image_id"] = ""

            orginzationdata = self._salesforce_query(
                "select Id,CreatedDate,OrganizationType,InstanceName from Organization"
            )
            if not orginzationdata is None:
                self.trackingdata["orgid"] = orginzationdata["result"]["records"][0][
                    "Id"
                ]
                self.trackingdata["orgcreatedate"] = orginzationdata["result"][
                    "records"
                ][0]["CreatedDate"]
                self.trackingdata["organizationtype"] = orginzationdata["result"][
                    "records"
                ][0]["OrganizationType"]
                self.trackingdata["instancename"] = orginzationdata["result"][
                    "records"
                ][0]["InstanceName"]
            else:
                self.trackingdata["orgid"] = ""
                self.trackingdata["orgcreatedate"] = ""
                self.trackingdata["organizationtype"] = ""
                self.trackingdata["instancename"] = ""

            currentuserdata = get_who_am_i(self.accesstoken)
            
            #self._salesforce_query(
            #    f"select Email from User where username='{self.org_config.username}'"
            #)
            if not currentuserdata is None:
                
                try:
                    self.trackingdata["installuseremail"] = currentuserdata["email"]
                except:
                    self.trackingdata["installuseremail"] = ""
        
            else:
                self.trackingdata["installuseremail"] = ""

            qlaborgdata = self._salesforce_query(
                "select Identifier__c,Org_Type__c from QLabs__mdt"
            )
            if not qlaborgdata is None:
                self.trackingdata["qlabsorgidentifier"] = qlaborgdata["result"][
                    "records"
                ][0]["Identifier__c"]
                self.trackingdata["qlabsorgtype"] = qlaborgdata["result"]["records"][0][
                    "Org_Type__c"
                ]
            else:
                self.trackingdata["qlabsorgidentifier"] = ""
                self.trackingdata["qlabsorgtype"] = ""

            maxapiversion = self._get_org_max_api_version()
            if not maxapiversion is None:
                self.trackingdata["maxapiversion"] = maxapiversion
            else:
                self.trackingdata["maxapiversion"] = 0.0

            self.__writertrackingtofile()

        # Fake error
        # raise Exception("fake error for testing")

    def _get_org_max_api_version(self):
        url = f"{self.instanceurl}/services/data/"
        headers = {
            "Authorization": f"Bearer {self.accesstoken}",
            "Content-Type": "application/json",
        }
        response = requests.request("GET", url, headers=headers)
        data = json.loads(response.text)

        return float(data[-1]["version"])

    def _salesforce_query(self, soql):
        if soql != "":
            dx_command = f'sfdx force:data:soql:query -q "{soql}" --json '
            subprocess.run(
                f"sfdx config:set instanceUrl={self.org_config.instance_url}",
                shell=True,
                capture_output=True,
            )
            if isinstance(self.org_config, ScratchOrgConfig):
                dx_command += " -u {username}".format(username=self.org_config.username)
            else:
                dx_command += " -u {username}".format(
                    username=self.org_config.access_token
                )

            result = subprocess.run(dx_command, shell=True, capture_output=True)
            subprocess.run(
                "sfdx config:unset instanceUrl", shell=True, capture_output=True
            )

            if result.returncode > 0:
                if result.stderr:
                    error_detail = result.stderr.decode("UTF-8")
                    self.logger.error(
                        f"Salesforce Query Error - Details: {error_detail}"
                    )
                else:
                    self.logger.error(
                        "Salesforce Query Failed, although no error detail was returned."
                    )

                return None

            json_result = json.loads(result.stdout)
            self.logger.info(json_result)
            return json_result

        return None

    def _getlastccierror(self):
        try:
            result = subprocess.run("cci error info", shell=True, capture_output=True)
            if result.stderr:
                return "Unable to access last CCI error info"
            else:
                return result.stdout.decode("UTF-8")
        except:
            return ""

    def __writertrackingtofile(self):
        if (
            self.project_config.project__name in self.trackingdata
            or self.trackingdata is None
        ):
            self.logger.info("trackingdata is null")
            return

        try:
            if os.path.isfile(
                f".qbrix/installtracking_{self.project_config.project__name}.json"
            ):
                os.remove(
                    f".qbrix/installtracking_{self.project_config.project__name}.json"
                )

            with open(
                f".qbrix/installtracking_{self.project_config.project__name}.json", "w+"
            ) as tmpFile:
                jsondata = json.dumps(self.trackingdata)
                tmpFile.write(jsondata)
                tmpFile.close()

        except:
            pass

    def _handle_returncode(self, returncode, stderr):
        if returncode:
            self.logger.error(message)
            self.trackingdata["status"] = "Failed"
            self.__writertrackingtofile()
            message = "Return code: {}".format(returncode)
            if stderr:
                message += "\nstderr: {}".format(stderr.read().decode("utf-8"))

            raise CommandException(message)

    def _recordtracking(self):
        if self.trackingdata is None:
            return

        url = "https://qbrix-core.herokuapp.com/qbrix/InstallTracking"
        payload = json.dumps(self.trackingdata)
        response = requests.request("POST", url, data=payload, verify=True)
        print(response.text)

    def _exithandler(self):
        if self.trackingdata["explicitexit"] == False:
            self.logger.info("Exit Handler Entry")
            self.trackingdata["endtimestamp"] = (
                datetime.utcnow() - datetime(1970, 1, 1)
            ).total_seconds()
            self.trackingdata["elapsedseconds"] = (
                self.trackingdata["endtimestamp"] - self.trackingdata["starttimestamp"]
            )

            if self._hooks.exit_code is not None:
                print("death by sys.exit(%d)" % self._hooks.exit_code)
                self.trackingdata["status"] = "Failed"
                self.trackingdata["lasterror"] = self._getlastccierror()
                self.__writertrackingtofile()
                self._recordtracking()

            elif self._hooks.exception is not None:
                print("death by exception: %s" % self._hooks.exception)
                self.trackingdata["status"] = "Failed"
                self.trackingdata["lasterror"] = self._getlastccierror()
                self.__writertrackingtofile()
                self._recordtracking()

            else:
                print("natural death")
                self.trackingdata["status"] = "Completed"
                self.trackingdata["lasterror"] = ""
                self.__writertrackingtofile()
                self._recordtracking()

            self.logger.info("Exit Handler Exit")

    def _get_qbrixname(self):
        #we are in a qbrix def that project name has not updated - fall back to the git remote name parsed. last slice is it
        if(self.project_config.project__name =="xDO-Template"):
            qbrixDirName,qbrixDirNameError= run_command("basename -s .git `git config --get remote.origin.url`")
            #trim carriage return - slice off last
            return qbrixDirName[:-1]
        
        return self.project_config.project__name
            
    def _update_qbrix_version(self):
        # get the running folder, we will use that to determin if this is a direct call or a source dependency call
        my_path = os.getcwd()

        # get the obj of current github repo
        # my_repo = self.project_config.get_repo_from_url(self.project_config.project__git__repo_url)

        # if we see a ".cc/projects/", we should know it's a source dependency call, and that hash like folder is the full sha of the commit, and we will use the repo's default branch as my branch
        if ".cci/projects/" in my_path:
            my_sha = my_path.split("/")[-1]
            # my_branch = my_repo.default_branch
        # other wise, it's a direct call, we don't have a sha folder ready to use, but we can get these (and even more) info from git log commands.
        else:
            try:
                my_sha, sha_error = run_command(f"git log -1 --pretty=format:'%H'")
                # my_branch, branch_error = run_command(f"git branch --show-current")
                if sha_error:  # or branch_error:
                    print(
                        f"errors occurred when reading git info\n - sha_error: {sha_error}"
                    )  # \n - branch_error: {branch_error}")
                    return
            except Exception as e:
                print(f"failed getting git info: {e}")
                return

        # now we have the sha of this commit, let's get the obj of current commit, well, we are not using this commit time info yet, it's just for future, leave them here in case I forgot how to retreive them.
        # my_commit = None
        # commit_time = None
        # try:
        #     my_commit = get_commit(my_repo, my_sha)
        #     # with commit info, we can get the commit time
        #     try:
        #         commit_time = my_commit.commit.get('author').get('date')
        #     except Exception as e:
        #         print(f"failed getting git commit time info: {e}")
        # except Exception as e:
        #     print(f"failed getting git commit info: {e}")

        # well, we will combine the branch name and sha together as version, and we wrap the info with ||| because there is some regex replace later, we use those to prevent annoying group capture errors, TO DO: there should be better way to do it.
        # we also hope to add the "commit time" into the version for easier reading and comparing the versions, but it's a bit challenge to get that info from a source dependency call, another research TO DO for later
        my_version = f"|||{my_sha}|||"

        # now, let's find the QBrix Register custom metadata
        meta_folder = "force-app/main/default/customMetadata"
        qbrix_meta_file = None
        for one_file in os.listdir(meta_folder):
            if one_file.startswith("xDO_Base_QBrix_Register."):
                qbrix_meta_file = one_file
                break

        if not qbrix_meta_file:
            return

        # and replace the version
        replace_file_text(
            f"{meta_folder}/{qbrix_meta_file}",
            r"(<field>xDO_Version__c<\/field>\s*<value xsi:type=\"xsd:string\">)[^<]*(<\/value>)",
            rf"\1{my_version}\2",
            search_regex=True,
        )
        replace_file_text(
            f"{meta_folder}/{qbrix_meta_file}", r"\|\|\|", "", search_regex=True
        )

        return {
            "sha": my_sha,
            # "branch": my_branch,
            # "commit_time": commit_time,
        }


class ExitHooks(object):
    def __init__(self):
        self.exit_code = None
        self.exception = None

    def hook(self):
        self._orig_exit = sys.exit
        self._orig_exc_handler = self.exc_handler
        sys.exit = self.exit
        sys.excepthook = self.exc_handler

    def exit(self, code=0):
        self.exit_code = code
        self._orig_exit(code)

    def exc_handler(self, exc_type, exc, *args):
        self.exception = exc
        self._orig_exc_handler(self, exc_type, exc, *args)
