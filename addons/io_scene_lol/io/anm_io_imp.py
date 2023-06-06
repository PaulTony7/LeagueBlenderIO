from __future__ import annotations
from typing import NamedTuple, List, IO, Optional
from ..helper.io_helper import LoLIO, LoLForm3D, LoLQuat, LoLVec3
from ..helper.io_helper import lol_elf_hash as lol_bone_hash
import os

class LoLANM(NamedTuple):
    class Track(NamedTuple):
        frames: List[LoLForm3D]
        bone_hash: int

    tracks: List[Track]
    tick_duration: float
    asset_name: str = ""
    flags: int = 0

    @staticmethod
    def read(io_src: IO, full_read = False) -> LoLANM:
        rw = LoLIO(io_src)
        magic =  rw.read_bytes(8)
        version = rw.read_u32()

        def read_anmd_v3():
            anm_id = rw.read_u32()
            anm_num_tracks = rw.read_u32()
            anm_num_frames = rw.read_u32()
            anm_frame_frate = rw.read_i32()

            tracks = []
            for _ in range(0, anm_num_tracks):
                bone_name = rw.read_fstr(32)
                track_flags = rw.read_u32()
                bone_hash = lol_bone_hash(bone_name)
                track_frames = []
                for _ in range(0, anm_num_frames):
                    frame_rot = rw.read_quat()
                    frame_scale = LoLVec3(1.0, 1.0, 1.0)
                    frame_pos = rw.read_vec3()
                    frame = LoLForm3D(
                        pos = frame_pos,
                        scale = frame_scale,
                        rot = frame_rot,
                        )
                    track_frames.append(frame)
                track = LoLANM.Track(
                    frames = track_frames,
                    bone_hash = bone_hash,
                )
                tracks.append(track)
            if asset_name is '':
                asset_name = os.path.splitext(os.path.basename(io_src.name))[0]

            anm = LoLANM(
                tracks = tracks,
                tick_duration = 1.0 / anm_frame_frate,
            )
            return anm

        def read_anmd_v4():
            start = rw.tell()

            anm_size = rw.read_u32()
            anm_magic = rw.read_u32()
            anm_version = rw.read_u32()
            anm_flags = rw.read_u32()
            anm_num_tracks = rw.read_u32()
            anm_num_frames = rw.read_u32()
            anm_tick_duration = rw.read_f32()
            anm_off_tracks = rw.read_ptr(start)
            anm_off_asset_name = rw.read_ptr(start)
            anm_off_time = rw.read_ptr(start)
            anm_off_vectors = rw.read_ptr(start)
            anm_off_quats = rw.read_ptr(start)
            anm_off_frames = rw.read_ptr(start)
            anm_ext = (rw.read_u32(), rw.read_u32(), rw.read_u32(),)

            assert(not anm_off_tracks)
            assert(not anm_off_time)
            
            asset_name = ""
            if anm_off_asset_name:
                with rw.seek_push(anm_off_asset_name):
                    asset_name = rw.read_zstr()

            tracks = []
            if anm_num_tracks and anm_num_frames:
                anm_frames = []
                anm_num_vectors = 0
                anm_num_quats = 0

                with rw.seek_push(anm_off_frames):
                    for _ in range(0, anm_num_tracks * anm_num_frames):
                        frame_bone_hash = rw.read_u32()
                        frame_pos_idx = rw.read_u16()
                        frame_scale_idx = rw.read_u16()
                        frame_rot_idx = rw.read_u16()
                        frame_pad = rw.read_u16()
                        anm_num_vectors = max(anm_num_vectors, frame_pos_idx + 1, frame_scale_idx + 1)
                        anm_num_quats = max(anm_num_quats, frame_rot_idx + 1)
                        frame = (frame_bone_hash, frame_pos_idx, frame_scale_idx, frame_rot_idx,)
                        anm_frames.append(frame)

                anm_vectors = []
                with rw.seek_push(anm_off_vectors):
                    for _ in range(0, anm_num_vectors):
                        vec = rw.read_vec3()
                        anm_vectors.append(vec)
                
                anm_quats = []
                with rw.seek_push(anm_off_quats):
                    for _ in range(0, anm_num_quats):
                        quat = rw.read_quat()
                        anm_quats.append(quat)

                for track_idx in range(0, anm_num_tracks):
                    bone_hash = None
                    track_frames = []
                    for frame_idx in range(0, anm_num_frames):
                        idx = frame_idx * anm_num_tracks + track_idx
                        frame_bone_hash, frame_pos_idx, frame_scale_idx, frame_rot_idx in anm_frames[idx]
                        if bone_hash == None:
                            bone_hash = frame_bone_hash
                        else:
                            assert(bone_hash == frame_bone_hash)
                        frame_pos = anm_vectors[frame_pos_idx]
                        frame_scale = anm_vectors[frame_scale_idx]
                        frame_rot = anm_quats[frame_rot_idx]
                        frame = LoLForm3D(pos = frame_pos, scale = frame_scale, rot = frame_rot)
                        track_frames.append(frame)
                    track = LoLANM.Track(
                        frames = track_frames,
                        bone_hash = bone_hash,
                    )
                    tracks.append(track)
            if asset_name is '':
                asset_name = os.path.splitext(os.path.basename(io_src.name))[0]

            anm = LoLANM(
                tracks = tracks,
                tick_duration = anm_tick_duration,
                asset_name = asset_name,
                flags = anm_flags,
            )
            return anm

        def read_anmd_v5():
            start = rw.tell()

            anm_size = rw.read_u32()
            anm_magic = rw.read_u32()
            anm_version = rw.read_u32()
            anm_flags = rw.read_u32()
            anm_num_tracks = rw.read_u32()
            anm_num_frames = rw.read_u32()
            anm_tick_duration = rw.read_f32()
            anm_off_bone_hashes = rw.read_ptr(start)
            anm_off_asset_name = rw.read_ptr(start)
            anm_off_time = rw.read_ptr(start)
            anm_off_vectors = rw.read_ptr(start)
            anm_off_quats = rw.read_ptr(start)
            anm_off_frames = rw.read_ptr(start)
            anm_ext = (rw.read_u32(), rw.read_u32(), rw.read_u32(),)

            asset_name = ""
            if anm_off_asset_name:
                with rw.seek_push(anm_off_asset_name):
                    asset_name = rw.read_zstr()

            tracks = []
            if anm_num_tracks and anm_num_frames:
                anm_frames = []
                anm_num_vectors = 0
                anm_num_quats = 0

                with rw.seek_push(anm_off_frames):
                    for _ in range(0, anm_num_tracks * anm_num_frames):
                        frame_pos_idx = rw.read_u16()
                        frame_scale_idx = rw.read_u16()
                        frame_rot_idx = rw.read_u16()
                        anm_num_vectors = max(anm_num_vectors, frame_pos_idx + 1, frame_scale_idx + 1)
                        anm_num_quats = max(anm_num_quats, frame_rot_idx + 1)
                        frame = (frame_pos_idx, frame_scale_idx, frame_rot_idx,)
                        anm_frames.append(frame)

                anm_vectors = []
                with rw.seek_push(anm_off_vectors):
                    for _ in range(0, anm_num_vectors):
                        vec = rw.read_vec3()
                        anm_vectors.append(vec)
                
                anm_quats = []
                with rw.seek_push(anm_off_quats):
                    for _ in range(0, anm_num_quats):
                        quat = rw.read_quat_quantized()
                        anm_quats.append(quat)

                anm_bone_hashes = []
                with rw.seek_push(anm_off_bone_hashes):
                    for _ in range(0, anm_num_tracks):
                        bone_hash = rw.read_u32()
                        anm_bone_hashes.append(bone_hash)

                for track_idx in range(0, anm_num_tracks):
                    bone_hash = anm_bone_hashes[track_idx]
                    track_frames = []
                    for frame_idx in range(0, anm_num_frames):
                        idx = frame_idx * anm_num_tracks + track_idx
                        frame_pos_idx, frame_scale_idx, frame_rot_idx in anm_frames[idx]
                        frame_pos = anm_vectors[frame_pos_idx]
                        frame_scale = anm_vectors[frame_scale_idx]
                        frame_rot = anm_quats[frame_rot_idx]
                        frame = LoLForm3D(pos = frame_pos, scale = frame_scale, rot = frame_rot)
                        track_frames.append(frame)
                    track = LoLANM.Track(
                        frames = track_frames,
                        bone_hash = bone_hash,
                    )
                    tracks.append(track)
            if asset_name is '':
                asset_name = os.path.splitext(os.path.basename(io_src.name))[0]
            anm = LoLANM(
                tracks = tracks,
                tick_duration = anm_tick_duration,
                asset_name = asset_name,
                flags = anm_flags,
            )
            return anm

        def read_canm_v1():
            start = rw.tell()

            anm_size = rw.read_u32()
            anm_magic = rw.read_u32()
            anm_flags = rw.read_u32()
            anm_num_tracks = rw.read_u32()
            anm_num_frame_parts = rw.read_u32()
            anm_num_jump_caches = rw.read_u32()
            anm_total_duration = rw.read_f32()
            anm_fps = rw.read_f32()
            anm_rot_error_margin = rw.read_f32()
            anm_rot_discontinuity_threshold = rw.read_f32()
            anm_pos_error_margin = rw.read_f32()
            anm_pos_discontinuity_threshold = rw.read_f32()
            anm_scale_error_margin = rw.read_f32()
            anm_scale_discontinuity_threshold = rw.read_f32()
            anm_pos_min = rw.read_vec3()
            anm_pos_max = rw.read_vec3()
            anm_scale_min = rw.read_vec3()
            anm_scale_max = rw.read_vec3()
            anm_off_frames = rw.read_ptr(start)
            anm_off_jump_cache = rw.read_ptr(start)
            anm_off_bone_hashes = rw.read_ptr(start)

            tracks = []
            tracks_bone_hash = []
            if anm_num_tracks and anm_num_frame_parts:
                frame_parts = []

                # Read raw tracks frames
                with rw.seek_push(anm_off_frames):
                    for _ in range(0, anm_num_frame_parts):
                        time = rw.read_f32_pack16(anm_total_duration)
                        #time = rw.read_u16()
                        bits = rw.read_u16()
                        indx = bits & 0x3FFF
                        match bits & 0xC000:
                            case 0x0000:
                                v = rw.read_quat_quantized()
                                frame_parts.append((indx, time, "rot", v))
                            case 0x4000:
                                v = rw.read_vec3_pack48(anm_pos_min, anm_pos_max)
                                frame_parts.append((indx, time, "pos", v))
                            case 0x8000:
                                v = rw.read_vec3_pack48(anm_scale_min, anm_scale_max)
                                frame_parts.append((indx, time, "scale", v))
                            case _:
                                raise ValueError(f'Bad compressed anm frame type: 3')

                # Read bone hashes
                with rw.seek_push(anm_off_bone_hashes):
                    for _ in range(0, anm_num_tracks):
                        bone_hash = rw.read_u32()
                        tracks_bone_hash.append(bone_hash)

                if anm_off_jump_cache: # and full_read:
                    # Used to construct "HotFrames", we don't care about it
                    print("anm_total_duration", anm_total_duration)
                    print("anm_fps", anm_fps)
                    with rw.seek_push(anm_off_jump_cache):
                        for jump_indx in range(0, anm_num_jump_caches):
                            print("jump_indx", jump_indx)
                            for track_indx in range(0, anm_num_tracks):
                                print("\t", "track_indx", track_indx, hex(tracks_bone_hash[track_indx]))
                                indices = []
                                if anm_num_frame_parts <= 0x10000:
                                    for _ in range(0, 4 * 3):
                                        indices.append(rw.read_u16())
                                else:
                                    for _ in range(0, 4 * 3):
                                        indices.append(rw.read_u32())
                                cursor = max(indices)
                                t = [ frame_parts[i][1] for i in indices[4:8] ]
                                x = [ frame_parts[i][3].x for i in indices[4:8] ]
                                print("\t\t", f"t = {t!r}")
                                print("\t\t", f"x = {x!r}")

                                for i in indices[0:4]:
                                    assert(frame_parts[i][2] == "rot")
                                for i in indices[4:8]:
                                    assert(frame_parts[i][2] == "pos")
                                for i in indices[8:12]:
                                    assert(frame_parts[i][2] == "scale")

            anm = LoLANM(
                tracks = tracks,
                tick_duration = 1 / anm_fps,
                flags = anm_flags,
                asset_name = "",
            )
            return anm

        if magic == b'r3d2anmd' and version == 3:
            return read_anmd_v3()
        elif magic == b'r3d2anmd' and version == 4:
            return read_anmd_v4()
        elif magic == b'r3d2anmd' and version == 5:
            return read_anmd_v5()
        elif magic == b'r3d2canm' and version == 1:
            return read_canm_v1()
        else:
            raise ValueError(f'Unsupported LoLANM with magic = {repr(magic)} and version = {version:#08X}!')

