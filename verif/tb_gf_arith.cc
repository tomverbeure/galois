
#include <stdio.h>

#ifdef MASTROVITO
#include "gf_poly_mult_mastrovito.h"
#else
#ifdef REF
#include "gf_poly_mult_ref.h"
#else
#include "gf_poly_mult.h"
#endif
#endif

int main() {
    cxxrtl_design:: DESIGN_TOP top;
    top.step();

    for(unsigned int a=0;a<GF;++a){
        for(unsigned int b=0;b<GF;++b){
            top.p_poly__a.set(a);
            top.p_poly__b.set(b);
            top.step();
            unsigned int poly_out = top.p_poly__out.get<unsigned int>();
            printf("%02x,%02x,%02x\n", a, b, poly_out);
        }
    }
}

