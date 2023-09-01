import maya.cmds as cmds

mp="C:/Users/Panauti/Documents/maya/2020/scripts/ninja/model/ninja_model_mesh.mb"
gp="C:/Users/Panauti/Documents/maya/2020/scripts/ninja/guides/ninja_model_guide.mb"
import nmrig.build.buildPart as nmPart
#reload(nmPart)
cmds.file(new=True, f=True)
root = nmPart.build_module(module_type="root", side="Cn",part="root", model_path=mp, guide_path=gp)
cmds.viewFit("perspShape", fitFactor=1, all=True, animate=True)
hip = nmPart.build_module(module_type="hip", side="Cn",part="hip", ctrl_scale=55, guide_list=["Hips"])
chest = nmPart.build_module(module_type="chest", side="Cn",part="chest", ctrl_scale=55, guide_list=["Spine1"])

