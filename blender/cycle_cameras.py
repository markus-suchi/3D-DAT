import bpy


class VIEW3D_OT_cycle_cameras(bpy.types.Operator):
    """Cycle through available cameras"""
    bl_idname = "view3d.cycle_cameras"
    bl_label = "Cycle Cameras"
    # bl_options = {}

    direction: bpy.props.EnumProperty(
        name="Direction",
        items=(
            ('FORWARD', "Forward", "Next camera"),
            ('BACKWARD', "Backward", "Previous camera"),
        ),
        default='FORWARD'
    )
    
    step: bpy.props.IntProperty(
        name="Step",
        default=1
    )

    @classmethod
    def poll(self, context):
        return (context.area.type == 'VIEW_3D' and 
                (bpy.data.collections.get('cameras') is not None))

    def execute(self, context):
        if(bpy.data.collections['cameras']):
            cameras = bpy.data.collections['cameras'].objects
            cam_objects = [ob for ob in cameras if ob.type == 'CAMERA']

            if len(cam_objects) == 0:
                return {'CANCELLED'}

            try:
                idx = cam_objects.index(context.area.spaces.active.camera)
                new_idx = (idx + self.step if self.direction ==
                           'FORWARD' else idx - self.step) % len(cam_objects)
            except ValueError:
                new_idx = 0

            current_camera = bpy.context.area.spaces.active.camera
            next_camera = cam_objects[new_idx]
            current_camera.hide_viewport = next_camera.hide_viewport
            bpy.context.area.spaces.active.camera = next_camera
            bpy.context.area.spaces.active.use_local_camera = True
            bpy.context.area.spaces.active.camera.hide_viewport = False
            return {'FINISHED'}
        else:
            return {'CANCELLED'}


addon_keymaps = []


def register():
    bpy.utils.register_class(VIEW3D_OT_cycle_cameras)

    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon

    if kc:
        km = wm.keyconfigs.addon.keymaps.new(
            name='3D View', space_type='VIEW_3D')
        kmi = km.keymap_items.new(
            VIEW3D_OT_cycle_cameras.bl_idname, 'RIGHT_ARROW', 'PRESS', ctrl=True, shift=True)
        kmi.properties.direction = 'FORWARD'
        addon_keymaps.append((km, kmi))

        kmi = km.keymap_items.new(
            VIEW3D_OT_cycle_cameras.bl_idname, 'LEFT_ARROW', 'PRESS', ctrl=True, shift=True)
        kmi.properties.direction = 'BACKWARD'
        addon_keymaps.append((km, kmi))

        kmi = km.keymap_items.new(
            VIEW3D_OT_cycle_cameras.bl_idname, 'WHEELDOWNMOUSE', 'PRESS', ctrl=False, shift=True)
        kmi.properties.direction = 'BACKWARD'
        addon_keymaps.append((km, kmi))
 
        kmi = km.keymap_items.new(
            VIEW3D_OT_cycle_cameras.bl_idname, 'WHEELUPMOUSE', 'PRESS', ctrl=False, shift=True)
        kmi.properties.direction = 'FORWARD'
        addon_keymaps.append((km, kmi))
 

def unregister():
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()
    bpy.utils.unregister_class(VIEW3D_OT_cycle_cameras)


# if __name__ == "__main__":
    # register()
