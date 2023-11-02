
import os
import re
import sys
import uuid
import subprocess
import importlib

from cumulusci.core.tasks import BaseTask

class PreCommit(BaseTask):

    def is_guid(self,possibleguid):
        try:
            uuid.UUID(str(possibleguid))
            return True
        except ValueError:
            return False
        
    def _ensure_deps(self):
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyJwt"])
    
    def _is_jwt_in_file(self,filepath):
        
        if not os.path.isfile(filepath):
            print(f"Not a File::{filepath}")
            return False
        
        scandata = ""
        with open(filepath) as file:
            scandata=file.read()
        
        
        try:
           
            if(self.dynaload == False):
                self._ensure_deps()
                self.dynaload = True
            
            jwt = importlib.import_module('jwt')
            matches = re.findall("[\w-]+\.[\w-]+\.[\w-]+",scandata)
            #print(matches)
            for match in matches:
                try:
                    res = jwt.get_unverified_header(match)
                    #print('**** Found a JWT ****')
                    return True
                except:
                    #print('Pattern found but not a JWT')
                    pass
        except Exception as e:
            return False
        
        return False
        
        
    def _run_task(self):
       
        
        self.dynaload = False
        ignoredirs=['./cci','./.cci','./config','./.config/sfdx','./.git','./.git/objects','./.qbrix','./qbrix','./.vscode','./.sfdx']
        ignorefiles=['.DS_Store','.forceignore','.lock','.prettierignore']
        rootdir = "."
        patterns={}
        filebasedscans={}

        
        #amazaon - cloud
        patterns['Amazon Marketing Services-Auth Token']=re.compile("amzn\.mws\.[0-9a-f]{8}-[0-9a-f]{4}-10-9a-f1{4}-[0-9a,]{4}-[0-9a-f]{12}")
        patterns['Amazon Web Services-Access Key ID']=re.compile("AKIA[0-9A-Z]{16}")
        #this one leades to false positives from within legit metadata
        #patterns['Amazon Web Services-Secret Key']=re.compile("[0-9a-zA-Z/+]{40}")
            
        #meta - social 
        patterns['Facebook-Access Token']=re.compile("EAACEdEose0cBA[0-9A-Za-z]+")
        patterns['Facebook-OAuth 2.0']=re.compile("[A-Za-z0-9]{125} (counting letters [2])")
        patterns['Instagram-OAuth 2.0']=re.compile("[0-9a-fA-F]{7}\.[0-9a-fA-F]{32}")
        
        #foursqare - social
        patterns['Foursquare-Secret Key']=re.compile("R_[0-9a-f]{32}")
        
        #google - cloud
        patterns['Google-API Key']=re.compile("AIza[0-9A-Za-z-_]{35}")
        patterns['Google-OAuth 2.0 Auth Code']=re.compile("4/[0-9A-Za-z\-_]+")
        patterns['Google-OAuth 2.0 Refresh Token']=re.compile("1/[0-9A-Za-z\-_]{43}|1/[0-9A-Za-z\-_]{64}")
        patterns['Google-OAuth 2.0 Access Token']=re.compile("ya29\.[0-9A-Za-z\-_]+")        
        patterns['Google Cloud Platform-OAuth 2.0']=re.compile("[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}")
        patterns['Google Cloud Platform-API Key']=re.compile("[A-Za-z0-9_]{21}--[A-Za-z0-9_]{8}")
        #patterns['Google-OAuth 2.0 Secret']=re.compile("[0-9a-zA-Z\-_]{24}")

        #git - code management
        patterns['GitHub-Personal Access Token (Classic)']=re.compile("ghp_[a-zA-Z0-9]{36}")
        patterns['GitHub-Personal Access Token (Fine-Grained)']=re.compile("github_pat_[a-zA-Z0-9]{22}_[a-zA-Z0-9]{59}")
        patterns['GitHub-OAuth 2.0 Access Token']=re.compile("gho_[a-zA-Z0-9]{36}")
        patterns['GitHub-User-to-Server Access Token']=re.compile("ghu_[a-zA-Z0-9]{36}")
        patterns['GitHub-Server-to-Server Token']=re.compile("ghs_[a-zA-Z0-9]{36}")
        patterns['GitHub-Refresh Token']=re.compile("ghr_[a-zA-Z0-9]{36}")
        
        #mailgun - messaging
        patterns['MailGun-API Key']=re.compile("key-[0-9a-zA-Z]{32}")
        patterns['MailChimp-API Key']=re.compile("[0-9a-f]{32}-us[0-9]{1,2}")
        
        #mapbox
        patterns['Mapbox-Public Key']=re.compile("([s,p]k.eyJ1Ijoi[\w\.-]+)")
        patterns['Mapbox-Secret Key']=re.compile("([s,p]k.eyJ1Ijoi[\w\.-]+)")
        
        #picatic - online ticketing
        patterns['Picatic-API Key']=re.compile("sk_live_[0-9a-z]{32}")
        
        #stripe - payments
        patterns['Stripe-Standard API Key']  =re.compile("sk_live_[0-9a-zA-Z]{24}")
        patterns['Stripe-Restricted API Key']=re.compile("rk_live_[0-9a-zA-Z]{24}")
        
        #square - payments
        patterns['Square-Access Token']=re.compile("sqOatp-[0-9A-Za-z\-_]{22}")
        patterns['Square-OAuth Secret']=re.compile("q0csp-[ 0-9A-Za-z\-_]{43}")
        
        #paypal - payments
        patterns['Paypal / Braintree-Access Token']=re.compile("access_token\,production\$[0-9a-z]{161[0-9a,]{32}")
        
        #twilio - messaging
        # a lot of false positives in static resources 
        #patterns['Twilio-API key']=re.compile("55[0-9a-fA-F]{32}")
        
        #slack - messaging
        patterns['Slack-OAuth v2 Bot Access Token']=re.compile("xoxb-[0-9]{11}-[0-9]{11}-[0-9a-zA-Z]{24}")
        patterns['Slack-OAuth v2 User Access Token']=re.compile("xoxp-[0-9]{11}-[0-9]{11}-[0-9a-zA-Z]{24}")
        patterns['Slack-OAuth v2 Configuration Token']=re.compile("xoxe.xoxp-1-[0-9a-zA-Z]{166}")
        patterns['Slack-OAuth v2 Refresh Token']=re.compile("xoxe-1-[0-9a-zA-Z]{147}")
        patterns['Slack-Webhook']=re.compile("T[a-zA-Z0-9_]{8}/B[a-zA-Z0-9_]{8}/[a-zA-Z0-9_]{24}")
        
        #twitter or X - social
        patterns['Twitter-Access Token']=re.compile("[1-9][ 0-9]+-[0-9a-zA-Z]{40}")
        
        #heroku - cloud
        #if you authenticate heroku and run heroku auth:token - the value is a guid with no prefix. This will result in false positives
        #patterns['Heroku-API Key']=re.compile("[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}")
        patterns['Heroku-OAuth 2.0']=re.compile("[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}")
        
        #custom
        patterns['QBranch NextGen Legacy Generic Token']=re.compile(".\?token=.{42}")
        

        #JWT are different and really need a two part test. string identify and string decode to determine if it really is a value jwt string
        filebasedscans['QBranch NextGen - Embedded JWT Token']= self._is_jwt_in_file
        

        results=[]
        matches=[]
        for subdir, dirs, files in os.walk(rootdir):
            for file in files:
                continuepprocessing=True
                for ign in ignoredirs:
                    if ign in subdir:
                        continuepprocessing=False

                for ign in ignorefiles:
                    if ign in file:
                        continuepprocessing=False

                if(continuepprocessing):
                    filepath = subdir + os.sep + file
                    #print(subdir)
                    try:
                    
                        #full file scan
                        for patternid,filevalidationfunction in filebasedscans.items():
                            if not filevalidationfunction is None:
                                fileres = filevalidationfunction(filepath)
                                if(fileres):
                                    #print(f'pattern::{patternid}::{filepath}')
                                    results.append(f'pattern::{patternid}::{filepath}')
                        
                        #file line processing
                        for i, line in enumerate(open(filepath)):
                            for patternid,pattern in patterns.items():
                                #print(f'file::{filepath}')
                                for match in re.finditer(pattern, line):
                                    noadd=False
                                    #****************************************************
                                    #do not leave the print statements on. debugging only
                                    #**************************************************** 
                                    
                                    #a lot of patterns can crossover into url paths
                                    #check the match NOT the line. prune / string - no token will have it. if so, find me.
                                    #GUIDS can be false positives. e.g. heroku api key
                                    #print(type(match))
                                    foundmatch =f"{match}"
                                    if(not foundmatch.__contains__('/')):
                                    
                                        #****************************************************
                                        #do not leave the print statements on. debugging only
                                        #**************************************************** 
                                        results.append(f'pattern::{patternid}::{filepath}::match::{match}')
                                        print(f'pattern::{patternid}::{filepath}::match::{match}')
                                        #results.append(f'pattern::{patternid}::{filepath}')
                        
                    except UnicodeDecodeError:
                        pass

        if(len(results)>0):
            self.logger.error(f'*********************************************************************************')
            self.logger.error(f'*****   COMMIT BLOCKED Possible Restricted Key(s) found in these files:  ********')
            self.logger.error(f'*********************************************************************************')
            
            for file in results:
                self.logger.error(file)
            sys.exit(os.EX_DATAERR)