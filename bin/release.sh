#!/bin/bash
#
# Simple script to package up the TT SDK as an 
# installable UF2 for the RP2040
#
# Copyright (C) 2024 Pat Deegan, https://psychogenic.com
#
# To run:
#  1) ensure you have uf2utils
#     pip install uf2utils
#  2) run from top dir using
#     ./bin/release.sh VERSION [SDKSRCDIR]
#     e.g.
#     ./bin/release.sh 1.2.4
#     or
#     ./bin/release.sh 1.2.4 /path/to/sdk/src
#
#


RPOS_UF2FILE=RPI_PICO-20240222-v1.22.2.uf2
TT_RUNS_SUPPORTED="tt03p5 tt04 tt05 tt06"

VERSION=$1
SRCDIR=$2

# check for uf2utils
UF2INFOPATH=`which uf2info`
if [ "$?" == "1" ]
then
	echo "uf2utils is required (https://pypi.org/project/uf2utils/)"
	exit 1
fi

# check version was specified
if [ "x$VERSION" == "x" ]
then
	echo "USAGE: $0 VERSION [SDKSRCDIR]"
	exit 2
fi

# check and test source dir
if [ "x$SRCDIR" == "x" ]
then
	SRCDIR=./src
fi

if [ -d $SRCDIR ]
then
	echo "Using SDK from $SRCDIR"
else
	echo "Can't find SDK in $SRCDIR"
	exit 3
fi

# create some temp stuff
BUILDDIR=`mktemp -d -t ttupython-XXXXX`
RPUF2=`mktemp -t rp2-pico-XXXX.uf2`

echo "Download $RPOS_UF2FILE"
wget -O $RPUF2 -c "https://micropython.org/resources/firmware/$RPOS_UF2FILE"

echo "Download shuttles for $TT_RUNS_SUPPORTED"
mkdir $BUILDDIR/shuttles
for chip in $TT_RUNS_SUPPORTED; do wget -O $BUILDDIR/shuttles/$chip.json "https://index.tinytapeout.com/$chip.json?fields=repo,address,commit,clock_hz,title"; done
touch $BUILDDIR/release_$VERSION

echo "Including SDK from $SRCDIR"
cp -Ra $SRCDIR/* $BUILDDIR
for pcd in `find $BUILDDIR -type d -name "__pycache__"`
do
	echo "cleaning up $pcd"
	rm -rf $pcd
done


echo "Generating UF2"
OUTFILE=/tmp/tt-demo-rp2040-$VERSION.uf2
python -m uf2utils.examples.custom_pico --fs_root $BUILDDIR --upython $RPUF2 --out $OUTFILE
echo
uf2info $OUTFILE

rm -rf $BUILDDIR
rm $RPUF2
echo
echo "Done: $OUTFILE created"
echo 
exit 0
