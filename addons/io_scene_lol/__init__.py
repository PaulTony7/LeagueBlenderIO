bl_info = {
    'name': 'SKN 4.1 format',
    'author': 'Paul Kokot',
    'version': (0, 0, 1),
    'blender': (3, 3, 0),
    'location': 'File > Import-Export',
    'description': 'Import-Export as SKN',
    'category': 'Import-Export'
}

import bpy;
from bpy.types import Operator;
from bpy_extras.io_utils import ImportHelper, ExportHelper

class ExportSKN(Operator, ExportHelper):
    """Export scene as SKN file"""
    bl_idname = 'export_scene.skn'
    bl_label = 'Export SKN'

class ImportSKN(Operator, ImportHelper): 
    """Import a SKN file"""
    bl_idname = 'import_scene.skn'
    bl_label = 'Import SKN'
    bl_options = {'REGISTER', 'UNDO'}

    def draw(self, context):
        layout = self.layout
        
        layout.use_property_split = True
        layout.use_property_decorate = False

    def execute(self, context):
        return self.import_skn(context)

    def import_skn(self, context):
        import time
        from .io.skn_io_imp import sknImporter, ImportError

        try:
            with open(self.filepath):
                skn_importer = sknImporter(self.filepath)
                skn_importer.read()
            return {'FINISHED'}
        except ImportError as e:
            self.report({'ERROR'}, e.args[0])
            return {'CANCELLED'}

def menu_func_import(self, context):
    self.layout.operator(ImportSKN.bl_idname, text='SKN 4.1 (.skn)')

def register():
    bpy.utils.register_class(ExportSKN)
    bpy.utils.register_class(ImportSKN)

    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)

def unregister():
    bpy.utils.unregister_class(ExportSKN)
    bpy.utils.unregister_class(ImportSKN)

    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
