'''
Viva La GLOOOP
Get Latest Org Out Of Pool
This utility allows a QBrix Developer to tap into the org pool
'''

import json
import os
import subprocess
import requests
import json
import socket
from abc import abstractmethod

from cumulusci.core.exceptions import CommandException
from cumulusci.core.keychain import BaseProjectKeychain
from cumulusci.tasks.command import Command


class Glooop(Command):
    keychain_class = BaseProjectKeychain
    
    task_docs = """
    Used to pool an org from a pre-built org pool in QLabs. This requires you have access to QLabs and already have established an existing SFDX Session.
    """

    task_options = {
        "qlabs_username": {
            "description": "Username or Alias of the SFDX Sesssion to QLabs",
            "required": True
        },
        "org_pool_name": {
            "description": "QLabs Org Pool name to tap into for an existing org to checkout.",
            "required": True
        },
        "cci_target_org": {
            "description": "Alias to import under for the cci org list",
            "required": True
        }

    }

    def _init_options(self, kwargs):
        super(Command, self)._init_options(kwargs)
        self.qlabsAccessToken=None
                
    def _prepruntime(self):

        if "qlabs_username" not in self.options or not self.options["qlabs_username"]:
            raise ValueError('Missing QLabs sfdx username.')
        else:
            self.qlabs_username = self.options["qlabs_username"]

        if "org_pool_name" not in self.options or not self.options["org_pool_name"]:
            raise ValueError('Missing Org Pool Name.')
        else:
            self.org_pool_name = self.options["org_pool_name"]
            
        if "cci_target_org" not in self.options or not self.options["cci_target_org"]:
            raise ValueError('Missing Target CCI Org to input into.')
        else:
            self.cci_target_org = self.options["cci_target_org"]
            
    def run(self):
        self._getQlabsAccessToken()
        exchangePayload = self._getExchangeId()
        if(not exchangePayload is None):
            self.logger.info('Exchange Id located')
            self._exchangeId(exchangePayload)
        else:
            self.logger.error('No Exchange Id found.')
            
    
    def _getQlabsAccessToken(self):
        
        if(not self.qlabsAccessToken is None):
            return self.qlabsAccessToken
        
        if(self.qlabs_username.strip()!=''):
            result = subprocess.run([f'sf org open -o {self.qlabs_username} -r --json'], shell=True, capture_output=True)
            if(not result is None and result!=''):
                qlabsJson = json.loads(result.stdout)
                urlData = qlabsJson["result"]["url"]
                qlabsAccessToken= urlData.replace('https://qlabs-org.my.salesforce.com/secur/frontdoor.jsp?sid=','')
                self.qlabsAccessToken=qlabsAccessToken.strip()
                return
        
        self.logger.error('Unable to get access token to QLabs')
    
    def _getExchangeId(self):

        try:
            url = "https://qlabs-org.my.salesforce.com/services/apexrest/NGQBrixGlooopService"
            payload = json.dumps({
            "poolname": f"{self.org_pool_name}",
            "context": f"{socket.gethostname()}"
            })
            
            headers = {
            'Authorization': f'Bearer {self._getQlabsAccessToken()}',
            'Content-Type': 'application/json'
            }
            response=requests.request("POST", url, headers=headers, data=payload)
            data = json.loads(response.text)
            return data
        except Exception as ex:
            self.logger.error(f"Unable to contact GLOOOP::{ex}")

        #fail closed sine the object or access to the object is not present
        return None
        
    def _exchangeId(self,exchangePayload):
        #self.logger.info(exchangePayload)
        try:
            url = "https://qlabs-org.my.salesforce.com/services/apexrest/NGQBrixGlooopService"
            payload = json.dumps(exchangePayload)
            headers = {
            'Authorization': f'Bearer {self._getQlabsAccessToken()}',
            'Content-Type': 'application/json'
            }
            response=requests.request("POST", url, headers=headers, data=payload)
            glooopResult = json.loads(response.text)
            glooopAccessToken =glooopResult["accessToken"]
            glooopInstanceUrl =glooopResult["instanceUrl"]
            glooopUsername =glooopResult["pooledUserName"]

            importSFDXCmd =f"export SFDX_ACCESS_TOKEN='{glooopAccessToken}' && sf org login access-token --instance-url {glooopInstanceUrl} -a {glooopUsername} --no-prompt --json"
            importCCICmd = f"cci org import {glooopUsername} {self.cci_target_org}"
            subprocess.run([importSFDXCmd], shell=True, capture_output=True)
            
            p= subprocess.Popen(importCCICmd,stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=1,universal_newlines=True,shell=True)
            (out, err)=p.communicate()
            self.logger.info(out)
            self.logger.error(err)
          
        except:
            self.logger.error("Unable to contact GLOOOP with Exchange Id")
        
    def _run_task(self):
        self._prepruntime()
        self.run()
        
        