import os,sys
import bpy
import numpy as np
from numpy.linalg import inv
import yaml

class save_pose(bpy.types.Operator):
    bl_idname="object.save"
    bl_label = "Save Pose"
    filepath: bpy.props.StringProperty(subtype="FILE_PATH", default = "./poses.yaml")
    
    def execute(self,context):
        print("Saving poses to: " + self.filepath)
        output_list = []
        for obj in bpy.data.collections['objects'].objects:
                print("obj: ", obj.name)
                pose = np.zeros((4,4))
                pose[:,:]=obj.matrix_world    
                #try to get to same coordinate system as jnb reprojection
                #pose[:3,:3] = pose[:3, :3] * -1
                #pose[:3, 0] = pose[:3, 0] * -1 
                pose = pose.reshape(-1)
                output_list.append({"path":"-/Test.ply","id":obj.name,"pose":pose.tolist()})

        if output_list:       
            print(yaml.dump(output_list, default_flow_style=False))
            with open(self.filepath,'w') as f:
                yaml.dump(output_list, f, default_flow_style=False)
      
        return {'FINISHED'}
    
    def invoke(self,context, event):
        #set filepath with default value of property
        self.filepath = self.filepath
        context.window_manager.fileselect_add(self)
        print(self.filepath)
        return {'RUNNING_MODAL'}
       
class PoseAnnotationPanel(bpy.types.Panel):
    bl_label = "Pose Annotation"
    bl_idname = "3D_VIEW__PT_annotation_1"
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"

    def draw(self, context):
        layout = self.layout
        row=layout.row()
        row.alignment = 'CENTER'
        row.operator("object.save")
        
def register():
    bpy.utils.register_class(save_pose)
    bpy.utils.register_class(PoseAnnotationPanel)
    
def unregister():
    bpy.utils.unregister_class(save_pose)
    bpy.utils.unregister_class(PoseAnnotationPanel)

if __name__ == "__main__":
    register()
