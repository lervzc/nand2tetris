import re, os
from Token import Token
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
        token_regex = '(class|constructor|function|method|field|static|var(?=\s)|int(?=\s)|char(?=\s)|boolean|void|true|false|null|this|let(?=\s)|do(?=\s)|if|else|while|return)|({|}|\(|\)|\[|\]|\.|,|\||;|\+|-|\*|\/|&|\||<|>|=|~)|(\d+)|(\".*\")|(\w+)'
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
