import maya.cmds as cmds


    
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
                
joints = Chain(name="cylinder", position_list = [(0,0,0), (0,1,0)] )

joints.joint_list



class Ctrl:
    def __init__(self, name=None, suffix='CTRL'):
        self.name=name
        self.suffix= suffix
        
        self.ctrl_name = name+"_"+ suffix
        
    def create_control(self):
        self.ctrl = cmds.circle(name= self.name, normal= (0,1,0), radius = 1.5, ch=False)[0]
        
start = Ctrl(name="cylinder")
start.create_control()
print start.ctrl




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
                
fk_module = Fk(name="Cylinder", position_list=[(0,0,0),(0,1,0),(0,2,0),(0,3,0),(0,4,0),(0,5,0),(0,6,0)])
fk_module.build_fk()        
            
            
            
        
        
                
        
        
        