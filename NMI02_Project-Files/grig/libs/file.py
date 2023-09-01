import maya.cmds as cmds


def import_hierarchy(path, namespace='import_hierarchy_tmp_ns'):
    cmds.file(path, i=True, namespace=namespace)
    root_list = cmds.ls(namespace + ':|*')
    root_nodes = []
    for root in root_list:
        root_nodes.append(root.split(':')[-1])
    cmds.namespace(moveNamespace=(namespace, ':'), force=True)
    cmds.namespace(removeNamespace=namespace)
    return root_nodes