import maya.cmds as cmds

class RigBase(object):
    def __init__(self, model_path=None):
        self.model_path = model_path
        
    
    def create_module(self, name=None):
        self.rig_hierarchy()
        self.load_model(name)
        
    def rig_hierarchy(self):
        self.root = self.rig_group(name = "CHAR")
        self.model = self.rig_group(name="MODEL", parent = self.root)
        self.rig = self.rig_group(name = "RIG", parent = self.root)
        self.skel = self.rig_group(name = "SKEL", parent = self.root)
        
    def load_model(self, name):
        print("HELLO")
        if self.model_path == 'cylinder':
            model = cmds.polyCylinder(name = name, radius = 1, height=6, subdivisionsX = 8, subdivisionsY= 6, axis = (0,1,0), ch=False)[0]
            
            cmds.xform(model, translation = (0,3,0), worldSpace = True)
            cmds.parent(model, self.model)
            
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
        self.base_Mname = self.side +"_" + self.part+"_Mesh"
        
        
    def create_module(self):
        super(RigModule, self).create_module(self.base_Mname)
        self.part_hierarchy()
        
    def part_hierarchy(self):
        self.part_grp = self.rig_group(name= self.base_name, parent = self.rig)
        self.module_grp = self.rig_group(name= self.base_name + "_MODULE", parent = self.part_grp)
        self.control_grp = self.rig_group(name= self.base_name + "_CONTROL", parent = self.part_grp)
        
    
rig_object = RigModule(side = "l", part = "arm", model_path = 'cylinder')
rig_object.create_module()
        
        
        
            
    