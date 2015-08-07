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

def triangulate(obj):
	mesh = bmesh.new()
	mesh.from_mesh(obj.data)
	bmesh.ops.triangulate(mesh, faces=mesh.faces)
	return mesh

def mesh_data(obj, bone_ids):
	mesh = triangulate(obj)

	meshdata = {}
	vertices_lookup = {}
	vertices = []
	indices = []
	submeshes = {}

	write_skin = False
	vertex_groups = obj.vertex_groups
	dvert_layer = mesh.verts.layers.deform.active

	if bone_ids is not None and vertex_groups is not None and dvert_layer is not None:
		write_skin = True

	uv_layer = mesh.loops.layers.uv.active
	if uv_layer is None:
		raise TypeError("mesh %s has no active uv layer" %obj.data.name)

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

			vertexattributes = {}
			vertexattributes["position"] = [position.x, position.y, position.z]
			vertexattributes["texcoord"] = [texcoord.x, 1.0 - texcoord.y]
			vertexattributes["normal"] = [normal.x, normal.y, normal.z]

			vertex_tupel = (
				vertexattributes["position"][0],
				vertexattributes["position"][1],
				vertexattributes["position"][2],
				vertexattributes["texcoord"][0],
				vertexattributes["texcoord"][1],
				vertexattributes["normal"][0],
				vertexattributes["normal"][1],
				vertexattributes["normal"][2]
			)
			if vertex_tupel not in vertices_lookup:
				vertices_lookup[vertex_tupel] = len(vertices)
				vertices.append(vertexattributes)

			triangle.append(vertices_lookup[vertex_tupel])

			if write_skin:
				dvert = vertex[dvert_layer]
				if len(dvert.values()) > 4:
					raise ValueError("vertex is assigned to too many vertex groups")
				if len(dvert.values()) == 0:
					parent_name = vertex_groups
					vertexattributes["indices"] = [0]
					vertexattributes["weights"] = [1.0]
				else:
					vertexattributes["indices"] = []
					vertexattributes["weights"] = []
					for key, value in dvert.items():
						bone_name = vertex_groups[key].name
						index = bone_ids[bone_name]
						vertexattributes["indices"].append(index)
						vertexattributes["weights"].append(value)

		material = obj.material_slots[face.material_index].material
		submeshes[material.name]["indices"].append(triangle)

	meshdata["vertices"] = vertices
	meshdata["submeshes"] = submeshes

	mesh.free()
	del mesh

	return meshdata

from mathutils import Matrix, Quaternion

def anim_data(armature, bone_ids):
	armature_data = {}
	armature_data["skeleton"] = {}
	ids = 0

	armature_data["bone_hierachy"] = {}
	for i in range(0, len(armature.bones)):
		armature_data["bone_hierachy"][i] = []
	for bone in armature.bones:
		bone_data = {}
		if bone.name not in bone_ids:
			bone_ids[bone.name] = ids
			ids += 1
		bone_data["id"] = bone_ids[bone.name]
		parent = bone.parent
		parent_transformation = Matrix()
		parent_transformation.identity()
		if parent is None:
			bone_data["parent"] = None
		else:
			if parent.name not in bone_ids:
				bone_ids[parent.name] = ids
				ids += 1
			bone_data["parent"] = bone_ids[parent.name]
			parent_transformation = armature.bones[bone_data["parent"]].matrix_local
			armature_data["bone_hierachy"][bone_data["parent"]].append(bone_data["id"])

		transformation = parent_transformation.inverted() * bone.matrix_local
		rot = transformation.to_quaternion()
		rot.normalize()
		bone_data["rotation"] = [rot.w, rot.x, rot.y, rot.z]
		pos = transformation.to_translation()
		bone_data["translation"] = [pos.x, pos.y, pos.z]
		scale = transformation.to_scale()
		bone_data["scale"] = [scale.x, scale.y, scale.z]

		armature_data["skeleton"][bone_ids[bone.name]] = bone_data

	armature_data["animations"] = {}
	for action in bpy.data.actions:
		armature_data["animations"][action.name] = {}
		frame_range = action.frame_range
		armature_data["animations"][action.name]["length"] = frame_range[1] - frame_range[0]
		armature_data["animations"][action.name]["tracks"] = {}
		old_name = ""
		for fcu in action.fcurves:
			bone_name = fcu.data_path
			bone_name = bone_name[12:len(bone_name)]
			bone_name = bone_name[0:bone_name.find("\"")]
			bone_id = bone_ids[bone_name]

			if bone_name not in armature_data["animations"][action.name]["tracks"]:
				armature_data["animations"][action.name]["tracks"][bone_name] = {}
				armature_data["animations"][action.name]["tracks"][bone_name]["id"] = bone_id

			transformation_name = fcu.data_path
			transformation_name = transformation_name[transformation_name.rfind(".") + 1:len(transformation_name)]
			trans = armature_data["animations"][action.name]["tracks"][bone_name]
			if transformation_name not in trans:
				trans[transformation_name] = []

			index = 0
			for keyframe in fcu.keyframe_points:
				if transformation_name != old_name:
					trans[transformation_name].append({});
					trans[transformation_name][-1]["frame"] = keyframe.co.x - frame_range[0]
					trans[transformation_name][-1]["data"] = []

				trans[transformation_name][index]["data"].append(keyframe.co.y)
				index += 1

			old_name = transformation_name

	return armature_data

def write_json(file, data):
	json.dump(data, file, indent="\t", separators=(',', ' : '))

def write_model(filepath, selected):
	models = {}

	objects = None
	if selected:
		objects = bpy.context.selected_objects
	else:
		objects = bpy.data.objects

	for obj in objects:
		if obj.users > 0 and obj.type == 'MESH' and obj.name[0:3] != 'WGT':
			armature = obj.find_armature()
			if armature is not None:
				models[obj.name] = {}
				bone_ids = {}
				models[obj.name].update(anim_data(armature.data, bone_ids))
				models[obj.name].update(mesh_data(obj, bone_ids))
			else:
				models[obj.name] = mesh_data(obj, None)

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

	selected = BoolProperty(
		name="selected",
		description="Export only selected objects.",
		default=False
	)

	def execute(self, context):
		return write_model(self.filepath, self.selected)
