import maya.cmds as cmds


class Group:
    def group_by_list(self, nodes, pad_name_list, name=None):
        self.group_list = []
        nodes = self.get_node_list(nodes)

        for node in nodes:
            if not name:
                name = node

            for grp_name in pad_name_list[::-1]:
                grp = cmds.group(em=True, name=name + '_' + grp_name + '_GRP')
                if grp_name != pad_name_list[-1]:
                    cmds.parent(self.top, grp)
                else:
                    self.bot = grp
                self.top = grp
                self.group_list.append(grp)
            cmds.parent(node, self.bot)

    def group_by_int(self, nodes, group_num, name=None):
        self.group_list = []
        nodes = self.get_node_list(nodes)
        num_len = len(str(group_num)) + 1
        for node in nodes:
            if not name:
                name = node

            for i in range(group_num):
                grp = cmds.group(em=True, name=name + '_' +
                                               str(i + 1).zfill(num_len) +
                                               '_OFF_GRP')
                if i < 1:
                    self.bot = grp
                else:
                    cmds.parent(self.top, grp)
                self.top = grp
                self.group_list.append(grp)
            cmds.parent(node, self.bot)

    def get_node_list(self, nodes):
        if isinstance(nodes, list):
            return nodes
        else:
            nodes = [nodes]
            return nodes
