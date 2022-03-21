#!/bin/bash

rootdir=$(dirname $0)/../..

echo '*** Creating netconf server certs'
(cd ${rootdir} && make certs)

echo "*** Starting up hwtopo.py with netconf"
sudo HOME=~ PYTHONPATH=${rootdir} python3 -m mnoptical.ofcdemo.hwtopo
