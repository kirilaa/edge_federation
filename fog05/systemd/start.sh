#!/bin/bash

sudo systemctl start zenoh

sleep 1

sudo systemctl start fos_agent

sleep 1

sudo systemctl start fos_linux

sleep 1

sudo systemctl start fos_linuxbridge

sleep 1

sudo systemctl start fos_lxd
