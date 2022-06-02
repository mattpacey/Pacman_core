from htd_utilities import *
import math
from copy import deepcopy
# --------------------------


def check_compulsory_dictionary_keys(all_dict_list, key_name, error_message):
    if (key_name not in list(all_dict_list.keys())):
        htdte_logger.error(error_message)


def check_key_in_dictionary(dictionary, dict_key, error_message):
    if (dict_key not in list(dictionary.keys())):
        htdte_logger.error(error_message)


def htd_update_pcuio_rtl_node_cnl(dict_name, dictionary, all_dict_list, CFG, debug=0):
    check_compulsory_dictionary_keys(all_dict_list, "pcu_io_indexes", " Missing expected pcu_io_indexes dictionary - handling per PCUIO INDEX by parsing $MODEL_ROOT/target/gen/pcode/pcu_info.vh  ")
    check_compulsory_dictionary_keys(all_dict_list, "pcu_io_indexes", " Missing expected pcuioreg_scope dictionary - handling per PCUIO scope by parsing $MODEL_ROOT/subIP/punit/source/punit/rtl/ptpcfsms.vs $MODEL_ROOT/subIP/punit/source/punit/rtl/ptpcbclk.vs  $MODEL_ROOT/subIP/punit/source/punit/rtl/ptpcioregs.vs")
    check_key_in_dictionary(dictionary, "pcu_io", " Missing \"pcu_io\" registerFile expected in cr_info dictionary - handling criff register definition  ")
    check_key_in_dictionary(dictionary["pcu_io"], "register", " Missing \"pcu_io\" registerFile expected in cr_info dictionary - handling criff register definition  ")
    check_key_in_dictionary(CFG, "PCUIO_RTL_NODE_Name", " Missing \"PCUIO_RTL_NODE_Name\" CFG entry in TE_cfg  - mapping pcu io scope to rtlnodeName.Example: <Var key=\"ptpcbclk\"   value=\"RegValOutF70nH\" />  ")
    # ---------------------------------------
    for io in list(dictionary["pcu_io"]["register"].keys()):
        io_index = -1
        io_instance = 0
        path = ""
        reg_name = io
        # 1.0 - trying to match register of type <name>_<instance_num>
        m = re.match("^([A-z0-9_]+)_([0-9])$", io)
        if(m):
            if(("%s_INDEX") % (m.groups()[0]) in all_dict_list["pcu_io_indexes"]):
                io_index = all_dict_list["pcu_io_indexes"][("%s_INDEX") % (m.groups()[0])]
                io_instance = int(m.groups()[1])
                reg_name = m.groups()[0]
        else:
            # 2.0 - trying to match register of type <name>_CORE<num> or <name>_THREAD<num>
            m = re.match("^([A-z0-9_]+)_(CORE|THREAD)([0-9])$", io)
            if(m):
                if(("%s_INDEX") % (m.groups()[0]) in all_dict_list["pcu_io_indexes"]):
                    io_index = all_dict_list["pcu_io_indexes"][("%s_INDEX") % (m.groups()[0])]
                    io_instance = int(m.groups()[2])
                    reg_name = m.groups()[1]
            else:
                if (("%s_INDEX") % (io) in all_dict_list["pcu_io_indexes"]):
                    io_index = all_dict_list["pcu_io_indexes"][("%s_INDEX") % (io)]
        # ---------------------------------
        if(io_index >= 0):
            if (reg_name in list(all_dict_list["pcuioreg_scope"].keys())):
                if (all_dict_list["pcuioreg_scope"][reg_name] not in list(CFG["PCUIO_RTL_NODE_Name"].keys())):
                    htdte_logger.error((" Missing  IO scope key \"%s\" in CFG[\"PCUIO_RTL_NODE_Name\"]  in TE_cfg  - mapping pcu io scope to rtlnodeName.Example: <Var key=\"ptpcbclk\"   value=\"RegValOutF70nH\" />  ") % (all_dict_list["pcuioreg_scope"][io]))
                path = ("%s.%s[%d][0][%d]") % (all_dict_list["pcuioreg_scope"][reg_name], CFG["PCUIO_RTL_NODE_Name"][all_dict_list["pcuioreg_scope"][reg_name]], io_index, io_instance)
            # --TODO:review these registers with Alexse
            else:
                if (io in list(CFG["PCUIO_DEBUG_REG_RTL_NODE_Name"].keys())):
                    all_dict_list["pcuioreg_scope"][io] = "pcuctld"
                    path = CFG["PCUIO_DEBUG_REG_RTL_NODE_Name"][io]
            for field in list(dictionary["pcu_io"]["register"][io]["field"].keys()):
                lsb = dictionary["pcu_io"]["register"][io]["field"][field]["bitOffset"]
                msb = lsb + dictionary["pcu_io"]["register"][io]["field"][field]["bitWidth"] - 1
                if(path != ""):
                    dictionary["pcu_io"]["register"][io]["field"][field]["rtlPath"] = ("%s[%d:%d]") % (path, msb, lsb)
                    if (debug):
                        print(("RtlPath(%s.%s): %s") % (io, field, dictionary["pcu_io"]["register"][io]["field"][field]["rtlPath"]))

    # ---Reorganize PCUIO dictionary by register files per scope:ptpcfsms,ptpcbclk,ptpcioregs----------------
    io_l = list(dictionary["pcu_io"]["register"].keys())
    for io in io_l:
        if (io in list(all_dict_list["pcuioreg_scope"].keys())):
            # ---Create and copy register files as per category
            regFileScope = all_dict_list["pcuioreg_scope"][io]
        # --TODO:review these registers with  Alexse
        else:
            regFileScope = "debug"
        if (regFileScope not in list(dictionary.keys())):
            dictionary[regFileScope] = {}
            dictionary[regFileScope]["register"] = {}
        if (io not in list(dictionary[regFileScope]["register"].keys())):
            dictionary[regFileScope]["register"][io] = deepcopy(dictionary["pcu_io"]["register"][io])
            del (dictionary["pcu_io"]["register"][io])

    del (dictionary["pcu_io"])
    del (all_dict_list["pcuioreg_scope"])
    del (all_dict_list["pcu_io_indexes"])
