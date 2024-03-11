#!/bin/bash

# Constants
NEWLINE="echo """
PASSWORD="tolga.halit.batu"
USERNAME="pi_user"
TEMPLATE="192.168.1.12"

# Parse arguments
while getopts :as:f: flag ; do
    case "${flag}" in
        a) START=0; FINISH=9;;
        s) START=${OPTARG};;
        f) FINISH=${OPTARG};;
    esac
done

ZK_START="sudo service zookeeper start"
CD="cd /home/batuhan/pire-store"
PROXY_START="python ./scripts/zookeeper/zkproxy.py"
EXIT="exit"
SCRIPT="$ZK_START;$CD;$PROXY_START;$EXIT"

# Start ZooKeeper Servers
while [ $START -le $FINISH ] ; do
    NODE_NAME="node-0$START"
    HOSTNAME=$TEMPLATE$START

	$NEWLINE
	echo "---------------------------------"
	echo "SSH Connection with $NODE_NAME"
	echo "---------------------------------"

	sshpass -p $PASSWORD ssh $USERNAME@$HOSTNAME $SCRIPT
    START=$(($START+1))
done