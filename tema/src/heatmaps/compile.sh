#!/bin/sh
# script for compiling the heatmaps MATLAB module

eval /usr/local/MATLAB/R2020b/bin/mcc -m heatmaps.m -a ../../../lib/MATLAB/add_files/ -a ../../../lib/MATLAB/getscreen/ -a ../../../lib/MATLAB/traci4matlab/


