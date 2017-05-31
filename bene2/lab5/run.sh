#/bin/sh
python mesh_fifteen_tcp_exp.py > tmp.txt 
grep \-oh "CWND,.*" tmp.txt > plot_data.txt 
grep \-oh "R,.*" tmp.txt >> plot_data.txt 
python3 plot.py 
gnome-open graphs/new_cwnd.png 
