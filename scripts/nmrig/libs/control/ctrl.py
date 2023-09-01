import maya.cmds as cmds
import nmrig.libs.control.draw as nmDraw
import nmrig.libs.group as nmGroup
import nmrig.libs.common as nmCommon
import nmrig.libs.attribute as nmAttr
import nmrig.libs.transform as nmXform



class Control(nmDraw.Draw, nmGroup.Group):
    def __init__(self, ctrl=None,
                 parent=None,
                 shape='circle',
                 prefix='Lf',
                 suffix='CTRL',
                 name='default',
                 axis='y',
                 group_type='main',
                 rig_type='primary',
                 ctrl_scale=1,
                 position=(0, 0, 0),
                 rotation=(0, 0, 0),
                 scale=(1, 1, 1)):

        self.group_dict = {'main': ['CNST', 'MOCAP', 'SDK', 'OFF'],
                           'offset': ['CNST', 'OFF']}
        self.parent = parent
        self.position = position
        self.rotation = rotation
        self.scale = scale

        self.ctrl = ctrl
        if not self.ctrl:
            self.shape = shape
            self.prefix = prefix
            self.suffix = suffix
            self.name = name
            self.axis = axis
            self.group_type = group_type
            self.rig_type = rig_type
            self.ctrl_scale = ctrl_scale
            if prefix:
                self.ctrl_name = '{}_{}_{}'.format(self.prefix, self.name,
                                                   self.suffix)
            else:
                self.ctrl_name = '{}_{}'.format(self.name, self.suffix)

            self.create()

        else:
            self.get_control()

    def create(self):
        # draw the control
        self.create_curve(name=self.ctrl_name,
                          shape=self.shape,
                          axis=self.axis,
                          scale=self.ctrl_scale)
        self.ctrl = self.curve

        # add grouping
        if isinstance(self.group_type, str):
            self.group_by_list(nodes=self.ctrl,
                               pad_name_list=self.group_dict[self.group_type],
                               name=self.ctrl_name)

        elif isinstance(self.group_type, list):
            self.group_by_list(nodes=self.ctrl,
                               pad_name_list=self.group_type,
                               name=self.ctrl_name)

        elif isinstance(self.group_type, int):
            self.group_by_int(nodes=self.ctrl,
                              group_num=self.group_type,
                              name=self.ctrl_name)

        else:
            self.group_list = None
            self.top = self.ctrl_name
            self.bot = self.ctrl_name
            # cmds.warning(self.ctrl + ' has no group padding.')

        nmXform.match_pose(node=self.top,
                           position=self.position,
                           rotation=self.rotation,
                           scale=self.scale)
        if self.parent:
            cmds.parent(self.top, self.parent)
        self.tag_control()

    def get_control(self):
        tag_dict = cmds.getAttr(self.ctrl + '.ctrlDict')
        self.control_dict = ast.literal_eval(tag_dict)
        self.curve = self.ctrl
        self.shape = self.control_dict['shape']
        self.prefix = self.control_dict['prefix']
        self.suffix = self.control_dict['suffix']
        self.name = self.control_dict['name']
        self.axis = self.control_dict['axis']
        self.group_list = self.control_dict['rig_groups']
        self.rig_type = self.control_dict['rig_type']
        self.ctrl_scale = self.control_dict['ctrl_scale']
        if self.prefix:
            self.ctrl_name = '{}_{}_{}'.format(self.prefix, self.name,
                                               self.suffix)
        else:
            self.ctrl_name = '{}_{}'.format(self.name, self.suffix)

        if self.group_list:
            self.bot = self.group_list[0]
            self.top = self.group_list[-1]

    def tag_control(self):
        self.control_dict = {'shape': self.shape,
                             'prefix': self.prefix,
                             'suffix': self.suffix,
                             'name': self.name,
                             'axis': self.axis,
                             'rig_groups': self.group_list,
                             'rig_type': self.rig_type,
                             'ctrl_scale': self.ctrl_scale}

        tag_string = str(self.control_dict)

        nmAttr.Attribute(type='string',
                         node=self.ctrl,
                         name='ctrlDict',
                         value=tag_string,
                         lock=True)