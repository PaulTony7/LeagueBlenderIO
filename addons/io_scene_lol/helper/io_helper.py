from __future__ import annotations
from typing import Any, NamedTuple, List, Optional, Tuple, IO
from struct import Struct
import math
from mathutils import Vector, Quaternion

class LoLVec2(NamedTuple):
    x: float = 0.0
    y: float = 0.0
    def to_blender(self) -> Vector:
        return Vector((self.x, self.y))

class LoLVec3(NamedTuple):
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    def to_blender(self) -> Vector:
        return Vector((self.x, -self.z, self.y))

class LoLVec4(NamedTuple):
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    w: float = 0.0
    def to_blender(self) -> Vector:
        return Vector((self.x, -self.z, self.y, self.w))

class LoLQuat(NamedTuple):
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    w: float = 0.0

    def to_blender(self) -> Quaternion:
        return Quaternion((self.w, self.x, -self.z, self.y))
    def normalize(self) -> LoLQuat:
        n = math.sqrt(self.w ** 2 + self.x ** 2  + self.y ** 2 + self.z ** 2)
        return LoLQuat(self.x / n, self.y / n, self.z / n, self.w / n)
    @staticmethod
    def from_blender(quat:Quaternion) -> LoLQuat:
        return LoLQuat(x = quat.x, y = quat.y, z = quat.z, w = quat.w)

class LoLColor(NamedTuple):
    r: float = 0.0
    g: float = 0.0
    b: float = 0.0
    a: float = 0.0
    def to_blender(self) -> Vector:
        return Vector(tuple(self))

class LoLBox(NamedTuple):
    start: LoLVec3
    end: LoLVec3

class LoLSphere(NamedTuple):
    center: LoLVec3
    radius: float

class LoLForm3D(NamedTuple):
    pos: LoLVec3
    scale: LoLVec3
    rot: LoLQuat

class LoLIO(NamedTuple):
    class ScopedOffset(NamedTuple):
        io_: IO
        old_offset_: int
        new_offset_: int

        def __enter__(self):
            self.io_.seek(self.new_offset_)
            return self

        def __exit__(self, exec_type, exec_value, exec_trace_back):
            self.io_.seek(self.old_offset_)

    io_: IO

    def tell(self) -> int:
        return self.io_.tell()

    def seek(self, off: int):
        self.io_.seek(off)

    def seek_push(self, off: int) -> ScopedOffset:
        return LoLIO.ScopedOffset(self.io_, self.tell(), off)

    def read_bytes(self, n: int) -> bytes:
        return self.io_.read(n)
    
    def write_bytes(self, v: bytes):
        self.io_.write(v)

    def read_struct(self, fmt: str) -> Any:
        struct = Struct(fmt)
        return struct.unpack(self.io_.read(struct.size))

    def write_struct(self, fmt: str, *args: Any):
        struct = Struct(fmt)
        self.io_.write(struct.pack(*args))

    def read_i8(self) -> int:
        return self.read_struct('< b')[0]

    def write_i8(self, v: int):
        self.write_struct('< b', v)

    def read_u8(self) -> int:
        return self.read_struct('< B')[0]

    def write_u8(self, v: int):
        self.write_struct('< B', v)

    def read_i16(self) -> int:
        return self.read_struct('< h')[0]
        
    def write_i16(self, v: int):
        self.write_struct('< h', v)

    def read_u16(self) -> int:
        return self.read_struct('< H')[0]

    def write_u16(self, v: int):
        self.write_struct('< H', v)

    def read_i32(self) -> int:
        return self.read_struct('< i')[0]

    def write_i32(self, v: int):
        self.write_struct('< i', v)        

    def read_u32(self) -> int:
        return self.read_struct('< I')[0]

    def write_u32(self, v: int):
        self.write_struct('< I', v)

    def read_i64(self) -> int:
        return self.read_struct('< q')[0]

    def write_i64(self, v: int):
        self.write_struct('< q', v)

    def read_u64(self) -> int:
        return self.read_struct('< Q')[0]

    def write_u64(self, v: int):
        self.write_struct('< Q', v)

    def read_f32(self) -> float:
        return self.read_struct('< f')[0]

    def write_f32(self, v: float):
        self.write_struct('< f', v)

    def read_f64(self) -> float:
        return self.read_struct('< d')[0]

    def write_f64(self, v: float):
        self.write_struct('< d', v)

    def read_fstr(self, n: int) -> str:
        return self.io_.read(n).split(b'\0')[0].decode('ascii')

    def write_fstr(self, n: int, v: str):
        data = v.encode('ascii')
        assert(len(data) < n)
        self.io_.write(data)
        self.io_.write(b'\0' * (n - len(data)))

    def read_zstr(self) -> str:
        buffer = []
        while c := self.io_.read(1)[0]:
            buffer.append(c)
        return bytes(buffer).decode('ascii')

    def write_zstr(self, v: str):
        data = v.encode('ascii')
        self.io_.write(data)
        self.io_.write(b'\0')

    def read_vec2(self) -> LoLVec2:
        x = self.read_f32()
        y = self.read_f32()
        return LoLVec2(x, y)

    def write_vec2(self, v: LoLVec2):
        self.write_f32(v.x)
        self.write_f32(v.y)

    def read_vec3(self) -> LoLVec3:
        x = self.read_f32()
        y = self.read_f32()
        z = self.read_f32()
        return LoLVec3(x, y, z)

    def write_vec3(self, v: LoLVec3):
        self.write_f32(v.x)
        self.write_f32(v.y)
        self.write_f32(v.z)

    def read_vec4(self) -> LoLVec4:
        x = self.read_f32()
        y = self.read_f32()
        z = self.read_f32()
        w = self.read_f32()
        return LoLVec4(x, y, z, w)

    def write_vec4(self, v: LoLVec4):
        self.write_f32(v.x)
        self.write_f32(v.y)
        self.write_f32(v.z)
        self.write_f32(v.w)

    def read_f32_pack16(self, factor: float, offset: float = 0) -> float:
        return offset + (self.read_u16() / 65535.0) * factor

    def read_vec3_pack48(self, min_vec, max_vec):
        x = self.read_f32_pack16(factor = max_vec.x - min_vec.x, offset = min_vec.x)
        y = self.read_f32_pack16(factor = max_vec.y - min_vec.y, offset = min_vec.y)
        z = self.read_f32_pack16(factor = max_vec.z - min_vec.z, offset = min_vec.z)
        return LoLVec3(x, y, z)

    def read_quat_quantized(self):
        convert = lambda v: (v / 32767.0) * math.sqrt(2.0) - 1.0 / math.sqrt(2.0)
        bits0 = self.read_u16()
        bits1 = self.read_u16()
        bits2 = self.read_u16()
        bits = bits0 | (bits1 << 16) | (bits2 << 32)
        max_index = (bits >> 45) & 0b11
        a = convert((bits >> 30) & 0x7FFF)
        b = convert((bits >> 15) & 0x7FFF)
        c = convert(bits & 0x7FFF)
        d = math.sqrt(max(0.0, 1.0 - (a * a + b * b + c * c)))
        if max_index == 0:
            return LoLQuat(d, a, b, c).normalize()
        elif max_index == 1:
            return LoLQuat(a, d, b, c).normalize()
        elif max_index == 2:
            return LoLQuat(a, b, d, c).normalize()
        else:
            return LoLQuat(a, b, c, d).normalize()

    def read_quat(self) -> LoLQuat:
        x = self.read_f32()
        y = self.read_f32()
        z = self.read_f32()
        w = self.read_f32()
        return LoLQuat(x, y, z, w)

    def write_quat(self, v: LoLQuat):
        self.write_f32(v.x)
        self.write_f32(v.y)
        self.write_f32(v.z)
        self.write_f32(v.w)

    def read_color(self) -> LoLColor:
        r = self.read_u8() / 255.0
        g = self.read_u8() / 255.0
        b = self.read_u8() / 255.0
        a = self.read_u8() / 255.0
        return LoLColor(r, g, b, a)

    def write_color(self, v: LoLColor):
        self.write_u8(int(v.r * 255.0))
        self.write_u8(int(v.g * 255.0))
        self.write_u8(int(v.b * 255.0))
        self.write_u8(int(v.a * 255.0))

    def read_box(self) -> LoLBox:
        start = self.read_vec3()
        end = self.read_vec3()
        return LoLBox(start, end)

    def write_box(self, v: LoLBox):
        self.write_vec3(v.start)
        self.write_vec3(v.end)

    def read_sphere(self) -> LoLSphere:
        center = self.read_vec3()
        radius = self.read_f32()
        return LoLSphere(center, radius)

    def write_sphere(self, v: LoLSphere):
        self.write_vec3(v.center)
        self.write_f32(v.radius)

    def read_form3d(self) -> LoLForm3D:
        pos = self.read_vec3()
        scale = self.read_vec3()
        rot = self.read_quat()
        return LoLForm3D(pos, scale, rot)

    def write_form3d(self, v: LoLForm3D):
        self.write_vec3(v.pos)
        self.write_vec3(v.scale)
        self.write_quat(v.rot)

    def read_ptr(self, from_offset: Optional[int] = None) -> int:
        if from_offset == None:
            from_offset = self.tell()
        ptr = self.read_i32()
        if ptr == 0 or ptr == -1:
            return 0
        return ptr + from_offset

    def write_ptr(self, ptr: int, from_offset: Optional[int] = None):
        if from_offset == None:
            from_offset = self.tell()
        if ptr == 0 or ptr == -1:
            self.write_i32(0)
            return
        self.write_i32(ptr - from_offset)

    def read_align(self, n: int) -> bytes:
        rem = self.tell() % n
        if not rem:
            return b''
        return self.io_.read(n - rem)

    def write_align(self, n: int):
        rem = self.tell() % n
        if not rem:
            return
        self.io_.write(b'\0' * (n - rem))

def lol_elf_hash(v: str) -> int:
    state = 0
    for b in v.encode('ascii').lower():
        state <<= 4
        state += b 
        high = state & 0xF0000000
        if high:
            state ^= high >> 24
        state &= ~high
    return state
