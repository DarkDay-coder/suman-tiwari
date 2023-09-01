import maya.cmds as cmds


def build_joints(name="default_name", position_list=[(3, 6, 0), (6, 6, -1), (9, 6, 0)]):
    joint_list = []
    par = None
    for i, pos in enumerate(position_list):
        jnt = cmds.joint(par, p=pos, name='{}_{:03}_JNT'.format(name, i + 1))
        print(pos)
        par = jnt
        joint_list.append(jnt)
    return joint_list


joints = build_joints()


class Limb:
    def __init__(self, side=None, part=None, position_list=None):
        self.side = side
        self.part = part
        self.position_list = position_list
        self.base_name = self.side + "_" + self.part
        self.build_limb()

    def build_limb(self):
        self.build_chain()
        self.build_ikh()

    def build_chain(self):
        self.joints = build_joints(name=self.base_name, position_list=self.position_list)

    def build_ikh(self):
        self.ikh = cmds.ikHandle(name=self.base_name + "_IKH", startJoint=self.joints[0], endEffector=self.joints[-1],
                                 sticky='sticky', solver='ikSCsolver')[0]



l_arm = Limb(side="l", part="arm", position_list=[(3, 6, 0), (6, 6, -1), (9, 6, 0)])
