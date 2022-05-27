#!/bin/bash

lualatex -interaction=nonstopmode -halt-on-error pgfmanual.tex
lwarpmk cleanall
lwarpmk html
./build-limages-with-margin.lua limages
sleep 5
python3 postprocessing.py
svgo -f processed/pgfmanual-images