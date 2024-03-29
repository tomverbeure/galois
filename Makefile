NR_BITS 	= 8
GF		= 256

#NR_BITS 	= 16
#GF		= 65536

#NR_BITS 	= 4
#GF		= 16

CPLUSPLUS	= g++


all: ./build/tb_gf_arith_mastrovito ./build/tb_gf_arith #./build/tb_gf_arith_ref
	./build/tb_gf_arith_mastrovito > build/sim_mastrovito.log
	./build/tb_gf_arith> build/sim_traditional.log
	#./build/tb_gf_arith_ref > build/sim_ref.log
	#-diff -u build/sim_ref.log build/sim_mastrovito.log > sim_mastrovito.diff
	#-diff -u build/sim_ref.log build/sim_traditional.log > sim_traditional.diff
	diff -u build/sim_traditional.log build/sim_mastrovito.log > sim_traditional_mastrovito.diff

synth: ./build/gf$(GF)_arith.v
	cd gatemap && yosys -s synth$(GF).ys -l ../build/synth$(GF).log

./build/tb_gf_arith_mastrovito: ./verif/tb_gf_arith.cc ./build/gf_poly_mult_mastrovito.h 
	$(CPLUSPLUS) -O2 -DMASTROVITO -DDESIGN_TOP=p_gf$(GF)__poly__mult__mastrovito -DGF=$(GF) -std=c++11 -I`yosys-config --datdir`/include -I./build $< -o $@

./build/tb_gf_arith: ./verif/tb_gf_arith.cc ./build/gf_poly_mult.h
	$(CPLUSPLUS) -O2 -DDESIGN_TOP=p_gf$(GF)__poly__mult -DGF=$(GF) -std=c++11 -I`yosys-config --datdir`/include -I./build $< -o $@

#./build/tb_gf_arith_ref: ./verif/tb_gf_arith.cc ./build/gf_poly_mult_ref.h
#	$(CPLUSPLUS) -DREF -std=c++11 -I`yosys-config --datdir`/include -I./build $< -o $@

./build/gf_poly_mult_mastrovito.h: ./build/gf$(GF)_arith.v
	yosys -p "read_verilog $<; hierarchy -top gf$(GF)_poly_mult_mastrovito; flatten; write_cxxrtl $@"

./build/gf_poly_mult.h: ./build/gf$(GF)_arith.v
	yosys -p "read_verilog $<; hierarchy -top gf$(GF)_poly_mult; flatten; write_cxxrtl $@"

./build/gf_poly_mult_ref.h: ./verilog/gf$(GF)_traditional_ab_mod_p.v
	yosys -p "read_verilog $<; hierarchy -top gf$(GF)_traditional_ab_mod_p; flatten; write_cxxrtl $@"


./build/gf$(GF)_arith.v: ./generate/mult.py ./generate/sym.py
	./generate/mult.py -n $(NR_BITS) --output $@ --prefix gf$(GF) --mult_trad --mult_mast

clean:
	\rm -f build/*

