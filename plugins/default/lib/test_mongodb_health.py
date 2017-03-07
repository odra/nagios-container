#!/usr/bin/env python
import unittest

from mongodb_health import analize, parse_mongo_result, report, REPLSET_STATUS
import nagios


class TestAnalize(unittest.TestCase):

    def runTest(self):
        self.assertEqual(analize(REPLSET_STATUS.STARTUP), nagios.WARN)
        self.assertEqual(analize(REPLSET_STATUS.PRIMARY), nagios.OK)
        self.assertEqual(analize(REPLSET_STATUS.SECONDARY), nagios.OK)
        self.assertEqual(analize(REPLSET_STATUS.RECOVERING), nagios.CRIT)
        self.assertEqual(analize(REPLSET_STATUS.FATAL), nagios.CRIT)
        self.assertEqual(analize(REPLSET_STATUS.STARTUP2), nagios.CRIT)
        self.assertEqual(analize(REPLSET_STATUS.UNKNOWN), nagios.CRIT)
        self.assertEqual(analize(REPLSET_STATUS.ARBITER), nagios.WARN)
        self.assertEqual(analize(REPLSET_STATUS.DOWN), nagios.CRIT)
        self.assertEqual(analize(REPLSET_STATUS.ROLLBACK), nagios.CRIT)
        self.assertEqual(analize(REPLSET_STATUS.REMOVED), nagios.CRIT)
        self.assertEqual(analize(None), nagios.UNKNOWN)


class TestParseMongoResult(unittest.TestCase):

    def runTest(self):
        self.assertEqual(parse_mongo_result(
            '{"set":"rs0","date":"2016-08-04T20:24:47.000Z","myState":1,"members":[{"_id":1,"name":'
            '"mongodb-1:27017","health":1,"state":1,"stateStr":"PRIMARY","uptime":17147,"optime":{"'
            't":1470342112,"i":1},"optimeDate":"2016-08-04T20:21:52.000Z","self":true}],"ok":1}'
        ), REPLSET_STATUS.PRIMARY)
        self.assertEqual(parse_mongo_result(
            '{"set":"rs0","date":"2016-08-04T20:28:26.000Z","myState":2,"syncingTo":"10.1.1.5:27017'
            '","members":[{"_id":1,"name":"10.1.1.5:27017","health":1,"state":1,"stateStr":"PRIMARY'
            '","uptime":93150,"optime":{"t":1470269408,"i":2},"optimeDate":"2016-08-04T00:10:08.000'
            'Z","lastHeartbeat":"2016-08-04T20:28:26.000Z","lastHeartbeatRecv":"2016-08-04T20:28:25'
            '.000Z","pingMs":0},{"_id":2,"name":"10.1.5.7:27017","health":1,"state":2,"stateStr":"S'
            'ECONDARY","uptime":93150,"optime":{"t":1470269408,"i":2},"optimeDate":"2016-08-04T00:1'
            '0:08.000Z","lastHeartbeat":"2016-08-04T20:28:25.000Z","lastHeartbeatRecv":"2016-08-04T'
            '20:28:25.000Z","pingMs":1,"syncingTo":"10.1.1.5:27017"},{"_id":3,"name":"10.1.2.3:2701'
            '7","health":1,"state":2,"stateStr":"SECONDARY","uptime":93162,"optime":{"t":1470269408'
            ',"i":2},"optimeDate":"2016-08-04T00:10:08.000Z","self":true}],"ok":1}'
        ), REPLSET_STATUS.SECONDARY)
        self.assertEqual(parse_mongo_result(
            '{"state":10,"stateStr":"REMOVED","uptime":80472,"optime":{"ts":{"t":1474915670,"i":2},'
            '"t":{"floatApprox":4}},"optimeDate":"2016-09-26T18:47:50.000Z","ok":0,"errmsg":"Our re'
            'plica set config is invalid or we are not a member of it","code":93}'
        ), REPLSET_STATUS.REMOVED)
        self.assertEqual(parse_mongo_result("\n"), None)
        self.assertEqual(parse_mongo_result(""), None)


class TestReport(unittest.TestCase):

    def runTest(self):
        self.assertEqual(report(
            pods=("mongodb-1-1-s1ngl",),
            rs_statuses=(REPLSET_STATUS.PRIMARY,),
            nag_statuses=(nagios.OK,),
        ), nagios.OK)
        self.assertEqual(report(
            pods=("mongodb-1-1-9hj1x", "mongodb-2-1-xu70c", "mongodb-3-1-wdq55"),
            rs_statuses=(REPLSET_STATUS.PRIMARY, REPLSET_STATUS.SECONDARY, REPLSET_STATUS.SECONDARY),
            nag_statuses=(nagios.OK, nagios.OK, nagios.OK)
        ), nagios.OK)
        self.assertEqual(report(
            pods=("mongodb-1-1-9hj1x", "mongodb-2-1-xu70c", "mongodb-3-1-wdq55"),
            rs_statuses=(REPLSET_STATUS.PRIMARY, REPLSET_STATUS.SECONDARY, REPLSET_STATUS.PRIMARY),
            nag_statuses=(nagios.OK, nagios.OK, nagios.OK)
        ), nagios.CRIT)
        self.assertEqual(report(
            pods=("mongodb-1-1-9hj1x", "mongodb-2-1-xu70c"),
            rs_statuses=(REPLSET_STATUS.PRIMARY, REPLSET_STATUS.SECONDARY),
            nag_statuses=(nagios.OK, nagios.OK)
        ), nagios.WARN)
        self.assertEqual(report(
            pods=("mongodb-1-1-9hj1x", "mongodb-2-1-xu70c", "mongodb-3-1-wdq55"),
            rs_statuses=(REPLSET_STATUS.PRIMARY, REPLSET_STATUS.SECONDARY, REPLSET_STATUS.SECONDARY),
            nag_statuses=(nagios.WARN, nagios.OK, nagios.OK)
        ), nagios.WARN)
        self.assertEqual(report(
            pods=("mongodb-1-1-9hj1x", "mongodb-2-1-xu70c", "mongodb-3-1-wdq55"),
            rs_statuses=(REPLSET_STATUS.PRIMARY, REPLSET_STATUS.ARBITER, REPLSET_STATUS.SECONDARY),
            nag_statuses=(nagios.OK, nagios.WARN, nagios.OK)
        ), nagios.WARN)
        self.assertEqual(report(
            pods=("mongodb-1-1-9hj1x", "mongodb-2-1-xu70c"),
            rs_statuses=(REPLSET_STATUS.PRIMARY,),
            nag_statuses=(nagios.OK, nagios.UNKNOWN)
        ), nagios.UNKNOWN)
        self.assertEqual(report(
            pods=(),
            rs_statuses=(),
            nag_statuses=()
        ), nagios.UNKNOWN)


if __name__ == "__main__":
    unittest.main()
