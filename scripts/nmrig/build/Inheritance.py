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
        print("HELLO")
        if self.model_path == 'cylinder':
            model = cmds.polyCylinder(radius = 1, height=6, subdivisionsX = 8, subdivisionsY= 6, axis = (0,1,0), ch=False)[0]
            
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
        
        
        
rig_object = RigBase(model_path = "cylinder")
rig_object.create_module()
        
        
        
        
            
    