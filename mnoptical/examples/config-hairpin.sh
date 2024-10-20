#!/bin/bash -x

set -e

# For now, devices are all at the same IP address and port
mn=localhost:8080; t1=$mn; t2=$mn; t3=$mn
echo "* t1 is at $t1"
echo "* t2 is at $t2"
echo "* t3 is at $t3"

echo "* Attempting to configure hairpin.py network"

curl="curl -s"

$curl "$t1/connect?node=t1&ethPort=1&wdmPort=2&channel=1"
$curl "$t2/connect?node=t2&ethPort=1&wdmPort=2&channel=2"
$curl "$t3/connect?node=t3&wdmInPort=1&wdmPort=2&inChannel=1&channel=2"
$curl "$t1/turn_on?node=t1"
$curl "$t2/turn_on?node=t2"
$curl "$t3/turn_on?node=t3"

echo "* Monitoring signals at endpoints"
$curl "$t1/monitor?monitor=t1-monitor"
$curl "$t2/monitor?monitor=t2-monitor"
$curl "$t3/monitor?monitor=t2-monitor"

echo "* Done."
