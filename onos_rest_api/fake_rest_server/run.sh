#!/bin/bash

a=9000
for i in $(eval echo {1..$1});
do
   sum=$(( $a + $i))
   fuser -k $sum/tcp
   python rest_server.py "$sum" &
done
