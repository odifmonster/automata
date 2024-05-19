#!/usr/bin/env bash

for f in *.dot; do
    fname="$(basename $f .dot)"
    dot -Tpng $f > $fname.png
done