#!/bin/bash

set -e

# Having checked this repo out to a directory
# you can use this script to quickly setup the local development.
# Typically, assuming you've forked all the corresponding repos,
# (say to the informaticsmatters organisation) you'd: -
#
#   git clone https://github.com/InformaticsMatters/dls-fragalysis-stack-openshift.git
#   ./dls-fragalysis-stack-openshift/setup-local-dev.sh informaticsmatters

if [ "$1" == "" ]
then
  echo "ERROR: Missing GitHub organisation"
  echo "Usage: setup-local-dev.sh <ACCOUNT>"
  exit 1
fi

# Clone the 'fragalsys-???' repos...
ACCOUNT="$1"
for REPO in frontend backend stack loader
do
  TGT=fragalysis-"$REPO"
  if [ ! -d "$TGT" ]
  then
    git clone https://github.com/"ACCOUNT"/fragalysis-"$REPO"
  fi
done
# Clone 'fragalsys'...
TGT=fragalysis
if [ ! -d "$TGT" ]
then
  git clone https://github.com/"ACCOUNT"/"$TGT"
fi

# Create some key data directories
#
# Note: The data/input/django_data directory will need to be populated
#       with EXAMPLE data before you can launch the application.
mkdir -p data/input/django_data
mkdir -p data/mysql/data
mkdir -p data/neo4j/data
mkdir -p data/neo4j/logs
mkdir -p data/stack/media
mkdir -p data/stack/logs
