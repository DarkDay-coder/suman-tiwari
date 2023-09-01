import maya.cmds as cmds
import json
import os

import nmrig.libs.common as nmCommon
reload(nmCommon)

SHAPE_DIR = os.path.dirname(os.path.realpath(__file__)) + '\shapes'


class Draw(object):
    def __init__(self, curve=None):
        # make sure we're using the curve's transform node
        if curve:
            self.curve = nmCommon.get_transform(curve)
        elif len(cmds.ls(selection=True)):
            self.curve = nmCommon.get_transform(cmds.ls(selection=True)[0])
        else:
            self.curve = None

    def write_curve(self, control=None, name=None, force=False):
        """
        Saves selected or defined curve to shape library.

        :param control: Name of curve object you want to copy data from,
        if None, this will look for selected object and error if nothing is
        defined or selected.
        :type control: *str* or *None*

        :param name: Name to give control, this will be the name called later to
        build the curve.
        :type name: *str* or *None*

        :param force: If set to True, it will overwrite an existing curve in
        library with the same name. If False, it will give an error message when
        attempting to save over an object with the same name.
        :type force: *bool*
        """
        # make sure we either define a curve or have one selected
        # also make sure we're using the transform node
        if control:
            self.curve = nmCommon.get_transform(control)
        elif len(cmds.ls(selection=True)):
            sel = cmds.ls(selection=True)
            self.curve = nmCommon.get_transform(sel[0])
        elif self.curve:
            pass
        else:
            cmds.error('Please define or select a curve to write out.')

        # if a name is not defined, use the curves name instead
        if not name:
            name = self.curve

        # get curve data
        curve_data = self.get_curve_info(self.curve)

        json_path = '{}/{}.json'.format(SHAPE_DIR, name)
        json_dump = json.dumps(curve_data, indent=4)

        # write shape if forced or file does not exist
        if force or os.path.isfile(json_path) == False:
            json_file = open(json_path, 'w')
            json_file.write(json_dump)
            json_file.close()
        else:
            cmds.error('The shape you are trying to save already exists in ' +
                       'library, please use a different name, delete the ' +
                       'existing file, or use the force flag to overwrite.')

    def get_curve_info(self, curve=None):
        """
        Gets useful information used to rebuild curve shapes

        Example:
        curve_util = Draw('curve_name')
        curve_data = curve_util.get_curve_info()

        :param curve: Name of the control to gather info from, or None to use
        selection
        :type curve: *str* or *None*

        :return: Returns dictionary of curves and data required to rebuild them
        :rtype: *dict*
        """
        if not curve:
            curve = self.curve

        self.curve_dict = {}
        # loop through the shapes under curve's transform and collect data
        for crv in nmCommon.get_shapes(curve):
            min_value = cmds.getAttr(crv + '.minValue')
            max_value = cmds.getAttr(crv + '.maxValue')
            spans = cmds.getAttr(crv + '.spans')
            degree = cmds.getAttr(crv + '.degree')
            form = cmds.getAttr(crv + '.form')
            cv_len = len(cmds.ls(crv + '.cv[*]', flatten=True))
            cv_pose = self.get_cv_positions(curve=crv, cv_len=cv_len)

            curve_info = {'min': min_value,
                          'max': max_value,
                          'spans': spans,
                          'degree': degree,
                          'form': form,
                          'cv_len': cv_len,
                          'cv_pose': cv_pose}
            self.curve_dict[crv] = curve_info

        return self.curve_dict

    def get_cv_positions(self, curve, cv_len):
        """
        This creates a list of world space points from the given curve

        :param curve: Our curve shape node
        :type curve: *str*

        :param cv_len: Number of cvs in curve
        :type cv_len: *int*

        :return: Returs a list of cv positions in world space
        :rtype: *list*
        """
        cv_pose = []
        # query the object space translation of each cv and add it to a list
        for i in range(cv_len):
            pos = cmds.xform('{}.cv[{}]'.format(curve, i),
                             query=True, objectSpace=True,
                             translation=True)
            cv_pose.append(pos)

        return cv_pose

    def create_curve(self, name='default', shape='circle', axis='y', scale=1):
        """
        Create a curve to be used as a control.

        :param name: Name of the curve
        :type name: *str*

        :param shape: Name of curve shape where data is stored
        :type shape: *str*

        :param axis: Primary axis for the control
        :type axis: *str*

        :param scale: Scale factor for drawing the points, relative to origin
        :type scale: *int* or *str*
        """
        # check if curve dict is a file and convert it to dictionary if it is
        file_path = '{}/{}.json'.format(SHAPE_DIR, shape)
        if os.path.isfile(file_path):
            json_file = open(file_path, 'r')
            json_data = json_file.read()
            curve_dict = json.loads(json_data)
        else:
            cmds.error('Shape does not exist in library. You must write out ' +
                       'shape before creating.')

        # rebuild the curve from our data dictionary
        for i, shp in enumerate(curve_dict):
            # get the info per shape saved in dictionary
            info = curve_dict[shp]
            point_info = []
            for point_list in info['cv_pose']:
                point = [p * scale for p in point_list]
                point_info.append(point)
            # if this is the first time through the loop, create our main curve
            if i == 0:
                self.curve = cmds.curve(point=point_info,
                                        degree=info['degree'],
                                        name=name)
                crv_shape = nmCommon.get_shapes(self.curve)[0]
            # if more than one curve shape, parent the additional shape to
            # the main curve and delete the extra transform
            else:
                child_crv = cmds.curve(point=point_info,
                                       degree=info['degree'])
                crv_shape = nmCommon.get_shapes(child_crv)[0]
                cmds.parent(crv_shape, self.curve,
                            shape=True, relative=True)
                cmds.delete(child_crv)

            # check to see if the curve needs to be closed
            if info['form'] >= 1:
                cmds.closeCurve(crv_shape, constructionHistory=False,
                                preserveShape=0, replaceOriginal=True)

        # rename all child shapes
        curve_shapes = nmCommon.get_shapes(self.curve)
        for i, shp in enumerate(curve_shapes):
            if i == 0:
                cmds.rename(shp, self.curve + 'Shape')
            else:
                cmds.rename(shp, '{}Shape_{}'.format(self.curve, i))

        # aim control down correct axis
        if not axis == 'y':
            self.set_axis(axis)

    def combine_curves(self, curve=None, shapes=None):
        """
        This is a utility that can be used to combine curve under one transform

        :param curve: main control transform that shapes will be parented under
        :type curve: *str* or *None*

        :param shapes: a list of other shapes to combine under main transform
        :type shapes: *list* or *None*
        """
        if not curve:
            curve = self.curve
        cmds.makeIdentity(curve, apply=True)

        if not shapes:
            shapes = cmds.ls(selection=True)

        all_shapes = []
        for s in shapes:
            shape_list = nmCommon.get_shapes(s)
            if shape_list:
                all_shapes += shape_list

        for s in all_shapes:
            transform = cmds.listRelatives(s, parent=True)
            cmds.makeIdentity(transform, apply=True)
            if cmds.listRelatives(s, parent=True)[0] == self.curve:
                continue
            cmds.parent(s, curve, shape=True, relative=True)
            if not cmds.listRelatives(transform, allDescendents=True):
                cmds.delete(transform)

    def set_axis(self, axis='y'):
        """
        This allows us to orient our control in a different axis after it has
        been created

        :param axis: Primary axis for the control
        :type axis: *string*
        """
        axis_dict = {'x': [0, 0, -90],
                     '-x': [0, 0, 90],
                     'y': [0, 0, 0],
                     '-y': [0, 0, 180],
                     'z': [90, 0, 0],
                     '-z': [-90, 0, 0]}

        cmds.setAttr(self.curve + '.rotate', *axis_dict[axis])
        cmds.refresh()
        cmds.makeIdentity(self.curve, apply=True)

