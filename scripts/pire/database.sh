#!/bin/bash

# Constants
NEWLINE="echo """
USERNAME="pi_user"
TEMPLATE="192.168.1.12"
PASSWORD="tolga.halit.batu"

# Commands
CD="cd /home/batuhan/pire-store"
DISPLAY="sudo cat local.db"
EXIT="exit"

# Script to execute
SCRIPT="$CD;$DISPLAY;$EXIT"

# Parse arguments
while getopts :an: flag ; do
    case "${flag}" in
        a) START=0; FINISH=9;;
        n) START=${OPTARG}; FINISH=$START;;
    esac
done

# Dispaly logs
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