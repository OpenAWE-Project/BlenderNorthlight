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
from .factory import Factory

import enum


class StandardmaterialFlags(enum.IntFlag):
    NORMAL_MAP = 0x00000001
    DETAIL_MAP = 0x00000002
    SPECULAR_MAP = 0x00000004


def create_material(properties, uniforms):
    from ..material import GlobalFlags

    color_map_file = uniforms["g_sColorMap"]
    color_multiplier = uniforms["g_vColorMultiplier"]

    f = Factory("standardmaterial")
    color_map = f.add_input_image("g_sColorMap", color_map_file)
    color_multiplier = f.add_input_rgba("g_vColorMultiplier", color_multiplier)
    color_multiply = f.add_multiply(0)

    f.add_link(color_map, color_multiply, "Color", 0)
    f.add_link(color_multiplier, color_multiply, "Color", 1)
    f.add_output_link(color_multiply, "Vector", "Base Color")

    if properties & GlobalFlags.ALPHA_TEST_SAMPLER:
        f.new_block()
        alpha_map_file = uniforms["g_sAlphaTestSampler"]

        alpha_map = f.add_input_image("g_sAlphaTestSampler", alpha_map_file)
        f.add_output_link(alpha_map, "Alpha", "Alpha")

    if properties & StandardmaterialFlags.SPECULAR_MAP:
        f.new_block()
        specular_map_file = uniforms["g_sSpecularMap"]
        specular_multiplier = uniforms["g_vSpecularMultiplier"]
        glossiness_factor = uniforms["g_fGlossiness"][0]

        specular_map = f.add_input_image("g_sSpecularMap", specular_map_file)
        specular_multiplier = f.add_input_rgb("g_vSpecularMultiplier", specular_multiplier)
        glossiness_factor = f.add_input_value("g_fGlossiness", glossiness_factor)

        specular_multiply = f.add_multiply(0)

        f.add_link(specular_map, specular_multiply, "Color", 0)
        f.add_link(specular_multiplier, specular_multiply, "Color", 1)
        f.add_output_link(specular_multiply, "Vector", "Specular")
        f.add_output_link(glossiness_factor, "Value", "Metallic")

    return f.material
