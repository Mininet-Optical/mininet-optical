#!/bin/bash -x

set -e  # exit script on error

# URL for REST server
url="localhost:8080"; t1=$url; t2=$url; t3=$url; r1=$url
curl="curl -s"

echo "* Configuring terminals in singleroadm.py network"

$curl "$t1/connect?node=t1&ethPort=1&wdmPort=2&channel=1"
$curl "$t2/connect?node=t2&ethPort=1&wdmPort=2&channel=1"
$curl "$t3/connect?node=t3&ethPort=1&wdmPort=2&channel=1"

echo "* Monitoring signals at endpoints"
for tname in t1 t2 t3; do
    url=${!tname}
    $curl "$url/monitor?monitor=$tname-monitor"
done

echo "* Resetting ROADM"
$curl "$r1/reset?node=r1"

echo "* Configuring ROADM to forward ch1 from t1 to t2"
$curl "$r1/connect?node=r1&port1=1&port2=2&channels=1"

echo "* Turning on terminals/transceivers"

$curl "$t1/turn_on?node=t1"
$curl "$t2/turn_on?node=t2"
$curl "$t3/turn_on?node=t3"

echo "* Monitoring signals at endpoints"
for tname in t1 t2 t3; do
    url=${!tname}
    echo "* $tname"
    $curl "$url/monitor?monitor=$tname-monitor"
done

echo "* Done."
