
all: ./build/tb_gf_arith_mastrovito ./build/tb_gf_arith
	./build/tb_gf_arith_mastrovito > build/sim_mastrovito.log
	./build/tb_gf_arith> build/sim.log
	diff build/sim.log build/sim_mastrovito.log

synth: galois.v
	yosys -s synth.ys

./build/tb_gf_arith_mastrovito: ./verif/tb_gf_arith.cc ./build/gf_poly_mult_mastrovito.h 
	clang++ -DMASTROVITO -std=c++11 -I`yosys-config --datdir`/include -I./build $< -o $@

./build/tb_gf_arith: ./verif/tb_gf_arith.cc ./build/gf_poly_mult.h
	clang++ -std=c++11 -I`yosys-config --datdir`/include -I./build $< -o $@

./build/gf_poly_mult_mastrovito.h: ./build/gf_arith.v
	yosys -p "read_verilog $<; hierarchy -top gf_poly_mult_mastrovito; flatten; write_cxxrtl $@"

./build/gf_poly_mult.h: ./build/gf_arith.v
	yosys -p "read_verilog $<; hierarchy -top gf_poly_mult; flatten; write_cxxrtl $@"


./build/gf_arith.v: ./generate/mult.py
	./generate/mult.py > $@

clean:
	\rm -f build/*

