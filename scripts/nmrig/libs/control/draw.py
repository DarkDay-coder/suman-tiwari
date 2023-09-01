import maya.cmds as cmds
import json
import os

import nmrig.libs.common as nmCommon


SHAPE_DIR = os.path.dirname(os.path.realpath(__file__))+'\shapes'

class Draw(object):
    def __init__(self, curve=None):
        #make sure that we are using the curve's transform node

        if curve:
            self.curve = nmCommon.get_transform(curve)
        elif len(cmds.ls(selection = True)):
            self.curve = nmCommon.get_transform(cmds.ls(selection=True)[0])
        else:
            self.curve = None


    def write_curve(self, control=None, name=None, force=False):
        if control:
            self.curve = nmCommon.get_transform(control)
        elif len(cmds.ls(selection=True)):
            sel = cmds.ls(selection=True)
            self.curve = nmCommon.get_transform(sel[0])
        elif self.curve:
            pass
        else:
            cmds.error("Please define or select a curve to write out.")


        if not name:
            name=self.curve

        #now lets get curve data

        curve_data = self.get_curve_info(self.curve)

        json_path = '{}/{}.json'.format(SHAPE_DIR, name)
        json_dump = json.dumps(curve_data, indent=4)

        #write a name is not defined, use the curves to write out

        if force or os.path.isfile(json_path)==False:
            json_file = open(json_path, 'w')
            json_file.write(json_dump)
            json_file.close()
        else:
            cmds.error("The shape you are trying to save already exists, or use a different name of the file or delete old file.")




    def get_curve_info(self, curve=None):
        if not curve:
            curve =self.curve

        self.curve_dict = {}

        #loop through the shapes under curve's transform and collect data

        for crv in nmCommon.get_shapes(curve):
            min_value = cmds.getAttr(crv+'.minValue')
            max_value = cmds.getAttr(crv+'.maxValue')
            spans = cmds.getAttr(crv + '.spans')
            degree = cmds.getAttr(crv+ '.degree')
            form = cmds.getAttr(crv+ '.form')
            cv_len = len(cmds.ls(crv+ '.cv[*]', flatten=True))
            cv_pose = self.get_cv_positons(curve=crv , cv_len=cv_len)

            curve_info = {'min': min_value,
                          'max': max_value,
                          'spans': spans,
                          'degree': degree,
                          'form': form,
                          'cv_len': cv_len,
                          'cv_pose': cv_pose}

            self.curve_dict[crv]= curve_info

        return self.curve_dict


    def get_cv_positons(self, curve, cv_len):
        cv_pose =[]

        #query the object space translation of each cv and add it to a list
        for i in range(cv_len):
            pos = cmds.xform('{}.cv[{}]'.format(curve, i), query=True, objectSpace=True, translation =True)

            cv_pose.append(pos)

        return cv_pose


    def create_curve(self, name='default', shape='circle', axis='y', scale=1):
        #to check if the curve is a file and convert it to dict if it is
        file_path = '{}/{}.json'.format(SHAPE_DIR, shape)
        if os.path.isfile(file_path):
            json.file = open(file_path, 'r')
            json.data = json.file.read()
            curve_dict = json.loads(json.data)

        #lets rebuild the curev from our dict data

        for i, shp in enumerate(curve_dict):
            #get the info per shape in the dict
            info = curve_dict[shp]
            #if this is the first time through the loop, create our main curve
            point_info = []

            for point_list in info['cv_pose']:
                point =[p * scale for p in point_list]
                point_info.append(point)

            if i==0:
                self.curve = cmds.curve(point =point_info, degree = info['degree'], name = name)
                crv_shape = nmCommon.get_shapes(self.curve)[0]


            # if there is a more than a one curve, parent the addition shape to the main curve

            else:
                child_crv = cmds.curve(point = point_info, degree = info['degree'])
                crv_shape = nmCommon.get_shapes(child_crv)[0]

                cmds.parent(crv_shape, self.curve, shape=True, relative=True)
                cmds.delete(child_crv)


            #check to see if the curve needs to be closed

            if info['form']>=1:
                cmds.closeCurve(crv_shape, ch=False, preserveShape = 0, replaceOriginal=True)

        #rename all child shapes

        curve_shapes = nmCommon.get_shapes(self.curve)
        for i, shp in enumerate(curve_shapes):
            if i==0:
                cmds.rename(shp, self.curve+"Shape")

            else:
                cmds.rename(shp, '{}Shape_{}'.format(self.curve, i))
            #for aming the control down at a correct axis

        if not axis =='y':
            self.set_axis(axis)








    def combine_curve(self, curve=None, shapes=None):
        if not curve:
            curve = self.curve
            cmds.makeIdentity(curve, apply=True)

        if not shapes:
            shapes = cmds.ls(selection =True)

        all_shapes = []

        for s in shapes:
            shape_list = nmCommon.get_shapes(s)
            print(s)

            if shape_list:
                all_shapes += shape_list
                print(all_shapes)

        for s in all_shapes:
            transform = cmds.listRelatives(s, parent=True)
            cmds.makeIdentity(transform, apply=True)
            print("FOR S LOOP")
            print(s)

            if cmds.listRelatives(s, parent=True)[0] == self.curve:
                continue
            cmds.parent(s, curve, shape=True, relative =True)
            if not cmds.listRelatives(transform, allDescendents =True):
                cmds.delete(transform)



    def set_axis(self, axis='y'):
        axis_dict = {'x': [90,0, 0],
                     '-x':[-90,0,0],
                     'y': [0,90,0],
                     '-y':[0,-90,0],
                     'z': [0, 0, 90],
                     '-z': [0, 0,-90]
                     }
        cmds.setAttr(self.curve + '.rotate', *axis_dict[axis])
        cmds.refresh()

        cmds.makeIdentity(self.curve, apply=True)



#
# crv_info = get_curve_info(curve="curve1")
# cv_list = get_cv_positons("curve1", crv_info['curveShape1']['cv_len'])
#
# cmds.curve(point=cv_list, degree=crv_info['curveShape1']['degree'], name="samircrv")
