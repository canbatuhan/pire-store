#!/bin/bash

# Constants
NEWLINE="echo """
USERNAME="pi_user"
TEMPLATE="192.168.1.12"
PASSWORD="tolga.halit.batu"

# Commands
CD="cd /home/batuhan"
REMOVE="sudo rm -rf pire-store"
EXIT="exit"

# Script to execute
SCRIPT="$CD;$REMOVE;$EXIT"

# Parse arguments
while getopts :as:f: flag ; do
    case "${flag}" in
        a) START=0; FINISH=9;;
        s) START=${OPTARG};;
        f) FINISH=${OPTARG};;
    esac
done

# Clone pire-store
while [ $START -le $FINISH ] ; do
    NODE_NAME="node-0$START"
    HOSTNAME=$TEMPLATE$START

	$NEWLINE
	echo "---------------------------------"
	echo "SSH Connection with $NODE_NAME..."
	echo "---------------------------------"

	sshpass -p $PASSWORD ssh $USERNAME@$HOSTNAME $SCRIPT
    echo "[Seagull Server Machine] > 'pire-store' codes are removed."
    START=$(($START+1))
done