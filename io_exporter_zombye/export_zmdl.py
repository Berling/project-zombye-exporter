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

def triangulate(obj):
	mesh = bmesh.new()
	mesh.from_mesh(obj.data)
	bmesh.ops.triangulate(mesh, faces=mesh.faces)
	return mesh

def mesh_data(obj):
	mesh = triangulate(obj)

	meshdata = {}
	vertices_lookup = {}
	vertices = []
	indices = []
	submeshes = {}

	uv_layer = mesh.loops.layers.uv.active
	if uv_layer is None:
		raise TypeError("mesh %s has no active uv layer" %name)

	for material_slot in obj.material_slots:
		material = material_slot.material
		if material.users > 0:
			submeshes[material.name] = {}
			submeshes[material.name]["indices"] = []
			submeshes[material.name]["textures"] = {}

			texture_slots = material.texture_slots
			textures = ["diffuse", "normal", "material"]
			for texture in textures:
				for key, value in texture_slots.items():
					if texture in key:
						submeshes[material.name]["textures"][texture] = bpy.path.abspath(value.texture.image.filepath)
						break
					else:
						submeshes[material.name]["textures"][texture] = ""

	for face in mesh.faces:
		triangle = []
		for loop in face.loops:
			vertex = loop.vert
			position = vertex.co
			normal = face.normal
			if face.smooth:
				normal = vertex.normal
			texcoord = loop[uv_layer].uv
			index = vertex.index

			vertexattributes = {}
			vertexattributes["position"] = [position.x, position.y, position.z]
			vertexattributes["texcoord"] = [texcoord.x, 1.0 - texcoord.y]
			vertexattributes["normal"] = [normal.x, normal.y, normal.z]

			if index not in vertices_lookup:
				vertices_lookup[index] = len(vertices)
				vertices.append(vertexattributes)

			triangle.append(vertices_lookup[index])

		material = obj.material_slots[face.material_index].material
		submeshes[material.name]["indices"].append(triangle)

	meshdata["vertices"] = vertices
	meshdata["submeshes"] = submeshes

	return meshdata

def write_json(file, data):
	json.dump(data, file, indent="\t", separators=(',', ' : '))

def write_model(filepath):
	models = {}
	for obj in bpy.data.objects:
		if obj.users > 0 and obj.type == 'MESH':
			models[obj.name] = mesh_data(obj)

	file = open(filepath, 'w', encoding='utf-8')
	write_json(file, models)
	file.close()

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
