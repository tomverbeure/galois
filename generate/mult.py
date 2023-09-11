#! /usr/bin/env python3

import sys
import galois
from sym import *

def verilog_gf_poly2power(gf):
    name = "gf%d_poly2power" % gf.order

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
    name = "gf%d_power2poly" % gf.order

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

def verilog_gf_poly_mult(gf):
    SymSum.nr_sums  = 0
    SymFactor.nr_facts = 0

    name = "gf%d_poly_mult" % gf.order

    str = f'''
// Polynomial multiplication of 2 GF numbers of the same order
// Modulo reduction is not included
//
// XORs: {SymSum.nr_sums}
// ANDs: {SymFactor.nr_facts}
module %s(
    input      [%d:0] poly_a,
    input      [%d:0] poly_b,
    output     [%d:0] poly_out
    );

''' % (name, gf.degree-1, gf.degree-1, 2*gf.degree-2)

    output_factors = [ None ] * (2*gf.degree-1)

    for a_idx in range(0,gf.degree):
        for b_idx in range(0,gf.degree):
            o_idx = a_idx + b_idx
            if output_factors[o_idx] is None:
                output_factors[o_idx] = [ [a_idx, b_idx] ]
            else:
                output_factors[o_idx].append([a_idx, b_idx])

    for o_idx, o_factors in enumerate(output_factors):
        if o_factors is None:
            str += f"    assign poly_out[%d] = 1'b0;\n" % o_idx;
        else:
            str += f'    assign poly_out[%d] = ^{{ ' % o_idx
            str += ", ".join(["poly_a[%d] & poly_b[%d]" % (x[0], x[1]) for x in o_factors])

            str += " };\n"

    str += f'endmodule'

    return str

def verilog_gf_poly_mod(gf):
    SymSum.nr_sums  = 0
    SymFactor.nr_facts = 0

    name = "gf%d_poly_mod" % gf.order

    p_coefs = [ 0 ] * (gf.degree+1)
    for i in range(gf.degree+1):
        p_coefs[i] = (int(gf.irreducible_poly)>>i)&1

    # Input for a[3:0] * b[3:0] -> d[6:0]
    # Primitive poly: p[4:0]
    # 
    #   d6       d5      d4      d3      d2      d1      d0
    #   p4       p3      p2      p1      p0
    #
    # + d6p4     d6p3    d6p2    d6p1    d6p0  
    # ----------------------------------------
    #   d6       d5+d6p3 d4+d6p3 d3+d6p1 d2+d6p0 
    #            p4      p3      p2      p1      p0
    #
    #                    p4      p3      p2      p1      p0
    # ...
   
    R = [ SymSymbol(f"d[{i}]") for i in range (2*gf.degree-1) ] 

    #Trui Result for each step of the division
    R = [ [ SymZero() for _ in range (2*gf.degree-1) ] for _ in range(gf.degree) ]

    for d in range(2*gf.degree-1):
        R[0][d] = SymSymbol(f"d[{d}]")

    r_coefs = [ ]

    #for d_idx in reversed(range(gf.degree-1)):
    for step in range(1, gf.degree):
        d_idx = gf.degree-1-step
        d_msb = d_idx+gf.degree

        for d in range(2*gf.degree-1):
            R[step][d] = R[step-1][d]

        for p_idx in range(1, gf.degree+1):
            if True:
                if p_coefs[gf.degree-p_idx] == 1:
                    R[step][d_msb-p_idx] = SymSum(R[step-1][d_msb-p_idx], R[step-1][d_msb])
            else:
                R[step][d_msb-p_idx] = SymSum(
                                    R[step-1][d_msb-p_idx], 
                                    SymFactor(R[step-1][d_msb], SymSymbol(f"p[{gf.degree-p_idx}]"))
                                )

            if True:
                r_coef_str = f"r_{step}_{d_msb-p_idx}"
                r_coef = SymSymbol(r_coef_str)
                r_coefs.append([r_coef_str, R[step][d_msb-p_idx] ])
                R[step][d_msb-p_idx] = r_coef

    #for r in r_coefs:
    #    print(r[0], "=", r[1].flatten())

    #for (step, r) in enumerate(R):
    #    print(f"Step {step}:")
    #    for r_term in reversed(r):
    #        print(r_term.flatten())

    s = f'''
// Modulo reduction by primitive polynomial of a polynomial that was the result of a 
// poly_mult of 2 GF numbers
//
// XORs: {SymSum.nr_sums}
// ANDs: {SymFactor.nr_facts}
module %s(
    input      [%d:0] poly_in,
    output     [%d:0] poly_out
    );

    wire [{2*gf.degree-2:0}:0] d = poly_in;

''' % (name, 2*gf.degree-2, gf.degree-1)

    for r in r_coefs:
        s += f'    wire {r[0]} = {r[1].flatten()};\n'

    s += "\n"
    s += f'    assign poly_out = {{%s}};\n' % (',').join([r.flatten() for r in reversed(R[gf.degree-1][0:gf.degree])])

    s += f'endmodule'


    return s

def verilog_gf_poly_mult_mastrovito(gf, opt = True):
    SymSum.nr_sums  = 0
    SymFactor.nr_facts = 0

    p_coefs = []
    p_coefs_sym = []
    for i in range(gf.degree+1):
        p_coef = (int(gf.irreducible_poly)>>i)&1
        p_coefs.append(p_coef)
        if p_coef == 0:
            p_coefs_sym.append(SymZero())
        else:
            p_coefs_sym.append(SymOne())
    #print(p_coefs)

    m_coefs = []

    # Step 1: create matrix
    # (i,j) are swapped around compared to the paper...

    M = [ [ SymZero() for _ in range (gf.degree) ] for _ in range(gf.degree) ]

    # M[0] = [ a_coefs[0], a_coefs[1], a_coefs[2], a_coefs[3] ]
    for j in range(gf.degree):
        M[0][j] = SymSymbol(f"a[%d]" % j)

    for i in range(1, gf.degree):       # Go throug all rows
        M[i][0] = M[i-1][gf.degree-1]

        for j in range(1, gf.degree):       # Go throug all columns
            if opt:
                if p_coefs[j] == 1:
                    M[i][j] = M[i-1][j-1]
                else:
                    M[i][j] = SymSum(M[i-1][j-1], M[i-1][gf.degree-1])
            else:
                M[i][j] = SymSum(M[i-1][j-1], SymFactor(M[i-1][gf.degree-1], p_coefs_sym[j]))

            m_coef_str = f"m_%d_%d" % (i,j)
            m_coef = SymSymbol(m_coef_str)
            m_coefs.append([ m_coef_str, M[i][j] ])
            M[i][j] = m_coef

    # Step 2: Multiply M with B
    c_coefs = []
    for j in range(gf.degree):
        c_j = SymSumVector([ SymFactor(M[i][j], SymSymbol(f"b[%d]"%i)) for i in range(gf.degree) ])
        c_coefs.append(c_j)

    #print(m_coefs)
    #print(M)
    #print(c_coefs)

    name = "gf%d_poly_mult_mastrovito" % gf.order

    s = f'''
// Mastrovito GF multiplier
//
// XORs: {SymSum.nr_sums}
// ANDs: {SymFactor.nr_facts}
module %s(
    input      [%d:0] poly_a,
    input      [%d:0] poly_b,
    output     [%d:0] poly_out
    );

    wire [%d:0] a = poly_a;
    wire [%d:0] b = poly_b;

''' % (name, gf.degree-1, gf.degree-1, gf.degree-1, gf.degree-1, gf.degree-1)

    for m_coef in m_coefs:
        s += f'    wire %s = %s;\n' % (m_coef[0], m_coef[1].flatten()) 

    s += '\n'

    for (c_idx, c_coef) in enumerate(c_coefs):
        s += f'    assign poly_out[%d] = %s;\n' % (c_idx, c_coef.flatten())

    s += f'endmodule'

    return s
    

if False:
    gf = galois.GF(2**8)
    s = verilog_gf_poly2power(gf)
    print(s)
    print()
    s = verilog_gf_power2poly(gf)
    print(s)

if False:
    gf = galois.GF(2**8)
    s = verilog_poly_mult(gf)
    print(s)

if False:
    gf = galois.GF(2**8)
    s = verilog_gf_poly_mod(gf)
    print(s)

if False:
    gf = galois.GF(2**8)
    s = verilog_poly_mul_mastrovito(gf)
    print(s)

if True:
    gf = galois.GF(2**8)
    s = ""
    s += ''.join([f"// %s\n" % x for x in gf.properties.split('\n')])
    s += verilog_gf_poly2power(gf)
    s += "\n"
    s += verilog_gf_power2poly(gf)
    s += "\n"
    s += verilog_gf_poly_mult(gf)
    s += "\n"
    s += verilog_gf_poly_mod(gf)
    s += "\n"
    s += verilog_gf_poly_mult_mastrovito(gf)
    s += "\n"
    s += "\n"
    print(s)

