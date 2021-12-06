#!/bin/bash -x

set -e  # exit script on error

# This script removes the ROADM rule installed by
# config-singleroadm.sh

# URL for REST server
url="localhost:8080"; t1=$url; t2=$url; t3=$url; r1=$url
curl="curl -s"

echo "* Removing ROADM rule forwarding ch1 from t1 to t2"
$curl "$r1/connect?node=r1&port1=1&port2=2&channels=1&action=remove"

echo "* Monitoring signals at endpoints"
for tname in t1 t2 t3; do
    url=${!tname}
    echo "* $tname"
    $curl "$url/monitor?monitor=$tname-monitor"
done

echo "* Done."
