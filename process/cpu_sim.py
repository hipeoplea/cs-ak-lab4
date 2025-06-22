import struct
from microcode_memory import ROM, OPCODE_TO_UADDR

class Registers:
    def __init__(self):
        self.ACC = 0
        self.SP = 0x7FFFFFFC
        self.IP = 0
        self.DR = 0
        self.DataA = 0
        self.uPC = 0
        self.IR = 0
        self.Z = 0
        self.N = 0
        self.halted = False
        self.macro_cnt = 0

class Memory:
    def __init__(self):
        self.data = {}
        self.instr = []

class CPU:
    def __init__(self, instr_mem, data_mem, log_path="trace.log"):
        self.ROM = ROM
        self.LUT = OPCODE_TO_UADDR

        self.registers = Registers()
        self.memory = Memory()
        self.memory.instr = instr_mem
        self.memory.data = data_mem

        self.log = open(log_path, "w", encoding="utf-8")

    def fetch_next_instruction(self):
        r = self.registers
        if r.IP >= len(self.memory.instr):
            print(f"[FETCH] IP вышел за пределы памяти: IP={r.IP}")
            r.halted = True
            return

        r.IR = self.memory.instr[r.IP]
        opcode = (r.IR >> 27) & 0x1F
        argument = r.IR & 0x07FFFFFF
        if argument & (1 << 26):
            argument -= (1 << 27)

        r.DR = argument
        r.uPC = self.LUT[opcode]
        r.macro_cnt += 1
        print(f"OPCODE={opcode} uPC={self.LUT[opcode]} ROM[{self.LUT[opcode]}]={hex(self.ROM[self.LUT[opcode]])}")
        self.log.write(f"[TICK  {r.macro_cnt} (FETCH)] IP={r.IP:04} OPCODE={opcode:02} ARG={argument}\n")
        self.log.write("-" * 40 + "\n")

    def step(self):
        r = self.registers
        uword = self.ROM[r.uPC]
        r.macro_cnt += 1

        halted = (uword >> 26) & 1
        acc_l = (uword >> 25) & 1
        dal = (uword >> 24) & 1
        mem_l = (uword >> 23) & 1
        sp_l = (uword >> 22) & 1
        dr_l = (uword >> 21) & 1
        out_l = (uword >> 20) & 1
        ip_l = (uword >> 19) & 1
        adr_sel = (uword >> 18) & 1
        io_sel = (uword >> 17) & 1
        cla = (uword >> 15) & 0b11
        cld = (uword >> 13) & 0b11
        ip_sel = (uword >> 12) & 1
        alu_op = (uword >> 9) & 0b111
        cond = (uword >> 6) & 0b111
        next_u = uword & 0x3F

        # ───── ALU ─────
        left = {1: r.ACC, 2: r.SP}.get(cla, 0)
        right = {1: r.DR, 2: r.IP}.get(cld, 0)

        if alu_op == 0b000:
            alu = (left + right) & 0xFFFFFFFF
        elif alu_op == 0b001:
            alu = (left - right) & 0xFFFFFFFF
        elif alu_op == 0b010:
            alu = (left * right) & 0xFFFFFFFF
        elif alu_op == 0b011:
            alu = (left // right if right != 0 else 0) & 0xFFFFFFFF
        elif alu_op == 0b100:
            alu = (right + 1) & 0xFFFFFFFF
        elif alu_op == 0b101:
            alu = (left - 1) & 0xFFFFFFFF
        else:
            alu = 0

        if acc_l:
            r.ACC = 0 if io_sel else alu

        if dal:
            r.DataA = r.DR if adr_sel else r.ACC

        if mem_l:
            self.memory.data[r.DataA] = r.ACC & 0xFFFFFFFF

        if dr_l:
            r.DR = self.memory.data.get(r.DataA, 0)

        if sp_l:
            r.SP = alu

        if out_l:
            print(f"[OUT]: {chr(r.ACC & 0xFF)}")

        if ip_l:
            if ip_sel == 0b00:
                r.IP = alu
            elif ip_sel == 0b01:
                r.IP = r.DR

        cond_true = (
                (cond == 0b001) or
                (cond == 0b010 and r.Z == 1) or
                (cond == 0b011 and r.N != 0) or
                (cond == 0b100 and r.Z == 0) or
                (cond == 0b101 and r.N == 0 and r.Z == 0)
        )

        self.last_uPC = r.uPC
        r.uPC = next_u if cond_true else (r.uPC + 1) & 0x3F

        if halted:
            r.halted = True

        self.print_state()

        if r.uPC == 0 and not r.halted and self.last_uPC != 0:
            self.fetch_next_instruction()

    def run(self):
        self.fetch_next_instruction()
        while not self.registers.halted:
            self.step()

    def print_memory(self):
        print("=== .data memory (адрес: значение) ===")
        for addr, val in sorted(self.memory.data.items()):
            print(f"{addr:>5} : {val}")

        print("\n=== .text memory (opcode, аргумент) ===")
        for i, word in enumerate(self.memory.instr):
            opcode = (word >> 27) & 0x1F
            arg = word & 0x07FFFFFF
            if arg & (1 << 26):
                arg -= (1 << 27)
            print(f"{i:04}: opcode={opcode:>2}, arg={arg}")

    def print_state(self):
        r = self.registers
        self.log.write(f"[TICK {r.macro_cnt}] uPC={r.uPC:02} IR={r.IR:08X}\n")
        self.log.write(f"ACC={r.ACC:11} DR={r.DR:11} IP={r.IP:08X} SP={r.SP:08X}\n")
        self.log.write(f"DataA={r.DataA} Z={r.Z} N={r.N}\n")
        self.log.write("-" * 40 + "\n")


def load_binary(filepath):
    with open(filepath, 'rb') as f:
        data = f.read()

    word_count, = struct.unpack_from('>I', data, 0)
    offset = 4

    data_mem = {}
    for _ in range(word_count):
        addr, val = struct.unpack_from('>II', data, offset)
        data_mem[addr] = val
        offset += 8

    instr_mem = []
    while offset < len(data):
        word, = struct.unpack_from('>I', data, offset)
        instr_mem.append(word)
        offset += 4

    return instr_mem, data_mem


instr_mem, data_mem = load_binary("..\\test_binop.bin")
cpu = CPU(instr_mem, data_mem)
cpu.print_memory()
cpu.run()
cpu.print_memory()