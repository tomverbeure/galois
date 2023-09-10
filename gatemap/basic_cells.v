// Verilog version of basic cells with timing arcs for sta command
module INV(
    input A,
    output Y);

    specify 
        (A => Y) = 1;
    endspecify
endmodule

module BUF(
    input A,
    output Y);

    specify 
        (A => Y) = 1;
    endspecify
endmodule

module NAND2(
    input A,
    input B,
    output Y);

    specify 
        (A => Y) = 1;
        (B => Y) = 1;
    endspecify
endmodule

module XOR2(
    input A,
    input B,
    output Y);

    specify 
        (A => Y) = 1;
        (B => Y) = 1;
    endspecify
endmodule

module DFF(
    input D,
    input CK,
    output Q);

    specify 
        (posedge CK *> (Q : D)) = 1;
        $setup(D, posedge CK, 0);
    endspecify
endmodule


