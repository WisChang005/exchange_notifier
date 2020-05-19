#! /bin/bash

FILEDIR=$(dirname "$0")

source ~/.env_src
python3 ${FILEDIR}/exchange_notifier.py