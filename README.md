# RHMAP Nagios for Docker

[![Build Status](https://travis-ci.org/feedhenry/nagios-container.svg?branch=master)](https://travis-ci.org/feedhenry/nagios-container)

Nagios server in a Docker container for RHMAP.

## Development

### Running tests

```
python -m unittest discover -s plugins/default
```

### Style Guide and common problems

We use tools to enforce the [PEP8](https://www.python.org/dev/peps/pep-0008/)
style guide and prevent common problems on all Python code in this repository.

When developing the project, you'll need to install the dependencies:

```
pip install flake8 autopep8
brew install flake8 #osx
```

Use [flake8](https://pypi.python.org/pypi/flake8) to verify that the code
conforms to the style guide, and is free of common errors:

```
flake8 --show-source
```

Automatically format source code using
[autopep8](https://pypi.python.org/pypi/autopep8):

```
find . -name '*.py' -print0 | xargs -0 autopep8 --in-place --aggressive --aggressive
```

You may integrate `flake8` and `autopep8` with your code editor.

### General Development Info
#### Order of Nagios Status'

The order of priority of the Nagios Checks as indicated by their number in [nagios.py](plugins/default/lib/nagios.py) when reporting to the console is:
```
 OK = 0
 WARN = 1
 CRIT = 2
 UNKNOWN =3
```
In the case of checks where multiple components are involved (i.e cpu and memory usage) `max(status)` is used to check the highest result. I.e. if there are no unknown it will report a critical. However if there is an unknown this would be reported over a critical result.

#### Hostgroups

Currently there are 4 available hostgroups that nagios will run checks for, `core, mbaas, userdata and digger` Depending on the project the nagios container is being deployed to, the checks run will be decided by this value.

#### Create a New Check

In order to add a new check, the following syntax is followed, (using digger mac machine check as an example) [fhservices.cfg.j2](https://github.com/feedhenry/nagios-container/blob/master/fhservices.cfg.j2) is a j2 template file where services and commands are defined to be templated out and used by nagios.

Variables are passed to the file from [make-nagios-fh-services.cfg](https://github.com/feedhenry/nagios-container/blob/master/make-nagios-fhservices-cfg#L47-L52) and are picked up using the j2 syntax `{{ variable_name }}`

Do the following steps in the file:

* define the service (notice the hosgroup_name specified as digger)

```
define service {
       service_description mac_ios:ping
       check_command ios_machine_health!{{ jenkins_host }}!443!{{ jenkins_user }}!{{ jenkins_pass }}
       use generic-service
       hostgroup_name digger
       contact_groups rhmapadmins
}
```

The syntax for passing arguments is `check_command <command-name>!<param1>!<param2>`

* define the command called by check_command
```
define command {
      command_name    ios_machine_health
      command_line    /opt/rhmap/nagios/plugins/ios_machine_health -H $ARG1$ -P $ARG2$ -u $ARG3$ -p $ARG4$
}
```
The syntax for receiving commands is $ARG<X>$ which picks up the arguments in the order they are passed.


#### Writing a plugin

In this example an additional plugin is required - ios_machine_health. The plugin carries out the logic required to complete the check and print and return the status of the check. In this case:

* a request is sent to jenkins for some data about the mac machine.
* the response is parsed for the value `offline` for each mac machine.
* results are logged to the results/errors tuple
* Messages are printed out for each mac machine checked
* the Nagios check values in the tuple are evaluated following the order mentioned here
* an overall status is returned which is show in the nagios dashboard along with the printed text


#### Testing/Developing a Plugin

To test some changes in OpenShift:

* add the initial changes mentioned above.
* push the changes to pr to trigger image build
* udpate the image to the the new image tag in the nagios-container deploymentconfig
* Go to terminal in the OpenShift console or `oc rsh` to the pod
* Copy the nagios folder to /tmp. `cp -r /opt/rhmap/nagios /tmp
* cd to the plugin folder `cd /tmp/nagios/plugins`
* Edit the plugin as required using vi editor
* run the plugin from the command line (passing the required params) e.g. `./ios_machine_health -H <hostname> -P <port> -u <jenkins-user> -p <jenkins-password>`

### Version Bump

To bump the version for nagios-container:

* Go to the [nagios_container_pullrequests](http://bob.feedhenry.net:8080/job/nagios-container_pullrequests/) job in Jenkins
* Configure
* Go to `Execute shell`
* Bump the version at `VERSION=""`
