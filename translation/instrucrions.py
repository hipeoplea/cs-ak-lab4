import json
from enum import Enum

class AddressingType(int, Enum):
    DIRECT = 0
    INDIRECT = 1

class Opcode(str, Enum):
    LOADI = "loadi"
    LOAD = "load"
    STORE = "store"
    PUSH = "push"
    POP = "pop"
    ADD = "add"
    SUB = "sub"
    MUL = "mul"
    DIV = "div"
    CALL = "call"
    RET = "ret"
    IN_ = "in"
    OUT = "out"
    JMP = "jmp"
    JZ = "jz"
    JNZ = "jnz"
    JLT = "jlt"
    JGT = "jgt"
    HALT = "halt"

control_commands = [Opcode.JZ, Opcode.JNZ, Opcode.JGT, Opcode.JMP, Opcode.JLT]


def write_code(filename, code):
    with open(filename, "w", encoding="utf-8") as file:
        file.write(json.dumps(code, indent=4))


def read_code(filename):
    with open(filename, encoding="utf-8") as file:
        code = json.loads(file.read())
    return code[1:], code[0]