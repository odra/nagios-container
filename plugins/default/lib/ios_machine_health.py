#!/usr/bin/env python
import argparse
import nagios
import sys
import json
import traceback
import urllib2
import base64
from collections import Counter


class RequestError(Exception):

    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message


def generate_parser():
    parser = argparse.ArgumentParser(
        description="Checks the online status of the ios mac machines via Jenkins"
    )
    parser.add_argument(
        "-H", "--host", required=True,
        help="host of the Jenkins service"
    )
    parser.add_argument(
        "-P", "--port", required=True,
        help="port of the Jenkins service"
    )
    parser.add_argument(
        "-u", "--user", required=True,
        help="The username of the Jenkins service"
    )
    parser.add_argument(
        "-p", "--password", required=True,
        help="The password of the Jenkins service"
    )
    return parser


def report(results, errors):

    if not results:
        return nagios.UNKNOWN

    unique_statuses = Counter(
        computer[1]
        for computer in results
        )

    ret = max(unique_statuses)

    for computer in results:
        computer[1]
        if computer[1] == nagios.CRIT:
            print 'Machine: %s is unavailable to Jenkins - Status is %s ' % (
                computer[0], nagios.status_code_to_label(computer[1]))
        elif computer[1] == nagios.OK:
            print 'Machine: %s is available to Jenkins - Status is %s ' % (
                computer[0], nagios.status_code_to_label(computer[1]))
        elif computer[1] == nagios.UNKNOWN:
            print 'Machine: %s status is %s ' % (
                computer[0], nagios.status_code_to_label(computer[1]))
        else:
            print 'Unable to determine the status of the mac machine'

    if ret == nagios.OK:
        print "%s: %s ios slave machine(s) is/are available" % (
            nagios.status_code_to_label(ret), len(results))
    elif ret == nagios.UNKNOWN:
        print "%s: Unable to determine status of %s ios slave machine(s)" % (
            nagios.status_code_to_label(ret), len(results))
    elif ret == nagios.CRIT:
        print "%s: Unable to contact %s ios slave machine(s)" % (
            nagios.status_code_to_label(ret), len(results))
    if errors:
        ret = nagios.UNKNOWN

    return ret


def parse_response(response):
    results = []
    errors = []
    if response is not None:
        for computer in response['computer']:
            nagios_status = nagios.UNKNOWN
            if "mac" in str(computer['displayName']):
                try:
                    offline = computer['offline']
                    if offline:
                        nagios_status = nagios.CRIT
                    else:
                        nagios_status = nagios.OK
                    results.append((computer['displayName'], nagios_status))
                except:
                    nagios_status = nagios.UNKNOWN
                    errors.append((computer['displayName'], nagios_status))
    else:
        sys.stdout.write("No response from request")
        errors.append(("", nagios.UNKNOWN))
    return (results, errors)


def do_request(host, port, username, password):
    endpoint = "/computer/api/json"
    request = urllib2.Request("https://%s:%s%s" % (host, port, endpoint))
    base64string = base64.encodestring('%s:%s' % (username, password)).replace('\n', '')
    request.add_header("Authorization", "Basic %s" % base64string)
    try:
        response = urllib2.urlopen(request).read()
        try:
            data = json.loads(response)
        except ValueError:
            raise RequestError('The response data did not return parseable json data')
    except urllib2.URLErrror as error:
        raise RequestError(
            'The health endpoint at "%s" is not contactable. Error: %s' %
            (request, error))
    return data


def check(host, port, username, password):
    if host == "" or host is None:
        msg = "Jenkins host must be valid and not null, unable to carry out the check"
        raise ValueError(msg, "Hostname: %s " % host)

    results = []
    errors = []
    response = do_request(host, port, username, password)
    results, errors = parse_response(response)
    report(results, errors)


if __name__ == "__main__":
    args = generate_parser().parse_args()
    code = nagios.UNKNOWN
    try:
        code = check(args.host, args.port, args.user, args.password)
    except:
        traceback.print_exc()
    finally:
        sys.exit(code)
