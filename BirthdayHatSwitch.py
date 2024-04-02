import bpy
import math
import json
import collections
import traceback
from math import pi
from bpy.props import StringProperty
from mathutils import Euler, Matrix, Quaternion, Vector
from rna_prop_ui import rna_idprop_quote_path

rig_id = "ws0pfgdn2647d236"


############################
## Math utility functions ##
############################

def perpendicular_vector(v):
    """ Returns a vector that is perpendicular to the one given.
        The returned vector is _not_ guaranteed to be normalized.
    """
    # Create a vector that is not aligned with v.
    # It doesn't matter what vector.  Just any vector
    # that's guaranteed to not be pointing in the same
    # direction.
    if abs(v[0]) < abs(v[1]):
        tv = Vector((1,0,0))
    else:
        tv = Vector((0,1,0))

    # Use cross prouct to generate a vector perpendicular to
    # both tv and (more importantly) v.
    return v.cross(tv)


def rotation_difference(mat1, mat2):
    """ Returns the shortest-path rotational difference between two
        matrices.
    """
    q1 = mat1.to_quaternion()
    q2 = mat2.to_quaternion()
    angle = math.acos(min(1,max(-1,q1.dot(q2)))) * 2
    if angle > pi:
        angle = -angle + (2*pi)
    return angle

def find_min_range(f,start_angle,delta=pi/8):
    """ finds the range where lies the minimum of function f applied on bone_ik and bone_fk
        at a certain angle.
    """
    angle = start_angle
    while (angle > (start_angle - 2*pi)) and (angle < (start_angle + 2*pi)):
        l_dist = f(angle-delta)
        c_dist = f(angle)
        r_dist = f(angle+delta)
        if min((l_dist,c_dist,r_dist)) == c_dist:
            return (angle-delta,angle+delta)
        else:
            angle=angle+delta

def ternarySearch(f, left, right, absolutePrecision):
    """
    Find minimum of unimodal function f() within [left, right]
    To find the maximum, revert the if/else statement or revert the comparison.
    """
    while True:
        #left and right are the current bounds; the maximum is between them
        if abs(right - left) < absolutePrecision:
            return (left + right)/2

        leftThird = left + (right - left)/3
        rightThird = right - (right - left)/3

        if f(leftThird) > f(rightThird):
            left = leftThird
        else:
            right = rightThird

###################
## Rig UI Panels ##
###################

class RigUI(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_label = "Rig Main Properties"
    bl_idname = "VIEW3D_PT_rig_ui_" + rig_id
    bl_category = 'Item'

    @classmethod
    def poll(self, context):
        if context.mode != 'POSE':
            return False
        try:
            return (context.active_object.data.get("rig_id") == rig_id)
        except (AttributeError, KeyError, TypeError):
            return False

    def draw(self, context):
        layout = self.layout
        pose_bones = context.active_object.pose.bones
        try:
            selected_bones = set(bone.name for bone in context.selected_pose_bones)
            selected_bones.add(context.active_pose_bone.name)
        except (AttributeError, TypeError):
            return

        def is_selected(names):
            # Returns whether any of the named bones are selected.
            if isinstance(names, list) or isinstance(names, set):
                return not selected_bones.isdisjoint(names)
            elif names in selected_bones:
                return True
            return False

        num_rig_separators = [-1]

        def emit_rig_separator():
            if num_rig_separators[0] >= 0:
                layout.separator()
            num_rig_separators[0] += 1

class RigLayers(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_label = "Rig Layers"
    bl_idname = "VIEW3D_PT_rig_layers_" + rig_id
    bl_category = 'Item'

    @classmethod
    def poll(self, context):
        try:
            return (context.active_object.data.get("rig_id") == rig_id)
        except (AttributeError, KeyError, TypeError):
            return False

    def draw(self, context):
        layout = self.layout
        col = layout.column()

        row = col.row()
        row.prop(context.active_object.data, 'layers', index=0, toggle=True, text='M')

        row = col.row()
        row.separator()
        row = col.row()
        row.separator()

        row = col.row()
        row.prop(context.active_object.data, 'layers', index=28, toggle=True, text='Root')




class GORRO_MT_TemplateMenu(bpy.types.Menu):
    bl_label = "Gorros Trotties"
    bl_idname = "GORROS_MT_TemplateMenu"  

    def draw(self, context):
        layout = self.layout
        layout.operator("wm.template_operator", icon='CONE', text = "Emma").bl_gorrosName = 'Emma'
        layout.operator("wm.template_operator", icon='CONE', text = "Lucy").bl_gorrosName = 'Lucy'
        layout.operator("wm.template_operator", icon='CONE', text = "Mia").bl_gorrosName = 'Mia'
        layout.operator("wm.template_operator", icon='CONE', text = "Sophie").bl_gorrosName = 'Sophie'




class GORROS_PT_TemplatePanel(bpy.types.Panel):
    bl_label = "Gorros Cumpleaños"
    bl_idname = "GORROS_PT_TemplatePanel"
    bl_space_type = "VIEW_3D"
    bl_region_type = 'UI'
    bl_category = "Item"
    
    
    def draw(self, context):
        layout = self.layout
        iconRender = ['SEQUENCE_COLOR_03','SEQUENCE_COLOR_07','SEQUENCE_COLOR_05','SEQUENCE_COLOR_04']
        textRender = ['Gorro Emma','Gorro Lucy','Gorro Mia','Gorro Sophie']
        layout.menu(GORRO_MT_TemplateMenu.bl_idname, icon=iconRender[bpy.data.objects[bpy.context.active_object.name].pose.bones["root"]["GorroSet"]], text=textRender[bpy.data.objects[bpy.context.active_object.name].pose.bones["root"]["GorroSet"]])



def conmutadorGorros(nameTrottie):
    listNames = ['Emma', 'Lucy','Mia','Sophie']
    listNames.remove(nameTrottie)
    rigName = bpy.context.active_object.name 

    if bpy.context.active_object.name[-4:][:1] !=".":
        for itemName in listNames:

            GeoName = "geo_GorrosCumple_"+itemName.replace(itemName[:1],itemName[:1].lower())+"_00_n"
            bpy.data.objects[GeoName].modifiers[itemName+"LAT"].show_viewport = False
            bpy.data.objects[GeoName].modifiers[itemName+"LAT"].show_render = False
            bpy.data.objects[GeoName].hide_viewport = True
            bpy.data.objects[GeoName].hide_render = True


        GeoName = "geo_GorrosCumple_"+nameTrottie.replace(nameTrottie[:1],nameTrottie[:1].lower())+"_00_n"
        bpy.data.objects[GeoName].modifiers[nameTrottie+"LAT"].show_viewport = True
        bpy.data.objects[GeoName].modifiers[nameTrottie+"LAT"].show_render = True
        bpy.data.objects[GeoName].hide_viewport = False
        bpy.data.objects[GeoName].hide_render = False    

    else:
        for itemName in listNames:

            GeoName = "geo_GorrosCumple_"+itemName.replace(itemName[:1],itemName[:1].lower())+"_00_n" + bpy.context.active_object.name[-4:]
            bpy.data.objects[GeoName].modifiers[itemName+"LAT"].show_viewport = False
            bpy.data.objects[GeoName].modifiers[itemName+"LAT"].show_render = False
            bpy.data.objects[GeoName].hide_viewport = True
            bpy.data.objects[GeoName].hide_render = True


        GeoName = "geo_GorrosCumple_"+nameTrottie.replace(nameTrottie[:1],nameTrottie[:1].lower())+"_00_n" + bpy.context.active_object.name[-4:]
        bpy.data.objects[GeoName].modifiers[nameTrottie+"LAT"].show_viewport = True
        bpy.data.objects[GeoName].modifiers[nameTrottie+"LAT"].show_render = True
        bpy.data.objects[GeoName].hide_viewport = False
        bpy.data.objects[GeoName].hide_render = False    

class GORROS_OT_TemplateOperator(bpy.types.Operator):
    bl_label = "Gorros"
    bl_idname = "wm.template_operator"
    bl_gorrosName: bpy.props.StringProperty(name="")
    
    
    def execute(self, context):
        
        conmutadorGorros(self.bl_gorrosName)
        if self.bl_gorrosName == 'Emma':
            
            bpy.data.objects[bpy.context.active_object.name].pose.bones["root"]["GorroSet"] = 0

        
        if self.bl_gorrosName == 'Lucy':
            bpy.data.objects[bpy.context.active_object.name].pose.bones["root"]["GorroSet"] = 1
            
        
        if self.bl_gorrosName == 'Mia':
          
            bpy.data.objects[bpy.context.active_object.name].pose.bones["root"]["GorroSet"] = 2

        if self.bl_gorrosName == 'Sophie':
            
            bpy.data.objects[bpy.context.active_object.name].pose.bones["root"]["GorroSet"] = 3

        return {'FINISHED'}    


def register():
    bpy.utils.register_class(RigUI)
    bpy.utils.register_class(RigLayers)
    bpy.utils.register_class(GORRO_MT_TemplateMenu)
    bpy.utils.register_class(GORROS_PT_TemplatePanel)
    bpy.utils.register_class(GORROS_OT_TemplateOperator)

def unregister():
    bpy.utils.unregister_class(RigUI)
    bpy.utils.unregister_class(RigLayers)
    bpy.utils.unregister_class(GORRO_MT_TemplateMenu)
    bpy.utils.unregister_class(GORROS_PT_TemplatePanel)
    bpy.utils.unregister_class(GORROS_OT_TemplateOperator)

register()