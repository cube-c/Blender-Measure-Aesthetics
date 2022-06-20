# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; If not, see <http://www.gnu.org/licenses/>.
#  All rights reserved.
#
# ##### END GPL LICENSE BLOCK #####

bl_info = {
    'name': 'Measure Aesthetics',
    "author": 'cubec',
    'blender': (3, 2, 0),
    'version': (1, 0, 0),
    'category': 'Render',
    'description': 'Measure image aesthetics based on technical parameters and attractiveness using Everypixel API',
    'doc_url': 'https://github.com/cube-c/Blender-Measure-Aesthetics/blob/master/README.md'
}

import bpy
from .measure_aesthetics import *

classes = (
    EpAestheticsProperties,
    IMAGE_OT_EpMeasureOperator,
    IMAGE_PT_EpAesthetics,
    EpAestheticsPrefs
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
    bpy.types.Image.ep_aesthetics = bpy.props.PointerProperty(type=EpAestheticsProperties)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    del bpy.types.Image.ep_aesthetics
