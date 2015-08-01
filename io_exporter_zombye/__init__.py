# The MIT License (MIT)
#
# Copyright (c) 2015 Georg Schäfer
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import bpy
from .export_zmdl import export_zmdl

bl_info = {
	"name" : "Zombye Model Exporter",
	"author" : "Georg Schäfer",
	"version" : (0, 1, 1),
	"blender" : (2, 7, 5),
	"location" : "File > Export > Zombye Model (.zmdl)",
	"description" : "The script exports meshes, armatures and animations to the Zombye Model format (zmdl)",
	"category" : "Import-Export"
}

def menu_func_export(self, context):
	self.layout.operator(export_zmdl.bl_idname, text="Zombye Model (.zmdl)")

def register():
	bpy.utils.register_class(export_zmdl)
	bpy.types.INFO_MT_file_export.append(menu_func_export)

def unregister():
	bpy.utils.unregister_class(export_zmdl)
	bpy.types.INFO_MT_file_export.remove(menu_func_export)

if __name__ == "__main__":
	register()
	bpy.ops.zmdl.export('INVOKE_DEFAULT')
