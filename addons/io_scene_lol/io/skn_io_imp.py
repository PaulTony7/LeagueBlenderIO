from os.path import isfile, splitext
import bpy
import struct
from ..helper.io_helper import *
from .skl_io_imp import SkeletonReader, SkeletonJoint
import mathutils

class SimpleSkinSubmesh():
    def __init__(self, file):
        self.name = file.read(64).decode('utf-8')
        self.startVertex = readInt(file)
        self.vertexCount = readInt(file)
        self.startIndex = readInt(file)
        self.indexCount = readInt(file)

class R3DBox():
    def __init__(self, file):
        self.Min = readVector3(file)
        self.Max = readVector3(file)

class R3DSphere():
    def __init__(self, file):
        self.Position = readVector3(file)
        self.Radius = readFloat(file)

class SimpleSkinVertex():
    def __init__(self, file, vertexType):
        self.Position = readVector3(file)
        self.BoneIndices = [file.read(1), file.read(1), file.read(1), file.read(1)]
        self.Weights = [readFloat(file), readFloat(file), readFloat(file), readFloat(file)]
        self.Normal = readVector3(file)
        self.UV = readVector2(file)
        
        if vertexType == 1:
            self.Color = readColor(file)

class SimpleSkinReader():
    def __init__(self, path):
        
        file = open(path, 'rb')
        if file.read(4) == bytes([0x33, 0x22, 0x11, 0x00]):
            self.major, self.minor = struct.unpack('<HH', file.read(4))
            self.submeshCount = readInt(file)

            self.submeshes = []
            for i in range(self.submeshCount):
                self.submeshes.append(SimpleSkinSubmesh(file))

            self.flags, self.indexCount, self.vertexCount, self.vertexSize, self.vertexType = struct.unpack('<IIIII', file.read(20))

            self.r3DBox = R3DBox(file)
            self.r3DSphere = R3DSphere(file)

            self.indices = []
            for _ in range(int(self.indexCount / 3)):
                self.indices.append(struct.unpack('<HHH', file.read(6)))

            self.vertices = []
            for i in range(self.vertexCount):
                self.vertices.append(SimpleSkinVertex(file, self.vertexType))

            print("File loaded")
        else:
            print('not simple skin file type!')


class ImportError(RuntimeError()):
    pass

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

        ssr = SimpleSkinReader(self.filename)
        print(splitext(self.filename)[0]+'.skl')
        skl = SkeletonReader(splitext(self.filename)[0]+'.skl')
        
        vertices = []
        for i in range(ssr.vertexCount):
            vertices.append(ssr.vertices[i].Position)
        edges = []
        faces = ssr.indices
        new_mesh = bpy.data.meshes.new('new_mesh')
        new_mesh.from_pydata(vertices, edges, faces)
        new_mesh.update()
        # make object from mesh
        new_object = bpy.data.objects.new('new_object', new_mesh)
        # make collection
        new_collection = bpy.data.collections.new('new_collection')
        bpy.context.scene.collection.children.link(new_collection)
        # add object to scene collection
        new_collection.objects.link(new_object)

        # Create Armature
        bpy.ops.object.armature_add(location=(0, 0, 0), enter_editmode=True)
        obj = bpy.context.active_object
        armature = obj.data

        bones = armature.edit_bones

        bones.remove(bones[0])

        for i in range(skl.jointCount):
            bone = skl.joints[i]
            boneParentID = bone.ParentID

            parentPos = mathutils.Vector([0,0,0])
            boneHead = bone.localTranslation
            
            newBone = armature.edit_bones.new(bone.Name)

            if boneParentID >= 0 and boneParentID < skl.jointCount:
                parentName = skl.joints[boneParentID].Name
                parentBone = armature.edit_bones[parentName]
                
                newBone.parent = parentBone
                parentRotation = skl.joints[boneParentID].localRotation
                boneHead.rotate(parentRotation)
                bone.localRotation = parentRotation * bone.localRotation

                parentPos = parentBone.head

            newBone.head = parentPos + boneHead

            if newBone.length == 0:
                newBone.tail[1] += .001 
                
        for bone in armature.edit_bones:
            if bone.length == 0:
                bone.length = 1
            if len(bone.children) == 0:
                bone.length = 10
                if bone.parent:
                    if bone.parent.tail != bone.head:
                        bone.tail = bone.head
                        bone.head = bone.parent.tail
                    else:
                        bone.align_orientation(bone.parent)
            else:

                numChildren = len(bone.children)
                pos = mathutils.Vector((0, 0, 0))
                for child in bone.children:
                    if child.name.isupper() or child.name.lower().count('buffbone'):
                        pos = child.head
                        break
                    pos += child.head/numChildren
                bone.tail = pos
        bpy.ops.object.mode_set(mode='OBJECT')
