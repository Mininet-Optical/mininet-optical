#!/bin/bash -x

set -e

echo "* Attempting to configure singlelink.py network"

curl 'localhost:8080/connect?node=t1&ethPort=1&wdmPort=2&channel=1'
curl 'localhost:8080/connect?node=t2&ethPort=1&wdmPort=2&channel=1'
curl 'localhost:8080/turn_on?node=t1'
curl 'localhost:8080/turn_on?node=t2'

echo "* Done."
