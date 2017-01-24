from enum import Enum
class Ins(Enum):
	A_COMMAND = 1
	C_COMMAND = 2
	L_COMMAND = 3

class Code():
	def __init__(self, line):
		self.line = line
		self._decompose()

	def _decompose(self):
		if self.getCommandType() == Ins.C_COMMAND:
			jmp_idx = self.line.find(';')
			dest_idx = self.line.find('=')
			if jmp_idx > 0:	# jmp field exist
				self.jmp = self.line[ jmp_idx+1: ]
			if dest_idx > 0: # dest field exist
				self.dest = self.line[ :dest_idx ]

			jmp_idx = len(self.line) if jmp_idx == -1 else jmp_idx # find start of jmp or EOL
			dest_idx = 0 if dest_idx == -1 else dest_idx+1	# find end of dest or start of line
			self.cmp = self.line[dest_idx:jmp_idx]

	def getCommandType(self):
		if self.line[0] == '@':
			return Ins.A_COMMAND
		if self.line[0] == '(':
			return Ins.L_COMMAND
		return Ins.C_COMMAND

	def getSymbol(self):
		if self.getCommandType() == Ins.A_COMMAND:
			return self.line[1:]
		if self.getCommandType() == Ins.L_COMMAND:
			return self.line[1:-1]

	def getCmp(self):
		if self.getCommandType() == Ins.C_COMMAND and hasattr(self,'cmp'):
			return self.cmp
		return ""

	def getDest(self):
		if self.getCommandType() == Ins.C_COMMAND and hasattr(self,'dest'):
			return self.dest
		return ""

	def getJmp(self):
		if self.getCommandType() == Ins.C_COMMAND and hasattr(self,'jmp'):
			return self.jmp
		return ""

	def display(self):
		if self.getCommandType() == Ins.L_COMMAND:
			print "("+self.getSymbol()+")"
		elif self.getCommandType() == Ins.A_COMMAND:
			print("A:"+ self.getSymbol())
		elif self.getCommandType() == Ins.C_COMMAND:
			print("C:"+ self.getDest()+"="+self.getCmp()+";" + self.getJmp()) 
			


class Assembler(object):
	"""Hack language Assembler"""
	DEBUG = False
	def __init__(self, fname):
		super(Assembler, self).__init__()
		self.fname = fname
		self._parseFile();
	
	def _parseFile(self):
		with open(fname) as f:
			content = f.readlines()
			content = [x.strip().replace(" ","") for x in content]
			content = [x if x.find("//") == -1 else x[:x.find("//")] for x in content]
			content = [x for x in content if len(x) > 0 ]
			self.code_content = [Code(line) for line in content]
		

	def viewAssemblerSteps(self):
		for code in self.code_content:
			code.display()

	def buildSymbolTable(self):
		self.sym_table = {
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
		for code in self.code_content:
			if code.getCommandType() == Ins.L_COMMAND:
				line_no -= 1
				self.sym_table[code.getSymbol()] = line_no+1;
			line_no += 1

		if(Assembler.DEBUG):
			print self.sym_table

	def assemble(self):
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

	 	if not hasattr(self, 'sym_table'):
	 		self.buildSymbolTable()

	 	outfile = open(self.fname[:-4]+".hack", "w")
		print "Writing to ", outfile.name

	 	var_count = 16
	 	for code in self.code_content:
	 		if code.getCommandType() == Ins.A_COMMAND:
	 			sym = code.getSymbol()
	 			if sym.isdigit(): # @12
	 				value = int(sym)
	 			else: # @symbol
				 	if self.sym_table.has_key(sym):
				 		value = self.sym_table[sym]
	 				else:
	 					value = var_count
	 					self.sym_table[sym] = value
	 					var_count += 1
				value_str = '{0:015b}'.format(value)
			 	binary = "0" + value_str
			 	outfile.write(binary+"\n")
		 	elif code.getCommandType() == Ins.C_COMMAND:
		 		a_bit = "0" if (code.getCmp()).find('M') == -1 else "1"
				d1_bit = "0" if code.getDest().find('A') == -1 else "1"
				d2_bit = "0" if code.getDest().find('D') == -1 else "1"
				d3_bit = "0" if code.getDest().find('M') == -1 else "1"
				cmp_bits = LOOKUP_COM[code.getCmp()] if LOOKUP_COM.has_key(code.getCmp()) else "000"
				jmp_bits = LOOKUP_JMP[code.getJmp()] if LOOKUP_JMP.has_key(code.getJmp()) else "000"
				binary = "111" + a_bit + cmp_bits + d1_bit + d2_bit + d3_bit + jmp_bits
				outfile.write(binary+"\n")
		outfile.close()

import sys
if len(sys.argv) > 1:
	fname = sys.argv[1]
	a = Assembler(fname)
	a.assemble()
	#a.viewAssemblerSteps()
