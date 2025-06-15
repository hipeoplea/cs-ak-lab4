from dataclasses import dataclass

@dataclass
class Microcomand:
    halt: int = 0
    condition_code: int = 0      # 2 bits
    condition_jump: int = 0      # 1 bit
    output_latch: int = 0
    memory_latch: int = 0
    data_reg_latch: int = 0
    ip_latch: int = 0
    data_addr_latch: int = 0
    address_selector: int = 0    # 2 bits
    io_selector: int = 0         # 2 bits
    ip_selector: int = 0         # 2 bits
    alu_control: int = 0         # 3 bits
    cla: int = 0
    cld: int = 0
    next_addr: int = 0

    def to_bits(self):
        bits = 0
        bits |= (self.halt & 1) << 19
        bits |= (self.condition_code & 0b11) << 17
        bits |= (self.condition_jump & 1) << 16
        bits |= (self.output_latch & 1) << 15
        bits |= (self.memory_latch & 1) << 14
        bits |= (self.data_reg_latch & 1) << 13
        bits |= (self.ip_latch & 1) << 12
        bits |= (self.data_addr_latch & 1) << 11
        bits |= (self.address_selector & 0b11) << 9
        bits |= (self.io_selector & 0b11) << 7
        bits |= (self.ip_selector & 0b11) << 5
        bits |= (self.alu_control & 0b111) << 2
        bits |= (self.cla & 1) << 1
        bits |= (self.cld & 1)
        return bits


def generate_microcode_for_command(opcode_hex, start_addr=0):
    microcode = {}
    def step_addr(step): return start_addr + step

    if opcode_hex in ['00001', '00010', '00011', '00100', '00101']:
        microcode[step_addr(0)] = Microcomand(
            data_addr_latch=1,
            address_selector=0b00,
            next_addr=step_addr(1)
        )
        if opcode_hex == '00001':  # LOADI
            microcode[step_addr(1)] = Microcomand(
                data_reg_latch=1,
                address_selector=0b00,
                ip_latch=1,
                next_addr=0
            )
        elif opcode_hex == '00010':  # LOAD
            microcode[step_addr(1)] = Microcomand(
                data_reg_latch=1,
                memory_latch=0,
                address_selector=0b00,
                ip_latch=1,
                next_addr=0
            )
        elif opcode_hex == '00011':  # STORE
            microcode[step_addr(1)] = Microcomand(
                memory_latch=1,
                ip_latch=1,
                next_addr=0
            )
        elif opcode_hex == '00100':  # PUSH
            microcode[step_addr(1)] = Microcomand(
                memory_latch=1,
                ip_latch=1,
                next_addr=0
            )
        elif opcode_hex == '00101':  # POP
            microcode[step_addr(1)] = Microcomand(
                data_reg_latch=1,
                ip_latch=1,
                next_addr=0
            )

    elif opcode_hex in ['00110', '00111', '01000', '01001']:
        microcode[step_addr(0)] = Microcomand(
            data_addr_latch=1,
            address_selector=0b00,
            next_addr=step_addr(1)
        )
        microcode[step_addr(1)] = Microcomand(
            data_reg_latch=1,
            next_addr=step_addr(2)
        )
        alu_ops = {
            '00110': 0b001,  # ADD
            '00111': 0b010,  # SUB
            '01000': 0b011,  # MUL
            '01001': 0b100,  # DIV
        }
        microcode[step_addr(2)] = Microcomand(
            alu_control=alu_ops[opcode_hex],
            cla=1,
            cld=1,
            ip_latch=1,
            next_addr=0
        )

    elif opcode_hex == '01010':  # CALL
        microcode[step_addr(0)] = Microcomand(
            data_addr_latch=1,
            address_selector=0b00,
            next_addr=step_addr(1)
        )
        microcode[step_addr(1)] = Microcomand(
            memory_latch=1,
            ip_latch=0,
            next_addr=step_addr(2)
        )
        microcode[step_addr(2)] = Microcomand(
            ip_selector=0b01,
            ip_latch=1,
            next_addr=0
        )

    elif opcode_hex == '01011':  # RET
        microcode[step_addr(0)] = Microcomand(
            data_addr_latch=1,
            address_selector=0b01,
            next_addr=step_addr(1)
        )
        microcode[step_addr(1)] = Microcomand(
            ip_selector=0b01,
            ip_latch=1,
            next_addr=0
        )

    elif opcode_hex == '01101':  # IN
        microcode[step_addr(0)] = Microcomand(
            io_selector=0b01,
            output_latch=1,
            ip_latch=1,
            next_addr=0
        )

    elif opcode_hex == '01110':  # OUT
        microcode[step_addr(0)] = Microcomand(
            io_selector=0b10,
            output_latch=1,
            ip_latch=1,
            next_addr=0
        )

    elif opcode_hex == '01111':  # NOP
        microcode[step_addr(0)] = Microcomand(
            ip_latch=1,
            next_addr=0
        )
    else:
        raise ValueError(f"Unknown opcode {opcode_hex}")

    return microcode
