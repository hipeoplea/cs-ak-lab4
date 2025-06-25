import sys
import struct
from tokenizer import LispParser, ast_to_expr
from instrucrions import OPCODE_TABLE


class CompileContext:
    def __init__(self):
        self.var_map = {}
        self.literal_pool = {}
        self.temp_counter = 0
        self.next_addr = 0
        self.code = []
        self.literal_rev = {}
        self.var_is_number = {}
        self.array_sizes = {}


    def allocate_literal(self, value):
        if value in self.literal_rev:
            return self.literal_rev[value]
        addr = self.next_addr
        self.literal_pool[addr] = value
        self.literal_rev[value] = addr
        self.next_addr += 1
        return addr

    def define_var(self, name, size=None):
        addr = self.next_addr
        self.var_map[name] = addr
        if size is not None:
            self.array_sizes[name] = size
            self.next_addr += size
        else:
            self.next_addr += 1
        return addr

    def lookup_var(self, name):
        return self.var_map[name]

    def allocate_temp(self):
        addr = self.next_addr
        self.next_addr += 1
        return addr

    def store_string(self, s):
        addr = self.allocate_temp()
        self.literal_pool[addr] = len(s)
        for i, c in enumerate(s):
            self.literal_pool[addr + 1 + i] = ord(c)
            self.next_addr += 1
        return addr


def compile_expr(expr, ctx):
    if expr["type"] == "number":
        addr = ctx.allocate_literal(expr["value"])
        return [("load", addr)]
    elif expr["type"] == "var":
        addr = ctx.lookup_var(expr["name"])
        return [("load", addr)]
    elif expr["type"] == "string":
        base = ctx.store_string(expr["value"])
        addr_holder = ctx.allocate_temp()
        ctx.literal_pool[addr_holder] = base
        return [("load", addr_holder)]
    elif expr["type"] == "binop":
        op_map = {"+": "add", "-": "sub", "*": "mul", "/": "div"}
        code = []
        code += compile_expr(expr["left"], ctx)
        code += [("push",)]
        code += compile_expr(expr["right"], ctx)
        tmp = ctx.allocate_temp()
        code += [("store", tmp), ("pop",)]
        code += [(op_map[expr["op"]], tmp)]

        return code

    else:
        raise NotImplementedError(f"Unknown expr type: {expr['type']}")


def compile_read_line(expr, ctx):
    addr = ctx.lookup_var(expr["value"]["name"])

    ptr = ctx.allocate_temp()
    newline = ctx.allocate_literal(ord('\n'))
    one = ctx.allocate_literal(1)
    zero = ctx.allocate_literal(0)
    temp_indirect = ctx.allocate_temp()
    tmp_char = ctx.allocate_temp()

    code = [("load", zero), ("store", ptr)]

    loop_start = len(ctx.code) + len(code)

    code += [("in", 0)]
    code += [("store", tmp_char)]

    code += [("load", ptr), ("add", addr), ("store", temp_indirect)]
    code += [("load", tmp_char), ("store_addr", temp_indirect)]

    code += [("load", tmp_char), ("sub", newline)]
    code += [("jz", 7)]
    code += [("load", ptr), ("add", one), ("store", ptr)]
    code += [("jmp", -(len(code) - loop_start))]

    code += [("load", ptr), ("store", addr)]
    return code






def compile_print_var(var_expr, ctx):
    var_name = var_expr["name"]
    addr = ctx.lookup_var(var_name)

    if ctx.var_is_number.get(var_name):
        val = ctx.literal_pool.get(addr)
        return compile_print_string({
            "type": "print_string",
            "value": {"type": "string", "value": str(val)}
        }, ctx)

    ptr = ctx.allocate_temp()
    end = ctx.allocate_temp()
    temp_len = ctx.allocate_temp()
    one = ctx.allocate_literal(1)

    code = []
    code += [("load_addr", addr), ("store", temp_len)]
    code += [("load", addr), ("add", one), ("store", ptr)]
    code += [("load", addr), ("add", one), ("add", temp_len), ("store", end)]
    code += [("load", ptr), ("sub", end), ("jz", 7)]
    code += [("load_addr", ptr), ("out", 0)]
    code += [("load", ptr), ("add", one), ("store", ptr)]
    code += [("jmp", -8)]

    return code







def compile_print_string(expr, ctx):
    val = expr["value"]
    print(val)
    if val["type"] != "string":
        return compile_print_var(val, ctx)

    s = val["value"]
    base = ctx.store_string(s)

    ptr = ctx.allocate_temp()
    end = ctx.allocate_temp()
    one = ctx.allocate_literal(1)

    code = []
    code += [("load", ctx.allocate_literal(base + 1)), ("store", ptr)]
    code += [("load", ctx.allocate_literal(base + len(s) + 1)), ("store", end)]

    loop_start = len(ctx.code) + len(code)
    code += [("load", end), ("sub", ptr), ("jz", 7)]
    code += [("load_addr", ptr), ("out", 0)]
    code += [("load", ptr), ("add", one), ("store", ptr)]
    code += [("jmp", -(len(code) - loop_start))]

    return code




def compile_stmt(stmt, ctx):
    if stmt["type"] == "var":
        size = stmt.get("size")
        addr = ctx.define_var(stmt["name"], size)
        expr = stmt.get("expr")

        if expr and expr["type"] == "number":
            ctx.literal_pool[addr] = expr["value"]
            ctx.var_is_number[stmt["name"]] = True
            return compile_expr(expr, ctx) + [("store", addr)]

        elif expr and expr["type"] == "binop":
            left = expr["left"]
            right = expr["right"]
            if left["type"] == "number" and right["type"] == "number":
                op = expr["op"]
                result = eval(f"{left['value']} {op} {right['value']}")
                ctx.literal_pool[addr] = result
                ctx.var_is_number[stmt["name"]] = True
                return compile_expr(expr, ctx) + [("store", addr)]

        return compile_expr(expr, ctx) + [("store", addr)] if expr else []


    elif stmt["type"] == "set":
        addr = ctx.lookup_var(stmt["name"])
        return compile_expr(stmt["expr"], ctx) + [("store", addr)]

    elif stmt["type"] == "print_string":
        return compile_print_string(stmt, ctx)

    elif stmt["type"] == "read_line":
        return compile_read_line(stmt, ctx)

    else:
        raise NotImplementedError(f"Unknown stmt type: {stmt['type']}")


def compile_program(ast_list):
    ctx = CompileContext()
    for node in ast_list:
        code = compile_stmt(node, ctx)
        ctx.code.extend(code)
    ctx.code.append(("halt",))
    return ctx.code, ctx


def collect_data_section(ctx):
    data = {}
    for addr, val in ctx.literal_pool.items():
        data[addr] = val
    for name, addr in ctx.var_map.items():
        if addr not in data:
            data[addr] = 0
    return data


def write_binary_file(path, code, data):
    with open(path, "wb") as f:
        f.write(struct.pack(">I", len(code)))

        for instr in code:
            opcode = OPCODE_TABLE[instr[0]]
            arg = instr[1] if len(instr) > 1 else 0
            word = (opcode << 27) | (arg & 0x07FFFFFF)
            f.write(struct.pack(">I", word))

        for addr, val in sorted(data.items()):
            f.write(struct.pack(">Ii", addr, val))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python compiler.py <source.lisp> <out.bin>")
        sys.exit(1)

    with open(sys.argv[1], encoding="utf-8") as f:
        source = f.read()

    parser = LispParser(source)
    ast = [ast_to_expr(e) for e in parser.parse_program()]
    print(ast)
    code, ctx = compile_program(ast)
    data = collect_data_section(ctx)
    print(code)
    print(data)
    write_binary_file(sys.argv[2], code, data)
