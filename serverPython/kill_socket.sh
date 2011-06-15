#!/bin/bash

pid=`netstat -tanpu | grep $1 | awk '{print $7}' | cut -d "/" -f 1`
kill $pid
