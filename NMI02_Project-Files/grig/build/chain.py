import maya.cmds as cmds

import grig.libs.control.ctrl as gnCtrl
import grig.libs.common as gnCommon
import grig.libs.group as gnGroup
import grig.libs.attribute as gnAttr
import grig.libs.transform as gnXform
import grig.libs.maths as gnMath
reload(gnCtrl)
reload(gnCommon)
reload(gnGroup)
reload(gnAttr)
reload(gnXform)
reload(gnMath)


class Chain:
    def __init__(self,
                 transform_list=None,
                 label_chain=True,
                 prefix='Lf',
                 suffix='JNT',
                 name='default'):
        self.transform_list = transform_list
        self.label_chain = label_chain
        self.prefix = prefix
        self.suffix = suffix
        self.name = name
        self.split_jnt_dict = None

    def create_from_curve(self, joint_num=5, curve=None, aim_vector=(0, 1, 0),
                          up_vector=(0, 0, 1), world_up_vector=(0, 0, 1),
                          stretch=None):
        if not curve:
            cmds.error('Please provide a curve to build joints along.')
        self.joints = []

        pad = len(str(joint_num)) + 1
        inc = 1.0 / (joint_num - 1)
        par = None
        for i in range(joint_num):
            # name and pad the joints
            name_list = [self.prefix, self.name, str(i + 1).zfill(pad),
                         self.suffix]
            jnt_name = '_'.join(name_list)

            # create joint and parent for next iteration
            jnt = cmds.joint(None, name=jnt_name)

            # find position on curve to create joints
            pos = gnXform.find_position_on_curve(curve, i * inc)
            cmds.setAttr(jnt + '.translate', *pos)

            # aim joint at parent
            if par:
                aim = cmds.aimConstraint(jnt, par, aimVector=aim_vector,
                                         upVector=up_vector,
                                         worldUpType='vector',
                                         worldUpVector=world_up_vector)
                cmds.delete(aim)
                cmds.parent(jnt, par)

            par = jnt
            self.joints.append(jnt)

        # freeze joint chain and zero end joint orient
        cmds.makeIdentity(self.joints[0], rotate=True, apply=True)
        cmds.setAttr(self.joints[-1] + '.jointOrient', 0, 0, 0)

        if self.label_chain:
            self.label_side(self.joints)

    def create_from_transforms(self,
                               parent_constraint=True,
                               orient_constraint=False,
                               point_constraint=False,
                               scale_constraint=False,
                               connect_scale=True,
                               parent=False,
                               static=False,
                               pad='auto'):
        pose_dict = gnXform.read_pose(self.transform_list)
        if pad == 'auto':
            pad = len(str(len(self.transform_list))) + 1
        if not pad:
            if len(self.transform_list) > 1:
                cmds.error('Must use padding to avoid name clashes on chains ' +
                           'with more than one joint.')

        self.joints = []
        for i, pose in enumerate(pose_dict):
            if pad:
                name_list = [self.prefix, self.name,
                             str(i + 1).zfill(pad), self.suffix]
            else:
                name_list = [self.prefix, self.name, self.suffix]
            jnt_name = '_'.join(name_list)

            if i == 0:
                jnt = cmds.joint(None, name=jnt_name)
                p_jnt = jnt
            else:
                jnt = cmds.joint(p_jnt, name=jnt_name)
                p_jnt = jnt

            gnXform.set_pose(jnt, pose_dict[pose])
            self.joints.append(jnt)

        if parent:
            cmds.parent(self.joints[0], parent)

        gnCommon.freeze(self.joints[0])

        if not static:
            if point_constraint or orient_constraint:
                parent_constraint = False

            self.constraints = []
            for src, jnt in zip(pose_dict, self.joints):
                if parent_constraint:
                    pac = cmds.parentConstraint(src, jnt, mo=True)[0]
                    self.constraints.append(pac)
                elif orient_constraint and point_constraint:
                    orc = cmds.orientConstraint(src, jnt, mo=True)[0]
                    poc = cmds.pointConstraint(src, jnt, mo=True)[0]
                    self.constraints.append(orc)
                    self.constraints.append(poc)
                elif orient_constraint:
                    orc = cmds.orientConstraint(src, jnt, mo=True)[0]
                    self.constraints.append(orc)
                elif point_constraint:
                    poc = cmds.pointConstraint(src, jnt, mo=True)[0]
                    self.constraints.append(poc)
                else:
                    cmds.connectAttr(src + '.translate', jnt + '.translate')
                    cmds.connectAttr(src + '.rotate', jnt + '.rotate')

                if scale_constraint:
                    scc = cmds.scaleConstraint(src, jnt, mo=True)[0]
                    self.constraints.append(scc)
                else:
                    if connect_scale:
                        cmds.connectAttr(src + '.scale', jnt + '.scale')

        self.get_chain_lengths()

        if self.label_chain:
            self.label_side(self.joints)

    def label_side(self, chain):
        for jnt in chain:
            if any(self.prefix[0] == side for side in ['C', 'c']):
                cmds.setAttr(jnt + '.side', 0)
            elif any(self.prefix[0] == side for side in ['L', 'l']):
                cmds.setAttr(jnt + '.side', 1)
            elif any(self.prefix[0] == side for side in ['R', 'r']):
                cmds.setAttr(jnt + '.side', 2)
            else:
                cmds.setAttr(jnt + '.side', 3)

    def create_blend_chain(self,
                           switch_node,
                           chain_a,
                           chain_b,
                           translate=True,
                           rotate=True,
                           scale=True):
        self.create_from_transforms(static=True)

        self.switch = gnAttr.Attribute(node=switch_node, type='double', min=0,
                                       max=1, value=0, keyable=True,
                                       name='switch')

        i = 0
        for a, b in zip(chain_a, chain_b):
            bcn_name = self.joints[i].replace(self.suffix, '')
            if translate:
                bcn = cmds.createNode('blendColors',
                                      name=bcn_name + 'trans_BCN')
                cmds.connectAttr(a + '.t', bcn + '.color1')
                cmds.connectAttr(b + '.t', bcn + '.color2')
                cmds.connectAttr(bcn + '.output', self.joints[i] + '.t')
                cmds.connectAttr(self.switch.attr, bcn + '.blender')
            if rotate:
                bcn = cmds.createNode('blendColors',
                                        name=bcn_name + 'rot_BCN')
                cmds.connectAttr(a + '.r', bcn + '.color1')
                cmds.connectAttr(b + '.r', bcn + '.color2')
                cmds.connectAttr(bcn + '.output', self.joints[i] + '.r')
                cmds.connectAttr(self.switch.attr, bcn + '.blender')
            if scale:
                bcn = cmds.createNode('blendColors',
                                      name=bcn_name + 'scale_BCN')
                cmds.connectAttr(a + '.s', bcn + '.color1')
                cmds.connectAttr(b + '.s', bcn + '.color2')
                cmds.connectAttr(bcn + '.output', self.joints[i] + '.s')
                cmds.connectAttr(self.switch.attr, bcn + '.blender')

            i += 1

    def create_src_chain(self, parent):
        self.src_list = []
        for j in self.transform_list:
            if j == self.transform_list[0]:
                par = parent
            else:
                par = src
            src = cmds.group(em=True,
                             name=j.replace(self.suffix, 'SRC'),
                             parent=par)

            cmds.parentConstraint(j, src, mo=False)
            cmds.scaleConstraint(j, src, mo=False)
            self.src_list.append(src)

    def get_chain_lengths(self):
        self.bone_lengths = []

        for i in range(len(self.joints) - 1):
            jnt_a = self.joints[i]
            jnt_b = self.joints[i + 1]

            bone_len = gnMath.distance_between(point_a=jnt_a, point_b=jnt_b)
            self.bone_lengths.append(bone_len)

        self.chain_length = sum(self.bone_lengths)

    def split_chain(self, segments=4):
        self.split_jnt_dict = {}
        for bone in self.joints[0:-1]:
            split_jnts = self.split_bone(bone=bone, segments=segments)
            self.split_jnt_dict[bone] = split_jnts

    def split_bone(self, bone=None, segments=4):
        pad = len(str(segments)) + 1

        # find the start and end joint positions
        end_jnt = cmds.listRelatives(bone, children=True, type='joint')
        s = cmds.xform(bone, query=True, worldSpace=True, translation=True)
        e = cmds.xform(end_jnt, query=True, worldSpace=True, translation=True)

        split_jnts = []
        n = segments
        for i in range(1, n + 1):
            name_list = [bone.replace('_' + self.suffix, ''), 'seg',
                         str(i).zfill(pad), self.suffix]
            seg_name = '_'.join(name_list)
            seg_jnt = cmds.joint(bone, name=seg_name)
            if i > 1:
                # find the position of our joint segment
                seg_pos = [s[axis] + ((i-1) * ((e[axis] - s[axis]) / n)) for
                           axis in range(3)]
                cmds.xform(seg_jnt, ws=True, t=seg_pos)
            split_jnts.append(seg_jnt)

        return split_jnts

    def twist_chain(self,
                    start_translate,
                    start_rotate,
                    end_translate,
                    end_rotate,
                    twist_bone,
                    twist_driver,
                    reverse=False):
        # load quatNodes if not already loaded
        if not cmds.pluginInfo('quatNodes', query=True, loaded=True):
            cmds.loadPlugin('quatNodes')

        twist_name = twist_bone.replace('_JNT', '')
        twist_loc = cmds.spaceLocator(name=twist_name + '_twist_LOC')[0]
        driver_loc = cmds.spaceLocator(name=twist_name + '_twist_driver_LOC')[0]
        cmds.hide(twist_loc, driver_loc)

        # move twist locator to twist driver position and twist bone orientation
        cmds.matchTransform(twist_loc, start_translate,
                            rotation=False, position=True)
        cmds.matchTransform(twist_loc, start_rotate,
                            rotation=True, position=False)
        cmds.parent(twist_loc, twist_bone)

        # match driver_loc position to twist_loc and parent it under driver node
        cmds.matchTransform(driver_loc, end_translate,
                            rotation=False, position=True)
        cmds.matchTransform(driver_loc, end_rotate,
                            rotation=True, position=False)
        cmds.parent(driver_loc, twist_driver)

        # create the matrix and euler node to drive twist_loc
        mult = cmds.createNode('multMatrix', name=twist_name + '_MMX')
        dcm = cmds.createNode('decomposeMatrix', name=twist_name + '_DCM')
        qte = cmds.createNode('quatToEuler', name=twist_name + '_QTE')

        cmds.connectAttr(driver_loc + '.worldMatrix[0]', mult + '.matrixIn[0]')
        cmds.connectAttr(twist_loc + '.parentInverseMatrix[0]',
                         mult + '.matrixIn[1]')
        cmds.connectAttr(mult + '.matrixSum', dcm + '.inputMatrix')
        cmds.connectAttr(dcm + '.outputQuatY', qte + '.inputQuatY')
        cmds.connectAttr(dcm + '.outputQuatW', qte + '.inputQuatW')
        cmds.connectAttr(qte + '.outputRotateY', twist_loc + '.rotateY')
        cmds.setAttr(qte + '.inputRotateOrder', 1)

        ti = 1 / float(len(self.split_jnt_dict[twist_bone]))
        t_val = ti
        for jnt in self.split_jnt_dict[twist_bone]:
            twist_percent = t_val - ti
            if reverse:
                twist_percent = 1 - twist_percent
            mdl = cmds.createNode('multDoubleLinear', name=jnt + '_twist_MDL')
            cmds.connectAttr(twist_loc + '.rotateY', mdl + '.input1')
            cmds.setAttr(mdl + '.input2', twist_percent)
            cmds.connectAttr(mdl + '.output', jnt + '.rotateY')
            t_val += ti

    def bend_chain(self, bone, ctrl_scale, spans=16, mirror=False,
                   global_scale=None):
        #cmds.warning('USE STRETCH SEGMENT.....!')
        if mirror:
            mirror = -1
        else:
            mirror = 1
        seg_jnt_list = self.split_jnt_dict[bone]
        # find end joint of bone
        end_jnt = cmds.listRelatives(bone, type='joint')
        end_jnt = [ej for ej in end_jnt if ej not in seg_jnt_list][0]

        # start and end joint positions
        s = cmds.xform(bone, q=True, ws=True, t=True)
        e = cmds.xform(end_jnt, q=True, ws=True, t=True)
        m = [(s[axis] + e[axis]) / float(2) for axis in range(3)]

        # build points for bezier curve
        pos_list = [s]
        for i in range(1, 6):
            pos = [s[axis] + (i * ((e[axis] - s[axis]) / 6)) for axis in
                   range(3)]
            pos_list.append(pos)
        pos_list.append(e)
        b_crv = cmds.curve(point=pos_list, degree=3, bezier=True,
                           knot=[0, 0, 0, 1, 1, 1, 2, 2, 2])
        b_crv = cmds.rename(b_crv, bone.replace('JNT', 'bezier_CRV'))

        # build joint driver curve and wire it to the bezier curve
        j_crv = cmds.curve(editPoint=[s, e], degree=1)
        j_crv = cmds.rename(j_crv, bone.replace('JNT', 'bend_CRV'))
        cmds.rebuildCurve(j_crv,
                          replaceOriginal=True,
                          rebuildType=0,
                          endKnots=1,
                          keepRange=0,
                          keepControlPoints=False,
                          keepEndPoints=False,
                          keepTangents=False,
                          spans=spans,
                          degree=3)

        loc_list = []
        seg_inc = 1 / float(len(seg_jnt_list))
        for i, jnt in enumerate(seg_jnt_list):
            if jnt != seg_jnt_list[-1]:
                next_jnt = seg_jnt_list[i + 1]
            else:
                next_jnt = end_jnt

            # connect joint to curve
            loc = cmds.spaceLocator(n=jnt.replace('JNT', 'pose_LOC'))[0]
            pci = cmds.createNode('pointOnCurveInfo',
                                  name=jnt.replace('JNT', 'PCI'))
            cmds.connectAttr(j_crv + 'Shape.worldSpace[0]',
                             pci + '.inputCurve')
            cmds.connectAttr(pci + '.position', loc + '.translate')
            cmds.setAttr(pci + '.parameter', seg_inc * i)
            cmds.pointConstraint(loc, jnt)

            # aim at the next joint
            cmds.setAttr(jnt + '.rotateOrder', 1)
            cmds.aimConstraint(next_jnt, jnt, aimVector=(0, 1 * mirror, 0),
                               upVector=(0, 0, 1), worldUpType='none', skip='y')
            loc_list.append(loc)

        # create the stretch per joint
        for i, jnt in enumerate(seg_jnt_list):
            if jnt != seg_jnt_list[-1]:
                next_loc = loc_list[i + 1]
            else:
                next_loc = end_jnt
            dist = cmds.createNode('distanceBetween',
                                   name=jnt.replace('JNT', 'DST'))
            mdn = cmds.createNode('multiplyDivide',
                                  name=jnt.replace('JNT', 'MDN'))
            cmds.setAttr(mdn + '.operation', 2)
            cmds.connectAttr(loc_list[i] + '.worldMatrix[0]',
                             dist + '.inMatrix1')
            cmds.connectAttr(next_loc + '.worldMatrix[0]',
                             dist + '.inMatrix2')
            cmds.connectAttr(dist + '.distance', mdn + '.input1X')
            d = cmds.getAttr(dist + '.distance')

            if global_scale:
                mdl = cmds.createNode('multDoubleLinear',
                                      name=jnt.replace('JNT', 'MDL'))
                cmds.connectAttr(global_scale, mdl + '.input1')
                cmds.connectAttr(mdl + '.output', mdn + '.input2X')
                cmds.setAttr(mdl + '.input2', d)
            else:
                cmds.setAttr(mdn + '.input2X', d)
            cmds.connectAttr(mdn + '.outputX', jnt + '.scaleY')

        # organize
        rig_grp = cmds.group(b_crv, j_crv, loc_list,
                             name=bone.replace('JNT', 'bendy_rig_GRP'))
        ctrl_grp = cmds.group(empty=True, name=bone.replace('JNT', 'CTRL_GRP'))
        cmds.matchTransform(ctrl_grp, bone)
        cmds.hide(rig_grp)

        # do not inherit transforms on bendy groups
        cmds.setAttr(rig_grp + '.inheritsTransform', 0)
        cmds.setAttr(ctrl_grp + '.inheritsTransform', 0)

        # drive control group with decompose matrix of bone
        dcm = cmds.createNode('decomposeMatrix', name=bone.replace('JNT', 'DCM'))
        cmds.connectAttr(bone + '.worldMatrix[0]', dcm + '.inputMatrix')
        for attr in ['translate', 'rotate', 'scale']:
            cmds.connectAttr(dcm + '.output' + attr.capitalize(),
                             ctrl_grp + '.' + attr)

        attr_util = gnAttr.Attribute(add=False)
        # build controls for bend system
        mid_ctrl = gnCtrl.Control(parent=ctrl_grp,
                                  shape='circle',
                                  prefix=None,
                                  suffix='CTRL',
                                  name=bone.replace('JNT', 'bendy'),
                                  axis='y',
                                  group_type='main',
                                  rig_type='bendy',
                                  position=m,
                                  rotation=bone,
                                  ctrl_scale=ctrl_scale * 0.8)
        s_tan = gnCtrl.Control(parent=ctrl_grp,
                               shape='square',
                               prefix=None,
                               suffix='CTRL',
                               name=bone.replace('JNT', 'start_tangent'),
                               axis='y',
                               group_type=2,
                               rig_type='tangent',
                               position=b_crv + '.cv[1]',
                               rotation=bone,
                               ctrl_scale=ctrl_scale * 0.6)
        e_tan = gnCtrl.Control(parent=ctrl_grp,
                               shape='square',
                               prefix=None,
                               suffix='CTRL',
                               name=bone.replace('JNT', 'end_tangent'),
                               axis='y',
                               group_type=2,
                               rig_type='tangent',
                               position=b_crv + '.cv[5]',
                               rotation=bone,
                               ctrl_scale=ctrl_scale * 0.6)

        # lock and hide attributes on controls
        attr_util.lock_and_hide(node=mid_ctrl.ctrl,
                                translate=False,
                                rotate=False,
                                scale='XZ')
        attr_util.lock_and_hide(node=s_tan.ctrl,
                                translate=False)
        attr_util.lock_and_hide(node=e_tan.ctrl,
                                translate=False)

        # add attributes to drive curvature and tangent visibility
        curvature = gnAttr.Attribute(node=mid_ctrl.ctrl, type='double', value=1,
                                     min=0.001, max=3, keyable=True,
                                     name='curvature')
        tangent_vis = gnAttr.Attribute(node=mid_ctrl.ctrl, type='bool',
                                       value=False, keyable=True,
                                       name='tangentVisibility')
        cmds.connectAttr(tangent_vis.attr, s_tan.top + '.visibility')
        cmds.connectAttr(tangent_vis.attr, e_tan.top + '.visibility')

        # move group pivots to start and end pose
        cmds.xform(mid_ctrl.top, worldSpace=True, pivots=s)
        cmds.xform(s_tan.top, worldSpace=True, pivots=s)
        cmds.xform(e_tan.top, worldSpace=True, pivots=e)
        cmds.xform(s_tan.control_dict['rig_groups'][0], worldSpace=True,
                   pivots=s)
        cmds.xform(e_tan.control_dict['rig_groups'][0], worldSpace=True,
                   pivots=e)

        # deform the curves
        cmds.wire(j_crv, wire=b_crv,
                  dropoffDistance=[0, 5000], crossingEffect=0, localInfluence=0,
                  name=j_crv + '_wire')

        # create clusters to control curve
        # start
        cmds.cluster(b_crv + '.cv[0]', bindState=True,
                     weightedNode=(bone, bone), name=b_crv + '_start_CLS')
        # start tangent
        cmds.cluster(b_crv + '.cv[1]', bindState=True,
                     weightedNode=(s_tan.ctrl, s_tan.ctrl),
                     name=b_crv + '_start_tangent_CLS')
        # mid
        cmds.cluster(b_crv + '.cv[2:4]', bindState=True,
                     weightedNode=(mid_ctrl.ctrl, mid_ctrl.ctrl),
                     name=b_crv + '_mid_CLS')
        # end tangent
        cmds.cluster(b_crv + '.cv[5]', bindState=True,
                     weightedNode=(e_tan.ctrl, e_tan.ctrl),
                     name=b_crv + '_end_tangent_CLS')
        # end
        cmds.cluster(b_crv + '.cv[6]', bindState=True,
                     weightedNode=(bone, bone), name=b_crv + '_end_CLS')


        # create wire base clusters to nullify curvature deformation
        sb_cls = cmds.cluster(b_crv + 'BaseWire.cv[1]',
                              name=b_crv + '_base_start_CLS')[1]
        eb_cls = cmds.cluster(b_crv + 'BaseWire.cv[5]',
                              name=b_crv + '_base_end_CLS')[1]
        cmds.xform(sb_cls, worldSpace=True, pivots=s)
        cmds.xform(eb_cls, worldSpace=True, pivots=e)
        cmds.parent(sb_cls, eb_cls, rig_grp)

        # connect curvature attributes
        for axis in 'xyz':
            cmds.connectAttr(curvature.attr, sb_cls + '.s' + axis)
            cmds.connectAttr(curvature.attr, eb_cls + '.s' + axis)
        cmds.connectAttr(curvature.attr, s_tan.top + '.sy')
        cmds.connectAttr(curvature.attr, e_tan.top + '.sy')

        return {'control': ctrl_grp,
                'module': rig_grp}


def stretch_segment(jnt, start, end,
                    stretch_driver=None,
                    global_scale=None):
    dist = cmds.createNode('distanceBetween',
                           name=jnt.replace('JNT', 'DST'))
    mdn = cmds.createNode('multiplyDivide',
                          name=jnt.replace('JNT', 'MDN'))
    cmds.setAttr(mdn + '.operation', 2)
    cmds.connectAttr(start + '.worldMatrix[0]',
                     dist + '.inMatrix1')
    cmds.connectAttr(end + '.worldMatrix[0]',
                     dist + '.inMatrix2')
    cmds.connectAttr(dist + '.distance', mdn + '.input1X')
    d = cmds.getAttr(dist + '.distance')

    if global_scale:
        mdl = cmds.createNode('multDoubleLinear',
                              name=jnt.replace('JNT', 'MDL'))
        cmds.connectAttr(global_scale, mdl + '.input1')
        cmds.connectAttr(mdl + '.output', mdn + '.input2X')
        cmds.setAttr(mdl + '.input2', d)
    else:
        cmds.setAttr(mdn + '.input2X', d)

    if stretch_driver:
        bta = cmds.createNode('blendTwoAttr',
                              name=jnt.replace('JNT', 'BTA'))
        cmds.setAttr(bta + '.input[0]', 1)
        cmds.connectAttr(mdn + '.outputX', bta + '.input[1]')
        cmds.connectAttr(stretch_driver, bta + '.attributesBlender')
        cmds.connectAttr(bta + '.output', jnt + '.scaleY')
    else:
        cmds.connectAttr(mdn + '.outputX', jnt + '.scaleY')