// This file is part of www.nand2tetris.org
// and the book "The Elements of Computing Systems"
// by Nisan and Schocken, MIT Press.
// File name: projects/04/Mult.asm

// Multiplies R0 and R1 and stores the result in R2.
// (R0, R1, R2 refer to RAM[0], RAM[1], and RAM[2], respectively.)

// Put your code here.

// For 0 to R0
// 		Add R1 to R2

@R2 // reset to 0
M=0

@R0
D=M
@ZERO // Multiplication by 0
D;JEQ
@loop_count
M=D


@R1
D=M
@ZERO // Multiplication by 0
D;JEQ
@add_by
M=D

@loop_count // Check if loop counts is positive
D=M
@LOOP
D;JGT	// start loop if positive
// negative loop count, check if add_by is negative too
@add_by
D=M
@FLIP // Flip both variables
D; JLT

// Swap loop count and add by
@loop_count
D=M
@temp // temp = loop_count
M=D
@add_by
D=M
@loop_count // loop_count = add_by
M=D
@temp	
D=M
@add_by // add_by = temp
M=D


(LOOP)
	@loop_count
	D=M
	@END
	D;JLE

	@add_by
	D=M
	@R2
	M=D+M

	@loop_count
	M=M-1

	@LOOP
	0;JMP

(FLIP)
	@loop_count
	M=-M
	@add_by
	M=-M
	@LOOP
	0; JMP


(ZERO)
	@R2
	M=0
	@END
	0;JMP


(END)
	@END
	0;JMP