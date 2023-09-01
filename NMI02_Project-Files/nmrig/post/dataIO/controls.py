import maya.cmds as cmds
import json
import os

import nmrig.libs.control.ctrl as nmCtrl
reload(nmCtrl)

def write_controls(directory, name='control_curves', force=False):
    curve_data = {}
    for c_dict in cmds.ls('*.ctrlDict'):
        ctrl_name = c_dict.split('.')[0]
        ctrl = nmCtrl.Control(ctrl=ctrl_name)
        ctrl_info = ctrl.get_curve_info()
        curve_data[ctrl_name] = ctrl_info

    json_path = '{}/{}.json'.format(directory, name)
    json_dump = json.dumps(curve_data, indent=4)

    # write shapes if forced or file does not exist
    if force or os.path.isfile(json_path) == False:
        json_file = open(json_path, 'w')
        json_file.write(json_dump)
        json_file.close()
    else:
        cmds.error('The shape you are trying to save already exists in ' +
                   'the specified directory, please use a different name, ' +
                   'delete the existing file, or use the force flag to ' +
                   'overwrite.')


def read_controls(path):
    if os.path.isfile(path):
        json_file = open(path, 'r')
        json_data = json_file.read()
        curve_data = json.loads(json_data)
    else:
        cmds.error('Control file does not exist. You must write out control ' +
                   'shapes before reading them in.')

    for ctrl_info in curve_data.values():
        for shp in ctrl_info:
            if cmds.objExists(shp):
                for i, pos in enumerate(ctrl_info[shp]['cv_pose']):
                    cmds.xform('{}.cv[{}]'.format(shp, i), objectSpace=True,
                               translation=pos)
