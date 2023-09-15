#! /usr/bin/env python3

import galois
import numpy

#print("Galois")

if False:
    GF = galois.GF(2**4)
    print(GF.properties)
    #x = GF([236,87,38,112])
    x = GF([12,2,1,8])
    print(x)
    GF.repr("poly")
    print(x)
    GF.repr("power")
    print(x)

if False:
    GF = galois.GF(2**4)
    print(GF.properties)
    GF.repr("power")
    print(GF.order)

    x = GF(1)
    for i in range(0,16):
        GF.repr("power")
        print(x)
        GF.repr("poly")
        print(x)
        GF.repr("int")
        print(x)
        x = x * GF(2)

def sym_test():

    a       = SymSymbol("a[0]")
    b       = SymSymbol("b[0]")
    c       = SymSymbol("c[1]")
    one     = SymLeafValue(1)
    zero    = SymLeafValue(0)

    n1 = SymFactor(a,b)
    nl
    n2 = SymFactor(a,c)
    n3 = SymFactor(c,one)
    n4 = SymSum(n1, n2)
    n5 = SymSum(n4, zero)

    print(n5.flatten())

def mastrovito_mul(a_coefs_in, b_coefs_in, p_coefs_in):   # Coefs are MSB first
    GF2 = galois.GF(2)

    # LSB first...
    a_coefs = a_coefs_in[::-1]
    b_coefs = b_coefs_in[::-1]
    p_coefs = p_coefs_in[::-1]

    # Step 1: create matrix
    # (i,j) are swapped around compared to the paper...
    M = GF2.Identity(4)

    M[0] = [ a_coefs[0], a_coefs[1], a_coefs[2], a_coefs[3] ]

    for i in range(1, 4):       # Go through all rows
        M[i] = [
            M[i-1][3],
            M[i-1][0] + (M[i-1][3] * p_coefs[1]),
            M[i-1][1] + (M[i-1][3] * p_coefs[2]),
            M[i-1][2] + (M[i-1][3] * p_coefs[3])
        ]

    c_coefs = []
    for j in range(0,4):
        c = GF2(0)
        for i in range(0,4):
            c += M[i][j] * b_coefs[i]
        c_coefs.append(c)

    c_coefs.reverse()
    return c_coefs

if True:
    GF2 = galois.GF(2)
    GF16 = galois.GF(2**4)

    GF2.repr("int")
    GF16.repr("int")

    p = GF16.irreducible_poly
    p_coefs = [(int(p)>>3)&1, (int(p)>>2)&1, (int(p)>>1)&1, (int(p)>>0)&1]

    for a_int in range(0,16):
        for b_int in range(0,16):
            #print(a_int,b_int)

            #a_coefs = [1,1,0,1]
            #b_coefs = [0,1,1,0]

            a_coefs = [0] * 4
            for i in range(0,4):
                a_coefs[3-i] = (a_int>>i)&1     # MSB first

            b_coefs = [0] * 4
            for i in range(0,4):
                b_coefs[3-i] = (b_int>>i)&1
        
            a = galois.Poly(a_coefs, GF2)
            b = galois.Poly(b_coefs, GF2)
        
            c = (a*b) % p

            c_coefs = [(int(c)>>3)&1, (int(c)>>2)&1, (int(c)>>1)&1, (int(c)>>0)&1]
            c_coefs_m = mastrovito_mul(a_coefs, b_coefs, p_coefs)
        
            c_coefs = GF2(c_coefs)
            c_coefs_m = GF2(c_coefs_m)
        
            #print(c_coefs)
            #print(c_coefs_m)

            if numpy.array_equal(c_coefs, c_coefs_m):
                #print("OK!")
                pass
            else:
                #print(c_coefs)
                #print(c_coefs_m)
                print("MISMATCH!")
                pass

            print(f"%02x,%02x,%02x"%(int(a),int(b),c))

if False:
    sym_test()

