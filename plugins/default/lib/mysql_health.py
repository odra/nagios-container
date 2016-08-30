#!/usr/bin/env python
import argparse
import sys
import traceback

import nagios
import openshift
from subprocess import CalledProcessError, check_output


def generate_parser():
    parser = argparse.ArgumentParser(
        description="Checks the status of a system running mysql",
    )
    parser.add_argument(
        "-s", "--service", required=True,
        help='service name for mysql',
    )
    parser.add_argument(
        "-c", "--containers", required=True,
        help='container name(s) for mysql pods separated by commas (e.g. mysql,mysql-service)',
    )
    return parser


check_mysql_path = '/usr/lib64/nagios/plugins/check_mysql'


def report(nag_status, output):
    print output

    return nag_status


def check(service, containers):
    project = openshift.get_project()

    selectors = openshift.get_service_selectors(project, service)
    pcs = openshift.get_running_pod_containers(project, selector=selectors, container_names=containers.split(','))

    # since core only has single mysql with replication, we only check one even if there are multiple results
    pod_name, container_name, container_data = pcs[0]

    env = openshift.get_container_env(project, pod_name, container_name)

    args = (check_mysql_path, "-H", service, "-u", env["MYSQL_USER"], "-p", env["MYSQL_PASSWORD"])

    try:
        output = check_output(args)
        nag_status = nagios.OK
    except CalledProcessError as cpe:
        if cpe.returncode in (nagios.OK, nagios.WARN, nagios.CRIT, nagios.UNKNOWN):
            output = cpe.output
            nag_status = cpe.returncode
        else:
            output = str(cpe)
            nag_status = nagios.UNKNOWN

    return report(nag_status, output)


if __name__ == "__main__":
    args = generate_parser().parse_args()
    code = nagios.UNKNOWN
    try:
        code = check(args.service, args.containers)
    except:
        traceback.print_exc()
    finally:
        sys.exit(code)
