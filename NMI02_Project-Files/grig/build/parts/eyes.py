import maya.cmds as cmds

import grig.build.rigModule as gnModule
import grig.libs.attribute as gnAttr
import grig.build.chain as gnChain
import grig.libs.control.ctrl as gnCtrl
import grig.build.guide as gnGuide
reload(gnAttr)
# reload(gnModule)
# reload(gnChain)
# reload(gnCtrl)


class Eyes(gnModule.RigModule):
    def __init__(self,
                 side=None,
                 part=None,
                 guide_list=None,
                 ctrl_scale=None,
                 model_path=None,
                 guide_path=None,
                 offset=20,
                 side_list=['Lf', 'Rt']):
        super(Eyes, self).__init__(side=side, part=part,
                                       guide_list=guide_list,
                                       ctrl_scale=ctrl_scale,
                                       model_path=model_path,
                                       guide_path=guide_path)

        self.offset = offset
        self.side_list = side_list
        self.create_module()

    def create_module(self):
        super(Eyes, self).create_module()

        self.control_rig()
        self.output_rig()
        self.skeleton()
        self.add_plugs()

    def control_rig(self):
        # guides expect LeftEye, LeftEyeEnd, RightEye, RightEyeEnd

        # create side rig groups
        self.l_part_grp = cmds.group(empty=True,
                                     name=self.side_list[0] + '_' + self.part,
                                     parent=self.rig)
        self.r_part_grp = cmds.group(empty=True,
                                     name=self.side_list[1] + '_' + self.part,
                                     parent=self.rig)
        cmds.connectAttr(self.part_grp + '.scale', self.l_part_grp + '.scale')
        cmds.connectAttr(self.part_grp + '.scale', self.r_part_grp + '.scale')

        # create side control groups
        grp_name = '_' + self.part + '_CONTROL'
        self.l_control_grp = cmds.group(empty=True,
                                        name=self.side_list[0] + grp_name,
                                        parent=self.l_part_grp)
        self.r_control_grp = cmds.group(empty=True,
                                        name=self.side_list[1] + grp_name,
                                        parent=self.r_part_grp)

        # up vector object for eye aim constraints
        self.up_object = cmds.spaceLocator(name=self.part + '_upObject_LOC')[0]
        cmds.parent(self.up_object, self.module_grp)

        # left eye fk
        self.l_eye_fk = gnCtrl.Control(parent=self.l_control_grp,
                                       shape='tweaker',
                                       prefix=self.side_list[0],
                                       suffix='CTRL',
                                       name=self.part + '_fk',
                                       axis='y',
                                       group_type='main',
                                       rig_type='l_eye',
                                       position=self.guide_list[0],
                                       ctrl_scale=self.ctrl_scale)

        # aim at end joint
        aim = cmds.aimConstraint(self.guide_list[1], self.l_eye_fk.top,
                                 aimVector=(0, 0, 1),
                                 upVector=(0, 1, 0),
                                 worldUpType='vector',
                                 worldUpVector=(0, 1, 0))
        cmds.delete(aim)

        # right eye fk
        self.r_eye_fk = gnCtrl.Control(parent=self.r_control_grp,
                                       shape='tweaker',
                                       prefix=self.side_list[1],
                                       suffix='CTRL',
                                       name=self.part + '_fk',
                                       axis='y',
                                       group_type='main',
                                       rig_type='r_eye',
                                       position=self.guide_list[2],
                                       ctrl_scale=self.ctrl_scale)

        # aim at end joint
        aim = cmds.aimConstraint(self.guide_list[3], self.r_eye_fk.top,
                                 aimVector=(0, 0, 1),
                                 upVector=(0, 1, 0),
                                 worldUpType='vector',
                                 worldUpVector=(0, 1, 0))
        cmds.delete(aim)

        # move up object between eyes and push hack
        poc = cmds.pointConstraint(self.l_eye_fk.ctrl,
                                   self.r_eye_fk.ctrl,
                                   self.up_object,
                                   offset=(0, 0, self.offset * -0.5),
                                   maintainOffset=False)
        cmds.delete(poc)

        # left eye target control
        self.l_eye_target = gnCtrl.Control(parent=self.l_control_grp,
                                           shape='circle',
                                           prefix=self.side_list[0],
                                           suffix='CTRL',
                                           name=self.part + '_target',
                                           axis='z',
                                           group_type='main',
                                           rig_type='l_eye',
                                           position=self.l_eye_fk.ctrl,
                                           rotation=self.l_eye_fk.ctrl,
                                           ctrl_scale=self.ctrl_scale)
        cmds.xform(self.l_eye_target.top,
                   objectSpace=True,
                   relative=True,
                   translation=(0, 0, self.offset))
        cmds.setAttr(self.l_eye_target.top + '.rotate', 0, 0, 0)

        self.r_eye_target = gnCtrl.Control(parent=self.r_control_grp,
                                           shape='circle',
                                           prefix=self.side_list[1],
                                           suffix='CTRL',
                                           name=self.part + '_target',
                                           axis='z',
                                           group_type='main',
                                           rig_type='r_eye',
                                           position=self.r_eye_fk.ctrl,
                                           rotation=self.r_eye_fk.ctrl,
                                           ctrl_scale=self.ctrl_scale)
        cmds.xform(self.r_eye_target.top,
                   objectSpace=True,
                   relative=True,
                   translation=(0, 0, self.offset))
        cmds.setAttr(self.r_eye_target.top + '.rotate', 0, 0, 0)

        # eye main ctrl
        self.eye_main = gnCtrl.Control(parent=self.control_grp,
                                           shape='circle',
                                           prefix=self.side,
                                           suffix='CTRL',
                                           name=self.part + '_target',
                                           axis='z',
                                           group_type='main',
                                           rig_type='c_eye',
                                           ctrl_scale=self.ctrl_scale)

        # move eye main control between the two targets
        cmds.delete(cmds.pointConstraint(self.l_eye_target.ctrl,
                                         self.r_eye_target.ctrl,
                                         self.eye_main.top,
                                         maintainOffset=False))

        # clean up controls
        attr_util = gnAttr.Attribute(add=False)
        ctrl_list = [self.l_eye_fk.ctrl, self.r_eye_fk.ctrl]
        for ctrl in ctrl_list:
            attr_util.lock_and_hide(node=ctrl,
                                    rotate=False,
                                    translate=False)

        ctrl_list = [self.l_eye_target.ctrl, self.r_eye_target.ctrl]
        for ctrl in ctrl_list:
            attr_util.lock_and_hide(node=ctrl,
                                    translate=False)
        attr_util.lock_and_hide(node=self.eye_main.ctrl,
                                translate=False,
                                rotate=False,
                                scale=False)


    def output_rig(self):
        # build guides to show eye-line
        gde_grp = cmds.group(empty=True,
                             parent=self.control_grp,
                             name=self.part + '_GDE_GRP')
        cmds.setAttr(gde_grp + '.inheritsTransform', 0)
        lg = gnGuide.create_line_guide(a=self.l_eye_fk.ctrl,
                                       b=self.l_eye_target.ctrl,
                                       name=self.side_list[0] + '_' + self.part)
        rg = gnGuide.create_line_guide(a=self.r_eye_fk.ctrl,
                                       b=self.r_eye_target.ctrl,
                                       name=self.side_list[1] + '_' + self.part)
        cmds.parent(lg['clusters'],
                    lg['curve'],
                    rg['clusters'],
                    rg['curve'],
                    gde_grp)

        # create main joint grp
        jnt_grp = cmds.group(empty=True,
                             parent=self.module_grp,
                             name=self.part + '_JNT_GRP')
        # create joints
        l_jnt = cmds.joint(jnt_grp,
                           name=self.side_list[0] + '_' + self.part + '_fk_JNT')
        r_jnt = cmds.joint(jnt_grp,
                           name=self.side_list[1] + '_' + self.part + '_fk_JNT')

        # create eye constraints
        cmds.aimConstraint(self.l_eye_target.ctrl, self.l_eye_fk.top,
                           aimVector=(0, 0, 1),
                           upVector=(0, 1, 0),
                           worldUpType='objectrotation',
                           worldUpObject=self.up_object,
                           maintainOffset=True)

        cmds.aimConstraint(self.r_eye_target.ctrl, self.r_eye_fk.top,
                           aimVector=(0, 0, 1),
                           upVector=(0, 1, 0),
                           worldUpType='objectrotation',
                           worldUpObject=self.up_object,
                           maintainOffset=True)

        cmds.parentConstraint(self.l_eye_fk.ctrl, l_jnt, maintainOffset=False)
        cmds.parentConstraint(self.r_eye_fk.ctrl, r_jnt, maintainOffset=False)

    def skeleton(self):
        l_jnt = cmds.joint(self.skel,
                           name=self.side_list[0] + '_' + self.part + '_JNT')
        r_jnt = cmds.joint(self.skel,
                           name=self.side_list[1] + '_' + self.part + '_JNT')
        cmds.parentConstraint(l_jnt.replace('JNT', 'fk_JNT'),
                              l_jnt,
                              maintainOffset=False)
        cmds.parentConstraint(r_jnt.replace('JNT', 'fk_JNT'),
                              r_jnt,
                              maintainOffset=False)

        self.bind_joints = [l_jnt, r_jnt]
        self.tag_bind_joints(self.bind_joints)

    def add_plugs(self):
        # add skeleton plugs
        gnAttr.Attribute(node=self.part_grp, type='plug',
                         value=[self.side + '_head_JNT',
                                self.side + '_head_JNT'],
                         name='skeletonPlugs',
                         children_name=self.bind_joints)

        # add parentConstraint rig plugs
        driver_list = [self.side + '_head_JNT']
        driven_list = [self.up_object]

        gnAttr.Attribute(node=self.part_grp, type='plug',
                         value=driver_list, name='pacRigPlugs',
                         children_name=driven_list)

        # add parentConstraint "point" rig plugs
        driver_list = [self.side + '_head_JNT',
                       self.side + '_head_JNT']
        driven_list = [self.l_eye_fk.top,
                       self.r_eye_fk.top,]

        gnAttr.Attribute(node=self.part_grp, type='plug',
                         value=driver_list, name='pacPocRigPlugs',
                         children_name=driven_list)

        # add space plugs
        target_list = ['CHAR', 'Cn_global_CTRL', 'Cn_root_02_CTRL',
                       'Cn_head_JNT', '3']
        name_list = ['world', 'global', 'root', 'head', 'default_value']
        gnAttr.Attribute(node=self.part_grp, type='plug',
                         value=target_list,
                         name=self.eye_main.ctrl + '_parent',
                         children_name=name_list)

        target_list = ['CHAR', 'Cn_global_CTRL', 'Cn_root_02_CTRL',
                       'Cn_head_JNT', self.eye_main.ctrl, '4']
        name_list = ['world', 'global', 'root', 'head', 'target',
                     'default_value']
        gnAttr.Attribute(node=self.l_part_grp, type='plug',
                         value=target_list,
                         name=self.l_eye_target.ctrl + '_parent',
                         children_name=name_list)

        target_list = ['CHAR', 'Cn_global_CTRL', 'Cn_root_02_CTRL',
                       'Cn_head_JNT', self.eye_main.ctrl, '4']
        name_list = ['world', 'global', 'root', 'head', 'target',
                     'default_value']
        gnAttr.Attribute(node=self.r_part_grp, type='plug',
                         value=target_list,
                         name=self.r_eye_target.ctrl + '_parent',
                         children_name=name_list)