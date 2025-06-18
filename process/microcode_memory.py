def encode_u(halted=0, acc_l=0, dal=0, mem=0, sp_l=0, dr=0, out=0, ip_l=0,
             adr_sel=0, io_sel=0, cla=0, cld=0,
             ip_sel=0, alu=0, cond=0, next_addr=0):
    return ((halted  & 1) << 26) | \
           ((acc_l   & 1) << 25) | \
           ((dal     & 1) << 24) | \
           ((mem     & 1) << 23) | \
           ((sp_l    & 1) << 22) | \
           ((dr      & 1) << 21) | \
           ((out     & 1) << 20) | \
           ((ip_l    & 1) << 19) | \
           ((adr_sel & 1) << 18) | \
           ((io_sel  & 1) << 17) | \
           ((cla     & 0b11) << 15) | \
           ((cld     & 0b11) << 13) | \
           ((ip_sel  & 0b11) << 11) | \
           ((alu     & 0b111) << 8) | \
           ((cond    & 0b111) << 6) | \
           (next_addr & 0x3F)

ROM = [0]*64

# FETCH
ROM[0] = encode_u(ip_l=1)

# LOAD
ROM[1] = encode_u(adr_sel=1, dal=1, dr=1)
ROM[2] = encode_u(cld=1, io_sel=0, acc_l=1)
ROM[3] = encode_u(cld=0b10, alu=0b100, ip_l=1)
ROM[4] = encode_u(cond=1, next_addr=0)

# STORE
ROM[5] = encode_u(adr_sel=1, dal=1, mem=1)
ROM[6] = encode_u(cld=0b10, alu=0b100, ip_l=1)
ROM[7] = encode_u(cond=1, next_addr=0)

# CALL
ROM[8]  = encode_u(cla=0, cld=0b10, alu=0, acc_l=1)
ROM[9]  = encode_u(cla=0b10, cld=0, alu=0b101, sp_l=1)
ROM[10] = encode_u(adr_sel=0, dal=1, mem=1)
ROM[11] = encode_u(cond=1, next_addr=42)

# RET
ROM[12] = encode_u(cla=0b10, cld=0, alu=0)
ROM[13] = encode_u(adr_sel=0, dal=1, dr=1)
ROM[14] = encode_u(cla=0, cld=0b01, alu=0, ip_l=1)
ROM[15] = encode_u(cla=0b10, cld=0, alu=0b100, sp_l=1)
ROM[16] = encode_u(cond=1, next_addr=0)

# Arithmetic
ROM[17] = encode_u(adr_sel=1, dal=1, dr=1)
ROM[18] = encode_u(cla=1, cld=1, alu=0, acc_l=1)
ROM[19] = encode_u(cld=0b10, alu=0b100, ip_l=1)
ROM[20] = encode_u(cond=1, next_addr=0)

ROM[21] = encode_u(adr_sel=1, dal=1, dr=1)
ROM[22] = encode_u(cla=1, cld=1, alu=0b001, acc_l=1)
ROM[23] = encode_u(cld=0b10, alu=0b100, ip_l=1)
ROM[24] = encode_u(cond=1, next_addr=0)

ROM[25] = encode_u(adr_sel=1, dal=1, dr=1)
ROM[26] = encode_u(cla=1, cld=1, alu=0b010, acc_l=1)
ROM[27] = encode_u(cld=0b10, alu=0b100, ip_l=1)
ROM[28] = encode_u(cond=1, next_addr=0)

ROM[29] = encode_u(adr_sel=1, dal=1, dr=1)
ROM[30] = encode_u(cla=1, cld=1, alu=0b011, acc_l=1)
ROM[31] = encode_u(cld=0b10, alu=0b100, ip_l=1)
ROM[32] = encode_u(cond=1, next_addr=0)

# PUSH
ROM[33] = encode_u(cla=0b10, cld=0, alu=0b101, sp_l=1)
ROM[34] = encode_u(adr_sel=0, dal=1, mem=1)
ROM[35] = encode_u(adr_sel=0, cld=0b10, ip_l=1)
ROM[36] = encode_u(cond=1, next_addr=0)

# POP
ROM[37] = encode_u(adr_sel=0, dal=1, dr=1)
ROM[38] = encode_u(cla=0, cld=0b01, alu=0, acc_l=1, ip_l=1)
ROM[39] = encode_u(cld=0b01, alu=0b100, sp_l=1)
ROM[40] = encode_u(cond=1, next_addr=0)

# IN / OUT
ROM[41] = encode_u(io_sel=1, cld=0b10, alu=0b100, acc_l=1, ip_l=1, cond=1, next_addr=0)
ROM[42] = encode_u(out=1, cld=0b10, alu=0b100, ip_l=1, cond=1, next_addr=0)

# JUMP base
ROM[43] = encode_u(cla=0, cld=0b10, alu=0, acc_l=1)
ROM[44] = encode_u(ip_sel=0b01, ip_l=1)
ROM[45] = encode_u(cla=0b01, cld=0b10, alu=0, ip_l=1)
ROM[46] = encode_u(cond=0b001, next_addr=0)

# Conditional jumps
ROM[47] = encode_u(cond=0b010, next_addr=43)  # JZ
ROM[48] = encode_u(cond=0b001, next_addr=0)
ROM[49] = encode_u(cond=0b100, next_addr=43)  # JNZ
ROM[50] = encode_u(cond=0b001, next_addr=0)
ROM[51] = encode_u(cond=0b011, next_addr=43)  # JLT
ROM[52] = encode_u(cond=0b001, next_addr=0)
ROM[53] = encode_u(cond=0b101, next_addr=43)  # JGT
ROM[54] = encode_u(cond=0b001, next_addr=0)

# HALT
ROM[55] = encode_u(halted=1)

OPCODE_TO_UADDR = [0] * 32

OPCODE_TO_UADDR[0x00] = 55   # HALT      (было 54)
OPCODE_TO_UADDR[0x02] = 1    # LOAD
OPCODE_TO_UADDR[0x03] = 5    # STORE
OPCODE_TO_UADDR[0x04] = 33   # PUSH      (было 32)
OPCODE_TO_UADDR[0x05] = 37   # POP       (было 36)
OPCODE_TO_UADDR[0x06] = 17   # ADD
OPCODE_TO_UADDR[0x07] = 21   # SUB
OPCODE_TO_UADDR[0x08] = 25   # MUL
OPCODE_TO_UADDR[0x09] = 29   # DIV
OPCODE_TO_UADDR[0x0A] = 8    # CALL
OPCODE_TO_UADDR[0x0B] = 12   # RET
OPCODE_TO_UADDR[0x0D] = 41   # IN        (было 40)
OPCODE_TO_UADDR[0x0E] = 42   # OUT       (было 41)
OPCODE_TO_UADDR[0x0F] = 43   # JMP       (было 42)
OPCODE_TO_UADDR[0x10] = 47   # JZ        (было 46)
OPCODE_TO_UADDR[0x11] = 49   # JNZ       (было 48)
OPCODE_TO_UADDR[0x12] = 51   # JLT       (было 50)
OPCODE_TO_UADDR[0x13] = 53   # JGT       (было 52)