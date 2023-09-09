
all: tb_galois #synth

synth: galois.v
	yosys -s synth.ys

tb_galois: tb_galois.cc galois.h
	clang++ -std=c++11 -I`yosys-config --datdir`/include tb_galois.cc -o tb_galois

galois.h: galois.v
	yosys -p "read_verilog galois.v; write_cxxrtl galois.h"


galois.v: mult.py
	./mult.py > galois.v

clean:
	\rm -f galois.v galois.h tb.gate.v tb_galois 

