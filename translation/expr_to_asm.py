import struct
import sys

from tokenizer import *
from instrucrions import *


class CodeGenerator:
    def __init__(self):
        self.lab_cnt = 0
        # секции
        self.data_lines, self.code_lines = [], []
        # карты адресов
        self.data_addr: dict[str, int] = {}
        self.const_map: dict[int, str] = {}         # value → label
        self.funcs: dict[str, tuple[list[str], list[dict]]] = {}
        self.scopes: list[dict[str, str]] = [{}]    # переменные

    def _lab(self, p='L'):
        self.lab_cnt += 1
        return f'{p}{self.lab_cnt}'

    def _const(self, v: int):
        if v not in self.const_map:
            lbl = f'c_{v}'
            self.const_map[v] = lbl
            self.data_lines.append(f'{lbl} .word {v}')
        return self.const_map[v]

    def _emit(self, op: str, arg: str | int | None = None):
        self.code_lines.append(op if arg is None else f"{op} {arg}")

    def _label(self, name: str):
        self.code_lines.append(f"{name}:")

    def _decl(self, name: str):
        scope = self.scopes[-1]
        if name not in scope:
            addr = f'{name}_{len(self.scopes)-1}'
            scope[name] = addr
            self.data_lines.append(f'{addr} .word 0')
        return scope[name]

    def _addr(self, name: str):
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        raise NameError(name)

    # ───────── expr ─────────
    def expr(self, e):
        t = e['type']

        if t == 'number':
            self._emit(Opcode.LOAD.value, self._const(e['value']))
            return

        if t in ('var'):
            self._emit(Opcode.LOAD.value, self._addr(e['name']))
            return

        if t == 'string':
            s = e['value'].rstrip('\n')[:32]  # <= здесь убираем \n
            self._emit(Opcode.LOAD.value, self._const(len(s)))  # длина
            self._emit(Opcode.OUT.value, 0)
            for ch in s:
                self._emit(Opcode.LOAD.value, self._const(ord(ch)))
                self._emit(Opcode.OUT.value, 0)
            return

        if t == 'binop':
            l, r, op = e['left'], e['right'], e['op']
            tl, tr = self._decl('_tl'), self._decl('_tr')
            self.expr(l); self._emit(Opcode.STORE.value, tl)
            self.expr(r); self._emit(Opcode.STORE.value, tr)
            self._emit(Opcode.LOAD.value, tl)
            if op in '+-*/':
                self._emit({'+': Opcode.ADD, '-': Opcode.SUB, '*': Opcode.MUL, '/': Opcode.DIV}[op].value, tr)
                return
            self._emit(Opcode.SUB.value, tr)
            lt, le = self._lab('T'), self._lab('E')
            self._emit({'=': Opcode.JZ, '!=': Opcode.JNZ, '<': Opcode.JLT, '>': Opcode.JGT}[op].value, lt)
            self._emit(Opcode.LOAD.value, self._const(0))
            self._emit(Opcode.JMP.value, le)
            self._label(lt)
            self._emit(Opcode.LOAD.value, self._const(1))
            self._label(le)
            return

        if t == 'funcall':
            if e['name'] == 'print_string':
                arg = e['args'][0]
                if arg['type'] == 'string':
                    self.expr(arg)
                else:
                    self._emit(Opcode.LOAD.value, self._const(0))
                    self._emit(Opcode.OUT.value, 0)
                return
            for a in e['args']:
                self.expr(a); self._emit(Opcode.PUSH.value)
            self._emit(Opcode.CALL.value, e['name'])
            return

        if t == 'read_line':
            a = self._addr(e['value']['name'])
            self._emit(Opcode.IN_.value, 0)
            self._emit(Opcode.STORE.value, a)
            self._emit(Opcode.LOAD.value, a)
            return

        raise NotImplementedError(t)

    def node(self, n):
        if n is None:
            return
        t = n['type']
        if t in ('var', 'var_decl'):
            a = self._decl(n['name'])
            if 'expr' in n and not (n['expr']['type'] == 'number' and n['expr']['value'] == 0):
                self.expr(n['expr']); self._emit(Opcode.STORE.value, a)
            return
        if t == 'set':
            self.expr(n['expr']); self._emit(Opcode.STORE.value, self._addr(n['name']))
            return
        if t == 'defunc':
            self.funcs[n['name']] = (n['params'], n['body'])
            return
        if t == 'print_string':
            self.expr({'type': 'funcall', 'name': 'print_string', 'args': [n['value']]})
            return
        if t == 'if':
            le, ld = self._lab('ELSE'), self._lab('END')
            self.expr(n['cond']); self._emit(Opcode.JZ.value, le)
            self.node(n['then']); self._emit(Opcode.JMP.value, ld)
            self._label(le); self.node(n.get('else'))
            self._label(ld)
            return
        if t == 'while':
            ls, le = self._lab('W0'), self._lab('W1')
            self._label(ls)
            self.expr(n['cond']); self._emit(Opcode.JZ.value, le)
            for s in n['body']:
                self.node(s)
            self._emit(Opcode.JMP.value, ls)
            self._label(le)
            return
        if t == 'funcall':
            self.expr(n)
            return
        self.expr(n)

    def _emit_funcs(self):
        for name, (params, body) in self.funcs.items():
            self.scopes.append({})
            self._label(name)
            ret_tmp = self._decl('_ret')
            self._emit(Opcode.POP.value)
            self._emit(Opcode.STORE.value, ret_tmp)
            for p in reversed(params):
                self._emit(Opcode.POP.value)
                self._emit(Opcode.STORE.value, self._decl(p))
            self._emit(Opcode.LOAD.value, ret_tmp)
            self._emit(Opcode.PUSH.value)
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

    def generate(self, prog):
        for s in prog:
            self.node(s)
        self._emit(Opcode.HALT.value)
        self._emit_funcs()

    def code(self):
        return '\n'.join(['.data'] + self.data_lines + ['', '.text'] + self._link())

    def to_binary(self):
        linked = self._link()
        binary = bytearray()

        word_count = len(self.data_lines)
        binary.extend(struct.pack('>I', word_count))  # количество .word

        for i, line in enumerate(self.data_lines):
            value = int(line.split()[-1])
            binary.extend(struct.pack('>I', i))  # адрес
            binary.extend(struct.pack('>I', value))  # значение

        for line in linked:
            parts = line.split()
            op = parts[0]
            opcode = OPCODE_TABLE[op]
            arg = int(parts[1]) if len(parts) == 2 else 0
            if arg < 0:
                arg &= (1 << 27) - 1
            word = (opcode << 27) | arg
            binary.extend(struct.pack('>I', word))

        return binary


if __name__ == '__main__':
    if sys.argv[1] == '--test':
        code = """
        (defunc f (x) ((print_string x)))
        (funcall f ("Hello!\n"))
        """
        parser = LispParser(code)
        raw = parser.parse_program()
        prog = [ast_to_expr(e) for e in raw]
        gen = CodeGenerator()
        gen.generate(prog)
        print("ASM:", gen.code())
        print("HEX:", gen.to_binary())
    else:
        with open(sys.argv[1], 'r', encoding='utf-8') as f:
            src = f.read()
        parser = LispParser(src)
        prog = [ast_to_expr(e) for e in parser.parse_program()]
        gen = CodeGenerator()
        gen.generate(prog)
        with open(sys.argv[2].replace('.bin', '.txt'), 'w') as f:
            f.write(gen.code())
        with open(sys.argv[2].replace('.bin', '.sym'), 'w') as f:
            for name, addr in gen.data_addr.items():
                f.write(f'{name} = {addr}\n')
        with open(sys.argv[2], 'wb') as f:
            f.write(gen.to_binary(with_data=True))
