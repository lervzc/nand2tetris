// This file is part of www.nand2tetris.org
// and the book "The Elements of Computing Systems"
// by Nisan and Schocken, MIT Press.
// File name: projects/04/Fill.asm

// Runs an infinite loop that listens to the keyboard input.
// When a key is pressed (any key), the program blackens the screen,
// i.e. writes "black" in every pixel;
// the screen should remain fully black as long as the key is pressed. 
// When no key is pressed, the program clears the screen, i.e. writes
// "white" in every pixel;
// the screen should remain fully clear as long as no key is pressed.

// Put your code here

@8192
D=A
@screen_size
M=D

@current_color // white
M=0

(LOOP)
	@KBD
	D=M
	@BLACK
	D; JGT
	@WHITE
	D; JEQ

(DRAW)
	@i
	M=0

	@screen_size
	D=M
	@n
	M=D

	@cursor
	M=0

	@color
	D=M
	@current_color
	M=D

	(DRAW_LOOP)
		// if drawing completes (i == n)
		@i
		D=M
		@n
		D=D-M
		@LOOP // Exit back to main loop
		D; JEQ

		// SCREEN[base+i] = color
		@SCREEN
		D=A
		@i
		D=D+M
		@cursor
		M=D

		@color
		D=M
		@cursor
		A=M
		M=D

		// i++
		@i
		M=M+1

		@DRAW_LOOP
		0;JMP


(BLACK)
	@color
	M=-1

	// Draw if current color is white
	@current_color
	D=M
	@DRAW
	D;JEQ

	@LOOP
	0;JMP

(WHITE)
	@color
	M=0

	// Draw if current color is black
	@current_color
	D=M
	@DRAW
	D;JLT

	@LOOP
	0;JMP