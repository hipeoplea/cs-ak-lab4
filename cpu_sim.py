import struct

from microcode_memory import OPCODE_TO_UADDR, ROM


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
        self.ARG = 0
        self.halted = False
        self.macro_cnt = 0


class Memory:
    def __init__(self):
        self.data = {}
        self.instr = []


def _decode_microcode(uword):
    return {
        "halted": (uword >> 26) & 1,
        "acc_l": (uword >> 25) & 1,
        "dal": (uword >> 24) & 1,
        "mem_l": (uword >> 23) & 1,
        "sp_l": (uword >> 22) & 1,
        "dr_l": (uword >> 21) & 1,
        "out_l": (uword >> 20) & 1,
        "ip_l": (uword >> 19) & 1,
        "adr_sel": (uword >> 18) & 1,
        "io_sel": (uword >> 17) & 1,
        "cla": (uword >> 15) & 0b11,
        "cld": (uword >> 13) & 0b11,
        "ip_sel": (uword >> 12) & 1,
        "alu_op": (uword >> 9) & 0b111,
        "cond": (uword >> 6) & 0b111,
        "next_u": uword & 0x3F,
    }


class CPU:
    def __init__(self, instr_mem, data_mem, log_path="trace.log", input_path=None, output_path=None):
        self.ROM = ROM
        self.LUT = OPCODE_TO_UADDR

        self.registers = Registers()
        self.memory = Memory()
        self.memory.instr = instr_mem
        self.memory.data = data_mem

        self.input_buffer = list(open(input_path, encoding="utf-8").read()) if input_path else []
        self.output_buffer = []
        self.output_path = output_path

        self.last_uPC = 0
        self.log = open(log_path, "w", encoding="utf-8")

    def fetch_next_instruction(self):
        r = self.registers
        if r.IP >= len(self.memory.instr):
            r.halted = True
            return

        r.IR = self.memory.instr[r.IP]
        r.ARG = (r.IR & 0x07FFFFFF)
        if r.ARG & (1 << 26):
            r.ARG -= (1 << 27)
        opcode = (r.IR >> 27) & 0x1F
        r.uPC = self.LUT[opcode]
        r.macro_cnt += 1
        self.log.write(f"[TICK  {r.macro_cnt} (FETCH)] IP={r.IP:04} OPCODE={opcode:02}\n")
        self.log.write("-" * 40 + "\n")
        self.print_memory()
        self.step()

    def step(self):
        r = self.registers
        uword = self.ROM[r.uPC]

        signals = _decode_microcode(uword)
        alu = self._execute_alu(signals)
        self._apply_latches(signals, alu)
        self._update_flags_and_branch(signals, alu)

    def _execute_alu(self, s):
        r = self.registers
        left = {1: r.ACC, 2: r.SP}.get(s["cla"], 0)
        right = {1: r.DR, 2: r.IP}.get(s["cld"], 0)
        op = s["alu_op"]

        alu_ops = {
            0: lambda l_alu, r_alu: l_alu + r_alu,
            1: lambda l_alu, r_alu: l_alu - r_alu,
            2: lambda l_alu, r_alu: l_alu * r_alu,
            3: lambda l_alu, r_alu: l_alu // r_alu if r_alu != 0 else 0,
            4: lambda l_alu, r_alu: l_alu + r_alu + 1,
            5: lambda l_alu, r_alu: l_alu + r_alu - 1,
        }

        return alu_ops.get(op, lambda l_alu, r_alu: 0)(left, right) & 0xFFFFFFFF

    def _update_acc(self, s, alu):
        r = self.registers
        if not s["acc_l"]:
            return
        if s["io_sel"]:
            if self.input_buffer:
                r.ACC = ord(self.input_buffer.pop(0))
            else:
                r.halted = True
        else:
            r.ACC = alu

    def _update_memory_access(self, s, alu):
        r = self.registers
        if s["dal"]:
            r.DataA = r.ARG if s["adr_sel"] else alu
        if s["mem_l"]:
            self.memory.data[r.DataA] = r.ACC & 0xFFFFFFFF
        if s["dr_l"]:
            r.DR = self.memory.data.get(r.DataA, 0)

    def _update_sp_ip_out(self, s, alu):
        r = self.registers
        if s["sp_l"]:
            r.SP = alu
        if s["out_l"]:
            ch = chr(r.ACC & 0xFF)
            self.output_buffer.append(ch)
            print(f"[OUT]: {ch}")
        if s["ip_l"]:
            r.IP = alu if s["ip_sel"] == 0 else r.ARG

    def _apply_latches(self, s, alu):
        self._update_acc(s, alu)
        self._update_memory_access(s, alu)
        self._update_sp_ip_out(s, alu)

    def _update_flags_and_branch(self, s, alu):
        r = self.registers

        r.Z = int(alu == 0)
        r.N = (alu >> 31) & 1

        cond = s["cond"]
        cond_true = (
                cond == 0b001 or
                (cond == 0b010 and r.Z == 1) or
                (cond == 0b011 and r.N != 0) or
                (cond == 0b100 and r.Z == 0) or
                (cond == 0b101 and r.N == 0 and r.Z == 0)
        )

        r.macro_cnt += 1
        self.print_state()

        self.last_uPC = r.uPC
        r.uPC = s["next_u"] if cond_true else (r.uPC + 1) & 0x3F

        if s["halted"]:
            r.halted = True

        if r.uPC == 0 and not r.halted and self.last_uPC != 0:
            self.fetch_next_instruction()

    def run(self):
        self.fetch_next_instruction()
        while not self.registers.halted:
            self.step()
        if self.output_path:
            with open(self.output_path, "w", encoding="utf-8") as f:
                f.write(str(self.output_buffer))

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


def load_binary(path):
    with open(path, "rb") as f:
        data = f.read()

    instr_count = struct.unpack_from(">I", data, 0)[0]
    instr_mem = []
    offset = 4
    for _ in range(instr_count):
        instr = struct.unpack_from(">I", data, offset)[0]
        instr_mem.append(instr)
        offset += 4

    data_mem = {}
    while offset < len(data):
        addr, val = struct.unpack_from(">Ii", data, offset)
        data_mem[addr] = val
        offset += 8

    return instr_mem, data_mem


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 4:
        print("Usage:")
        print("  python cpu_sim.py <program.bin> <input.txt> <output.txt>")
        sys.exit(1)

    bin_path = sys.argv[1]
    input_path = sys.argv[2]
    output_path = sys.argv[3]

    instr_mem, data_mem = load_binary(bin_path)

    cpu = CPU(instr_mem, data_mem, input_path=input_path, output_path=output_path)
    cpu.run()
    cpu.print_memory()
