
all: ./build/tb_gf256_arith_mastrovito ./build/tb_gf256_arith

synth: galois.v
	yosys -s synth.ys

./build/tb_gf256_arith_mastrovito: ./verif/tb_gf256_arith.cc ./build/gf256_poly_mult_mastrovito.h 
	clang++ -DMASTROVITO -std=c++11 -I`yosys-config --datdir`/include -I./build $< -o $@

./build/tb_gf256_arith: ./verif/tb_gf256_arith.cc ./build/gf256_poly_mult.h
	clang++ -std=c++11 -I`yosys-config --datdir`/include -I./build $< -o $@

./build/gf256_poly_mult_mastrovito.h: ./build/gf256_arith.v
	yosys -p "read_verilog $<; hierarchy -top gf256_poly_mult_mastrovito; flatten; write_cxxrtl $@"

./build/gf256_poly_mult.h: ./build/gf256_arith.v
	yosys -p "read_verilog $<; hierarchy -top gf256_poly_mult; flatten; write_cxxrtl $@"


./build/gf256_arith.v: ./generate/mult.py
	./generate/mult.py > $@

clean:
	\rm -f build/*

