"""
This is a collection of useful functions that can be called in a variety of
different scripts.
"""

import maya.cmds as cmds


def get_shapes(node):
    # list the shapes of node
    shape_list = cmds.listRelatives(node, shapes=True, noIntermediate=True)

    # make sure shapes were listed
    if not shape_list:
        # check if the node is a shape
        shape_list = cmds.ls(node, shapes=True)

    if shape_list:
        return shape_list
    else:
        return None


def get_transform(node):
    if node:
        if cmds.nodeType(node) == 'transform':
            transform = node
        else:
            transform = cmds.listRelatives(node, type='transform',
                                           parent=True)[0]
        return transform
    else:
        return None


def get_bounding_box(nodes):
    x1, y1, z1, x2, y2, z2 = cmds.exactWorldBoundingBox(nodes,
                                                        calculateExactly=True)
    return x1, y1, z1, x2, y2, z2