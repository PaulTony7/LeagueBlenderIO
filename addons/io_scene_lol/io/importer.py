
import mathutils
import bpy;
from os.path import isfile, splitext, basename
from .skn_io_imp import LoLSKN
from .skl_io_imp import LoLSKL
# from .anm_io_imp import LoLANM

class ImportError(RuntimeError):
    pass

#TODO: rewrite to another file 
class sknImporter():
    """SKN Importer class."""
    #TODO: separate to seperate submeshes

    def __init__(self, filename):
        """Initialization."""
        self.filename = filename

    def read(self):
        """Read file."""
        if not isfile(self.filename):
            raise ImportError('Please select a file')

        print('loading', self.filename)
        # Load Mesh
        with open(self.filename, 'rb') as file:
            skn = LoLSKN.read(file)

        skl_file = splitext(self.filename)[0]+'.skl'
        print(splitext(self.filename)[0]+'.skl')
        if isfile(skl_file):
            # Load Skeleton
            mesh_only = False
            with open(splitext(self.filename)[0]+'.skl', 'rb') as file2:
                skl = LoLSKL.read(file2)
        else:
            mesh_only = True
            print('Couldn find', splitext(self.filename)[0]+'.skl')
        
        # TODO: change to multiple not hardcoded animation files
        # TEST READ ANIMATION
        # print('Reading animation file')
        # with open('C:\\Users\\kokot.p\\Desktop\\LeagueBlenderIO-main\\res\\aatrox_attack1.anm', 'rb') as file3:
        #     anm = LoLANM.read(file3)
        #     print(anm.asset_name)
        
        # TODO: Refactor to a different class
        # Create mesh
        # Use correct blender axis order
        vertices = [(t.position.x, -t.position.z, t.position.y) for t in skn.vertices]
        edges = []
        faces = []
        for i in range(int(len(skn.indices) / 3)):
            # Use correct blender face orientation 
            faces.append((skn.indices[i*3+1],skn.indices[i*3],skn.indices[i*3+2]))
        name = basename(splitext(self.filename)[0])
        new_mesh = bpy.data.meshes.new(name)
        new_mesh.from_pydata(vertices, edges, faces)
        # Set normals
        normalList = []
        for i in range(len(skn.vertices)):
            vertex = skn.vertices[i]
            normalList.append(mathutils.Vector(tuple(vertex.normal)))
        new_mesh.normals_split_custom_set_from_vertices(normalList)
        # new_mesh.shade_smooth()
        # new_mesh.corner_normals
        # new_mesh.update()
        new_mesh.shade_flat()
        
        # Create object
        new_object = bpy.data.objects.new(name, new_mesh)

        # Set UV's
        # new_object.data.uv_layers.new(name='lolUVTexture')
        # uv_layer = new_object.data.uv_layers[-1].data
        # uv_set = []
        # for k, loop in enumerate(new_object.data.loops):
        #     v = loop.vertex_index
        #     uv_set.append(skn.vertices[v].uv[0])
        #     # flipped V
        #     uv_set.append(1 - skn.vertices[v].uv[1])
        # uv_layer.foreach_set('uv', uv_set)
        #
        # # Create materials and assign faces to materials
        # for i in range(len(skn.meshes)):
        #     new_material = bpy.data.materials.new(skn.meshes[i].name)
        #     new_material.use_nodes = True
        #     bsdf = new_material.node_tree.nodes['Principled BSDF']
        #     textureImage = new_material.node_tree.nodes.new('ShaderNodeTexImage')
        #     new_material.node_tree.links.new(bsdf.inputs['Base Color'], textureImage.outputs['Color'])
        #
        #     new_mesh.materials.append(new_material)
        #     for j in range(len(faces)):
        #         if faces[j][0] >= skn.meshes[i].vtx_start and faces[j][0] < skn.meshes[i].vtx_start + skn.meshes[i].vtx_count:
        #             new_object.data.polygons[j].material_index = i
        #
        # if not mesh_only:
        #     # create vertex groups
        #     for i in range(len(skl.influences)):
        #         new_object.vertex_groups.new(name=skl.joints[skl.influences[i]].name)
        #
        #     # bone influence
        #     for i in range(len(skn.vertices)):
        #         vertex = skn.vertices[i]
        #         new_object.vertex_groups[vertex.blend_indices[0]].add([i], vertex.blend_weights[0], 'ADD')
        #         new_object.vertex_groups[vertex.blend_indices[1]].add([i], vertex.blend_weights[1], 'ADD')
        #         new_object.vertex_groups[vertex.blend_indices[2]].add([i], vertex.blend_weights[2], 'ADD')
        #         new_object.vertex_groups[vertex.blend_indices[3]].add([i], vertex.blend_weights[3], 'ADD')
        #
        # # make collection
        new_collection = bpy.data.collections.new('new_collection')
        bpy.context.scene.collection.children.link(new_collection)
        # add object to scene collection
        new_collection.objects.link(new_object)
        #
        # # Create Armature
        #
        # bpy.ops.object.armature_add(location=(0, 0, 0), enter_editmode=True)
        # obj = bpy.context.active_object
        # armature = obj.data
        #
        # # calc bone matrices
        # editbone_arm_mats = []
        # for i in range(len(skl.joints)):
        #     bone = skl.joints[i]
        #     if bone.parent_idx > -1:
        #         parent_editbone_mat = editbone_arm_mats[bone.parent_idx]
        #     else:
        #         parent_editbone_mat = mathutils.Matrix.Identity(4)
        #
        #     t, r = bone.local_transform.pos.to_blender(), bone.local_transform.rot.to_blender()
        #     local_to_parent = mathutils.Matrix.Translation(t) @ mathutils.Quaternion(r).to_matrix().to_4x4()
        #     editbone_arm_mats.append(parent_editbone_mat @ local_to_parent)
        #
        # for i in range(len(skl.joints)):
        #     bone = skl.joints[i]
        #     editbone = armature.edit_bones.new(bone.name)
        #     editbone.use_connect = False
        #
        #     arma_mat = editbone_arm_mats[i]
        #     editbone.head = arma_mat @ mathutils.Vector((0,0,0))
        #     editbone.tail = arma_mat @ mathutils.Vector((0,1,0))
        #     # editbone.length = bone.radius
        #     editbone.align_roll(arma_mat @ mathutils.Vector((0, 0, 1)) - editbone.head)
        #
        # # set all bone parents
        # for i in range(len(skl.joints)):
        #     bone = skl.joints[i]
        #     if bone.parent_idx >= 0:
        #         parent_bone = skl.joints[bone.parent_idx]
        #         editbone = armature.edit_bones[bone.name]
        #         parent_editbone = armature.edit_bones[parent_bone.name]
        #         editbone.parent = parent_editbone
        #
        # bpy.ops.object.mode_set(mode='OBJECT')
