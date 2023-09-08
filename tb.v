module galois_tb(
    input           clk, 
    input  [7:0]    poly_in, 
    output [7:0]    poly_out
    );

    wire    [7:0]   power;
    reg    [7:0]    power_p1;
    reg    [7:0]    poly_out_pre;

    gf_poly2power_8 poly2power(
        poly_in,
        power,
    );

    always @(posedge clk) begin
        power_p1    <= power;
    end

    gf_power2poly_8 power2poly(
        power_p1,
        poly_out_pre
    );

    always @(posedge clk) begin
        poly_out <= poly_out_pre;
    end

endmodule
