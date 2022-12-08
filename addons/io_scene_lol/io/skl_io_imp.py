from ..helper.io_helper import *
import mathutils
        
class SkeletonJoint():
    def __init__(self, file):
        self.Flags = readShort(file)
        self.id = readShort(file)
        self.ParentID = readShort(file)
        # Padding
        readShort(file)
        # -------
        self.nameHash = readInt(file)
        self.Radius = readFloat(file)

        self.localTranslation = mathutils.Vector(readVector3(file))
        self.localScale = mathutils.Vector(readVector3(file))
        self.localRotation = mathutils.Quaternion(readQuaternion(file))

        self.inverseGlobalTranslation = mathutils.Vector(readVector3(file))
        self.inverseGlobalScale = mathutils.Vector(readVector3(file))
        self.inverseGlobalRotation = mathutils.Quaternion(readQuaternion(file))

        self.nameOffset = readInt(file)
        self.returnOffset = file.tell()

        file.seek(self.returnOffset - 4 + self.nameOffset)
        self.Name = readString(file)
        file.seek(self.returnOffset)
    
    def show(self):
        print(self.id, self.Name, 'parent:', self.ParentID)

class SkeletonReader():
    def __init__(self, path):
        file = open(path, 'rb')
        self.filesize = readInt(file)
        self.formatToken = readInt(file)
        self.version = readInt(file)
        self.flags = readShort(file)
        self.jointCount = readShort(file)
        self.influencesCount = readInt(file)

        #offsets
        self.jointsOffset = readInt(file)
        self.jointIndicesOffset = readInt(file)
        self.influencesOffset = readInt(file)
        self.nameOffset = readInt(file)
        self.assetNameOffset = readInt(file)
        self.boneNameOffset = readInt(file)
        self.reservedOffset1 = readInt(file)
        self.reservedOffset2 = readInt(file)
        self.reservedOffset3 = readInt(file)
        self.reservedOffset4 = readInt(file)
        self.reservedOffset5 = readInt(file)

        self.joints = []
        if self.jointsOffset > 0 and self.jointCount > 0:
            file.seek(self.jointsOffset)
            for i in range(self.jointCount):
                self.joints.append(SkeletonJoint(file))
        
        self.influences = []
        if self.influencesOffset > 0 and self.influencesCount > 0:
            file.seek(self.influencesOffset)
            for i in range(self.influencesCount):
                self.influences.append(readShort(file))

        #TODO: Check if joint indeces are required

        if self.nameOffset > 0:
            file.seek(self.nameOffset)
            self.Name = readString(file)
        
        if self.assetNameOffset > 0:
            file.seek(self.assetNameOffset)
            self.AssetName = readString(file)