#!/bin/bash

# Constants
NEWLINE="echo """
PASSWORD="tolga.halit.batu"
USERNAME="pi_user"
TEMPLATE="192.168.1.12"

# Commands
REMOVE="rm /var/lib/etcd/*"
REBOOT="sudo reboot"

# Script to execute
SCRIPT="$REMOVE;$REBOOT"

# Parse arguments
while getopts :as:f: flag ; do
    case "${flag}" in
        a) START=0; FINISH=9;;
        s) START=${OPTARG};;
        f) FINISH=${OPTARG};;
    esac
done

# Clear 'log.txt' and 'local.db'
while [ $START -le $FINISH ] ; do
    NODE_NAME="node-0$START"
    HOSTNAME=$TEMPLATE$START

	$NEWLINE
	echo "---------------------------------"
	echo "SSH Connection with $NODE_NAME"
	echo "---------------------------------"
	
    sshpass -p $PASSWORD ssh $USERNAME@$HOSTNAME $SCRIPT
    echo "[Seagull Server Machine] > etcd-cluster is killed."
    START=$(($START+1))
done