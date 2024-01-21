This repo contains some code to experiment with Galois multipliers in Verilog.

The only thing of interest here is probably the `mult.py` script in the ./generate directory. It generates Verilog code for GF(2^n) multipliers,
where n can be specified on the command line.

Right now, it uses a standard primitive polynomial as selected by the Python Galois package, but it should be
trivial to modify to code for any random primitive poly.
