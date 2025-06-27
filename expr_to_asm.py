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
        self.functions = {}
        self.function_addrs = {}
        self.pending_calls = []

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

    def define_function(self, name, params, body):
        self.functions[name] = {"params": params, "body": body}


def compile_expr(expr, ctx):
    if expr["type"] == "binop" and expr["op"] == "=":
        code = []
        code += compile_expr(expr["left"], ctx)
        code += [("push",)]
        code += compile_expr(expr["right"], ctx)
        tmp = ctx.allocate_temp()
        code += [("store", tmp), ("pop",)]
        code += [("sub", tmp)]
        return code

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


def compile_funcall(stmt, ctx):
    fname = stmt["name"]
    args = stmt["args"]
    param_names = ctx.functions[fname]["params"]

    code = []

    for arg_expr, param in zip(args, param_names):
        code += compile_expr(arg_expr, ctx)
        code += [("store", ctx.lookup_var(param["name"]))]

    code.append(("call", ("PENDING", fname)))

    return code



def compile_if(stmt, ctx):
    cond_code = compile_expr(stmt["cond"], ctx)
    code = []
    code += cond_code
    if stmt["then"] is not None:
        then_code = compile_stmt(stmt["then"], ctx)
        code += [("jz", len(then_code) + 2)]
        code += then_code
    else_code = compile_stmt(stmt["else"], ctx) if stmt.get("else") else []
    code += [("jz", len(else_code) + 1)]
    code += else_code
    return code


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
    code = []
    if address is None:
        var_name = var_expr["name"]
        addr = ctx.lookup_var(var_name)

        if var_name in ctx.array_sizes:
            return compile_print_var(ctx, address=addr)

        return [("load", addr), ("out", 0)]


    addr = address
    ptr = ctx.allocate_temp()
    end = ctx.allocate_temp()
    temp_len = ctx.allocate_temp()
    one = ctx.allocate_literal(1)

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
        "funcall": compile_funcall,
        "if": compile_if,
        "defunc": lambda s, ctx: []
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

def collect_functions(ast_list, ctx):
    for node in ast_list:
        if node["type"] == "defunc":
            ctx.define_function(node["name"], node["params"], node["body"])

def compile_all_functions(ctx):
    for fname, f in ctx.functions.items():
        if ctx.function_addrs[fname] is None:
            ctx.function_addrs[fname] = len(ctx.code)
        for param in f["params"]:
            ctx.define_var(param["name"])
        for stmt in f["body"]:
            ctx.code.extend(compile_stmt(stmt, ctx))
        ctx.code.append(("ret",))

def patch_pending_calls(ctx):
    for idx, instr in enumerate(ctx.code):
        if instr[0] == "call" and isinstance(instr[1], tuple) and instr[1][0] == "PENDING":
            fname = instr[1][1]
            addr = ctx.function_addrs[fname]
            rel = addr - idx
            ctx.code[idx] = ("call", rel)

def compile_program(ast_list):
    ctx = CompileContext()

    main_jump_placeholder = len(ctx.code)
    ctx.code.append(("jmp", 0))

    collect_functions(ast_list, ctx)

    for fname in ctx.functions:
        ctx.function_addrs[fname] = None

    compile_all_functions(ctx)

    main_start = len(ctx.code)
    for node in ast_list:
        if node["type"] != "defunc":
            ctx.code.extend(compile_stmt(node, ctx))

    ctx.code.append(("halt",))
    patch_pending_calls(ctx)
    ctx.code[main_jump_placeholder] = ("jmp", main_start)

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
