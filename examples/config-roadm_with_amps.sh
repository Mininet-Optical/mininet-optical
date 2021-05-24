#!/bin/bash -x

set -e  # exit script on error

# URL for REST server
url="localhost:8080"; t1=$url; t2=$url; r1=$url
curl="curl -s"

$curl "$t1/connect?node=t1&ethPort=1&wdmPort=2&channel=1"
$curl "$t2/connect?node=t2&ethPort=1&wdmPort=2&channel=1"
$curl "$r1/connect?node=r1&port1=1&port2=2&channels=1"
$curl "$t1/turn_on?node=t1"
$curl "$t2/turn_on?node=t2"
