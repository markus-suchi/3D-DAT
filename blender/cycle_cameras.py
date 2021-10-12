import bpy
bl_info = {
    "name": "Cycle Cameras",
    "author": "CoDEmanX",
    "version": (1, 0),
    "blender": (2, 80, 0),
    "location": "View3D > Ctrl + Shift + Left/Right Arrow",
    "description": "Switch scene camera to next or previous camera object",
    "warning": "",
    "wiki_url": "",
    "category": "3D View"}


class VIEW3D_OT_cycle_cameras(bpy.types.Operator):
    """Cycle through available cameras"""
    bl_idname = "view3d.cycle_cameras"
    bl_label = "Cycle Cameras"
    bl_options = {'REGISTER', 'UNDO'}

    direction: bpy.props.EnumProperty(
        name="Direction",
        items=(
            ('FORWARD', "Forward", "Next camera (alphabetically)"),
            ('BACKWARD', "Backward", "Previous camera (alphabetically)"),
        ),
        default='FORWARD'
    )

    def execute(self, context):
        if(bpy.data.collections['cameras']):
            cameras = bpy.data.collections['cameras'].objects
            cam_objects = [ob for ob in cameras if ob.type == 'CAMERA']

            if len(cam_objects) == 0:
                print("CANCELLED")
                return {'CANCELLED'}

            try:
                idx = cam_objects.index(context.scene.camera)
                new_idx = (idx + 1 if self.direction ==
                           'FORWARD' else idx - 1) % len(cam_objects)
            except ValueError:
                new_idx = 0

            bpy.context.area.spaces.active.camera = cam_objects[new_idx]
            bpy.context.area.spaces.active.use_local_camera = True
            context.scene.camera = cam_objects[new_idx]
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


def unregister():
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()
    bpy.utils.unregister_class(VIEW3D_OT_cycle_cameras)


# if __name__ == "__main__":
    # register()
