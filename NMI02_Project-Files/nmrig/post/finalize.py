import maya.cmds as cmds

import nmrig.libs.control.ctrl as nmCtrl
import nmrig.libs.attribute as nmAttr
import nmrig.libs.space as nmSpace
reload(nmAttr)

def get_control_types():
    type_dict = {}
    for x in cmds.ls('*.ctrlDict'):
        ctrl = nmCtrl.Control(ctrl=x.split('.')[0])
        if ctrl.rig_type in type_dict:
            type_dict[ctrl.rig_type].append(ctrl.ctrl)
        else:
            type_dict[ctrl.rig_type] = [ctrl.ctrl]

    return type_dict

def add_dislpay_type(node, value, name, target):
    dt = nmAttr.Attribute(node=node, type='enum', value=value,
                          enum_list=['Normal', 'Template', 'Reference'],
                          keyable=True, name=name)
    cmds.setAttr(target + '.overrideEnabled', 1)
    cmds.connectAttr(dt.attr, target + '.overrideDisplayType')


def add_color_attributes():
    attr_util = nmAttr.Attribute(add=False)
    type_dict = get_control_types()

    # add control info node
    if cmds.objExists('Cn_global_CTRL'):
        par = 'Cn_global_CTRL'
    else:
        par = 'RIG'

    c_ctrl = nmCtrl.Control(parent=par,
                            shape='brush3',
                            prefix=None,
                            suffix='CTRL',
                            name='color',
                            axis='y',
                            group_type=None,
                            rig_type='global')
    attr_util.lock_and_hide(node=c_ctrl.ctrl)

    # color control info shapes
    c_shapes = cmds.listRelatives(c_ctrl.ctrl, shapes=True)
    for shp in c_shapes:
        cmds.setAttr(shp + '.overrideEnabled', 1)
        cmds.setAttr(shp + '.overrideRGBColors', 1)
    cmds.setAttr(c_shapes[0] + '.overrideColorRGB', 1, 0, 0)
    cmds.setAttr(c_shapes[1] + '.overrideColorRGB', 0, 1, 0)
    cmds.setAttr(c_shapes[2] + '.overrideColorRGB', 0, 0, 1)

    # add color attribute and connect to control shapes
    for typ, ctrl_list in type_dict.items():
        nmAttr.Attribute(node=c_ctrl.ctrl, type='separator', name=typ)
        clr = nmAttr.Attribute(node=c_ctrl.ctrl, type='double3', value=0,
                               keyable=True, min=0, name=typ + 'Color',
                               children_name='RGB')
        for ctrl in ctrl_list:
            for shp in cmds.listRelatives(ctrl, shapes=True, type='nurbsCurve'):
                cmds.setAttr(shp + '.overrideEnabled', 1)
                cmds.setAttr(shp + '.overrideRGBColors', 1)
                cmds.connectAttr(clr.attr, shp + '.overrideColorRGB')

    set_color_defaults(c_ctrl.ctrl)


def set_color_defaults(ctrl_info):
    color_dict = {'gimbal': (0, 0.45, 0),
                  'root_01': (0, 1, 0),
                  'root_02': (0, 1, 0.1),
                  'global': (1, 0.25, 1),
                  'pivot': (1, 0.25, 0),
                  'primary': (1, 1, 0),
                  'bendy': (1, 0.2, 0.4),
                  'tangent': (0.85, 0.15, 0),
                  'offset': (0.75, 0, 0),
                  'pv': (0, 1, 1),
                  'fk': (0, 0, 1),
                  'secondary': (1, 0.2, 0.2),
                  'l_eye': (0.1, 0.1, 0.7),
                  'r_eye': (0.7, 0.1, 0.1),
                  'c_eye': (0.7, 0.7, 0.1)}

    for typ, val in color_dict.items():
        color_attr = '{}.{}Color'.format(ctrl_info, typ)
        if cmds.objExists(color_attr):
            cmds.setAttr(color_attr, *val)


def assemble_skeleton():
    for part in cmds.listRelatives('RIG'):
        if cmds.objExists(part + '.skeletonPlugs'):
            children = cmds.listAttr(part + '.skeletonPlugs')
            for child in children[1:]:
                plug = part + '.' + child
                par = cmds.getAttr(plug)
                if 'cmds.' in par:
                    par = eval(par)
                    cmds.setAttr(plug, par, type='string')
                if cmds.objExists(par):
                    cmds.parent(child, par)
                else:
                    cmds.warning(par + ' does not exist, skipping...')


def assemble_rig():
    for part in cmds.listRelatives('RIG'):
        # hide / remove nodes
        plug_types = ['hideRigPlugs',
                      'deleteRigPlugs']
        for pt in plug_types:
            if cmds.objExists(part + '.' + pt):
                driven_list = cmds.listAttr(part + '.' + pt)
                for driven in driven_list[1:]:
                    plug = part + '.' + driven
                    node_list = cmds.getAttr(plug)
                    if pt == 'hideRigPlugs':
                        cmds.hide(node_list.split(' '))
                    elif pt == 'deleteRigPlugs':
                        cmds.delete(node_list.split(' '))
                    else:
                        cmds.warning(pt, ' plug type not found, skipping...')

        # constrain nodes
        plug_types = ['pacRigPlugs',
                      'pacPocRigPlugs',
                      'pocRigPlugs',
                      'orcRigPlugs']
        for pt in plug_types:
            if cmds.objExists(part + '.' + pt):
                driven_list = cmds.listAttr(part + '.' + pt)
                for driven in driven_list[1:]:
                    plug = part + '.' + driven
                    driver = cmds.getAttr(plug)
                    if 'cmds.' in driver:
                        driver = eval(driver)
                        cmds.setAttr(plug, driver, type='string')
                    if cmds.objExists(driver):
                        if pt == 'pacRigPlugs':
                            cmds.parentConstraint(driver, driven,
                                                  maintainOffset=True)
                        elif pt == 'pacPocRigPlugs':
                            cmds.parentConstraint(driver, driven,
                                                  skipRotate=['x', 'y', 'z'],
                                                  maintainOffset=True)
                        elif pt == 'pocRigPlugs':
                            if '_point' in driven:
                                driven = driven.replace('_point', '')
                            cmds.pointConstraint(driver, driven,
                                                 maintainOffset=True)
                        elif pt == 'orcRigPlugs':
                            if '_orient' in driven:
                                driven = driven.replace('_orient', '')
                            cmds.orientConstraint(driver, driven,
                                                  maintainOffset=True)
                        else:
                            cmds.warning(pt,
                                         ' plug type not found, skipping...')
                    else:
                        cmds.warning(driver + ' does not exist, skipping...')

        # add space switching
        plug_types = ['parent',
                      'point',
                      'orient']

        for pt in plug_types:
            for ctrl in cmds.ls(part + '*.ctrlDict'):
                ctrl = ctrl.split('.')[0]
                attr_name = '{}.{}_{}'.format(part, ctrl, pt)
                if cmds.objExists(attr_name):
                    name_list = cmds.listAttr(attr_name)
                    driver = name_list[0].split('.')[0]
                    if cmds.objExists(part + '.' + driver):
                        driver = nmCtrl.Control(
                            ctrl=driver.replace('_' + pt, ''))
                        target_list = []
                        for name in name_list[1:]:
                            plug = part + '.' + name
                            target = cmds.getAttr(plug)
                            if 'cmds.' in target:
                                target = eval(target)
                                cmds.setAttr(plug, target, type='string')
                            target_list.append(target)

                        value = int(target_list[-1])
                        name_list = [n.replace(pt, '').lower() for n in
                                     name_list[1:-1]]
                        if all(cmds.objExists(ob) for ob in target_list[:-1]):
                            nmSpace.space_switch(node=driver.top,
                                                 driver=driver.ctrl,
                                                 target_list=target_list[:-1],
                                                 name_list=name_list,
                                                 name=pt + 'Space',
                                                 constraint_type=pt,
                                                 value=value)

        # transfer attributes
        if cmds.objExists(part + '.transferAttributes'):
            driven_list = cmds.listAttr(part + '.transferAttributes')
            for driven in driven_list[1:]:
                plug = part + '.' + driven
                transfer_node = cmds.getAttr(plug)
                attr_list = cmds.listAttr(driven, userDefined=True)
                for attr in attr_list:
                    if attr != 'ctrlDict':
                        src_attr = nmAttr.Attribute(add=False,
                                                    node=driven,
                                                    name=attr,
                                                    transfer_to=transfer_node)
                        src_attr.transfer_attr()

            
def add_vis_ctrl():
    attr_util = nmAttr.Attribute(add=False)

    # add control info node
    if cmds.objExists('Cn_global_CTRL'):
        par = 'Cn_global_CTRL'
    else:
        par = 'RIG'

    v_ctrl = nmCtrl.Control(parent=par,
                            shape='v',
                            prefix=None,
                            suffix='CTRL',
                            name='visibility',
                            axis='y',
                            group_type=None,
                            rig_type='global')
    attr_util.lock_and_hide(node=v_ctrl.ctrl)

    # color control info shapes
    c_shapes = cmds.listRelatives(v_ctrl.ctrl, shapes=True)
    for shp in c_shapes:
        cmds.setAttr(shp + '.overrideEnabled', 1)
        cmds.setAttr(shp + '.overrideRGBColors', 1)
    cmds.setAttr(c_shapes[0] + '.overrideColorRGB', 0.1, 0.2, 0.8)

    # add default attributes
    model_vis = nmAttr.Attribute(node=v_ctrl.ctrl, type='bool', value=1,
                                 keyable=True, name='modelVis')
    skel_vis = nmAttr.Attribute(node=v_ctrl.ctrl, type='bool', value=0,
                                keyable=True, name='skelVis')
    rig_vis = nmAttr.Attribute(node=v_ctrl.ctrl, type='bool', value=0,
                               keyable=True, name='rigVis')

    # add display type separator
    nmAttr.Attribute(node=v_ctrl.ctrl, type='separator', value=0,
                     name='displayType')

    # connect model_vis
    cmds.connectAttr(model_vis.attr, 'model_GRP.visibility')
    add_dislpay_type(node=v_ctrl.ctrl, value=2, name='modelDisplay',
                     target='model_GRP')

    # connect skel_vis
    cmds.connectAttr(skel_vis.attr, 'SKEL.visibility')
    add_dislpay_type(node=v_ctrl.ctrl, value=2, name='skelDisplay',
                     target='SKEL')

    # connect rig_vis
    for m in cmds.ls('*_MODULE'):
        cmds.connectAttr(rig_vis.attr, m + '.visibility')

    # add part vis separator
    nmAttr.Attribute(node=v_ctrl.ctrl, type='separator', value=0,
                     name='partVis')

    # connect ctrl_vis to all modules
    part_dict = {}
    for c in cmds.ls('*_CONTROL'):
        side = c.split('_')[0]
        part = c.split('_')[1]
        if part in part_dict:
            part_dict[part].append(side)
        else:
            part_dict[part] = [side]

    for part, sides in part_dict.items():
        p_vis = nmAttr.Attribute(node=v_ctrl.ctrl, type='bool', value=1,
                                 keyable=True, name=part + 'Vis')
        for side in sides:
            cmds.connectAttr(p_vis.attr,
                             '{}_{}_CONTROL.visibility'.format(side, part))

    # add type vis separator
    type_dict = get_control_types()
    nmAttr.Attribute(node=v_ctrl.ctrl, type='separator', value=0,
                     name='controlType')
    for typ, ctrl_list in type_dict.items():
        t_vis = nmAttr.Attribute(node=v_ctrl.ctrl, type='bool', value=1,
                                 keyable=True, name=typ + 'Vis')
        for ctrl in ctrl_list:
            c_shapes = cmds.listRelatives(ctrl, shapes=True, path=True)
            for shp in c_shapes:
                if cmds.nodeType(shp) == 'nurbsCurve':
                    cmds.connectAttr(t_vis.attr, shp + '.visibility')
                    

def add_global_scale(global_ctrl='Cn_global_CTRL'):
    gs_list = cmds.ls('*.globalScale')
    gs = nmAttr.Attribute(node=global_ctrl, type='double', value=1,
                          keyable=True, min=0.001, name='globalScale')
    cmds.connectAttr(gs.attr, 'SKEL.sx')
    cmds.connectAttr(gs.attr, 'SKEL.sy')
    cmds.connectAttr(gs.attr, 'SKEL.sz')
    cmds.connectAttr(gs.attr, global_ctrl + '.sx')
    cmds.connectAttr(gs.attr, global_ctrl + '.sy')
    cmds.connectAttr(gs.attr, global_ctrl + '.sz')
    gs.lock_and_hide(translate=False, rotate=False)

    for ps in gs_list:
        part = ps.split('.')[0]
        cmds.connectAttr(gs.attr, ps)
        cmds.connectAttr(ps, part + '.sx')
        cmds.connectAttr(ps, part + '.sy')
        cmds.connectAttr(ps, part + '.sz')


def add_rig_sets():
    rig_set = cmds.sets(name='rig_SET', empty=True)
    ctrl_set = cmds.sets(name='control_SET', empty=True)
    cache_set = cmds.sets(name='cache_SET', empty=True)
    cmds.sets(ctrl_set, add=rig_set)
    cmds.sets(cache_set, add=rig_set)

    for part in cmds.listRelatives('RIG'):
        part_set = cmds.sets(cmds.ls(part + '*_CTRL'), name=part + '_SET')
        cmds.sets(part_set, add=ctrl_set)

    cmds.sets('model_GRP', add=cache_set)
    

def add_switch_ctrl():
    attr_util = nmAttr.Attribute(add=False)

    # switch control
    if cmds.objExists('Cn_global_CTRL'):
        par = 'Cn_global_CTRL'
    else:
        par = 'RIG'

    s_ctrl = nmCtrl.Control(parent=par,
                            shape='switch',
                            prefix=None,
                            suffix='CTRL',
                            name='switch',
                            axis='y',
                            group_type=None,
                            rig_type='global')
    attr_util.lock_and_hide(node=s_ctrl.ctrl)

    # color shapes
    c_shapes = cmds.listRelatives(s_ctrl.ctrl, shapes=True)
    for shp in c_shapes:
        cmds.setAttr(shp + '.overrideEnabled', 1)
        cmds.setAttr(shp + '.overrideRGBColors', 1)
    cmds.setAttr(c_shapes[0] + '.overrideColorRGB', 1.0, 0.15, 0.25)
    cmds.setAttr(c_shapes[1] + '.overrideColorRGB', 0.0, 0.8, 0.8)

    # build and connect switch attributes
    for part in cmds.listRelatives('RIG'):
        if cmds.objExists(part + '.switchRigPlugs'):
            switch_name = cmds.getAttr(part + '.ikFkSwitch')
            if cmds.objExists(s_ctrl.ctrl + '.' + switch_name):
                switch_attr = nmAttr.Attribute(node=s_ctrl.ctrl,
                                               name=switch_name,
                                               add=False)
            else:
                switch_attr = nmAttr.Attribute(node=s_ctrl.ctrl, type='double',
                                               value=0, keyable=True, min=0,
                                               max=1, name=switch_name)
            cmds.connectAttr(switch_attr.attr, part + '.switch')


def finalize_rig(vis_ctrl=True, color_ctrl=True, switch_ctrl=True,
                 constrain_model=False):
    if color_ctrl:
        add_color_attributes()
    if switch_ctrl:
        add_switch_ctrl()
    if vis_ctrl:
        add_vis_ctrl()
    assemble_skeleton()
    assemble_rig()
    add_global_scale()
    add_rig_sets()

    if constrain_model:
        if cmds.objExists('Cn_root_JNT'):
            cmds.parentConstraint('Cn_root_JNT', 'model_GRP',
                                  maintainOffset=True)
            cmds.scaleConstraint('Cn_root_JNT', 'model_GRP',
                                 maintainOffset=True)