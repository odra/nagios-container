#!/usr/bin/env python
######################################################################
#
# Nagios plugin to check mongodb pod nodes
#
# If 2 of the 3 mongodb pods are on the same node, a warning is generated.
# If less than 3 mongodb pods are found, a critical is generated.
#
# Copyright (c) 2018, Red Hat Ltd. All rights reserved.
#
######################################################################
import sys
import traceback

import nagios
import openshift


def report(nag_status, output):
    print(output)
    print(nag_status)
    return nag_status


def check():
    project = openshift.get_project()
    pods = openshift.get_running_pod_names(project, container_names="mongodb")
    if not pods:
        output = "Unable to locate any mongodb containers"
        return nagios.UNKNOWN
    nodes = openshift.get_nodes_from_names(pods)
    nodes_pods = dict(zip(pods,nodes))
    if len(nodes) < 3:
      output = nodes_pods
      return nagios.CRIT
    print(pods)
    print(nodes)
    if nodes[0] == nodes[1] or nodes[0] == nodes[2] or nodes[1] == nodes[2]:
      output = nodes_pods
      nag_status = nagios.WARN
    else:
      output = nodes_pods
      nag_status = nagios.OK
    return report(nag_status, output)


if __name__ == "__main__":
    code = nagios.UNKNOWN
    try:
        code = check()
    except:
        traceback.print_exc()
    finally:
        sys.exit(code)
