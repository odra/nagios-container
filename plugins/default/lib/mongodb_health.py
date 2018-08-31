#!/usr/bin/env python
import argparse
import json
import sys
import traceback
from collections import Counter

import nagios
import openshift


def enum(*sequential, **named):
    enums = dict(zip(sequential, range(len(sequential))), **named)
    reverse = dict((value, key) for key, value in enums.iteritems())
    enums['reverse_mapping'] = reverse
    return type('Enum', (), enums)


# MongoDB replset status codes:
REPLSET_STATUS = enum(
    STARTUP=0,
    PRIMARY=1,
    SECONDARY=2,
    RECOVERING=3,
    FATAL=4,
    STARTUP2=5,
    UNKNOWN=6,
    ARBITER=7,
    DOWN=8,
    ROLLBACK=9,
    REMOVED=10
)


def generate_parser():
    parser = argparse.ArgumentParser(
        description="Checks the status of a MongoDB replica set",
    )
    parser.add_argument(
        "-c", "--containers", required=True,
        help='container name(s) for MongoDB pods separated by , (e.g.: "mongodb,mongodb-service")',
    )
    parser.add_argument(
        "-p", "--project", required=False,
        help='the project name the checks should be running against',
    )
    return parser


check_mongodb_cmd = (
    "bash", "-c",
    'mongo 127.0.0.1/admin -u admin -p "$MONGODB_ADMIN_PASSWORD" --eval="print(JSON.stringify((rs.status())))" --quiet'
)


def parse_mongo_result(output):
    try:
        js = json.loads(output)
        return int(js.get("myState", js.get("state")))
    except:
        return None


def analize(status):
    return {
        REPLSET_STATUS.PRIMARY: nagios.OK,
        REPLSET_STATUS.SECONDARY: nagios.OK,
        REPLSET_STATUS.STARTUP: nagios.WARN,
        REPLSET_STATUS.ARBITER: nagios.WARN,
        REPLSET_STATUS.RECOVERING: nagios.CRIT,
        REPLSET_STATUS.FATAL: nagios.CRIT,
        REPLSET_STATUS.STARTUP2: nagios.CRIT,
        REPLSET_STATUS.UNKNOWN: nagios.CRIT,
        REPLSET_STATUS.DOWN: nagios.CRIT,
        REPLSET_STATUS.ROLLBACK: nagios.CRIT,
        REPLSET_STATUS.REMOVED: nagios.CRIT
    }.get(status, nagios.UNKNOWN)


def report(pods, rs_statuses, nag_statuses):
    if not pods:
        print "%s: Unable to locate any pods running mongodb" % (
            nagios.status_code_to_label(nagios.UNKNOWN),)
        return nagios.UNKNOWN

    unique_rs_statuses = Counter(rs_status for rs_status in rs_statuses)
    unique_nag_statuses = Counter(nag_status for nag_status in nag_statuses)

    ret = max(unique_nag_statuses)

    if unique_rs_statuses[REPLSET_STATUS.PRIMARY] != 1:
        ret = nagios.CRIT
        print "%s: There are %s nodes claiming to be primary members of the replica set" % (
            nagios.status_code_to_label(ret), unique_rs_statuses[REPLSET_STATUS.PRIMARY])
    elif len(rs_statuses) % 2 == 0:
        ret = nagios.WARN
        print "%s: There are an even number of voting members (%s) partipating in the replica set" % (
            nagios.status_code_to_label(ret), len(rs_statuses))
    else:
        print "%s: There are %s primary and %s secondary members in the replica set" % (
            (nagios.status_code_to_label(ret)),
            unique_rs_statuses[REPLSET_STATUS.PRIMARY],
            unique_rs_statuses[REPLSET_STATUS.SECONDARY])

    for pod, rs_status, nag_status in zip(pods, rs_statuses, nag_statuses):
        print "%s: %s - %s" % (
            nagios.status_code_to_label(nag_status),
            pod,
            REPLSET_STATUS.reverse_mapping[rs_status])

    return ret


def check(containers, project):
    if not project:
        project = openshift.get_project()

    pods = openshift.get_running_pod_names(project, container_names=containers.split(','))

    rs_statuses = map(parse_mongo_result, openshift.exec_in_pods(project, pods, check_mongodb_cmd))
    nag_statuses = map(analize, rs_statuses)

    return report(pods, rs_statuses, nag_statuses)


if __name__ == "__main__":
    args = generate_parser().parse_args()
    code = nagios.UNKNOWN
    try:
        code = check(args.containers, args.project)
    except:
        traceback.print_exc()
    finally:
        sys.exit(code)

# TODO: add logic to validate the health of all members in the json returned for each mongo
