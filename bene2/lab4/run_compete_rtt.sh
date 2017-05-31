#!/bin/sh
python compete_rtt.py \-f $1 > output.txt
grep \-oh "CWND,.*" output.txt > plot_data.txt
grep \-oh "Q,.*" output.txt >> plot_data.txt
grep \-oh "X,.*" output.txt >> plot_data.txt
grep \-oh "R,.*" output.txt >> plot_data.txt
python3 plot.py 2
gnome-open graphs/new_cwnd.png
