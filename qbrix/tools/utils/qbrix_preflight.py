import os
import subprocess
import json 
import re
from abc import ABC

from cumulusci.core.config import ScratchOrgConfig, TaskConfig
from cumulusci.core.keychain import BaseProjectKeychain
from cumulusci.core.tasks import BaseTask
from cumulusci.tasks.salesforce import CreateCommunity

from qbrix.salesforce.qbrix_salesforce_tasks import QbrixInstallCheck
from qbrix.tools.shared.qbrix_cci_tasks import run_cci_flow, run_cci_task
from qbrix.tools.utils.qbrix_orgconfig_hydrate import NGOrgConfig
from qbrix.salesforce.qbrix_salesforce_experience_cloud import pre_deploy_all_project_communities


class RunPreflight(BaseTask, ABC):

    """Runs initial setup tasks before any other deployment happens"""


    task_docs = """
    Q Brix Preflight runs multiple tasks and flows against your target org to prepare it for the main deployment. By default it deploys settings and ensures that the Q Brix Registration package is installed.
    """

    task_options = {
        "include_base_config": {
            "description": "Set to True if you want the base config and data deployed into the target org. Defaults to False",
            "required": False
        },
        "base_config_only_scratch": {
            "description": "Set to True if you want the base config and data deployed into only scratch orgs. Defaults to False",
            "required": False
        },
        "only_base_config": {
            "description": "Set to True if you only want to deploy base config and NOT base data. Defaults to False",
            "required": False
        },
        "skip_settings_deployment": {
            "description": "Set to True if you don't want preflight to deploy settings. Defaults to False",
            "required": False
        },
        "skip_hydrate": {
            "description": "Set to True if you don't want preflight to hydrate options for where clauses. Defaults to False",
            "required": False
        },
        "org": {
            "description": "The alias for the connected target org within the CumulusCI Project. Ensure that either this is provided or the access token.",
            "required": False
        },
        "pre_deploy_communities": {
            "description": "Set to True to pre-deploy all communities within the project, Default is False",
            "required": False
        }
    }

    salesforce_task = True
    keychain_class = BaseProjectKeychain

    def _init_options(self, kwargs):
        super(RunPreflight, self)._init_options(kwargs)
        # Initiate Shared Variables
        self.scratch_org_mode = bool(isinstance(self.org_config, ScratchOrgConfig))

        # Initiate Options
        self.include_base_config = self.options["include_base_config"] if "include_base_config" in self.options else False
        self.base_config_only_scratch = self.options["base_config_only_scratch"] if "base_config_only_scratch" in self.options else False
        self.only_base_config = self.options["only_base_config"] if "only_base_config" in self.options else False
        self.skip_settings_deployment = self.options["skip_settings_deployment"] if "skip_settings_deployment" in self.options else False
        self.skip_hydrate = self.options["skip_hydrate"] if "skip_hydrate" in self.options else False
        self.pre_deploy_communities = self.options["pre_deploy_communities"] if "pre_deploy_communities" in self.options else False

    def _deploy_settings(self):

        self.logger.info("\nPREFLIGHT TASK: Pre-Deploy Org Settings to Org with alias %s", self.org_config.name)

        if not self.skip_settings_deployment:

            # Get Settings Path
            settings_path = os.path.join(os.getcwd(), 'force-app', 'main', 'default', 'settings')

            if os.path.exists(settings_path):
                run_cci_task("deploy", self.org_config.name, path=settings_path)
            else:
                self.logger.info(" -> Settings not found at %s, skipping settings deployment.", settings_path)
        else:
            self.logger.info(" -> Option to Skip Enabled - Skipping Settings Deployment.")

    def deploy_qbrix_register(self):


        # Check if Q Brix Registration is already installed
        self.logger.info(f"\nPREFLIGHT TASK: Check Q Brix Register is deployed in org with alias {self.org_config.name}")

        if not QbrixInstallCheck("QBrix-1-xDO-Tool-QBrixRegister", self.org_config.name):
            self.logger.info(f" -> Deploying Q Brix Registration to Org {self.org_config.name}")
            checkreg_deploy_result = run_cci_task("base:check_register", self.org_config.name)
            if checkreg_deploy_result:
                self.logger.info(" -> Q Brix Register Check Complete!")
            else:
                self.logger.info(" -> Q Brix Register Check Failed. Check errors and warnings (if any) mentioned above.")

    def deploy_base_config_and_data(self):
        self.logger.info(f"\nPREFLIGHT TASK: Deploy Base Config and Base Data to org with alias {self.org_config.name}")

        if not QbrixInstallCheck("QBrix-0-xDO-BaseConfig", self.org_config.name):
            self.logger.info(" -> Deploying Q Brix Base Config")
            deploy_result = run_cci_flow("base:deploy_qbrix", self.org_config.name)

            if deploy_result:
                self.logger.info(" -> Q Brix Base Config Deployment Complete!")
            else:
                self.logger.error(" -> Q Brix Base Config Deployment Failed. Check errors and warnings (if any) mentioned above.")
        else:
            self.logger.info(" -> Q Brix Base Config Deployed")

        if not self.only_base_config:
            if not QbrixInstallCheck("QBrix-0-xDO-BaseData", self.org_config.name):
                self.logger.info(" -> Installing Q Brix Base Data")
                deploy_result = run_cci_flow("base:deploy_qbrix_base_data", self.org_config.name)

                if deploy_result:
                    self.logger.info(" -> Q Brix Base Data Deployment Complete!")
                else:
                    self.logger.error(" ->Q Brix Base Data Deployment Failed. Check errors and warnings (if any) mentioned above.")
            else:
                self.logger.info(" -> Q Brix Base Data Deployed")

    def scratch_org_tasks(self):

        """Add Tasks here to be executed when the target org is a Scratch Org or Sandbox"""

        if self.include_base_config:
            self.deploy_base_config_and_data()

    def production_org_tasks(self):

        """Add Tasks here to be executed when the target org is a Production Org"""

        if self.include_base_config and self.base_config_only_scratch is False:
            self.deploy_base_config_and_data()

    def shared_tasks(self):

        """Add Tasks here to be executed for all deployments"""

        # Deploy Settings
        self._deploy_settings()

        # Check and deploy Q Brix Register
        self.deploy_qbrix_register()

        # Check for Experience Cloud sites
        if self.pre_deploy_communities:
            if os.path.exists(os.path.join("force-app", "main", "default", "experiences")) or os.path.exists(os.path.join("force-app", "main", "default", "digitalExperiences", "site")):
                pre_deploy_all_project_communities(self.org_config.name)
            else:
                self.logger.info("No Experiences to pre-deploy.")

    def _run_task(self):
        self.logger.info("\nPREFLIGHT: Starting Q Brix Preflight Check")

        # Initial Q Brix Tasks
        if not self.skip_hydrate:
            self.logger.info("\nPREFLIGHT TASK: Running Org Config Hydrate")
            hydrate = NGOrgConfig(
                org_config=self.org_config,
                project_config=self.project_config,
                task_config=TaskConfig({"class_path": "qbrix.tools.utils.qbrix_orgconfig_hydrate.NGOrgConfig"})
            )
            hydrate._run_task()
            self.logger.info(" -> Org Config Hydrated!")
            
        #check for a defined parameters set
        if(os.path.isfile(os.path.join("qbrix_local","inputs","required.json"))):
            self._validate_required_json()

        self.logger.info("\nPREFLIGHT: Running Shared Tasks, which apply to all Orgs")
        self.shared_tasks()

        # Other Tasks
        if self.scratch_org_mode:
            self.logger.info("\nPREFLIGHT: Running Scratch Org and Sandbox Related Tasks")
            self.scratch_org_tasks()
        else:
            self.logger.info("\nPREFLIGHT: Running Production Org Related Tasks")
            self.production_org_tasks()

        self.logger.info("\nPREFLIGHT: Preflight Complete")
    
    def _validate_required_json(self):
        negative_results=[]
        inputsfile =os.path.join("qbrix_local","inputs","required.json")
        suppliedinputsfile =os.path.join(".qbrix","inputs","supplied_inputs.json")
        
        #termwidth >0 - we are running in a non-headless world
        termwidth = self._get_terminal_width()
        
        #check for headless run with zero parameters supplied and parameters defined
        if(os.path.isfile(inputsfile)):
            
            inputcontent = open(inputsfile, "r")
            inputjson=inputcontent.read()
            inputsdict = json.loads(inputjson)
            suppliedinputjson={}
            suppliedinputsdict={}
            
            if(not "parameters" in inputsdict): return

            if(os.path.isfile(suppliedinputsfile)):
                suppliedinputcontent = open(suppliedinputsfile, "r")
                suppliedinputjson=suppliedinputcontent.read()
                
                try:
                    suppliedinputsdict = json.loads(suppliedinputjson)
                except Exception as e:
                    #bad file = default to empty dict
                    suppliedinputsdict={}
                    
            
            
            for reqin in inputsdict["parameters"]:
                #ignore any empty required names. Fail on them.
                if("name" in reqin and len(reqin["name"].strip())>0):
                    trgname=reqin["name"]
                    trgvalue=None
                    friendlyname=trgname
                    
                    if("friendly_name" in reqin):
                        friendlyname = reqin["friendly_name"]
                        
                    if(trgname in suppliedinputsdict):
                        trgvalue =suppliedinputsdict[trgname].strip()
                        
                    #self.logger.info(f'Current parameter::{trgname}::Current Value::{trgvalue}')
                    
                    #nothing supplied via inputs - go for defaults - if defined
                    if("default" in reqin and (trgvalue is None or len(trgvalue)==0)):
                        trgvalue = self._get_default(reqin["default"])        
                        
                    #if we are in a non-headless and no value and no default preset - prompt them
                    if(termwidth > 0 and  (trgvalue is None or len(trgvalue)==0)):
                        trgvalue=input(f"Please enter a value for::{friendlyname}->")
                        trgvalue=trgvalue.strip() #kill leading and trailing whitespaces
                    
                    #check for regex irrespective if supplied or defaulted
                    if("regex" in reqin and len(reqin["regex"].strip())>0):
                        if(self._value_is_regex_match(trgvalue,reqin["regex"].strip())==False):
                            msg = f"Required Parameter::{friendlyname} does not match the required regex."
                            negative_results.append(msg)
                    
                    #we have gone through the Gauntlet
                    if(trgvalue is None or len(trgvalue)==0):
                        msg=(f"Required Parameter::{friendlyname} is missing.")
                        negative_results.append(msg)
                    else: 
                        #store it to the cache
                        self.org_config.qbrix_cache_set(trgname,trgvalue)
                    
                               
        if(len(negative_results)>0):
            self.logger.error("****** MISSING REQUIRED PARAMETERS ******")
            for parmmsg in negative_results:
                self.logger.error(parmmsg)
            raise Exception("****** MISSING REQUIRED PARAMETERS ******")
        
    
    def _get_default(self,exp=str):
        #strip whitespace 
        if(exp is None or len(exp.strip())==0):
            return None
        
        if(exp.startswith("${{") and exp.endswith("}}")):
            try:
                parsedexp = exp[3:][:-2].strip()

                #exit if inline import detected
                if "__import__" in parsedexp:
                    return None

                compliledcode = compile(parsedexp, "<string>", "eval")
                #no builtins = no __import__ # DO NOT allow globals
                #restrict scope to expression - no builtins and only locals self
                res = eval(compliledcode,{},{"self":self})
                return str(res)
                
            except Exception as inst:
                self.logger.error(f"Unable to evaluate dynamic express::{inst}")
                #fail closed
                return None
        else:
            return exp
            
    def _get_terminal_width(self):
        # if we are running in a headless runner- tty will not be there.
        try:
            return int(subprocess.check_output(['stty', 'size']).split()[1])
        except Exception as e:
            pass
        
        return 0
    
    def _value_is_regex_match(self,value=str,regex=str):
        
        if(value is None or regex is None):
            return True
        
        if(not regex is None and len(regex)>0):
            compiledregex = re.compile(regex)
            return len(re.findall(compiledregex, value))>0
        
        #fall open
        return True
            
