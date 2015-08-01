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

import bmesh
import bpy
import json
import mathutils

def write_model(filepath):
	return {"FINISHED"}

from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy.types import Operator
from bpy_extras.io_utils import ExportHelper

class export_zmdl(Operator, ExportHelper):
	"""Exporter for the zombye model format"""
	bl_idname = "zmdl.export"
	bl_label = "Export ZMDL"

	filename_ext = ".zmdl"
	filter_glob = StringProperty(
		default="*.zmdl",
		options={'HIDDEN'}
	)

	def execute(self, context):
		return write_model(self.filepath)

def menu_func_export(self, context):
	self.layout.operator(export_zmdl.bl_idname, text="Exporter for the zombye model format")


def register():
	bpy.utils.register_class(export_zmdl)
	bpy.types.INFO_MT_file_export.append(menu_func_export)


def unregister():
	bpy.utils.unregister_class(export_zmdl)
	bpy.types.INFO_MT_file_export.remove(menu_func_export)

if __name__ == "__main__":
	register()
	bpy.ops.zmdl.export('INVOKE_DEFAULT')
