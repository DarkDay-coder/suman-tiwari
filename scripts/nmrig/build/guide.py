import maya.cmds as cmds

import nmrig.libs.attribute as nmAttr
import nmrig.libs.maths as nmMath
reload(nmAttr)
reload(nmMath)


def create_pv_guide(guide_list=None,
                    name=None,
                    suffix=None,
                    slide_pv=None,
                    offset_pv=0,
                    delete_setup=None):
    if not guide_list:
        guide_list = cmds.ls(sl=True)

    if len(guide_list) != 3:
        cmds.error('Must select or define three transforms to use as guides.')

    if not suffix:
        suffix = 'guide'

    if not name:
        name = guide_list[0] + '_' + suffix

    # build pv guide groups
    guide_grp = cmds.group(empty=True, name=name + '_GRP')
    middle_grp = cmds.group(parent=guide_grp, empty=True,
                            name=name + '_middle_GRP')
    dnt_grp = cmds.group(parent=guide_grp, empty=True, name=name + '_DNT_GRP')
    cls_grp = cmds.group(parent=dnt_grp, empty=True, name=name + '_CLS_GRP')
    cmds.hide(dnt_grp)

    # define points of polygon from guides
    point_list = []
    for guide in guide_list:
        pos = cmds.xform(guide, query=True, worldSpace=True, translation=True)
        point_list.append(pos)

    # create polygon plane
    poly = cmds.polyCreateFacet(p=point_list, name=name + '_MSH',
                                constructionHistory=False)[0]

    # create clusters of the plane and constrain them to guides
    for i, vtx in enumerate(cmds.ls(poly + '.vtx[*]', flatten=True)):
        cls, handle = cmds.cluster(vtx, name='{}_{:02d}_CLS'.format(name, i))
        cmds.pointConstraint(guide_list[i], handle, maintainOffset=False)
        cmds.parent(handle, cls_grp)

    # create up vector locator
    upv_loc = cmds.spaceLocator(name=name + '_upV_LOC')[0]

    # constrain upV_LOC between the first and last guide
    upv_cnst = cmds.pointConstraint(guide_list[0], guide_list[-1], upv_loc,
                                    maintainOffset=False)[0]
    wal = cmds.pointConstraint(upv_cnst, query=True, weightAliasList=True)

    # constrain middle group to middle guide
    cmds.parentConstraint(guide_list[1], middle_grp, maintainOffset=False)

    # create nurbs plane
    nrb = cmds.nurbsPlane(pivot=(0, 0, 0),
                          axis=(0, 1, 0),
                          width=0.25,
                          lengthRatio=1,
                          degree=1,
                          patchesU=1,
                          patchesV=1,
                          constructionHistory=False,
                          name=name + '_NRB')[0]

    # hide the nurb shape
    surf = cmds.listRelatives(nrb, shapes=True)[0]
    cmds.hide(surf)

    cmds.matchTransform(nrb, guide_list[1])
    cmds.parent(nrb, middle_grp)

    # create normal constraint from poly to nurb
    cmds.normalConstraint(poly, nrb, weight=1, aimVector=(0, 0, 1),
                          upVector=(1, 0, 0), worldUpType='object',
                          worldUpObject=upv_loc)

    # create poleVector locator
    pv_loc = cmds.spaceLocator(name=name + '_LOC')[0]
    cmds.matchTransform(pv_loc, nrb)
    cmds.parent(pv_loc, nrb)

    # find slide value and give attributes to pv locator
    if slide_pv:
        slide_ratio = slide_pv
    else:
        a_len = nmMath.distance_between(point_a=guide_list[0],
                                        point_b=guide_list[1])
        b_len = nmMath.distance_between(point_a=guide_list[1],
                                        point_b=guide_list[2])
        total_len = a_len + b_len
        slide_ratio = float(b_len) / total_len

    offset = nmAttr.Attribute(node=pv_loc, type='double', value=offset_pv,
                              keyable=True, name='offset')
    slide = nmAttr.Attribute(node=pv_loc, type='double', min=0, max=1,
                             value=slide_ratio,
                             keyable=True, name='slide')

    # calculate distance between mid joint and upV
    dist = cmds.createNode('distanceBetween', name=name + '_DST')
    adl = cmds.createNode('addDoubleLinear', name=name + '_ADL')
    mdl = cmds.createNode('multDoubleLinear', name=name + '_MDL')
    rev = cmds.createNode('reverse', name=name + '_REV')

    cmds.connectAttr(upv_loc + '.worldMatrix[0]', dist + '.inMatrix1')
    cmds.connectAttr(guide_list[1] + '.worldMatrix[0]', dist + '.inMatrix2')
    cmds.connectAttr(dist + '.distance', adl + '.input1')
    cmds.connectAttr(offset.attr, adl + '.input2')
    cmds.connectAttr(adl + '.output', mdl + '.input1')
    cmds.setAttr(mdl + '.input2', -1)

    cmds.connectAttr(slide.attr, rev + '.inputX')
    cmds.connectAttr(slide.attr, upv_cnst + '.' + wal[0])
    cmds.connectAttr(rev + '.outputX', upv_cnst + '.' + wal[1])
    cmds.connectAttr(mdl + '.output', pv_loc + '.translateX')

    # create and organize guides lines
    ik_gde = create_line_guide(a=guide_list[0], b=guide_list[-1],
                               name=name + '_ik')
    pv_gde = create_line_guide(a=pv_loc, b=upv_loc, name=name + '_pv')

    cmds.parent(ik_gde['curve'], pv_gde['curve'], pv_loc)
    cmds.setAttr(ik_gde['curve'] + '.inheritsTransform', 0)
    cmds.setAttr(ik_gde['curve'] + '.translate', 0, 0, 0)
    cmds.setAttr(ik_gde['curve'] + '.rotate', 0, 0, 0)
    cmds.setAttr(pv_gde['curve'] + '.inheritsTransform', 0)
    cmds.setAttr(pv_gde['curve'] + '.translate', 0, 0, 0)
    cmds.setAttr(pv_gde['curve'] + '.rotate', 0, 0, 0)

    # cleanup
    cmds.parent(poly, upv_loc, ik_gde['clusters'], pv_gde['clusters'], dnt_grp)
    offset.lock_and_hide(node=pv_loc)

    if delete_setup:
        pv_guide = cmds.xform(pv_loc, query=True, worldSpace=True,
                              translation=True)
        cmds.delete(guide_grp)
        return pv_guide
    else:
        return pv_loc


def create_line_guide(a=None, b=None, name=None, suffix=None):
    if not a and not b:
        a, b = cmds.ls(sl=True)[0:2]

    if not suffix:
        suffix = 'GDE'
    if name:
        name = name + '_' + suffix
    else:
        name = '{}_to_{}_{}'.format(a, b, suffix)

    # start and end positions
    pos_a = cmds.xform(a, query=True, worldSpace=True, translation=True)
    pos_b = cmds.xform(b, query=True, worldSpace=True, translation=True)

    # create guide curve and rename shape
    crv = cmds.curve(ep=[pos_a, pos_b], degree=1, name=name)
    shp = cmds.listRelatives(crv, shapes=True)[0]
    shp = cmds.rename(shp, crv + 'Shape')

    # drawing options for curve
    cmds.setAttr(shp + '.overrideEnabled', 1)
    cmds.setAttr(shp + '.overrideDisplayType', 1)

    # create and constrain clusters to drive guide
    cls_a, handle_a = cmds.cluster(crv + '.cv[0]', name=crv + '_start_CLS')
    cls_b, handle_b = cmds.cluster(crv + '.cv[1]', name=crv + '_end_CLS')
    cmds.pointConstraint(a, handle_a, maintainOffset=False)
    cmds.pointConstraint(b, handle_b, maintainOffset=False)
    cmds.hide(handle_a, handle_b)

    return {'clusters': [handle_a, handle_b],
            'curve': crv}

