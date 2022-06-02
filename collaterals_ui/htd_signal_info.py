import socket
import sys
import re
import os
import subprocess
import random
from htd_utilities import *
from htd_collaterals import *


class htd_signal_info(object):

    def __init__(self):
        try:
            l = list(dict_sig_GetModulePath.keys())
        except NameError:
            htdte_logger.error(
                ("Missing \"sig_GetModulePath\" - dictionary definition in TE_cfg.xml used by HTD_INFO::htd_signal_info API class - this dictionary used to identify RTL path to each module in design. "))
        if("PKG_HIER_PATH" not in CFG["HPL"]):
            htdte_logger.error(
                "Missing CFG[HPL][PKG_HIER_PATH] - contain rtl path to DUT external signals . ")
        self.dut_pin_map = {}
        self.parse_dut_file()
    # ---------------------------

    def get_signal_by_dut_pin(self, pin_name):
        if(not self.dut_pin_defined(pin_name)):
            htdte_logger.error(
                ("Trying to retrieve not existent dut pin alias: \"%s\" ") % (pin_name))
        return (self.dut_pin_map[pin_name])
    # -------------------------------------------------------------------------

    def dut_pin_defined(self, pin_name):
        return (pin_name in list(self.dut_pin_map.keys()))
    # -------------------------------------------------------------------------

    def parse_dut_file(self):
        if("dut_pin_map_file" in list(CFG["HPL"].keys()) and CFG["HPL"]["dut_pin_map_file"] != ""):
            dut_pin_map_file = util_resolve_unix_env(
                CFG["HPL"]["dut_pin_map_file"])
            htdte_logger.inform(
                ("Found DUT Pin mapping file: %s ") % (dut_pin_map_file))
            if(not os.access(dut_pin_map_file, os.R_OK)):
                htdte_logger.inform(
                    ("Can't access DUT Pin mapping file: %s , pls. make sure file existence, permissions or disable CFG[\"HPL\"][\"dut_pin_map_file\"]") % (dut_pin_map_file))
            fh = open(dut_pin_map_file, 'r')
            htdte_logger.inform(
                ("Loading DUT Pin mapping file: %s ") % (dut_pin_map_file))
            line_num = 0
            for line in fh.readlines():
                if(len(line.strip()) == 0):
                    continue
                line_num += 1
                columns = line.split()
                if(len(columns) > 0 and (list(columns[0])[0] == '#')):
                    continue
                if(len(columns) < 2):
                    htdte_logger.inform(("Illegal format DUT Pin mapping file: %s,line:%d ") % (
                        dut_pin_map_file, line_num))
                self.dut_pin_map[columns[0]] = columns[1]
            fh.close()
    # -------------------------------------------------------------------------
    # Need for SEOLA restriction :
    # If msb-lsb>31 , reformat a signal to 32 bits chunk, return (list_of_signals,list_of_values)
    # -------------------------------------------------------------------------

    def normalize_to_32_bit_signals(self, input_signal, value, size):
        if(size < 32):
            return ([input_signal], [value])
        m = re.search(r"\[(\d+):(\d+)\]$", input_signal)
        lsb = 0
        if(m):
            msb = int(m.groups()[0])
            lsb = int(m.groups()[1])
            input_signal = re.sub(r"\[(\d+):(\d+)\]$", "", input_signal)
        res_sig = []
        res_val = []
        for i in range(0, size, 32):
            res_sig.append(("%s[%d:%d]") % (
                input_signal, lsb + i + (31 if((i + 32) < size) else size - lsb - i - 1), lsb + i))
            res_val.append(value & 0xffffffff)
            value = (value >> 32)
        return (res_sig, res_val)
    # ----------------------------------------------------

    def get_module_file_name(self):
        collateral_name = HTD_INFO.te_cfg_col[
            'sig_GetModulePath'][0]['collateral'][0]
        path_l = HTD_INFO.collaterals_list[
            collateral_name]['path'].rsplit("/", 1)
        if(len(path_l) == 2):
            return path_l[1]
        else:
            return path_l[0]
    # ---------------------------------------------------

    def get_avialable_modules(self):
        return list(dict_sig_GetModulePath.keys())
    # ----------------------------------------------------

    def signal_module_exists(self, search_module):
        # -TODO: CHECK how to configure out the list of cheef files to be loaded
        #       Do we have a centrilized cheef modele xml (not per IP) ?
        #       If we are loading per IP cheef files , how we are finding the path to IP perefiry ?
        # RES.sig_GetModulePath["module_name"] -> rtlpath
        # if("sig_GetModulePath" not in dir(sys.modules["__main__"])):
        #   htdte_logger.error(("Missing CheefFile dictionary - \"sig_GetModulePath\" - collateral table encapsulating all RTL modules info"))

        if(re.search("/", search_module)):
            hierarchy_l = search_module.split('/')
        elif(re.search(".", search_module)):
            hierarchy_l = search_module.split('.')
        else:
            hierarchy_l = search_module

        if(hierarchy_l[0] in dict_sig_GetModulePath):
            return 1
        else:
            return 0
        # for module in hierarchy_l:
        #  if(module in dict_sig_GetModulePath.keys()):
        #    return 1
        #  else:
        #    return 0

    # ----------------------------------------
    def extract_full_signal_path(self, signal_path, lsb=-1, msb=-1, selector="."):
        # assuming we are getting a signal path separated by '/' or by '.' -
        # example sa/pcu/pcuctrls.ptpcioregs/io_global_reset_U70nH.ucreset
        if(re.search("^~", signal_path)):
            if(lsb >= 0 and msb >= 0):
                return ("%s[%d:%d]") % (signal_path, msb, lsb)
            else:
                return signal_path
        if(selector == "none" or selector == ""):
            selector = "."
        normalized_str = signal_path.replace("/", ".")
        hierarchy_l = normalized_str.split('.')
        full_path = []

        # -----------------------------
        if(len(hierarchy_l) > 1):
            if(len(hierarchy_l[0]) < 1):
                del hierarchy_l[0]
            if(not self.signal_module_exists(hierarchy_l[0])):
                htdte_logger.error(
                    ("Can't find the module-\"%s\" reference in signal path:\"%s\",Look for available modules in rtl modules collateral file or override module in \"RTL_module_mapping\" CFG key.") % (str(hierarchy_l[0]), signal_path))
            # -------------------------------
            module_pathes = dict_sig_GetModulePath[hierarchy_l[0]]
            if(len(module_pathes) > 1):
                module_pathes = [
                    x for x in module_pathes if re.search(selector, x)]
                if(len(module_pathes) == 0):
                    htdte_logger.error(("Can't match any found module (signal-%s) to selector regexp (%s): List of found modules :%s") % (
                        signal_path, selector, dict_sig_GetModulePath[hierarchy_l[0]]))
            # ---Replace all oreceeding items in path that are matching lready in module path
            normalized_str = re.sub(
                "(\.|^)" + hierarchy_l[0] + "\.", ".", normalized_str)
            for p in module_pathes:
                full_path.append(
                    (("%s.%s") % (p, normalized_str)).replace("..", "."))
        else:  # end of if(len(hierarchy_l)>1)
            # --EXTERNAL DUT signal expected
            if(CFG["HPL"]["PKG_HIER_PATH"] != ""):
                full_path.append(("%s.%s") %
                                 (CFG["HPL"]["PKG_HIER_PATH"], hierarchy_l[0]))
            else:
                full_path.append(("%s") % (hierarchy_l[0]))
        # --------------------
        if(lsb >= 0 and msb >= 0):
            for p in full_path:
                full_path[full_path.index(p)] = (("%s[%d:%d]") % (p, msb, lsb))
        # TODO: selector should filter multiple matching (core0,core1)-----------
        return full_path
    # -----------------------------------
