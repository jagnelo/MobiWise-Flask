#!/bin/sh
# script for compiling the heatmaps MATLAB module

eval /usr/local/MATLAB/R2020b/bin/mcc -m heatmaps.m -a add_files/ -a getscreen/ -a traci4matlab/

