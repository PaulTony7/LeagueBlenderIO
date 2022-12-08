import struct

def readVector3(file):
    x, y, z = struct.unpack('<fff', file.read(12))
    return (x, y, z)
def readVector2(file):
    return struct.unpack('<ff', file.read(8))
def readInt(file):
    return int.from_bytes(file.read(4), 'little')
def readShort(file):
    return struct.unpack('<H', file.read(2))[0]
def readFloat(file):
    return struct.unpack('<f', file.read(4))[0]
def readQuaternion(file):
    x, y, z, w = struct.unpack('<ffff', file.read(16))
    return (x, y, z, w)
def readColor(file):
    #TODO: implement rgbaU8
    return readInt(file)
def readString(file):
    returnString = b''
    while True:
        c = file.read(1)
        if c == b'\x00':
            break

        if not c:
            print('EOF')
            break
        
        returnString += c
    return returnString.decode('utf-8')