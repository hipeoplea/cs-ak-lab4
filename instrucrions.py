from enum import Enum


class Opcode(str, Enum):
    LOAD = "load"
    LOAD_ADDR = "load_addr"
    STORE = "store"
    STORE_ADDR = "store_addr"
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

OPCODE_TABLE = {
    "halt": 0b00000,
    "load_addr": 0b00001,
    "load": 0b00010,
    "store": 0b00011,
    "push": 0b00100,
    "pop":  0b00101,
    "add":  0b00110,
    "sub":  0b00111,
    "mul":  0b01000,
    "div":  0b01001,
    "call": 0b01010,
    "ret":  0b01011,
    "in":   0b01101,
    "out":  0b01110,
    "jmp":  0b01111,
    "jz":   0b10000,
    "jnz":  0b10001,
    "jlt":  0b10010,
    "jgt":  0b10011,
    "store_addr": 0b10100
}

BRANCH_OPS = {Opcode.JMP.value, Opcode.JZ.value, Opcode.JNZ.value,
              Opcode.JLT.value, Opcode.JGT.value, Opcode.CALL.value}
