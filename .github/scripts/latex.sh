#!/usr/bin/env sh

set -e

apt-get update -qq
DEBIAN_FRONTEND=noninteractive apt-get -y install --no-install-recommends git

cd $(dirname $0)/../../docs

python3 -m venv ./venv
. ./venv/bin/activate

pip3 install -r requirements.txt
pip3 install ../

cd build/latex
LATEXMKOPTS='-interaction=nonstopmode' make
cp *.pdf ../html/

cd -
rm -r ./venv
