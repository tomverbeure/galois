#! /usr/bin/env python3

import galois

#a = galois.Poly([1,0,1,1])
#b = galois.Poly([1,1,0,1])
#
#print(a)
#print(b)
#print(a*b)
#
#
## all irreducible polys for GF(2^4):
#list(galois.irreducible_polys(2,4))
#
#
## gs24 is a class
#gf24 = galois.GF(2**4)
#print(gf24.properties)
#
#a = gf24([1,1,1,1,1])

def verilog_gf_poly2power(gf, name = None):
    name = "gf_poly2power_%d" % gf.degree

    str = f'''
// Convert Galois field number from poly representation (provided as an integer)
// to power/exponent representation
module %s(
    input      [%d:0] poly,
    output reg [%d:0] power
    );

    always @(*) begin
        case(poly)
''' % (name, gf.degree-1, gf.degree-1)

    for poly in range(0,gf.order):
        if poly == 0:
            # There's no power for element zero, so assign the
            # maximum power, which is not actually used...
            power = gf.order-1
        else:
            power = gf(poly).log()

        str += f"            %d'b%s: power = %d'd%s;\n" % (gf.degree, format(poly, '0%db' % gf.degree), gf.degree, format(power, 'd'))

    str += f'''        endcase
    end
endmodule
'''

    return str

def verilog_gf_power2poly(gf, name = None):
    name = "gf_power2poly_%d" % gf.degree

    str = f'''
// Convert Galois field number from power representation 
// to poly representation
module %s(
    input      [%d:0] power,
    output reg [%d:0] poly
    );

    always @(*) begin
        case(power)
''' % (name, gf.degree-1, gf.degree-1)

    x = gf(1)
    for power in range(0,gf.order):
        if power == gf.order-1:
            poly = 0
        else:
            poly = int(x)
            x = x * gf(2)

        str += f"            %d'd%s: poly = %d'b%s;\n" % (gf.degree, format(power, 'd'), gf.degree, format(poly, '0%db' % gf.degree))

    str += f'''        endcase
    end
endmodule
'''

    return str

if True:
    gf = galois.GF(2**8)
    str = verilog_gf_poly2power(gf)
    print(str)
    print()
    str = verilog_gf_power2poly(gf)
    print(str)

