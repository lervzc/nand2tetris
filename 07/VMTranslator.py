import os.path
class Parser(object):
	def __init__(self, fname):
		super(Parser, self).__init__()
		self.fname = fname
		self._open_file()

	def _open_file(self):
		self.file = open(self.fname,'r')

	def parse(self):
		for line in self.file:
			line = line.strip()
			comment_idx = line.find("//")
			if comment_idx != -1:
				line = line[:comment_idx]
			if len(line) > 0:
				yield Command(line)

class Command(object):
	C_ARITHMETIC, C_PUSH, C_POP, C_LABEL, C_GOTO, C_IF, C_FUNCTION, C_RETURN, C_CALL = range(9)
	ARITHMETICS = ['add', 'sub', 'neg', 'lt', 'gt' ,'eq', 'and', 'or', 'not']
	def __init__(self, line):
		super(Command, self).__init__()
		self.line = line
		self._decompose()

	def _decompose(self):
		command_line = self.line.split(' ')
		self.command = command_line[0]
		if len(command_line) > 1:
			self.segment = command_line[1]
			if command_line[2].isdigit():
				self.idx = int(command_line[2])

	def commandType(self):
		if self.command == 'push':
			return Command.C_PUSH
		elif self.command == 'pop':
			return Command.C_POP
		elif self.command in Command.ARITHMETICS:
			return Command.C_ARITHMETIC
		#TODO: more command types

	def arg1(self):
		if self.commandType() != Command.C_RETURN:
			return self.command

	def arg2(self):
		if self.commandType() != Command.C_ARITHMETIC:
			return self.segment

	def arg3(self):
		return self.idx

	def display(self):
		if hasattr(self, 'segment'):
			print self.command + " " + self.segment +  " " + str(self.idx)
		else:
			print self.command

class CodeWriter(object):
	LOGICAL_SKIPPERS = ["eq","gt","lt"]
	INF_LOOP = """
	(INFINITE_LOOP)
		@INFINITE_LOOP
		0;JMP 
	"""
	ARITHMETICS_LOOKUP = {
		"add" : """
					@SP
					AM=M-1
					D=M
					@SP
					A=M-1
					M=D+M
				""",
		"sub" : """
					@SP
					AM=M-1
					D=M
					@SP
					A=M-1
					M=M-D
					""",
		"neg" : """
					@SP
					A=M-1
					M=-M
				""",
		"eq" : """
					@SP
					AM=M-1
					D=M
					A=A-1
					D=M-D
					M=0 //assume false
					@R14 // skip to line #
					A=M
					D;JNE // skip if not eq
					@SP
					A=M-1
					M=-1
				""",
		"gt" : """
					@SP
					AM=M-1
					D=M
					A=A-1
					D=M-D
					M=0 //assume false
					@R14 // skip to line #
					A=M
					D;JLE // skip if not gt
					@SP
					A=M-1
					M=-1
				""",
		"lt" : """
					@SP
					AM=M-1
					D=M
					A=A-1
					D=M-D
					M=0 //assume false
					@R14 // skip to line #
					A=M
					D;JGE // skip if not lt
					@SP
					A=M-1
					M=-1
				""",
		"and" : """
					@SP
					AM=M-1
					D=M
					A=A-1
					M=D&M
				""",
		"or" : """
					@SP
					AM=M-1
					D=M
					A=A-1
					M=D|M
				""",
		"not" : """
				@SP
				A=M-1
				M=!M
				"""
	}
	SEGMENT_MAP = {
		"local" : "LCL",
		"argument" : "ARG",
		"this" : "THIS",
		"that" : "THAT"
	}
	def __init__(self, outname):
		self.outfile = open(outname, 'w')
		filename = os.path.basename(self.outfile.name)
		self.filename = filename.replace(".asm","")
		print "Writing to " + outname
		self.code_count = 0


	def vm_push(self, segment, idx):
		if segment == 'temp':
			idx = idx + 5 # temp segment 5-12
			return """
				@{:d}
				D=M
				@SP
				A=M
				M=D
				@SP
				M=M+1
			""".format(idx)

		if segment == 'constant':
			return """
				@{:d}
				D=A
				@SP
				A=M
				M=D
				@SP
				M=M+1
			""".format(idx)

		if CodeWriter.SEGMENT_MAP.has_key(segment):
			seg = CodeWriter.SEGMENT_MAP[segment]
			return """
				@{:d}
				D=A
				@{:s}
				A=D+M
				D=M
				@SP
				A=M
				M=D
				@SP
				M=M+1
			""".format(idx, seg)

		# stack.push(var)
		if segment == 'static':
			vname = self.filename+"."+str(idx)
			return """
				@{:s}
				D=M
				@SP
				A=M
				M=D
				@SP
				M=M+1
			""".format(vname)

		# idx  =  0   1
		# *SP=THIS/THAT, SP++ 
		if segment == 'pointer':
			target = "THIS" if idx == 0 else "THAT"
			return """
				@{:s}
				D=M
				@SP
				A=M
				M=D
				@SP
				M=M+1
			""".format(target)

		return ""

	def vm_pop(self, segment, idx):
		# addr = segPointer + i, SP--, *addr=*SP
		if CodeWriter.SEGMENT_MAP.has_key(segment):
			seg = CodeWriter.SEGMENT_MAP[segment]
			return """
				@{:d}
				D=A
				@{:s}
				D=D+M
				@R15
				M=D
				@SP
				AM=M-1
				D=M
				@R15
				A=M
				M=D
			""".format(idx, seg)

		if segment == 'temp':
			idx = idx + 5 # temp segment 5-12
			return """
				@SP
				A=M-1
				D=M
				@{:d}
				M=D
				@SP
				M=M-1
			""".format(idx)

		#D = stack.pop
		#@var
		#M=D
		if segment == 'static':
			vname = self.filename+"."+str(idx)
			return """
				@SP
				AM=M-1
				D=M
				@{:s}
				M=D
			""".format(vname)
		# idx  =  0   1
		# SP--, THIS/THAT = *SP 
		if segment == 'pointer':
			target = "THIS" if idx == 0 else "THAT"
			return """
				@SP
				AM=M-1
				D=M
				@{:s}
				M=D
			""".format(target)

		return ""

	def translate(self, code):
		c_type = code.commandType()
		if c_type == Command.C_ARITHMETIC:
			self.writeArithmetic(code.arg1())
		elif c_type== Command.C_POP or c_type == Command.C_PUSH:
			self.writePushPop(code.arg1(), code.arg2(), code.arg3())

	def writeArithmetic(self, command):
		self.write("// "+command)
		if self.ARITHMETICS_LOOKUP.has_key(command):
			asm = self.ARITHMETICS_LOOKUP[command]
			if command in self.LOGICAL_SKIPPERS: 
				ret_asm = """
							@{:d}
							D=A
							@R14
							M=D
						""".format(self.code_count+self.countCommand(asm)+4) # count target skip lines
				self.write(ret_asm)
			self.write(asm)

	def writePushPop(self, command, segment, idx):
		self.write("// "+command + " " + segment + " " + str(idx))
		if command == 'push':
			asm = self.vm_push(segment, idx)
		elif command == 'pop':
			asm = self.vm_pop(segment, idx)
		self.write(asm)

	def countCommand(self, asm):
		asm = self.strip_tabs(asm)
		lines = asm.split('\n')
		count = sum( len(l) > 0 and l[:2] != '//' and l.find("(") == -1 for l in lines )
		return count

	def write(self, asm):
		asm = self.strip_tabs(asm)
		self.code_count += self.countCommand(asm)
		self.outfile.write(asm + "\n")

	def strip_tabs(self, asm):
		return asm.replace("\t","").strip()

	def close(self):
		self.write(self.INF_LOOP)
		self.outfile.close()
		print "file closed."

import sys
if len(sys.argv) > 1:
	fname = sys.argv[1]
	oname = fname[:-3]+".asm"
	writer = CodeWriter(oname)

	a = Parser(fname)
	for code in a.parse():
		#code.display()
		writer.translate(code)
	writer.close()

