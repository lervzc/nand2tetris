import os.path
import sys


class Parser(object):

    def __init__(self, fname):
        super(Parser, self).__init__()
        self.fname = fname
        self.file = open(self.fname, 'r')

    def clean(self, line):
        line = line.strip()
        comment_idx = line.find("//")
        if comment_idx != -1:
            line = line[:comment_idx]
        return line.strip().replace("\t", "")

    def parse(self):
        for line in self.file:
            line = self.clean(line)
            if len(line) > 0:
                yield Command(line)


class Command(object):
    C_ARITHMETIC, C_PUSH, C_POP, C_LABEL, C_GOTO, C_IF, C_FUNCTION, C_RETURN, C_CALL = range(
        9)
    ARITHMETICS = ['add', 'sub', 'neg', 'lt', 'gt', 'eq', 'and', 'or', 'not']

    def __init__(self, line):
        super(Command, self).__init__()
        self.line = line
        self._tokenise()

    def _tokenise(self):
        tokens = self.line.split(' ')
        self.command = tokens[0]
        if len(tokens) > 1:
            self.segment = tokens[1]

        if len(tokens) > 2 and tokens[2].isdigit():
            self.idx = int(tokens[2])

    def commandType(self):
        if self.command == 'push':
            return Command.C_PUSH
        elif self.command == 'pop':
            return Command.C_POP
        elif self.command in Command.ARITHMETICS:
            return Command.C_ARITHMETIC
        elif self.command == 'label':
            return Command.C_LABEL
        elif self.command == 'goto':
            return Command.C_GOTO
        elif self.command == 'if-goto':
            return Command.C_IF
        elif self.command == 'function':
            return Command.C_FUNCTION
        elif self.command == 'return':
            return Command.C_RETURN
        elif self.command == 'call':
            return Command.C_CALL

    def arg1(self):  # command eg. push pop call return
        if self.commandType() != Command.C_RETURN:
            return self.command

    def arg2(self):  # label, segment
        if self.commandType() != Command.C_ARITHMETIC:
            return self.segment

    def arg3(self):  # index number
        return self.idx

    def to_string(self):
        return self.line

    def display(self):
        print self.line


class CodeWriter(object):
    LOGICAL_SKIPPERS = ["eq", "gt", "lt"]
    INF_LOOP = """
    (INFINITE_LOOP)
        @INFINITE_LOOP
        0;JMP
    """
    ARITHMETICS_LOOKUP = {
        "add": """
                    @SP
                    AM=M-1
                    D=M
                    @SP
                    A=M-1
                    M=D+M
                """,
        "sub": """
                    @SP
                    AM=M-1
                    D=M
                    @SP
                    A=M-1
                    M=M-D
                    """,
        "neg": """
                    @SP
                    A=M-1
                    M=-M
                """,
        "eq": """
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
        "gt": """
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
        "lt": """
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
        "and": """
                    @SP
                    AM=M-1
                    D=M
                    A=A-1
                    M=D&M
                """,
        "or": """
                    @SP
                    AM=M-1
                    D=M
                    A=A-1
                    M=D|M
                """,
        "not": """
                @SP
                A=M-1
                M=!M
                """
    }
    SEGMENT_MAP = {
        "local": "LCL",
        "argument": "ARG",
        "this": "THIS",
        "that": "THAT"
    }

    def __init__(self, outname, init=False):
        self.outfile = open(outname, 'w')
        filename = os.path.basename(self.outfile.name)
        self.set_file_name(filename)
        print "Writing to " + outname
        self.code_count = 0
        self.within_function = False
        self.func_name = "main"
        self.func_call_count = 0
        if init:
            self.writeInit()

    def set_file_name(self, fname):
        filename = os.path.basename(fname)
        self.filename = filename.replace(".vm", "")
        self.filename = filename.replace(".asm", "")

    def vm_push(self, segment, idx):
        if segment == 'temp':
            idx = idx + 5  # temp segment 5-12
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

        if CodeWriter.SEGMENT_MAP in segment:
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
        if CodeWriter.SEGMENT_MAP in segment:
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
            idx = idx + 5  # temp segment 5-12
            return """
                @SP
                A=M-1
                D=M
                @{:d}
                M=D
                @SP
                M=M-1
            """.format(idx)

        # D = stack.pop
        # @var
        # M=D
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
        self.write("// "+code.to_string())
        c_type = code.commandType()
        if c_type == Command.C_ARITHMETIC:
            self.writeArithmetic(code.arg1())
        elif c_type == Command.C_POP or c_type == Command.C_PUSH:
            self.writePushPop(code.arg1(), code.arg2(), code.arg3())
        elif c_type == Command.C_LABEL:
            self.writeLabel(code.arg2())
        elif c_type == Command.C_IF:
            self.writeIf(code.arg2())
        elif c_type == Command.C_GOTO:
            self.writeGoto(code.arg2())
        elif c_type == Command.C_CALL:
            self.writeCall(code.arg2(), code.arg3())
        elif c_type == Command.C_FUNCTION:
            self.writeFunction(code.arg2(), code.arg3())
        elif c_type == Command.C_RETURN:
            self.writeReturn()

    def writeInit(self):
        self.write("// -- bootstrap starts --")
        self.write("""
                @256
                D=A
                @SP
                M=D
            """)
        self.writeCall("Sys.init", 0)
        self.write("// -- bootstrap ends -- ")
        return ""

    def writeLabel(self, label):
        if self.within_function:
            label = self.func_name + "$" + label

        self.write("("+label+")")

    def writeGoto(self, label):
        if self.within_function:
            label = self.func_name + "$" + label

        goto = """
            @{:s}
            0;JMP
        """.format(label)
        self.write(goto)

    def writeIf(self, label):
        if self.within_function:
            label = self.func_name + "$" + label

        if_goto = """
            @SP
            AM=M-1
            D=M
            @{:s}
            D;JNE
        """.format(label)
        self.write(if_goto)

    def writeCall(self, func_name, num_args):
        # assuming caller pushed num_args on stack
        ret_label = self.func_name + "$ret." + str(self.func_call_count)
        self.func_call_count += 1
        call = """
            @{:s}
            D=A
            @SP // push retAddr
            A=M
            M=D
            @SP
            M=M+1
            @LCL
            D=M
            @SP // push LCL
            A=M
            M=D
            @SP
            M=M+1
            @ARG
            D=M
            @SP // push ARG
            A=M
            M=D
            @SP
            M=M+1
            @THIS
            D=M
            @SP // push THIS
            A=M
            M=D
            @SP
            M=M+1
            @THAT
            D=M
            @SP // push THAT
            A=M
            M=D
            @SP
            MD=M+1
            @{:d}
            D=D-A
            @5
            D=D-A
            @ARG // ARG=SP-nArgs-5
            M=D
            @SP
            D=M
            @LCL
            M=D
            @{:s}
            0;JMP
            ({:s})
        """.format(ret_label, num_args, func_name, ret_label)
        self.write(call)

    def writeFunction(self, func_name, num_locals):
        self.within_function = True
        self.func_name = func_name
        self.func_call_count = 0
        self.write("("+func_name+")")
        for _ in range(num_locals):
            self.writePushPop("push", "constant", 0)

    def writeReturn(self):
        ret = """
            @LCL
            D=M
            @R15 // frame
            M=D
            @5 // *(frame-5)
            A=D-A
            D=M
            @R14 // retaddr
            M=D
            @SP // pop
            AM=M-1
            D=M
            @ARG // replace arg 1
            A=M
            M=D
            D=A
            @SP // SP=ARG+1
            M=D+1
            @R15
            D=M
            @1 // *(frame-1)
            A=D-A
            D=M
            @THAT
            M=D
            @R15
            D=M
            @2 // *(frame-2)
            A=D-A
            D=M
            @THIS
            M=D
            @R15
            D=M
            @3 // *(frame-3)
            A=D-A
            D=M
            @ARG
            M=D
            @R15
            D=M
            @4 // *(frame-4)
            A=D-A
            D=M
            @LCL
            M=D
            @R14
            A=M
            0;JMP
        """
        self.write(ret)

    def writeArithmetic(self, command):
        if self.ARITHMETICS_LOOKUP in command:
            asm = self.ARITHMETICS_LOOKUP[command]
            if command in self.LOGICAL_SKIPPERS:
                ret_asm = """
                            @{:d}
                            D=A
                            @R14
                            M=D
                        """.format(self.code_count+self.countCommand(asm)+4)  # count target skip lines
                self.write(ret_asm)
            self.write(asm)

    def writePushPop(self, command, segment, idx):
        if command == 'push':
            asm = self.vm_push(segment, idx)
        elif command == 'pop':
            asm = self.vm_pop(segment, idx)
        self.write(asm)

    def countCommand(self, asm):
        asm = self.strip_tabs(asm)
        lines = asm.split('\n')
        count = sum(
            len(l) > 0 and l[:2] != '//' and l.find("(") == -1 for l in lines)
        return count

    def write(self, asm):
        asm = self.strip_tabs(asm)
        self.code_count += self.countCommand(asm)
        self.outfile.write(asm + "\n")

    def strip_tabs(self, asm):
        return asm.replace("\t", "").strip()

    def close(self):
        # self.write(self.INF_LOOP)
        self.outfile.close()
        print "file closed."


class VMTranslator():

    def main(self):
        file_list = []

        if len(sys.argv) > 1:
            fname = os.path.normpath(sys.argv[1])  # use supplied file/dir
        else:
            fname = os.path.normpath(os.getcwd())  # use current dir

        oname = ""
        toInit = False
        if os.path.isdir(fname):  # add all .vm files
            toInit = True
            dirname = os.path.split(fname)
            oname = os.path.join(fname, dirname[1] + ".asm")
            for f in os.listdir(fname):
                if f.endswith(".vm"):
                    file_list.append(f)
            file_list = [os.path.join(fname, f) for f in file_list]
        else:
            oname = fname[:-3]+".asm"
            file_list.append(fname)

        # print oname
        # print file_list
        if len(file_list) == 0:
            print "No vm files to translate"
            return

        # create a single CodeWriter
        writer = CodeWriter(oname, init=toInit)

        # process all vm files
        for file in file_list:
            writer.set_file_name(file)
            a = Parser(file)  # parse each file
            for code in a.parse():
                # code.display()
                writer.translate(code)
        writer.close()

if __name__ == '__main__':
    vm_translator = VMTranslator()
    vm_translator.main()
