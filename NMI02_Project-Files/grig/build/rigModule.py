import maya.cmds as cmds

import grig.build.rigBase as gnBase
import grig.libs.attribute as gnAttr
import grig.libs.common as gnCommon
reload(gnCommon)


class RigModule(gnBase.RigBase):
    def __init__(self,
                 side=None,
                 part=None,
                 guide_list=None,
                 ctrl_scale=None,
                 model_path=None,
                 guide_path=None):
        super(RigModule, self).__init__(model_path=model_path,
                                        guide_path=guide_path)

        self.side = side
        self.part = part
        self.guide_list = guide_list
        self.ctrl_scale = ctrl_scale

        if not self.side:
            self.side = 'Cn'
        if not self.part:
            self.part = 'default'
        self.base_name = self.side + '_' + self.part

        if self.guide_list:
            # format guide_list into a list if it is not one
            if not isinstance(self.guide_list, list):
                self.guide_list = [self.guide_list]

    def create_module(self):
        super(RigModule, self).create_module()
        self.part_hierarchy()

        if not self.ctrl_scale:
            # get scale factor based on model's bounding box
            bb = gnCommon.get_bounding_box(self.model)
            # check to see if the character is larger in the x or z axis
            if abs(bb[0]) > abs(bb[1]):
                scale_factor = abs(bb[0])
            else:
                scale_factor = abs(bb[1])
            self.ctrl_scale = scale_factor

    def part_hierarchy(self):
        self.part_grp = self.rig_group(name=self.base_name,
                                       parent=self.rig)
        self.module_grp = self.rig_group(name=self.base_name + '_MODULE',
                                         parent=self.part_grp)
        self.control_grp = self.rig_group(name=self.base_name + '_CONTROL',
                                          parent=self.part_grp)
        if self.part != 'root':
            self.global_scale = gnAttr.Attribute(node=self.part_grp,
                                                 type='double',
                                                 value=1,
                                                 keyable=True,
                                                 name='globalScale')

    def tag_bind_joints(self, joints):
        if not isinstance(joints, list):
            joints = [joints]

        for jnt in joints:
            gnAttr.Attribute(node=jnt, type='bool', value=True, keyable=False,
                             name='bindJoint')