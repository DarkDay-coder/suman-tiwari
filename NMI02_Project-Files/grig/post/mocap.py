import maya.cmds as cmds


def build_mocap_rig(namespace=None):
    if namespace:
        ns = namespace + ':'
    else:
        ns = ''

    # main group for mocap setup
    rig_grp = cmds.group(ns + 'Hips', name='MOCAP_RIG_GRP')

    # build a list of all the controls intended to be driven by mocap
    cn_list = [ns + 'Cn_hip_01_CTRL',
                 ns + 'Cn_spine_01_FK_CTRL',
                 ns + 'Cn_spine_02_FK_CTRL',
                 ns + 'Cn_spine_03_FK_CTRL',
                 ns + 'Cn_chest_01_CTRL',
                 ns + 'Cn_neck_base_CTRL',
                 ns + 'Cn_head_01_CTRL']

    side_list = ['_clavicle_CTRL',
                 '_arm_01_fk_CTRL',
                 '_arm_02_fk_CTRL',
                 '_arm_03_fk_CTRL',
                 '_leg_01_fk_CTRL',
                 '_leg_02_fk_CTRL',
                 '_foot_01_fk_CTRL',
                 '_foot_02_fk_CTRL',
                 '_hand_01_CTRL',
                 '_arm_IK_pv_CTRL',
                 '_foot_01_CTRL',
                 '_leg_IK_pv_CTRL',
                 '_foot_toe_CTRL']

    finger_list = ['pinky', 'ring', 'middle', 'index', 'thumb']

    ctrl_list = []
    for ctrl in cn_list:
        if cmds.objExists(ctrl):
            ctrl_list.append(ctrl)
    for side in ['Lf', 'Rt']:
        for ctrl in side_list:
            if cmds.objExists(ns + side + ctrl):
                ctrl_list.append(ns + side + ctrl)
        for finger in finger_list:
            finger_ctrls = cmds.ls('{}{}_{}_*_fk_CTRL'.format(ns, side, finger))
            for fc in finger_ctrls:
                ctrl_list.append(fc)


    # offset group
    for ctrl in ctrl_list:
        loc = cmds.spaceLocator(name=ctrl + '_mocap_LOC')[0]
        grp = cmds.group(loc, name=loc + '_GRP')
        cmds.matchTransform(grp, ctrl)
        cmds.parent(grp, rig_grp)
        cmds.connectAttr(loc + '.t', ctrl + '_MOCAP_GRP.t')
        cmds.connectAttr(loc + '.r', ctrl + '_MOCAP_GRP.r')

    # drive rig with skeleton
    cmds.parentConstraint('Hips', ns + 'Cn_hip_01_CTRL_mocap_LOC', mo=True)
    orient_with_offset('Hips', ns + 'Cn_spine_01_FK_CTRL_mocap_LOC')
    orient_with_offset('Spine', ns + 'Cn_spine_02_FK_CTRL_mocap_LOC')
    orient_with_offset('Spine1', ns + 'Cn_spine_03_FK_CTRL_mocap_LOC')
    orient_with_offset('Spine2', ns + 'Cn_chest_01_CTRL_mocap_LOC')
    orient_with_offset('Neck', ns + 'Cn_neck_base_CTRL_mocap_LOC')
    orient_with_offset('Head', ns + 'Cn_head_01_CTRL_mocap_LOC')

    for long, short in zip(['Left', 'Right'], ['Lf', 'Rt']):
        sn = ns + short
        ln = ns + long
        cmds.setAttr(sn + '_arm_01_fk_CTRL.orientSpace', 2)
        orient_with_offset(ln + 'Shoulder', sn + '_clavicle_CTRL_mocap_LOC')
        orient_with_offset(ln + 'Arm', sn + '_arm_01_fk_CTRL_mocap_LOC', )
        orient_with_offset(ln + 'ForeArm', sn + '_arm_02_fk_CTRL_mocap_LOC')
        orient_with_offset(ln + 'Hand', sn + '_arm_03_fk_CTRL_mocap_LOC')
        orient_with_offset(ln + 'UpLeg', sn + '_leg_01_fk_CTRL_mocap_LOC', )
        orient_with_offset(ln + 'Leg', sn + '_leg_02_fk_CTRL_mocap_LOC')
        orient_with_offset(ln + 'Foot', sn + '_foot_01_fk_CTRL_mocap_LOC')
        orient_with_offset(ln + 'ToeBase', sn + '_foot_02_fk_CTRL_mocap_LOC')
        orient_with_offset(ln + 'ToeBase', sn + '_foot_toe_CTRL_mocap_LOC')
        parent_with_offset(ln + 'Hand', sn + '_hand_01_CTRL_mocap_LOC')
        parent_with_offset(ln + 'Arm', sn + '_arm_IK_pv_CTRL_mocap_LOC')
        parent_with_offset(ln + 'Foot', sn + '_foot_01_CTRL_mocap_LOC')
        parent_with_offset(ln + 'UpLeg', sn + '_leg_IK_pv_CTRL_mocap_LOC')
        for finger in finger_list:
            finger_ctrls = cmds.ls(
                '{}_{}_*_fk_CTRL_mocap_LOC'.format(sn, finger))
            for i, fc in enumerate(finger_ctrls):
                orient_with_offset('{}Hand{}{}'.format(ln,
                                                       finger.title(),
                                                       i + 1), fc)

def orient_with_offset(driver, driven):
    if cmds.objExists(driven):
        driver_par = driven.replace('mocap_LOC', 'CNST_GRP')
        driven_par = cmds.listRelatives(driven, parent=True)[0]
        cmds.parentConstraint(driver_par, driven_par, mo=True)
        cmds.orientConstraint(driver, driven, mo=True)

def parent_with_offset(driver, driven):
    if cmds.objExists(driven):
        cmds.parentConstraint(driver, driven, maintainOffset=True)


def align_skeletons(driver_namespace='Backflip', driven_namespace=None):
    # get driver and driven namespace
    if driver_namespace:
        dvr_ns = driver_namespace + ':'
    else:
        dvr_ns = ''

    if driven_namespace:
        dvn_ns = driven_namespace + ':'
    else:
        dvn_ns = ''

    # match hips and zero out animated driver skeleton
    cmds.matchTransform(dvr_ns + 'Hips', dvn_ns + 'Hips')
    for jnt in cmds.ls(dvr_ns + '*'):
        if cmds.nodeType(jnt) == 'joint':
            cmds.setAttr(jnt + '.rotate', 0, 0, 0)


def connect_to_mocap(driver_namespace='Backflip', driven_namespace=None):
    align_skeletons(driver_namespace, driven_namespace)

    # get driver and driven namespace
    if driver_namespace:
        dvr_ns = driver_namespace + ':'
    else:
        dvr_ns = ''

    if driven_namespace:
        dvn_ns = driven_namespace + ':'
    else:
        dvn_ns = ''

    # constrain guide skeleton to animated driver skeleton
    for jnt in cmds.ls(dvr_ns + '*'):
        if cmds.objExists(jnt.split(':')[1]):
            if 'Hips' in jnt:
                cmds.parentConstraint(jnt, dvn_ns + jnt.split(':')[1], mo=True)
            else:
                cmds.orientConstraint(jnt, dvn_ns + jnt.split(':')[1], mo=True)


def bake_to_controls(delete_rig=True):
    # get start and end frame for bake
    start_frame = cmds.playbackOptions(minTime=True, query=True)
    end_frame = cmds.playbackOptions(maxTime=True, query=True)

    bake_locs = []
    bake_grps = []
    # constraint a locator to each control
    for m_loc in cmds.ls('*_mocap_LOC', '*:*_mocap_LOC'):
        ctrl = m_loc.replace('_mocap_LOC', '')
        cnst_grp = ctrl + '_CNST_GRP'
        b_loc = cmds.spaceLocator(name=m_loc.replace('mocap_LOC', 'bake_LOC'))[
            0]
        b_grp = cmds.group(b_loc, name=b_loc + '_GRP')
        cmds.parentConstraint(cnst_grp, b_grp, mo=False)
        cmds.parentConstraint(ctrl, b_loc, mo=False)
        bake_locs.append(b_loc)
        bake_grps.append(b_grp)

    # bake locator animation
    cmds.bakeResults(bake_locs, time=(start_frame, end_frame))

    # transfer locator animation to control
    for b_loc in bake_locs:
        ctrl = b_loc.replace('_bake_LOC', '')
        mocap_grp = b_loc.replace('bake_LOC', 'MOCAP_GRP')

        # clear animation on control
        cmds.cutKey(ctrl)
        # copy animation from locator
        cmds.copyKey(b_loc)
        # paste locator anim to control
        cmds.pasteKey(ctrl)

        # disconnect and zero mocap group in rig
        con_list = cmds.listConnections(mocap_grp, destination=False,
                                        plugs=True)
        for con in con_list:
            attr = con.split('.')[1]
            cmds.disconnectAttr(con, mocap_grp + '.' + attr)
        cmds.setAttr(mocap_grp + '.translate', 0, 0, 0)
        cmds.setAttr(mocap_grp + '.rotate', 0, 0, 0)

    cmds.delete(bake_grps)

    if delete_rig:
        cmds.delete('MOCAP_RIG_GRP')