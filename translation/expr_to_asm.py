from tokenizer import *


class CodeGenerator:
    def __init__(self):
        self.label_cnt = 0
        self.var_addr = {}
        self.next_var = 100
        self.func_table = {}
        self.data_section = []
        self.code_section = []

    def new_label(self, prefix='L'):
        label = f'{prefix}_{self.label_cnt}'
        self.label_cnt += 1
        return label

    def emit(self, line):
        self.code_section.append(line)

    def declare_var(self, name):
        if name not in self.var_addr:
            self.var_addr[name] = name
            self.data_section.append(f'{name} .word 0')

    def gen_expr(self, expr):
        t = expr['type']
        if t == 'number':
            self.emit(f'LOADI {expr["value"]}')
        elif t == 'var':
            self.emit(f'LOAD {expr["name"]}')
        elif t == 'binop':
            self.gen_expr(expr['left'])
            self.emit('PUSH')
            self.gen_expr(expr['right'])
            self.emit('POP tmp')
            self.declare_var('tmp')
            op = expr['op']
            if op == '+':
                self.emit('ADD tmp')
            elif op == '-':
                self.emit('SUB tmp')
            elif op == '*':
                self.emit('MUL tmp')
            elif op == '/':
                self.emit('DIV tmp')
            elif op == '=':
                l1 = self.new_label('IF_TRUE')
                l2 = self.new_label('END_IF')
                self.emit('SUB tmp')
                self.emit(f'JZ {l1}')
                self.emit('LOADI 0')
                self.emit(f'JMP {l2}')
                self.emit(f'{l1}:')
                self.emit('LOADI 1')
                self.emit(f'{l2}:')
            elif op in ['=', '!=', '<', '>']:
                l1 = self.new_label('IF_TRUE')
                l2 = self.new_label('END_IF')
                self.emit('SUB tmp')

                if op == '=':
                    self.emit(f'JZ {l1}')
                elif op == '!=':
                    self.emit(f'JNZ {l1}')
                elif op == '<':
                    self.emit(f'JLT {l1}')
                elif op == '>':
                    self.emit(f'JGT {l1}')

                self.emit('LOADI 0')
                self.emit(f'JMP {l2}')
                self.emit(f'{l1}:')
                self.emit('LOADI 1')
                self.emit(f'{l2}:')

        elif t == 'funcall':
            if expr['name'] == 'print_string':
                val = expr['args'][0]
                if val['type'] == 'string':
                    for ch in val['value']:
                        self.emit(f'LOADI {ord(ch)}')
                        self.emit('OUT 0')
                else:
                    self.gen_expr(val)
                    self.emit('OUT 0')
            else:
                for arg in expr['args']:
                    self.gen_expr(arg)
                    self.emit('PUSH')
                self.emit(f'CALL {expr["name"]}')
                for _ in expr['args']:
                    self.emit('POP tmp')
        elif t == 'read_line':
            varname = expr['value']['name']
            self.declare_var(varname)
            self.emit('IN 0')  # читаем байт
            self.emit(f'STORE {varname}')  # сохраняем в переменную
            self.emit(f'LOAD {varname}')  # загружаем обратно в ACC — как результат выражения

        else:
            raise NotImplementedError(f"Не реализовано для типа {t}")

    def gen_node(self, node):
        t = node['type']
        if t == 'var':
            self.declare_var(node['name'])
            self.gen_expr(node['expr'])
            self.emit(f'STORE {node["name"]}')
        elif t == 'set':
            self.gen_expr(node['expr'])
            self.emit(f'STORE {node["name"]}')
        elif t == 'defunc':
            self.func_table[node['name']] = (node['params'], node['body'])
        elif t == 'print_string':
            val = node['value']
            if val['type'] == 'string':
                for ch in val['value']:
                    self.emit(f'LOADI {ord(ch)}')
                    self.emit('OUT 0')
            else:
                self.gen_expr(val)
                self.emit('OUT 0')
        elif t == 'if':
            cond = node['cond']
            then_branch = node['then']
            else_branch = node['else']

            label_else = self.new_label("ELSE")
            label_end = self.new_label("ENDIF")

            self.gen_expr(cond)
            self.emit(f'JZ {label_else}')

            if then_branch:
                self.gen_node(then_branch)
            self.emit(f'JMP {label_end}')

            self.emit(f'{label_else}:')
            if else_branch:
                self.gen_node(else_branch)
            self.emit(f'{label_end}:')
        elif t == 'while':
            start_label = self.new_label('WHILE_START')
            end_label = self.new_label('WHILE_END')

            self.emit(f'{start_label}:')
            self.gen_expr(node['cond'])
            self.emit('JZ ' + end_label)

            for stmt in node['body']:
                self.gen_node(stmt)

            self.emit('JMP ' + start_label)
            self.emit(f'{end_label}:')
        elif t == 'funcall':
            self.gen_expr(node)
        else:
            self.gen_expr(node)

    def gen_functions(self):
        for name, (params, body) in self.func_table.items():
            self.emit(f'{name}:')
            for param in reversed(params):  # параметры приходят в обратном порядке
                self.declare_var(param)
                self.emit(f'POP {param}')
            for stmt in body:
                self.gen_node(stmt)
            self.emit('RET')

    def get_code(self):
        return '\n'.join(['.data'] + self.data_section +
                         ['\n.text\n_start:'] + self.code_section +
                         ['HALT'])


    def generate(self, program):
        for stmt in program:
            self.gen_node(stmt)


# if __name__ == '__main__':
#     source = """
# (var x 0)
# (while
# (read_line x)
#     (print_string x))
#         """
#     parser = LispParser(source)
#     raw = parser.parse_program()
#     print(raw)
#     prog = [ast_to_expr(expr) for expr in raw]
#     print(prog)
#     generator = CodeGenerator()
#     generator.generate(prog)
#     generator.gen_functions()
#     print(generator.get_code())
