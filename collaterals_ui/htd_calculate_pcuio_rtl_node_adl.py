from htd_utilities import *
import math
from copy import deepcopy
#--------------------------

def check_compulsory_dictionary_keys(all_dict_list, key_name, error_message):
    if (key_name not in all_dict_list.keys()):
        htdte_logger.error(error_message)

def check_key_in_dictionary(dictionary, dict_key, error_message):
    if (dict_key not in dictionary.keys()):
        htdte_logger.error(error_message)

def htd_update_pcuio_rtl_node_icl(dict_name, dictionary, all_dict_list, CFG, debug=0):
    check_compulsory_dictionary_keys(all_dict_list, "pcu_io_indexes"," Missing expected pcu_io_indexes dictionary - handling per PCUIO INDEX by parsing $MODEL_ROOT/target/gen/pcode/pcu_info.vh  ")
    check_compulsory_dictionary_keys(all_dict_list, "pcu_io_indexes"," Missing expected pcuioreg_scope dictionary - handling per PCUIO scope by parsing $MODEL_ROOT/subIP/punit/source/punit/rtl/ptpcfsms.vs $MODEL_ROOT/subIP/punit/source/punit/rtl/ptpcbclk.vs  $MODEL_ROOT/subIP/punit/source/punit/rtl/ptpcioregs.vs")
    check_key_in_dictionary(dictionary, "pcu_io"," Missing \"pcu_io\" registerFile expected in cr_info dictionary - handling criff register definition  ")
    check_key_in_dictionary(dictionary["pcu_io"], "register"," Missing \"pcu_io\" registerFile expected in cr_info dictionary - handling criff register definition  ")
    check_key_in_dictionary(CFG, "PCUIO_RTL_NODE_Name"," Missing \"PCUIO_RTL_NODE_Name\" CFG entry in TE_cfg  - mapping pcu io scope to rtlnodeName.Example: <Var key=\"ptpcbclk\"   value=\"RegValOutF70nH\" />  ")
    #---------------------------------------
    for io in dictionary["pcu_io"]["register"].keys():
        if ( ("%s_INDEX") % (io) in all_dict_list["pcu_io_indexes"]):
	    path=""
#            io_index = all_dict_list["pcu_io_indexes"][("%s_INDEX") % (io)]
            if (io in all_dict_list["pcuioreg_scope"].keys()):
                if (all_dict_list["pcuioreg_scope"][io] not in CFG["PCUIO_RTL_NODE_Name"].keys()):
                    htdte_logger.error((" Missing  IO scope key \"%s\" in CFG[\"PCUIO_RTL_NODE_Name\"]  in TE_cfg  - mapping pcu io scope to rtlnodeName.Example: <Var key=\"ptpcbclk\"   value=\"RegValOutF70nH\" />  ") % (all_dict_list["pcuioreg_scope"][io]))
                if os.environ.get('HTD_PROJ') == None:
                  htdte_logger.error("please define at te_cfg HTD_PROJ env var")
                else:
                    path = ("%s.%s.%s") % (all_dict_list["pcuioreg_scope"][io], CFG["PCUIO_RTL_NODE_Name"][all_dict_list["pcuioreg_scope"][io]],io.lower())
            #--TODO:review these registers with Alexse
            else:
                if (io in CFG["PCUIO_DEBUG_REG_RTL_NODE_Name"].keys()):
                    all_dict_list["pcuioreg_scope"][io] = "pcuctld"
                    path = CFG["PCUIO_DEBUG_REG_RTL_NODE_Name"][io]
            for field in dictionary["pcu_io"]["register"][io]["field"].keys():
                lsb = dictionary["pcu_io"]["register"][io]["field"][field]["bitOffset"]
                msb = lsb + dictionary["pcu_io"]["register"][io]["field"][field]["bitWidth"] - 1
                width = msb - lsb
                if(path!=""):
					if( all_dict_list["pcuioreg_scope"][io] == "pcuctld"):
						dictionary["pcu_io"]["register"][io]["field"][field]["rtlPath"] = ("%s[%d:%d]") % (path, msb, lsb)
					else:
						if (width > 0):
							dictionary["pcu_io"]["register"][io]["field"][field]["rtlPath"] = ("%s.%s[%d:%d]") % (path,field.lower(),width,0)
						else:
							dictionary["pcu_io"]["register"][io]["field"][field]["rtlPath"] = ("%s.%s") % (path,field.lower()) 
                if (debug): print  ("RtlPath(%s.%s): %s") % (io, field, dictionary["pcu_io"]["register"][io]["field"][field]["rtlPath"])

#for adl :
#dictionary["pcu_io"]["register"][io]["field"][field]["rtlPath"] = ("%s[%d:%d]") % (path, msb, lsb)
#1. use for scope match:
#/p/hdk/rtl/models/xhdk74/adl/soc/soc-adl-a0-19ww16a/target/gen/pcode/ptpcbclk_io_definitions.vs
#/p/hdk/rtl/models/xhdk74/adl/soc/soc-adl-a0-19ww16a/target/gen/pcode/ptpcfsms_io_definitions.vs
#/p/hdk/rtl/models/xhdk74/adl/soc/soc-adl-a0-19ww16a/target/gen/pcode/ptpcioregs_io_definitions.vs
#2.
#PunitIOoutput_ptpcbclk CFG["PCUIO_RTL_NODE_Name"]
#PunitIOoutput_ptpcfsms CFG["PCUIO_RTL_NODE_Name"]
#PunitIOoutput_ptpcioregs CFG["PCUIO_RTL_NODE_Name"]
#path = ("%s.%s.%s[0][0]") % ("punit", CFG["PCUIO_RTL_NODE_Name"][all_dict_list["pcuioreg_scope"][io]],io.lower())


    #---Reorganize PCUIO dictionary by register files per scope:ptpcfsms,ptpcbclk,ptpcioregs----------------
    io_l = dictionary["pcu_io"]["register"].keys()
    for io in io_l:
        if (io in all_dict_list["pcuioreg_scope"].keys()):
            #---Create and copy register files as per category
            regFileScope = all_dict_list["pcuioreg_scope"][io]
        #--TODO:review these registers with  Alexse
        else:
            regFileScope = "debug";
        if (regFileScope not in dictionary.keys()):
            dictionary[regFileScope] = {}
            dictionary[regFileScope]["register"] = {}
        if (io not in dictionary[regFileScope]["register"].keys()):
            dictionary[regFileScope]["register"][io] = deepcopy(dictionary["pcu_io"]["register"][io])
            del (dictionary["pcu_io"]["register"][io])

    del (dictionary["pcu_io"])
    del (all_dict_list["pcuioreg_scope"])
    del (all_dict_list["pcu_io_indexes"])
