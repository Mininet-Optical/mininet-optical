#!/bin/bash

set -e

cd `dirname $0`
driversrc=`pwd`
echo "* Looking for driver source in $driversrc"
ls $driversrc/roadm

onosver=2.4.0
archive=$onosver.tar.gz
echo "* Building for ONOS version $onosver"
builddir=`mktemp -d`

echo "* Building in $builddir"
pushd $builddir

url=https://github.com/opennetworkinglab/onos/archive/$archive
echo "* Fetching $url"
wget $url

echo "* Unpacking $archive"
tar xzf $archive

targetdir=$builddir/onos-$onosver/drivers/opticalemulator
echo "* Copying $driversrc into $targetdir"
cp -r $driversrc $targetdir

echo "* Building driver"
cd $targetdir
bazel build //drivers/opticalemulator/roadm:onos-drivers-opticalemulator-roadm-oar

echo "* Driver build complete"
echo "* Done"
