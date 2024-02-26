#!/bin/bash

testdir=$(dirname $0)

# config-crosslayer.sh:
#
# TODO: description

# REST ports for network components
r1l1ie=localhost:8080
r1l2ie=localhost:8080
r2l3ie=localhost:8080
r2l4ie=localhost:8080
r3l5ie=localhost:8080
r3l6ie=localhost:8080
r1l1us=localhost:8080
r1l2us=localhost:8080
r2l3us=localhost:8080
r2l4us=localhost:8080
r3l5us=localhost:8080
r3l6us=localhost:8080
teraie1=localhost:8080
teraus1=localhost:8080
teraie2=localhost:8080
teraus2=localhost:8080
polatisie=localhost:8080
polatisus=localhost:8080

# Helper script for sending commands to servers
m=../mininet/util/m


# Reset ROADM configurations

echo '*** Resetting ROADMs IE'
curl "$r1l1ie/reset?node=r1l1ie"
curl "$r1l2ie/reset?node=r1l2ie"
curl "$r2l3ie/reset?node=r2l3ie"
curl "$r2l4ie/reset?node=r2l4ie"
curl "$r3l5ie/reset?node=r3l5ie"
curl "$r3l6ie/reset?node=r3l6ie"

echo '*** Resetting ROADMs US'
curl "$r1l1us/reset?node=r1l1us"
curl "$r1l2us/reset?node=r1l2us"
curl "$r2l3us/reset?node=r2l3us"
curl "$r2l4us/reset?node=r2l4us"
curl "$r3l5us/reset?node=r3l5us"
curl "$r3l6us/reset?node=r3l6us"

echo '*** Resetting Polatis'
curl "$polatisie/reset?node=polatisie"
curl "$polatisus/reset?node=polatisus"


# ROADM scenario 1 - REST version


echo '*** Installing ROADM configuration IE (REST)'

curl "$r1l1ie/connect?node=r1l1ie&port1=4101&port2=4201&channels=61"
curl "$r1l2ie/connect?node=r1l2ie&port1=4101&port2=4201&channels=61"
curl "$r1l1ie/connect?node=r1l1ie&port1=5101&port2=5201&channels=61"
curl "$r1l2ie/connect?node=r1l2ie&port1=5101&port2=5201&channels=61"

curl "$r2l3ie/connect?node=r2l3ie&port1=4101&port2=4201&channels=61"
curl "$r2l4ie/connect?node=r2l4ie&port1=4101&port2=4201&channels=61"
curl "$r2l3ie/connect?node=r2l3ie&port1=5101&port2=5201&channels=61"
curl "$r2l4ie/connect?node=r2l4ie&port1=5101&port2=5201&channels=61"

curl "$r3l5ie/connect?node=r3l5ie&port1=4101&port2=4201&channels=61"
curl "$r3l6ie/connect?node=r3l6ie&port1=4101&port2=4201&channels=61"
curl "$r3l5ie/connect?node=r3l5ie&port1=5101&port2=5201&channels=61"
curl "$r3l6ie/connect?node=r3l6ie&port1=5101&port2=5201&channels=61"

echo '*** Installing ROADM configuration US (REST)'

curl "$r1l1us/connect?node=r1l1us&port1=4101&port2=4201&channels=61"
curl "$r1l2us/connect?node=r1l2us&port1=4101&port2=4201&channels=61"
curl "$r1l1us/connect?node=r1l1us&port1=5101&port2=5201&channels=61"
curl "$r1l2us/connect?node=r1l2us&port1=5101&port2=5201&channels=61"

curl "$r2l3us/connect?node=r2l3us&port1=4101&port2=4201&channels=61"
curl "$r2l4us/connect?node=r2l4us&port1=4101&port2=4201&channels=61"
curl "$r2l3us/connect?node=r2l3us&port1=5101&port2=5201&channels=61"
curl "$r2l4us/connect?node=r2l4us&port1=5101&port2=5201&channels=61"

curl "$r3l5us/connect?node=r3l5us&port1=4101&port2=4201&channels=61"
curl "$r3l6us/connect?node=r3l6us&port1=4101&port2=4201&channels=61"
curl "$r3l5us/connect?node=r3l5us&port1=5101&port2=5201&channels=61"
curl "$r3l6us/connect?node=r3l6us&port1=5101&port2=5201&channels=61"


# Netconf part:

#addc=$testdir/nc_add_connection.py
#r1l1ie_netconf=localhost:1831
#r1l2ie_netconf=localhost:1832
#r1l3ie_netconf=localhost:1833
#r2l4ie_netconf=localhost:1834
#r2l5ie_netconf=localhost:1835
#r3l6ie_netconf=localhost:1836
#r3l7ie_netconf=localhost:1837
#r2l8ie_netconf=localhost:1838
#
#r1l1us_netconf=localhost:1841
#r1l2us_netconf=localhost:1842
#r1l3us_netconf=localhost:1843
#r2l4us_netconf=localhost:1844
#r2l5us_netconf=localhost:1845
#r3l6us_netconf=localhost:1846
#r3l7us_netconf=localhost:1847
#r2l8us_netconf=localhost:1848



# Configure Transponders and transceivers (bidirectional connections)
echo '*** Configuring Tera transponders and transceivers'
curl "$teraie1/connect?node=teraie1&ethPort=1&wdmPort=2&channel=61"
curl "$teraie1/connect?node=teraie1&ethPort=4&wdmPort=3&channel=61"
curl "$teraie2/connect?node=teraie2&ethPort=1&wdmPort=3&channel=61"
curl "$teraie2/connect?node=teraie2&ethPort=4&wdmPort=2&channel=61"
curl "$teraus1/connect?node=teraus1&ethPort=1&wdmPort=2&channel=61"
curl "$teraus1/connect?node=teraus1&ethPort=4&wdmPort=3&channel=61"
curl "$teraus2/connect?node=teraus2&ethPort=1&wdmPort=3&channel=61"
curl "$teraus2/connect?node=teraus2&ethPort=4&wdmPort=2&channel=61"

# scenario 1:
scenario1(){

  curl "$polatisie/connect?node=polatisie&port1=1&port2=3&channels=61"
  curl "$polatisie/connect?node=polatisie&port1=8&port2=16&channels=61"

  curl "$polatisus/connect?node=polatisus&port1=1&port2=2&channels=61"
  curl "$polatisus/connect?node=polatisus&port1=8&port2=16&channels=61"

}

# scenario 2:
scenario2() {

  curl "$polatisie/connect?node=polatisie&port1=1&port2=6&channels=61"
  curl "$polatisie/connect?node=polatisie&port1=12&port2=14&channels=61"
  curl "$polatisie/connect?node=polatisie&port1=9&port2=16&channels=61"

  curl "$polatisus/connect?node=polatisus&port1=1&port2=6&channels=61"
  curl "$polatisus/connect?node=polatisus&port1=12&port2=14&channels=61"
  curl "$polatisus/connect?node=polatisus&port1=9&port2=16&channels=61"

}

echo '*** Set up scenario'

scenario2

echo '*** Turning on transponders'

curl "$teraie1/turn_on?node=teraie1"
curl "$teraus1/turn_on?node=teraus1"
curl "$teraie2/turn_on?node=teraie2"
curl "$teraus2/turn_on?node=teraus2"


"* Monitoring signals at endpoints"
for tname in teraie1 teraie2 teraus1 teraus2; do
    url=${!tname}
    echo "* $tname"
    curl "$url/monitor?monitor=$tname-monitor"
done

echo '*** Done.'


