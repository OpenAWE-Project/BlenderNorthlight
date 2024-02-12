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

from bpy.utils import register_class, unregister_class

from . import northlight_binmsh_import

bl_info = {
    "name": "Northlight Import",
    "author": "Patrick Dworski <nostritius@googlemail.com>",
    "version": (1, 0, 0),
    "blender": (3, 1, 0),
    "location": "File -> Import",
    "description": "Import Northlight engine mesh files",
    "warning": "",
    "category": "Import-Export",
}

classes = [
    northlight_import.NorthlightImport
]


def menu_func_northlight_import(self, context):
    self.layout.operator(northlight_import.NorthlightImport.bl_idname, text="Northlight (.binmsh, .binfbx)")


def register():
    for c in classes:
        register_class(c)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_northlight_import)


def unregister():
    for c in classes:
        unregister_class(c)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_northlight_import)


if __name__ == '__main__':
    register()
