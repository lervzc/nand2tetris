class SymbolTable(object):
	STATIC, FIELD, ARG, VAR = ["static", "this", "argument", "local"]
	"""This class manages 2 hashtables used in jack language compilation"""

	def __init__(self):
		self.classTable = {}
		self.subTable = {}
		self.declaration = True
		self.countHash = {
			self.STATIC : 0,
			self.FIELD : 0,
			self.ARG : 0,
			self.VAR : 0
		}

	def start_subroutine(self):
		""" Starts a new subroutine (resets subTable)"""

		self.subTable = {}
		self.countHash[self.VAR] = 0
		self.countHash[self.ARG] = 0
		self.declaration = True

	def stop_declaration(self):
		self.declaration = False

	def define(self, name, _type, kind):
		""" Define a new symbol """

		if(kind == self.ARG or kind == self.VAR):
			# Sub routine scope
			self.subTable[name] = [_type, self.var_count(kind), kind]
		else:
			self.classTable[name] = [_type, self.var_count(kind), kind]
			# class scope

		self.countHash[kind] += 1

	def var_count(self, kind):
		return self.countHash[kind]

	def isDeclaration(self):
		return self.declaration

	def type_of(self, name):
		if name in self.subTable:
			return self.subTable[name][0]
		elif name in self.classTable:
			return self.classTable[name][0]
		else:
			return None

	def kind_of(self, name):
		"""ARG, VAR"""
		if name in self.subTable:
			return self.subTable[name][2]
		elif name in self.classTable:
			return self.classTable[name][2]
		else:
			return None


	def index_of(self, name):
		if name in self.subTable:
			return self.subTable[name][1]
		elif name in self.classTable:
			return self.classTable[name][1]
		else:
			return None

