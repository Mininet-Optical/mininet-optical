#!/bin/bash -x

set -e  # exit script on error

# URL for REST server
url="localhost:8080"

echo "* Configuring terminals in singleroadm.py network"

curl "$url/connect?node=t1&ethPort=1&wdmPort=2&channel=1"
curl "$url/connect?node=t2&ethPort=1&wdmPort=2&channel=1"
curl "$url/connect?node=t3&ethPort=1&wdmPort=2&channel=1"

echo "* Resetting ROADM"
curl "$url/reset?node=r1"

echo "* Configuring ROADM to forward ch1 from t1 to t2"
curl "$url/connect?node=r1&port1=1&port2=2&channels=1"

echo "* Turning on terminals/transceivers"

curl "$url/turn_on?node=t1"
curl "$url/turn_on?node=t2"
curl "$url/turn_on?node=t3"

echo "* Done."
