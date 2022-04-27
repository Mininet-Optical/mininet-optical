#!/bin/bash

# Exit on non-handled error
set -e

# By default, test the version in this repo
testdir=$(dirname $0)
if [ ! -v PYTHONPATH ]; then
    export PYTHONPATH=$testdir/..
    echo "**** PYTHONPATH set to $PYTHONPATH"
fi

# Accumulate passed and failed tests
tests=($testdir/*.py)
passed=()
failed=()

# Run all scripts in this directory
for test in ${tests[@]}; do
    echo -e "**** Running $test\n"
    if python $test; then
        echo -e "\n**** PASSED: $test\n"
        passed+=($test)
    else
        echo -e "\n**** FAILED: $test\n"
        failed+=($test)
    fi
done

# Report results
echo -e "**** Test results:\n"

for test in ${passed[@]}; do
    echo "**** PASSED: $test"
done
echo
for test in ${failed[@]}; do
    echo "**** FAILED: $test"
done

# Succeed if no tests failed
passcount=${#passed[@]}
failcount=${#failed[@]}
echo
echo "**** $passcount tests passed"
echo "**** $failcount tests failed"
echo "**** Exiting with code $failcount."
exit $failcount
