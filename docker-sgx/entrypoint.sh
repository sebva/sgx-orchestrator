#!/bin/bash

source /opt/intel/sgxsdk/environment

jhid -d
/opt/intel/sgxpsw/aesm/aesm_service &
pid=$!

trap "kill ${pid}" TERM INT

sleep 2

exec "$@"
