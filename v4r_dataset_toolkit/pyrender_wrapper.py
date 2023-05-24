# From https://github.com/marian42/mesh_to_sdf
# Marian Kleineberg

# Wrapper around the pyrender library that allows to
# 1. disable antialiasing
# 2. render a normal buffer
# This needs to be imported before pyrender or OpenGL is imported anywhere

import os
import sys
if 'pyrender' in sys.modules:
    raise ImportError(
        'The mesh_to_sdf package must be imported before pyrender is imported.')
if 'OpenGL' in sys.modules:
    raise ImportError(
        'The mesh_to_sdf package must be imported before OpenGL is imported.')

# Disable antialiasing:
import OpenGL.GL

suppress_multisampling = True
old_gl_enable = OpenGL.GL.glEnable


def new_gl_enable(value):
    if suppress_multisampling and value == OpenGL.GL.GL_MULTISAMPLE:
        OpenGL.GL.glDisable(value)
    else:
        old_gl_enable(value)


OpenGL.GL.glEnable = new_gl_enable

old_glRenderbufferStorageMultisample = OpenGL.GL.glRenderbufferStorageMultisample


def new_glRenderbufferStorageMultisample(target, samples, internalformat, width, height):
    if suppress_multisampling:
        OpenGL.GL.glRenderbufferStorage(target, internalformat, width, height)
    else:
        old_glRenderbufferStorageMultisample(
            target, samples, internalformat, width, height)


OpenGL.GL.glRenderbufferStorageMultisample = new_glRenderbufferStorageMultisample
