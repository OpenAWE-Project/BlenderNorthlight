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

from .util import *


class NorthlightFoliageImport(bpy.types.Operator, bpy_extras.io_utils.ImportHelper):
    bl_idname = "northlight.import"
    bl_label = "Import Northlight foliage mesh file"
    bl_description = "Import Northlight foliage mesh file"

    filename_ext = ".binfol"

    filter_glob: bpy.props.StringProperty(default='*.binfol', options={"HIDDEN"})

    def execute(self, context):
        f = open(self.filepath, 'rb')

        version = unpack("I", f.read(4))[0]
        if version != 19:
            raise Exception("Unsupported binfol version")

        mesh_data_size = unpack("I", f.read(4))[0]
        mesh_data = io.BytesIO(f.read(mesh_data_size))
        binmsh = BINMSH(mesh_data)

        bone_names = binmsh.bone_names

        for i, m in zip(range(len(binmsh.meshs)), binmsh.meshs):
            mesh = bpy.data.meshes.new("mesh{}.lod{}".format(i, m.lod))
            obj = bpy.data.objects.new("mesh{}.lod{}".format(i, m.lod), mesh)

            # Create the meshs basic geometry
            mesh.from_pydata(m.positions, [], m.faces)

            # Create the uv layers
            add_uv_layers(mesh, m.faces, m.uv_layers)

            # Create the color layers
            add_vertex_colors(mesh, m.faces, m.vertex_colors)

            # Create vertex groups for bones
            add_bone_data(obj, m.bone_map, bone_names, m.bone_ids, m.bone_weights)

            # Create material for object
            add_material(obj, m.material)

            bpy.context.scene.collection.objects.link(obj)

        return {'FINISHED'}