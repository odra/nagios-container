#!/usr/bin/env python
import argparse
import re
import sys
import traceback
from collections import Counter

import nagios
import openshift


def generate_parser():
    parser = argparse.ArgumentParser(
        description="Checks the disk usage (blocks and inodes)",
    )
    parser.add_argument(
        "-w", "--warn", type=int, required=True,
        help="set warning threshold of disk usage (%% of blocks or inodes)",
    )
    parser.add_argument(
        "-c", "--crit", type=int, required=True,
        help="set critical threshold of disk usage (%% of blocks or inodes), "
             "must be higher than or equal the warning threshold",
    )
    parser.add_argument(
        "-m", "--minimum", type=int, required=False, default=10,
        help="set minimum threshold of disk usage  (%% of blocks or inodes), "
             "details will only be reported for volumes over this value",
    )
    return parser


check_disk_cmd = ("df", "--output=pcent,ipcent,target")
# Example output:
# Use% IUse% Mounted on
#   1%    1% /
#  20%    8% /etc/hosts
check_disk_output_pattern = re.compile(r"\s*(\d+)%\s+(\d+)%\s+(.+)$")


def parse_df_line(line):
    mo = check_disk_output_pattern.match(line)
    if mo is None:
        return ()
    return mo.group(3), int(mo.group(1)), int(mo.group(2))


def parse_df_lines(lines):
    return filter(None, map(parse_df_line, lines.splitlines()))


def analize(pod, container, disks, warning_threshold, critical_threshold):
    results = []
    for mount, space_usage, inode_usage in disks:
        max_pcent = max(space_usage, inode_usage)

        disk_status = nagios.UNKNOWN
        if max_pcent >= critical_threshold:
            disk_status = nagios.CRIT
        elif max_pcent >= warning_threshold:
            disk_status = nagios.WARN
        elif max_pcent < warning_threshold:
            disk_status = nagios.OK

        results.append([pod, container, mount, space_usage, inode_usage, disk_status])
    return results


def report(results, errors, minimum):
    if not results:
        return nagios.UNKNOWN

    unique_statuses = Counter(
        disk_status
        for pod, container, mount, space_usage, inode_usage, disk_status in results
    )

    ret = max(unique_statuses)

    print "Checked %s volumes (%s critical, %s warning)" % (
        len(results), unique_statuses[nagios.CRIT], unique_statuses[nagios.WARN])

    for pod, container, mount, disk_usage, inode_usage, status in results:
        if max(disk_usage, inode_usage) > minimum:
            print "%s: %s:%s:%s - bytes used: %s%%, inodes used: %s%%" % (
                nagios.status_code_to_label(status), pod, container, mount, disk_usage, inode_usage)

    if errors:
        ret = nagios.UNKNOWN
        for pod_name, container_name, ex in errors:
            print "%s: %s:%s %s" % (
                nagios.status_code_to_label("WARNING"), pod_name, container_name, ex)

    return ret


def check(warn, crit, minimum):
    if crit < warn:
        msg = "critical threshold cannot be lower than warning threshold: %d < %d"
        raise ValueError(msg % (crit, warn))

    project = openshift.get_project()

    results = []
    errors = []

    pcs = openshift.get_running_pod_containers(project)

    for pod_name, container_name, container_data in pcs:
        try:
            result = openshift.exec_in_pod_container(project, pod_name, container_name, check_disk_cmd)

            results.extend(analize(pod_name, container_name, parse_df_lines(result), warn, crit))
        except Exception as e:
            errors.append((pod_name, container_name, e))

    return report(results, errors, minimum)


if __name__ == "__main__":
    args = generate_parser().parse_args()
    code = nagios.UNKNOWN
    try:
        code = check(args.warn, args.crit, args.minimum)
    except:
        traceback.print_exc()
    finally:
        sys.exit(code)
