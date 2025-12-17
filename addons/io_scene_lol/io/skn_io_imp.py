from __future__ import annotations

import math
from typing import NamedTuple, List, Optional, Tuple, IO

from ..helper.io_helper import *

class LoLSKN(NamedTuple):
    class SubMesh(NamedTuple):
        name: str
        vtx_start: int
        vtx_count: int
        idx_start: int
        idx_count: int

    class Vertex(NamedTuple):
        position: LoLVec3
        blend_indices: Tuple[int, int, int, int]
        blend_weights: Tuple[float, float, float, float]
        normal: LoLVec3
        uv: LoLVec2
        color: Optional[LoLColor] = None
        
        def get_color(self) -> LoLColor:
            return self.color if self.color != None else LoLColor(0.0, 0.0, 0.0, 0.0)

    class Metadata(NamedTuple):
        bound_box: LoLBox
        bound_sphere: LoLSphere
        has_color: bool = False
        flags: int = 0

        # NOTE: flags seem to allways be == 0 so we don't care about them as much

        @staticmethod
        def create(vertices: List[LoLSKN.Vertex], flags: int = 0) -> LoLSKN.Metadata:
            sx = min(vtx.position.x for vtx in vertices)
            sy = min(vtx.position.y for vtx in vertices)
            sz = min(vtx.position.z for vtx in vertices)
            ex = max(vtx.position.x for vtx in vertices)
            ey = max(vtx.position.y for vtx in vertices)
            ez = max(vtx.position.z for vtx in vertices)
            meta_data = LoLSKN.Metadata(
                bound_box = LoLBox(
                    start = LoLVec3(x = sx, y = sy, z = sz),
                    end = LoLVec3(x = ex, y = ey, z = ez),
                ),
                bound_sphere = LoLSphere(
                    center = LoLVec3(x = (sx + ex) / 2.0, y = (sy + ey) / 2.0, z = (sz + ez) / 2.0),
                    radius = math.sqrt((sx - ex) ** 2 + (sy - ey) ** 2 + (sz - ez) ** 2) / 2.0,
                ),
                has_color = all(vtx.color != None for vtx in vertices),
                flags = flags
            )
            return meta_data
    
    meshes: List[SubMesh]
    indices: List[int]
    vertices: List[Vertex]
    pivot_point: Optional[LoLVec3] = None
    meta_data: Optional[Metadata] = None

    @staticmethod
    def read(io_src: IO) -> LoLSKN:
        rw = LoLIO(io_src)
        skn_magic = rw.read_u32()
        skn_version_minor = rw.read_u16()
        skn_version_major = rw.read_u16()

        assert(skn_magic == 0x00112233)
        assert(skn_version_minor in range(0, 5))
        assert(skn_version_major == 1)

        # Read (Sub)meshes
        meshes = []
        if skn_version_minor >= 1:
            mesh_count = rw.read_u32()
            for _ in range(0, mesh_count):
                mesh_name = rw.read_fstr(64)
                mesh_vtx_start = rw.read_i32()
                mesh_vtx_count = rw.read_i32()
                if mesh_vtx_start < 0 or mesh_vtx_count <= 0:
                    mesh_vtx_start = 0
                    mesh_vtx_count = 0
                mesh_idx_start = rw.read_i32()
                mesh_idx_count = rw.read_i32()
                if mesh_idx_start < 0 or mesh_idx_count <= 0:
                    mesh_idx_start = 0
                    mesh_idx_count = 0
                meshes.append(LoLSKN.SubMesh(
                    name = mesh_name,
                    vtx_start = mesh_vtx_start,
                    vtx_count = mesh_vtx_count,
                    idx_start = mesh_idx_start,
                    idx_count = mesh_idx_count,
                ))

        meta_data = None
        skn_idx_total = 0
        skn_vtx_total = 0

        # Read geometry data
        if skn_version_minor >= 4:
            skn_flags = rw.read_u32()
            skn_idx_total = rw.read_u32()
            skn_vtx_total = rw.read_u32()
            skn_vtx_size = rw.read_u32()
            skn_vtx_type = rw.read_u32()
            skn_bound_box = rw.read_box()
            skn_bound_sphere = rw.read_sphere()
            assert(skn_vtx_size in [52, 56])
            assert(skn_vtx_type in [0, 1])
            meta_data = LoLSKN.Metadata(
                bound_box = skn_bound_box,
                bound_sphere = skn_bound_sphere,
                has_color = skn_vtx_type != 0,
                flags = skn_flags,
            )
        else:
            skn_idx_total = rw.read_u32()
            skn_vtx_total = rw.read_u32()

        indices = []
        for _ in range(0, skn_idx_total):
            idx = rw.read_u16()
            indices.append(idx)
        
        vertices = []
        for _ in range(0, skn_vtx_total):
            vtx_position = rw.read_vec3()
            vtx_blend_indices = (rw.read_u8(), rw.read_u8(), rw.read_u8(), rw.read_u8(),)
            vtx_blend_weights = (rw.read_f32(), rw.read_f32(), rw.read_f32(), rw.read_f32(),)
            vtx_normal = rw.read_vec3()
            vtx_uv = rw.read_vec2()
            vtx_color = None
            if meta_data != None and meta_data.has_color:
                vtx_color = rw.read_color()
            vtx = LoLSKN.Vertex(
                position = vtx_position,
                blend_indices = vtx_blend_indices,
                blend_weights = vtx_blend_weights,
                normal = vtx_normal,
                uv = vtx_uv,
                color = vtx_color,
            )
            vertices.append(vtx)

        pivot_point = None
        if skn_version_minor >= 2:
            pivot_point = rw.read_vec3()

        skn = LoLSKN(
            meshes = meshes,
            indices = indices,
            vertices = vertices,
            pivot_point = pivot_point,
            meta_data = meta_data,
        )

        return skn

    def write(self, io_dst: IO, request_version = None):
        rw = LoLIO(io_dst)

        skn_magic = 0x00112233
        skn_version_minor = 0
        skn_version_major = 1

        # If there is no requested version we auto detect version with least requirements
        if request_version == None:
            skn_version_minor = 0
            if len(self.meshes) > 0:
                skn_version_minor = 1
            if self.pivot_point != None:
                skn_version_minor = 2
            if self.meta_data != None:
                skn_version_minor = 4
        else:
            assert (request_version in range(0, 5))
            skn_version_minor = request_version

        rw.write_u32(skn_magic)
        rw.write_u16(skn_version_minor)
        rw.write_u16(skn_version_major)

        if skn_version_minor >= 1:
            rw.write_u32(len(self.meshes))
            for mesh in self.meshes:
                rw.write_fstr(64, mesh.name)
                rw.write_i32(mesh.vtx_start)
                rw.write_i32(mesh.vtx_count)
                rw.write_i32(mesh.idx_start)
                rw.write_i32(mesh.idx_count)

        if skn_version_minor >= 4:
            meta_data = self.get_meta_data()
            rw.write_u32(meta_data.flags) # flags
            rw.write_u32(len(self.indices))
            rw.write_u32(len(self.vertices))
            rw.write_u32(56 if meta_data.has_color else 52)
            rw.write_u32(1 if meta_data.has_color else 0)
            rw.write_box(meta_data.bound_box)
            rw.write_sphere(meta_data.bound_sphere)
        else:
            rw.write_u32(len(self.indices))
            rw.write_u32(len(self.vertices))

        for idx in self.indices:
            rw.write_u16(idx)

        for vtx in self.vertices:
            rw.write_vec3(vtx.position)
            for i in range(0, 4):
                rw.write_u8(vtx.blend_indices[i])
            for i in range(0, 4):
                rw.write_f32(vtx.blend_weights[i])
            rw.write_vec3(vtx.normal)
            rw.write_vec2(vtx.uv)
            if self.vtx_type != 0:
                rw.write_color(vtx.get_color())

        if skn_version_minor >= 2:
            rw.write_vec3(self.get_pivot_point())

    def get_pivot_point(self) -> LoLVec3:
        if self.pivot_point != None:
            return self.pivot_point
        return LoLVec3(0.0, 0.0, 0.0)

    def get_meta_data(self) -> Metadata:
        if self.meta_data != None:
            return self.meta_data
        return LoLSKN.Metadata.create(self.vertices)
