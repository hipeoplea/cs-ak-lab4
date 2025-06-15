from process.microcode_generator import generate_microcode_for_command


class MicrocodeMemory:
    def __init__(self):
        # Словарь: адрес -> Microcommand
        self.memory = {}

    def load_microcode(self):
        addr = 0
        for opcode in [
            '00001', '00010', '00011', '00100', '00101',
            '00110', '00111', '01000', '01001',
            '01010', '01011',
            '01101', '01110',
            '01111'
        ]:
            microcode_for_cmd = generate_microcode_for_command(opcode, start_addr=addr)
            self.memory.update(microcode_for_cmd)
            addr += len(microcode_for_cmd)

    def get_microcommand(self, addr):
        return self.memory.get(addr, None)

    def get_memory(self):
        return self.memory

memory = MicrocodeMemory()
memory.load_microcode()
print(memory.get_memory())

