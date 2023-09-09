module galois_tb_power(
    input           clk, 
    input  [7:0]    poly_in, 
    output [7:0]    poly_out
    );

    wire   [7:0]    power;
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

module galois_tb_mul_mastrovito(
    input           clk, 
    input  [7:0]    poly_a, 
    input  [7:0]    poly_b, 
    output [7:0]    poly_out
    );

    reg    [7:0]    poly_a_p1;
    reg    [7:0]    poly_b_p1;
    reg    [7:0]    poly_out_p1;

    always @(posedge clk) begin
        poly_a_p1    <= poly_a;
        poly_b_p1    <= poly_b;
    end

    gf_poly_mul_mastrovito_8 mul_mastrovito(
        poly_a_p1,
        poly_b_p1,
        poly_out_p1
    );

    always @(posedge clk) begin
        poly_out <= poly_out_p1;
    end

endmodule
