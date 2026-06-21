#! /usr/bin/env python3

import sys
import argparse

import galois
from sym import *

def balanced_xor_depth(delays):
    if len(delays) == 1:
        return delays[0]

    mid = len(delays) // 2
    return max(
        balanced_xor_depth(delays[:mid]),
        balanced_xor_depth(delays[mid:])
    ) + 1

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
    logic_depth = max(balanced_xor_depth([ 1 for _ in output_factor ]) for output_factor in output_factors)

    str = f'''
// Polynomial multiplication of 2 GF numbers of the same order
// Modulo reduction is not included
//
// XORs: {SymSum.nr_sums}
// ANDs: {SymFactor.nr_facts}
// Logic depth: {logic_depth}
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
    R_depth = [ [ 0 for _ in range (2*gf.degree-1) ] for _ in range(gf.degree) ]

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
            R_depth[step][d] = R_depth[step-1][d]

        for p_idx in range(1, gf.degree+1):
            if opt:
                # When optimization is on, only sum the 2 terms when the coefficient
                # of the primitive is 1, otherwise we can just reuse the previous value (which
                # we already filled in.)
                if p_coefs[gf.degree-p_idx] == 1:
                    R[step][d_msb-p_idx] = SymSum(R[step-1][d_msb-p_idx], R[step-1][d_msb])
                    R_depth[step][d_msb-p_idx] = max(R_depth[step-1][d_msb-p_idx], R_depth[step-1][d_msb]) + 1
            else:
                R[step][d_msb-p_idx] = SymSum(
                                    R[step-1][d_msb-p_idx], 
                                    SymFactor(R[step-1][d_msb], SymSymbol(f"p[{gf.degree-p_idx}]"))
                                )
                R_depth[step][d_msb-p_idx] = max(R_depth[step-1][d_msb-p_idx], R_depth[step-1][d_msb] + 1) + 1

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

    logic_depth = max(R_depth[gf.degree-1][0:gf.degree])

    s = f'''
// Modulo reduction by primitive polynomial of a polynomial that was the result of a 
// poly_mult of 2 GF numbers
//
// XORs: {SymSum.nr_sums}
// ANDs: {SymFactor.nr_facts}
// Logic depth: {logic_depth}
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
# Traditional 2-stage Galois field multiplication
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
def verilog_gf_poly_mult_mastrovito(gf, prefix = None, name = None, latency_opt = False):
    SymSum.nr_sums  = 0
    SymFactor.nr_facts = 0

    if prefix is None:
        prefix = f"gf%d" % gf.degree

    if name is None:
        name = f"{prefix}_poly_mult_mastrovito"

    p_coefs = []
    for i in range(gf.degree+1):
        p_coef = (int(gf.irreducible_poly)>>i)&1
        p_coefs.append(p_coef)

    class WireExpr:
        def __init__(self, name, expr):
            self.name = name
            self.expr = expr

    m_coefs = []

    # Step 1: create matrix
    # M[row][col] matches the Mastrovito pseudo-code indexing.

    # A matrix cell's function is represented by the set of a[] terms XORed together.
    # This lets us implement the paper's CHECK 1/2 
    class MCell:
        def __init__(self, expr, xor_set, delay):
            # Math operation tree (sym.py)
            # Maintains the hierarchical tree with intermediate signals to 
            # get there.
            self.expr       = expr

            # Set with all XOR contributing indices of input vector a
            # frozenset ensures that xor_set can be used as a hash key
            self.xor_set    = frozenset(xor_set)

            # Cumulative delay from all inputs
            self.delay      = delay

    def calc_delay(cell_a, cell_b):
        return max(cell_a.delay, cell_b.delay) + 1

    def remember_cell(cell):
        cells.append(cell)

        # Update cell_by_xor_set if the delay of this cell is less than what we already have.
        if cell.xor_set not in cell_by_xor_set or cell.delay < cell_by_xor_set[cell.xor_set].delay:
            cell_by_xor_set[cell.xor_set] = cell

    def connect_new_xor(row, col, cell_a, cell_b, xor_set):
        m_coef_name = f"m_%d_%d" % (row,col)
        m_coef = SymSymbol(m_coef_name)
        m_coefs.append(WireExpr(m_coef_name, SymSum(cell_a.expr, cell_b.expr)))
        return MCell(m_coef, xor_set, calc_delay(cell_a, cell_b))

    c_sum_coefs = []

    def balanced_xor_delay(delays):
        if len(delays) == 1:
            return delays[0]

        mid = len(delays) // 2
        return max(
            balanced_xor_delay(delays[:mid]),
            balanced_xor_delay(delays[mid:])
        ) + 1

    def latency_optimized_xor_sum(c_idx, terms):
        class Signal:
            def __init__(self, expr, delay):
                self.expr = expr
                self.delay = delay

        signals = [ Signal(SymFactor(cell.expr, b_sym), cell.delay + 1) for cell, b_sym in terms ]
        signals = list(signals)
        step = 0

        while len(signals) > 1:
            signals.sort(key=lambda signal: signal.delay)
            signal_a = signals.pop(0)
            signal_b = signals.pop(0)
            c_coef_str = f"c_%d_%d" % (c_idx, step)
            c_coef = SymSymbol(c_coef_str)
            c_sum_coefs.append(WireExpr(c_coef_str, SymSum(signal_a.expr, signal_b.expr)))
            signals.append(Signal( c_coef, max(signal_a.delay, signal_b.delay) + 1))
            step += 1

        return signals[0]

    M = [ [ SymZero() for _ in range (gf.degree) ] for _ in range(gf.degree) ]

    cells           = []
    cell_by_xor_set = {}

    # Initialize M[i][0] = a_i.
    for row in range(gf.degree):
        M[row][0] = MCell(SymSymbol(f"a[%d]" % row), [row], 0)
        remember_cell(M[row][0])

    # for col=1,...,m-1 loop {
    for col in range(1, gf.degree):

        # connect M0,col to Mm-1,col-1
        M[0][col] = M[gf.degree-1][col-1]
        remember_cell(M[0][col])

        # for row=1,...,m-1 loop {
        for row in range(1, gf.degree):

            # if p_row=0 then
            if p_coefs[row] == 0:
                # connect Mrow,col to Mrow-1,col-1
                M[row][col] = M[row-1][col-1]
            else:
                # new_func=Mrow-1,col-1 XOR Mm-1,col-1
                default_a   = M[row-1][col-1]
                default_b   = M[gf.degree-1][col-1]
                new_xor_set = default_a.xor_set ^ default_b.xor_set

                # CHECK 1: if this function has already been calculated, reuse
                # it directly instead of adding an XOR gate.
                if new_xor_set in cell_by_xor_set:
                    M[row][col] = cell_by_xor_set[new_xor_set]
                else:
                    # D=Delay(Mrow-1,col-1 XOR Mm-1,col-1); ...
                    best_a      = default_a
                    best_b      = default_b
                    best_delay  = calc_delay(default_a, default_b)

                    # CHECK 2: use an equivalent previously-calculated XOR pair
                    # when it improves delay.
                    if False:
                        # Direct implementation of the paper, but not efficient because
                        # it doesn't use the already existing cell_by_xor_set hash table.
                        for cell_a in cells:
                            for cell_b in cells:
                                possible_xor_set    = cell_a.xor_set ^ cell_b.xor_set
    
                                if possible_xor_set == new_xor_set:
                                    delay   = calc_delay(cell_a, cell_b)
                                    if delay < best_delay:
                                        best_a      = cell_a
                                        best_b      = cell_b
                                        best_delay  = delay
                    else:
                        for cell_a in cells:
                            needed_xor_set = cell_a.xor_set ^ new_xor_set
                            if needed_xor_set in cell_by_xor_set:
                                cell_b  = cell_by_xor_set[needed_xor_set]
                                delay   = calc_delay(cell_a, cell_b)
                                if delay < best_delay:
                                    best_a      = cell_a
                                    best_b      = cell_b
                                    best_delay  = delay

                    M[row][col] = connect_new_xor(row, col, best_a, best_b, new_xor_set)

            remember_cell(M[row][col])

    # Step 2: Multiply M with B
    c_coefs     = []
    c_delays    = []
    for row in range(gf.degree):
        terms   = [ (M[row][col], SymSymbol(f"b[%d]"%col)) for col in range(gf.degree) ]

        if latency_opt:
            c_signal    = latency_optimized_xor_sum(row, terms)
            c_j         = c_signal.expr
            c_delay     = c_signal.delay
        else:
            c_j         = SymSum([ SymFactor(cell.expr, b_sym) for cell, b_sym in terms ])
            c_delay     = balanced_xor_delay([ cell.delay + 1 for cell, _ in terms ])

        c_coefs.append(c_j)
        c_delays.append(c_delay)

    s = f'''
// Mastrovito GF multiplier
//
// XORs: {SymSum.nr_sums}
// ANDs: {SymFactor.nr_facts}
// Logic depth: {max(c_delays)}
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
        s += f'    wire %s = %s;\n' % (m_coef.name, m_coef.expr.flatten()) 

    for c_sum_coef in c_sum_coefs:
        s += f'    wire %s = %s;\n' % (c_sum_coef.name, c_sum_coef.expr.flatten())

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
    parser.add_argument('--poly', help='Primitive polynomial as a hex value (e.g. 0x11b).')
    parser.add_argument('-a', '--all', action='store_true', help='Output all known Verilog modules.')
    parser.add_argument('-d', '--mult_trad', action='store_true', help='Output traditional multiplier.')
    parser.add_argument('-m', '--mult_mast', action='store_true', help='Output Mastrovito multiplier.')
    parser.add_argument('--poly2power', action='store_true', help='Output poly2power.')
    parser.add_argument('--power2poly', action='store_true', help='Output power2poly.')
    parser.add_argument('--no_opt', action='store_true', help='Don\'t optimize away constant primitive terms')
    parser.add_argument('--mast_latency_opt', action='store_true', help='Optimize Mastrovito output XOR trees for latency.')

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

    if args.poly:
        gf = galois.GF(2**int(args.degree), irreducible_poly=int(args.poly, 16))
    else:
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
        s += verilog_gf_poly_mult_mastrovito(gf, prefix=prefix, latency_opt=args.mast_latency_opt)
        s += "\n"

        s += "\n"
    print(s, file=output)

    if output is not sys.stdout:
        output.close()
