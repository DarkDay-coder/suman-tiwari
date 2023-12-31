import maya.cmds as cmds

import nmrig.build.rigModule as nmModule
import nmrig.build.chain as nmChain
import nmrig.build.fk as nmFk
import nmrig.build.ik as nmIk
import nmrig.libs.attribute as nmAttr
reload(nmChain)


class BipedLimb(nmModule.RigModule, nmIk.Ik, nmFk.Fk):
    def __init__(self,
                 side=None,
                 part=None,
                 guide_list=None,
                 ctrl_scale=1,
                 create_ik=True,
                 create_fk=True,
                 stretchy=True,
                 twisty=True,
                 bendy=True,
                 segments=4,
                 sticky=None,
                 solver=None,
                 pv_guide='auto',
                 offset_pv=0,
                 slide_pv=None,
                 gimbal=True,
                 offset=True,
                 pad='auto',
                 fk_shape='circle',
                 gimbal_shape='circle',
                 offset_shape='square',
                 model_path=None,
                 guide_path=None):
        super(BipedLimb, self).__init__(side=side, part=part,
                                        guide_list=guide_list,
                                        ctrl_scale=ctrl_scale,
                                        model_path=model_path,
                                        guide_path=guide_path)

        self.gimbal = gimbal
        self.create_ik = create_ik
        self.create_fk = create_fk
        self.stretchy = stretchy
        self.twisty = twisty
        self.bendy = bendy
        self.segments = segments

        # fk shape kwargs
        self.fk_shape = fk_shape
        self.gimbal_shape = gimbal_shape
        self.offset_shape = offset_shape

        # ik kwargs
        self.sticky = sticky
        self.solver = solver
        self.pv_guide = pv_guide
        self.offset_pv = offset_pv
        self.slide_pv = slide_pv

        if self.twisty or self.bendy and not self.segments:
            self.segments = 4

        # fk kwargs
        self.gimbal = gimbal
        self.offset = offset
        self.pad = pad

        if self.pad == 'auto':
            self.pad = len(str(len(self.guide_list))) + 1

        self.create_module()

    def create_module(self):
        super(BipedLimb, self).create_module()

        self.check_solvers()
        self.check_pv_guide()

        self.control_rig()
        self.output_rig()
        self.skeleton()
        self.add_plugs()

    def control_rig(self):
        # fk
        if self.create_fk:
            self.build_fk_controls()
            cmds.parent(self.fk_ctrls[0].top, self.control_grp)

        # ik
        if self.create_ik:
            self.build_ik_controls()
            cmds.parent(self.ik_ctrl_grp, self.control_grp)

    def output_rig(self):
        self.limb_grp = cmds.group(em=True, parent=self.module_grp,
                                   name=self.base_name + '_RIG_GRP')
        cmds.matchTransform(self.limb_grp, self.guide_list[0])

        # fk
        if self.create_fk:
            self.build_fk_chain()
            cmds.parent(self.fk_joints[0], self.limb_grp)
            self.src_chain = self.fk_chain
            self.src_joints = self.fk_joints
            up_twist = self.fk_ctrls[0].ctrl
            lo_twist = self.fk_ctrls[-1].ctrl


        # ik
        if self.create_ik:
            self.build_ik_chain()
            self.build_ikh(scale_attr=self.global_scale)
            cmds.parent(self.ikh, self.ik_joints[0], self.limb_grp)
            self.src_chain = self.ik_chain
            self.src_joints = self.ik_joints
            up_twist = self.base_ctrl.ctrl
            lo_twist = self.main_ctrl.ctrl

        if self.create_ik and self.create_fk:
            blend_chain = nmChain.Chain(transform_list=self.src_joints,
                                        prefix=self.side,
                                        suffix='switch_JNT',
                                        name=self.part)

            blend_chain.create_blend_chain(switch_node=self.base_name,
                                           chain_a=self.fk_joints,
                                           chain_b=self.ik_joints)
            cmds.parent(blend_chain.joints[0], self.limb_grp)
            self.src_chain = blend_chain
            self.src_joints = blend_chain.joints

            # twist
            up_twist = cmds.spaceLocator(name=self.base_name + '_up_twist_LOC')[0]
            lo_twist = cmds.spaceLocator(name=self.base_name + '_lo_twist_LOC')[0]
            cmds.matchTransform(up_twist, self.guide_list[0])
            cmds.matchTransform(lo_twist, self.guide_list[-1])

            rev = cmds.createNode('reverse', name=self.base_name + '_REV')
            pac = cmds.parentConstraint(self.fk_ctrls[-1].ctrl,
                                        self.main_ctrl.ctrl,
                                        lo_twist, maintainOffset=True)[0]
            wal = cmds.parentConstraint(pac, query=True, weightAliasList=True)
            cmds.setAttr(pac + '.interpType', 2)
            cmds.connectAttr(blend_chain.switch.attr, rev + '.inputY')
            cmds.connectAttr(rev + '.outputY', pac + '.' + wal[1])
            cmds.connectAttr(blend_chain.switch.attr, pac + '.' + wal[0])
            cmds.parent(lo_twist, up_twist, self.limb_grp)
            cmds.hide(lo_twist, up_twist)

            # vis switch
            cmds.connectAttr(blend_chain.switch.attr, rev + '.inputZ')
            cmds.connectAttr(blend_chain.switch.attr,
                             self.fk_ctrls[0].top + '.visibility')
            cmds.connectAttr(rev + '.outputZ', self.ik_ctrl_grp + '.visibility')



        if self.segments:
            self.src_chain.split_chain(segments=self.segments)
            self.src_joints = []
            for jnt in self.src_chain.joints[:-1]:
                split_list = self.src_chain.split_jnt_dict[jnt]
                for s_jnt in split_list:
                    self.src_joints.append(s_jnt)
            self.src_joints.append(self.src_chain.joints[-1])

        if self.twisty:
            # up limb
            self.src_chain.twist_chain(start_translate=self.src_chain.joints[1],
                                       start_rotate=self.src_chain.joints[0],
                                       end_translate=self.src_chain.joints[0],
                                       end_rotate=self.src_chain.joints[0],
                                       twist_bone=self.src_chain.joints[0],
                                       twist_driver=up_twist,
                                       reverse=True)
            # lo limb
            self.src_chain.twist_chain(start_translate=self.src_chain.joints[2],
                                       start_rotate=self.src_chain.joints[1],
                                       end_translate=self.src_chain.joints[2],
                                       end_rotate=self.src_chain.joints[1],
                                       twist_bone=self.src_chain.joints[1],
                                       twist_driver=lo_twist)

        if self.bendy:
            if self.side == 'Rt':
                mirror = True
            else:
                mirror = False
            bend_01 = self.src_chain.bend_chain(bone=self.src_chain.joints[0],
                                                ctrl_scale=self.ctrl_scale,
                                                mirror=mirror,
                                                global_scale=self.global_scale.attr)
            bend_02 = self.src_chain.bend_chain(bone=self.src_chain.joints[1],
                                                ctrl_scale=self.ctrl_scale,
                                                mirror=mirror,
                                                global_scale=self.global_scale.attr)
            cmds.parent(bend_01['control'], bend_02['control'],
                        self.control_grp)
            cmds.parent(bend_01['module'], bend_02['module'], self.module_grp)

    def skeleton(self):
        limb_chain = nmChain.Chain(transform_list=self.src_joints,
                                   prefix=self.side,
                                   suffix='JNT',
                                   name=self.part)
        if self.create_fk:
            poc = True
        else:
            poc = False
        limb_chain.create_from_transforms(orient_constraint=True,
                                          point_constraint=poc,
                                          scale_constraint=False,
                                          parent=self.skel)
        self.bind_joints = limb_chain.joints

        self.tag_bind_joints(self.bind_joints[:-1])

    def add_plugs(self):
        if self.part == 'leg':
            par = 'Cn_hip_JNT'
            driver_list = ['Cn_hip_02_CTRL',
                           'Cn_hip_02_CTRL',
                           'Cn_hip_02_CTRL',
                           self.base_name + '_IK_base_CTRL',
                           self.side + '_foot_01_ik_JNT']
            driven_list = [self.limb_grp,
                           self.base_name + '_IK_base_CTRL_CNST_GRP',
                           self.base_name + '_01_fk_CTRL_CNST_GRP',
                           self.base_name + '_up_twist_LOC',
                           self.base_name + '_IK_main_CTRL_CNST_GRP']
            hide_list = [self.base_name + '_IK_main_CTRL_CNST_GRP',
                         self.fk_ctrls[-1].top]
            pv_targets = ['CHAR', 'Cn_global_CTRL', 'Cn_root_02_CTRL',
                          'Cn_hip_01_CTRL', self.side + '_leg_IK_base_CTRL',
                          self.side + '_foot_02_CTRL', '2']
            pv_names = ['world', 'global', 'root', 'hip', 'leg', 'foot',
                        'default_value']
            ik_ctrl = [self.side + '_foot_01_CTRL']
        elif self.part == 'arm':
            par = self.side + '_clavicle_02_JNT'
            driver_list = [self.side + '_clavicle_02_driver_JNT',
                           self.side + '_clavicle_02_driver_JNT',
                           self.side + '_clavicle_02_driver_JNT',
                           self.side + '_hand_01_ik_JNT']
            driven_list = [self.limb_grp,
                           self.base_name + '_IK_base_CTRL_CNST_GRP',
                           self.base_name + '_up_twist_LOC',
                           self.base_name + '_IK_main_CTRL_CNST_GRP']
            hide_list = [self.base_name + '_IK_base_CTRL_CNST_GRP',
                         self.base_name + '_IK_main_CTRL_CNST_GRP']
            pv_targets = ['CHAR', 'Cn_global_CTRL', 'Cn_root_02_CTRL',
                          'Cn_chest_01_CTRL', self.side + '_hand_local_CTRL',
                          '2']
            pv_names = ['world', 'global', 'root', 'chest', 'hand',
                        'default_value']
            ik_ctrl = [self.side + '_hand_01_CTRL']

            # add pointConstraint rig plugs
            nmAttr.Attribute(node=self.part_grp, type='plug',
                             value=[self.side + '_clavicle_02_driver_JNT'],
                             name='pocRigPlugs',
                             children_name=[
                                 self.side + '_arm_01_fk_CTRL_CNST_GRP'])

            # add space plugs
            target_list = ['Cn_chest_01_CTRL', 'Cn_chest_02_CTRL',
                           self.side + '_clavicle_02_driver_JNT', '0']
            name_list = ['chest01', 'chest02', 'clavicle', 'default_value']
            orient_names = ['orient' + n.title() for n in name_list]

            nmAttr.Attribute(node=self.part_grp, type='plug',
                             value=target_list,
                             name=self.fk_ctrls[0].ctrl + '_orient',
                             children_name=orient_names)
        else:
            par = 'insert limb plug here'
            driver_list = ['driver_node']
            driven_list = ['driven_node']
            hide_list = ['list of geo to hide']
            ik_ctrl = ['ik driver control (hand/foot)']


        # add skeleton plugs
        nmAttr.Attribute(node=self.part_grp, type='plug',
                         value=[par], name='skeletonPlugs',
                         children_name=[self.bind_joints[0]])


        # add parentConstraint rig plugs
        nmAttr.Attribute(node=self.part_grp, type='plug',
                         value=driver_list, name='pacRigPlugs',
                         children_name=driven_list)

        # add hide rig plugs
        nmAttr.Attribute(node=self.part_grp, type='plug',
                         value=[' '.join(hide_list)], name='hideRigPlugs',
                         children_name=['hideNodes'])

        # add pv space plug
        nmAttr.Attribute(node=self.part_grp, type='plug',
                         value=pv_targets,
                         name=self.pv_ctrl.ctrl + '_parent',
                         children_name=pv_names)

        # add switch plug
        switch_attr = self.side.lower() + self.part.capitalize() + 'IKFK'
        nmAttr.Attribute(node=self.part_grp, type='plug',
                         value=[switch_attr], name='switchRigPlugs',
                         children_name=['ikFkSwitch'])

        # add transferAttributes plug
        nmAttr.Attribute(node=self.part_grp, type='plug',
                         value=ik_ctrl, name='transferAttributes',
                         children_name=[self.main_ctrl.ctrl])
