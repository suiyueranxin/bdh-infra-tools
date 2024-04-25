#!/bin/sh

set -ex

if [ -z $MAX_RUN ]; then
    max_run_time=3
else
    max_run_time=$MAX_RUN
fi

i=0
while :
do
    set +e
    /project/entrypoint.sh
    test_result=$?
    set -e

    if [ $test_result -eq 0 ]; then
        exit 0
    else
        i=$(($i+1))
	if [ $i -lt $max_run_time ]; then
            echo "## Test execution failed, rerun test ..."
	    rm -rf /infrabox/upload/testresult/*
	    mkdir /project/rerun_$i
	    cd /project/rerun_$i
	else
            echo "## Test execution failed after run "$max_run_time" times!"
	    exit 1
	fi
    fi
    
done
