# This file is based on broker.py from gunbound-server-link
# New comments should start with your username and : (Example: Mango: Here is my comment)

# GunBound Thor's Hammer packet layout:
# Packet Data: 0c 00 eb cb 12 13 30 00 ff ff ff ff
# Index:       00 01 02 03 04 05 06 07 08 09 0a 0b
#
# 00, 01 = Packet size, 00 = LSB, 01 = MSB
# 02, 03 = Packet sequence
# 04, 05 = Packet command
# 06 onwards = Packet parameters

# convert a bytes-like input into a hex-string
def bytes_to_hex(input_bytes):
    return "".join("{:02X}".format(b) for b in input_bytes)


# convert an integer into a series of little-endian bytes
# broker is strange where data is sometimes presented in big-endian
def int_to_bytes(input_integer, size, big_endian=False):
    output_bytes = bytearray()
    if big_endian:
        for i in range(size):
            output_bytes.insert(0, input_integer & 0xff)
            input_integer = input_integer >> 8
    else:
        for i in range(size):
            output_bytes.append(input_integer & 0xff)
            input_integer = input_integer >> 8
    return output_bytes


# GunBound packet sequence, generated from sum of packet lengths
# Normally the overall length is stored/incremented per socket, but the broker only uses this once (hence unnecessary)
# Taken from function at 0x40B760 in GunBoundServ2.exe (SHA-1: b8fce1f100ef788d8469ca0797022b62f870b79b)
#
# ECX: packet length
# 0040B799  IMUL CX,CX,43FD ; Multiply packet length with 43FD (int16)
# 0040B79E  ...
# 0040B7A1  ...
# 0040B7A9  ...
# 0040B7AB  ...
# 0040B7B2  ADD ECX,FFFFAC03 ; Inverted sign of FFFFAC03 equivalent would be SUB 53FD (implemented below)
#
# The client checks this output value. For the server to verify the client's packet sequence, subtract 0x613D instead
def get_sequence(sum_packet_length):
    return (((sum_packet_length * 0x43FD) & 0xFFFF) - 0x53FD) & 0xFFFF
