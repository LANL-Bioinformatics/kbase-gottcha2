#!/bin/bash

. /kb/deployment/user-env.sh

python ./scripts/prepare_deploy_cfg.py ./deploy.cfg ./work/config.properties

if [ -f ./work/token ] ; then
  export KB_AUTH_TOKEN=$(<./work/token)
fi

if [ $# -eq 0 ] ; then
  sh ./scripts/start_server.sh
elif [ "${1}" = "test" ] ; then
  echo "Run Tests"
  make test
elif [ "${1}" = "async" ] ; then
  sh ./scripts/run_async.sh
elif [ "${1}" = "init" ] ; then
  echo "Initialize module"
  mkdir -p /data/gottcha2
  cd /data/gottcha2

  echo "downloading: https://edge-dl.lanl.gov/GOTTCHA2/RefSeq-Release90/taxdump.tar.gz"
  mkdir -p /data/gottcha2/RefSeq90
  cd /data/gottcha2/RefSeq90
  wget -q https://edge-dl.lanl.gov/GOTTCHA2/RefSeq-Release90/taxdump.tar.gz

  echo "downloading: https://edge-dl.lanl.gov/GOTTCHA2/RefSeq-Release90/RefSeq-r90.cg.BacteriaViruses.species.fna.tar"
  wget -q https://edge-dl.lanl.gov/GOTTCHA2/RefSeq-Release90/RefSeq-r90.cg.BacteriaViruses.species.fna.tar
  tar -xf RefSeq-r90.cg.BacteriaViruses.species.fna.tar
  rm RefSeq-r90.cg.BacteriaViruses.species.fna.tar

   cd /data/gottcha2
#  if [ -s "/data/gottcha2/RefSeq90/RefSeq-r90.cg.BacteriaViruses.species.fna" ] ; then
  if [ -s "/data/gottcha2/RefSeq90/RefSeq-r90.cg.BacteriaViruses.species.fna" -a -s "/data/gottcha2/RefSeq90/taxdump.tar.gz" ] ; then
    echo "DATA DOWNLOADED SUCCESSFULLY"
    touch /data/__READY__
  else
    echo "Init failed"
  fi  

elif [ "${1}" = "bash" ] ; then
  bash
elif [ "${1}" = "report" ] ; then
  export KB_SDK_COMPILE_REPORT_FILE=./work/compile_report.json
  make compile
else
  echo Unknown
fi
