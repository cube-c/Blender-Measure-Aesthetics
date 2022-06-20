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

PKG = __package__

from bpy.props import (FloatProperty,
                       StringProperty,
                       BoolProperty
                       )

from bpy.types import (
                       AddonPreferences,
                       Panel,
                       Operator,
                       PropertyGroup,
                       )

class EpAestheticsProperties(PropertyGroup):
    quality: FloatProperty(name='Image Quality')
    status: StringProperty(name='Response Status')
    message: StringProperty(name='Response Message')

class IMAGE_OT_EpMeasureOperator(Operator):
    bl_idname = 'aesthetics.measure'
    bl_label = 'Measure Aesthetics'
    bl_description = 'Measure image aesthetics'
    bl_options = {'REGISTER'}

    def connect(self, context, filepath, image):
        with open(filepath,'rb') as pngfile:
            try:
                # import random
                # response = {'quality': {'score': random.random()}, 'status': 'ok'}
                preferences = context.preferences.addons[PKG].preferences
                client_id = preferences.client_id
                client_secret = preferences.client_secret
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
            
        ep_aesthetics = image.ep_aesthetics
        ep_aesthetics.status = response['status']
        if ep_aesthetics.status == 'error':
            ep_aesthetics.message = response['message']
        elif ep_aesthetics.status == 'ok':
            ep_aesthetics.quality = response['quality']['score']
        
    def execute(self, context):
        script_file = os.path.realpath(__file__)
        directory = os.path.dirname(script_file)
        filepath = os.path.join(directory, 'tmp.png')

        image = context.area.spaces.active.image
        file_format = image.file_format
        image.file_format = 'PNG'
        bpy.ops.image.save_as(filepath=filepath, copy=True)
        image.file_format = file_format

        self.connect(context, filepath, image)
        return {'FINISHED'}

class IMAGE_PT_EpAesthetics(Panel):
    bl_label = 'Measure Aesthetics'
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'Aesthetics'
    
    @classmethod
    def poll(cls, context):
        return context.area.spaces.active.image != None

    def draw(self, context):
        layout = self.layout
        ep_aesthetics = context.area.spaces.active.image.ep_aesthetics

        layout.operator(IMAGE_OT_EpMeasureOperator.bl_idname, text='Measure Aesthetics')

        status = ep_aesthetics.status
        if status == 'ok':
            box = layout.box()
            box.label(text='Quality: {:.2f}%'.format(ep_aesthetics.quality * 100))
        elif status == 'error':
            box = layout.box()
            box.label(text='Error: {}'.format(ep_aesthetics.message))

class EpAestheticsPrefs(AddonPreferences):
    bl_idname = PKG
    client_id: StringProperty()
    client_secret: StringProperty(subtype='PASSWORD')
    
    def draw(self, context):
        layout = self.layout
        op = layout.operator("wm.url_open", text="Register and get your Everypixel API credentials", icon='URL')
        op.url = 'https://labs.everypixel.com/api/register'
        layout.prop(self, 'client_id', text='Client ID')
        layout.prop(self, 'client_secret', text='Secret')
