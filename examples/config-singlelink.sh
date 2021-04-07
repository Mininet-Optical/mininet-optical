#!/bin/bash -x

set -e

# For now, devices are all at the same IP address and port
mn=localhost:8080; t1=$mn; t2=$mn
echo "* t1 is at $t1"
echo "* t2 is at $t2"

echo "* Attempting to configure singlelink.py network"

curl "$t1/connect?node=t1&ethPort=1&wdmPort=2&channel=1"
curl "$t2/connect?node=t2&ethPort=1&wdmPort=2&channel=1"
curl "$t1/turn_on?node=t1"
curl "$t2/turn_on?node=t2"

echo "* Monitoring signals at endpoints"
curl "$t1/monitor?monitor=t1-monitor"
curl "$t2/monitor?monitor=t2-monitor"

echo "* Done."
