import sys

from tokenizer import *
from instrucrions import *


class CodeGenerator:
    def __init__(self):
        self.lab_cnt = 0
        self.data_lines = []
        self.code_lines = []
        self.data_addr = {}
        self.const_map = {}
        self.funcs = {}
        self.scopes = [{}]

    def _lab(self, p='L'):
        self.lab_cnt += 1
        return f'{p}{self.lab_cnt}'

    def _const(self, v):
        if v not in self.const_map:
            label = f'c_{v}'
            self.const_map[v] = label
            self.data_lines.append(f'{label} .word {v}')
        return self.const_map[v]

    def _emit(self, op, arg=None):
        self.code_lines.append(op if arg is None else f"{op} {arg}")

    def _label(self, name):
        self.code_lines.append(f"{name}:")

    def _decl(self, name):
        scope = self.scopes[-1]
        if name not in scope:
            addr = f'{name}_{len(self.scopes) - 1}'
            scope[name] = addr
            self.data_lines.append(f'{addr} .word 0')
        return scope[name]

    def _addr(self, name):
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        raise NameError(name)

    def expr(self, e):
        t = e['type']
        if t == 'number':
            self._emit(Opcode.LOAD.value, self._const(e['value']))
            return
        if t in ('var', 'var_ref'):
            self._emit(Opcode.LOAD.value, self._addr(e['name']))
            return
        if t == 'binop':
            self.expr(e['left'])
            tmp = self._decl('_tmp')
            self._emit(Opcode.STORE.value, tmp)
            self.expr(e['right'])
            arith = {'+': Opcode.ADD, '-': Opcode.SUB, '*': Opcode.MUL, '/': Opcode.DIV}
            if e['op'] in arith:
                self._emit(arith[e['op']].value, tmp)
                return
            l_true, l_end = self._lab('T'), self._lab('E')
            self._emit(Opcode.SUB.value, tmp)
            cmp_j = {'=': Opcode.JZ, '!=': Opcode.JNZ, '<': Opcode.JLT, '>': Opcode.JGT}[e['op']]
            self._emit(cmp_j.value, l_true)
            self.expr({'type': 'number', 'value': 0})
            self._emit(Opcode.JMP.value, l_end)
            self._label(l_true)
            self.expr({'type': 'number', 'value': 1})
            self._label(l_end)
            return
        if t == 'funcall':
            if e['name'] == 'print_string':
                val = e['args'][0]
                if val['type'] == 'string':
                    for ch in val['value']:
                        self._emit(Opcode.LOAD.value, self._const(ord(ch)))
                        self._emit(Opcode.OUT.value, 0)
                else:
                    self.expr(val)
                    self._emit(Opcode.OUT.value, 0)
                return
            for arg in e['args']:
                self.expr(arg)
                self._emit(Opcode.PUSH.value)
            self._emit(Opcode.CALL.value, e['name'])
            return
        if t == 'read_line':
            addr = self._addr(e['value']['name'])
            self._emit(Opcode.IN_.value, 0)
            self._emit(Opcode.STORE.value, addr)
            self._emit(Opcode.LOAD.value, addr)
            return
        raise NotImplementedError(t)

    def node(self, n):
        if n is None:
            return
        t = n['type']
        if t in ('var_decl', 'var'):
            addr = self._decl(n['name'])
            if 'expr' in n and not (n['expr']['type'] == 'number' and n['expr']['value'] == 0):
                self.expr(n['expr'])
                self._emit(Opcode.STORE.value, addr)
            return
        if t == 'set':
            self.expr(n['expr'])
            self._emit(Opcode.STORE.value, self._addr(n['name']))
            return
        if t == 'defunc':
            self.funcs[n['name']] = (n['params'], n['body'])
            return
        if t == 'print_string':
            self.expr({'type': 'funcall', 'name': 'print_string', 'args': [n['value']]})
            return
        if t == 'if':
            l_else, l_end = self._lab('ELSE'), self._lab('END')
            self.expr(n['cond'])
            self._emit(Opcode.JZ.value, l_else)
            self.node(n['then'])
            self._emit(Opcode.JMP.value, l_end)
            self._label(l_else)
            if n.get('else'):
                self.node(n['else'])
            self._label(l_end)
            return
        if t == 'while':
            l_start, l_end = self._lab('W0'), self._lab('W1')
            self._label(l_start)
            self.expr(n['cond'])
            self._emit(Opcode.JZ.value, l_end)
            for stmt in n['body']:
                self.node(stmt)
            self._emit(Opcode.JMP.value, l_start)
            self._label(l_end)
            return
        if t == 'funcall':
            self.expr(n)
            return
        self.expr(n)

    def _emit_funcs(self):
        for name, (params, body) in self.funcs.items():
            self.scopes.append({})
            self._label(name)
            # PROLOGUE: pop return, then pop args, then restore return
            ret_tmp = self._decl('_ret')
            self._emit(Opcode.POP.value)
            self._emit(Opcode.STORE.value, ret_tmp)
            for p in reversed(params):
                self._emit(Opcode.POP.value)
                self._emit(Opcode.STORE.value, self._decl(p))
            self._emit(Opcode.LOAD.value, ret_tmp)
            self._emit(Opcode.PUSH.value)
            # function body
            for stmt in body:
                self.node(stmt)
            self._emit(Opcode.RET.value)
            self.scopes.pop()

    def _link(self):
        addr = 0
        for ln in self.data_lines:
            self.data_addr[ln.split()[0]] = addr
            addr += 1
        pc, lbl_addr = 0, {}
        for ln in self.code_lines:
            if ln.endswith(':'):
                lbl_addr[ln[:-1]] = pc
            else:
                pc += 1
        out, pc = [], 0
        for ln in self.code_lines:
            if ln.endswith(':'):
                continue
            parts = ln.split()
            if len(parts) == 2:
                op, arg = parts
                if op in BRANCH_OPS and arg in lbl_addr:
                    arg = str(lbl_addr[arg] - pc - 1)
                elif arg in self.data_addr:
                    arg = str(self.data_addr[arg])
                ln = f"{op} {arg}"
            out.append(ln)
            pc += 1
        return out

    def to_binary(self):
        linked = self._link()
        binary = bytearray()
        for line in linked:
            parts = line.split()
            op = parts[0]
            opcode = OPCODE_TABLE[op]
            arg = int(parts[1]) if len(parts) == 2 else 0
            if arg < 0:
                arg &= (1 << 27) - 1
            word = (opcode << 27) | arg
            binary.extend(word.to_bytes(4, 'big'))
        return binary

    def generate(self, prog):
        for s in prog:
            self.node(s)
        self._emit(Opcode.HALT.value)
        self._emit_funcs()

    def code(self):
        return '\n'.join(['.data'] + self.data_lines + ['', '.text'] + self._link())


if __name__ == '__main__':
    from tokenizer import LispParser, ast_to_expr

    with open(sys.argv[1], 'r', encoding='utf-8') as f:
        source = f.read()
    parser = LispParser(source)
    raw_ast = parser.parse_program()
    high_ast = [ast_to_expr(e) for e in raw_ast]
    gen = CodeGenerator()
    gen.generate(high_ast)
    print(gen.code())
    out_bytes = gen.to_binary()
    with open(sys.argv[2], 'wb') as f:
        f.write(out_bytes)
