
synth: galois.v

galois.v: mult.py
	./mult.py > galois.v

clean:
	\rm galois.v
