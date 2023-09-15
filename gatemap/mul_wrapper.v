
// Add FF wrapper around Galois logic

module gf256_poly_mult_mastrovito_wrapper(
    input            clk,
    input      [7:0] poly_a,
    input      [7:0] poly_b,
    output reg [7:0] poly_out
    );

    reg [7:0] poly_a_p1;
    reg [7:0] poly_b_p1;
    reg [7:0] poly_out_p1;

    always @(posedge clk) begin
        poly_a_p1 <= poly_a;
        poly_b_p1 <= poly_b;
    end

    gf256_poly_mult_mastrovito mul(
        poly_a_p1, 
        poly_b_p1, 
        poly_out_p1
    );

    always @(posedge clk) begin
        poly_out <= poly_out_p1;
    end

endmodule

module gf65536_poly_mult_mastrovito_wrapper(
    input            clk,
    input      [15:0] poly_a,
    input      [15:0] poly_b,
    output reg [15:0] poly_out
    );

    reg [15:0] poly_a_p1;
    reg [15:0] poly_b_p1;
    reg [15:0] poly_out_p1;

    always @(posedge clk) begin
        poly_a_p1 <= poly_a;
        poly_b_p1 <= poly_b;
    end

    gf65536_poly_mult_mastrovito mul(
        poly_a_p1, 
        poly_b_p1, 
        poly_out_p1
    );

    always @(posedge clk) begin
        poly_out <= poly_out_p1;
    end

endmodule
