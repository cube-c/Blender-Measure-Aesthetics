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

import numpy as np
import requests
import bpy
import os
import json
import secrets
from shutil import copyfile
from pathlib import Path
from datetime import datetime

preview_collections = {}
enum_collections = {}
enum_length = 0

PKG = __package__

from bpy.props import FloatProperty, StringProperty, BoolProperty, EnumProperty

from bpy.types import AddonPreferences, Panel, Operator, PropertyGroup

def generate_cache_folder():
    return '//cache_aes_' + secrets.token_hex(4) + '\\'

def cache_filenames(context):
    cache_folder = context.scene.aesthetics.cache_folder

    if cache_folder == '':
        return []

    filenames = list(reversed([f for f in os.listdir(bpy.path.abspath(cache_folder)) 
        if os.path.splitext(f)[1] == '.png']))

    return filenames

def cache_previews(context):
    cache_folder = context.scene.aesthetics.cache_folder
    try:
        enum_items = []
        filenames = cache_filenames(context)
        if context.scene.aesthetics.sort_by == 'time':
            indices = sorted(range(len(filenames)), key=lambda x: filenames[x], reverse=True)
        else:
            indices = sorted(range(len(filenames)), key=lambda x: filenames[x][-8:-4], reverse=True)
        filenames = [filenames[i] for i in indices]

        thumbs = preview_collections['aesthetics']
        for index, filename in zip(indices, filenames):
            if filename not in enum_collections:
                name = '{:2.2f}%'.format(int(filename[-8:-4]) / 100)
                thumb = thumbs.load(
                    filename,
                    os.path.join(bpy.path.abspath(cache_folder), filename),
                    'IMAGE'
                )
                thumb = thumb.icon_id
                enum_collections[filename] = (filename, name, '', thumb)
            enum_items.append(enum_collections[filename] + (index, ))
    except Exception as e:
        print(e)
        return []

    return enum_items

def cache_previews_wrapper(self, context):
    global enum_length
    enum_items = cache_previews(context)
    enum_length = len(enum_items)
    return enum_items

class AestheticsCacheTemp(PropertyGroup):
    quality: FloatProperty(name='Image Quality')
    status: StringProperty(name='Response Status')
    message: StringProperty(name='Response Message')
    cache_images: EnumProperty(
        items=cache_previews_wrapper,
        name='Cache Images'
    )

class AestheticsCacheSettings(PropertyGroup):
    cache_bool: BoolProperty(default=True)
    cache_folder: StringProperty(name='Cache Folder', default='', subtype='DIR_PATH')
    sort_by: EnumProperty(
        items=[
            ('time', 'Time', 'Sort by evaluated time'),
            ('quality', 'Quality', 'Sort by image quality')
        ],
        name='Sort'
    )

class IMAGE_OT_MeasureAestheticsOperator(Operator):
    bl_idname = 'aesthetics.measure'
    bl_label = 'Measure Aesthetics'
    bl_description = 'Measure image aesthetics'
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if context.scene.aesthetics.cache_folder == '':
            context.scene.aesthetics.cache_folder = generate_cache_folder()

        script_file = os.path.realpath(__file__)
        directory = os.path.dirname(script_file)
        filepath = os.path.join(directory, 'tmp', 'tmp.png')

        image = context.area.spaces.active.image
        file_format = image.file_format
        image.file_format = 'PNG'
        bpy.ops.image.save_as(filepath=filepath, copy=True)
        image.file_format = file_format

        with open(filepath, 'rb') as pngfile:
            try:
                preferences = context.preferences.addons[PKG].preferences
                client_id = preferences.client_id
                client_secret = preferences.client_secret
                # import random
                # response = {'quality': {'score': random.random()}, 'status': 'ok'}
                response = requests.post('https://api.everypixel.com/v1/quality', files={'data': pngfile}, auth=(client_id, client_secret)).json()
                if isinstance(response, str):
                    response = json.loads(response)
            except requests.exceptions.Timeout:
                response = {'status': 'error', 'message': 'Timeout'}
            except requests.exceptions.HTTPError:
                response = {'status': 'error', 'message': 'HTTP Error'}
            except requests.exceptions.ConnectionError:
                response = {'status': 'error', 'message': 'Connection Error'}
            except requests.exceptions.RequestException:
                response = {'status': 'error', 'message': 'Request Exception'}
            
        aesthetics = context.scene.aesthetics
        message = context.window_manager.aesthetics
        cache_folder = aesthetics.cache_folder

        message.status = response['status']
        if message.status == 'error':
            message.message = response['message']
        elif message.status == 'ok':
            message.quality = response['quality']['score']
            if aesthetics.cache_bool:
                tm = datetime.now().strftime('%Y%m%d%H%M%S%f')
                filename = '{}_{:04.0f}.png'.format(tm, message.quality * 10000)
                os.makedirs(bpy.path.abspath(cache_folder), exist_ok=True)
                copyfile(filepath, bpy.path.abspath(os.path.join(cache_folder, filename)))
                context.window_manager.aesthetics.cache_images = filename
        
        return {'FINISHED'}

class IMAGE_PT_Aesthetics(Panel):
    bl_label = 'Measure Aesthetics'
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'Aesthetics'
    
    def draw(self, context):
        layout = self.layout
        col = layout.column()
        if context.blend_data.filepath == '':
            col.label(text='Save the Blend File to Use the Feature.', icon='INFO')
            return

        if context.area.spaces.active.image != None and bpy.ops.image.save_as.poll():
            col.operator(IMAGE_OT_MeasureAestheticsOperator.bl_idname, text='Evaluate')
        else:
            col.label(text='Select Appropriate Image to Evaluate', icon='INFO')

        message = context.window_manager.aesthetics

        if not message.status == '':
            box = col.box()
            box.label(text='Status: {}'.format(message.status))
            if message.status == 'ok':
                box.label(text='Quality: {:2.2f}%'.format(message.quality * 100))
            elif message.status == 'error':
                box.label(text='Error: {}'.format(message.message))

class IMAGE_PT_AestheticsResult(Panel):
    bl_parent_id = 'IMAGE_PT_Aesthetics'
    bl_label = 'Cache'
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'Aesthetics'
    
    def draw_header(self, context):
        self.layout.prop(context.scene.aesthetics, 'cache_bool', text='')

    def draw(self, context):
        layout = self.layout
        col1 = layout.column()
        aesthetics = context.scene.aesthetics
        aesthetics_temp = context.window_manager.aesthetics
        col1.enabled = aesthetics.cache_bool
        col1.prop(aesthetics, 'cache_folder', text='')
        col2 = layout.column()
        if cache_filenames(context) and aesthetics.cache_bool:
            col2.prop(aesthetics, 'sort_by')
            col2.template_icon_view(aesthetics_temp, 'cache_images', show_labels=True)
            if not aesthetics_temp.cache_images == '':
                box = col2.box()
                box.label(text='Quality: {:2.2f}%'.format(int(aesthetics_temp.cache_images[-8:-4]) / 100))

class AestheticsPrefs(AddonPreferences):
    bl_idname = PKG
    client_id: StringProperty()
    client_secret: StringProperty(subtype='PASSWORD')
    
    def draw(self, context):
        layout = self.layout
        op = layout.operator("wm.url_open", text="Register and get your Everypixel API credentials", icon='URL')
        op.url = 'https://labs.everypixel.com/api/register'
        layout.prop(self, 'client_id', text='Client ID')
        layout.prop(self, 'client_secret', text='Secret')

classes = (
    AestheticsCacheTemp,
    AestheticsCacheSettings,
    IMAGE_OT_MeasureAestheticsOperator,
    IMAGE_PT_Aesthetics,
    IMAGE_PT_AestheticsResult,
    AestheticsPrefs
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
    bpy.types.Scene.aesthetics = bpy.props.PointerProperty(type=AestheticsCacheSettings)
    bpy.types.WindowManager.aesthetics = bpy.props.PointerProperty(type=AestheticsCacheTemp)

    pcoll = bpy.utils.previews.new()
    preview_collections['aesthetics'] = pcoll

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    del bpy.types.Scene.aesthetics
    del bpy.types.WindowManager.aesthetics

    for pcoll in preview_collections.values():
        bpy.utils.previews.remove(pcoll)
    preview_collections.clear()