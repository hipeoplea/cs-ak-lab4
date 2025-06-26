import struct
import sys

from instrucrions import OPCODE_TABLE
from tokenizer import LispParser, ast_to_expr


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
        self.literal_pool[addr] = addr + 1
        length = self.allocate_temp()
        self.literal_pool[length] = len(s)
        for i, c in enumerate(s):
            self.literal_pool[self.allocate_temp()] = ord(c)
        return addr


def compile_expr(expr, ctx):
    if expr["type"] == "number":
        addr = ctx.allocate_literal(expr["value"])
        return [("load", addr)]
    if expr["type"] == "var":
        addr = ctx.lookup_var(expr["name"])
        return [("load", addr)]
    if expr["type"] == "string":
        base = ctx.store_string(expr["value"])
        addr_holder = ctx.allocate_temp()
        ctx.literal_pool[addr_holder] = base
        return [("load", addr_holder)]
    if expr["type"] == "binop":
        op_map = {"+": "add", "-": "sub", "*": "mul", "/": "div"}
        code = []
        code += compile_expr(expr["left"], ctx)
        code += [("push",)]
        code += compile_expr(expr["right"], ctx)
        tmp = ctx.allocate_temp()
        code += [("store", tmp), ("pop",)]
        code += [(op_map[expr["op"]], tmp)]

        return code

    raise NotImplementedError(f"Unknown expr type: {expr['type']}")


def compile_read_line(expr, ctx):
    addr = ctx.lookup_var(expr["value"]["name"])

    ptr = ctx.allocate_temp()
    newline = ctx.allocate_literal(ord("\n"))
    one = ctx.allocate_literal(1)
    zero = ctx.allocate_literal(0)
    temp_indirect = ctx.allocate_literal(2)
    tmp_char = ctx.allocate_temp()

    code = [("load", zero), ("store", ptr)]
    code += [("load", addr), ("add", one), ("store", addr)]

    code += [("in", 0)]
    code += [("store", tmp_char)]
    code += [("load", tmp_char), ("sub", newline)]

    code += [("jz", 11)]
    code += [("load", ptr), ("add", addr), ("add", one), ("store", temp_indirect)]

    code += [("load", tmp_char), ("store_addr", temp_indirect)]
    code += [("load", ptr), ("add", one), ("store", ptr)]
    code += [("jmp", -14)]
    code += [("load", ptr), ("store_addr", addr)]
    return code


def compile_print_var(ctx, var_expr=None, address=None):
    if address is None:
        addr = ctx.lookup_var(var_expr["name"])
    else:
        addr = address
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
    code += [("jmp", -12)]

    return code


def compile_print_string(expr, ctx):
    val = expr["value"]

    if val["type"] != "string":
        return compile_print_var(ctx, var_expr=val)

    s = val["value"]
    addr = ctx.store_string(s)
    return compile_print_var(ctx, address=addr)


def compile_stmt(stmt, ctx):
    handlers = {
        "var": compile_var_stmt,
        "set": compile_set_stmt,
        "print_string": compile_print_string_stmt,
        "read_line": compile_read_line_stmt,
    }
    handler = handlers.get(stmt["type"])
    if handler:
        return handler(stmt, ctx)
    raise NotImplementedError(f"Unknown stmt type: {stmt['type']}")


def compile_var_stmt(stmt, ctx):
    size = stmt.get("size")
    addr = ctx.define_var(stmt["name"], size)
    expr = stmt.get("expr")

    if expr and expr["type"] == "number":
        ctx.literal_pool[addr] = expr["value"]
        ctx.var_is_number[stmt["name"]] = True
        return [*compile_expr(expr, ctx), ("store", addr)]

    if expr and expr["type"] == "binop":
        left = expr["left"]
        right = expr["right"]
        if left["type"] == "number" and right["type"] == "number":
            op = expr["op"]
            result = eval(f"{left['value']} {op} {right['value']}")
            ctx.literal_pool[addr] = result
            ctx.var_is_number[stmt["name"]] = True
            return [*compile_expr(expr, ctx), ("store", addr)]

    return [*compile_expr(expr, ctx), ("store", addr)] if expr else []


def compile_set_stmt(stmt, ctx):
    addr = ctx.lookup_var(stmt["name"])
    return [*compile_expr(stmt["expr"], ctx), ("store", addr)]



def compile_print_string_stmt(stmt, ctx):
    val = stmt["value"]
    if val["type"] == "var":
        return compile_print_var(ctx, var_expr=val)
    return compile_print_string(stmt, ctx)


def compile_read_line_stmt(stmt, ctx):
    return compile_read_line(stmt, ctx)


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

        hex_lines = []
        for addr, instr in enumerate(code):
            opcode = OPCODE_TABLE[instr[0]]
            arg = instr[1] if len(instr) > 1 else 0
            word = (opcode << 27) | (arg & 0x07FFFFFF)
            f.write(struct.pack(">I", word))

            hex_word = f"{word:08X}"
            mnemonic = instr[0]
            if len(instr) > 1:
                mnemonic += f" {arg}"
            hex_lines.append(f"{addr:04} - {hex_word} - {mnemonic}")

        for addr, val in sorted(data.items()):
            f.write(struct.pack(">Ii", addr, val))
        with open(path+".hex", "w", encoding="utf-8") as fhex:
            fhex.write("\n".join(hex_lines))


def main(input_path, output_path):
    with open(input_path, encoding="utf-8") as f:
        source = f.read()

    parser = LispParser(source)
    ast = [ast_to_expr(e) for e in parser.parse_program()]
    code, ctx = compile_program(ast)
    data = collect_data_section(ctx)
    write_binary_file(output_path, code, data)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python compiler.py <source.lisp> <out.bin>")
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])

