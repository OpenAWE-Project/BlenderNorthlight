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


class ComponentType(enum.Enum):
    POSITION = 0
    COLOR = 1
    BONE_INDEX = 2
    BONE_WEIGHT = 3
    TEX_COORD = 4
    NORMAL = 5


class DataType(enum.IntEnum):
    VEC3F = 0
    VEC4S = 1
    VEC2S = 2
    VEC4BF = 3
    VEC4BI = 4


@dataclasses.dataclass
class Material:
    type: str
    properties: int
    uniforms: dict


def read_string(f):
    string_length = unpack('I', f.read(4))[0]
    string = unpack('<' + str(string_length) + 's', f.read(string_length))[0].decode("ascii")
    string = string.replace("\x00", "")
    return string


def read_data(f, data_type):
    data = None
    match data_type:
        case DataType.VEC3F:
            data = unpack('fff', f.read(12))
        case DataType.VEC4S:
            data = unpack('HHHH', f.read(8))
            data = (
                data[0] / 65535.0,
                data[1] / 65535.0,
                data[2] / 65535.0,
                data[3] / 65535.0)
        case DataType.VEC2S:
            data = unpack('HH', f.read(4))
            data = (
                data[0] / 4096.0,
                data[1] / 4096.0)
        case DataType.VEC4BF:
            data = unpack('BBBB', f.read(4))
            data = (
                data[0] / 255.0,
                data[1] / 255.0,
                data[2] / 255.0,
                data[3] / 255.0)
        case DataType.VEC4BI:
            data = unpack('bbbb', f.read(4))

    return data


class NorthlightImport(bpy.types.Operator, bpy_extras.io_utils.ImportHelper):
    bl_idname = "northlight.import"
    bl_label = "Import Northlight mesh file"
    bl_description = "Import Northlight mesh file"

    filename_ext = ".binmsh"

    def execute(self, context):
        f = open(self.filepath, 'rb')

        version = unpack('I', f.read(4))[0]

        vertex_buffer_size = unpack('I', f.read(4))[0]
        indices_count = unpack('I', f.read(4))[0]
        indices_type = unpack('I', f.read(4))[0]
        flags = unpack('I', f.read(4))[0]

        vertex_buffer = io.BytesIO(f.read(vertex_buffer_size))
        index_buffer = io.BytesIO(f.read(indices_count * indices_type))

        bone_count = unpack('I', f.read(4))[0]
        bone_names = []
        for i in range(bone_count):
            bone_name = read_string(f)
            bone_names.append(bone_name)

            print(bone_name)
            
            # Inverse rest matrix + Bounding sphere for bone
            f.seek(16*4, 1)

        f.seek(4*4, 1)  # Global Bounding sphere
        f.seek(6*4, 1)  # Global Bounding Box

        lod_count = unpack('I', f.read(4))[0]

        materials = []
        material_count = unpack('I', f.read(4))[0]
        print(material_count)
        for i in range(material_count):
            if version >= 20:
                read_string(f)

            shader_name = read_string(f)

            properties = unpack('I', f.read(4))[0]
            blend_mode = unpack('I', f.read(4))[0]
            cull_mode = unpack('I', f.read(4))[0]
            material_flags = unpack('I', f.read(4))[0]

            num_attributes = unpack('I', f.read(4))[0]
            uniforms = {}
            for i in range(num_attributes):
                attribute_name = read_string(f)
                data_type = unpack('I', f.read(4))[0]

                match data_type:
                    case 0:
                        data = unpack('f', f.read(4))
                    case 1:
                        data = unpack('ff', f.read(8))
                    case 2:
                        data = unpack('fff', f.read(12))
                    case 3:
                        data = unpack('ffff', f.read(16))
                    case 7:
                        data = read_string(f)
                    case _:
                        raise Exception("Invalid data type for {}".format(attribute_name))

                uniforms[attribute_name] = data

            print("Material Shader: {}".format(shader_name))
            print("Material Blend Mode: {}".format(blend_mode))
            print("Material Cull Mode: {}".format(cull_mode))
            print("Material Properties: {}".format(hex(properties)))
            print("Material Flags: {}".format(hex(material_flags)))
            print(uniforms)
            materials.append(Material(shader_name, properties, uniforms))

        # Create the root object
        name = os.path.basename(self.filepath)
        root_mesh = bpy.data.meshes.new(name)
        root_object = bpy.data.objects.new(name, root_mesh)

        mesh_count = unpack('I', f.read(4))[0]
        for i in range(mesh_count):
            uv_count = 0

            lod = unpack('I', f.read(4))[0]
            vertex_count = unpack('I', f.read(4))[0]
            face_count = unpack('I', f.read(4))[0]
            vertex_offset = unpack('I', f.read(4))[0]
            face_offset = unpack('I', f.read(4))[0]
            f.seek(4, 1)

            assert lod < lod_count
            
            mesh = bpy.data.meshes.new("mesh" + str(i) + ".lod" + str(lod))
            obj = bpy.data.objects.new("mesh" + str(i) + ".lod" + str(lod), mesh)

            if version >= 21:
                f.seek(16, 1)

            vertex_attributes = []
            vertex_attribute_count = unpack('B', f.read(1))[0]
            for j in range(vertex_attribute_count):
                f.seek(1, 1)  # Unknown
                component_type = unpack('B', f.read(1))[0]
                data_type = unpack('B', f.read(1))[0]

                match component_type:
                    case 2:
                        component_type = ComponentType.POSITION
                    case 4:
                        component_type = ComponentType.COLOR
                    case 5:
                        if data_type == 5:
                            component_type = ComponentType.BONE_INDEX
                        else:
                            component_type = ComponentType.BONE_WEIGHT
                    case 7:
                        component_type = ComponentType.TEX_COORD
                        uv_count += 1
                    case 8:
                        component_type = ComponentType.NORMAL

                match data_type:
                    case 0:
                        data_type = DataType.VEC3F
                    case 1:
                        data_type = DataType.VEC4S
                    case 2:
                        data_type = DataType.VEC2S
                    case 3 | 4 | 6:
                        data_type = DataType.VEC4BF
                    case 5:
                        data_type = DataType.VEC4BI

                vertex_attributes.append((component_type, data_type))

            bone_map_count = unpack('I', f.read(4))[0]
            bone_map = unpack(str(bone_map_count) + 'B', f.read(bone_map_count))

            mesh_indices = []
            mesh_positions = []
            mesh_bone_indices = []
            mesh_bone_weights = []

            index_buffer.seek(face_offset * indices_type)
            for j in range(face_count):
                mesh_indices.append(unpack('HHH', index_buffer.read(6)))

            uv_layers = []
            for j in range(uv_count):
                uv_layers.append([])

            vertex_buffer.seek(vertex_offset)
            for j in range(vertex_count):
                current_uv = 0
                for attribute in vertex_attributes:
                    data_type = attribute[1]
                    component_type = attribute[0]
                    data = read_data(vertex_buffer, data_type)

                    match component_type:
                        case ComponentType.POSITION:
                            mesh_positions.append(data)
                        case ComponentType.TEX_COORD:
                            uv_layers[current_uv].append(data)
                            current_uv += 1
                        case ComponentType.BONE_INDEX:
                            mesh_bone_indices.append(data)
                        case ComponentType.BONE_WEIGHT:
                            mesh_bone_weights.append(data)

            # Create the meshs basic geometry
            mesh.from_pydata(mesh_positions, [], mesh_indices)

            # Create the uv layers
            for k in range(uv_count):
                uv_layer = mesh.uv_layers.new()
                for j in range(len(mesh_indices)):
                    indices = mesh_indices[j]
                    uv_layer.data[j * 3].uv = uv_layers[0][indices[0]]
                    uv_layer.data[j * 3 + 1].uv = uv_layers[0][indices[1]]
                    uv_layer.data[j * 3 + 2].uv = uv_layers[0][indices[2]]
            
            # Create vertex groups for bones
            for bone_index in bone_map:
                obj.vertex_groups.new(name=bone_names[bone_index])
            
            # Create the vertex groups with weight for skinning
            for vertex_index, vertex_bone_indices, vertex_bone_weights in zip(range(len(mesh_bone_indices)), mesh_bone_indices, mesh_bone_weights):
                for vertex_bone_index, vertex_bone_weight in zip(vertex_bone_indices, vertex_bone_weights):
                    if vertex_bone_weight == 0:
                        continue
                    obj.vertex_groups[bone_names[bone_map[vertex_bone_index]]].add([vertex_index], vertex_bone_weight, "REPLACE")

            mesh_material = materials[i]
            match mesh_material.type:
                case "standardmaterial":
                    standardmaterial.create_material(mesh_material.properties, mesh_material.uniforms)

            # If the flag for skinning is set, add an armature modifier
            if mesh_material.properties & GlobalFlags.SKINNING_MATRICES:
                armature_modifier = obj.modifiers.new("skin", "ARMATURE")
                armature_modifier.use_bone_envelopes = False
                armature_modifier.use_vertex_groups = True

            bpy.context.scene.collection.objects.link(obj)

        return {'FINISHED'}

