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
import mathutils

import io
import pathlib
from struct import unpack

def read_null_terminated_string(f):
    name = ""
    c = unpack('c', f.read(1))[0].decode('ascii')
    while c != '\0':
        name += c
        c = unpack('c', f.read(1))[0].decode('ascii')
    return name


class NorthlightSkelImport(bpy.types.Operator, bpy_extras.io_utils.ImportHelper):
    bl_idname = "northlight.skel_import"
    bl_label = "Import Northlight skeleton file"
    bl_description = "Import Northlight mesh file"

    filename_ext = ".skel"

    filter_glob: bpy.props.StringProperty(default='*.skel', options={"HIDDEN"})

    def execute(self, context):
        f = open(self.filepath, 'rb')

        skeleton_name = pathlib.Path(self.filepath).stem
        print(skeleton_name)

        deadbeef = unpack("<I", f.read(4))[0]
        if deadbeef != 0xD34DB33F: # 0xDEADBEEF
            return {"Invalid magic Id"}

        version = unpack("I", f.read(4))[0]
        size = unpack("I", f.read(4))[0]
        hash = unpack("I", f.read(4))[0]
        version2 = unpack("Q", f.read(8))[0]

        assert version == 1
        assert version2 == 1

        name_size = unpack("I", f.read(4))[0]
        name_data = io.BytesIO(f.read(name_size))

        num_name_offsets = unpack("I", f.read(4))[0]
        name_offsets = unpack(f"{num_name_offsets}I", f.read(num_name_offsets * 4))

        # Skip the unused hashes table
        num_hashes = unpack("I", f.read(4))[0]
        f.seek(num_hashes * 4, 1)

        num_parent_ids = unpack("I", f.read(4))[0]
        parent_ids = unpack(f"{num_parent_ids}i", f.read(num_parent_ids * 4))

        print(name_offsets)
        print(parent_ids)

        bone_translations = []
        bone_rotations = []
        num_transforms = unpack("I", f.read(4))[0]
        for _ in range(num_transforms):
            bone_translations.append(mathutils.Vector(unpack("ffff", f.read(16))[:3]))
            bone_rotations.append(mathutils.Quaternion(unpack("ffff", f.read(16))))

        armature = bpy.data.armatures.new(skeleton_name)
        armature_object = bpy.data.objects.new(skeleton_name, armature)

        context.collection.objects.link(armature_object)

        armature_object.select_set(True)
        context.view_layer.objects.active = armature_object
        bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
        bpy.ops.object.mode_set(mode="EDIT", toggle=False)

        bones = []
        absolute_rotations = []
        for name_offset, parent_id, translation, rotation in zip(name_offsets, parent_ids, bone_translations,
                                                                 bone_rotations):
            name_data.seek(name_offset)
            name = read_null_terminated_string(name_data)

            final_rotation  = mathutils.Quaternion()

            # Swizzle w from xyzw to wxyz for rotation
            local_rotation = mathutils.Quaternion((rotation[3],) + rotation[:3])

            bone = armature.edit_bones.new(name)
            if parent_id == -1:
                bone.head = (0, 0, 0)
            else:
                bone.parent = bones[parent_id]
                bone.parent.children.append(bone)
                bone.head = bone.parent.tail
                bone.tail = bone.parent.tail
                final_rotation.rotate(absolute_rotations[parent_id])

            absolute_rotations.append(final_rotation @ local_rotation)
            translation.rotate(final_rotation)
            bone.tail += translation

            bones.append(bone)
            print(name)

        return {'FINISHED'}
