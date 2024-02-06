#!/bin/bash

testdir=$(dirname $0)

# config-sigcommtutorial.sh:
#
# This is for the SIGCOMM 22 tutorial at <wiki-link>
#
# This script configures the tutorial network in two
# configurations. The first configuration connects srv1_co1
# and srv1_lg1, while the second configuration connects
# srv1_co1 and srv2_lg1

# REST ports for network components
r1l1ie=localhost:8080
r1l2ie=localhost:8080
r1l3ie=localhost:8080
r2l4ie=localhost:8080
r2l5ie=localhost:8080
r3l6ie=localhost:8080
r3l7ie=localhost:8080
r1l1us=localhost:8080
r1l2us=localhost:8080
r1l3us=localhost:8080
r2l4us=localhost:8080
r2l5us=localhost:8080
r3l6us=localhost:8080
r3l7us=localhost:8080
teraie=localhost:8080
teraus=localhost:8080
polatisie=localhost:8080
polatisus=localhost:8080

# Helper script for sending commands to servers
m=../mininet/util/m

# Helper function: send gratuitous arps from all servers
arp () {
    echo '*** Sending gratuitous ARPs'
    $m serverie arping -c 1 -U -I serverie-eth0 192.168.1.1
    $m serverie arping -c 1 -U -I serverie-eth1 192.168.1.1
    $m serverus arping -c 1 -U -I serverus-eth0 192.168.1.2
    $m serverus arping -c 1 -U -I serverus-eth1 192.168.1.2
    $m crossatl1 arping -c 1 -U -I crossatl1-eth0 192.168.1.3
    $m crossatl1 arping -c 1 -U -I crossatl1-eth1 192.168.1.3
    $m crossatl2 arping -c 1 -U -I crossatl2-eth0 192.168.1.3
    $m crossatl2 arping -c 1 -U -I crossatl2-eth1 192.168.1.3
    $m crossatl2 arping -c 1 -U -I crossatl2-eth2 192.168.1.3
    $m servermmw arping -c 1 -U -I servermmw-eth0 192.168.1.4
}

# Reset ROADM configurations
reset() {
    echo '*** Resetting ROADMs IE'
    curl "$r1l1ie/reset?node=r1l1ie"
    curl "$r1l2ie/reset?node=r1l2ie"
    curl "$r1l3ie/reset?node=r1l3ie"
    curl "$r2l4ie/reset?node=r2l4ie"
    curl "$r2l5ie/reset?node=r2l5ie"
    curl "$r3l6ie/reset?node=r3l6ie"
    curl "$r3l7ie/reset?node=r3l7ie"

    echo '*** Resetting ROADMs US'
    curl "$r1l1us/reset?node=r1l1us"
    curl "$r1l2us/reset?node=r1l2us"
    curl "$r1l3us/reset?node=r1l3us"
    curl "$r2l4us/reset?node=r2l4us"
    curl "$r2l5us/reset?node=r2l5us"
    curl "$r3l6us/reset?node=r3l6us"
    curl "$r3l7us/reset?node=r3l7us"
}

# ROADM scenario 1 - REST version

connect1rest() {
    echo '*** Installing ROADM configuration IE (REST)'

    curl "$r1l1ie/connect?node=r1l1ie&port1=4101&port2=4201&channels=61"
    curl "$r1l2ie/connect?node=r1l2ie&port1=4101&port2=4201&channels=61"
    curl "$r1l3ie/connect?node=r1l3ie&port1=4101&port2=4201&channels=61"
    curl "$r1l1ie/connect?node=r1l1ie&port1=5101&port2=5201&channels=61"
    curl "$r1l2ie/connect?node=r1l2ie&port1=5101&port2=5201&channels=61"
    curl "$r1l3ie/connect?node=r1l3ie&port1=5101&port2=5201&channels=61"

    curl "$r2l4ie/connect?node=r2l4ie&port1=4101&port2=4201&channels=61"
    curl "$r2l5ie/connect?node=r2l5ie&port1=4101&port2=4201&channels=61"
    curl "$r2l4ie/connect?node=r2l4ie&port1=5101&port2=5201&channels=61"
    curl "$r2l5ie/connect?node=r2l5ie&port1=5101&port2=5201&channels=61"

    curl "$r3l6ie/connect?node=r3l6ie&port1=4101&port2=4201&channels=61"
    curl "$r3l7ie/connect?node=r3l7ie&port1=4101&port2=4201&channels=61"
    curl "$r3l6ie/connect?node=r3l6ie&port1=5101&port2=5201&channels=61"
    curl "$r3l7ie/connect?node=r3l7ie&port1=5101&port2=5201&channels=61"

    echo '*** Installing ROADM configuration US (REST)'

    curl "$r1l1us/connect?node=r1l1us&port1=4101&port2=4201&channels=61"
    curl "$r1l2us/connect?node=r1l2us&port1=4101&port2=4201&channels=61"
    curl "$r1l3us/connect?node=r1l3us&port1=4101&port2=4201&channels=61"
    curl "$r1l1us/connect?node=r1l1us&port1=5101&port2=5201&channels=61"
    curl "$r1l2us/connect?node=r1l2us&port1=5101&port2=5201&channels=61"
    curl "$r1l3us/connect?node=r1l3us&port1=5101&port2=5201&channels=61"

    curl "$r2l4us/connect?node=r2l4us&port1=4101&port2=4201&channels=61"
    curl "$r2l5us/connect?node=r2l5us&port1=4101&port2=4201&channels=61"
    curl "$r2l4us/connect?node=r2l4us&port1=5101&port2=5201&channels=61"
    curl "$r2l5us/connect?node=r2l5us&port1=5101&port2=5201&channels=61"

    curl "$r3l6us/connect?node=r3l6us&port1=4101&port2=4201&channels=61"
    curl "$r3l7us/connect?node=r3l7us&port1=4101&port2=4201&channels=61"
    curl "$r3l6us/connect?node=r3l6us&port1=5101&port2=5201&channels=61"
    curl "$r3l7us/connect?node=r3l7us&port1=5101&port2=5201&channels=61"
}


# ROADM configuration 1: srv1_co1<->srv1_lg1 connection - NETCONF version

addc=$testdir/nc_add_connection.py
r1l1ie_netconf=localhost:1831
r1l2ie_netconf=localhost:1832
r1l3ie_netconf=localhost:1833
r2l4ie_netconf=localhost:1834
r2l5ie_netconf=localhost:1835
r3l6ie_netconf=localhost:1836
r3l7ie_netconf=localhost:1837

r1l1us_netconf=localhost:1841
r1l2us_netconf=localhost:1842
r1l3us_netconf=localhost:1843
r2l4us_netconf=localhost:1844
r2l5us_netconf=localhost:1845
r3l6us_netconf=localhost:1846
r3l7us_netconf=localhost:1847



# Configure Transponders and transceivers (bidirectional connections)
echo '*** Configuring Tera transponders and transceivers'
curl "$teraie/connect?node=teraie&ethPort=1&wdmPort=1&channel=61"
curl "$teraie/connect?node=teraie&ethPort=1&wdmPort=2&channel=61"
curl "$teraus/connect?node=teraus&ethPort=1&wdmPort=1&channel=61"
curl "$teraus/connect?node=teraus&ethPort=1&wdmPort=2&channel=61"


curl "$polatisie/connect?node=polatisie&wdmPort=2&wdmPort=11&channel=61"
curl "$polatisie/connect?node=polatisie&wdmPort=5&wdmPort=14&channel=61"
curl "$polatisie/connect?node=polatisie&wdmPort=6&wdmPort=17&channel=61"


curl "$teraie/turn_on?node=teraie"
curl "$teraus/turn_on?node=teraus"

    
# Configure server interfaces (using 'm' command)
echo '*** Configuring servers \n'
$m serverie ifconfig serverie-eth0 192.168.1.1/24
$m serverus ifconfig serverus-eth0 192.168.1.2/24
$m crossatl1 ifconfig crossatl1-eth1 192.168.1.3/24
$m crossatl2 ifconfig crossatl2-eth1 192.168.1.4/24
$m  servermmw ifconfig  servermmw-eth1 192.168.1.5/24

echo '*** Configuration'
connect1rest




echo '*** Done.'

