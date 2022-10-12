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
rdm1lg1=localhost:8080
rdm2lg1=localhost:8080
rdm2co1=localhost:8080
rdm1co1=localhost:8080
swda_co1=localhost:8080
swda_lg1=localhost:8080
comb1=localhost:8080
comb2=localhost:8080

ch1=($(seq 10 1 19))
ch2=($(seq 40 1 49))
ch3=($(seq 80 1 89))
comb_src_range=( "${ch1[@]}" "${ch2[@]}" "${ch3[@]}" )

# Helper script for sending commands to servers
m=../mininet/util/m

# Helper function: send gratuitous arps from all servers
arp () {
    echo '*** Sending gratuitous ARPs'
    $m srv1_co1 arping -c 1 -U -I srv1_co1-eth0 192.168.1.1
    $m srv1_lg1 arping -c 1 -U -I srv1_lg1-eth0 192.168.1.2
    $m srv2_lg1 arping -c 1 -U -I srv2_lg1-eth0 192.168.1.3
}

# Reset ROADM configurations
reset() {
    echo '*** Resetting ROADMs'
    curl "$rdm1co1/reset?node=rdm1co1"
    curl "$rdm1lg1/reset?node=rdm1lg1"
    curl "$rdm2lg1/reset?node=rdm2lg1"
    curl "$rdm2co1/reset?node=rdm2co1"
}

# ROADM configuration 1: srv1_co1<->srv1_lg1 connection - REST version

connect1rest() {
    echo '*** Installing ROADM configuration 1 for srv1_co1<->srv1_lg1 (REST)'

    for ch in "${comb_src_range[@]}";
    do
        curl "$rdm1co1/connect?node=rdm1co1&port1=4101&port2=4201&channels=$ch"
        curl "$rdm2co1/connect?node=rdm2co1&port1=4101&port2=4201&channels=$ch"
    done

    curl "$rdm1co1/connect?node=rdm1co1&port1=4102&port2=4201&channels=61"
    curl "$rdm1co1/connect?node=rdm1co1&port1=5101&port2=5202&channels=61"
    curl "$rdm1lg1/connect?node=rdm1lg1&port1=4102&port2=4201&channels=61"
    curl "$rdm1lg1/connect?node=rdm1lg1&port1=5101&port2=5202&channels=61"
}

# ROADM configuration 1: srv1_co1<->srv1_lg1 connection - NETCONF version

addc=$testdir/nc_add_connection.py
rdm1co1_netconf=localhost:1834
rdm1lg1_netconf=localhost:1831
rdm2lg1_netconf=localhost:1832
rdm2co1_netconf=localhost:1833
connect1netconf() {
    echo '*** Installing ROADM configuration 1 for srv1_co1<->srv1_lg1 (NETCONF)'

    $addc $rdm1co1_netconf 1 10 in-service false 4101 4201 191750 192300 5 Exp1-FromComb1-Band1
    $addc $rdm2co1_netconf 1 10 in-service false 4101 4201 191750 192300 5 Exp1-FromComb2-Band1

    $addc $rdm1co1_netconf 1 10 in-service false 4101 4201 193250 193800 5 Exp1-FromComb1-Band2
    $addc $rdm2co1_netconf 1 10 in-service false 4101 4201 193250 193800 5 Exp1-FromComb2-Band2

    $addc $rdm1co1_netconf 1 10 in-service false 4101 4201 195250 195800 5 Exp1-FromComb1-Band3
    $addc $rdm2co1_netconf 1 10 in-service false 4101 4201 195250 195800 5 Exp1-FromComb2-Band3

    $addc $rdm1co1_netconf 1 10 in-service false 4102 4201 194300 194400 5 Exp1_From_sw-da-co1
    $addc $rdm1co1_netconf 2 10 in-service false 5101 5202 194300 194400 5 Exp1-Toward_sw-da_co1
    $addc $rdm1lg1_netconf 1 10 in-service false 4102 4201 194300 194400 5 Exp1_From_sw-da-lg1
    $addc $rdm1lg1_netconf 2 10 in-service false 5101 5202 194300 194400 5 Exp1_Toward_sw-da-lg1
}

# ROADM configuration 2: srv1_co1<->srv2_lg1 connection - REST version

connect2rest() {
    echo '*** Installing ROADM configuration 1 for srv1_co1<->srv2_lg1'

    for ch in "${comb_src_range[@]}";
    do
        curl "$rdm1co1/connect?node=rdm1co1&port1=4101&port2=4201&channels=$ch"
        curl "$rdm1lg1/connect?node=rdm1lg1&port1=4111&port2=4201&channels=$ch"
        curl "$rdm2lg1/connect?node=rdm2lg1&port1=5101&port2=5211&channels=$ch"
        curl "$rdm2co1/connect?node=rdm2co1&port1=4101&port2=4201&channels=$ch"
        curl "$rdm1lg1/connect?node=rdm1lg1&port1=5101&port2=5211&channels=$ch"
        curl "$rdm2lg1/connect?node=rdm2lg1&port1=4111&port2=4201&channels=$ch"
    done

    # rdm1co1: same as connection 1
    curl "$rdm1co1/connect?node=rdm1co1&port1=4102&port2=4201&channels=61"
    curl "$rdm1co1/connect?node=rdm1co1&port1=5101&port2=5202&channels=61"
    # rdm1lg1: through connection
    curl "$rdm1lg1/connect?node=rdm1lg1&port1=4111&port2=4201&channels=61"
    curl "$rdm1lg1/connect?node=rdm1lg1&port1=5101&port2=5211&channels=61"
    # rdm2lg1: through connection
    curl "$rdm2lg1/connect?node=rdm2lg1&port1=4111&port2=4201&channels=61"
    curl "$rdm2lg1/connect?node=rdm2lg1&port1=5101&port2=5211&channels=61"
    # rdm2co1: same as rdm1co1
    curl "$rdm2co1/connect?node=rdm2co1&port1=4102&port2=4201&channels=61"
    curl "$rdm2co1/connect?node=rdm2co1&port1=5101&port2=5202&channels=61"
}

# ROADM configuration 2: srv1_co1<->srv2_lg1 connection - NETCONF version

connect2netconf() {
    echo '*** Installing ROADM configuration 1 for srv1_co1<->srv2_lg1'

    $addc $rdm1co1_netconf 1 10 in-service false 4101 4201 191750 192300 5 Exp2-FromComb1-Band1
    $addc $rdm2co1_netconf 1 10 in-service false 4101 4201 191750 192300 5 Exp2-FromComb2-Band1

    $addc $rdm1co1_netconf 1 10 in-service false 4101 4201 193250 193800 5 Exp2-FromComb1-Band2
    $addc $rdm2co1_netconf 1 10 in-service false 4101 4201 193250 193800 5 Exp2-FromComb2-Band2

    $addc $rdm1co1_netconf 1 10 in-service false 4101 4201 195250 195800 5 Exp2-FromComb1-Band3
    $addc $rdm2co1_netconf 1 10 in-service false 4101 4201 195250 195800 5 Exp2-FromComb2-Band3

    $addc $rdm1lg1_netconf 1 10 in-service false 4111 4201 191750 192300 5 Exp2-Rdm1Pass-Band1
    $addc $rdm2lg1_netconf 2 10 in-service false 5101 5211 191750 192300 5 Exp2-Rdm2Pass-Band1

    $addc $rdm1lg1_netconf 1 10 in-service false 4111 4201 193250 193800 5 Exp2-Rdm1Pass-Band2
    $addc $rdm2lg1_netconf 2 10 in-service false 5101 5211 193250 193800 5 Exp2-Rdm2Pass-Band2

    $addc $rdm1lg1_netconf 1 10 in-service false 4111 4201 195250 195800 5 Exp2-Rdm1Pass-Band3
    $addc $rdm2lg1_netconf 2 10 in-service false 5101 5211 195250 195800 5 Exp2-Rdm2Pass-Band3

    $addc $rdm1lg1_netconf 2 10 in-service false 5101 5211 191750 192300 5 Exp2-Rdm1Pass-Band1
    $addc $rdm2lg1_netconf 1 10 in-service false 4111 4201 191750 192300 5 Exp2-Rdm2Pass-Band1

    $addc $rdm1lg1_netconf 2 10 in-service false 5101 5211 193250 193800 5 Exp2-Rdm1Pass-Band2
    $addc $rdm2lg1_netconf 1 10 in-service false 4111 4201 193250 193800 5 Exp2-Rdm2Pass-Band2

    $addc $rdm1lg1_netconf 2 10 in-service false 5101 5211 195250 195800 5 Exp2-Rdm1Pass-Band3
    $addc $rdm2lg1_netconf 1 10 in-service false 4111 4201 195250 195800 5 Exp2-Rdm2Pass-Band3

    # rdm1co1: same as connection 1
    $addc $rdm1co1_netconf 1 10 in-service false 4102 4201 194300 194400 5 Exp2_From_sw-da-co1
    $addc $rdm1co1_netconf 2 10 in-service false 5101 5202 194300 194400 5 Exp2_Toward_sw-da-co1
    # rdm1lg1: passthrough connections
    $addc $rdm1lg1_netconf 1 10 in-service false 4111 4201 194300 194400 5 Exp2_East_rdm1-lg1
    $addc $rdm1lg1_netconf 2 10 in-service false 5101 5211 194300 194400 5 Exp2_West_rdm1-lg1
    # rdm2lg1: passthrough connections
    $addc $rdm2lg1_netconf 1 10 in-service false 4111 4201 194300 194400 5 Exp2_East_rdm2-lg1
    $addc $rdm2lg1_netconf 2 10 in-service false 5101 5211 194300 194400 5 Exp2_West_rdm2-lg1
    # rdm2co1: same as rdm1co1
    $addc $rdm2co1_netconf 1 10 in-service false 4102 4201 194300 194400 5 Exp2_From_sw-da-lg1
    $addc $rdm2co1_netconf 2 10 in-service false 5101 5202 194300 194400 5 Exp2_Toward_sw-da_lg1
}

# Configure ToR switches and transceivers (bidirectional connections)
echo '*** Configuring ToR switches and transceivers'
curl "$swda_co1/connect?node=swda-co1&ethPort=1&wdmPort=320&wdmInPort=321&channel=61"
curl "$swda_lg1/connect?node=swda-lg1&ethPort=2&wdmPort=290&wdmInPort=291&channel=61"
curl "$swda_lg1/connect?node=swda-lg1&ethPort=3&wdmPort=310&wdmInPort=311&channel=61"
curl "$swda_co1/turn_on?node=swda-co1"
curl "$swda_lg1/turn_on?node=swda-lg1"
curl "$comb1/turn_on?node=comb1"
curl "$comb2/turn_on?node=comb2"
    
# Configure server interfaces (using 'm' command)
echo '*** Configuring servers \n'
$m srv1_co1 ifconfig srv1_co1-eth0 192.168.1.1/24
$m srv1_lg1 ifconfig srv1_lg1-eth0 192.168.1.2/24
$m srv2_lg1 ifconfig srv2_lg1-eth0 192.168.1.3/24

test() {
    arp
    echo '*** srv1_co1 pinging srv1_lg1'
    $m srv1_co1 ping -c3 192.168.1.2
    echo '*** srv1_co1 pinging srv2_lg1'
    $m srv1_co1 ping -c3 192.168.1.3
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

