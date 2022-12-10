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

import enum


class StandardmaterialFlags(enum.IntFlag):
    NORMAL_MAP = 0x00000001
    DETAIL_MAP = 0x00000002
    SPECULAR_MAP = 0x00000004


def create_material(properties, uniforms):
    from ..material import GlobalFlags

    standardmaterial = bpy.data.materials.new("standardmaterial")
    standardmaterial.use_nodes = True

    nodes = standardmaterial.node_tree.nodes
    links = standardmaterial.node_tree.links

    shader_root = nodes["Principled BSDF"]

    color_map_file = uniforms["g_sColorMap"]
    color_multiplier = uniforms["g_vColorMultiplier"]

    color_map_node = nodes.new("ShaderNodeTexImage")
    color_map_image = bpy.data.images.new(color_map_file, 32, 32)
    color_map_image.source = "FILE"
    color_map_node.image = color_map_image
    color_map_node.location = mathutils.Vector((-750, 300))

    color_multiplier_math_node = nodes.new("ShaderNodeVectorMath")
    color_multiplier_math_node.operation = "MULTIPLY"
    color_multiplier_math_node.location = mathutils.Vector((-450, 150))

    color_multiplier_value_node = nodes.new("ShaderNodeRGB")
    color_multiplier_value_node.outputs[0].default_value = color_multiplier
    color_multiplier_value_node.location = mathutils.Vector((-750, 0))

    links.new(color_map_node.outputs["Color"], color_multiplier_math_node.inputs[0])
    links.new(color_multiplier_value_node.outputs["Color"], color_multiplier_math_node.inputs[1])
    links.new(color_multiplier_math_node.outputs["Vector"], shader_root.inputs["Base Color"])

    if properties & GlobalFlags.ALPHA_TEST_SAMPLER:
        alpha_map_file = uniforms["g_sAlphaTestSampler"]
        alpha_map_image = bpy.data.images.new(alpha_map_file, 32, 32)
        alpha_map_image.source = "FILE"

        alpha_map_node = nodes.new("ShaderNodeTexImage")
        alpha_map_node.image = alpha_map_image
        alpha_map_node.location = mathutils.Vector((-750, -1000))

        links.new(alpha_map_node.outputs["Alpha"], shader_root.inputs["Alpha"])

    if properties & StandardmaterialFlags.SPECULAR_MAP:
        specular_map_file = uniforms["g_sSpecularMap"]
        specular_multiplier = uniforms["g_vSpecularMultiplier"]
        glossiness_factor = uniforms["g_fGlossiness"]

        specular_map_image = bpy.data.images.new(specular_map_file, 32, 32)
        specular_map_image.source = "FILE"

        specular_map_node = nodes.new("ShaderNodeTexImage")
        specular_map_node.image = specular_map_image
        specular_map_node.location = mathutils.Vector((-750, -300))

        specular_multiplier_node = nodes.new("ShaderNodeRGB")
        specular_multiplier_node.outputs[0].default_value = specular_multiplier + (1.0,)
        specular_multiplier_node.location = mathutils.Vector((-750, -600))

        specular_multiplier_math_node = nodes.new("ShaderNodeVectorMath")
        specular_multiplier_math_node.operation = "MULTIPLY"
        specular_multiplier_math_node.location = mathutils.Vector((-450, -450))

        specular_rgb_to_bw_node = nodes.new("ShaderNodeRGBToBW")
        specular_rgb_to_bw_node.location = mathutils.Vector((-300, -450))

        glossiness_node = nodes.new("ShaderNodeValue")
        glossiness_node.outputs[0].default_value = glossiness_factor[0]
        glossiness_node.location = mathutils.Vector((-750, -800))

        links.new(specular_map_node.outputs["Color"], specular_multiplier_math_node.inputs[0])
        links.new(specular_multiplier_node.outputs["Color"], specular_multiplier_math_node.inputs[1])
        links.new(specular_multiplier_math_node.outputs["Vector"], specular_rgb_to_bw_node.inputs["Color"])
        links.new(specular_rgb_to_bw_node.outputs["Val"], shader_root.inputs["Specular"])
        links.new(glossiness_node.outputs["Value"], shader_root.inputs["Metallic"])
