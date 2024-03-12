#!/bin/bash

# Constants
NEWLINE="echo """
PASSWORD="tolga.halit.batu"
USERNAME="pi_user"
TEMPLATE="192.168.1.12"

# Parse arguments
while getopts :n: flag ; do
    case "${flag}" in
        n) NODE=${OPTARG};;
    esac
done

SLEEP="sleep 3"
CD="cd /home/batuhan/pire-store"
PROXY_START="python ./scripts/zookeeper/zkproxy.py"
EXIT="exit"
SCRIPT="$SLEEP;$CD;$PROXY_START;$EXIT"

# Start ZooKeeper Servers
NODE_NAME="node-0$NODE"
HOSTNAME=$TEMPLATE$NODE

$NEWLINE
echo "---------------------------------"
echo "SSH Connection with $NODE_NAME"
echo "---------------------------------"

sshpass -p $PASSWORD ssh $USERNAME@$HOSTNAME $SCRIPT