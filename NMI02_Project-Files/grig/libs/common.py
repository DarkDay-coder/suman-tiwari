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
        return False


def transfer_pivots(origin=False, sel=False):
    # if selection list is not defined, use selected in scene
    if not sel:
        sel = cmds.ls(selection=True)

    # move pivot to origin
    if origin:
        for s in sel:
            cmds.xform(s, worldSpace=True, pivots=(0, 0, 0))

    # move pivot to first selected object
    else:
        # get the rotate pivot
        first_piv = cmds.xform(sel[0], query=True, worldSpace=True,
                               rotatePivot=True)
        for s in sel[1:]:
            # set the rotate and scale pivot simultaneously
            cmds.xform(s, worldSpace=True, pivots=first_piv)


def freeze(nodes, apply=True, translate=True, rotate=True, scale=True,
           normal=False):
    cmds.makeIdentity(nodes, apply=apply, translate=translate,
                      rotate=rotate, scale=scale, normal=normal)

def get_bounding_box(nodes):
    x1, y1, z1, x2, y2, z2 = cmds.exactWorldBoundingBox(nodes,
                                                        calculateExactly=True)
    return x1, y1, z1, x2, y2, z2