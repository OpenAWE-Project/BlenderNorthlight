# OpenAWE - A reimplementation of Remedy's Alan Wake Engine
#
# OpenAWE is the legal property of its developers, whose names
# can be found in the AUTHORS file distributed with this source
# distribution.
#
# OpenAWE is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 3
# of the License, or (at your option) any later version.
#
# OpenAWE is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with OpenAWE. If not, see <http://www.gnu.org/licenses/>.

import bpy

from .material import GlobalFlags
from .material import standardmaterial

def add_uv_layers(mesh, faces, uv_layers):
    # Create the uv layers
    for uv in uv_layers:
        uv_layer = mesh.uv_layers.new()
        for j in range(len(faces)):
            indices = faces[j]
            uv_layer.data[j * 3].uv = uv[indices[0]]
            uv_layer.data[j * 3 + 1].uv = uv[indices[1]]
            uv_layer.data[j * 3 + 2].uv = uv[indices[2]]


def add_bone_data(obj, bone_map, bone_names, bone_ids, bone_weights):
    # Create vertex groups for bones
    for bone_index in bone_map:
        obj.vertex_groups.new(name=bone_names[bone_index])

    # Create the vertex groups with weight for skinning
    for vertex_index, vertex_bone_indices, vertex_bone_weights in zip(range(len(bone_ids)), bone_ids, bone_weights):
        for vertex_bone_index, vertex_bone_weight in zip(vertex_bone_indices, vertex_bone_weights):

            if vertex_bone_weight == 0:
                continue

            obj.vertex_groups[bone_names[bone_map[vertex_bone_index]]].add(
                [vertex_index],
                vertex_bone_weight,
                "REPLACE"
            )


def add_material(obj, material):
    mesh_material = material
    material = None
    match mesh_material.type:
        case "standardmaterial":
            material = standardmaterial.create_material(
                mesh_material.properties,
                mesh_material.uniforms,
                mesh_material.name
            )

    if material is not None:
        obj.data.materials.append(material)

    # If the flag for skinning is set, add an armature modifier
    if mesh_material.properties & GlobalFlags.SKINNING_MATRICES:
        armature_modifier = obj.modifiers.new("skin", "ARMATURE")
        armature_modifier.use_bone_envelopes = False
        armature_modifier.use_vertex_groups = True
