#!/bin/sh
python five_flow.py \-f $1 > output.txt
grep \-oh "CWND,.*" output.txt > plot_data.txt
grep \-oh "Q,.*" output.txt >> plot_data.txt
grep \-oh "X,.*" output.txt >> plot_data.txt
grep \-oh "R,.*" output.txt >> plot_data.txt
python3 plot.py 5
gnome-open graphs/new_cwnd.png
