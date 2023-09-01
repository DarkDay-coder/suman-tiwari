import maya.cmds as cmds

import nmrig.build.rigModule as nmModule
import nmrig.build.chain as nmChain
import nmrig.build.spline as nmSpline
import nmrig.libs.control.ctrl as nmCtrl
import nmrig.libs.attribute as nmAttr

# reload(nmModule)
# reload(nmChain)
reload(nmSpline)
# reload(nmCtrl)
# reload(nmAttr)


class Spine(nmModule.RigModule, nmSpline.Spline):
    def __init__(self,
                 side=None,
                 part=None,
                 guide_list=None,
                 ctrl_scale=None,
                 joint_num=5,
                 mid_ctrl=True,
                 local_ctrl=False,
                 stretchy=True,
                 aim_vector=(0, 1, 0),
                 up_vector=(0, 0, 1),
                 world_up_vector=(0, 0, 1),
                 fk_offset=False,
                 model_path=None,
                 guide_path=None):
        super(Spine, self).__init__(side=side, part=part,
                                    guide_list=guide_list,
                                    ctrl_scale=ctrl_scale,
                                    model_path=model_path,
                                    guide_path=guide_path)
        self.joint_num = joint_num
        self.mid_ctrl = mid_ctrl
        self.local_ctrl = local_ctrl
        self.stretchy = stretchy
        self.aim_vector = aim_vector
        self.up_vector = up_vector
        self.world_up_vector = world_up_vector
        self.fk_offset = fk_offset
        self.pad = len(str(self.joint_num)) + 1

        self.create_module()

    def create_module(self):
        super(Spine, self).create_module()

        # build spline curve
        self.build_spline_curve()
        self.control_rig()
        self.output_rig()
        self.skeleton()
        self.add_plugs()

    def control_rig(self):
        # create and parent controls
        self.build_spline_controls()

        # build fk controls
        fk_chain = nmChain.Chain(prefix=self.side,
                                 suffix='ctrl_JNT',
                                 name=self.part)
        fk_chain.create_from_curve(joint_num=4, curve=self.crv, stretch=None)

        self.fk_ctrl_list = []
        par = None
        for i, jnt in enumerate(fk_chain.joints[:-1]):
            name_list = [self.part, str(i + 1).zfill(2), 'FK']
            ctrl_name = '_'.join(name_list)
            if i == 0:
                shape = 'lever'
            else:
                shape = 'halfCylinder'
            fk_ctrl = nmCtrl.Control(parent=par,
                                     shape=shape,
                                     prefix=self.side,
                                     suffix='CTRL',
                                     name=ctrl_name,
                                     axis='y',
                                     group_type='main',
                                     rig_type='fk',
                                     position=jnt,
                                     rotation=jnt,
                                     ctrl_scale=self.ctrl_scale)
            self.attr_util.lock_and_hide(node=fk_ctrl.ctrl, translate=False,
                                         rotate=False)
            par = fk_ctrl.ctrl
            self.fk_ctrl_list.append(fk_ctrl)

        # clean up and organize
        cmds.delete(fk_chain.joints[0])
        cmds.parent(self.crv_ctrls, self.fk_ctrl_list[0].top, self.control_grp)

    def output_rig(self):
        # build spline joints
        self.build_spline_chain(scale_attr=self.global_scale)

        # build joints to bind the curve to
        c_jnt_grp = cmds.group(empty=True,
                               parent=self.module_grp,
                               name=self.base_name + '_curve_bind_JNT_GRP')
        base_jnt = cmds.joint(c_jnt_grp,
                              name=self.base_ctrl.ctrl.replace('CTRL', 'JNT'))
        tip_jnt = cmds.joint(c_jnt_grp,
                             name=self.tip_ctrl.ctrl.replace('CTRL', 'JNT'))

        cmds.matchTransform(base_jnt, self.spline_joints[0])
        cmds.matchTransform(tip_jnt, self.spline_joints[-1])
        cmds.parentConstraint(self.base_driver, base_jnt,
                              maintainOffset=True)
        cmds.parentConstraint(self.tip_driver, tip_jnt, maintainOffset=True)
        cmds.parentConstraint(self.fk_ctrl_list[-1].ctrl, self.tip_ctrl.top,
                              maintainOffset=True)

        if self.mid_ctrl:
            blend = nmAttr.Attribute(node=self.mid_ctrl.ctrl, type='double',
                                     value=1, min=0, max=1, keyable=True,
                                     name='blendBetween')

            mid_jnt = cmds.joint(c_jnt_grp,
                                 name=self.mid_ctrl.ctrl.replace('CTRL', 'JNT'))
            cmds.parentConstraint(self.mid_ctrl.ctrl, mid_jnt,
                                  maintainOffset=False)

            # blend locator between start and end
            mid_loc = cmds.spaceLocator(name=mid_jnt.replace('JNT', 'LOC'))[0]
            cmds.matchTransform(mid_loc, mid_jnt)
            cmds.pointConstraint(base_jnt, tip_jnt,
                                 mid_loc, maintainOffset=True)
            aim = cmds.aimConstraint(tip_jnt, mid_loc, aimVector=(0, 1, 0),
                                     upVector=(0, 0, 1),
                                     worldUpType='vector',
                                     worldUpVector=(0, 0, 1),
                                     maintainOffset=True)[0]
            b_vp = cmds.createNode('vectorProduct',
                                   name=base_jnt.replace('JNT', 'VP'))
            t_vp = cmds.createNode('vectorProduct',
                                   name=tip_jnt.replace('JNT', 'VP'))
            pma = cmds.createNode('plusMinusAverage',
                                  name=mid_jnt.replace('JNT', 'PMA'))
            rev = cmds.createNode('reverse',
                                  name=mid_jnt.replace('JNT', 'REV'))
            cmds.connectAttr(base_jnt + '.worldMatrix', b_vp + '.matrix')
            cmds.connectAttr(tip_jnt + '.worldMatrix', t_vp + '.matrix')
            cmds.connectAttr(b_vp + '.output', pma + '.input3D[0]')
            cmds.connectAttr(t_vp + '.output', pma + '.input3D[1]')
            cmds.connectAttr(pma + '.output3D', aim + '.worldUpVector')
            cmds.setAttr(b_vp + '.input1Z', 1)
            cmds.setAttr(t_vp + '.input1Z', 1)
            cmds.setAttr(b_vp + '.operation', 3)
            cmds.setAttr(t_vp + '.operation', 3)
            cmds.setAttr(pma + '.operation', 3)

            pac = cmds.parentConstraint(self.fk_ctrl_list[1].ctrl, mid_loc,
                                        self.mid_ctrl.top,
                                        maintainOffset=True)[0]
            wal = cmds.parentConstraint(pac, query=True, weightAliasList=True)
            cmds.connectAttr(blend.attr, rev + '.inputX')
            cmds.connectAttr(rev + '.outputX', pac + '.' + wal[0])
            cmds.connectAttr(blend.attr, pac + '.' + wal[1])

            cmds.parent(mid_loc, self.loc_grp)
            cmds.parent(self.loc_grp, self.module_grp)

        # bind curve to control joint
        bind_list = cmds.listRelatives(c_jnt_grp) + [self.crv]
        cmds.skinCluster(bind_list, toSelectedBones=True,
                         name=self.crv.replace('CRV', 'SKC'))

        # build spline ik handle
        self.build_spline_ikh()
        ikh_grp = cmds.group(self.spline_ikh, self.crv, parent=self.module_grp,
                             name=self.base_name + '_spline_IKH_GRP')
        cmds.setAttr(ikh_grp + '.inheritsTransform', 0)
        cmds.group(self.spline_joints[0], parent=self.module_grp,
                   name=self.base_name + '_driver_JNT_GRP')

        # setup advanced twist
        cmds.setAttr(self.spline_ikh + '.dTwistControlEnable', 1)
        cmds.setAttr(self.spline_ikh + '.dWorldUpType', 4)
        cmds.setAttr(self.spline_ikh + '.dForwardAxis', 2)
        cmds.setAttr(self.spline_ikh + '.dWorldUpAxis', 3)
        cmds.setAttr(self.spline_ikh + '.dTwistControlEnable', 1)
        cmds.setAttr(self.spline_ikh + '.dWorldUpVector', 0, 0, 1)
        cmds.setAttr(self.spline_ikh + '.dWorldUpVectorEnd', 0, 0, 1)
        cmds.connectAttr(base_jnt + '.worldMatrix[0]',
                         self.spline_ikh + '.dWorldUpMatrix')
        cmds.connectAttr(tip_jnt + '.worldMatrix[0]',
                         self.spline_ikh + '.dWorldUpMatrixEnd')

    def skeleton(self):
        spine_chain = nmChain.Chain(transform_list=self.spline_joints,
                                    prefix=self.side,
                                    suffix='JNT',
                                    name=self.part)
        spine_chain.create_from_transforms(parent=self.skel)
        self.bind_joints = spine_chain.joints

        self.tag_bind_joints(self.bind_joints[:-1])

    def add_plugs(self):
        # add skeleton plugs
        nmAttr.Attribute(node=self.part_grp, type='plug',
                         value=['Cn_hip_JNT'], name='skeletonPlugs',
                         children_name=[self.bind_joints[0]])

        # add parentConstraint rig plugs
        driver_list = ['Cn_hip_02_CTRL',
                       'Cn_hip_01_CTRL',
                       'Cn_chest_02_CTRL']
        driven_list = [self.base_name + '_base_CTRL_CNST_GRP',
                       self.base_name + '_01_FK_CTRL_CNST_GRP',
                       self.base_name + '_tip_CTRL_CNST_GRP']
        nmAttr.Attribute(node=self.part_grp, type='plug',
                         value=driver_list, name='pacRigPlugs',
                         children_name=driven_list)

        # add hide rig plugs
        hide_list = [self.base_name + '_base_CTRL_CNST_GRP',
                     self.base_name + '_tip_CTRL_CNST_GRP']
        nmAttr.Attribute(node=self.part_grp, type='plug',
                         value=[' '.join(hide_list)], name='hideRigPlugs',
                         children_name=['hideNodes'])
