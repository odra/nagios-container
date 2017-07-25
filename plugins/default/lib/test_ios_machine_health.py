import unittest
import nagios

from ios_machine_health import report, parse_response, check


class TestCheck(unittest.TestCase):

    def runTest(self):
        self.assertRaises(ValueError, check, "", "", "", "")


class TestReport(unittest.TestCase):

    def runTest(self):
        self.assertEqual(report(
            results=[
                ["macOS (machine1)", nagios.OK],
                ["macOS (machine2)", nagios.OK]
            ],
            errors=(),
            ), nagios.OK)
        self.assertEqual(report(
            results=[
                ["macOS (machine1)", nagios.OK],
                ["macOS (machine2)", nagios.CRIT]
            ],
            errors=()
            ), nagios.CRIT)
        self.assertEqual(report(
            results=[
                ["macOS (machine1)", nagios.OK],
                ["macOS (machine2)", nagios.CRIT],
                ["macOS (machine3)", nagios.UNKNOWN]
            ],
            errors=()
            ), nagios.UNKNOWN)
        self.assertEqual(report(
            results=[],
            errors=["machine1", nagios.UNKNOWN]
            ), nagios.UNKNOWN)


class TestParseResponse(unittest.TestCase):

    def runTest(self):
        self.assertEqual(parse_response(
                    response={"displayName": "Nodes", "busyExecutors": 0, "computer": [
                            {
                                "displayName": "master", "offline": False
                            },
                            {
                                "displayName": "macOS machine1", "offline": False
                            }
                        ]
                    }),
            ([('macOS machine1', nagios.OK)], [])
            )
        self.assertEqual(parse_response(
                    response={"displayName": "Nodes", "busyExecutors": 0, "computer": [
                            {
                                "displayName": "master", "offline": True
                            },
                            {
                                "displayName": "macOS machine1", "offline": True
                            }
                        ]
                    }),
            ([("macOS machine1", nagios.CRIT)], [])
            )
        self.assertRaises(KeyError, parse_response,
                          response={"msg": "some other response from the server"})


if __name__ == "__main__":
    unittest.main()
