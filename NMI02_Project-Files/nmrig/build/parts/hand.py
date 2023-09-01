import maya.cmds as cmds

import nmrig.build.rigModule as nmModule
import nmrig.libs.control.ctrl as nmCtrl
import nmrig.build.chain as nmChain
import nmrig.libs.attribute as nmAttr


class Hand(nmModule.RigModule):
    def __init__(self,
                 side=None,
                 part=None,
                 guide_list=None,
                 ctrl_scale=None,
                 model_path=None,
                 guide_path=None):
        super(Hand, self).__init__(side=side, part=part,
                                   guide_list=guide_list,
                                   ctrl_scale=ctrl_scale,
                                   model_path=model_path,
                                   guide_path=guide_path)

        self.create_module()

    def create_module(self):
        super(Hand, self).create_module()

        self.control_rig()
        self.output_rig()
        self.skeleton()
        self.add_plugs()

    def control_rig(self):
        # create controls
        self.hand_01 = nmCtrl.Control(parent=self.control_grp,
                                      shape='cube',
                                      prefix=self.side,
                                      suffix='CTRL',
                                      name=self.part + '_01',
                                      axis='y',
                                      group_type='main',
                                      rig_type='primary',
                                      position=self.guide_list[0],
                                      rotation=(0, 0, 0),
                                      ctrl_scale=self.ctrl_scale)

        self.hand_02 = nmCtrl.Control(parent=self.hand_01.ctrl,
                                      shape='cube',
                                      prefix=self.side,
                                      suffix='CTRL',
                                      name=self.part + '_02',
                                      axis='y',
                                      group_type='main',
                                      rig_type='secondary',
                                      position=self.guide_list[0],
                                      rotation=(0, 0, 0),
                                      ctrl_scale=self.ctrl_scale * 0.85)

        self.hand_local = nmCtrl.Control(parent=self.hand_02.ctrl,
                                         shape='arrowFourWay',
                                         prefix=self.side,
                                         suffix='CTRL',
                                         name=self.part + '_local',
                                         axis='y',
                                         group_type='main',
                                         rig_type='secondary',
                                         position=self.guide_list[0],
                                         rotation=self.guide_list[0],
                                         ctrl_scale=self.ctrl_scale)

        self.hand_fk = nmCtrl.Control(parent=self.control_grp,
                                      shape='flagHalfCircle',
                                      prefix=self.side,
                                      suffix='CTRL',
                                      name=self.part + '_fk',
                                      axis='y',
                                      group_type='main',
                                      rig_type='fk',
                                      position=self.guide_list[0],
                                      rotation=self.guide_list[0],
                                      ctrl_scale=self.ctrl_scale)

    def output_rig(self):
        # create ik and fk hand joint
        ik_jnt = cmds.joint(self.hand_local.ctrl,
                            name=self.hand_01.ctrl.replace('CTRL', 'ik_JNT'))

        fk_jnt = cmds.joint(self.hand_fk.ctrl,
                            name=self.hand_fk.ctrl.replace('CTRL', 'JNT'))

        cmds.parentConstraint(self.hand_local.ctrl, ik_jnt, maintainOffset=True)
        cmds.parentConstraint(self.hand_fk.ctrl, fk_jnt, maintainOffset=True)
        cmds.connectAttr(self.hand_local.ctrl + '.scale', ik_jnt + '.scale')
        cmds.connectAttr(self.hand_fk.ctrl + '.scale', fk_jnt + '.scale')

        # create blend chain
        self.blend_chain = nmChain.Chain(transform_list=[ik_jnt],
                                         prefix=self.side,
                                         suffix='switch_JNT',
                                         name=self.part)

        self.blend_chain.create_blend_chain(switch_node=self.base_name,
                                            chain_a=[fk_jnt],
                                            chain_b=[ik_jnt],
                                            translate=False)
        cmds.setAttr(self.blend_chain.joints[0] + '.jointOrient', 0, 0, 0)

        # switch visibilities
        rev = cmds.createNode('reverse', name=self.base_name + '_REV')
        cmds.connectAttr(self.blend_chain.switch.attr, rev + '.inputX')
        cmds.connectAttr(rev + '.outputX', self.hand_01.top + '.visibility')

        # organize
        cmds.group(ik_jnt, fk_jnt, self.blend_chain.joints[0],
                   parent=self.module_grp, name=self.base_name + '_JNT_GRP')
        cmds.matchTransform(self.base_name + '_JNT_GRP', self.guide_list[0])

    def skeleton(self):
        jnt = cmds.joint(self.skel, name=self.base_name + '_JNT')
        cmds.parentConstraint(self.blend_chain.joints[0], jnt,
                              maintainOffset=False)
        cmds.connectAttr(self.blend_chain.joints[0] + '.scale', jnt + '.scale')
        self.bind_joints = [jnt]
        self.tag_bind_joints(self.bind_joints)

    def add_plugs(self):
        # add skeleton plugs
        nmAttr.Attribute(node=self.part_grp, type='plug',
                         value=['cmds.ls("' + self.side + '_arm_??_JNT")[-1]'],
                         name='skeletonPlugs',
                         children_name=[self.bind_joints[0]])

        # add parentConstraint rig plugs
        driver_list = [self.side + '_arm_03_switch_JNT',
                       self.side + '_clavicle_02_driver_JNT']
        driven_list = [self.base_name + '_fk_CTRL_CNST_GRP',
                       self.base_name + '_JNT_GRP']

        nmAttr.Attribute(node=self.part_grp, type='plug',
                         value=driver_list, name='pacRigPlugs',
                         children_name=driven_list)

        # add pointConstraint rig plugs
        driver_list = [self.side + '_arm_03_switch_JNT']
        driven_list = [self.base_name + '_01_switch_JNT']

        nmAttr.Attribute(node=self.part_grp, type='plug',
                         value=driver_list, name='pocRigPlugs',
                         children_name=driven_list)

        # add hide rig plugs
        hide_list = [self.side + '_hand_fk_CTRL_CNST_GRP']
        nmAttr.Attribute(node=self.part_grp, type='plug',
                         value=[' '.join(hide_list)], name='hideRigPlugs',
                         children_name=['hideNodes'])

        # add space plugs
        target_list = ['CHAR', 'Cn_global_CTRL', 'Cn_root_02_CTRL',
                       'Cn_hip_01_CTRL', 'Cn_chest_01_CTRL',
                       self.side + '_clavicle_CTRL', '2']
        name_list = ['world', 'global', 'root', 'hip', 'chest', 'clavicle',
                     'default_value']

        nmAttr.Attribute(node=self.part_grp, type='plug',
                         value=target_list,
                         name=self.hand_01.ctrl + '_parent',
                         children_name=name_list)

        # add switch plug
        switch_attr = self.side.lower() + 'ArmIKFK'
        nmAttr.Attribute(node=self.part_grp, type='plug',
                         value=[switch_attr], name='switchRigPlugs',
                         children_name=['ikFkSwitch'])
