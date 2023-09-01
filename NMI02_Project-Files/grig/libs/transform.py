import maya.cmds as cmds
from collections import OrderedDict

def match_pose(node, position=None, rotation=None, scale=None):
    if isinstance(position, list) or isinstance(position, tuple):
        if len(position) == 3:
            cmds.setAttr(node + '.translate', *position)
        else:
            cmds.error('Please provide X, Y, and Z translate coordinates.')
    elif not position:
        pass
    else:
        if cmds.objExists(position):
            src = cmds.xform(position,
                             query=True,
                             worldSpace=True,
                             translation=True)
            cmds.xform(node,
                       worldSpace=True,
                       translation=src)
        else:
            cmds.error('Input for position not valid. Please give ' +
                       'coordinates or an existing object.')

    if isinstance(rotation, list) or isinstance(rotation, tuple):
        if len(rotation) == 3:
            cmds.setAttr(node + '.rotate', *rotation)
        else:
            cmds.error('Please provide X, Y, and Z rotate coordinates.')
    elif not rotation:
        pass
    else:
        if cmds.objExists(rotation):
            src = cmds.xform(rotation,
                             query=True,
                             worldSpace=True,
                             rotation=True)
            cmds.xform(node,
                       worldSpace=True,
                       rotation=src)
        else:
            cmds.error('Input for rotation not valid. Please give ' +
                       'coordinates or an existing object.')

    if isinstance(scale, list) or isinstance(scale, tuple):
        if len(scale) == 3:
            cmds.setAttr(node + '.scale', *scale)
        else:
            cmds.error('Please provide X, Y, and Z scale coordinates.')
    elif not scale:
        pass
    else:
        if cmds.objExists(rotation):
            src = cmds.xform(rotation,
                             query=True,
                             worldSpace=True,
                             scale=True)
            cmds.xform(node,
                       worldSpace=True,
                       scale=src)
        else:
            cmds.error('Input for scale not valid. Please give ' +
                       'coordinates or an existing object.')


def read_pose(nodes):
    if not isinstance(nodes, list):
        nodes = [nodes]
    pose_dict = OrderedDict()

    for node in nodes:
        pose_dict[node] = cmds.xform(node,
                                     query=True,
                                     worldSpace=True,
                                     matrix=True)
        # pose_dict[node]['translate'] = cmds.xform(node,
        #                                           query=True,
        #                                           worldSpace=True,
        #                                           translation=True)
        # pose_dict[node]['rotate'] = cmds.xform(node,
        #                                        query=True,
        #                                        worldSpace=True,
        #                                        rotation=True)
        # pose_dict[node]['scale'] = cmds.xform(node,
        #                                       query=True,
        #                                       worldSpace=True,
        #                                       scale=True)
    return pose_dict


def set_pose(node, matrix):
    cmds.xform(node, worldSpace=True, matrix=matrix)


def find_position_on_curve(curve, u_value):
    pci = cmds.createNode('pointOnCurveInfo', name='tmp_pci')
    cmds.connectAttr(curve + 'Shape.worldSpace[0]', pci + '.inputCurve')
    cmds.setAttr(pci + '.turnOnPercentage', 1)
    cmds.setAttr(pci + '.parameter', u_value)
    pos = cmds.getAttr(pci + '.position')[0]
    cmds.delete(pci)
    return pos