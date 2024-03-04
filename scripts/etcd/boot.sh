#!/bin/bash

# Constants
NEWLINE="echo """
PASSWORD="tolga.halit.batu"
USERNAME="pi_user"
TEMPLATE="192.168.1.12"

# etcd Constants
TOKEN="etcd-token-1"
CLUSTER_STATE="new"
CLUSTER_PORT="2380"
CLIENT_PORT="2379"

# etcd Node Names
NAME_0="etcd-node-00"
NAME_1="etcd-node-01"
NAME_2="etcd-node-02"
NAME_3="etcd-node-03"
NAME_4="etcd-node-04"

# etcd Node Hosts
HOST_0="192.168.1.120"
HOST_1="192.168.1.121"
HOST_2="192.168.1.122"
HOST_3="192.168.1.123"
HOST_4="192.168.1.124"

# etcd Cluster
CLUSTER="${NAME_0}=http://${HOST_0}:${CLUSTER_PORT},${NAME_1}=http://${HOST_1}:${CLUSTER_PORT},${NAME_2}=http://${HOST_2}:${CLUSTER_PORT},${NAME_3}=http://${HOST_3}:${CLUSTER_PORT},${NAME_4}=http://${HOST_4}:${CLUSTER_PORT}"

# Parse arguments
while getopts :n: flag ; do
    case "${flag}" in
        n) NODE_ID=${OPTARG};;
    esac
done

# Clear 'log.txt' and 'local.db'
NODE_NAME="node-0$NODE_ID"
HOSTNAME=$TEMPLATE$NODE_ID

$NEWLINE
echo "---------------------------------"
echo "SSH Connection with $NODE_NAME"
echo "---------------------------------"
	
ETCD_NODE_NAME="etcd-node-0${NODE_ID}"
CLUSTER_LISTENER="http://${HOSTNAME}:${CLUSTER_PORT}"
CLIENT_LISTENER="http://${HOSTNAME}:${CLIENT_PORT}"

START="etcd --name ${ETCD_NODE_NAME} --initial-advertise-peer-urls ${CLUSTER_LISTENER} --listen-peer-urls ${CLUSTER_LISTENER} --advertise-client-urls ${CLIENT_LISTENER} --listen-client-urls ${CLIENT_LISTENER} --initial-cluster ${CLUSTER} --initial-cluster-state ${CLUSTER_STATE} --initial-cluster-token ${TOKEN} --backend-batch-limit=1"

# Script to execute
SCRIPT="$START"
sshpass -p $PASSWORD ssh $USERNAME@$HOSTNAME $SCRIPT