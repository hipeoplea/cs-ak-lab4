from tokenizer import *
from instrucrions import Opcode  # импортируем перечисление инструкций

class CodeGenerator:
    def __init__(self):
        self.label_cnt = 0
        self.data_section = []
        self.code_section = []
        self.func_table = {}
        self.scopes = [{}]  # стек областей видимости

    def new_label(self, prefix='L'):
        label = f'{prefix}_{self.label_cnt}'
        self.label_cnt += 1
        return label

    def emit(self, line):
        self.code_section.append(line)

    def declare_var(self, name):
        current_scope = self.scopes[-1]
        if name not in current_scope:
            addr = f'{name}_{len(self.scopes)-1}'
            current_scope[name] = addr
            self.data_section.append(f'{addr} .word 0')
        return current_scope[name]

    def lookup_var(self, name):
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        raise NameError(f"Variable '{name}' not declared in any visible scope")

    def gen_expr(self, expr):
        t = expr['type']
        if t == 'number':
            self.emit(f'{Opcode.LOADI.value} {expr["value"]}')
        elif t == 'var':
            addr = self.lookup_var(expr['name'])
            self.emit(f'{Opcode.LOAD.value} {addr}')
        elif t == 'binop':
            self.gen_expr(expr['left'])
            self.emit(Opcode.PUSH.value)
            self.gen_expr(expr['right'])
            self.emit('POP tmp')
            tmp_addr = self.declare_var('tmp')
            op = expr['op']
            if op == '+':
                self.emit(f'{Opcode.ADD.value} {tmp_addr}')
            elif op == '-':
                self.emit(f'{Opcode.SUB.value} {tmp_addr}')
            elif op == '*':
                self.emit(f'{Opcode.MUL.value} {tmp_addr}')
            elif op == '/':
                self.emit(f'{Opcode.DIV.value} {tmp_addr}')
            elif op in ['=', '!=', '<', '>']:
                l1 = self.new_label('IF_TRUE')
                l2 = self.new_label('END_IF')
                self.emit(f'{Opcode.SUB.value} {tmp_addr}')
                if op == '=':
                    self.emit(f'{Opcode.JZ.value} {l1}')
                elif op == '!=':
                    self.emit(f'{Opcode.JNZ.value} {l1}')
                elif op == '<':
                    self.emit(f'{Opcode.JLT.value} {l1}')
                elif op == '>':
                    self.emit(f'{Opcode.JGT.value} {l1}')
                self.emit(f'{Opcode.LOADI.value} 0')
                self.emit(f'{Opcode.JMP.value} {l2}')
                self.emit(f'{l1}:')
                self.emit(f'{Opcode.LOADI.value} 1')
                self.emit(f'{l2}:')
        elif t == 'funcall':
            if expr['name'] == 'print_string':
                val = expr['args'][0]
                if val['type'] == 'string':
                    for ch in val['value']:
                        self.emit(f'{Opcode.LOADI.value} {ord(ch)}')
                        self.emit(f'{Opcode.OUT.value} 0')
                else:
                    self.gen_expr(val)
                    self.emit(f'{Opcode.OUT.value} 0')
            else:
                for arg in expr['args']:
                    self.gen_expr(arg)
                    self.emit(Opcode.PUSH.value)
                self.emit(f'{Opcode.CALL.value} {expr["name"]}')
                for _ in expr['args']:
                    self.emit('POP tmp')
        elif t == 'read_line':
            varname = expr['value']['name']
            addr = self.lookup_var(varname)
            self.emit(f'{Opcode.IN.value} 0')
            self.emit(f'{Opcode.STORE.value} {addr}')
            self.emit(f'{Opcode.LOAD.value} {addr}')
        else:
            raise NotImplementedError(f"Не реализовано для типа {t}")

    def gen_node(self, node):
        t = node['type']
        if t == 'var':
            addr = self.declare_var(node['name'])
            self.gen_expr(node['expr'])
            self.emit(f'{Opcode.STORE.value} {addr}')
        elif t == 'set':
            addr = self.lookup_var(node['name'])
            self.gen_expr(node['expr'])
            self.emit(f'{Opcode.STORE.value} {addr}')
        elif t == 'defunc':
            self.func_table[node['name']] = (node['params'], node['body'])
        elif t == 'print_string':
            val = node['value']
            if val['type'] == 'string':
                for ch in val['value']:
                    self.emit(f'{Opcode.LOADI.value} {ord(ch)}')
                    self.emit(f'{Opcode.OUT.value} 0')
            else:
                self.gen_expr(val)
                self.emit(f'{Opcode.OUT.value} 0')
        elif t == 'if':
            cond = node['cond']
            then_branch = node['then']
            else_branch = node['else']
            label_else = self.new_label('ELSE')
            label_end = self.new_label('ENDIF')
            self.gen_expr(cond)
            self.emit(f'{Opcode.JZ.value} {label_else}')
            if then_branch:
                self.gen_node(then_branch)
            self.emit(f'{Opcode.JMP.value} {label_end}')
            self.emit(f'{label_else}:')
            if else_branch:
                self.gen_node(else_branch)
            self.emit(f'{label_end}:')
        elif t == 'while':
            start_label = self.new_label('WHILE_START')
            end_label = self.new_label('WHILE_END')
            self.emit(f'{start_label}:')
            self.gen_expr(node['cond'])
            self.emit(f'{Opcode.JZ.value} {end_label}')
            for stmt in node['body']:
                self.gen_node(stmt)
            self.emit(f'{Opcode.JMP.value} {start_label}')
            self.emit(f'{end_label}:')
        elif t == 'funcall':
            self.gen_expr(node)
        else:
            self.gen_expr(node)

    def gen_functions(self):
        for name, (params, body) in self.func_table.items():
            self.scopes.append({})
            self.emit(f'{name}:')
            for param in reversed(params):
                addr = self.declare_var(param)
                self.emit(f'{Opcode.POP.value} {addr}')
            for stmt in body:
                self.gen_node(stmt)
            self.emit(Opcode.RET.value)
            self.scopes.pop()

    def get_code(self):
        return '\n'.join(
            ['.data'] + self.data_section +
            ['\n.text\n_start:'] + self.code_section +
            [Opcode.HALT.value]
        )

    def generate(self, program):
        for stmt in program:
            self.gen_node(stmt)


if __name__ == '__main__':
    source = """
(defunc tail_recursion_loop (i) (
    (var char 0)
    (set char (+ i 48))
    (print_string char)
    (print_string "\\n")
    (set i (- i 1))
    (if (= i 0) (0)(funcall tail_recursion_loop (i)))
 ))
(funcall tail_recursion_loop (9)) 
 """
    parser = LispParser(source)
    raw = parser.parse_program()
    print(raw)
    prog = [ast_to_expr(expr) for expr in raw]
    print(prog)
    generator = CodeGenerator()
    generator.generate(prog)
    generator.gen_functions()
    print(generator.get_code())
