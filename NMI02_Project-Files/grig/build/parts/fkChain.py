import maya.cmds as cmds

import grig.build.rigModule as gnModule
import grig.build.chain as gnChain
import grig.build.fk as gnFk
import grig.libs.attribute as gnAttr

# reload(gnModule)
# reload(gnChain)
reload(gnFk)



class FkChain(gnModule.RigModule, gnFk.Fk):
    def __init__(self,
                 side=None,
                 part=None,
                 guide_list=None,
                 gimbal=True,
                 offset=True,
                 pad='auto',
                 ctrl_scale=1,
                 remove_last=True,
                 fk_shape='circle',
                 gimbal_shape='circle',
                 offset_shape='square',
                 model_path=None,
                 guide_path=None):
        super(FkChain, self).__init__(side=side, part=part,
                                      guide_list=guide_list,
                                      ctrl_scale=ctrl_scale,
                                      model_path=model_path,
                                      guide_path=guide_path)

        self.guide_list = guide_list
        self.gimbal = gimbal
        self.offset = offset
        self.pad = pad
        self.remove_last = remove_last
        self.fk_shape = fk_shape
        self.gimbal_shape = gimbal_shape
        self.offset_shape = offset_shape

        if self.pad == 'auto':
            self.pad = len(str(len(self.guide_list))) + 1

        self.create_module()

    def create_module(self):
        super(FkChain, self).create_module()

        self.control_rig()
        self.output_rig()
        self.skeleton()
        self.add_plugs()

    def control_rig(self):
        self.build_fk_controls()
        cmds.parent(self.fk_ctrls[0].top, self.control_grp)

    def output_rig(self):
        self.build_fk_chain()
        cmds.parent(self.fk_joints[0], self.module_grp)

    def skeleton(self):
        fk_chain = gnChain.Chain(transform_list=self.fk_joints,
                                 prefix=self.side,
                                 suffix='JNT',
                                 name=self.part)
        fk_chain.create_from_transforms(parent=self.skel)

        if self.remove_last:
            cmds.delete(self.fk_ctrls[-1].top)
            self.bind_joints = fk_chain.joints[:-1]
        else:
            self.bind_joints = fk_chain.joints

        self.tag_bind_joints(self.bind_joints)

    def add_plugs(self):
        gnAttr.Attribute(node=self.part_grp, type='plug',
                         value=['add fk plug here'], name='skeletonPlugs',
                         children_name=[self.bind_joints[0]])