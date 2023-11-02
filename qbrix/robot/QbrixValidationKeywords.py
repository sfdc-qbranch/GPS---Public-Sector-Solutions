import json
import os
import xml.etree.ElementTree as et

import pandas as pd
import pandasql as ps
import requests
from robot.api.deco import library

from qbrix.core.qbrix_robot_base import QbrixRobotTask


@library(scope='GLOBAL', auto_keywords=True, doc_format='reST')
class QbrixValidationKeywords(QbrixRobotTask):
    """Validation Keywords for Robot"""

    def __init__(self):
        super().__init__()
        self._validationresults = None
        self._mainusersessionid = self.cumulusci.sf.session_id
        self._susessionid = None

    @property
    def validationresults(self):
        if self._validationresults is None:
            self._validationresults = []

        if not "results" in self._validationresults:
            self._validationresults = {"results": []}

        return self._validationresults

    def __recordFailureResultException(self, resulttype: str = None, name: str = None, exceptionMessage: str = None, datatag=None):
        """Records a result exception"""

        if not resulttype:
            resulttype = "NONE PROVIDED"

        if not name:
            name = "NO NAME PROVIDED"

        if not exceptionMessage:
            exceptionMessage = "NO EXCEPTION MESSAGE PROVIDED"

        res = {'type': resulttype, 'name': name, 'status': "Result Exception", 'details': exceptionMessage, 'datatag': datatag}

        self.builtin.log_to_console("\n[VALIDATION] Recording Exception")
        self.builtin.log_to_console(f"\n{res}")

        self.__recordFailureResult(resulttype=resulttype, name=name, details=exceptionMessage, datatag=datatag)
        self.validationresults["results"].append(res)
        self.__writeresultstofile()

        raise Exception(exceptionMessage)

    def __recordIgnoredResult(self, resulttype: str, name: str, details: str = None, datatag=None):
        """Records an ignored validation result"""

        if details is None:
            details = ""

        if datatag is None:
            datatag = ""

        res = {'type': resulttype, 'name': name, 'status': "Ignored", 'details': details, 'datatag': datatag}

        self.builtin.log_to_console("\n[VALIDATION] Recording Ignored Validation Result")
        self.builtin.log_to_console(f"\n{res}")

        self.validationresults["results"].append(res)
        self.__writeresultstofile()

    def __recordFailureResult(self, resulttype: str, name: str, details: str = None, datatag=None):
        if details is None:
            details = ""

        if datatag is None:
            datatag = ""

        res = {'type': resulttype, 'name': name, 'status': "Failing", 'details': details, 'datatag': datatag}

        self.builtin.log_to_console("\n[VALIDATION] Recording Record Failure Result")
        self.builtin.log_to_console(f"\n{res}")

        self.validationresults["results"].append(res)
        self.__writeresultstofile()

    def __recordPassingResult(self, resulttype: str, name: str, details: str = None, datatag=None):
        if details is None:
            details = ""

        if datatag is None:
            datatag = ""

        res = {'type': resulttype, 'name': name, 'status': "Passing", 'details': details, 'datatag': datatag}

        self.builtin.log_to_console("\n[VALIDATION] Recording Record Passing Result")
        self.builtin.log_to_console(f"\n{res}")

        self.validationresults["results"].append(res)
        self.__writeresultstofile()

    def __writeresultstofile(self):
        if os.path.isfile("validationresult.json"):
            os.remove("validationresult.json")

        with open("validationresult.json", "w+", encoding="utf-8") as tmpFile:
            jsondata = json.dumps(self.validationresults)
            tmpFile.write(jsondata)
            tmpFile.close()

    def validate_minimal_rowcount(self, targetobject, count, filter=None, tooling=False, continueonfail=True, datatag=None, targetruntime=None, runasfilter=None):
        """
        Validate that the rows for the target object and filter do not go below the minimal count
        :param targetobject: The target object you want to lookup
        :param count: The expected minimal count for the object
        :param filter: (Optional) SOQL Filter for the target object (e.g. MyCustomField__c = 'Example')
        :param tooling: (Optional) Set to True if the target object requires the Tooling API
        :param continueonfail(Optional): Boolean flag to continue testing or abort
        :param datatag(Optional): Additional context added to the validation result
        :param targetruntime(Optional): Identifier if the validation only should run in SCRATCHONLY or PRODONLY orgs. None applies to both org types.
        :param runasfilter(Optional): To use a different user context, filter to query User by to locate the first user record.
        """

        resulttype = "Data"
        resultname = f'Validate Minimal Count of {targetobject} for {count} rows'

        # Check the runtime to see if this validation should be run on the org type
        if not self.__isapplicableruntime(targetruntime):
            self.__recordIgnoredResult(resulttype, resultname, f"IGNORED::targetruntime {targetruntime} does not apply to this org", datatag=datatag)
            return

        if targetobject is None:
            self.__recordFailureResultException(resulttype, resultname, "A target object must be specified", datatag=datatag)

        if count is None:
            self.__recordFailureResultException(resulttype, resultname, "'count' must be specified. This should be the minimum number of object records you expect in the org.", datatag=datatag)

        foundcnt = self.find_record_count(targetobject, filter, tooling, targetruntime, runasfilter)

        if (int(foundcnt) >= int(count)) is False:
            if continueonfail:
                self.__recordFailureResult(resulttype, resultname, f"A minimal count not met. The expected minimal number of records was: {count} and the total found was: {foundcnt}", datatag=datatag)
                return
            else:
                self.__recordFailureResultException(resulttype, resultname, f"A minimal count not met. The expected minimal number of records was: {count} and the total found was: {foundcnt}", datatag=datatag)

        self.__recordPassingResult(resulttype, resultname, f"Minimal count met. Found: {foundcnt}", datatag=datatag)

        pass

    def validate_exact_rowcount(self, targetobject, count, filter=None, tooling=False, continueonfail=True, datatag=None, targetruntime=None, runasfilter=None):
        """
        Validate that the rows for the target object and filter match the expected count
        :param targetobject: Target Object you want to lookup
        :param count: Expected count for the object.
        :param filter: (Optional) SOQL Filter for the target object (e.g. MyCustomField__c = 'Example')
        :param tooling: (Optional) Set to True if the target object requires the Tooling API
        :param continueonfail(Optional): Boolean flag to continue testing or abort
        :param datatag(Optional): Additional context added to the validation result
        :param targetruntime(Optional): Identifier if the validation only should run in SCRATCHONLY or PRODONLY orgs. None applies to both org types.
        :param runasfilter(Optional): To use a different user context, filter to query User by to locate the first user record.
        """

        resulttype = "Data"
        resultname = f'Validate Exact Count of {targetobject} for {count} rows'

        # Check the runtime to see if this validation should be run on the org type
        if (self.__isapplicableruntime(targetruntime) == False):
            self.__recordIgnoredResult(resulttype, resultname, f"IGNORED::targetruntime {targetruntime} does not apply to this org", datatag=datatag)
            return

        if targetobject is None:
            self.__recordFailureResultException(resulttype, resultname, "A target object must be specified", datatag=datatag)

        if count is None:
            self.__recordFailureResultException(resulttype, resultname, "'count' must be specified. This should be the exact number of object records you expect in the org.", datatag=datatag)

        foundcnt = self.find_record_count(targetobject, filter, tooling, targetruntime, runasfilter)

        if not foundcnt == int(count):
            if (continueonfail):
                self.__recordFailureResult(resulttype, resultname, f"An exact count not met. Expected was: {count} and found count was {foundcnt}", datatag=datatag)
                return
            else:
                self.__recordFailureResultException(resulttype, resultname, f"An exact count not met. Expected was: {count} and found count was {foundcnt}", datatag=datatag)

        self.__recordPassingResult(resulttype, resultname, f"Exact count met. Found: {foundcnt}", datatag=datatag)
        pass

    def validate_maximum_rowcount(self, targetobject, count, filter=None, tooling=False, continueonfail=True, datatag=None, targetruntime=None, runasfilter=None):
        """
        Validate that the rows for the target object and filter do not exceed the expected count
        :param targetobject: Object to lookup
        :param count: Expected maximum count
        :param filter: (Optional) SOQL Filter for the target object (e.g. MyCustomField__c = 'Example')
        :param tooling: (Optional) Set to True if the target object requires the Tooling API
        :param continueonfail(Optional): Boolean flag to continue testing or abort
        :param datatag(Optional): Additional context added to the validation result
        :param targetruntime(Optional): Identifier if the validation only should run in SCRATCHONLY or PRODONLY orgs. None applies to both org types.
        :param runasfilter(Optional): To use a different user context, filter to query User by to locate the first user record.
        """

        resulttype = "Data"
        resultname = f'Validate Maximum Count of {targetobject} for {count} rows'

        # Check the runtime to see if this validation should be run on the org type
        if (self.__isapplicableruntime(targetruntime) == False):
            self.__recordIgnoredResult(resulttype, resultname, f"IGNORED::targetruntime {targetruntime} does not apply to this org", datatag=datatag)
            return

        if targetobject is None:
            self.__recordFailureResultException(resulttype, resultname, "A target object must be specified", datatag=datatag)

        if count is None:
            self.__recordFailureResultException(resulttype, resultname, "'count' must be specified. This should be the maximum number of object records you expect in the org.", datatag=datatag)

        foundcnt = self.find_record_count(targetobject, filter, tooling, targetruntime, runasfilter)

        if foundcnt > int(count):
            if (continueonfail):
                self.__recordFailureResult(resulttype, resultname, f"A max count not met. Expected was: {count} and found count was {foundcnt}", datatag=datatag)
                return
            else:
                self.__recordFailureResultException(resulttype, resultname, f"A max count not met. Expected was: {count} and found count was {foundcnt}", datatag=datatag)

        self.__recordPassingResult(resulttype, resultname, f"Max count met. Found: {foundcnt}", datatag=datatag)
        pass

    def validate_range_rowcount(self, targetobject, lowercount, uppercount, filter=None, tooling=False, continueonfail=True, datatag=None, targetruntime=None, runasfilter=None):
        """Validate the count of the rows for the specified object and filter is >= lower value and <= upper value
        :param targetobject: Target object you are going to lookup
        :param lowercount: Minimum number for the range you want to specify. e.g. 0 if the range is 0-10
        :param uppercount: Maximum number for the range you want to specify. e.g. 10 if the range is 0-10
        :param filter: (Optional) SOQL Filter for the target object (e.g. MyCustomField__c = 'Example')
        :param tooling: (Optional) Set to True if the target object requires the Tooling API
        :param continueonfail(Optional): Boolean flag to continue testing or abort
        :param datatag(Optional): Additional context added to the validation result
        :param targetruntime(Optional): Identifier if the validation only should run in SCRATCHONLY or PRODONLY orgs. None applies to both org types.
        :param runasfilter(Optional): To use a different user context, filter to query User by to locate the first user record.
        """
        resulttype = "Data"
        resultname = f'Validate Range Count of {targetobject} between {lowercount} and {uppercount} rows'

        self.shared.log_to_file(f"Found targetruntime::{targetruntime}")
        # Check the runtime to see if this validation should be run on the org type
        if (self.__isapplicableruntime(targetruntime) == False):
            self.__recordIgnoredResult(resulttype, resultname, f"IGNORED::targetruntime {targetruntime} does not apply to this org", datatag=datatag)
            return

        if targetobject is None:
            self.__recordFailureResultException(resulttype=resulttype, name="A target object must be specified", datatag=datatag)

        if lowercount is None:
            self.__recordFailureResultException(resulttype=resulttype, name="A lower count must be specified", datatag=datatag)

        if uppercount is None:
            self.__recordFailureResultException(resulttype=resulttype, name="As upper count must be specified", datatag=datatag)

        foundcnt = self.find_record_count(targetobject, filter, tooling, targetruntime, runasfilter)

        if not foundcnt >= int(lowercount) or not foundcnt <= int(uppercount):
            message = f"A range count not met. Expected Range was between {lowercount} and {uppercount} and the found count was {foundcnt}"

            if (continueonfail):
                self.__recordFailureResult(resulttype, resultname, message, datatag=datatag)
                return
            else:
                self.__recordFailureResultException(resulttype, resultname, message, datatag=datatag)

        self.__recordPassingResult(resulttype, resultname, f"Range count met. Found: {foundcnt}", datatag=datatag)
        pass

    def find_record_count(self, targetobject, filter=None, tooling=False, targetruntime=None, runasfilter=None):
        """Locate the record count for the target object and given filter
        :param targetobject: Target Object
        :param filter: (Optional) SOQL Filter for the target object (e.g. MyCustomField__c = 'Example')
        :param tooling: (Optional) Set to True if the target object requires the Tooling API
        :param targetruntime(Optional): Identifier if the validation only should run in SCRATCHONLY or PRODONLY orgs. None applies to both org types.
        :param runasfilter(Optional): To use a different user context, filter to query User by to locate the first user record.
        :return: Returns record count, if records are found, otherwise returns None.
        """

        # Check the runtime to see if this validation should be run on the org type
        if self.__isapplicableruntime(targetruntime) is False:
            self.__recordIgnoredResult("Data", "Data Query to Find Row Count", f"IGNORED::targetruntime {targetruntime} does not apply to this org")
            return

        if targetobject is None or targetobject == "":
            raise Exception("A target object must be specified")

        # default:
        soql = f"select count(Id) DataCount from {targetobject}"

        if self.__does_not_support_count(targetobject):
            soql = f"select Id from {targetobject}"

        if filter is not None:
            soql = f"{soql} where ({filter})"

        # self.shared.log_to_file(f"Running::tooling::{tooling}::{soql}")
        self.builtin.log_to_console("\n[VALIDATION] Running SOQL Statement")
        self.builtin.log_to_console(f"\n{soql}")

        if runasfilter is not None and runasfilter != "":
            self.shared.log_to_file(f"RunAs filter::{runasfilter}")
            runasusercontext = self.__getrunasuserid(runasfilter)
            self.shared.log_to_file(f"RunAs Context::{runasusercontext}")

            if not runasusercontext is None:
                self.cumulusci.sf.session_id = runasusercontext

        if not tooling:
            results = self.cumulusci.sf.query_all(f"{soql}")
        else:
            toolingendpoint = 'query?q='
            results = self.cumulusci.sf.toolingexecute(f"{toolingendpoint}{soql.replace(' ', '+')}")

        # revert to the original token
        self.cumulusci.sf.session_id = self._mainusersessionid

        # so this gets translated to a dict with 3 keys:
        # records
        # totalSize
        # done

        # we use the totalsize instead of aggregate count
        if self.__does_not_support_count(targetobject):
            self.builtin.log_to_console(f"\n[VALIDATION] {targetobject} does not support count")
            return int(results["totalSize"])
        else:
            if results["totalSize"] == 1:
                data_count_result = int(results["records"][0]["DataCount"])
                self.builtin.log_to_console("\n[VALIDATION] Result Found")
                self.builtin.log_to_console(f"\n{data_count_result}")
                return data_count_result

        self.builtin.log_to_console("\n[VALIDATION] Returning Nothing")
        return None

    def __does_not_support_count(self, objectname: str):
        if objectname.lower() == "standardvalueset":
            return True

        return False

    def validate_entity_contains(self, targetobjectlabel: str, layer: str, findfilter: str, continueonfail=True, datatag=None, targetruntime=None):
        """Allows a validation to treat metadata for the specified object as a queryable object via SQL and DataFrames
        :param targetobjectlabel: The object that metadata will be extracted via the REST api.
        :param layer: The array of data within the metadata to search against
        :param findfilter: The filter where clause to search the dataframe against.
        :param continueonfail(Optional): Boolean flag to continue testing or abort
        :param datatag(Optional): Additional context added to the validation result
        :param targetruntime(Optional): Identifier if the validation only should run in SCRATCHONLY or PRODONLY orgs. None applies to both org types.
        """

        # self.shared.log_to_file(f"Target SObject::{targetobjectlabel}")
        # self.shared.log_to_file(f"Taget Layer::{layer}")
        # self.shared.log_to_file(f"Find Filter::{findfilter}")

        resulttype = "Metadata"
        resultname = f'Validate that {targetobjectlabel} has {layer}'

        # Check the runtime to see if this validation should be run on the org type
        if self.__isapplicableruntime(targetruntime) is False:
            self.__recordIgnoredResult(resulttype, resultname, f"IGNORED::targetruntime {targetruntime} does not apply to this org", datatag=datatag)
            return

        sobjectset = self.cumulusci.sf.describe()["sobjects"]
        # self.shared.log_to_file(f"SOjectKeys::{sobjectset}")
        for x in sobjectset:
            foundlabel = x["label"]
            foundname = x["name"]

            if foundlabel.lower() == targetobjectlabel.lower() or foundname.lower() == targetobjectlabel.lower():
                # self.shared.log_to_file(f"Found SObject::{foundlabel}")

                targetdescribe = self.cumulusci.sf.__getattr__(targetobjectlabel).describe()

                # self.shared.log_to_file(f"DescKey::{targetdescribe.keys()}")
                layerfound = False
                truelayername = None
                for key in targetdescribe.keys():
                    if key.lower() == layer.lower():
                        truelayername = key
                        layerfound = True

                if layerfound == False:
                    # self.shared.log_to_file(f"Layer Not Found::{layer}")
                    break

                if not truelayername is None:
                    fields = targetdescribe[truelayername]

                    # self.shared.log_to_file(f"DataType::{type(fields)}")
                    df = pd.DataFrame(fields)

                    # convert to string- all values
                    for col in df.columns:
                        try:
                            df[col] = df[col].apply(str)
                        except Exception as e:
                            # self.shared.log_to_file(f"Dropping Col::{col}")
                            df.drop(columns=[col])

                    # self.shared.log_to_file(f"DataFrame::{df.head()}")

                    try:
                        if not findfilter is None:
                            filter = f"SELECT count(*) datacount from df where {findfilter}"
                        else:
                            filter = "SELECT count(*) datacount"

                        dfqueryres = ps.sqldf(filter)
                        # self.shared.log_to_file(f"Query Result::{dfqueryres}")

                        if not dfqueryres is None or (len(dfqueryres) == 1 and dfqueryres[1] == 0):
                            self.__recordPassingResult(resulttype, resultname, "Metadata contains the specified", datatag=datatag)
                            return
                    except:
                        message = 'Unable to locate the metadata object to locate the layer'
                        # we hit an exception - fail closed

        # we did not locate the object to traverse the metadata
        message = 'Unable to locate the metadata object to locate the layer'

        if continueonfail:
            self.__recordFailureResult(resulttype, resultname, message, datatag=datatag)
            return
        else:
            self.__recordFailureResultException(resulttype, resultname, message, datatag=datatag)

    def validate_with_testim(self, testimscriptname: str, continueonfail=True, datatag=None, targetruntime=None, runasfilter=None):
        """NO LONGER USED"""

        raise Exception("TESTIM NO LONGER SUPPORTED. PLEASE UPDATE YOUR SCRIPT.")

    def find_xpath_in_xmlfile(self, sourcefile, xpathfilter):
        """Locates the xpath within the xml
        :param sourcefile: Source XML File
        :param xpathfilter: XPath to traverse the XML and locate nodes
        """

        if xpathfilter is None or xpathfilter == "":
            raise Exception("A xpath must be specified")

        if sourcefile is None or sourcefile == "":
            raise Exception("A source file must be specified")

        if os.path.isfile(sourcefile) is False:
            raise Exception("The source file does not exist")
        else:
            with open(sourcefile, "r", encoding="utf-8") as datafile:
                xmldata = datafile.read()
            tree = et.fromstring(bytes(xmldata, 'utf-8'))
            foundata = tree.xpath(xpathfilter)
            return foundata

        return None

    def __isapplicableruntime(self, targetruntime):
        self.shared.log_to_file(f"RunTimeCheck::{targetruntime}")

        if targetruntime is None:
            self.shared.log_to_file(f"RunTimeCheck::is::{targetruntime}::return True")

            return True

        elif targetruntime in ('SCRATCHONLY', 'PRODONLY'):
            results = self.cumulusci.sf.query_all("SELECT IsSandbox FROM Organization")
            self.shared.log_to_file(f"RunTimeCheck::results::{results}")
            totalSize = results["totalSize"]
            self.shared.log_to_file(f"RunTimeCheck::results::totalSize:{totalSize}::{type(totalSize)}")

            if totalSize == 1:
                if targetruntime == 'SCRATCHONLY' and bool(results["records"][0]["IsSandbox"]):
                    return True

                if targetruntime == 'PRODONLY' and bool(results["records"][0]["IsSandbox"]) is False:
                    return True

        # TODO: Look at supporting a customizable lookup that indicates the runtime condition of the env.
        # TBD: ? support for tooling api
        # TBD: ? as admin or run as user
        # possible flat condition: SOQL->()::TOOLING->(True)::RUNAS->()
        # else if(targetruntime.startswith('SOQL->()')):
        #    soqlquery= targetruntime.string('SOQL-->()')

        # fail closed
        return False

    def __getrunasuserid(self, userfilter: str):
        if userfilter is None:
            raise Exception("Run As user filter cannot be None")

        if userfilter == "":
            raise Exception("Run As user filter cannot be empty")

        self.shared.log_to_file(f"Running::__getrunasuserid::{userfilter}")

        results = self.cumulusci.sf.query_all(f"SELECT Username FROM User where {userfilter} LIMIT 1")
        self.shared.log_to_file(f"RunAs Filter Results::{results}")

        if results["totalSize"] == 1:
            # parse out the username
            targetusername = results["records"][0]["Username"]
            # get the target runas username

            self.shared.log_to_file(f"Running::__getrunasuserid::{targetusername}")

            url = "https://sfi-needlecast-stage.herokuapp.com/authenticate"
            payload = json.dumps({"username": f"{targetusername}"})
            self.shared.log_to_file(payload)
            headers = {'Content-Type': 'application/json'}
            response = requests.request("POST", url, headers=headers, data=payload, timeout=30)

            self.shared.log_to_file(response.text)
            jsondata = json.loads(response.text)
            return jsondata["result"]["accessToken"]

        # fail closed
        return None
