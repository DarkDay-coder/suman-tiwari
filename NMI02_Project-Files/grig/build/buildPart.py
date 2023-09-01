import maya.cmds as cmds

import grig.build.parts.root as gnRoot
import grig.build.parts.hip as gnHip
import grig.build.parts.chest as gnChest
import grig.build.parts.fkChain as gnFkChain
import grig.build.parts.ikChain as gnIkChain
import grig.build.parts.bipedLimb as gnLimb
import grig.build.parts.clavicle as gnClavicle
import grig.build.parts.spine as gnSpine
import grig.build.parts.neck as gnNeck
import grig.build.parts.head as gnHead
import grig.build.parts.hand as gnHand
import grig.build.parts.finger as gnFinger
import grig.build.parts.foot as gnFoot
import grig.build.parts.eyes as gnEyes
import grig.libs.attribute as gnAttr
reload(gnRoot)
reload(gnHip)
reload(gnChest)
reload(gnIkChain)
reload(gnFkChain)
reload(gnLimb)
reload(gnClavicle)
reload(gnSpine)
reload(gnNeck)
reload(gnHead)
reload(gnHand)
reload(gnFinger)
reload(gnFoot)
reload(gnEyes)
reload(gnAttr)

MODULE_DICT = {'root': gnRoot.Root,
               'hip': gnHip.Hip,
               'chest': gnChest.Chest,
               'fk': gnFkChain.FkChain,
               'ik': gnIkChain.IkChain,
               'bipedLimb': gnLimb.BipedLimb,
               'clavicle': gnClavicle.Clavicle,
               'spine': gnSpine.Spine,
               'neck': gnNeck.Neck,
               'head': gnHead.Head,
               'hand': gnHand.Hand,
               'finger': gnFinger.Finger,
               'foot': gnFoot.Foot,
               'eyes': gnEyes.Eyes}


def build_module(module_type, **kwargs):
    module = MODULE_DICT[module_type](**kwargs)

    gnAttr.Attribute(node=module.part_grp, type='string', name='moduleType',
                     value=module_type, lock=True)

    cmds.refresh()
    return module

