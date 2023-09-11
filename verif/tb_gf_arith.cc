
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
#ifdef MASTROVITO
    cxxrtl_design::p_gf__poly__mult__mastrovito top;
#else
#ifdef REF
    cxxrtl_design::p_traditional__ab__mod__p__8 top;
#else
    cxxrtl_design::p_gf__poly__mult top;
#endif
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

