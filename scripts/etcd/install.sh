#!/bin/bash

# Constants
NEWLINE="echo """
USERNAME="pi_user"
TEMPLATE="192.168.1.12"
PASSWORD="tolga.halit.batu"

# Commands
GET="wget -q --show-progress --https-only --timestamping \"https://github.com/coreos/etcd/releases/download/v3.5.0/etcd-v3.5.0-linux-arm64.tar.gz\""
UNZIP="tar -xvf etcd-v3.5.0-linux-arm64.tar.gz"
MOVE="sudo mv etcd-v3.5.0-linux-arm64/etcd* /usr/local/bin/"
CHECK="etcd --version"
EXIT="exit"

# Parse arguments
while getopts :as:f: flag ; do
    case "${flag}" in
        a) START=0; FINISH=9;;
        s) START=${OPTARG};;
        f) FINISH=${OPTARG};;
    esac
done

# Start pire-store clients
while [ $START -le $FINISH ] ; do
    NODE_NAME="node-0$START"
    HOSTNAME=$TEMPLATE$START
    SCRIPT="$GET;$UNZIP;$MOVE;$EXIT"

	$NEWLINE
	echo "---------------------------------"
	echo "SSH Connection with $NODE_NAME"
	echo "---------------------------------"

	sshpass -p $PASSWORD ssh $USERNAME@$HOSTNAME $SCRIPT

    echo "[Seagull Server Machine] etcd-v3.5.0 is installed."
    START=$(($START+1))
done