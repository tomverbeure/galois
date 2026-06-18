#! /usr/bin/env python3

import sys
import argparse

import galois
from sym import *

#============================================================
# Convert from standard base to exponent representation
#============================================================
def verilog_gf_poly2power(gf, prefix = None, name = None):
    if prefix is None:
        prefix = f"gf%d" % gf.degree

    if name is None:
        name = f"{prefix}_poly2power"

    str = f'''
// Convert Galois field number from poly representation (provided as an integer)
// to power/exponent representation
module {name}(
    input      [%d:0] poly,
    output reg [%d:0] power
    );

    always @(*) begin
        case(poly)
''' % (gf.degree-1, gf.degree-1)

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

#============================================================
# Convert from exponent to standard base representation
#============================================================
def verilog_gf_power2poly(gf, prefix = None, name = None):
    if prefix is None:
        prefix = f"gf%d" % gf.degree

    if name is None:
        name = f"{prefix}_power2poly"

    str = f'''
// Convert Galois field number from power representation 
// to poly representation
module {name}(
    input      [%d:0] power,
    output reg [%d:0] poly
    );

    always @(*) begin
        case(power)
''' % (gf.degree-1, gf.degree-1)

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

#============================================================
# Polynomial multiplication of 2 values
#============================================================
def verilog_gf_poly_ab(gf, prefix = None, name = None):
    SymSum.nr_sums  = 0
    SymFactor.nr_facts = 0

    if prefix is None:
        prefix = f"gf%d" % gf.degree

    if name is None:
        name = f"{prefix}_poly_ab"

    # output_factor contains 2*gf.degree-1 lists.
    # Each list contains the multiplication (AND) of 1 bit from a and 1 bit from b.
    output_factors = [ [] for _ in range(2 * gf.degree - 1)]

    for a_idx in range(0,gf.degree):
        for b_idx in range(0,gf.degree):
            o_idx = a_idx + b_idx
            output_factors[o_idx].append(SymFactor( SymSymbol(f"poly_a[{a_idx}]"),SymSymbol(f"poly_b[{b_idx}]")) )

    outputs = [ SymSum(output_factor) for output_factor in output_factors ]

    str = f'''
// Polynomial multiplication of 2 GF numbers of the same order
// Modulo reduction is not included
//
// XORs: {SymSum.nr_sums}
// ANDs: {SymFactor.nr_facts}
module {name}(
    input      [%d:0] poly_a,
    input      [%d:0] poly_b,
    output     [%d:0] poly_out
    );

''' % (gf.degree-1, gf.degree-1, 2*gf.degree-2)

    for o_idx, output in enumerate(outputs):
        str += f'    assign poly_out[%d] = ' % o_idx
        str += output.flatten()
        str += ";\n"

    str += f'endmodule'

    return str

#============================================================
# Polynomial modulo
#
# Given an input vector d(x) with degree 2^n-1 and an irreducible polynomial p(x), 
# calculate the d(x) mod p(x)
#============================================================
def verilog_gf_poly_mod(gf, prefix = None, name = None, opt = True):

    SymSum.nr_sums      = 0
    SymFactor.nr_facts  = 0

    if prefix is None:
        prefix = f"gf%d" % gf.degree

    if name is None:
        name = f"{prefix}_poly_mod"

    # Array with irreducible polynomial coefficients
    p_coefs = [ 0 ] * (gf.degree+1)
    for i in range(gf.degree+1):
        p_coefs[i] = (int(gf.irreducible_poly)>>i)&1

    # Input for a[3:0] * b[3:0] -> d[6:0]
    # Primitive poly: p[4:0]
    # p[4] is always 1
    # 
    # R[0]:  d6            d5           d4           d3           d2           d1           d0
    #    +   d6          d6p3         d6p2         d6p1         d6p0  
    #     ----------------------------------------------------------
    # R[1]:   0       d5+d6p3      d4+d6p2      d3+d6p1      d2+d6p0           d1           d0
    #
    #         0       R[1][5]      R[1][4]      R[1][3]      R[1][3]      R[1][2]
    #             +   R[1][5]   R[1][5].p3   R[1][5].p2   R[1][5].p2   R[1][5].p1  
    #              --------------------------------------------------------------
    # R[2]                  0          ...

   
    # R is a 2-dimensional array with the resulting polynomial
    # after each step of the division.
    R = [ [ SymZero() for _ in range (2*gf.degree-1) ] for _ in range(gf.degree) ]

    # R[0][x] starts out with with the input operand d[x].
    for x in range(2*gf.degree-1):
        R[0][x] = SymSymbol(f"d[{x}]")

    r_coefs = [ ]

    for step in range(1, gf.degree):
        d_idx = gf.degree-1-step
        d_msb = d_idx+gf.degree

        # First copy the previous result. Some terms are overwritten.
        for d in range(2*gf.degree-1):
            R[step][d] = R[step-1][d]

        for p_idx in range(1, gf.degree+1):
            if opt:
                # When optimization is on, only sum the 2 terms when the coefficient
                # of the primitive is 1, otherwise we can just reuse the previous value (which
                # we already filled in.)
                if p_coefs[gf.degree-p_idx] == 1:
                    R[step][d_msb-p_idx] = SymSum(R[step-1][d_msb-p_idx], R[step-1][d_msb])
            else:
                R[step][d_msb-p_idx] = SymSum(
                                    R[step-1][d_msb-p_idx], 
                                    SymFactor(R[step-1][d_msb], SymSymbol(f"p[{gf.degree-p_idx}]"))
                                )

            if True:
                # Intermediate values for cleaner and easier to debug code.
                r_coef_str= f"r_{step}_{d_msb-p_idx}"
                r_coef = SymSymbol(r_coef_str)
                r_coefs.append([r_coef_str, R[step][d_msb-p_idx] ])
                R[step][d_msb-p_idx] = r_coef

    # Debug
    if False:
        for r in r_coefs:
            print(r[0], "=", r[1].flatten())
    
        for (step, r) in enumerate(R):
            print(f"Step {step}:")
            for r_term in reversed(r):
                print(r_term.flatten())

    s = f'''
// Modulo reduction by primitive polynomial of a polynomial that was the result of a 
// poly_mult of 2 GF numbers
//
// XORs: {SymSum.nr_sums}
// ANDs: {SymFactor.nr_facts}
module {name}(
    input      [{2*gf.degree-2}:0] poly_in,
    output     [{gf.degree-1}:0] poly_out
    );

    wire [{2*gf.degree-2:0}:0] d = poly_in;
    wire [{gf.degree}:0] p = 'h%x;

''' % (int(gf.irreducible_poly))

    for r in r_coefs:
        s += f'    wire {r[0]} = {r[1].flatten()};\n'

    s += "\n"
    s += f'    assign poly_out = {{%s}};\n' % (',').join([r.flatten() for r in reversed(R[gf.degree-1][0:gf.degree])])

    s += f'endmodule'


    return s

#============================================================
# Traditional Galois field multiplication
#============================================================
def verilog_gf_poly_mult(gf, prefix = None, name = None):
    if prefix is None:
        prefix = f"gf%d" % gf.degree

    if name is None:
        name = f"{prefix}_poly_mult"

    s = f'''
// Traditional GF multiplier
module {name}(
    input      [{gf.degree-1}:0] poly_a,
    input      [{gf.degree-1}:0] poly_b,
    output     [{gf.degree-1}:0] poly_out
    );

    wire [{2*gf.degree-2}:0] poly_ab;

    {prefix}_poly_ab u_gf_poly_ab(
        poly_a, 
        poly_b,
        poly_ab
    );

    {prefix}_poly_mod u_gf_poly_mod(
        poly_ab,
        poly_out
    );

endmodule
'''
    return s


#============================================================
# Mastrovito Galois field multiplication
#============================================================
def verilog_gf_poly_mult_mastrovito(gf, prefix = None, name = None, opt = True):
    SymSum.nr_sums  = 0
    SymFactor.nr_facts = 0

    if prefix is None:
        prefix = f"gf%d" % gf.degree

    if name is None:
        name = f"{prefix}_poly_mult_mastrovito"

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

    for i in range(1, gf.degree):       # Go through all rows
        M[i][0] = M[i-1][gf.degree-1]

        for j in range(1, gf.degree):       # Go through all columns
            if opt:
                if p_coefs[j] == 1:
                    M[i][j] = SymSum(M[i-1][j-1], M[i-1][gf.degree-1])
                else:
                    M[i][j] = M[i-1][j-1]
            else:
                M[i][j] = SymSum(M[i-1][j-1], SymFactor(M[i-1][gf.degree-1], SymSymbol(f"p[{j}]")))

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


    s = f'''
// Mastrovito GF multiplier
//
// XORs: {SymSum.nr_sums}
// ANDs: {SymFactor.nr_facts}
module {name}(
    input      [{gf.degree-1}:0] poly_a,
    input      [{gf.degree-1}:0] poly_b,
    output     [{gf.degree-1}:0] poly_out
    );

    wire [{gf.degree-1}:0] a = poly_a;
    wire [{gf.degree-1}:0] b = poly_b;
    wire [{gf.degree}:0] p = 'h%x;

''' % (int(gf.irreducible_poly))

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
    gf = galois.GF(2**4)
    s = verilog_gf_poly_mod(gf)
    print(s)

if False:
    gf = galois.GF(2**8)
    s = verilog_poly_mult_mastrovito(gf)
    print(s)

if True:
    parser = argparse.ArgumentParser(description="Generate verilog Galois field arithmetic logic")
    parser.add_argument('-o', '--output', help='name of output verilog file. When not given, output is sent to stdout.')
    parser.add_argument('-p', '--prefix', help='prefix string of generate verilog modules. Default is gf<order>.')
    parser.add_argument('-n', '--degree', default=8, help='Degree of the GF(2^n) field. Default is 8.')
    parser.add_argument('-a', '--all', action='store_true', help='Output all known Verilog modules.')
    parser.add_argument('-d', '--mult_trad', action='store_true', help='Output traditional multiplier.')
    parser.add_argument('-m', '--mult_mast', action='store_true', help='Output Mastrovito multiplier.')
    parser.add_argument('--poly2power', action='store_true', help='Output poly2power.')
    parser.add_argument('--power2poly', action='store_true', help='Output power2poly.')
    parser.add_argument('--no_opt', action='store_true', help='Don''t optimize away constant primitive terms')

    args = parser.parse_args()

    degree = args.degree
    opt = not(args.no_opt)

    if args.prefix is None:
        prefix = f"gf{degree}"
    else:
        prefix = args.prefix

    if args.output is None:
        output = sys.stdout
    else:
        output = open(args.output, 'wt')


    gf = galois.GF(2**int(args.degree))

    s = ""
    s += ''.join([f"// %s\n" % x for x in gf.properties.split('\n')])

    if args.all or args.poly2power:
        s += verilog_gf_poly2power(gf, prefix=prefix)
        s += "\n"

    if args.all or args.power2poly:
        s += verilog_gf_power2poly(gf, prefix=prefix)
        s += "\n"

    if args.all or args.mult_trad:
        s += verilog_gf_poly_ab(gf, prefix=prefix)
        s += "\n"
        s += verilog_gf_poly_mod(gf, prefix=prefix, opt=opt)
        s += "\n"
        s += verilog_gf_poly_mult(gf, prefix=prefix)
        s += "\n"

    if args.all or args.mult_mast:
        s += verilog_gf_poly_mult_mastrovito(gf, prefix=prefix, opt=opt)
        s += "\n"

        s += "\n"
    print(s, file=output)

    if output is not sys.stdout:
        output.close()


