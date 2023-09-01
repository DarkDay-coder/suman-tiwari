import maya.cmds as cmds

import nmrig.build.rigModule as nmModule
import nmrig.build.chain as nmChain
import nmrig.libs.control.ctrl as nmCtrl
import nmrig.libs.attribute as nmAttr


class Hip(nmModule.RigModule):
    def __init__(self,
                 side=None,
                 part=None,
                 guide_list=None,
                 ctrl_scale=None,
                 offset_hip=-0.1,
                 model_path=None,
                 guide_path=None):
        super(Hip, self).__init__(side=side, part=part,
                                  guide_list=guide_list,
                                  ctrl_scale=ctrl_scale,
                                  model_path=model_path,
                                  guide_path=guide_path)

        self.offset_hip = offset_hip

        self.create_module()

    def create_module(self):
        super(Hip, self).create_module()

        self.control_rig()
        self.output_rig()
        self.skeleton()
        # self.add_plugs()

    def control_rig(self):
        # create controls
        self.hip_01 = nmCtrl.Control(parent=self.control_grp,
                                     shape='hip',
                                     prefix=self.side,
                                     suffix='CTRL',
                                     name=self.part + '_01',
                                     axis='y',
                                     group_type='main',
                                     rig_type='primary',
                                     position=self.guide_list[0],
                                     rotation=(0, 0, 0),
                                     ctrl_scale=self.ctrl_scale * 0.4)

        self.hip_02 = nmCtrl.Control(parent=self.hip_01.ctrl,
                                     shape='hip',
                                     prefix=self.side,
                                     suffix='CTRL',
                                     name=self.part + '_02',
                                     axis='y',
                                     group_type='main',
                                     rig_type='secondary',
                                     position=self.guide_list[0],
                                     rotation=(0, 0, 0),
                                     ctrl_scale=self.ctrl_scale * 0.35)

    def output_rig(self):
        hip_jnt_grp = cmds.group(parent=self.module_grp, empty=True,
                                 name=self.base_name + '_JNT_GRP')
        cmds.matchTransform(hip_jnt_grp, self.hip_02.ctrl)
        self.hip_jnt = cmds.joint(hip_jnt_grp,
                                  name=self.hip_02.ctrl.replace('CTRL', 'JNT'))

        cmds.parentConstraint(self.hip_02.ctrl, self.hip_jnt, mo=True)

    def skeleton(self):
        hip_chain = nmChain.Chain(transform_list=[self.hip_jnt],
                                  prefix=self.side,
                                  suffix='JNT',
                                  name=self.part)
        hip_chain.create_from_transforms(parent=self.skel,
                                         pad=False)
        self.bind_joints = hip_chain.joints

        # offset hip joint for better weight mirroring
        cmds.setAttr(
            hip_chain.constraints[0] + '.target[0].targetOffsetTranslateY',
            self.offset_hip)

        self.tag_bind_joints(self.bind_joints)


