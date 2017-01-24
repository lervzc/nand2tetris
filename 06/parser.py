
from enum import Enum
class Ins(Enum):
	A_COMMAND = 1
	C_COMMAND = 2
	L_COMMAND = 3

class Assembler(object):
	"""Hack language Assembler"""
	def __init__(self, arg):
		super(Assembler, self).__init__()
		self.arg = arg
		print self.arg
		

class Parser:
	'splits each instruction into separate components'

	def __init__(self, instruction):
		instruction = instruction.replace(" ", "")
		comment_idx = instruction.find("//")
		if comment_idx != -1:
			instruction = instruction[:comment_idx]
		if len(instruction) == 0:
			self.nil=True
			return None

		if instruction[0] == "(":
			label_idx = instruction.find(')')
			if label_idx > 0:
				self.label = instruction[1:label_idx]
		elif instruction[0] == '@':
			# A-instruction
			self.astruct = instruction[1:]
		else:
			# C-instruction
			self.jmp = ""
			self.com = ""
			self.dest = ""
			jmp_idx = instruction.find(';')
			dest_idx = instruction.find('=')
			if jmp_idx > 0:
				self.jmp = instruction[jmp_idx+1:]
			if dest_idx > 0:
				self.dest = instruction[:dest_idx]

			jmp_idx = len(instruction) if jmp_idx == -1 else jmp_idx
			dest_idx = 0 if dest_idx == -1 else dest_idx+1
			self.com = instruction[dest_idx :jmp_idx]
	def getType(self):
		if hasattr(self, 'nil'):
			return "nil"
		elif hasattr(self, 'astruct'):
			return "A"
		elif hasattr(self, 'com'):
			return "C"
		elif hasattr(self, 'label'):
			return "label"
	def display(self):
		if self.getType() == "nil":
			print("#"+ self.nil)
		elif self.getType() == "label":
			print "("+self.label+")"
		elif self.getType() == "A":
			print("A:"+ self.astruct)
		elif self.getType() == "C":
			print("C:"+ self.dest+"="+self.com+";" + self.jmp)

# dest d1 d2 d3 jump j1 j2 j3
# null 	0 0 0 	null 0 0 0
# M 	0 0 1 		JGT  0 0 1
# D 	0 1 0 		JEQ  0 1 0
# MD 	0 1 1 		JGE  0 1 1
# A 	1 0 0 		JLT  1 0 0
# AM 	1 0 1 		JNE  1 0 1
# AD 	1 1 0 		JLE  1 1 0
# AMD	1 1 1 	JMP  1 1 1
# 0 101010
# 1 111111
# -1 1 1 1 0 1 0
# D 001100
# A 110000 M
# !D 0 0 1 1 0 1
# !A 1 1 0 0 0 1 !M
# -D 0 0 1 1 1 1
# -A 1 1 0 0 1 1 -M
# D+1 0 1 1 1 1 1
# A+1 1 1 0 1 1 1 M+1
# D-1 0 0 1 1 1 0
# A-1 1 1 0 0 1 0 M-1
# D+A 0 0 0 0 1 0 D+M
# D-A 0 1 0 0 1 1 D-M
# A-D 0 0 0 1 1 1 M-D
# D&A 0 0 0 0 0 0 D&M
# D|A 0 1 0 1 0 1 D|M

class Code:
	'translate components into binary string'
	LOOKUP_COM = {
		"0":"101010",
		"1":"111111",
		"-1":"111010",
		"D":"001100",
		"A":"110000",
		"M":"110000",
		"!D":"001101",
		"!A":"110001",
		"!M":"110001",
		"-D":"001111",
		"-A":"110011",
		"-M":"110011",
		"D+1":"011111",
		"A+1":"110111",
		"M+1":"110111",
		"D-1":"001110",
		"A-1":"110010",
		"M-1":"110010",
		"D+A":"000010",
		"D+M":"000010",
		"D-A":"010011",
		"D-M":"010011",
		"A-D":"000111",
		"M-D":"000111",
		"D&A":"000000",
		"D&M":"000000",
		"D|A":"010101",
		"D|M":"010101"
	}
 	LOOKUP_JMP = {
 		"JGT":"001",
 		"JEQ":"010",
 		"JGE":"011",
 		"JLT":"100",
 		"JNE":"101",
 		"JLE":"110",
 		"JMP":"111"
 	}
 	def __init__(self, parser, sym_table=None,var_count=None):
 		self.binary = ""
 		if hasattr(parser, 'astruct'):
 			if parser.astruct.isdigit():
	 			value = int(parser.astruct)
	 		else:
	 			if sym_table is not None:
	 				if sym_table.has_key(parser.astruct):
	 					value = sym_table[parser.astruct] 
	 				else:
	 					print str(var_count)+":"+ parser.astruct
	 					value = var_count
	 					var_count += 1
	 		value_str = '{0:015b}'.format(value)
 			self.binary = "0" + value_str
		elif hasattr(parser, 'com'):
			a_bit = "0" if parser.com.find('M') == -1 else "1"
			d1_bit = "0" if parser.dest.find('A') == -1 else "1"
			d2_bit = "0" if parser.dest.find('D') == -1 else "1"
			d3_bit = "0" if parser.dest.find('M') == -1 else "1"
			com_bits = self.LOOKUP_COM[parser.com] if self.LOOKUP_COM.has_key(parser.com) else "000"
			jmp_bits = self.LOOKUP_JMP[parser.jmp] if self.LOOKUP_JMP.has_key(parser.jmp) else "000"
			self.binary = "111" + a_bit + com_bits + d1_bit + d2_bit + d3_bit + jmp_bits
	
	def toBinaryString(self):
		return self.binary
# class SymbolTable:
# 	'manages the symbol table'
# 	def __init__(self, parser):
import sys

if len(sys.argv) > 1:
	fname = sys.argv[1]
	with open(fname) as f:
		
		content = f.readlines()
		content = [x.strip() for x in content]
		sym_table = {
			"SP":0,
			"LCL":1,
			"ARG":2,
			"THIS":3,
			"THAT":4,
			"SCREEN":16384,
			"KBD":24576,
			"R0":0,
			"R1":1,
			"R2":2,
			"R3":3,
			"R4":4,
			"R5":5,
			"R6":6,
			"R7":7,
			"R8":8,
			"R9":9,
			"R10":10,
			"R11":11,
			"R12":12,
			"R13":13,
			"R14":14,
			"R15":15
		}
		line_no = 0
		for line in content: # first pass, build sym table
			p = Parser(line)
			if not hasattr(p,"nil"):
				if p.getType() == "label":
					line_no -= 1
					sym_table[p.label] = line_no+1;
				line_no += 1
		print sym_table
		outfile = open(fname[:-4]+".hack", "w")
		print "Writing to ", outfile.name
		var_count = 16
		for line in content:
			p = Parser(line)
			if not hasattr(p,"nil") and p.getType() != "label":
				#print p.display()
				c = Code(p,sym_table,var_count)
				outfile.write(c.toBinaryString()+"\n")
		outfile.close()



