#!/bin/bash

robotsdir="myrobots"

now=`date +"%Y-%m-%d_%H:%M:%S"`
dir="../divisions_tournament.${now}"
python3 src/divisions_tournament.py -robots "${robotsdir}" -output "$dir"

