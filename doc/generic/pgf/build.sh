#!/bin/bash

lualatex -interaction=nonstopmode -halt-on-error pgfmanual.tex
lwarpmk cleanall
lwarpmk html
./build-limages-with-margin.lua limages
python3 postprocessing.py