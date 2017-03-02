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
        if string_token in self.KEYWORDS_MAP:
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
        if self.str_tok in self.SYM_MAP:
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
        """
        return self.xmlString()

    def __repr__(self):
        return self.__str__()