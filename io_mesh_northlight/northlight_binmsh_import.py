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
import bpy_extras

import enum
import io
import os.path
import dataclasses

from struct import unpack

from .material import GlobalFlags
from .material import standardmaterial
from .material import character
from .material import light

from .binmsh_loader import BINMSH


class NorthlightImport(bpy.types.Operator, bpy_extras.io_utils.ImportHelper):
    bl_idname = "northlight.import"
    bl_label = "Import Northlight mesh file"
    bl_description = "Import Northlight mesh file"

    filename_ext = ".binmsh"

    filter_glob: bpy.props.StringProperty(default='*.binmsh;*.binfbx', options={"HIDDEN"})

    def execute(self, context):
        f = open(self.filepath, 'rb')

        binmsh = BINMSH(f)

        bone_names = binmsh.bone_names

        for m in binmsh.meshs:
            mesh = bpy.data.meshes.new("mesh.lod" + str(m.lod))
            obj = bpy.data.objects.new("mesh.lod" + str(m.lod), mesh)

            # Create the meshs basic geometry
            mesh.from_pydata(m.positions, [], m.faces)

            # Create the uv layers
            for uv in m.uv_layers:
                uv_layer = mesh.uv_layers.new()
                for j in range(len(m.faces)):
                    indices = m.faces[j]
                    uv_layer.data[j * 3].uv = uv[indices[0]]
                    uv_layer.data[j * 3 + 1].uv = uv[indices[1]]
                    uv_layer.data[j * 3 + 2].uv = uv[indices[2]]


            # Create vertex groups for bones
            for bone_index in m.bone_map:
                obj.vertex_groups.new(name=bone_names[bone_index])

            # Create the vertex groups with weight for skinning
            for vertex_index, vertex_bone_indices, vertex_bone_weights in zip(range(len(m.bone_ids)), m.bone_ids, m.bone_weights):
                for vertex_bone_index, vertex_bone_weight in zip(vertex_bone_indices, vertex_bone_weights):

                    if vertex_bone_weight == 0:
                        continue

                    obj.vertex_groups[bone_names[m.bone_map[vertex_bone_index]]].add(
                        [vertex_index],
                        vertex_bone_weight,
                        "REPLACE"
                    )

            mesh_material = m.material
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

            bpy.context.scene.collection.objects.link(obj)

        return {'FINISHED'}

