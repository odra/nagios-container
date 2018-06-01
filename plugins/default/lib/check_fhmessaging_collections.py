#!/usr/bin/env python
######################################################################
#
# Nagios plugin to check existance of fh-messaging collections
#
# Daily collections created in the fh-messaging/fh-reporting database
# are created via calls from millicore. The absence of these collections
# might indicate an issue with millicore
#
# Copyright (c) 2018, Red Hat Ltd. All rights reserved.
#
######################################################################
import argparse
import json
import sys
import time
import traceback

import nagios
import openshift


# fh-messaging topics
topics = [
  "apicalled",
  "appbuild",
  "appcreate",
  "appinit",
  "fhact",
  "useractivate",
  "userlogin"
]


def generate_parser():
    parser = argparse.ArgumentParser(
        description="Checks for the existance of fh-messaging collections on a MongoDB replica set",
    )
    parser.add_argument(
        "-c", "--containers", required=True,
        help='container name(s) for MongoDB pods separated by , (e.g.: "mongodb,mongodb-service")',
    )
    return parser


check_mongodb_cmd = (
    "bash", "-c",
    'mongo 127.0.0.1/$MONGODB_FHREPORTING_DATABASE -u $MONGODB_FHREPORTING_USER ' +
    '-p $MONGODB_FHREPORTING_PASSWORD --eval="rs.slaveOk();' +
    'print(JSON.stringify(db.getCollectionNames()))" --quiet'
)


def parse_mongo_result(output):
    try:
        js = json.loads(output)
        return js
    except:
        return None


def topic_existance(topics, data):
    today = time.strftime('%Y%m%d')
    result = {}

    for topic in topics:
        topic_name = topic + "_" + today
        result[topic] = topic_name in data[0]

    return result


def report(pods, project, result):
    if not pods:
        print "%s: Unable to locate any pods running mongodb" % (
            nagios.status_code_to_label(nagios.UNKNOWN),)
        return nagios.UNKNOWN

    code = nagios.OK
    today = time.strftime('%Y%m%d')
    collections_missing_count = 0

    for topic, exist in result.iteritems():
        # fh-reporting fhact_yyyymmdd collections are not stored in the core database
        if project == "rhmap-core" and topic == "fhact":
            continue
        # fh-reporting database on the mbaas contains only the fhact_yyyymmdd collections
        elif project != "rhmap-core" and topic != "fhact":
            continue

        if not exist:
            print "Collection %s_%s does not exist" % (topic, today)
            code = nagios.WARN
            collections_missing_count += 1

    # If more than one of the collections is missing on the core its potentially an issue
    # with millicore
    if project == "rhmap-core" and collections_missing_count > 1:
        code = nagios.CRIT

    # If the fhact collection is missing in the mbaas, its potentially an issue with millicore
    elif project != "rhmap-core" and collections_missing_count == 1:
        code = nagios.CRIT

    if code == nagios.OK:
        print "OK. Collections exist"

    return code


def check(containers):
    project = openshift.get_project()
    pods = openshift.get_running_pod_names(project, container_names=containers.split(','))
    collections = map(parse_mongo_result, openshift.exec_in_pods(project, pods, check_mongodb_cmd))
    result = topic_existance(topics, collections)

    return report(pods, project, result)


if __name__ == "__main__":
    args = generate_parser().parse_args()
    code = nagios.UNKNOWN
    try:
        code = check(args.containers)
    except:
        traceback.print_exc()
    finally:
        sys.exit(code)
