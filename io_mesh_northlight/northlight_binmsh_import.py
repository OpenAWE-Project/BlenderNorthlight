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

from .binmsh_loader import BINMSH

from .util import *

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

        for i, m in zip(range(len(binmsh.meshs)), binmsh.meshs):
            mesh = bpy.data.meshes.new("mesh{}.lod{}".format(i, m.lod))
            obj = bpy.data.objects.new("mesh{}.lod{}".format(i, m.lod), mesh)

            # Create the meshs basic geometry
            mesh.from_pydata(m.positions, [], m.faces)

            # Create the uv layers
            add_uv_layers(mesh, m.faces, m.uv_layers)

            # Create vertex groups for bones
            add_bone_data(obj, m.bone_map, bone_names, m.bone_ids, m.bone_weights)

            # Create material for object
            add_material(obj, m.material)

            bpy.context.scene.collection.objects.link(obj)

        return {'FINISHED'}

