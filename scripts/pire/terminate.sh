#!/bin/bash

# Constants
NEWLINE="echo """
PASSWORD="tolga.halit.batu"
USERNAME="pi_user"
TEMPLATE="192.168.1.12"
PORT=9000

# Commands
KILL="pkill -9 python"
CLOSE="fuser -k -n tcp $PORT"
EXIT="exit"

# Script to execute
SCRIPT="$KILL;$CLOSE;$EXIT"

# Parse arguments
while getopts :as:f: flag ; do
    case "${flag}" in
        a) START=0; FINISH=9;;
        s) START=${OPTARG};;
        f) FINISH=${OPTARG};;
    esac
done

# Terminate pire-store clients
while [ $START -le $FINISH ] ; do
    NODE_NAME="node-0$START"
    HOSTNAME=$TEMPLATE$START

	$NEWLINE
	echo "---------------------------------"
	echo "SSH Connection with $NODE_NAME"
	echo "---------------------------------"
	
    sshpass -p $PASSWORD ssh $USERNAME@$HOSTNAME $SCRIPT
    echo "[Seagull Server Machine] > All 'python' processes are killed."
    START=$(($START+1))
done