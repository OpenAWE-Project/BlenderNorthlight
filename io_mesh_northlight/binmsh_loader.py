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

import os
import io
import enum
import dataclasses
from struct import unpack


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
    VEC4SI = 5


@dataclasses.dataclass
class Material:
    type: str
    name: str
    properties: int
    uniforms: dict


@dataclasses.dataclass
class Mesh:
    lod: int
    positions: []
    faces: []
    bone_ids: []
    bone_weights: []
    bone_map: []
    uv_layers: []
    vertex_colors: []
    material: Material


def read_string(binmsh):
    string_length = unpack('I', binmsh.read(4))[0]
    string = unpack('<' + str(string_length) + 's', binmsh.read(string_length))[0].decode("ascii")
    string = string.replace("\x00", "")
    return string


def read_data(binmsh, data_type):
    data = None
    match data_type:
        case DataType.VEC3F:
            data = unpack('fff', binmsh.read(12))
        case DataType.VEC4S:
            data = unpack('HHHH', binmsh.read(8))
            data = (
                data[0] / 65535.0,
                data[1] / 65535.0,
                data[2] / 65535.0,
                data[3] / 65535.0)
        case DataType.VEC2S:
            data = unpack('HH', binmsh.read(4))
            data = (
                data[0] / 4096.0,
                1.0 - (data[1] / 4096.0))
        case DataType.VEC4BF:
            data = unpack('BBBB', binmsh.read(4))
            data = (
                data[0] / 255.0,
                data[1] / 255.0,
                data[2] / 255.0,
                data[3] / 255.0)
        case DataType.VEC4BI:
            data = unpack('bbbb', binmsh.read(4))
        case DataType.VEC4SI:
            data = unpack('hhhh', binmsh.read(8))

    return data


class BINMSH:
    def __init__(self, binmsh):
        version = unpack('I', binmsh.read(4))[0]
        match version:
            case 19:
                print("Alan Wake Mesh")
            case 20 | 21:
                print("Alan Wakes American Nightmare Mesh")
            case 43:
                print("Quantum Break Mesh")
            case _:
                raise Exception("Invalid or unsupported mesh version")

        if version >= 43:
            secondary_buffer_size = unpack('I', binmsh.read(4))[0]

        vertex_buffer_size = unpack('I', binmsh.read(4))[0]
        indices_count = unpack('I', binmsh.read(4))[0]
        indices_type = unpack('I', binmsh.read(4))[0]
        flags = unpack('I', binmsh.read(4))[0]

        secondary_buffer = None
        if version >= 43:
            secondary_buffer = io.BytesIO(binmsh.read(secondary_buffer_size))

        vertex_buffer = io.BytesIO(binmsh.read(vertex_buffer_size))
        index_buffer = io.BytesIO(binmsh.read(indices_count * indices_type))

        self.bone_names = []
        bone_count = unpack('I', binmsh.read(4))[0]
        for i in range(bone_count):
            bone_name = read_string(binmsh)
            self.bone_names.append(bone_name)

            print(bone_name)

            # Inverse rest matrix + Bounding sphere for bone
            binmsh.seek(16 * 4, 1)

            # Unknown value
            if version >= 43:
                binmsh.seek(4, 1)

        if version >= 43:
            binmsh.seek(16, 1)  # Unknown

            num_unks = unpack('I', binmsh.read(4))[0]
            unks = unpack(str(num_unks) + 'f', binmsh.read(num_unks * 4))

            unk = unpack('f', binmsh.read(4))[0]

        binmsh.seek(4 * 4, 1)  # Global Bounding sphere
        binmsh.seek(6 * 4, 1)  # Global Bounding Box

        lod_count = unpack('I', binmsh.read(4))[0]

        materials = []
        material_count = unpack('I', binmsh.read(4))[0]
        print(material_count)
        for i in range(material_count):
            if version >= 43:
                binmsh.seek(4, 1)  # Unknown (Always 4?)

            if version >= 20:
                material_name = read_string(binmsh)
                print("Material Name: %s" % material_name)
            else:
                material_name = ""

            shader_name = read_string(binmsh)

            # Source file
            if version >= 43:
                source_file = read_string(binmsh)
                print("Source File: %s" % source_file)

                num_unks = unpack('I', binmsh.read(4))[0]
                binmsh.seek(num_unks * 8, 1)

            properties = unpack('I', binmsh.read(4))[0]
            blend_mode = unpack('I', binmsh.read(4))[0]
            cull_mode = unpack('I', binmsh.read(4))[0]
            material_flags = unpack('I', binmsh.read(4))[0]

            if version >= 43:
                binmsh.seek(4, 1)

            num_attributes = unpack('I', binmsh.read(4))[0]
            uniforms = {}
            for i in range(num_attributes):
                attribute_name = read_string(binmsh)
                data_type = unpack('I', binmsh.read(4))[0]

                match data_type:
                    case 0:  # Float
                        data = unpack('f', binmsh.read(4))
                    case 1:  # Vec2
                        data = unpack('ff', binmsh.read(8))
                    case 2:  # Vec3
                        data = unpack('fff', binmsh.read(12))
                    case 3:  # Vec4
                        data = unpack('ffff', binmsh.read(16))
                    case 7 | 9:  # Texture
                        data = read_string(binmsh)
                    case 8:  # Sampler type
                        data = None
                    case 12:  # Bool
                        data = unpack('I', binmsh.read(4))[0] != 0
                    case _:
                        raise Exception("Invalid data type for {}".format(attribute_name))

                uniforms[attribute_name] = data

            print("Material Shader: {}".format(shader_name))
            print("Material Blend Mode: {}".format(blend_mode))
            print("Material Cull Mode: {}".format(cull_mode))
            print("Material Properties: {}".format(hex(properties)))
            print("Material Flags: {}".format(hex(material_flags)))
            print(uniforms)
            materials.append(Material(shader_name, material_name, properties, uniforms))

            print("------------------------------------------------------")

        if version >= 43:
            # Unknown data table
            num_unks = unpack('I', binmsh.read(4))[0]
            binmsh.seek(num_unks * 4, 1)

            binmsh.seek(4, 1)

            # Another unknown data table
            num_unks = unpack('I', binmsh.read(4))[0]
            binmsh.seek(num_unks * 4, 1)

        # Create the root object
        name = os.path.basename("mesh")

        mesh_count = unpack('I', binmsh.read(4))[0]
        self.meshs = []
        for i in range(mesh_count):
            uv_count = 0
            color_count = 0

            lod = unpack('I', binmsh.read(4))[0]
            vertex_count = unpack('I', binmsh.read(4))[0]
            face_count = unpack('I', binmsh.read(4))[0]

            if version >= 43:
                secondary_vertex_offset = unpack('I', binmsh.read(4))[0]

            vertex_offset = unpack('I', binmsh.read(4))[0]
            face_offset = unpack('I', binmsh.read(4))[0]
            binmsh.seek(4, 1)

            assert lod < lod_count

            if version == 21:
                binmsh.seek(16, 1)

            if version >= 43:
                binmsh.seek(4 * 4, 1)
                binmsh.seek(6 * 4, 1)
                binmsh.seek(4, 1)

            vertex_attributes = []
            vertex_attribute_count = unpack('B', binmsh.read(1))[0]
            for j in range(vertex_attribute_count):
                different_buffer = False
                if version >= 43:
                    different_buffer = unpack("B", binmsh.read(1))[0] == 1
                else:
                    binmsh.seek(1, 1)  # Unknown
                component_type = unpack('B', binmsh.read(1))[0]
                data_type = unpack('B', binmsh.read(1))[0]

                if version >= 43:
                    binmsh.seek(1, 1)

                match component_type:
                    case 2:
                        component_type = ComponentType.POSITION
                    case 4:
                        component_type = ComponentType.COLOR
                        color_count += 1
                    case 5:
                        if data_type == 5:
                            component_type = ComponentType.BONE_INDEX
                        else:
                            component_type = ComponentType.BONE_WEIGHT
                    case 13:
                        component_type = ComponentType.BONE_INDEX
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
                        if version >= 43:
                            data_type = DataType.VEC4SI
                        else:
                            data_type = DataType.VEC4BI

                vertex_attributes.append((component_type, data_type, different_buffer))
                print((component_type, data_type, different_buffer))

            if version >= 43:
                binmsh.seek(13, 1)

                # Identity bone map since all games >=Quantum Break use the bone indices directly
                # TODO: Make sure, that only the bones used in this part mesh are used
                bone_map = range(bone_count)
            else:
                bone_map_count = unpack('I', binmsh.read(4))[0]
                bone_map = unpack(str(bone_map_count) + 'B', binmsh.read(bone_map_count))

            mesh_indices = []
            mesh_positions = []
            mesh_bone_indices = []
            mesh_bone_weights = []
            mesh_colors = []
            for j in range(color_count):
                mesh_colors.append([])

            index_buffer.seek(face_offset * indices_type)
            for j in range(face_count):
                mesh_indices.append(unpack('HHH', index_buffer.read(6)))

            uv_layers = []
            for j in range(uv_count):
                uv_layers.append([])

            if secondary_buffer is not None:
                secondary_buffer.seek(secondary_vertex_offset)

            vertex_buffer.seek(vertex_offset)
            for j in range(vertex_count):
                current_uv = 0
                current_color = 0
                for attribute in vertex_attributes:
                    different_buffer = attribute[2]
                    data_type = attribute[1]
                    component_type = attribute[0]

                    if different_buffer:
                        data = read_data(secondary_buffer, data_type)
                    else:
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
                        case ComponentType.COLOR:
                            mesh_colors[current_color].append(data)
                            current_color += 1

            mesh = Mesh(
                lod,
                mesh_positions,
                mesh_indices,
                mesh_bone_indices,
                mesh_bone_weights,
                bone_map,
                uv_layers,
                mesh_colors,
                materials[i % material_count]
            )
            self.meshs.append(mesh)
