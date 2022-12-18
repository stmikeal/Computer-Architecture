from grammar import Token, token_func, macro_regex, pointer_regex
from enum import Enum
import re

class Label:
    name    : str = ""
    local   : bool = False

    def __str__(self) -> str:
        return "{\n\t\tname:%s,\n\t\tlocal:%s\n\t}" % (self.name, str(self.local))

class Macro:
    name    : str = ""
    value   : str = ""

    def __str__(self) -> str:
        return "{\n\t\tname:%s,\n\t\tvalue:%s\n\t}" % (self.name, self.value)

class Pointer:
    name    : str = ""
    size    : str = ""

    def __str__(self) -> str:
        return "{\n\t\tname:%s,\n\t\tsize:%s\n\t}" % (self.name, self.size)

class Argument:
    value   : str = ""
    reg     : bool = False
    mem     : bool = False

    def __str__(self) -> str:
        return "{\n\t\tvalue: %s,\n\t\treg: %s,\n\t\tmem: %s\n\t}" % (self.value, str(self.reg), str(self.mem))

class Operation:
    labels      : list[Label]   = []
    operation   : str           = ""
    args        : list[str]     = []
    def __init__(self) -> None:
        self.labels = []
        self.operation = ""
        self.args = []
    def __str__(self) -> str:
        return "{\n\tlabels: [%s],\n\toperation: %s,\n\targs: [%s]\n}" % \
            (", ".join(list(map(str, self.labels))), self.operation, ", ".join(list(map(str, self.args))))

class Parser:
    macros   : list[Macro]   = []
    pointers : list[Pointer] = []

    def token_to_enum(self, token : Token, match : re.Match) -> Enum:
        type : Enum[int] = token_func[token]
        for enum in type.__iter__():
            if enum.name.replace("_op", "") == match.group():
                return enum

    def parse_token(self, string : str) -> dict[str : [Token, str]]:
        for token in Token.__iter__():
            match = re.match(token.value.regex, string)
            if match:
                result = ""
                if token == Token.number:
                    result = str(int(match.group()))
                elif token == Token.string:
                    result = match.group()
                else:
                    result = self.token_to_enum(token, match).name.replace("_op", "")
                return {"type" : token, "value" : result}

    def make_macro(self, string : str) -> str:
        for macro in self.macros:
            string = string.replace(macro.name, macro.value)
        return string

    def parse_operation(self, string : str) -> Operation:
        string = re.sub(r"\s+", " ", string)
        if not string or len(string) < 2 or re.match(macro_regex, string) or re.match(pointer_regex, string):
            return None
        operation : Operation = Operation()
        string = self.make_macro(string)
        pieces = [sub for sub in re.split(r"\s+", string) if sub and len(sub)]
        idx = 0
        while idx < len(pieces) and pieces[idx][-1] == ":":
            pieces[idx] = pieces[idx][:-1]
            label : Label = Label() 
            if pieces[idx][0] == ".":
                label.local = True
                pieces[idx] = pieces[idx][1:]
            token = self.parse_token(pieces[idx])
            if Token.string == token['type']:
                label.name = token['value']
                operation.labels.append(label)
                idx += 1
            else:
                raise SyntaxError("Label naming error")
        if idx >= len(pieces):
            return operation
        command = self.parse_token(pieces[idx])
        operation.operation = command['value']
        idx += 1
        argument : Argument = Argument()

        if command['type'] == Token.op0:
            pass

        if command['type'] == Token.s_op1:
            if pieces[idx][0] == "[" and pieces[idx][-1] == "]":
                pieces[idx] = pieces[idx][1:-1]
                argument.mem = True
            arg = self.parse_token(pieces[idx])
            if arg['type'] == Token.reg:
                argument.reg = True
                argument.value = arg['value']
            if arg['type'] == Token.number:
                argument.value = arg['value']
            operation.args.append(argument)

        if command['type'] == Token.mem_op1:
            if pieces[idx][0] == "[" and pieces[idx][-1] == "]":
                pieces[idx] = pieces[idx][1:-1]
                argument.mem = True
            arg = self.parse_token(pieces[idx])
            if arg['type'] == Token.reg:
                argument.reg = True
                argument.value = arg['value']
            if arg['type'] == Token.number and argument.mem:
                argument.value = arg['value']
            operation.args.append(argument)

        if command['type'] == Token.op2:
            pieces[idx] = pieces[idx][:-1]
            if pieces[idx][0] == "[" and pieces[idx][-1] == "]":
                pieces[idx] = pieces[idx][1:-1]
                argument.mem = True
            arg = self.parse_token(pieces[idx])
            if arg['type'] == Token.reg:
                argument.reg = True
                argument.value = arg['value']
            if arg['type'] == Token.number and argument.mem:
                argument.value = arg['value']
            operation.args.append(argument)
            idx += 1
            argument : Argument = Argument()
            if pieces[idx][0] == "[" and pieces[idx][-1] == "]":
                pieces[idx] = pieces[idx][1:-1]
                argument.mem = True
            arg = self.parse_token(pieces[idx])
            if arg['type'] == Token.reg:
                argument.reg = True
                argument.value = arg['value']
            if arg['type'] == Token.number:
                argument.value = arg['value']
            operation.args.append(argument)
        
        if command['type'] == Token.jump_op:
            if pieces[idx][0] == ".":
                argument.mem = True
                pieces[idx] = pieces[idx][1:]
            arg = self.parse_token(pieces[idx])
            if arg['type'] == Token.string:
                argument.value = arg['value']
            operation.args.append(argument)
        return operation
            
    def parse_macro(self, string : str) -> None:
        if re.match(macro_regex, string):
            string = string.split()
            macro : Macro = Macro()
            macro.name = string[1]
            macro.value = string[2]
            self.macros.append(macro)

    def parse_pointer(self, string : str) -> None:
        if re.match(pointer_regex, string):
            string = string.split()
            pointer : Pointer = Pointer
            pointer.name = string[0]
            pointer.size = string[2]
            self.pointers.append(pointer)
