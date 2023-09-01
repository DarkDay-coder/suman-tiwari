import maya.cmds as cmds

import nmrig.build.rigModule as nmModule
import nmrig.build.chain as nmChain
import nmrig.libs.control.ctrl as nmCtrl
import nmrig.libs.attribute as nmAttr


class Chest(nmModule.RigModule):
    def __init__(self,
                 side=None,
                 part=None,
                 guide_list=None,
                 ctrl_scale=None,
                 model_path=None,
                 guide_path=None):
        super(Chest, self).__init__(side=side, part=part,
                                    guide_list=guide_list,
                                    ctrl_scale=ctrl_scale,
                                    model_path=model_path,
                                    guide_path=guide_path)

        self.create_module()

    def create_module(self):
        super(Chest, self).create_module()

        self.control_rig()
        self.output_rig()
        self.skeleton()
        self.add_plugs()

    def control_rig(self):
        # create controls
        self.chest_01 = nmCtrl.Control(parent=self.control_grp,
                                       shape='chest',
                                       prefix=self.side,
                                       suffix='CTRL',
                                       name=self.part + '_01',
                                       axis='y',
                                       group_type='main',
                                       rig_type='primary',
                                       position=self.guide_list[0],
                                       rotation=(0, 0, 0),
                                       ctrl_scale=self.ctrl_scale * 0.4)

        self.chest_02 = nmCtrl.Control(parent=self.chest_01.ctrl,
                                       shape='chest',
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
        chest_jnt_grp = cmds.group(parent=self.module_grp, empty=True,
                                   name=self.base_name + '_JNT_GRP')
        cmds.matchTransform(chest_jnt_grp, self.chest_02.ctrl)
        self.chest_jnt = cmds.joint(chest_jnt_grp,
                                    name=self.chest_02.ctrl.replace('CTRL',
                                                                   'JNT'))

        cmds.parentConstraint(self.chest_02.ctrl, self.chest_jnt, mo=True)

    def skeleton(self):
        chest_chain = nmChain.Chain(transform_list=[self.chest_jnt],
                                    prefix=self.side,
                                    suffix='JNT',
                                    name=self.part)
        chest_chain.create_from_transforms(parent=self.skel,
                                           pad=False)
        self.bind_joints = chest_chain.joints
        self.tag_bind_joints(self.bind_joints)

    def add_plugs(self):
        # add skeleton plugs
        nmAttr.Attribute(node=self.part_grp, type='plug',
                         value=['cmds.ls("Cn_spine_??_JNT")[-1]'],
                         name='skeletonPlugs',
                         children_name=[self.bind_joints[0]])

        # add delete rig plugs
        delete_list = ['Cn_chest_02_JNT_parentConstraint1',
                       'Cn_spine_tip_CTRL_CNST_GRP_parentConstraint1']
        nmAttr.Attribute(node=self.part_grp, type='plug',
                         value=[' '.join(delete_list)], name='deleteRigPlugs',
                         children_name=['deleteNodes'])

        # add pointConstraint rig plugs
        nmAttr.Attribute(node=self.part_grp, type='plug',
                         value=['cmds.ls("Cn_spine_??_driver_JNT")[-1]'],
                         name='pocRigPlugs',
                         children_name=[self.chest_jnt + '_point'])

        # add orientConstraint rig plugs
        nmAttr.Attribute(node=self.part_grp, type='plug',
                         value=[self.chest_02.ctrl],
                         name='orcRigPlugs',
                         children_name=[self.chest_jnt + '_orient'])

        # add space plugs
        target_list = ['CHAR', 'Cn_global_CTRL', 'Cn_root_02_CTRL',
                       'Cn_spine_03_FK_CTRL', '3']
        name_list = ['world', 'global', 'root', 'spine', 'default_value']
        point_names = ['point' + n.title() for n in name_list]
        orient_names = ['orient' + n.title() for n in name_list]

        nmAttr.Attribute(node=self.part_grp, type='plug',
                         value=target_list,
                         name=self.chest_01.ctrl + '_point',
                         children_name=point_names)

        nmAttr.Attribute(node=self.part_grp, type='plug',
                         value=target_list,
                         name=self.chest_01.ctrl + '_orient',
                         children_name=orient_names)

        # add transferAttributes plug
        nmAttr.Attribute(node=self.part_grp, type='plug',
                         value=[self.chest_01.ctrl], name='transferAttributes',
                         children_name=['Cn_spine_tip_CTRL'])
