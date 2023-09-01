import maya.cmds as cmds

import nmrig.build.parts.root as nmRoot
import nmrig.build.parts.chest as nmChest
import nmrig.build.parts.hip as nmHip
import nmrig.build.parts.bipedLimb as nmLimb
import nmrig.build.parts.finger as nmFinger
import nmrig.libs.attribute as nmAttr
import nmrig.build.parts.clavicle as nmClavicle
import nmrig.build.parts.hand as nmHand
import nmrig.build.parts.foot as nmFoot
reload(nmLimb)
reload(nmClavicle)

MODULE_DICT = {'root': nmRoot.Root,
               'hip': nmHip.Hip,
               'chest': nmChest.Chest,
               'limb': nmLimb.BipedLimb,
               'finger': nmFinger.Finger,
               'clavicle':nmClavicle.Clavicle,
               'hand': nmHand.Hand,
               'foot':nmFoot.Foot
               }


def build_module(module_type, **kwargs):
    module = MODULE_DICT[module_type](**kwargs)

    nmAttr.Attribute(node=module.part_grp, type='string', name='moduleType',
                     value=module_type, lock=True)

    cmds.refresh()
    return module
