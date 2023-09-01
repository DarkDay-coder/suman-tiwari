import maya.cmds as cmds
import json
import os


def write_skin(directory, name='skin_weights', force=False):
    skin_data = build_skin_dict()
    json_path = '{}/{}.json'.format(directory, name)
    json_dump = json.dumps(skin_data, indent=4)

    # write weights if forced or file does not exist
    if force or os.path.isfile(json_path) == False:
        json_file = open(json_path, 'w')
        json_file.write(json_dump)
        json_file.close()
    else:
        cmds.error('The skin clusters you are trying to save already exist ' +
                   'in the specified directory, please use a different name, ' +
                   'delete the existing file, or use the force flag to ' +
                   'overwrite.')

    # export deformers
    for sc in skin_data:
        cmds.deformerWeights(sc + '.xml', export=True, path=directory,
                             deformer=sc)


def read_skin(directory, weights_file='skin_weights.json'):
    path = directory + weights_file
    if os.path.isfile(path):
        json_file = open(path, 'r')
        json_data = json_file.read()
        skin_data = json.loads(json_data)
    else:
        cmds.error('Skin weights file does not exist. You must write out ' +
                   'weights before reading them in.')

    for sc, sc_dict in skin_data.items():
        inf = sc_dict['influences'] + [sc_dict['geometry']]
        max_inf = sc_dict['max_influences']

        # bind geometry to influences
        if not cmds.objExists(sc):
            cmds.skinCluster(inf, maximumInfluences=max_inf,
                             toSelectedBones=True, name=sc)

        # # import weights
        cmds.deformerWeights(sc + '.xml', im=True, deformer=sc, method='index',
                             path=directory)
        cmds.skinCluster(sc, edit=True, forceNormalizeWeights=True)


def build_skin_dict():
    skin_dict = {}
    for sc in cmds.ls(type='skinCluster'):
        geo = cmds.skinCluster(sc, query=True, geometry=True)[0]
        inf = cmds.skinCluster(sc, query=True, influence=True)
        max_inf = cmds.skinCluster(sc, query=True, maximumInfluences=True)
        skin_dict[sc] = {'geometry': geo,
                         'influences': inf,
                         'max_influences': max_inf}

    return skin_dict
