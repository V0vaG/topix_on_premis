#!/bin/bash

ver=$1

pod_num=$2

sed -i "s/ver_num/$ver/g" ./run.sh

sed -i "s/pod_num/$pod_num/g" ./run.sh

cat ./run.sh

