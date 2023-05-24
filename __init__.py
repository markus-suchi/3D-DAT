import os
import shutil
import sys


def copy_startup_file(dirname, filename):
    # --- create the startup file ---
    script_file = os.path.abspath(__file__)
    addon_dir = os.path.dirname(script_file)

    addon_dir_link, _ = os.path.split(os.path.dirname(__file__))
    script_dir, _ = os.path.split(addon_dir_link)
    startup_dir = os.path.join(
        script_dir, 'startup', 'bl_app_templates_system')
    setup_gui_startup_dir = os.path.join(
        startup_dir, dirname)
    setup_gui_startup_file = os.path.join(
        setup_gui_startup_dir, 'startup.blend')
    setup_gui_startup_file_source = os.path.join(
        addon_dir, 'blender', filename)

    if os.path.exists(startup_dir):
        if not os.path.exists(setup_gui_startup_dir):
            os.mkdir(setup_gui_startup_dir)
        shutil.copyfile(setup_gui_startup_file_source,
                        setup_gui_startup_file)
    else:
        print(f"Startup dir {startup_dir} does not exist")



bl_info = {
    "author": "Markus Suchi",
    "name": "3D-DAT - Annotation Plugin",
    "description": "Tools for annotating RGBD-data",
    "warning": "",
    "version": (0, 1),
    "blender": (2, 92, 0), 
    "support": 'TESTING',
    "category": 'User Interface'
}

if "bpy" in locals():
    import importlib
    importlib.reload(v4r_annotation_tool)
    importlib.reload(v4r_dataset_toolkit)
    importlib.reload(cycle_cameras)
else:
    from . import v4r_dataset_toolkit as v4r
    from .blender import v4r_annotation_tool
    from .blender import cycle_cameras
    copy_startup_file('3D-DAT', '3D-DAT-single.blend')


#### REGISTER ###
def register():
    v4r_annotation_tool.register()
    cycle_cameras.register()

def unregister():
    v4r_annotation_tool.unregister()
    cycle_cameras.unregister()

if __name__ == "__main__":
    register()
