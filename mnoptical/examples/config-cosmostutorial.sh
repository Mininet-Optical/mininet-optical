#!/bin/bash

testdir=$(dirname $0)

# config-cosmostutorial.sh:
#
# This is for the tutorial at:
# https://wiki.cosmos-lab.org/wiki/Tutorials/Optical/MininetOpticalTutorial1
#
# This script configures the tutorial network in two
# configurations. The first configuration connects server1
# and server2, while the second configuration connects
# server1 and server3

# REST ports for network components
roadm1=localhost:8080
roadm2=localhost:8080
roadm3=localhost:8080
roadm4=localhost:8080
tor1=localhost:8080
tor2=localhost:8080
tor3=localhost:8080

# Helper script for sending commands to servers
m=~/mininet/util/m

# Helper function: send gratuitous arps from all servers
arp () {
    echo '*** Sending gratuitous ARPs'
    for i in 1 2 3; do
        $m server$i arping -c 1 -U -I server$i-eth0 192.168.1.$i
    done
}

# Reset ROADM configurations
reset() {
    echo '*** Resetting ROADMs'
    curl "$roadm1/reset?node=roadm1"
    curl "$roadm2/reset?node=roadm2"
    curl "$roadm3/reset?node=roadm3"
    curl "$roadm4/reset?node=roadm4"
}

# ROADM configuration 1: tor1<->tor2 connection - REST version

connect1rest() {
    echo '*** Installing ROADM configuration 1 for tor1<->tor2 (REST)'
    curl "$roadm4/connect?node=roadm4&port1=4102&port2=4201&channels=34"
    curl "$roadm4/connect?node=roadm4&port1=5101&port2=5202&channels=34"
    curl "$roadm1/connect?node=roadm1&port1=4102&port2=4201&channels=34"
    curl "$roadm1/connect?node=roadm1&port1=5101&port2=5202&channels=34"
}

# ROADM configuration 1: tor1<->tor2 connection - NETCONF version

addc=$testdir/nc_add_connection.py
r1=localhost:1831
r2=localhost:1832
r3=localhost:1833
r4=localhost:1834
connect1netconf() {
    echo '*** Installing ROADM configuration 1 for tor1<->tor2 (NETCONF)'
    $addc $r4 1 10 in-service false 4102 4201 192950 193050 5 Exp1-FromTor1
    $addc $r4 2 10 in-service false 5101 5202 192950 193050 5 Exp1-TorwardTor1
    $addc $r1 1 10 in-service false 4102 4201 192950 193050 5 Exp1-FromTor2
    $addc $r1 2 10 in-service false 5101 5202 192950 193050 5 Exp1-TorwardTor2
}

# ROADM configuration 2: tor1<->tor3 connection - REST version

connect2rest() {
    echo '*** Installing ROADM configuration 1 for tor1<->tor3'
    # roadm4: same as connection 1
    curl "$roadm4/connect?node=roadm4&port1=4102&port2=4201&channels=34"
    curl "$roadm4/connect?node=roadm4&port1=5101&port2=5202&channels=34"
    # roadm1: through connection
    curl "$roadm1/connect?node=roadm1&port1=4101&port2=4201&channels=34"
    curl "$roadm1/connect?node=roadm1&port1=5101&port2=5201&channels=34"
    # roadm2: through connection
    curl "$roadm2/connect?node=roadm2&port1=4101&port2=4201&channels=34"
    curl "$roadm2/connect?node=roadm2&port1=5101&port2=5201&channels=34"
    # roadm3: same as roadm4
    curl "$roadm3/connect?node=roadm3&port1=4102&port2=4201&channels=34"
    curl "$roadm3/connect?node=roadm3&port1=5101&port2=5202&channels=34"
}

# ROADM configuration 2: tor1<->tor3 connection - NETCONF version

connect2netconf() {
    echo '*** Installing ROADM configuration 1 for tor1<->tor3'
    # roadm4: same as connection 1
    $addc $r4 1 10 in-service false 4102 4201 192950 193050 5 Exp1-FromTor1
    $addc $r4 2 10 in-service false 5101 5202 192950 193050 5 Exp1-TorwardTor1
    # roadm1: passthrough connections
    $addc $r1 1 10 in-service false 4101 4201 192950 193050 5 Exp1-EastR1
    $addc $r1 2 10 in-service false 5101 5201 192950 193050 5 Exp1-WestR1
    # roadm2: passthrough connections
    $addc $r2 1 10 in-service false 4101 4201 192950 193050 5 Exp1-WestR2
    $addc $r2 2 10 in-service false 5101 5201 192950 193050 5 Exp1-EastR2
    # roadm3: same as roadm4
    $addc $r3 1 10 in-service false 4102 4201 192950 193050 5 Exp1-FromTor2
    $addc $r3 2 10 in-service false 5101 5202 192950 193050 5 Exp1-TorwardTor2
}

# Configure ToR switches and transceivers (bidirectional connections)
echo '*** Configuring ToR switches and transceivers'
curl "$tor1/connect?node=tor1&ethPort=1&wdmPort=320&wdmInPort=321&channel=34"
curl "$tor2/connect?node=tor2&ethPort=2&wdmPort=290&wdmInPort=291&channel=34"
curl "$tor3/connect?node=tor3&ethPort=3&wdmPort=310&wdmInPort=311&channel=34"
curl "$tor1/turn_on?node=tor1"
curl "$tor2/turn_on?node=tor2"
curl "$tor3/turn_on?node=tor3"
    
# Configure server interfaces (using 'm' command)
echo '*** Configuring servers \n'
$m server1 ifconfig server1-eth0 192.168.1.1/24
$m server2 ifconfig server2-eth0 192.168.1.2/24
$m server3 ifconfig server3-eth0 192.168.1.3/24

test() {
    arp
    echo '*** server1 pinging server2'
    $m server1 ping -c3 192.168.1.2
    echo '*** server1 pinging server3'
    $m server1 ping -c3 192.168.1.3
}

echo '*** Base test before configuration'
echo -n 'press return to test base configuration> '
read line
test

echo '*** Test configuration 1'
echo -n 'press return to configure and test configuration 1> '
read line
connect1netconf
test

echo '*** Test configuration 2'
echo -n 'press return to configure and test configuration 2> '
read line
connect2netconf
test

echo '*** Done.'

