import maya.cmds as cmds

import grig.libs.attribute as gnAttr
reload(gnAttr)


def space_switch(node,
                 driver,
                 target_list=[],
                 name_list=[],
                 name='space',
                 constraint_type='parent',
                 value=0):
    node_split = node.split('_')
    base_name = node_split[0] + '_' + node_split[1]

    if constraint_type != 'parent':
        loc_grp = cmds.group(empty=True, parent=base_name + '_MODULE',
                             name=base_name + '_' + name + '_GRP')
        targets = []
        for target in target_list:
            target_name = base_name + '_' + target + '_LOC'
            if cmds.objExists(target_name):
                targets.append(target_name)
            else:
                loc = cmds.spaceLocator(name=target_name)[0]
                cmds.matchTransform(loc, node)
                cmds.parent(loc, loc_grp)
                cmds.parentConstraint(target, loc, maintainOffset=True)
                targets.append(loc)
        if not cmds.listRelatives(loc_grp):
            cmds.delete(loc_grp)
    else:
        targets = target_list

    if constraint_type == 'parent':
        cnst = cmds.parentConstraint(targets, node, maintainOffset=True)[0]
        wal = cmds.parentConstraint(cnst, query=True, weightAliasList=True)
    elif constraint_type == 'orient':
        cnst = cmds.orientConstraint(targets, node, maintainOffset=True)[0]
        wal = cmds.orientConstraint(cnst, query=True, weightAliasList=True)
    elif constraint_type == 'point':
        cnst = cmds.pointConstraint(targets, node, maintainOffset=True)[0]
        wal = cmds.pointConstraint(cnst, query=True, weightAliasList=True)
    else:
        cmds.error('constraint_type supports only parent, orient, or point.')

    space = gnAttr.Attribute(node=driver, type='enum', value=value,
                             enum_list=name_list, keyable=True, name=name)


    for i in range(len(targets)):
        if i > 0:
            cmds.setDrivenKeyframe(cnst + '.' + wal[i - 1],
                                   currentDriver=space.attr,
                                   driverValue=i,
                                   value=0)

        cmds.setDrivenKeyframe(cnst + '.' + wal[i],
                               currentDriver=space.attr,
                               driverValue=i,
                               value=1)

        if i <= len(target_list) - 2:
            cmds.setDrivenKeyframe(cnst + '.' + wal[i + 1],
                                   currentDriver=space.attr,
                                   driverValue=i,
                                   value=0)