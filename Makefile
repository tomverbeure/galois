
all: ./build/tb_gf_arith_mastrovito ./build/tb_gf_arith ./build/tb_gf_arith_ref
	./build/tb_gf_arith_mastrovito > build/sim_mastrovito.log
	./build/tb_gf_arith> build/sim_traditional.log
	./build/tb_gf_arith_ref > build/sim_ref.log
	-diff -u build/sim_ref.log build/sim_mastrovito.log > sim_mastrovito.diff
	-diff -u build/sim_ref.log build/sim_traditional.log > sim_traditional.diff

synth: galois.v
	yosys -s synth.ys

./build/tb_gf_arith_mastrovito: ./verif/tb_gf_arith.cc ./build/gf_poly_mult_mastrovito.h 
	g++ -DMASTROVITO -std=c++11 -I`yosys-config --datdir`/include -I./build $< -o $@

./build/tb_gf_arith: ./verif/tb_gf_arith.cc ./build/gf_poly_mult.h
	g++ -std=c++11 -I`yosys-config --datdir`/include -I./build $< -o $@

./build/tb_gf_arith_ref: ./verif/tb_gf_arith.cc ./build/gf_poly_mult_ref.h
	g++ -DREF -std=c++11 -I`yosys-config --datdir`/include -I./build $< -o $@

./build/gf_poly_mult_mastrovito.h: ./build/gf_arith.v
	yosys -p "read_verilog $<; hierarchy -top gf_poly_mult_mastrovito; flatten; write_cxxrtl $@"

./build/gf_poly_mult.h: ./build/gf_arith.v
	yosys -p "read_verilog $<; hierarchy -top gf_poly_mult; flatten; write_cxxrtl $@"

./build/gf_poly_mult_ref.h: ./verilog/traditional_ab_mod_p_8.v
	yosys -p "read_verilog $<; hierarchy -top traditional_ab_mod_p_8; flatten; write_cxxrtl $@"


./build/gf_arith.v: ./generate/mult.py
	./generate/mult.py -n 8 --output $@ --prefix gf --all

clean:
	\rm -f build/*

