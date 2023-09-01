import maya.cmds as cmds

class RigBase(object):
    def __init__(self, model_path=None):
        self.model_path = model_path
        
    
    def create_module(self):
        self.rig_hierarchy()
        self.load_model()
        
    def rig_hierarchy(self):
        self.root = self.rig_group(name = "CHAR")
        self.model = self.rig_group(name="MODEL", parent = self.root)
        self.rig = self.rig_group(name = "RIG", parent = self.root)
        self.skel = self.rig_group(name = "SKEL", parent = self.root)
        
    def load_model(self):
        if self.model_path == 'cylinder':
            self.modelname = cmds.polyCylinder(radius = 1, height=6, subdivisionsX = 8, subdivisionsY= 6, axis = (0,1,0), ch=False)[0]
            
            cmds.xform(self.modelname, translation = (0,3,0), worldSpace = True)
            cmds.parent(self.modelname, self.model)
            
        else: 
            pass
            
    def rig_group(self, empty=True, name=None, **kwargs):
        if not cmds.objExists(name):
            grp= cmds.group(empty=empty, name=name, **kwargs)
        else:
            grp=name
        return grp


       
class RigModule(RigBase):
    def __init__(self, side=None, part=None, model_path=None):
        self.side = side
        self.part = part
        self.model_path = model_path
        
        if not self.side:
            self.side = 'Cn'
            
        if not self.part:
            self.part = 'default'
            
        self.base_name = self.side +"_" + self.part
        
        
    def create_module(self):
        super(RigModule, self).create_module()
        self.part_hierarchy()
        
    def part_hierarchy(self):
        self.part_grp = self.rig_group(name= self.base_name, parent = self.rig)
        self.module_grp = self.rig_group(name= self.base_name + "_MODULE", parent = self.part_grp)
        self.control_grp = self.rig_group(name= self.base_name + "_CONTROL", parent = self.part_grp)
        
    


class Chain:
    def __init__(self, name=None, position_list = [(0,0,0), (0,1,0)]):
        self.name = name
        self.position_list = position_list
        self.build_joints()
        
    def build_joints(self):
        self.joint_list = []
        par = None
        for i, pos in enumerate(self.position_list):
            jnt = cmds.joint(par, p=pos, name='{}_{:03}_JNT'.format(self.name, i + 1))
            par = jnt
            self.joint_list.append(jnt)


class Ctrl:
    def __init__(self, name=None, suffix='CTRL'):
        self.name=name
        self.suffix= suffix
        
        self.ctrl_name = name+"_"+ suffix
        
    def create_control(self):
        self.ctrl = cmds.circle(name= self.name, normal= (0,1,0), radius = 1.5, ch=False)[0]


class Fk(Ctrl, Chain):
    def __init__(self, name=None, position_list=[]):
        self.name = name
        self.position_list=position_list
        self.control_list = []
        
    def build_fk(self):
        self.build_joints()
        
        for i, jnt in enumerate(self.joint_list):
            self.ctrl_name= jnt.replace("JNT", "CTRL")
            self.create_control()
            self.control_list.append(self.ctrl)
            cmds.matchTransform(self.ctrl, jnt)
            cmds.makeIdentity(self.ctrl, apply=True)
            cmds.parentConstraint(self.ctrl, jnt, mo=True)
            
            if i>0:
                cmds.parent(self.ctrl, self.control_list[i-1])
            
            
class RigFkPart(RigModule):
    def __init__(self, side=None, part=None, model_path=None, position_list=[]):
        super(RigFkPart, self).__init__(side=side, part=part, model_path=model_path)
        
        self.position_list = position_list
        self.create_module()
        
    def create_module(self):
        super(RigFkPart, self).create_module()
        fk_module = Fk(name=self.base_name, position_list=self.position_list)
        fk_module.build_fk()
        
        cmds.parent(fk_module.control_list[0], self.control_grp)
        cmds.parent(fk_module.joint_list[0], self.skel)
        
        self.bind_joints = fk_module.joint_list
       
       
        
fk_part = RigFkPart(model_path = "cylinder", position_list =[(0,0,0),(0,1,0),(0,2,0),(0,3,0),(0,4,0),(0,5,0),(0,6,0)] )

cmds.skinCluster(fk_part.bind_joints, fk_part.modelname, toSelectedBones = True)  
   
        
    
            
            
        
        
                
        
        
        