#!/bin/bash -x

set -e  # exit script on error

# URL for REST server
url="localhost:8080"; t0=$url; t1=$url; t2=$url; t3=$url; t4=$url; t5=$url;
r0=$url; r1=$url; r2=$url; r3=$url; r4=$url; r5=$url;

echo "* Configuring terminals in sixNodeRingTopology.py network"

curl "$t0/connect?node=t0&ethPort=1&wdmPort=8&channel=1"
curl "$t1/connect?node=t1&ethPort=2&wdmPort=9&channel=2"
curl "$t2/connect?node=t2&ethPort=3&wdmPort=10&channel=3"
curl "$t3/connect?node=t3&ethPort=1&wdmPort=8&channel=1"
curl "$t4/connect?node=t4&ethPort=2&wdmPort=9&channel=2"
curl "$t5/connect?node=t5&ethPort=3&wdmPort=10&channel=3"

echo "* Monitoring signals at endpoints"
for tname in t0 t1 t2 t3 t4 t5; do
    url=${!tname}
    curl "$url/monitor?monitor=$tname-monitor"
done

echo "* Resetting ROADM"
curl "$r0/reset?node=r0"
curl "$r1/reset?node=r1"
curl "$r2/reset?node=r2"
curl "$r3/reset?node=r3"
curl "$r4/reset?node=r4"
curl "$r5/reset?node=r5"

echo "* Configuring ROADM to forward ch1 from RU0 to BBU0"
curl "$r0/connect?node=r0&port1=2&port2=100&channels=1"
curl "$r1/connect?node=r1&port1=101&port2=100&channels=1"
curl "$r2/connect?node=r2&port1=101&port2=100&channels=1"
curl "$r3/connect?node=r3&port1=101&port2=2&channels=1"

echo "* Configuring ROADM to forward ch2 from RU1 to BBU1"
curl "$r1/connect?node=r1&port1=3&port2=100&channels=2"
curl "$r2/connect?node=r2&port1=101&port2=100&channels=2"
curl "$r3/connect?node=r3&port1=101&port2=100&channels=2"
curl "$r4/connect?node=r4&port1=101&port2=3&channels=2"

echo "* Configuring ROADM to forward ch2 from RU2 to BBU2"
curl "$r2/connect?node=r2&port1=4&port2=100&channels=3"
curl "$r3/connect?node=r3&port1=101&port2=100&channels=3"
curl "$r4/connect?node=r4&port1=101&port2=100&channels=3"
curl "$r5/connect?node=r5&port1=101&port2=4&channels=3"

echo "* Turning on terminals/transceivers"

curl "$t0/turn_on?node=t0"
curl "$t1/turn_on?node=t1"
#curl "$t2/turn_on?node=t2"

echo "* Monitoring signals at endpoints"
for tname in t0 t1 t2 t3 t4 t5; do
    url=${!tname}
    echo "* $tname"
    curl "$url/monitor?monitor=$tname-monitor"
done

echo "* Done."
