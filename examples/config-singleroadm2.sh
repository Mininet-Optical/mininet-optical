#!/bin/bash

set -e  # exit script on error

# URL for REST server
url="localhost:8080"; t1=$url; t2=$url; t3=$url; r1=$url

echo "* Configuring terminals in singleroadm.py network"
for tname in t1 t2 t3; do
    url=${!tname}
    curl "$url/connect?node=$tname&ethPort=3&wdmPort=1&channel=1"
    curl "$url/connect?node=$tname&ethPort=4&wdmPort=2&channel=2"
done

echo "* Resetting ROADM"
curl "$r1/reset?node=r1"

echo "* Configuring ROADM"
# Connect t1 to t2 and t3 on channels 1 and 2
# NB: this connects s3 <-> s1 <-> s2, so h3 can
# talk to h2 via s1 !!
curl "$r1/connect?node=r1&port1=1&port2=3&channels=1"
curl "$r1/connect?node=r1&port1=2&port2=6&channels=2"

echo "* Turning on terminals/transceivers"
for tname in t1 t2 t3; do
    url=${!tname}
    curl "$url/turn_on?node=$tname"
done

echo "* Monitoring signals at endpoints"
for tname in t1 t2 t3; do
    url=${!tname}
    echo "* $tname"
    curl "$url/monitor?monitor=$tname-monitor"
done

echo "* Done."
