# -*- coding: utf-8 -*-
import  os
import  datetime
# ======================================================================================================================
from    src.tools           import  tools                   as  t
from    src                 import  globals                 as  g
from    src.dictionaries    import  dictionary              as  d
# ======================================================================================================================

def check_event(ce_event, ce_infobase):
    return                                                                                                              # do nothing from 2019.06.11
    try:
        if not g.notify.failed_logons.get(ce_infobase):
            d.read_ib_dictionary(ce_infobase)
            ce_dict                                         =   g.execution.c1_dicts.actions[ce_infobase]
            for each in ce_dict:
                if(ce_dict[each]                            ==  "_$Session$_.AuthenticationError"):
                    g.notify.failed_logons[ce_infobase]     =   each
                    break
        if(g.notify.failed_logons.get(ce_infobase)):
            if(ce_event[8]                                  ==  int(g.notify.failed_logons[ce_infobase])):
                for ce_each_user in g.notify.select_user_re.findall(ce_event[12]):
                    ce_user                                 =   ce_each_user
                t.log_msg("Failed login "+t.normalize_ib_name(ce_infobase)+":"+ce_user)
    except Exception as e:
        t.debug_print("Exception "+str(e),"messenger")

