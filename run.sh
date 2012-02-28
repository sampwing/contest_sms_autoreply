#!/bin/bash
count=0

while :
do
   echo "Starting."
   python ./sms.py &> ./log_$count.txt
   echo "Crashed."
   count=$(( $count + 1 ))
   sleep 5
done
