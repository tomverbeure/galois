
#include <stdio.h>

#include "gf256_arith.h"

int main() {
    cxxrtl_design::p_gf256__poly__mult__mastrovito top;
    top.step();

    for(unsigned int a=0;a<256;++a){
        for(unsigned int b=0;b<256;++b){
            top.p_poly__a.set(a);
            top.p_poly__b.set(b);
            top.step();
            unsigned int poly_out = top.p_poly__out.get<unsigned int>();
            printf("%02x,%02x,%02x\n", a, b, poly_out);
        }
    }
}

