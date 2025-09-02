#!/usr/bin/env sh

set -e

cd $(dirname $0)/../../docs

python3 -m venv ./venv
. ./venv/bin/activate

pip3 install -r requirements.txt

make html latex

rm -r ./venv
