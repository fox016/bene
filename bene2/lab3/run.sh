#!/bin/sh
python transfer.py \-f $1 > output.txt
grep \-oh "X.*" output.txt >> sequence_plot_data.txt
python3 plot.py
gnome-open sequence_plot.png
