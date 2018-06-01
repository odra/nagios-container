#!/usr/bin/env python
import unittest

from check_fhmessaging_collections import parse_mongo_result, topic_existance, report, topics
import nagios


class TestParseMongoResult(unittest.TestCase):
    def runTest(self):
        collection_data = ["agendaJobs", "apicalled_20180514", "apicalled_20180515", "apicalled_20180516",
                           "apicalled_20180517", "apicalled_20180518", "apicalled_20180519",
                           "apicalled_20180520", "apicalled_20180521", "apicalled_20180522",
                           "apicalled_20180523", "apicalled_20180524", "appactivedevice",
                           "apprequestsdest", "apptransactionsdest", "domainactivedevice",
                           "domainrequestsdest", "domaintransactionsdest", "fhact_20200101",
                           "from_date", "mbaas_appactivedevice", "mbaas_apprequestsdest",
                           "mbaas_apptransactionsdest", "mbaas_domainactivedevice",
                           "mbaas_domainrequestsdest", "mbaas_domaintransactionsdest",
                           "metrics_audit_log", "useractivate_20180514", "userlogin_20180514",
                           "userlogin_20180516", "userlogin_20180524", "userlogin_20200101"]

        collection_json = '["agendaJobs","apicalled_20180514","apicalled_20180515",' \
                          '"apicalled_20180516","apicalled_20180517","apicalled_20180518","apicalled_20180519",' \
                          '"apicalled_20180520","apicalled_20180521","apicalled_20180522","apicalled_20180523",' \
                          '"apicalled_20180524","appactivedevice","apprequestsdest","apptransactionsdest",' \
                          '"domainactivedevice","domainrequestsdest","domaintransactionsdest","fhact_20200101",' \
                          '"from_date","mbaas_appactivedevice","mbaas_apprequestsdest","mbaas_apptransactionsdest",' \
                          '"mbaas_domainactivedevice","mbaas_domainrequestsdest","mbaas_domaintransactionsdest",' \
                          '"metrics_audit_log","useractivate_20180514","userlogin_20180514","userlogin_20180516",' \
                          '"userlogin_20180524","userlogin_20200101"]'

        self.assertEqual(parse_mongo_result(collection_json), collection_data)
        self.assertEqual(parse_mongo_result("\n"), None)
        self.assertEqual(parse_mongo_result(""), None)


class TestTopicExistance(unittest.TestCase):
    def runTest(self):
        result = {
            "apicalled": False,
            "appbuild": False,
            "appcreate": False,
            "appinit": False,
            "fhact": False,
            "useractivate": False,
            "userlogin": False
        }

        collection_data = ["agendaJobs", "apicalled_20180514", "apicalled_20180515", "apicalled_20180516",
                           "apicalled_20180517", "apicalled_20180518", "apicalled_20180519",
                           "apicalled_20180520", "apicalled_20180521", "apicalled_20180522",
                           "apicalled_20180523", "apicalled_20180524", "appactivedevice",
                           "apprequestsdest", "apptransactionsdest", "domainactivedevice",
                           "domainrequestsdest", "domaintransactionsdest", "fhact_20200101",
                           "from_date", "mbaas_appactivedevice", "mbaas_apprequestsdest",
                           "mbaas_apptransactionsdest", "mbaas_domainactivedevice",
                           "mbaas_domainrequestsdest", "mbaas_domaintransactionsdest",
                           "metrics_audit_log", "useractivate_20180514", "userlogin_20180514",
                           "userlogin_20180516", "userlogin_20180524", "userlogin_20200101"]
        t_results = topic_existance(topics, collection_data)
        self.assertEqual(t_results, result)


class TestReport(unittest.TestCase):
    def runTest(self):
        result_ok = {
            "apicalled": True,
            "appbuild": True,
            "appcreate": True,
            "appinit": True,
            "fhact": False,
            "useractivate": True,
            "userlogin": True
        }
        x = report([""], "rhmap-core", result_ok)
        self.assertEqual(x, nagios.OK)

        result_crit = {
            "apicalled": False,
            "appbuild": False,
            "appcreate": False,
            "appinit": False,
            "fhact": False,
            "useractivate": False,
            "userlogin": False
        }

        x = report([""], "rhmap-core", result_crit)
        self.assertEqual(x, nagios.CRIT)


if __name__ == "__main__":
    unittest.main()
