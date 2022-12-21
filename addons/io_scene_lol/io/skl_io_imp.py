from __future__ import annotations
from ..helper.io_helper import *
from typing import NamedTuple, List, IO
# import mathutils
        

class LoLSKL(NamedTuple):
    class Joint(NamedTuple):
        parent_idx: int
        name_hash: int
        radius: float
        local_transform: LoLForm3D
        inv_root_transform: LoLForm3D
        name: str = ""
        flags: int = 0

    joints: List[Joint]
    influences: List[int]
    name: str = ""
    asset_name: str = ""
    flags: int = 0    

    # NOTE: both SKL and Joint flags seems to allways be == 0

    @staticmethod
    def read(io_src: IO, full_read = False) -> LoLSKL:
        rw = LoLIO(io_src)

        start = rw.tell()

        skl_size = rw.read_u32()
        skl_magic = rw.read_u32()
        skl_version = rw.read_u32()

        assert(skl_magic == 0x22FD4FC3)
        assert(skl_version == 0)

        skl_flags = rw.read_u16()
        skl_num_joints = rw.read_u16()
        skl_num_influences = rw.read_u32()
        skl_off_joints = rw.read_ptr(start)
        skl_off_joints_by_hash = rw.read_ptr(start)
        skl_off_influences = rw.read_ptr(start)
        skl_off_name = rw.read_ptr(start)
        skl_off_asset_name = rw.read_ptr(start)
        skl_off_joint_names = rw.read_ptr(start)
        skl_extra = (rw.read_u32(), rw.read_u32(), rw.read_u32(), rw.read_u32(), rw.read_u32())

        name = ""
        if skl_off_name:
            with rw.seek_push(skl_off_name):
                name = rw.read_zstr()

        asset_name = ""
        if skl_off_asset_name:
            with rw.seek_push(skl_off_asset_name):
                asset_name = rw.read_zstr()

        joints = []
        if skl_num_joints and skl_off_joints:
            with rw.seek_push(skl_off_joints):
                for i in range(0, skl_num_joints):
                    joint_flags = rw.read_u16()
                    joint_idx = rw.read_i16()
                    assert(i == joint_idx)
                    joint_parent_idx = rw.read_i16()
                    joint_pad = rw.read_u16()
                    joint_name_hash = rw.read_u32()
                    joint_radius = rw.read_f32()
                    joint_local_transform = rw.read_form3d()
                    joint_inv_root_transform = rw.read_form3d()
                    joint_off_name = rw.read_ptr(None)
                    joint_name = ""
                    if joint_off_name:
                        with rw.seek_push(joint_off_name):
                            joint_name = rw.read_zstr()
                    joint = LoLSKL.Joint(
                        flags = joint_flags,
                        parent_idx = joint_parent_idx,
                        name_hash = joint_name_hash,
                        radius = joint_radius,
                        local_transform = joint_local_transform,
                        inv_root_transform = joint_inv_root_transform,
                        name = joint_name,
                    )
                    joints.append(joint)

        # Joint name vector
        if skl_num_joints and skl_off_joint_names and full_read:
            with rw.seek_push(skl_off_joint_names):
                for _ in range(0, skl_num_joints):
                    joint_name = rw.read_zstr()

        # Joint name_hash -> index binary search map
        if skl_num_joints and skl_off_joints_by_hash and full_read:
            with rw.seek_push(skl_off_joints_by_hash):
                for _ in range(0, skl_num_joints):
                    joint_idx = rw.write_i16()
                    joint_pad = rw.read_u16()
                    joint_name_hash = rw.read_u32()

        influences = []
        if skl_num_influences and skl_off_influences:
            with rw.seek_push(skl_off_influences):
                for _ in range(0, skl_num_influences):
                    joint_idx = rw.read_i16()
                    influences.append(joint_idx)

        skl = LoLSKL(
            joints = joints,
            influences = influences,
            name = name,
            asset_name = asset_name,
            flags = skl_flags,
        )
        return skl

    def write(self, io_dst: IO):
        rw = LoLIO(io_dst)

        skl_size = 0
        skl_magic = 0x22FD4FC3
        skl_version = 0
        skl_flags = self.flags
        skl_num_joints = len(self.joints)
        skl_num_influences = len(self.influences)
        skl_off_joints = 0
        skl_off_joints_by_hash = 0
        skl_off_influences = 0
        skl_off_name = 0
        skl_off_asset_name = 0
        skl_off_joint_names = 0
        skl_extra = (0, 0, 0, 0, 0,)

        # We write the header latter
        start = rw.tell()

        with rw.seek_push(start + 64):
            skl_off_name = rw.tell()
            rw.write_zstr(self.name)
            rw.write_align(4)

            skl_off_asset_name = rw.tell()
            rw.write_zstr(self.asset_name)
            rw.write_align(4)
            joint_off_name_by_idx = []

            if skl_num_joints:
                skl_off_joint_names = rw.tell()
                for joint in self.joints:
                    joint_off_name = rw.tell()
                    rw.write_zstr(joint.name)
                    rw.write_align(4)
                    joint_off_name_by_idx.append(joint_off_name)

            if skl_num_joints:
                skl_off_joints = rw.tell()
                for idx, joint in enumerate(self.joints):
                    rw.write_u16(joint.flags)
                    rw.write_i16(idx)
                    rw.write_i16(joint.parent_idx)
                    rw.write_u16(0) # PAD
                    rw.write_u32(joint.name_hash)
                    rw.write_f32(joint.radius)
                    rw.write_form3d(joint.local_transform)
                    rw.write_form3d(joint.inv_root_transform)
                    rw.write_ptr(joint_off_name_by_idx[idx], None)

            if skl_num_joints:
                skl_off_joints_by_hash = rw.tell()
                for idx, joint in sorted(enumerate(self.joints), key = lambda ij: ij[1].name_hash):
                    rw.write_i16(idx)
                    rw.write_u16(0) # PAD
                    rw.write_u32(joint.name_hash)
                
            if skl_num_influences:
                skl_off_influences = rw.tell()
                for idx in self.influences:
                    rw.write_i16(idx)
                rw.write_align(4)
            
            skl_size = rw.tell() - start

        rw.write_u32(skl_size) 
        rw.write_u32(skl_magic)
        rw.write_u32(skl_version)
        rw.write_u16(skl_flags)
        rw.write_u16(skl_num_joints)
        rw.write_u32(skl_num_influences)
        rw.write_ptr(skl_off_joints, start)
        rw.write_ptr(skl_off_joints_by_hash, start)
        rw.write_ptr(skl_off_influences, start)
        rw.write_ptr(skl_off_name, start)
        rw.write_ptr(skl_off_asset_name, start)
        rw.write_ptr(skl_off_joint_names, start)
        for extra in skl_extra:
            rw.write_u32(extra)
