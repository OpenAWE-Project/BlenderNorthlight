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
import mathutils


class Factory:
    def __init__(self, name, num_columns=1):
        self.material = bpy.data.materials.new(name)
        self.material.use_nodes = True
        self.nodes = self.material.node_tree.nodes
        self.links = self.material.node_tree.links

        self.columns = []
        self.column_offsets = []
        for i in range(num_columns):
            self.columns.append((i + 1) * -400)
            self.column_offsets.append(300)

        self.input_column_offset = 300
        self.input_column = (num_columns + 1) * -400

    def add_output_link(self, node, output, input):
        shader_root = self.nodes["Principled BSDF"]
        self.links.new(node.outputs[output], shader_root.inputs[input])

    def add_link(self, node1, node2, output, input):
        self.links.new(node1.outputs[output], node2.inputs[input])

    def new_block(self):
        max_offset = self.input_column_offset
        for column_offset in self.column_offsets:
            max_offset = min(max_offset, column_offset)

        self.input_column_offset -= 50
        for i in range(len(self.column_offsets)):
            self.column_offsets[i] = max_offset - 50

    def add_multiply(self, column: int):
        multiply_node = self.nodes.new("ShaderNodeVectorMath")
        multiply_node.operation = "MULTIPLY"
        multiply_node.location = (self.columns[column], self.column_offsets[column])
        self.column_offsets[column] -= 150
        return multiply_node

    def add_input_rgba(self, name: str, color: tuple):
        rgb_node = self.nodes.new("ShaderNodeRGB")
        rgb_node.label = name
        rgb_node.outputs[0].default_value = color
        rgb_node.location = (self.input_column, self.input_column_offset)
        self.input_column_offset -= 200
        return rgb_node

    def add_input_rgb(self, name: str, color: tuple):
        rgb_node = self.nodes.new("ShaderNodeRGB")
        rgb_node.label = name
        rgb_node.outputs[0].default_value = color + (1.0,)
        rgb_node.location = (self.input_column, self.input_column_offset)
        self.input_column_offset -= 200
        return rgb_node

    def add_input_value(self, name: str, value: tuple):
        value_node = self.nodes.new("ShaderNodeValue")
        value_node.label = name
        value_node.outputs[0].default_value = value
        value_node.location = (self.input_column, self.input_column_offset)
        self.input_column_offset -= 100
        return value_node

    def add_input_image(self, name: str, file: str):
        image_node = self.nodes.new("ShaderNodeTexImage")
        image_node.label = name

        image = bpy.data.images.new(file, 32, 32)
        image.source = "FILE"

        image_node.image = image
        image_node.location = (self.input_column, self.input_column_offset)
        self.input_column_offset -= 300
        return image_node

