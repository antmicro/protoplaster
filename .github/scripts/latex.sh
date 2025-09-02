#!/usr/bin/env sh

set -e

cd $(dirname $0)/../../docs

python3 -m venv ./venv
. ./venv/bin/activate

pip3 install -r requirements.txt

cd build/latex
LATEXMKOPTS='-interaction=nonstopmode' make
cp *.pdf ../html/

cd -
rm -r ./venv
