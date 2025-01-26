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


RPOS_UF2FILE=RPI_PICO-20241025-v1.24.0.uf2
TT_RUNS_SUPPORTED="unknown tt05 tt06 tt07 tt08"

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

if [ -e ./bin/serialize_shuttle.py ]
then 
	echo "Downloading and serializing shuttles"
else
	echo "Run this script from repo topdir, ./bin/release.sh"
fi
echo "Download shuttles for $TT_RUNS_SUPPORTED"
mkdir $SRCDIR/shuttles
for chip in $TT_RUNS_SUPPORTED; do echo "get shuttle $chip"; wget -O $SRCDIR/shuttles/$chip.json "https://index.tinytapeout.com/$chip.json?fields=address,clock_hz,title,danger_level"; done
for chip in $TT_RUNS_SUPPORTED; do echo "serialize $chip shuttle"; rm $SRCDIR/shuttles/$chip.json.bin; PYTHONPATH="./src/:./microcotb/src:$PYTHONPATH" python ./bin/serialize_shuttle.py $SRCDIR/shuttles/$chip.json; done

# create some temp stuff
BUILDDIR=`mktemp -d -t ttupython-XXXXX`
RPEXISTING=`ls /tmp/rp2-pico-????.uf2`

echo "Download $RPOS_UF2FILE"
if [ "x$RPEXISTING" == "x" ]
then
	RPUF2=`mktemp -t rp2-pico-XXXX.uf2`
	echo "Getting $RPOS_UF2FILE"
	wget -O $RPUF2 -c "https://micropython.org/resources/firmware/$RPOS_UF2FILE"
else
	echo "already have $RPOS_UF2FILE (as $RPEXISTING)"
	RPUF2=$RPEXISTING
fi

touch $BUILDDIR/release_v$VERSION

echo "Including SDK from $SRCDIR"
cp -Ra $SRCDIR/* $BUILDDIR
echo "Including microcotb"
cp -Ra $SRCDIR/../microcotb/src/microcotb $BUILDDIR
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
# echo $BUILDDIR
#rm $RPUF2
echo
echo "Done: $OUTFILE created"
echo 
exit 0
