from translation.instrucrions import *  # содержит OPCODE_TABLE

def encode_u(halted=0, dal=0, mem=0, sp_l=0, dr=0, out=0, ip_l=0,
             adr_sel=0, io_sel=0, cla=0, cld=0,
             ip_sel=0, alu=0, cond=0, next_addr=0):
    return ((halted & 1) << 25) | \
           ((dal    & 1) << 24) | \
           ((mem    & 1) << 23) | \
           ((sp_l   & 1) << 22) | \
           ((dr     & 1) << 21) | \
           ((out    & 1) << 20) | \
           ((ip_l   & 1) << 19) | \
           ((adr_sel & 1) << 18) | \
           ((io_sel  & 1) << 17) | \
           ((cla    & 0b11) << 15) | \
           ((cld    & 0b11) << 13) | \
           ((ip_sel & 0b11) << 11) | \
           ((alu    & 0b111) << 8) | \
           ((cond   & 0b11) << 6) | \
           (next_addr & 0x3F)

ROM = [0]*64

ROM[0] = encode_u(ip_l=1)


ROM[1] = encode_u(adr_sel=1, dal=1, dr=1)
ROM[2] = encode_u(cld=1, io_sel=0)
ROM[3] = encode_u(cld=0b10, alu=0b100, ip_l=1)
ROM[4] = encode_u(cond=1, next_addr=0)


ROM[5] = encode_u(adr_sel=1, dal=1, mem=1)
ROM[6] = encode_u(cld=0b10, alu=0b100, ip_l=1)
ROM[7] = encode_u(cond=1, next_addr=0)

#перемисать
ROM[8]  = encode_u(cla=0b10, cld=0, alu=0b101, sp_l=1)
ROM[9]  = encode_u(adr_sel=0, dal=1, mem=1, cla=0b10)
ROM[10] = encode_u(cld=0b10, alu=0b100, ip_l=1)
ROM[11] = encode_u(cond=1, next_addr=0)


ROM[12] = encode_u(cla=0b10, cld=0, sp_l=1, dal=1, dr=1)
ROM[13] = encode_u(cla=0, cld=1, alu=0b000, io_sel=0)
ROM[9]  = encode_u(cla=0b10, cld=0, alu=0b100, sp_l=1)
ROM[15] = encode_u(cld=0b10, alu=0b100, ip_l=1)
ROM[16] = encode_u(cond=1, next_addr=0)


ROM[17] = encode_u(adr_sel=1, dal=1, dr=1)
ROM[18] = encode_u(cla=1, cld=1, alu=0b000)
ROM[19] = encode_u(cld=0b10, alu=0b100, ip_l=1)
ROM[20] = encode_u(cond=1, next_addr=0)

ROM[21] = encode_u(adr_sel=1, dal=1, dr=1)
ROM[22] = encode_u(cla=1, cld=1, alu=0b001)
ROM[23] = encode_u(cld=0b10, alu=0b100, ip_l=1)
ROM[24] = encode_u(cond=1, next_addr=0)

ROM[25] = encode_u(adr_sel=1, dal=1, dr=1)
ROM[26] = encode_u(cla=1, cld=1, alu=0b010)
ROM[27] = encode_u(cld=0b10, alu=0b100, ip_l=1)
ROM[28] = encode_u(cond=1, next_addr=0)

ROM[29] = encode_u(adr_sel=1, dal=1, dr=1)
ROM[30] = encode_u(cla=1, cld=1, alu=0b011)
ROM[31] = encode_u(cld=0b10, alu=0b100, ip_l=1)
ROM[32] = encode_u(cond=1, next_addr=0)


ROM[32] = encode_u(cla=0b10, alu=0b100, sp_l=1, dal=1)
ROM[33] = encode_u(adr_sel=0, cld=0b10, mem=1)
ROM[34] = encode_u(adr_sel=0, cld=0b10, ip_l=1)
ROM[35] = encode_u(cond=1, next_addr=0)

ROM[36] = encode_u(adr_sel=0, dal=1, dr=1, cla=0b10)
ROM[37] = encode_u(cla=0, cld=0b01, alu=0, ip_l=1)
ROM[38] = encode_u(cld=0b01,  alu=0b100, sp_l=1)
ROM[39] = encode_u(cond=1, next_addr=0)

#in/ret
ROM[40] = encode_u(io_sel=1, cld=0b10, alu=0b100, ip_l=1, cond=1, next_addr=0)
ROM[41] = encode_u(out=1, cld=0b10, alu=0b100, ip_l=1, cond=1, next_addr=0)
#условия jump
ROM[42] = encode_u(ip_l=1, cond=1, next_addr=0, ip_sel=1)

