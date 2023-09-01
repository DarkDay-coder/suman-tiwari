import maya.cmds as cmds

import nmrig.build.parts.root as nmRoot
import nmrig.build.parts.hip as nmHip
import nmrig.build.parts.chest as nmChest
import nmrig.build.parts.finger as nmFinger
import nmrig.build.parts.bipedLimb as nmLimb
import nmrig.build.parts.clavicle as nmClavicle
import nmrig.build.parts.hand as nmHand
import nmrig.build.parts.foot as nmFoot
import nmrig.build.parts.spine as nmSpine
import nmrig.build.parts.neck as nmNeck
import nmrig.build.parts.head as nmHead
import nmrig.libs.attribute as nmAttr
reload(nmRoot)
reload(nmHip)
reload(nmChest)
reload(nmFinger)
reload(nmLimb)
reload(nmClavicle)
reload(nmHand)
reload(nmFoot)
reload(nmSpine)
reload(nmNeck)
reload(nmHead)
reload(nmAttr)

MODULE_DICT = {'root': nmRoot.Root,
               'hip': nmHip.Hip,
               'chest': nmChest.Chest,
               'finger': nmFinger.Finger,
               'bipedLimb': nmLimb.BipedLimb,
               'clavicle': nmClavicle.Clavicle,
               'hand': nmHand.Hand,
               'foot': nmFoot.Foot,
               'spine': nmSpine.Spine,
               'neck': nmNeck.Neck,
               'head': nmHead.Head}


def build_module(module_type, **kwargs):
    module = MODULE_DICT[module_type](**kwargs)

    nmAttr.Attribute(node=module.part_grp, type='string', name='moduleType',
                     value=module_type, lock=True)

    cmds.refresh()
    return module
