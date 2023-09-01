import maya.cmds as cmds


class Attribute:
    def __init__(self,
                 add=True,
                 type=None,
                 node=None,
                 name=None,
                 children_name=None,
                 enum_list=None,
                 min=None,
                 max=None,
                 value=None,
                 keyable=None,
                 lock=False,
                 transfer_to=None):
        self.type = type
        self.node = node
        self.name = name
        self.children_name = children_name
        self.enum_list = enum_list
        self.min = min
        self.max = max
        self.value = value
        self.keyable = keyable
        self.lock = lock
        self.transfer_to = transfer_to

        if self.min == None:
            self.hasMinValue = False
        else:
            self.hasMinValue = True

        if self.max == None:
            self.hasMaxValue = False
        else:
            self.hasMaxValue = True

        if self.name and self.node:
            self.attr = self.node + '.' + self.name

        if add:
            if not self.type:
                cmds.error('Must provide attribute type when adding attributes.')
            self.add_attr()

        if self.lock:
            self.lock_attr(self.attr)

        # if self.transfer_to:
        #     self.transfer_attr()

    def transfer_attr(self, connect=True):
        old_attr = self.attr
        self.get_attr()
        self.node = self.transfer_to
        self.add_attr()
        if connect:
            cmds.connectAttr(self.attr, old_attr)

    def get_attr(self):
        if not self.type:
            self.type = cmds.getAttr(self.attr, type=True)

        if not self.min:
            self.min = cmds.attributeQuery(self.name, node=self.node,
                                           minimum=True)[0]

        if not self.max:
            self.max = cmds.attributeQuery(self.name, node=self.node,
                                           maximum=True)[0]

        if not self.value:
            self.value = cmds.getAttr(self.attr)

        if not self.keyable:
            self.keyable = cmds.getAttr(self.attr, keyable=True)

        if self.min == None:
            self.hasMinValue = False
        else:
            self.hasMinValue = True

        if self.max == None:
            self.hasMaxValue = False
        else:
            self.hasMaxValue = True

    def add_attr(self):
        self.attr = self.node + '.' + self.name
        type_dict = {'bool': self.add_bool,
                     'double': self.add_double,
                     'double3': self.add_double3,
                     'string': self.add_string,
                     'enum': self.add_enum,
                     'separator': self.add_separator,
                     'plug': self.add_plug}
        type_dict[self.type]()

        if self.type == 'plug':
            self.value = self.children_name
        else:
            self.value = cmds.getAttr(self.attr)

    def add_string(self):
        cmds.addAttr(self.node, longName=self.name, dataType='string')
        cmds.setAttr(self.attr, self.value, type='string')

    def add_bool(self):
        cmds.addAttr(self.node,
                     attributeType='bool',
                     defaultValue=self.value,
                     keyable=self.keyable,
                     longName=self.name)

    def add_double(self):
        cmds.addAttr(self.node,
                     attributeType='double',
                     hasMinValue=self.hasMinValue,
                     hasMaxValue=self.hasMaxValue,
                     defaultValue=self.value,
                     keyable=self.keyable,
                     longName=self.name)

        if self.hasMinValue:
            cmds.addAttr(self.attr, edit=True, min=self.min)
        if self.hasMaxValue:
            cmds.addAttr(self.attr, edit=True, max=self.max)

    def add_double3(self):
        cmds.addAttr(self.node,
                     attributeType='double3',
                     hasMinValue=self.hasMinValue,
                     hasMaxValue=self.hasMaxValue,
                     keyable=self.keyable,
                     longName=self.name)

        # add all children attributes
        for child in self.children_name:
            cmds.addAttr(self.node,
                         parent=self.name,
                         attributeType='double',
                         hasMinValue=self.hasMinValue,
                         hasMaxValue=self.hasMaxValue,
                         defaultValue=self.value,
                         keyable=self.keyable,
                         longName=self.name + child)

        # set min/max values on children
        for child in self.children_name:
            child_attr = self.attr + child
            if self.hasMinValue:
                cmds.addAttr(child_attr, edit=True, min=self.min)
            if self.hasMaxValue:
                cmds.addAttr(child_attr, edit=True, max=self.max)

    def add_plug(self):
        cmds.addAttr(self.node,
                     numberOfChildren=len(self.children_name),
                     attributeType='compound',
                     longName=self.name)
        for child in self.children_name:
            cmds.addAttr(self.node, longName=child, dt='string',
                         parent=self.name)
        for plug, val in zip(cmds.listAttr(self.attr)[1:], self.value):
            cmds.setAttr(self.node + '.' + plug, val, type='string')

    def add_enum(self):
        if self.enum_list:
            enum_name = ':'.join(self.enum_list) + ':'
        cmds.addAttr(self.node,
                     attributeType='enum',
                     defaultValue=self.value,
                     enumName=enum_name,
                     keyable=self.keyable,
                     longName=self.name)

    def add_separator(self):
        cmds.addAttr(self.node,
                     attributeType='enum',
                     enumName='______',
                     keyable=False,
                     longName=self.name)
        cmds.setAttr(self.attr, cb=True)

    def lock_attr(self, attr):
        if not attr:
            attr = self.attr
        cmds.setAttr(attr, l=True)

    def lock_and_hide(self, node=None, translate=True, rotate=True, scale=True,
                      visibility=True, attribute_list=None):
        if not node:
            node = self.node

        for axis in 'XYZ':
            if translate:
                if isinstance(translate, str) and axis not in translate:
                    continue
                else:
                    pass
                cmds.setAttr('{}.translate{}'.format(node, axis), lock=True)
                cmds.setAttr('{}.translate{}'.format(node, axis),
                             keyable=False)
            if rotate:
                if isinstance(rotate, str) and axis not in rotate:
                    continue
                else:
                    pass
                cmds.setAttr('{}.rotate{}'.format(node, axis), lock=True)
                cmds.setAttr('{}.rotate{}'.format(node, axis),
                             keyable=False)
            if scale:
                if isinstance(scale, str) and axis not in scale:
                    continue
                else:
                    pass
                cmds.setAttr('{}.scale{}'.format(node, axis), lock=True)
                cmds.setAttr('{}.scale{}'.format(node, axis), keyable=False)

        if visibility:
            cmds.setAttr(node + '.visibility', lock=True)
            cmds.setAttr(node + '.visibility', keyable=False)

        if attribute_list:
            for attr in attribute_list:
                cmds.setAttr('{}.{}'.format(node, attr), lock=True)
                cmds.setAttr('{}.{}'.format(node, attr), keyable=False)