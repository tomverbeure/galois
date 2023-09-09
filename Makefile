
all: ./build/tb_gf256_arith #synth

synth: galois.v
	yosys -s synth.ys

./build/tb_gf256_arith: ./verif/tb_gf256_arith.cc ./build/gf256_arith.h
	clang++ -std=c++11 -I`yosys-config --datdir`/include -I./build $< -o $@

./build/gf256_arith.h: ./build/gf256_arith.v
	yosys -p "read_verilog $<; write_cxxrtl $@"


./build/gf256_arith.v: ./generate/mult.py
	./generate/mult.py > $@

clean:
	\rm -f build/*

