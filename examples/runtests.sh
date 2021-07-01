#!/bin/bash

# Exit on non-handled error
set -e

# Set necessary python path for execution
testdir=$(dirname $0)
timeout=60  # Fail test if it takes over 60s
run="env PYTHONPATH=$testdir/.. timeout $timeout python3"

# Accumulate passed and failed tests
tests=($testdir/*.py)
passed=()
failed=()

# Run all scripts in this directory
args='test'
for test in ${tests[@]}; do
    echo -e "**** Running $test\n"
    echo "$run $test $args"
    if $run $test $args < /dev/null; then
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
