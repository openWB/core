#!/bin/bash

# installing protobuf compiler protoc
# protoc version should not be too old!
# create temp folder
# mkdir proto; cd proto
# download zip file from release page for linux x86_64
# curl -LO $PB_REL/download/v25.1/protoc-25.1-linux-x86_64.zip
# download zip file from release page for linux arm_64
# curl -LO $PB_REL/download/v25.1/protoc-25.1-linux-aarch_64.zip
# unzip 
# unzip protoc-25.1-linux-x86_64.zip -d .
# install in /usr
# sudo cp bin/protoc /usr/bin/protoc
# sudo cp -r include/google/* /usr/include/google/



GEN_PATH="Gen_Proto_Python"
OWB_USER="openwb"
OWB_HOST="openwb2-alpha3"
OWB_PATH="~/openWB/packages/modules/vehicles/smarteq/proto"

# remove temp folders - will ge recreated by this script
rm -fr MBSDK-CarKit-iOS Proto $GEN_PATH

# create folder for generated python files
mkdir $GEN_PATH

# create folder for CarKit
mkdir MBSDK-CarKit-iOS
cd MBSDK-CarKit-iOS
git init
git remote add -f origin https://github.com/mercedes-benz/MBSDK-CarKit-iOS

# set sparse checkout, set to Proto only and checkout
git config core.sparseCheckout true
echo "Proto" >> .git/info/sparse-checkout
git pull origin master

# remove unrequired folder
rm -fr MBCarKit

# clone google protobuf repository
echo "cloning gogo/protobuf"
git clone https://github.com/gogo/protobuf "../Proto/github.com/gogo/protobuf" --branch v1.2.1 -q > /dev/null 2>&1 || true

# copy gogo.proto to CarKit Proto folder
cp ../Proto/github.com/gogo/protobuf/gogoproto/gogo.proto Proto

# fix path to gogo.proto in CarKit files
for f in `ls -1 Proto/*.proto | grep -v gogo.proto`
do
    echo "fix gogo path in $f"
    sed '/import .*gogo.proto/s/github.com\/gogo\/protobuf\/gogoproto\///' $f > $f.tmp
    mv $f.tmp $f
done

# generate python files from proto 
echo "generating proto"
protoc -I=./Proto --python_out=../$GEN_PATH ./Proto/*.proto

# modify generated files:
# - add flake8 noqa flag to avoid warnings on generated files
# set import path to owb structure (modules.vehicles.smarteq.proto)
for f in ../$GEN_PATH/*.py
do
    echo "fix generated file $f"
    echo "# flake8: noqa" > $f.tmp
    sed '/^import .*_pb2/s/import /import modules\.vehicles\.smarteq\.proto\./' $f >> $f.tmp
    mv $f.tmp $f
done

# get conformation to send generated files to owb2 system
echo "upload to owb? (Y/N)"
read x
if [ "$x" == "Y" ]
then
    scp ../$GEN_PATH/*.py $OWB_USER@$OWB_HOST:$OWB_PATH
fi
