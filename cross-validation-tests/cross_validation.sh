#!/bin/bash

###################### Description - start ######################
#
#    Aug 27, 2021
#
#    This script coordinates the execution of simulation tests using
#    Mininet-Optical and GNPy. The process is divided in the following steps:
#
#    1. Install dependencies
#    2. Run Mininet-Optical tests and log data.
#    3. Download the GNPy project in a subdirectory "../../gnpy-cross-validation".
#    4. Apply patches to GNPy files
#    5. Run GNPy tests and log data.
#    6. Run cross-validation analysis.
#    7. Clean log files (comment or remove this if you want to examine the files).
#
#
###################### Description - end ######################





###################### Install dependencies - start ######################
echo "Installing dependencies..."
pip install pandas
###################### Install dependencies - start ######################




###################### Mininet-Optical tests - start ######################
# Mininet-Optical directory
MO_DIR="optical-network-emulator"

# Run Mininet-Optical tests to create datafile
echo "Running Mininet-Optical tests..."
PYTHONPATH=.. python auto_tests.py
###################### Mininet-Optical tests - end ######################




###################### Cloning GNPy to subdirectory - start ######################
# Root directory for GNPy project (outside of Mininet-Optical)
GNPY_DIR="../../gnpy-cross-validation"

# Check if folder GNPY_DIR exists, if not, create and clone GNPy
if [ -d $GNPY_DIR ]
then
    echo "Directory $GNPY_DIR already exists."
else
    echo "Creating folder $GNPY_DIR and cloning GNPy project into it."
    mkdir $GNPY_DIR
    git clone https://github.com/Telecominfraproject/oopt-gnpy.git $GNPY_DIR
fi
###################### Cloning GNPy to subdirectory - end ######################




###################### Preparation for applying patches - start ######################
# Files to patch
cd $GNPY_DIR
ELEMENTS_FILE="gnpy/core/elements.py"
EQPT_FILE="tests/data/eqpt_config.json"

# Directory to patches and files from patches
CROSS_VAL_DIR="../$MO_DIR/cross-validation-tests"
PATCHES_DIR="$CROSS_VAL_DIR/patches"
GNPY_FILES_DIR="$CROSS_VAL_DIR/gnpy-files"
GNPY_TESTS_DIR="$CROSS_VAL_DIR/gnpy-mytests"

# Files from patches
P_ELEMENTS_FILE="$GNPY_FILES_DIR/elements.py"
P_EQPT_FILE="$GNPY_FILES_DIR/eqpt_config.json"

# Patches
ELEMENTS_PATCH="$PATCHES_DIR/elementspatch.patch"
EQPT_PATCH="$PATCHES_DIR/eqptpatch.patch"
###################### Preparation for applying patches - end ######################




###################### Applying patches - start ######################
# Apply patches
ELEMENTS_DIFF_COUNT=$(diff $ELEMENTS_FILE $P_ELEMENTS_FILE | wc -l)
if (( $ELEMENTS_DIFF_COUNT > 0))
then
    echo "Applying $ELEMENTS_PATCH to $ELEMENTS_FILE"
    patch $ELEMENTS_FILE $ELEMENTS_PATCH
else
    echo "Patch for $ELEMENTS_FILE already applied."
fi

EQPT_DIFF_COUNT=$(diff $EQPT_FILE $P_EQPT_FILE | wc -l)
if (( $EQPT_DIFF_COUNT > 0 ))
then
    echo "Applying $EQPT_PATCH to $EQPT_FILE"
    patch $EQPT_FILE $EQPT_PATCH
else
    echo "Patch for $EQPT_FILE already applied."
fi
###################### Applying patches - end ######################




###################### GNPy tests - start ######################
# Create directory for running tests
TEST_DIR="gnpy-mytests"
if [ -d $TEST_DIR ]
then
    echo "gnpy-mytests directory already exists."
else
    echo "Creating $TEST_DIR directory."
    mkdir $TEST_DIR
    cp $GNPY_TESTS_DIR/* $TEST_DIR
fi

cd $TEST_DIR
echo "Running GNPy tests..."
PYTHONPATH=../ python auto_tests.py
###################### GNPy tests - end ######################




###################### Cross-validation analysis - start ######################
cd ../$CROSS_VAL_DIR
echo "Running cross-validation analysis..."
python cross_val_test.py
###################### Cross-validation analysis - end ######################




###################### Clean files - start ######################
echo "Removing test files..."
rm mo_tests.csv
rm $GNPY_DIR/$TEST_DIR/gnpy_tests.csv
###################### Clean files - end ######################
