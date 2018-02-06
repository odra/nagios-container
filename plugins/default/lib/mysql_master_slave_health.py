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


check_master_cmd = (
    "bash", "-c",
    'mysql -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" -h127.0.0.1 -e \'SHOW SLAVE HOSTS;\''
)


check_slave_cmd = (
    "bash", "-c",
    'mysql -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" -h127.0.0.1 -e \'SHOW SLAVE STATUS;\''
)


check_mysql_path = '/usr/lib64/nagios/plugins/check_mysql'


def report(nag_status, status, output, service):
    print output

    if "mysql-2" in service or "mysql-3" in service:
        if "Waiting for master to send event" not in status:
            nag_status = nagios.CRIT
    elif "mysql" in service:
        if "Empty set" in status:
            nag_status = nagios.CRIT
    return nag_status


def check(service, containers):
    project = openshift.get_project()

    selectors = openshift.get_service_selectors(project, service)
    pcs = openshift.get_running_pod_containers(project, selector=selectors, container_names=containers.split(','))

    # since core only has single mysql with replication, we only check one even if there are multiple results
    pod_name, container_name, container_data = pcs[0]

    env = openshift.get_container_env(project, pod_name, container_name)

    args = (check_mysql_path, "-H", service, "-u", env["MYSQL_USER"], "-p", env["MYSQL_PASSWORD"])

    status = None

    if "mysql-2" in service or "mysql-3" in service:
        status = openshift.exec_in_pod(project, pod_name, check_slave_cmd)
    elif "mysql" in service:
        status = openshift.exec_in_pod(project, pod_name, check_master_cmd)

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

    return report(nag_status, status, output, service)


if __name__ == "__main__":
    args = generate_parser().parse_args()
    code = nagios.UNKNOWN
    try:
        code = check(args.service, args.containers)
    except:
        traceback.print_exc()
    finally:
        sys.exit(code)
