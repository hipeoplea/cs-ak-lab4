import re


class InvalidWhileBodyError(TypeError):
    """Body of a 'while' expression must be a list."""

def tokenize(code):
    lines = code.splitlines()
    no_comments = [re.sub(r";.*$", "", line) for line in lines]
    code_nc = "\n".join(no_comments)

    token_pattern = r""""([^"\\]*(\\.[^"\\]*)*)"|[\(\)]|[^\s\(\)]+"""
    tokens = []
    for match in re.finditer(token_pattern, code_nc):
        if match.group(1) is not None:
            tokens.append('"' + match.group(1) + '"')
        else:
            tokens.append(match.group(0))
    return tokens


class LispParser:
    def __init__(self, source_code):
        self.tokens = tokenize(source_code)
        self.pos = 0

    def parse(self):
        if self.tokens[self.pos] == "(":
            self.pos += 1
            lst = []
            while self.tokens[self.pos] != ")":
                lst.append(self.parse())
            self.pos += 1
            return lst
        return self.atom(self.tokens[self.pos])

    def atom(self, token):
        self.pos += 1
        if token.startswith('"') and token.endswith('"'):
            return {"type": "string", "value": token[1:-1].replace("\\n", "\n").replace("\\t", "\t")}
        if token.startswith("[") and token.endswith("]"):
            try:
                size = int(token[1:-1])
            except ValueError:
                return token
            else:
                return {"string_size": size}
        try:
            return int(token)
        except ValueError:
            return token

    def parse_program(self):
        program = []
        while self.pos < len(self.tokens):
            program.append(self.parse())
        return program


def ast_to_expr(ast):
    if isinstance(ast, int):
        return {"type": "number", "value": ast}
    if isinstance(ast, dict) and ast.get("type") == "string":
        return ast
    if isinstance(ast, str):
        return {"type": "var", "name": ast}

    head, *args = ast

    dispatch = {
        "var": _parse_var,
        "set": _parse_set,
        "defunc": _parse_defunc,
        "if": _parse_if,
        "while": _parse_while,
        "print_string": _parse_print_string,
        "read_line": _parse_read_line,
        "funcall": _parse_funcall,
        "get": _parse_get
    }

    if head in ("+", "-", "*", "/", "=", "<", ">"):
        return _parse_binop(head, args)

    handler = dispatch.get(head)
    if handler:
        return handler(args)

    return None

def _parse_get(args):
    return {
        "type": "get",
        "array": ast_to_expr(args[0]),
        "index": ast_to_expr(args[1])
    }


def _parse_var(args):
    value = ast_to_expr(args[1])
    if isinstance(args[1], dict) and "string_size" in args[1]:
        return {"type": "var", "name": args[0], "size": args[1]["string_size"]}
    return {"type": "var", "name": args[0], "expr": value}

def _parse_set(args):
    target = args[0]
    expr = ast_to_expr(args[1])
    if isinstance(target, list) and target[0] == "get":
        return {
            "type": "set_get",
            "array": ast_to_expr(target[1]),
            "index": ast_to_expr(target[2]),
            "expr": expr
        }
    return {
        "type": "set",
        "name": target,
        "expr": expr
    }

def _parse_defunc(args):
    return {
        "type": "defunc",
        "name": args[0],
        "params": [ast_to_expr(a[0]) for a in args[1]],
        "body": [ast_to_expr(b) for b in args[2]]
    }


def _parse_binop(op, args):
    left, right = args
    return {
        "type": "binop",
        "op": op,
        "left": ast_to_expr(left),
        "right": ast_to_expr(right),
    }

def _parse_if(args):
    return {
        "type": "if",
        "cond": ast_to_expr(args[0]),
        "then": ast_to_expr(args[1]),
        "else": ast_to_expr(args[2]) if len(args) > 2 else None,
    }

def _parse_while(args):
    body = args[1]
    if not isinstance(body, list):
        raise InvalidWhileBodyError()
    return {
        "type": "while",
        "cond": ast_to_expr(args[0]),
        "body": [ast_to_expr(stmt) for stmt in body]
    }


def _parse_print_string(args):
    return {"type": "print_string", "value": ast_to_expr(args[0])}

def _parse_read_line(args):
    return {"type": "read_line", "value": ast_to_expr(args[0])}

def _parse_funcall(args):
    return {
        "type": "funcall",
        "name": args[0],
        "args": [ast_to_expr(a[0]) for a in args[1:]],
    }


