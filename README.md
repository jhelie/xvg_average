xvg_average
===========

Python utility to average several .xvg files.

Requirements
------------

Files:
- all xvg files must have the same number of data rows and columns (column order doens't matter)
- the 1st data column must be identical in all the files

The following Python modules are required:
- numpy
- scipy

Usage
-----
python xvg_average.py --help

Features
--------
- columns averaged either by position of name (legend)
- can smooth output (rolling average)
- can skim output
- can perform weighted averages
- can deal with "nan" values
