import maya.cmds as cmds

import nmrig.build.rigModule as nmModule
import nmrig.build.chain as nmChain
import nmrig.libs.attribute as nmAttr
import nmrig.libs.control.ctrl as nmCtrl
import nmrig.build.ik as nmIk
import nmrig.build.fk as nmFk


class Foot(nmModule.RigModule):
    def __init__(self,
                 side=None,
                 part=None,
                 guide_list=None,
                 ctrl_scale=None,
                 model_path=None,
                 guide_path=None,
                 in_piv=None,
                 out_piv=None,
                 heel_piv=None,
                 toe_piv=None):
        super(Foot, self).__init__(side=side, part=part,
                                   guide_list=guide_list,
                                   ctrl_scale=ctrl_scale,
                                   model_path=model_path,
                                   guide_path=guide_path)

        self.in_piv = in_piv
        self.out_piv = out_piv
        self.heel_piv = heel_piv
        self.toe_piv = toe_piv

        if not self.toe_piv:
            self.toe_piv = self.guide_list[-1]

        self.create_module()

    def create_module(self):
        super(Foot, self).create_module()

        self.control_rig()
        self.output_rig()
        self.skeleton()
        #self.add_plugs()

    def control_rig(self):
        # create controls
        attr_util = nmAttr.Attribute(add=False)

        # main and secondary IK controls
        self.main_ctrl = nmCtrl.Control(parent=self.control_grp,
                                        shape='cube',
                                        prefix=self.side,
                                        suffix='CTRL',
                                        name=self.part + '_01',
                                        axis='y',
                                        group_type='main',
                                        rig_type='primary',
                                        position=self.guide_list[0],
                                        ctrl_scale=self.ctrl_scale)
        self.second_ctrl = nmCtrl.Control(parent=self.main_ctrl.ctrl,
                                          shape='cube',
                                          prefix=self.side,
                                          suffix='CTRL',
                                          name=self.part + '_02',
                                          axis='y',
                                          group_type='main',
                                          rig_type='secondary',
                                          position=self.guide_list[0],
                                          ctrl_scale=self.ctrl_scale * 0.85)

        # controls for banking and toe/ball/heel roll
        self.toe_piv = nmCtrl.Control(parent=self.second_ctrl.ctrl,
                                      shape='cube',
                                      prefix=self.side,
                                      suffix='CTRL',
                                      name=self.part + '_toe_piv',
                                      axis='y',
                                      group_type='main',
                                      rig_type='pivot',
                                      position=self.toe_piv,
                                      rotation=self.guide_list[-1],
                                      ctrl_scale=self.ctrl_scale * 0.2)
        self.heel_piv = nmCtrl.Control(parent=self.toe_piv.ctrl,
                                       shape='cube',
                                       prefix=self.side,
                                       suffix='CTRL',
                                       name=self.part + '_heel_piv',
                                       axis='y',
                                       group_type='main',
                                       rig_type='pivot',
                                       position=self.heel_piv,
                                       ctrl_scale=self.ctrl_scale * 0.2)
        self.in_piv = nmCtrl.Control(parent=self.heel_piv.ctrl,
                                     shape='cube',
                                     prefix=self.side,
                                     suffix='CTRL',
                                     name=self.part + '_in_piv',
                                     axis='y',
                                     group_type='main',
                                     rig_type='pivot',
                                     position=self.in_piv,
                                     ctrl_scale=self.ctrl_scale * 0.2)
        self.out_piv = nmCtrl.Control(parent=self.in_piv.ctrl,
                                      shape='cube',
                                      prefix=self.side,
                                      suffix='CTRL',
                                      name=self.part + '_out_piv',
                                      axis='y',
                                      group_type='main',
                                      rig_type='pivot',
                                      position=self.out_piv,
                                      ctrl_scale=self.ctrl_scale * 0.2)

        # control for ball roll
        self.ball_ctrl = nmCtrl.Control(parent=self.out_piv.ctrl,
                                        shape='flagHalfSquare',
                                        prefix=self.side,
                                        suffix='CTRL',
                                        name=self.part + '_ball',
                                        axis='y',
                                        group_type='main',
                                        rig_type='primary',
                                        position=self.guide_list[1],
                                        rotation=self.guide_list[1],
                                        ctrl_scale=self.ctrl_scale * 1.45)

        # control for ankle
        self.ankle_ctrl = nmCtrl.Control(parent=self.ball_ctrl.ctrl,
                                         shape='sphere',
                                         prefix=self.side,
                                         suffix='CTRL',
                                         name=self.part + '_ankle',
                                         axis='y',
                                         group_type='main',
                                         rig_type='secondary',
                                         position=self.guide_list[0],
                                         rotation=self.guide_list[0],
                                         ctrl_scale=self.ctrl_scale)

        # control for toe wiggle
        self.toe_ctrl = nmCtrl.Control(parent=self.out_piv.ctrl,
                                       shape='flagHalfCircle',
                                       prefix=self.side,
                                       suffix='CTRL',
                                       name=self.part + '_toe',
                                       axis='y',
                                       group_type='main',
                                       rig_type='secondary',
                                       position=self.guide_list[1],
                                       rotation=self.guide_list[1],
                                       ctrl_scale=self.ctrl_scale)

        ts_list = [self.ball_ctrl, self.toe_ctrl, self.toe_piv, self.heel_piv,
                   self.in_piv, self.out_piv]
        for c in ts_list:
            attr_util.lock_and_hide(node=c.ctrl, rotate=False)

        s_list = [self.main_ctrl, self.second_ctrl]
        for c in s_list:
            attr_util.lock_and_hide(node=c.ctrl, translate=False, rotate=False)

    def output_rig(self):
        # build ankle/ball IK
        sc = nmIk.Ik(side=self.side,
                     part=self.part,
                     guide_list=[self.guide_list[0], self.guide_list[1]],
                     solver='ikSCsolver')
        sc.build_ik_chain()
        sc.build_ikh(constrain=False)
        cmds.setAttr(sc.ik_joints[-1] + '.jointOrient', 0, 0, 0)

        # build toe chain
        toe_chain = nmChain.Chain(transform_list=[self.guide_list[1],
                                                  self.guide_list[2]],
                                  prefix=self.side,
                                  suffix='toe_JNT',
                                  name=self.part)
        toe_chain.create_from_transforms(parent=self.module_grp, static=True)

        # group sc chain and move pivot to the ball of foot
        sc_grp = cmds.group(empty=True, parent=self.module_grp,
                            name=sc.ikh + '_GRP')
        cmds.matchTransform(sc_grp, sc.ik_joints[-1])
        cmds.parent(sc.ik_joints[0], sc.ikh, sc_grp)

        # aim sc group at ankle control and point it to the ball joint
        cmds.aimConstraint(self.ankle_ctrl.ctrl, sc_grp, aimVector=(0, -1, 0),
                           upVector=(0, 0, 1), worldUpType='objectrotation',
                           worldUpObject=self.ankle_ctrl.ctrl,
                           worldUpVector=(0, 0, 1), maintainOffset=True)
        cmds.pointConstraint(self.ball_ctrl.ctrl, sc_grp, maintainOffset=True)
        cmds.parentConstraint(self.toe_ctrl.ctrl, toe_chain.joints[0],
                              maintainOffset=True)

        # build fk controls and chain
        fk = nmFk.Fk(side=self.side,
                     part=self.part,
                     guide_list=self.guide_list,
                     gimbal=False,
                     offset=False,
                     pad='auto',
                     ctrl_scale=self.ctrl_scale,
                     fk_shape='flagHalfCircle')
        fk.build_fk()
        cmds.parent(fk.fk_joints[0], self.module_grp)
        cmds.parent(fk.fk_ctrls[0].top, self.control_grp)

        ik_chain = nmChain.Chain(transform_list=[sc.ik_joints[0],
                                                 toe_chain.joints[0],
                                                 toe_chain.joints[1]],
                                 prefix=self.side,
                                 suffix='ik_JNT',
                                 name=self.part)
        ik_chain.create_from_transforms(parent=self.module_grp)

        # create blend chain
        self.blend_chain = nmChain.Chain(transform_list=fk.fk_joints,
                                         prefix=self.side,
                                         suffix='switch_JNT',
                                         name=self.part)

        self.blend_chain.create_blend_chain(switch_node=self.base_name,
                                            chain_a=fk.fk_joints,
                                            chain_b=ik_chain.joints)
        cmds.parent(self.blend_chain.joints[0], self.module_grp)

        self.add_foot_attributes()

        # vis switch
        rev = cmds.createNode('reverse', name=self.base_name + '_REV')
        cmds.connectAttr(self.blend_chain.switch.attr, rev + '.inputX')
        cmds.connectAttr(self.blend_chain.switch.attr,
                         fk.fk_ctrls[0].top + '.visibility')
        cmds.connectAttr(rev + '.outputX', self.main_ctrl.top + '.visibility')

    def add_foot_attributes(self):
        nmAttr.Attribute(node=self.main_ctrl.ctrl,
                         type='separator', name='______')

        roll = nmAttr.Attribute(node=self.main_ctrl.ctrl, type='double',
                                value=0, keyable=True, name='roll')
        roll_max = nmAttr.Attribute(node=self.main_ctrl.ctrl, type='double',
                                    value=30, min=0, keyable=True,
                                    name='rollMax')
        toe_roll = nmAttr.Attribute(node=self.main_ctrl.ctrl, type='double',
                                    value=0, keyable=True, name='toeRoll')
        heel_roll = nmAttr.Attribute(node=self.main_ctrl.ctrl, type='double',
                                     value=0, keyable=True, name='heelRoll')
        bank = nmAttr.Attribute(node=self.main_ctrl.ctrl, type='double',
                                value=0, keyable=True, name='bank')

        # create nodes to drive foot
        roll_cnd = cmds.createNode('condition',
                                   name=self.base_name + '_roll_CND')
        roll_pma = cmds.createNode('plusMinusAverage',
                                   name=self.base_name + '_roll_PMA')
        ball_mdl = cmds.createNode('multDoubleLinear',
                                   name=self.base_name + '_ball_MDL')
        toe_mdl = cmds.createNode('multDoubleLinear',
                                  name=self.base_name + '_toe_MDL')
        toe_adl = cmds.createNode('addDoubleLinear',
                                  name=self.base_name + '_toe_ADL')
        bank_cnd = cmds.createNode('condition',
                                   name=self.base_name + '_bank_CND')

        # set node states
        cmds.setAttr(ball_mdl + '.input2', -1)
        cmds.setAttr(toe_mdl + '.input2', -1)
        cmds.setAttr(roll_cnd + '.operation', 4)
        cmds.setAttr(roll_pma + '.operation', 2)
        cmds.setAttr(bank_cnd + '.operation', 2)
        cmds.setAttr(bank_cnd + '.colorIfFalseG', 0)

        # connect attributes and nodes for roll
        cmds.connectAttr(roll.attr, roll_cnd + '.firstTerm')
        cmds.connectAttr(roll.attr, roll_cnd + '.colorIfTrueR')
        cmds.connectAttr(roll.attr, roll_pma + '.input1D[0]')
        cmds.connectAttr(roll_max.attr, roll_cnd + '.secondTerm')
        cmds.connectAttr(roll_max.attr, roll_cnd + '.colorIfFalseR')
        cmds.connectAttr(roll_max.attr, roll_pma + '.input1D[1]')
        cmds.connectAttr(roll_pma + '.output1D', roll_cnd + '.colorIfFalseG')
        cmds.connectAttr(roll_cnd + '.outColorR', ball_mdl + '.input1')
        cmds.connectAttr(roll_cnd + '.outColorG', toe_adl + '.input1')
        cmds.connectAttr(toe_roll.attr, toe_adl + '.input2')
        cmds.connectAttr(toe_adl + '.output', toe_mdl + '.input1')

        # for bank
        cmds.connectAttr(bank.attr, bank_cnd + '.firstTerm')
        cmds.connectAttr(bank.attr, bank_cnd + '.colorIfFalseR')
        cmds.connectAttr(bank.attr, bank_cnd + '.colorIfTrueG')

        # drive groups
        cmds.connectAttr(ball_mdl + '.output',
                         self.ball_ctrl.group_list[1] + '.rotateX')
        cmds.connectAttr(toe_mdl + '.output',
                         self.toe_piv.group_list[1] + '.rotateX')
        cmds.connectAttr(heel_roll.attr,
                         self.heel_piv.group_list[1] + '.rotateX')
        if self.side == 'Lf':
            cmds.connectAttr(bank_cnd + '.outColorR',
                             self.out_piv.group_list[1] + '.rotateZ')
            cmds.connectAttr(bank_cnd + '.outColorG',
                             self.in_piv.group_list[1] + '.rotateZ')
        else:
            cmds.setAttr(bank_cnd + '.operation', 4)
            in_mdl = cmds.createNode('multDoubleLinear',
                                     name=self.base_name + '_bank_in_MDL')
            out_mdl = cmds.createNode('multDoubleLinear',
                                      name=self.base_name + '_bank_out_MDL')
            cmds.setAttr(in_mdl + '.input2', -1)
            cmds.setAttr(out_mdl + '.input2', -1)
            cmds.connectAttr(bank_cnd + '.outColorG', in_mdl + '.input1')
            cmds.connectAttr(bank_cnd + '.outColorR', out_mdl + '.input1')
            cmds.connectAttr(in_mdl + '.output',
                             self.out_piv.group_list[1] + '.rotateZ')
            cmds.connectAttr(out_mdl + '.output',
                             self.in_piv.group_list[1] + '.rotateZ')

    def skeleton(self):
        foot_chain = nmChain.Chain(transform_list=self.blend_chain.joints,
                                   prefix=self.side,
                                   suffix='JNT',
                                   name=self.part)
        foot_chain.create_from_transforms(parent=self.skel)

        self.bind_joints = foot_chain.joints
        self.tag_bind_joints(self.bind_joints[:-1])

    def add_plugs(self):
        # add skeleton plugs
        nmAttr.Attribute(node=self.part_grp, type='plug',
                         value=['cmds.ls("' + self.side + '_leg_??_JNT")[-1]'],
                         name='skeletonPlugs',
                         children_name=[self.bind_joints[0]])

        # add parentConstraint rig plugs
        driver_list = [self.side + '_leg_03_fk_CTRL']
        driven_list = [self.base_name + '_01_fk_CTRL_CNST_GRP']

        nmAttr.Attribute(node=self.part_grp, type='plug',
                         value=driver_list, name='pacRigPlugs',
                         children_name=driven_list)

        # add pointConstraint rig plugs
        driver_list = [self.side + '_leg_03_switch_JNT']
        driven_list = [self.base_name + '_01_switch_JNT']

        nmAttr.Attribute(node=self.part_grp, type='plug',
                         value=driver_list, name='pocRigPlugs',
                         children_name=driven_list)

        # add delete rig plugs
        delete_list = [self.base_name + '_01_trans_BCN']
        nmAttr.Attribute(node=self.part_grp, type='plug',
                         value=[' '.join(delete_list)], name='deleteRigPlugs',
                         children_name=['deleteNodes'])

        # add space plugs
        target_list = ['CHAR', 'Cn_global_CTRL', 'Cn_root_02_CTRL',
                       'Cn_hip_01_CTRL', self.side + '_leg_IK_base_CTRL', '2']
        name_list = ['world', 'global', 'root', 'hip', 'leg', 'default_value']

        nmAttr.Attribute(node=self.part_grp, type='plug',
                         value=target_list,
                         name=self.main_ctrl.ctrl + '_parent',
                         children_name=name_list)

        # add switch plug
        switch_attr = self.side.lower() + 'LegIKFK'
        nmAttr.Attribute(node=self.part_grp, type='plug',
                         value=[switch_attr], name='switchRigPlugs',
                         children_name=['ikFkSwitch'])



