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
        label = f'{prefix}{self.label_cnt}'
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
                self.emit('SUB tmp')  # ACC = right - left
                self.emit(f'JZ {l1}')
                self.emit('LOADI 0')
                self.emit(f'JMP {l2}')
                self.emit(f'{l1}:')
                self.emit('LOADI 1')
                self.emit(f'{l2}:')
        elif t == 'funcall':
            # Если встроенная функция print_string
            if expr['name'] == 'print_string':
                val = expr['args'][0]
                if val['type'] == 'string':
                    # Выводим каждый символ ASCII в цикле через OUT 0
                    for ch in val['value']:
                        self.emit(f'LOADI {ord(ch)}')
                        self.emit('OUT 0')
                else:
                    # например, var или funcall
                    self.gen_expr(val)
                    self.emit('OUT 0')
            else:
                # вызов пользовательской функции
                # Пока можно оставить заглушку
                pass
        else:
            raise NotImplementedError(f"Не реализовано для типа {t}")

    def gen_node(self, node):
        t = node['type']
        if t == 'var':
            self.declare_var(node['name'])
            self.gen_expr(node['expr'])
            self.emit(f'STORE {node["name"]}')
        elif t == 'defunc':
            # Сохраняем тело и параметры
            self.func_table[node['name']] = (node['params'], node['body'])
            # Здесь можно добавить генерацию функции позже
        elif t == 'print_string':
            val = node['value']
            if val['type'] == 'string':
                for ch in val['value']:
                    self.emit(f'LOADI {ord(ch)}')
                    self.emit('OUT 0')
            else:
                self.gen_expr(val)
                self.emit('OUT 0')
        else:
            self.gen_expr(node)

    def generate(self, program):
        for node in program:
            self.gen_node(node)

    def get_code(self):
        return '\n'.join(['; === DATA SECTION ==='] + self.data_section +
                         ['\n; === CODE SECTION ==='] + self.code_section +
                         ['HALT'])



# ------------------------------
# Точка входа: собрать программу
# ------------------------------

def generate(self, program):
    for stmt in program:
        self.gen_node(stmt)


if __name__ == '__main__':
    source = """
(defunc tail_recursion_loop (i) (
    (var char 0)
    (set char (+ i 48))
    (print_string char)
    (print_string "\n")
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
    print(generator.get_code())
