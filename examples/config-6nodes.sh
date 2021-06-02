#!/bin/bash -x

set -e  # exit script on error

# URL for REST server
url="localhost:8080"; t1=$url; t2=$url; t3=$url; t4=$url; t5=$url; t6=$url; r1=$url; r2=$url; r3=$url; r4=$url; r5=$url; r6=$url;

echo "* Configuring terminals in 6nodestopo.py network"

echo "* Configuring terminal 1 in 6nodestopo.py network"
#curl "$t1/connect?node=t1&ethPort=1&wdmPort=11&channel=1"
curl "$t1/connect?node=t1&ethPort=2&wdmPort=12&channel=2"
#curl "$t1/connect?node=t1&ethPort=3&wdmPort=13&channel=3"
curl "$t1/connect?node=t1&ethPort=4&wdmPort=14&channel=4"
curl "$t1/connect?node=t1&ethPort=5&wdmPort=15&channel=5"
#curl "$t1/connect?node=t1&ethPort=6&wdmPort=16&channel=6"

echo "* Configuring terminal 2 in 6nodestopo.py network"
curl "$t2/connect?node=t2&ethPort=3&wdmPort=13&channel=3"

echo "* Configuring terminal 3 in 6nodestopo.py network"
curl "$t3/connect?node=t3&ethPort=1&wdmPort=11&channel=1"
curl "$t3/connect?node=t3&ethPort=2&wdmPort=12&channel=2"

echo "* Configuring terminal 4 in 6nodestopo.py network"
curl "$t4/connect?node=t4&ethPort=1&wdmPort=11&channel=1"
#curl "$t4/connect?node=t4&ethPort=2&wdmPort=12&channel=2"
curl "$t4/connect?node=t4&ethPort=3&wdmPort=13&channel=3"
#curl "$t4/connect?node=t4&ethPort=4&wdmPort=14&channel=4"
#curl "$t4/connect?node=t4&ethPort=5&wdmPort=15&channel=5"
#curl "$t4/connect?node=t4&ethPort=6&wdmPort=16&channel=6"

echo "* Configuring terminal 5 in 6nodestopo.py network"
curl "$t5/connect?node=t5&ethPort=5&wdmPort=15&channel=5"

echo "* Configuring terminal 6 in 6nodestopo.py network"
curl "$t6/connect?node=t6&ethPort=4&wdmPort=14&channel=4"


echo "* Resetting ROADM"
curl "$r1/reset?node=r1"
curl "$r2/reset?node=r2"
curl "$r3/reset?node=r3"
curl "$r4/reset?node=r4"
curl "$r5/reset?node=r5"
curl "$r6/reset?node=r6"

echo "* Configuring ROADM 1"
curl "$r1/connect?node=r1&port1=111&port2=2&channels=2"
curl "$r1/connect?node=r1&port1=111&port2=4&channels=4"
curl "$r1/connect?node=r1&port1=111&port2=5&channels=5"

echo "* Configuring ROADM 2"
curl "$r2/connect?node=r2&port1=3&port2=222&channels=3"

echo "* Configuring ROADM 3"
curl "$r3/connect?node=r3&port1=111&port2=222&channels=3"
curl "$r3/connect?node=r3&port1=1&port2=222&channels=1"
curl "$r3/connect?node=r3&port1=2&port2=222&channels=2"

echo "* Configuring ROADM 4"
curl "$r4/connect?node=r4&port1=111&port2=1&channels=1"
curl "$r4/connect?node=r4&port1=111&port2=3&channels=3"
curl "$r4/connect?node=r4&port1=111&port2=222&channels=2"

echo "* Configuring ROADM 5"
curl "$r5/connect?node=r5&port1=111&port2=222&channels=2"
curl "$r5/connect?node=r5&port1=5&port2=222&channels=5"

echo "* Configuring ROADM 6"
curl "$r6/connect?node=r6&port1=111&port2=222&channels=2"
curl "$r6/connect?node=r6&port1=111&port2=222&channels=5"
curl "$r6/connect?node=r6&port1=4&port2=222&channels=4"

echo "* Turning on terminals/transceivers"

#curl "$t1/turn_on?node=t1"
curl "$t2/turn_on?node=t2"
curl "$t3/turn_on?node=t3"
#curl "$t4/turn_on?node=t4"
curl "$t5/turn_on?node=t5"
curl "$t6/turn_on?node=t6"

echo "* Monitoring signals at endpoints"
for tname in t1 t4; do
    url=${!tname}
    echo "* $tname"
    curl "$url/monitor?monitor=$tname-monitor"
done


echo "* Monitoring signals at ROADMs"
for rname in r1 r2 r3 r4 r5 r6; do
    url=${!rname}
    echo "* $rname"
    curl "$url/monitor?monitor=$rname-monitor"
done

echo "* Done."
