
#include <stdio.h>

#ifdef MASTROVITO
#include "gf256_poly_mult_mastrovito.h"
#else
#include "gf256_poly_mult.h"
#endif

int main() {
#ifdef MASTROVITO
    cxxrtl_design::p_gf256__poly__mult__mastrovito top;
#else
    cxxrtl_design::p_gf256__poly__mult top;
#endif
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

