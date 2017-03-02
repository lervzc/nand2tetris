import os.path
import sys

from JackTokenizer import JackTokenizer
from Token import Token
from SymbolTable import SymbolTable
from VMWriter import VMWriter


class CompilationEngine(object):
    KEYWORD_CONST = [Token.TRUE, Token.FALSE, Token.NULL, Token.THIS]
    OPS_MAP = {
        '+': "add",
        '-': "sub",
        '*': "Math.multiply",
        '/': "Math.divide",
        '&': "and",
        '|': "or",
        '<': "lt",
        '>': "gt",
        '=': "eq"
    }
    UNARY_OP_LIST = ['-', '~']

    def __init__(self, jackfile):
        self.tokenizer = JackTokenizer(jackfile)
        self.while_count = 0
        self.if_count = 0
        # self.tokenizer.saveToFile()

        dirname = os.path.dirname(jackfile)
        basename = os.path.basename(jackfile)

        outname = os.path.join(dirname, basename[:-5]+".vm")
        self.writer = VMWriter(outname)

        self.compileClass()
        self.writer.close()

    def peekTokenString(self):
        """ Get current token string without consuming """
        return self.tokenizer.current_token().stringToken()

    def eatRawString(self, string_token):
        tok = self.tokenizer.current_token()
        string_name = tok.stringToken()
        if(not self.matchRawString(string_token)):
            self._handleError(
                "Expected: " + str(string_token) + ", but gotten :" + string_name)
        elif self.tokenizer.has_next_token():
            self.tokenizer.next_token()
            return tok.stringToken()
        else:
            self._handleError("Unexpected end of line")

    def eatSymbol(self, string_token=None):
        tok = self.tokenizer.current_token()
        string_name = tok.stringToken()
        if (tok.tokenType() != Token.SYMBOL):
            self._handleError("Expected symbol but gotten " + tok.tokenType())
        elif (string_token is not None and string_name != string_token):
            self._handleError(
                "Expected: " + string_token + ", but gotten :" + string_name)
        elif self.tokenizer.has_next_token():
            self.tokenizer.next_token()
            return tok.stringToken()
        else:
            self._handleError("Unexpected end of line")

    def eatIdentifier(self):
        tok = self.tokenizer.current_token()
        if(tok.tokenType() != Token.IDENTIFIER):
            self._handleError(
                "Expected identifier but gotten " + tok.tokenType() + "," + tok.stringToken())
        elif self.tokenizer.has_next_token():

            kind = self.symbol_table.kind_of(tok.stringToken())
            var_type = self.symbol_table.type_of(tok.stringToken())
            idx = self.symbol_table.index_of(tok.stringToken())
            kind = kind if kind is not None else "CLASS/SUB"
            isDec = "Declaring, " if self.symbol_table.isDeclaration(
            ) else "Using, "
            self.tokenizer.next_token()

            return tok.stringToken()
        else:
            self._handleError("Unexpected end of line")

    def eatKeyword(self, keyword_type=None):
        tok = self.tokenizer.current_token()
        if(tok.tokenType() != Token.KEYWORD):
            self._handleError("Expected keyword but gotten " + tok.tokenType())
        elif(keyword_type is not None and tok.keyword() != keyword_type):
            self._handleError("Expected keyword but gotten " + tok.tokenType())
        elif self.tokenizer.has_next_token():
            self.tokenizer.next_token()
            return tok.stringToken()
        else:
            self._handleError("Unexpected end of line")

    def eatType(self):
        tok = self.tokenizer.current_token()
        if(self.matchType()):
            tok_str = tok.stringToken()
            self.tokenizer.next_token()
            return tok_str
        else:
            self._handleError("Expected type but gotten " + tok.stringToken())

    def eat(self):
        tok = self.tokenizer.current_token()
        if self.tokenizer.has_next_token():
            self.tokenizer.next_token()
            return tok.stringToken()
        else:
            self._handleError("Unexpected end of line")

    def matchType(self):
        tok = self.tokenizer.current_token()
        string_name = tok.stringToken()
        return string_name in ['int', 'char', 'boolean'] or tok.tokenType() == Token.IDENTIFIER

    def matchRawString(self, string_to_match):
        """Match string or array of strings"""
        tok = self.tokenizer.current_token()
        string_tok = tok.stringToken()
        if type(string_to_match) is list or type(string_to_match) is dict:
            return string_tok in string_to_match
        else:
            return string_tok == string_to_match

    def _handleError(self, error):
        print error
        raise StandardError(error)

    def compileClass(self):
        """
            CLASS Grammer:
            'class' className {
                varDeclarations*
                statements*
            }
        """
        self.symbol_table = SymbolTable()

        self.eatRawString("class")
        self.class_name = self.eatIdentifier()
        self.eatSymbol("{")
        while (self.matchRawString(['static', 'field'])):
            self.compileClassVarDec()

        self.symbol_table.stop_declaration()

        while (self.matchRawString(['constructor', 'function', 'method'])):
            self.compileSubroutine()

        self.eatSymbol("}")

    def compileClassVarDec(self):
        _kind = SymbolTable.FIELD if self.eatKeyword(
        ) == 'field' else SymbolTable.STATIC   # field or static
        _type = self.eatType()  # return type
        _name = self.eatIdentifier()  # var name
        self.symbol_table.define(_name, _type, _kind)

        while (self.matchRawString(",")):
            self.eatSymbol(',')
            _name = self.eatIdentifier()  # var name
            self.symbol_table.define(_name, _type, _kind)

        self.eatSymbol(';')
        return

    def compileSubroutine(self):
        self.symbol_table.start_subroutine()

        subroutine = self.eatRawString(['constructor', 'function', 'method'])

        if(self.matchType() or self.matchRawString('void')):
            self.eat()
        else:
            self._handleError("subroutine return type expected")

        if subroutine == 'method':
            self.symbol_table.define('this', self.class_name, SymbolTable.ARG)

        func_name = self.eatIdentifier()
        self.eatSymbol("(")
        self.compileParameterList()
        self.eatSymbol(")")
        self.eatSymbol("{")
        num_locals = 0
        while(self.matchRawString('var')):
            num_locals += self.compileVarDec()

        self.symbol_table.stop_declaration()
        self.writer.write_function(self.class_name+"."+func_name, num_locals)
        # setup code
        if subroutine == 'method':
            self.writer.write_push("argument", 0)
            self.writer.write_pop("pointer", 0)

        elif subroutine == 'constructor':
            class_size = self.symbol_table.var_count(SymbolTable.FIELD)
            self.writer.write_push("constant", class_size)
            self.writer.write_call("Memory.alloc", 1)  # allocate space
            self.writer.write_pop("pointer", 0)

        self.compileStatements()

        self.eatSymbol("}")

        return

    def compileParameterList(self):
        """((type varNmae) (',' type varName)*)?"""
        num_arg = 0
        if(self.matchType()):
            _type = self.eatType()
            _name = self.peekTokenString()
            self.symbol_table.define(_name, _type, SymbolTable.ARG)
            self.eatIdentifier()
            num_arg = 1
            while(self.matchRawString(",")):
                self.eatSymbol(',')
                _type = self.eatType()
                _name = self.peekTokenString()
                self.symbol_table.define(_name, _type, SymbolTable.ARG)
                self.eatIdentifier()
                num_arg += 1

        return num_arg

    def compileVarDec(self):
        """'var' type varName (',' varName)*"""
        num_locals = 0
        if self.matchRawString('var'):
            self.eatKeyword()
            _type = self.eatType()
            _name = self.peekTokenString()
            self.symbol_table.define(_name, _type, SymbolTable.VAR)
            self.eatIdentifier()
            num_locals = 1
            while(self.matchRawString(",")):
                self.eatSymbol(',')
                _name = self.peekTokenString()
                self.symbol_table.define(_name, _type, SymbolTable.VAR)
                self.eatIdentifier()
                num_locals += 1
            self.eatSymbol(';')
        return num_locals

    def compileStatements(self):
        tok = self.tokenizer.current_token()
        while (tok.tokenType() == Token.KEYWORD):
            keywordType = tok.keyword()
            if keywordType == Token.LET:
                self.compileLet()
            elif keywordType == Token.IF:
                self.compileIf()
            elif keywordType == Token.WHILE:
                self.compileWhile()
            elif keywordType == Token.DO:
                self.compileDo()
            elif keywordType == Token.RETURN:
                self.compileReturn()
            tok = self.tokenizer.current_token()

        return

    def compileDo(self):
        self.eatKeyword(Token.DO)
        """Subroutine call Grammar
            subroutineName '(' expressionList ')' | (className | varName)'.'subroutineName'('expressionList')'
        """
        self.compileExpression()
        # class_name = self.class_name
        # name = self.eatIdentifier()
        # kind = self.symbol_table.kind_of(name) # TODO: check field segment
        # idx = self.symbol_table.index_of(name)
        # if(self.matchRawString('.')):
        #     self.eatSymbol('.')
        #     method_name = self.eatIdentifier()
        # else: #subroutine
        #     method_name = name

        # num_arg = 0
        # if kind is not None: # this is a varName
        #     num_arg += 1
        #     vartype = self.symbol_table.kind_of(name)
        #     class_name = vartype
        #     self.writer.write_push(kind, idx) # push object base addr
        # else: # className
        #     class_name = name

        # func_name = class_name + "." + method_name

        # self.eatSymbol('(')
        # num_arg += self.compileExpressionList()
        # self.eatSymbol(')')
        # self.writer.write_call(func_name, num_arg)

        self.eatSymbol(';')
        self.writer.write_pop("temp", 0)

        return

    def compileLet(self):
        self.eatKeyword(Token.LET)
        dest = self.eatIdentifier()
        kind = self.symbol_table.kind_of(dest)
        idx = self.symbol_table.index_of(dest)

        if(self.matchRawString('[')):  # array access
            self.writer.write_push(kind, idx)  # push arr
            self.eatSymbol('[')
            self.compileExpression()
            self.eatSymbol(']')
            self.writer.write_arithmetic("add")
            # top stack contains destination addr
            self.eatSymbol('=')
            self.compileExpression(optional=False)
            # save exp results into temp
            self.writer.write_pop("temp", 0)
            # pop dest addr into that
            self.writer.write_pop("pointer", 1)
            # retrieve results
            self.writer.write_push("temp", 0)
            # save into dest
            self.writer.write_pop("that", 0)
        else:  # normal variable assignment

            self.eatSymbol('=')
            self.compileExpression(optional=False)
            # top of stack contains results
            self.writer.write_pop(kind, idx)

        self.eatSymbol(';')

        return

    def compileWhile(self):
        while_count = self.while_count
        self.writer.write_label("WHILE_START." + str(while_count))
        self.while_count += 1
        self.eatKeyword(Token.WHILE)
        self.eatSymbol('(')
        self.compileExpression(optional=False)
        self.writer.write_arithmetic('not')
        self.writer.write_if("WHILE_END."+str(while_count))
        self.eatSymbol(')')
        self.eatSymbol('{')
        self.compileStatements()
        self.eatSymbol('}')
        self.writer.write_goto("WHILE_START."+str(while_count))
        self.writer.write_label("WHILE_END."+str(while_count))

        return

    def compileReturn(self):
        self.eatKeyword(Token.RETURN)
        if not self.compileExpression():
            self.writer.write_push("constant", 0)
        self.eatSymbol(';')
        self.writer.write_return()
        return

    def compileIf(self):
        if_count = self.if_count
        self.eatKeyword(Token.IF)
        self.eatSymbol('(')
        self.compileExpression(optional=False)
        self.writer.write_arithmetic('not')
        self.writer.write_if("IF_FALSE."+str(if_count))
        self.if_count += 1
        self.eatSymbol(')')
        self.eatSymbol('{')
        self.compileStatements()
        self.eatSymbol('}')
        if(self.matchRawString('else')):
            self.writer.write_goto("IF_END."+str(if_count))
            self.writer.write_label("IF_FALSE."+str(if_count))
            self.eatKeyword(Token.ELSE)
            self.eatSymbol('{')
            self.compileStatements()
            self.eatSymbol('}')
            self.writer.write_label("IF_END."+str(if_count))
        else:
            self.writer.write_label("IF_FALSE."+str(if_count))

        return

    def compileExpression(self, optional=True):

        if(self.matchTerm() or not optional):
            self.compileTerm()
            while(self.matchRawString(self.OPS_MAP)):
                sym = self.eatSymbol()
                self.compileTerm()
                if sym == '+':
                    self.writer.write_arithmetic("add")
                elif sym == '-':
                    self.writer.write_arithmetic("sub")
                elif sym == '*':
                    self.writer.write_call("Math.multiply", 2)
                elif sym == '/':
                    self.writer.write_call("Math.divide", 2)
                elif sym == '>':
                    self.writer.write_arithmetic("gt")
                elif sym == '<':
                    self.writer.write_arithmetic("lt")
                elif sym == '&':
                    self.writer.write_arithmetic("and")
                elif sym == '|':
                    self.writer.write_arithmetic("or")
                elif sym == '=':
                    self.writer.write_arithmetic("eq")

            return True
        return False

    def matchTerm(self):
        tok = self.tokenizer.current_token()
        tok_type = tok.tokenType()
        if tok_type == Token.KEYWORD:
            return tok.keyword() in self.KEYWORD_CONST
        if tok_type == Token.SYMBOL:
            return tok.symbol() in (['('] + self.UNARY_OP_LIST)
        return tok_type == Token.INT_CONST or tok_type == Token.STRING_CONST or tok_type == Token.IDENTIFIER

    def compileTerm(self):
        if(self.matchTerm()):

            tok = self.tokenizer.current_token()
            tok_type = tok.tokenType()

            if tok_type == Token.INT_CONST:
                self.writer.write_push("constant", tok.intVal())
                self.eat()
                return True
            elif tok_type == Token.STRING_CONST:
                # string.new
                string_val = tok.stringVal()
                self.writer.write_push("constant", len(string_val))
                self.writer.write_call("String.new", 1)
                for i in range(len(string_val)):
                    char_code = ord(string_val[i])
                    self.writer.write_push("constant", char_code)
                    self.writer.write_call("String.appendChar", 2)
                self.eat()
                return True
            elif tok_type == Token.KEYWORD:
                keyword = tok.keyword()
                if keyword == Token.NULL or keyword == Token.FALSE:
                    self.writer.write_push("constant", 0)
                elif keyword == Token.TRUE:
                    self.writer.write_push("constant", 0)
                    self.writer.write_arithmetic("not")
                elif keyword == Token.THIS:
                    self.writer.write_push("pointer", 0)

                self.eat()

            elif tok_type == Token.IDENTIFIER:
                obj = self.eatIdentifier()  # a String for var or class

                kind = self.symbol_table.kind_of(obj)
                idx = self.symbol_table.index_of(obj)
                if self.matchRawString('['):  # array type

                    self.writer.write_push(kind, idx)  # push arr

                    self.eatSymbol('[')
                    self.compileExpression()
                    self.eatSymbol(']')
                    self.writer.write_arithmetic("add")
                    self.writer.write_pop("pointer", 1)
                    self.writer.write_push("that", 0)

                elif self.matchRawString(['.', '(']):  # a method call()

                    method_name = obj
                    hasParentClass = False
                    if(self.matchRawString('.')):  # eg. Game.new()
                        self.eatSymbol('.')
                        method_name = self.eatIdentifier()
                        hasParentClass = True

                    num_arg = 0
                    if kind is None:  # either class or method
                        if hasParentClass:  # class
                            class_name = obj
                        else:  # method of current class
                            class_name = self.class_name
                            num_arg += 1
                            self.writer.write_push("pointer", 0)  # push this
                    else:  # must be an object
                        num_arg += 1
                        vartype = self.symbol_table.type_of(obj)
                        class_name = vartype
                        # push object base addr
                        self.writer.write_push(kind, idx)

                    func_name = class_name + "." + method_name

                    self.eatSymbol('(')
                    num_arg += self.compileExpressionList()
                    self.eatSymbol(')')
                    self.writer.write_call(func_name, num_arg)

                elif not self.symbol_table.isDeclaration():  # variable access
                    self.writer.write_push(kind, idx)

            elif tok_type == Token.SYMBOL:
                if(tok.symbol() == '('):
                    self.eatSymbol('(')
                    self.compileExpression()
                    self.eatSymbol(')')
                elif tok.symbol() in self.UNARY_OP_LIST:
                    sym = self.eatSymbol()
                    self.compileTerm()
                    if sym == '-':
                        self.writer.write_arithmetic("neg")
                    elif sym == '~':
                        self.writer.write_arithmetic("not")
                else:
                    self._handleError(
                        "Unexpected symbol when compiling term " + str(tok))
            else:
                self.eat()

            return True
        return False

    def compileExpressionList(self):
        num_arg = 0
        if(self.compileExpression()):
            num_arg = 1
            while(self.matchRawString(',')):
                self.eatSymbol(',')
                if(self.compileExpression()):
                    num_arg += 1
        return num_arg


class JackCompiler():

    def main(self):
        file_list = []

        if len(sys.argv) > 1:
            fname = os.path.normpath(sys.argv[1])  # use supplied file/dir
        else:
            fname = os.path.normpath(os.getcwd())   # use current dir

        if os.path.isdir(fname):  # add all .jack files
            for f in os.listdir(fname):
                if f.endswith(".jack"):
                    file_list.append(f)
            file_list = [os.path.join(fname, f) for f in file_list]
        else:
            file_list.append(fname)

        if len(file_list) == 0:
            print "No jack files to parse"
            return

        # process all jack files
        for file in file_list:
            p = CompilationEngine(file)

if __name__ == '__main__':
    analyzer = JackCompiler()
    analyzer.main()
