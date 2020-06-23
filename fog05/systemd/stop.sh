#!/bin/bash

sudo systemctl stop fos_lxd

sleep 1

sudo systemctl stop fos_linuxbridge

sleep 1

sudo systemctl stop fos_linux

sleep 1

sudo systemctl stop fos_agent

sleep 1

sudo systemctl stop zenoh
