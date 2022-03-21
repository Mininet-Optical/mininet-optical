#!/bin/bash

rootdir=$(dirname $0)/../..

echo '*** Running netconf controller against hwtopo'
PYTHONPATH=${rootdir} python3 -m mnoptical.ofcdemo.demo_hwtopo
