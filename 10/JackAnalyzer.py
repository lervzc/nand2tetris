import os.path
import sys
import re


class Token(object):

    """Token types"""
    KEYWORD, SYMBOL, IDENTIFIER, INT_CONST, STRING_CONST = [
        "keyword", "symbol", "identifier", "integerConstant", "stringConstant"]
    CLASS, METHOD, FUNCTION, CONSTRUCTOR, INT, BOOLEAN, CHAR, VOID, VAR, STATIC, FIELD, LET, DO, IF, ELSE, WHILE, RETURN, TRUE, FALSE, NULL, THIS = range(
        21)

    KEYWORDS_MAP = {
        'class': CLASS,
        'constructor': CONSTRUCTOR,
        'function': FUNCTION,
        'method': METHOD,
        'field': FIELD,
        'static': STATIC,
        'var': VAR,
        'int': INT,
        'char': CHAR,
        'boolean': BOOLEAN,
        'void': VOID,
        'true': TRUE,
        'false': FALSE,
        'null': NULL,
        'this': THIS,
        'let': LET,
        'do': DO,
        'if': IF,
        'else': ELSE,
        'while': WHILE,
        'return': RETURN,
    }

    SYM_SET = set(['{', '}', '(', ')', '[', ']', '.', ',',
                   ';', '+', '-', '*', '/', '&', '|', '<', '>', '=', '~'])
    SYM_MAP = {
        '<': '&lt;',
        '>': '&gt;',
        '&': '&amp;',
    }

    def __init__(self, string_token):
        self.str_tok = string_token
        self.type = self.manage_type(string_token)

    def manage_type(self, string_token):
        if self.KEYWORDS_MAP in string_token:
            self._keyword = self.KEYWORDS_MAP[string_token]
            return self.KEYWORD
        if string_token in self.SYM_SET:
            return self.SYMBOL
        if string_token.isdigit():
            self.int_val = int(string_token)
            return self.INT_CONST
        if string_token.find('\"') != -1:
            self.string_val = string_token.replace("\"", "")
            return self.STRING_CONST

        return self.IDENTIFIER

    def keyword(self):
        return self._keyword

    def symbol(self):
        return self.str_tok

    def identifier(self):
        return self.str_tok

    def intVal(self):
        return self.int_val

    def stringVal(self):
        return self.string_val

    def tokenType(self):
        return self.type

    def stringToken(self):
        return self.str_tok

    def xmlString(self):
        if self.SYM_MAP in self.str_tok:
            str_repr = self.SYM_MAP[self.str_tok]
        else:
            str_repr = self.str_tok.replace("\"", "")
        return '<{type}> {value} </{type}>'.format(
            type=self.type,
            value=str_repr)

    def __str__(self):
        """String representation of the class instance.
        Examples:
            <symbol> ( </symbol>
            Token(STRING_CONST, '"HEELLO"')
        """
        return self.xmlString()

    def __repr__(self):
        return self.__str__()


class JackTokenizer(object):
    NOT_SKIP, SKIP_NOW, SKIP_NEXT = range(3)

    def __init__(self, jackfile):
        self.jackfile = jackfile
        file = open(jackfile, 'r')
        self.skip_from = self.NOT_SKIP
        self.tokens = self._tokenize_file(file)
        self.token_num = 0
        self.token_max_num = len(self.tokens)
        file.close()

    def _tokenize_file(self, file):
        token_regex = '(class|constructor|function|method|field|static|var|int|char|boolean|void|true|false|null|this|let|do|if|else|while|return)|({|}|\(|\)|\[|\]|\.|,|\||;|\+|-|\*|\/|&|\||<|>|=|~)|(\d+)|(\".*\")|(\w+)'
        matcher = re.compile(token_regex)
        tokens = []
        for line in file:
            line = self._remove_comments(line)
            line = self._process_block_comments(line)

            if(line is None or len(line) == 0 or self.skip_from == self.SKIP_NOW):
                continue
            for t in matcher.finditer(line):
                if t:
                    text_tok = t.group(0)
                    tokens.append(Token(text_tok))

            if(self.skip_from == self.SKIP_NEXT):
                self.skip_from = self.SKIP_NOW
        return tokens

    def _remove_comments(self, line):
        line = line.strip()
        comment_idx = line.find("//")
        if comment_idx != -1:
            line = line[:comment_idx]
        return line.strip().replace("\t", "")

    def _process_block_comments(self, line):
        line = line.strip()
        block_comment_start_idx = line.find("/*")
        block_comment_end_idx = line.find("*/")
        if block_comment_start_idx != -1 and block_comment_end_idx != -1:
            """/* a single line block comment*/"""
            front_part = line[:block_comment_start_idx]
            end_part = line[block_comment_end_idx+2:]
            line = front_part + end_part
        elif block_comment_start_idx != -1:
            if block_comment_start_idx == 0:
                self.skip_from = self.SKIP_NOW
            else:
                line = line[:block_comment_start_idx]
                self.skip_from = self.SKIP_NEXT
        elif block_comment_end_idx != -1:
            line = line[block_comment_end_idx+2:]
            self.skip_from = self.NOT_SKIP
        return line.strip().replace("\t", "")

    def has_next_token(self):
        return self.token_num < self.token_max_num

    def next_token(self):
        self.token_num += 1
        # return self.tokens[self.token_num]

    def current_token(self):
        return self.tokens[self.token_num]

    def saveToFile(self):
        dirname = os.path.dirname(self.jackfile)
        basename = os.path.basename(self.jackfile)
        outname = os.path.join(dirname, basename[:-5]+"T.xml")
        outfile = open(outname, 'w')
        print "Writing tokens to " + outfile.name
        outfile.write("<tokens>\n")
        for tok in self.tokens:
            outfile.write(tok.xmlString()+"\n")
        outfile.write("</tokens>")
        outfile.close()


class JackParser(object):
    KEYWORD_CONST = [Token.TRUE, Token.FALSE, Token.NULL, Token.THIS]
    OPS_LIST = ['+', '-', '*', '/', '&', '|', '<', '>', '=']
    UNARY_OP_LIST = ['-', '~']

    def __init__(self, jackfile):
        self.tokenizer = JackTokenizer(jackfile)
        # self.tokenizer.saveToFile()

        dirname = os.path.dirname(jackfile)
        basename = os.path.basename(jackfile)
        outname = os.path.join(dirname, basename[:-5]+".xml")
        self.outfile = open(outname, 'w')
        self.compileClass()
        self.outfile.close()

    def eatRawString(self, string_token):
        tok = self.tokenizer.current_token()
        string_name = tok.stringToken()
        if(not self.matchRawString(string_token)):
            self._handleError(
                "Expected: " + str(string_token) + ", but gotten :" + string_name)
        elif self.tokenizer.has_next_token():
            self.outfile.write(tok.xmlString()+"\n")
            self.tokenizer.next_token()
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
            self.outfile.write(tok.xmlString()+"\n")
            self.tokenizer.next_token()
        else:
            self._handleError("Unexpected end of line")

    def eatIdentifier(self):
        tok = self.tokenizer.current_token()
        if(tok.tokenType() != Token.IDENTIFIER):
            self._handleError(
                "Expected identifier but gotten " + tok.tokenType())
        elif self.tokenizer.has_next_token():
            self.outfile.write(tok.xmlString()+"\n")
            self.tokenizer.next_token()
        else:
            self._handleError("Unexpected end of line")

    def eatKeyword(self, keyword_type=None):
        tok = self.tokenizer.current_token()
        if(tok.tokenType() != Token.KEYWORD):
            self._handleError("Expected keyword but gotten " + tok.tokenType())
        elif(keyword_type is not None and tok.keyword() != keyword_type):
            self._handleError("Expected keyword but gotten " + tok.tokenType())
        elif self.tokenizer.has_next_token():
            self.outfile.write(tok.xmlString()+"\n")
            self.tokenizer.next_token()
        else:
            self._handleError("Unexpected end of line")

    def eatType(self):
        tok = self.tokenizer.current_token()
        if(self.matchType()):
            self.outfile.write(tok.xmlString()+"\n")
            self.tokenizer.next_token()
        else:
            self._handleError("Expected type but gotten " + tok.stringToken())

    def eat(self):
        tok = self.tokenizer.current_token()
        if self.tokenizer.has_next_token():
            self.outfile.write(tok.xmlString()+"\n")
            self.tokenizer.next_token()
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
        if type(string_to_match) is list:
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
        self.outfile.write("<class>\n")
        self.eatRawString("class")
        self.eatIdentifier()
        self.eatSymbol("{")

        while (self.matchRawString(['static', 'field'])):
            self.compileClassVarDec()

        while (self.matchRawString(['constructor', 'function', 'method'])):
            self.compileSubroutine()

        self.eatSymbol("}")
        self.outfile.write("</class>\n")

    def compileClassVarDec(self):
        self.outfile.write("<classVarDec>\n")
        self.eatKeyword()  # field or static
        self.eatType()  # return type
        self.eatIdentifier()  # var name

        while (self.matchRawString(",")):
            self.eatSymbol(',')
            self.eatIdentifier()  # var name

        self.eatSymbol(';')
        self.outfile.write("</classVarDec>\n")
        return

    def compileSubroutine(self):

        self.outfile.write("<subroutineDec>\n")
        self.eatRawString(['constructor', 'function', 'method'])
        if(self.matchType() or self.matchRawString('void')):
            self.eat()
        else:
            self._handleError("subroutine return type expected")

        self.eatIdentifier()
        self.eatSymbol("(")
        self.compileParemeterList()
        self.eatSymbol(")")
        self.outfile.write("<subroutineBody>\n")
        self.eatSymbol("{")
        while(self.matchRawString('var')):
            self.compileVarDec()

        self.compileStatements()

        self.eatSymbol("}")
        self.outfile.write("</subroutineBody>\n")
        self.outfile.write("</subroutineDec>\n")

        return

    def compileParemeterList(self):
        """((type varNmae) (',' type varName)*)?"""
        self.outfile.write("<parameterList>\n")
        if(self.matchType()):
            self.eatType()
            self.eatIdentifier()

            while(self.matchRawString(",")):
                self.eatSymbol(',')
                self.eatType()
                self.eatIdentifier()

        self.outfile.write("</parameterList>\n")
        return

    def compileVarDec(self):
        """'var' type varName (',' varName)*"""
        if self.matchRawString('var'):
            self.outfile.write("<varDec>\n")
            self.eatKeyword()
            self.eatType()
            self.eatIdentifier()
            while(self.matchRawString(",")):
                self.eatSymbol(',')
                self.eatIdentifier()
            self.eatSymbol(';')
            self.outfile.write("</varDec>\n")
        return

    def compileStatements(self):
        self.outfile.write("<statements>\n")
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

        self.outfile.write("</statements>\n")
        return

    def compileDo(self):
        self.outfile.write("<doStatement>\n")
        self.eatKeyword(Token.DO)
        """Subroutine call Grammar
            subroutineName '(' expressionList ')' | (className | varName)'.'subroutineName'('expressionList')'
        """
        self.eatIdentifier()
        if(self.matchRawString('.')):
            self.eatSymbol('.')
            self.eatIdentifier()

        self.eatSymbol('(')
        self.compileExpressionList()
        self.eatSymbol(')')
        self.eatSymbol(';')
        self.outfile.write("</doStatement>\n")
        return

    def compileLet(self):
        self.outfile.write("<letStatement>\n")
        self.eatKeyword(Token.LET)
        self.eatIdentifier()
        if(self.matchRawString('[')):
            self.eatSymbol('[')
            self.compileExpression()
            self.eatSymbol(']')
        self.eatSymbol('=')
        self.compileExpression(optional=False)
        self.eatSymbol(';')
        self.outfile.write("</letStatement>\n")
        return

    def compileWhile(self):
        self.outfile.write("<whileStatement>\n")
        self.eatKeyword(Token.WHILE)
        self.eatSymbol('(')
        self.compileExpression(optional=False)
        self.eatSymbol(')')
        self.eatSymbol('{')
        self.compileStatements()
        self.eatSymbol('}')
        self.outfile.write("</whileStatement>\n")
        return

    def compileReturn(self):
        self.outfile.write("<returnStatement>\n")
        self.eatKeyword(Token.RETURN)
        self.compileExpression()
        self.eatSymbol(';')
        self.outfile.write("</returnStatement>\n")
        return

    def compileIf(self):
        self.outfile.write("<ifStatement>\n")
        self.eatKeyword(Token.IF)
        self.eatSymbol('(')
        self.compileExpression(optional=False)
        self.eatSymbol(')')
        self.eatSymbol('{')
        self.compileStatements()
        self.eatSymbol('}')
        if(self.matchRawString('else')):
            self.eatKeyword(Token.ELSE)
            self.eatSymbol('{')
            self.compileStatements()
            self.eatSymbol('}')
        self.outfile.write("</ifStatement>\n")
        return

    def compileExpression(self, optional=True):
        if(self.matchTerm() or not optional):
            self.outfile.write("<expression>\n")
            self.compileTerm()
            while(self.matchRawString(self.OPS_LIST)):
                self.eatSymbol()
                self.compileTerm()
            self.outfile.write("</expression>\n")
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
            self.outfile.write("<term>\n")

            tok = self.tokenizer.current_token()
            tok_type = tok.tokenType()
            if tok_type == Token.IDENTIFIER:
                self.eatIdentifier()
                if self.matchRawString('['):  # array type
                    self.eatSymbol('[')
                    self.compileExpression()
                    self.eatSymbol(']')
                elif self.matchRawString(['.', '(']):  # routineName()
                    if self.matchRawString('.'):  # className.routineName()
                        self.eatSymbol('.')
                        self.eatIdentifier()

                    self.eatSymbol('(')
                    self.compileExpressionList()
                    self.eatSymbol(')')

            elif tok_type == Token.SYMBOL:
                if(tok.symbol() == '('):
                    self.eatSymbol('(')
                    self.compileExpression()
                    self.eatSymbol(')')
                elif tok.symbol() in self.UNARY_OP_LIST:
                    self.eatSymbol()
                    self.compileTerm()
                else:
                    self._handleError(
                        "Unexpected symbol when compiling term " + str(tok))
            else:
                self.eat()

            self.outfile.write("</term>\n")
            return True
        return False

    def compileExpressionList(self):
        self.outfile.write('<expressionList>\n')
        if(self.compileExpression()):
            while(self.matchRawString(',')):
                self.eatSymbol(',')
                self.compileExpression()
        self.outfile.write('</expressionList>\n')
        return


class JackAnalyzer():

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
            p = JackParser(file)

if __name__ == '__main__':
    analyzer = JackAnalyzer()
    analyzer.main()
