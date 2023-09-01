import maya.cmds as cmds

import nmrig.libs.attribute as nmAttr
import nmrig.build.chain as nmChain
import nmrig.libs.control.ctrl as nmCtrl
import nmrig.libs.transform as nmXform
reload(nmXform)
reload(nmChain)

class Spline:
    def __init__(self,
                 side=None,
                 part=None,
                 guide_list=None,
                 ctrl_scale=1,
                 joint_num=5,
                 mid_ctrl=True,
                 local_ctrl=False,
                 stretchy=True,
                 aim_vector=(0, 1, 0),
                 up_vector=(0, 0, 1),
                 world_up_vector=(0, 0, 1),
                 fk_offset=False):

        self.side = side
        self.part = part
        self.base_name = self.side + '_' + self.part

        self.guide_list = guide_list
        self.ctrl_scale = ctrl_scale
        self.joint_num = joint_num
        self.mid_ctrl = mid_ctrl
        self.local_ctrl = local_ctrl
        self.stretchy = stretchy
        self.aim_vector = aim_vector
        self.up_vector = up_vector
        self.world_up_vector = world_up_vector
        self.fk_offset = fk_offset

        if self.guide_list:
            if not isinstance(self.guide_list, list):
                self.guide_list = [self.guide_list]

    def build_spline(self):
        self.build_spline_curve()
        self.build_spline_controls()
        self.build_spline_chain()
        self.build_spline_ikh()

    def build_spline_controls(self):
        self.attr_util = nmAttr.Attribute(add=False)

        self.crv_ctrls = []
        # create controls
        self.base_ctrl = nmCtrl.Control(parent=None,
                                        shape='cube',
                                        prefix=self.side,
                                        suffix='CTRL',
                                        name=self.part + '_base',
                                        axis='y',
                                        group_type='main',
                                        rig_type='primary',
                                        position=self.guide_list[0],
                                        rotation=(0, 0, 0),
                                        ctrl_scale=self.ctrl_scale)
        self.attr_util.lock_and_hide(node=self.base_ctrl.ctrl, translate=False,
                                     rotate=False)
        self.crv_ctrls.append(self.base_ctrl.top)
        self.base_driver = self.base_ctrl.ctrl

        self.tip_ctrl = nmCtrl.Control(parent=None,
                                       shape='cube',
                                       prefix=self.side,
                                       suffix='CTRL',
                                       name=self.part + '_tip',
                                       axis='y',
                                       group_type='main',
                                       rig_type='primary',
                                       position=self.guide_list[-1],
                                       rotation=(0, 0, 0),
                                       ctrl_scale=self.ctrl_scale)
        self.attr_util.lock_and_hide(node=self.tip_ctrl.ctrl, translate=False,
                                     rotate=False)
        self.crv_ctrls.append(self.tip_ctrl.top)
        self.tip_driver = self.tip_ctrl.ctrl

        if self.local_ctrl:
            self.base_local = nmCtrl.Control(parent=self.base_ctrl.ctrl,
                                             shape='arrowFourWay',
                                             prefix=self.side,
                                             suffix='CTRL',
                                             name=self.part + '_base_local',
                                             axis='y',
                                             group_type='main',
                                             rig_type='secondary',
                                             position=self.guide_list[0],
                                             rotation=self.guide_list[0],
                                             ctrl_scale=self.ctrl_scale)
            self.attr_util.lock_and_hide(node=self.base_local.ctrl,
                                         translate=False,
                                         rotate=False)
            self.base_driver = self.base_local.ctrl

            self.tip_local = nmCtrl.Control(parent=self.tip_ctrl.ctrl,
                                            shape='arrowFourWay',
                                            prefix=self.side,
                                            suffix='CTRL',
                                            name=self.part + '_tip_local',
                                            axis='y',
                                            group_type='main',
                                            rig_type='secondary',
                                            position=self.guide_list[-1],
                                            rotation=self.guide_list[-1],
                                            ctrl_scale=self.ctrl_scale)
            self.attr_util.lock_and_hide(node=self.tip_local.ctrl,
                                         translate=False,
                                         rotate=False)
            self.tip_driver = self.tip_local.ctrl

        if self.mid_ctrl:
            pos = nmXform.find_position_on_curve(self.crv, 0.5)
            self.mid_ctrl = nmCtrl.Control(parent=None,
                                           shape='circle',
                                           prefix=self.side,
                                           suffix='CTRL',
                                           name=self.part + '_mid',
                                           axis='y',
                                           group_type='main',
                                           rig_type='primary',
                                           position=pos,
                                           rotation=(0, 0, 0),
                                           ctrl_scale=self.ctrl_scale)
            self.attr_util.lock_and_hide(node=self.mid_ctrl.ctrl,
                                         translate=False, rotate=False)
            self.crv_ctrls.append(self.mid_ctrl.top)

    def build_spline_curve(self):
        # build spline curve
        point_list = []
        for gde in self.guide_list:
            pos = cmds.xform(gde, query=True, worldSpace=True, translation=True)
            point_list.append(pos)

        tmp = cmds.curve(editPoint=point_list, degree=1,
                         name=self.base_name + '_tmp')
        self.crv, bs = cmds.fitBspline(tmp, constructionHistory=True,
                                       tolerance=0.01,
                                       name=self.base_name + '_CRV')

        cmds.delete(self.crv, constructionHistory=True)
        self.crv = cmds.rebuildCurve(self.crv,
                                     replaceOriginal=True,
                                     rebuildType=0,
                                     endKnots=1,
                                     keepRange=0,
                                     keepControlPoints=False,
                                     keepEndPoints=False,
                                     keepTangents=False,
                                     spans=4,
                                     degree=3)[0]
        cmds.delete(tmp)

    def build_spline_chain(self, scale_attr=None):
        if not scale_attr:
            scale_attr = nmAttr.Attribute(node=self.base_ctrl.ctrl,
                                          type='double', value=1, keyable=True,
                                          name='globalScale')

        # build spline chain
        self.spline_chain = nmChain.Chain(prefix=self.side,
                                          suffix='driver_JNT',
                                          name=self.part)
        self.spline_chain.create_from_curve(joint_num=self.joint_num,
                                            curve=self.crv,
                                            aim_vector=self.aim_vector,
                                            up_vector=self.up_vector,
                                            world_up_vector=self.world_up_vector,
                                            stretch=self.stretchy)
        self.spline_joints = self.spline_chain.joints

        if self.local_ctrl:
            cmds.matchTransform(self.base_local.top, self.spline_joints[0])
            cmds.matchTransform(self.tip_local.top, self.spline_joints[-1])

        if self.stretchy:
            stretch = nmAttr.Attribute(node=self.tip_ctrl.ctrl,
                                       type='double', value=1,
                                       min=0, max=1, keyable=True,
                                       name='stretch')

            self.loc_grp = cmds.group(empty=True,
                                      name=self.base_name + '_driver_LOC_GRP')
            inc = 1.0 / (self.joint_num - 1)
            par = None
            for i, jnt in enumerate(self.spline_joints):
                # create measure locators along curve
                pci = cmds.createNode('pointOnCurveInfo',
                                      name=jnt.replace('JNT', 'PCI'))
                loc = cmds.spaceLocator(name=jnt.replace('JNT', 'LOC'))[0]
                cmds.setAttr(pci + '.parameter', i * inc)
                cmds.connectAttr(self.crv + 'Shape.worldSpace[0]',
                                 pci + '.inputCurve')
                cmds.connectAttr(pci + '.position', loc + '.translate')
                cmds.setAttr(loc + '.inheritsTransform', 0)

                if par:
                    par_loc = cmds.listRelatives(self.loc_grp)[-1]
                    nmChain.stretch_segment(jnt=par, start=par_loc, end=loc,
                                            stretch_driver=stretch.attr,
                                            global_scale=scale_attr.attr)

                # define previous joint and use in the next iteration
                par = jnt
                cmds.parent(loc, self.loc_grp)

        if self.fk_offset:
            ctrl_par = None
            grp_par = None
            self.fk_offset_list = []
            for jnt in self.spline_joints:
                fk_name = jnt.replace(self.side + '_', '')
                fk_name = fk_name.replace('driver_JNT', 'fk_offset')
                fk_ctrl = nmCtrl.Control(parent=ctrl_par,
                                         shape='flagHalfCircle',
                                         prefix=self.side,
                                         suffix='CTRL',
                                         name=fk_name,
                                         axis='y',
                                         group_type='main',
                                         rig_type='fk',
                                         position=(0, 0, 0),
                                         rotation=(0, 0, 0),
                                         ctrl_scale=self.ctrl_scale)
                self.attr_util.lock_and_hide(node=fk_ctrl.ctrl, translate=False,
                                             rotate=False)
                self.fk_offset_list.append(fk_ctrl)
                cmds.setAttr(fk_ctrl.top + '.translate', 0, 0, 0)
                cmds.setAttr(fk_ctrl.top + '.rotate', 0, 0, 0)

                grp = cmds.group(empty=True, name=jnt.replace('driver_JNT',
                                                              'fk_offset_GRP'))
                pac = cmds.parentConstraint(jnt, grp, maintainOffset=False)[0]
                if grp_par:
                    cmds.parent(grp, grp_par)
                else:
                    self.offset_grp = grp
                cmds.connectAttr(pac + '.constraintTranslate',
                                 fk_ctrl.top + '.translate')
                cmds.connectAttr(pac + '.constraintRotate',
                                 fk_ctrl.top + '.rotate')

                ctrl_par = fk_ctrl.ctrl
                grp_par = grp

    def build_spline_ikh(self):
        self.spline_ikh = cmds.ikHandle(name=self.base_name + '_spline_IKH',
                                        startJoint=self.spline_joints[0],
                                        endEffector=self.spline_joints[-1],
                                        createCurve=False,
                                        curve=self.crv,
                                        solver='ikSplineSolver')[0]
