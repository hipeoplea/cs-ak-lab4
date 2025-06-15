import re

def tokenize(code):
    lines = code.splitlines()
    no_comments = [re.sub(r';.*$', '', line) for line in lines]
    code_nc = '\n'.join(no_comments)

    token_pattern = r'''"([^"\\]*(\\.[^"\\]*)*)"|[\(\)]|[^\s\(\)]+'''
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
        if self.tokens[self.pos] == '(':
            self.pos += 1
            lst = []
            while self.tokens[self.pos] != ')':
                lst.append(self.parse())
            self.pos += 1
            return lst
        else:
            return self.atom(self.tokens[self.pos])

    def atom(self, token):
        self.pos += 1
        if token.startswith('"') and token.endswith('"'):
            return {'type': 'string', 'value': token[1:-1].replace('\\n', '\n').replace('\\t', '\t')}
        if token.startswith('[') and token.endswith(']'):
            try:
                size = int(token[1:-1])
                return {'string_size': size}
            except ValueError:
                return token
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
        return {'type': 'number', 'value': ast}
    if isinstance(ast, dict) and ast.get('type') == 'string':
        return ast
    if isinstance(ast, str):
        return {'type': 'var', 'name': ast}

    head, *args = ast

    if head == 'var':
        value = ast_to_expr(args[1])
        if isinstance(args[1], dict) and 'string_size' in args[1]:
            return {'type': 'var', 'name': args[0], 'size': args[1]['string_size']}
        return {'type': 'var', 'name': args[0], 'expr': value}

    if head == 'set':
        return {'type': 'set', 'name': args[0], 'expr': ast_to_expr(args[1])}

    if head == 'defunc':
        return {
            'type': 'defunc',
            'name': args[0],
            'params': args[1][0],
            'body': [ast_to_expr(b) for b in args[2:][0]]
        }

    if head in ('+', '-', '*', '/', '=', '<', '>'):
        left, right = args
        return {
            'type': 'binop',
            'op': head,
            'left': ast_to_expr(left),
            'right': ast_to_expr(right)
        }

    if head == 'if':
        return {
            'type': 'if',
            'cond': ast_to_expr(args[0]),
            'then': ast_to_expr(args[1]),
            'else': ast_to_expr(args[2]) if len(args) > 2 else None
        }

    if head == 'while':
        return {
            'type': 'while',
            'cond': ast_to_expr(args[0]),
            'body': [ast_to_expr(b) for b in args[1:]]
        }

    if head == 'print_string':
        return {
            'type': 'print_string',
            'value': ast_to_expr(args[0])
        }

    if head == 'read_line':
        return {
            'type': 'read_line',
            'value': ast_to_expr(args[0])
        }

    if head == 'funcall':
        return {
        'type': 'funcall',
        'name': args[0],
        'args': [ast_to_expr(a[0]) for a in args[1:]]
        }



