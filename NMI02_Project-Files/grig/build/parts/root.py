import maya.cmds as cmds

import grig.build.rigModule as gnModule
import grig.build.chain as gnChain
import grig.libs.control.ctrl as gnCtrl


class Root(gnModule.RigModule):
    def __init__(self,
                 side=None,
                 part=None,
                 guide_list=None,
                 ctrl_scale=None,
                 global_shape='gnomon',
                 root_shape='pacman',
                 model_path=None,
                 guide_path=None):
        super(Root, self).__init__(side=side, part=part,
                                   guide_list=guide_list,
                                   ctrl_scale=ctrl_scale,
                                   model_path=model_path,
                                   guide_path=guide_path)

        if self.guide_list:
            self.root_pose = self.guide_list[0]
        else:
            self.root_pose = (0, 0, 0)

        self.global_shape = global_shape
        self.root_shape = root_shape

        self.create_module()

    def create_module(self):
        super(Root, self).create_module()

        self.control_rig()
        self.output_rig()
        self.skeleton()

    def control_rig(self):
        # create controls
        if self.root_pose == (0, 0, 0):
            group_type = None
        else:
            group_type = 1

        self.global_ctrl = gnCtrl.Control(parent=self.control_grp,
                                          shape=self.global_shape,
                                          prefix=self.side,
                                          suffix='CTRL',
                                          name='global',
                                          axis='y',
                                          group_type=group_type,
                                          rig_type='global',
                                          position=self.root_pose,
                                          rotation=self.root_pose,
                                          ctrl_scale=self.ctrl_scale)

        self.root_01 = gnCtrl.Control(parent=self.global_ctrl.ctrl,
                                      shape=self.root_shape,
                                      prefix=self.side,
                                      suffix='CTRL',
                                      name='root_01',
                                      axis='y',
                                      group_type='main',
                                      rig_type='root_01',
                                      position=self.root_pose,
                                      rotation=self.root_pose,
                                      ctrl_scale=self.ctrl_scale * 0.5)

        self.root_02 = gnCtrl.Control(parent=self.root_01.ctrl,
                                      shape=self.root_shape,
                                      prefix=self.side,
                                      suffix='CTRL',
                                      name='root_02',
                                      axis='y',
                                      group_type='main',
                                      rig_type='root_02',
                                      position=self.root_pose,
                                      rotation=self.root_pose,
                                      ctrl_scale=self.ctrl_scale * 0.4)

    def output_rig(self):
        root_jnt_grp = cmds.group(parent=self.module_grp, empty=True,
                                  name=self.base_name + '_JNT_GRP')
        cmds.matchTransform(root_jnt_grp, self.root_02.ctrl)
        self.root_jnt = cmds.joint(root_jnt_grp,
                                   name=self.root_02.ctrl.replace('CTRL',
                                                                  'JNT'))

        cmds.parentConstraint(self.root_02.ctrl, self.root_jnt, mo=True)
        cmds.scaleConstraint(self.root_02.ctrl, self.root_jnt, mo=True)

    def skeleton(self):
        self.bind_joints = []
        root_chain = gnChain.Chain(transform_list=[self.root_jnt],
                                   prefix=self.side,
                                   suffix='JNT',
                                   name=self.part)
        root_chain.create_from_transforms(parent=self.skel,
                                          pad=False)

        

