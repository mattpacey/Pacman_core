from htd_utilities import *
from htd_collaterals import *


class htd_cr_info(object):
    def __init__(self):
        self.rtl_path_register_indexing = {}
    # -----------------------------------

    def set_additional_register_indexing_rtl_path(self, indexing_str, crname, reg_space="NONE", regfile_filter_str=""):
        (reginfo, regfile, dict_ref) = self.get_cr_info_by_name(crname, reg_space, regfile_filter_str, 1, 1)
        if(regfile not in self.rtl_path_register_indexing):
            self.rtl_path_register_indexing[regfile] = {}
        self.rtl_path_register_indexing[regfile][crname] = indexing_str
    # -----------------------------------
    #
    # -----------------------------------
    # def verify_reg_access_integrity(self,
    # -----------------------------------
    #
    # -----------------------------------

    def get_cr_name_by_address(self, address, reg_space, regfile_filter_str="", port_id=-1, bar_id=-1, device_id=-1, function_id=-1, noerr=0):
        found_cr_regfiles = []
        found_cr_regscopes = []
        for reg_type in HTD_INFO.RegAccInfo:
            curr_dict = eval(("dict_%s") % (HTD_INFO.RegAccInfo[reg_type]["dictionary"]))
            for regfile in curr_dict:
                if(re.search(regfile_filter_str, regfile)):
                    for reg_name in curr_dict[regfile]["register"]:
                        try:
                            final_address = int(curr_dict[regfile]["register"][reg_name]["addressOffset"])
                            current_reg_bar = 0 if "bar" not in curr_dict[regfile]["register"][reg_name] else curr_dict[regfile]["register"][reg_name]["bar"]
                            current_reg_func = 0 if "function" not in curr_dict[regfile]["register"][reg_name] else curr_dict[regfile]["register"][reg_name]["function"]
                            current_reg_device = 0 if "device" not in curr_dict[regfile]["register"][reg_name] else curr_dict[regfile]["register"][reg_name]["device"]
                            current_reg_port = 0 if "portid" not in curr_dict[regfile]["register"][reg_name] else curr_dict[regfile]["register"][reg_name]["portid"]

                            port_match = (port_id < 0 or port_id == current_reg_port)
                            bar_match = (bar_id < 0 or bar_id == current_reg_bar)
                            function_match = (function_id < 0 or function_id == current_reg_func)
                            device_match = (device_id < 0 or device_id == current_reg_device)
                            address_match = (final_address == address)

                            if (address_match and port_match and bar_match and function_match and device_match):
                                htdte_logger.inform("found final_address %d - reg name %s" % (final_address, reg_name))
                                found_cr_regfiles.append(reg_name)
                                found_cr_regscopes.append(regfile)
                        except BaseException:
                            pass

        if(len(found_cr_regfiles) > 1):
            if (noerr):
                return ("", "")
            else:
                htdte_logger.error(("Multiple registers are matching to given cr address -\"0x%x\".Pls. specify \"crname_filter\" regexp or \"port_id\" to filter out on of regfiles:%s ") %
                                   (address, str(found_cr_regfiles).replace(",", "\n")))
        if(len(found_cr_regfiles) < 1):
            if(noerr):
                return ("", "")
            else:
                htdte_logger.error(("Can't find any register matching to given cr address -\"0x%x\" (filters are: regfile_filter_str=\"%s\" ,port_id=%d).Pls. specify \"cr_name\" or other address. ") %
                                   (address, regfile_filter_str, port_id))
        return (found_cr_regfiles[0], found_cr_regscopes[0])

    # ----------------------------------------
    # get matching CRs by name and scope
    # -----------------------------------------
    def get_matching_crs_by_name(self, name, reg_space, regfile_filter_str=""):
        found_cr_regfiles = []
        for reg_type in HTD_INFO.RegAccInfo:
            try:
                curr_dict = eval(("dict_%s") % (HTD_INFO.RegAccInfo[reg_type]["dictionary"]))
            except NameError:
                self.error(("Missing \"%s\" - dictionary definition in TE_cfg.xml  . ") % (HTD_INFO.RegAccInfo[reg_type]["dictionary"]), 1)
            for regfile in curr_dict:
                if (re.search(regfile_filter_str, regfile)):
                    if (name in curr_dict[regfile]["register"]):
                        found_cr_regfiles.append(regfile)
        return found_cr_regfiles

    # ----------------------------------------
    # get matching CRs by name and scope
    # -----------------------------------------
    def get_matching_crs_by_regex(self, regex, regfile_filter_str=""):
        found_cr_regs = []
        for reg_type in HTD_INFO.RegAccInfo:
            try:
                curr_dict = eval(("dict_%s") % (HTD_INFO.RegAccInfo[reg_type]["dictionary"]))
            except NameError:
                self.error(("Missing \"%s\" - dictionary definition in TE_cfg.xml  . ") % (HTD_INFO.RegAccInfo[reg_type]["dictionary"]), 1)
            for regfile in curr_dict:
                if (re.search(regfile_filter_str, regfile)):
                    for reg in curr_dict[regfile]["register"]:
                        if re.search(regex, reg):
                            found_cr_regs.append(reg)

        return found_cr_regs

    # ----------------------------------------
    # Processing all regfiles and looking for a register name ,
    # If more then one regfile matched - error asserted - user should provide
    #  filtering on regfile name
    # -----------------------------------------
    def get_cr_info_by_name(self, name, reg_space, regfile_filter_str="", get_regfile=0, get_dict=0, get_dict_name=0, noerr=0):
        found_cr_regfiles = {}
        not_matched_regfiles = []
        curr_regfile = ""
        curr_dict_name = ""
        curr_dict_ref = None
        # registerFile names can have pythons special characters '[' & ']' that
        # needs to be escaped so re.search pattern can match the registerFile from
        # the CRIF
        regfile_filter_str = re.sub(r"\[", r"\[", regfile_filter_str)
        regfile_filter_str = re.sub(r"\]", r"\]", regfile_filter_str)
        # Precompile regex used inside loop
        regfile_filter_re = re.compile(regfile_filter_str)
        for reg_type in HTD_INFO.RegAccInfo:
            try:
                curr_dict = eval(("dict_%s") % (HTD_INFO.RegAccInfo[reg_type]["dictionary"]))
            except NameError:
                self.error(("Missing \"%s\" - dictionary definition in TE_cfg.xml  . ") % (HTD_INFO.RegAccInfo[reg_type]["dictionary"]), 1)
            # ----------------
            for regfile in curr_dict:
                if(name in curr_dict[regfile]["register"]):
                    not_matched_regfiles.append(regfile)
                # Don't reorder this nested if. re search must be as late as possible, since it's expensive
                # Faster in dict check is O(1), so it should go first
                if(name in curr_dict[regfile]["register"]):

                    # Empty string check is needed since re.search will pass if it's a empty string, so short circuit the check
                    if regfile_filter_str == "" or regfile_filter_str == regfile or regfile_filter_re.search(regfile):
                        if(regfile not in found_cr_regfiles):
                            found_cr_regfiles[regfile] = {}
                        found_cr_regfiles[regfile] = curr_dict[regfile]["register"][name]
                        curr_regfile = regfile
                        curr_dict_ref = curr_dict
                        curr_dict_name = HTD_INFO.RegAccInfo[reg_type]["dictionary"]
        if(len(found_cr_regfiles) > 1):
            if (not noerr):
                htdte_logger.error(("Multiple registers are matching to given cr name -\"%s\".Pls. specify \"scope\" regexp to filter out on regfiles:%s or use \"broadcast\" switch") %
                                   (name, str(list(found_cr_regfiles.keys())).replace(",", "\n")))
        if(len(found_cr_regfiles) < 1):
            if(noerr):
                return (None, None, None)
            else:
                htdte_logger.error(("No register matching to given cr name -\"%s\".Pls. review given cr name or  \"scope\"-\"%s\" regexp to filter out on regfiles:%s .%s") %
                                   (name, regfile_filter_str, regfile_filter_str, ("The register found in regfiles: %s") % (str(not_matched_regfiles))))
        # if(len( found_cr_regfiles[found_cr_regfiles.keys()[0]])>1):
        #       htdte_logger.error(("Multiple registers are matching to given cr name -\"%s\" in same scope:%s ")%(name,regfile_filter_str))
        # XREG BACKDOOR OVERWRITE
        if("XREG_BACKDOOR" in CFG):
            if(name in CFG["XREG_BACKDOOR"]):
                htdte_logger.inform("Found a overwrite for this creg on TE_CFG %s" % (name))
                for field2mod in CFG["XREG_BACKDOOR"][name]:
                    if(field2mod in found_cr_regfiles[list(found_cr_regfiles.keys())[0]]):
                        htdte_logger.inform("Changing field %s for creg %s from %s to %s" % (
                            field2mod, name, found_cr_regfiles[list(found_cr_regfiles.keys())[0]][field2mod], CFG["XREG_BACKDOOR"][name][field2mod]))
                        found_cr_regfiles[list(found_cr_regfiles.keys())[0]][field2mod] = CFG["XREG_BACKDOOR"][name][field2mod]

        if(get_dict_name):
            return (found_cr_regfiles[list(found_cr_regfiles.keys())[0]], curr_regfile, curr_dict_ref, curr_dict_name)
        if(get_dict):
            return (found_cr_regfiles[list(found_cr_regfiles.keys())[0]], curr_regfile, curr_dict_ref)
        if(get_regfile == 1):
            return (found_cr_regfiles[list(found_cr_regfiles.keys())[0]], curr_regfile)
        if(get_regfile == 2):
            return list(found_cr_regfiles.keys())
        return found_cr_regfiles[list(found_cr_regfiles.keys())[0]]
    # -----------------------------------------------
    #
    # -----------------------------------------------

    def get_cr_regfile(self, name, reg_space, regfile_filter_str=""):
        (reginfo, regfile) = self.get_cr_info_by_name(name, regfile_filter_str, 1)
        return regfile

    def get_cr_info_and_regfile_name(self, name, reg_space, regfile_filter_str=""):
        (reginfo, regfile, dict_ref, dict_name) = self.get_cr_info_by_name(name, reg_space, regfile_filter_str, 1, 1, 1)
        return (dict_name, regfile)
    # ------------------------------------------------
    # Matching the cr info struct and return an adress
    # ------------------------------------------------

    def get_cr_address_by_name(self, name, reg_space, regfile_filter_str="", noerr=0):
        (reginfo, regfile, dict_ref) = self.get_cr_info_by_name(name, reg_space, regfile_filter_str, 1, 1, 0, noerr)
        # ---Noerror enforcment
        if(noerr and reginfo is None):
            return -1
        # ----------------
        if("addressBase" not in dict_ref[regfile]):
            dict_ref[regfile]["addressBase"] = 0
            #htdte_logger.error(("CR dictionary integrity error - missing \"addressBase\" property for regfile -\"%s\".Pls. review definition of dictionary  ")%(regfile))
        if("addressOffset" not in reginfo):
            htdte_logger.error(
                ("CR dictionary integrity error - missing \"addressOffset\" property for cr name -\"%s\".Pls. review definition of dictionary  ") % (name))
        if(type(reginfo["addressOffset"]) in [str, str] and re.match("[0xba-f0-9]", reginfo["addressOffset"]) is None):
            htdte_logger.error(
                ("CR dictionary integrity error - illegal \"addressOffset\" property (%s) for cr name -\"%s\".Pls. review definition of dictionary  ") % (reginfo["addressOffset"], name))
        if (type(reginfo["addressOffset"]) in [str, str]):
            num_type = (re.match(r"\d+'(b|h)[a-f0-9]+", reginfo["addressOffset"]) or re.match("^[a-f0-9]+$", reginfo["addressOffset"]))
            if (num_type):
                if(not num_type.groups()):
                    return int(reginfo["addressOffset"], 16) + int(dict_ref[regfile]["addressBase"])
                if (num_type.groups()[0] == 'b'):
                    reginfo["addressOffset"] = re.sub(r"\d+'(?:b|h)", "", reginfo["addressOffset"])
                    return int(reginfo["addressOffset"], 2) + int(dict_ref[regfile]["addressBase"])
                elif (num_type.groups()[0] == 'h'):
                    reginfo["addressOffset"] = re.sub(r"\d+'(?:b|h)", "", reginfo["addressOffset"])
                    return int(reginfo["addressOffset"], 16) + int(dict_ref[regfile]["addressBase"])
                else:
                    htdte_logger.error(
                        ("CR dictionary integrity error - illegal \"addressOffset\" property (%s) for cr name -\"%s\".Pls. review definition of dictionary  ") % (reginfo["addressOffset"], name))
        else:
            return int(reginfo["addressOffset"]) + int(dict_ref[regfile]["addressBase"])
    # ------------------------------------------------
    # Return Cr property
    # ------------------------------------------------

    def get_cr_property_by_name(self, name, property_str, reg_space, regfile_filter_str=""):
        (reginfo, regfile, dict_ref) = self.get_cr_info_by_name(name, reg_space, regfile_filter_str, 1, 1, 0)
        if(property_str not in reginfo):
            if(property_str not in dict_ref[regfile]):
                htdte_logger.error(
                    ("Attempting to extract missing cr info property - \"%s\" property for cr name -\"%s\".Pls. review definition of dictionary  ") % (property_str, name))
            else:
                return dict_ref[regfile][property_str]
        return reginfo[property_str]

    def has_cr_property_by_name(self, name, property_str, reg_space, regfile_filter_str=""):
        (reginfo, regfile, dict_ref) = self.get_cr_info_by_name(name, reg_space, regfile_filter_str, 1, 1, 0)
        if(property_str not in reginfo):
            if(property_str not in dict_ref[regfile]):
                return 0
            else:
                return 1
        return 1

    def get_cr_regfile_property_by_name(self, name, property_str, reg_space, regfile_filter_str=""):
        res_Str = self.get_cr_property_by_name(name, property_str, reg_space, regfile_filter_str)
        return res_Str

    def has_cr_regfile_property_by_name(self, name, property_str, reg_space, regfile_filter_str=""):
        res_Str = self.has_cr_property_by_name(name, property_str, reg_space, regfile_filter_str)
        return res_Str
    # ------------------------------------------

    def get_crfield_property_by_name(self, name, fieldname, property_str, reg_space, regfile_filter_str=""):
        (reginfo, regfile, dict_ref) = self.get_cr_info_by_name(name, reg_space, regfile_filter_str, 1, 1, 0)
        if(fieldname not in reginfo["field"]):
            htdte_logger.error(
                ("Attempting to extract  cr field  property - \"%s\"  by illegal field name - \"%s\" for cr name -\"%s\".Pls. review definition of dictionary  ") % (property_str, fieldname, name))
        if(property_str not in reginfo["field"][fieldname]):
            htdte_logger.error(("Attempting to extract missing cr field info property - \"%s->%s\" .Pls. review definition of dictionary  ") %
                               (property_str, name, fieldname))
        return reginfo["field"][fieldname][property_str]

    def has_crfield_property_by_name(self, name, fieldname, property_str, reg_space, regfile_filter_str=""):
        (reginfo, regfile, dict_ref) = self.get_cr_info_by_name(name, reg_space, regfile_filter_str, 1, 1, 0)
        if(fieldname not in reginfo["field"] or property_str not in reginfo["field"][fieldname]):
            return 0
        return 1

    # ------------------------------------------
    #
    # ------------------------------------------
    def get_cr_fields(self, name, reg_space, regfile_filter_str=""):
        reginfo = self.get_cr_info_by_name(name, reg_space, regfile_filter_str)
        return list(reginfo["field"].keys())

    def has_rtl_node_backdoor_override(self, regfield, regname, regfile):
        if("XREG_RTL_NODES_BACKDOOR" not in CFG or len(list(CFG["XREG_RTL_NODES_BACKDOOR"].keys())) == 0):
            return False
        if("regfile" not in CFG["XREG_RTL_NODES_BACKDOOR"]):
            htdte_logger.error(
                "Improper CFG[XREG_RTL_NODES_BACKDOOR] table found in TE_cfg.xml - missing \"regfile\" entry. Expected structure: <CFG category=\"XREG_RTL_NODES_BACKDOOR\">\n <regfile name=\"<regfile_name>\" ...   ")
        if(regfile not in CFG["XREG_RTL_NODES_BACKDOOR"]["regfile"]):
            return False
        if("register" not in CFG["XREG_RTL_NODES_BACKDOOR"]["regfile"][regfile]):
            htdte_logger.error(("Improper CFG[XREG_RTL_NODES_BACKDOOR] table found in TE_cfg.xml - missing \"register\" entry. Expected structure: <CFG category=\"XREG_RTL_NODES_BACKDOOR\">\n <regfile name=\"%s\">\n   <register name=\"<regname>\" <field_name1>=\"<field_rtl_path>\" <field_name2>=\"<field_rtl_path>\" ") % (regfile))
        if(regname not in CFG["XREG_RTL_NODES_BACKDOOR"]["regfile"][regfile]["register"]):
            return False
        if(regfield not in CFG["XREG_RTL_NODES_BACKDOOR"]["regfile"][regfile]["register"][regname]):
            return False
        return True

    def get_rtl_node_backdoor_override(self, regfield, regname, regfile):
        if(not self.has_rtl_node_backdoor_override(regfield, regname, regfile)):
            htdte_logger.error(("Trying to retrieve not existent XREG RTL node backdoor override (%s:%s:%s)...   ") % (regfile, regname, regfield))
        return CFG["XREG_RTL_NODES_BACKDOOR"]["regfile"][regfile]["register"][regname][regfield]
    # ------------------------------------------
    #
    # ------------------------------------------

    def has_rtl_node_backdoor_override(self, regfield, regname, regfile):
        if("XREG_RTL_NODES_BACKDOOR" not in CFG or len(list(CFG["XREG_RTL_NODES_BACKDOOR"].keys())) == 0):
            return False
        if("regfile" not in CFG["XREG_RTL_NODES_BACKDOOR"]):
            htdte_logger.error(
                "Improper CFG[XREG_RTL_NODES_BACKDOOR] table found in TE_cfg.xml - missing \"regfile\" entry. Expected structure: <CFG category=\"XREG_RTL_NODES_BACKDOOR\">\n <regfile name=\"<regfile_name>\" ...   ")
        if(regfile not in CFG["XREG_RTL_NODES_BACKDOOR"]["regfile"]):
            return False
        if("register" not in CFG["XREG_RTL_NODES_BACKDOOR"]["regfile"][regfile]):
            htdte_logger.error(("Improper CFG[XREG_RTL_NODES_BACKDOOR] table found in TE_cfg.xml - missing \"register\" entry. Expected structure: <CFG category=\"XREG_RTL_NODES_BACKDOOR\">\n <regfile name=\"%s\">\n   <register name=\"<regname>\" <field_name1>=\"<field_rtl_path>\" <field_name2>=\"<field_rtl_path>\" ") % (regfile))
        if(regname not in CFG["XREG_RTL_NODES_BACKDOOR"]["regfile"][regfile]["register"]):
            return False
        if(regfield not in CFG["XREG_RTL_NODES_BACKDOOR"]["regfile"][regfile]["register"][regname]):
            return False
        return True

    def get_rtl_node_backdoor_override(self, regfield, regname, regfile):
        if(not self.has_rtl_node_backdoor_override(regfield, regname, regfile)):
            htdte_logger.error(("Trying to retrieve not existent XREG RTL node backdoor override (%s:%s:%s)...   ") % (regfile, regname, regfield))
        return CFG["XREG_RTL_NODES_BACKDOOR"]["regfile"][regfile]["register"][regname][regfield]
    # ------------------------------------------
    #
    # ------------------------------------------

    def get_missing_cr_fields_rtlnodes(self, name, reg_space, regfile_filter_str=""):
        missing_field_rtl = []
        (reginfo, regfile, dict_ref) = self.get_cr_info_by_name(name, reg_space, regfile_filter_str, 1, 1)
        if("rtlPath" in dict_ref[regfile]):
            return []  # there is a global struct over all registerFile
        if("rtlPath" in reginfo):
            return []  # there is a global struct over all register
        for field in self.get_cr_fields(name, reg_space, regfile_filter_str):
            field_info = reginfo["field"][field]
            if((("rtlPath" not in field_info) or field_info["rtlPath"] is None or (len(field_info["rtlPath"]) < 2)) and not self.has_rtl_node_backdoor_override(field, name, regfile)):
                missing_field_rtl.append(field)
        return missing_field_rtl
    # --------------------------------------------------------
    #
    # -------------------------------------------------------

    def get_cr_field_boundaries(self, field, crname, reg_space, regfile_filter_str=""):
        reginfo = self.get_cr_info_by_name(crname, reg_space, regfile_filter_str)
        if("bitOffset" in reginfo["field"][field]):
            lsb = int(reginfo["field"][field]["bitOffset"])
            msb = lsb + int(reginfo["field"][field]["bitWidth"]) - 1
        else:
            (lsb_str, msb_str) = reginfo["field"][field]["range"].split(":")
            lsb = int(lsb_str)
            msb = int(msb_str)
            if(msb < lsb):
                tmp = msb
                msb = lsb
                lsb = tmp
        return (lsb, msb)
    # --------------------------------------------------------
    #
    # -------------------------------------------------------

    def get_cr_field_reset_val(self, field, crname, reg_space, regfile_filter_str="", reset_type=""):
        reginfo = self.get_cr_info_by_name(crname, reg_space, regfile_filter_str)
        if("reset" in reginfo["field"][field]):
            if(isinstance(reginfo["field"][field]["reset"], dict)):
                for rtype in reginfo["field"][field]["reset"]:
                    if(re.search(reset_type, rtype)):
                        return util_get_int_value(reginfo["field"][field]["reset"][rtype]["value"])[1]
            else:
                return util_get_int_value(reginfo["field"][field]["reset"])[1]
        return 0
     # ----------------------------------------
     #
     # ----------------------------------------

    def resolve_rtl_node(self, field, crname, reg_space, regfile_filter_str="", instance_num=0, selector=""):
        (reginfo, regfile, dict_ref) = self.get_cr_info_by_name(crname, reg_space, regfile_filter_str, 1, 1)
        node_rtl = ""
        rtl_path_additional_reg_indexing = ""
        if(regfile in self.rtl_path_register_indexing and crname in self.rtl_path_register_indexing[regfile]):
            rtl_path_additional_reg_indexing = self.rtl_path_register_indexing[regfile][crname]
        # ---------------------
        if(not self.has_rtl_node_backdoor_override(field, crname, regfile)):
            if("rtlPath" in dict_ref[regfile]['register'][crname]["field"][field]):
                node_rtl = dict_ref[regfile]['register'][crname]["field"][field]["rtlPath"]
            elif("rtlPath" in dict_ref[regfile]['register'][crname]):
                node_rtl = ("%s%s.%s") % (dict_ref[regfile]['register'][crname]["rtlPath"], rtl_path_additional_reg_indexing, field.lower())
            elif("rtlPath" in dict_ref[regfile]):
                node_rtl = ("%s.%s%s.%s") % (dict_ref[regfile]["rtlPath"], crname.lower(), rtl_path_additional_reg_indexing, field.lower())
            else:
                htdte_logger.error(("Trying to resolve not existent RTSignal value :CR:%s RegisterFile:%s field:%s  ") % (crname, regfile, field))

        # ----------
            if("rtlFub" in dict_ref[regfile]):
                node_rtl = ("%s.%s") % (dict_ref[regfile]["rtlFub"], node_rtl)
            elif("rtlFub" in dict_ref[regfile]['register'][crname]):
                node_rtl = ("%s.%s") % (dict_ref[regfile]['register'][crname]["rtlFub"], node_rtl)
            elif("rtlFub" in dict_ref[regfile]['register'][crname]["field"][field]):
                node_rtl = ("%s.%s") % (dict_ref[regfile]['register'][crname]["field"][field]["rtlFub"], node_rtl)
        # ---------------------------
            node_rtl = node_rtl.replace("`", "").replace("\"", "")
            if("RTL_module_mapping" in CFG):
                for rtl_module in CFG["RTL_module_mapping"]:
                    if(re.search((r"%s\.") % rtl_module, node_rtl)):
                        node_rtl = node_rtl.replace(("%s.") % rtl_module, ("%s.") % CFG["RTL_module_mapping"][rtl_module])
            node_rtl = node_rtl.replace("%INST_NUM%", str(instance_num))
        else:  # else if(not self.has_rtl_node_backdoor_override)
            node_rtl = self.get_rtl_node_backdoor_override(field, crname, regfile)
        return HTD_INFO.signal_info.extract_full_signal_path(node_rtl, -1, -1, selector)
    # ----------------------------------------
    #
    # ----------------------------------------

    def has_rtl_node(self, field, crname, reg_space, regfile_filter_str=""):
        (reginfo, regfile, dict_ref) = self.get_cr_info_by_name(crname, reg_space, regfile_filter_str, 1, 1)
        if(self.has_rtl_node_backdoor_override(field, crname, regfile)):
            return True
        if("rtlPath" in dict_ref[regfile]):
            return True  # there is a global struct over all registerFile
        if("rtlPath" in reginfo):
            return True  # there is a global struct over all register
        field_info = reginfo["field"][field]
        if("rtlPath" in field_info and field_info["rtlPath"] is not None):
            return True
        else:
            return False
   # ----------------------------------------
   # Check if any RTL node assigned for this register
   # ----------------------------------------

    def has_no_rtl_nodes(self, crname, reg_space, regfile_filter_str=""):
        reginfo = self.get_cr_info_by_name(crname, reg_space, regfile_filter_str, 0, 0, 0, 1)
        if(reginfo is not None):
            for f in reginfo["field"]:
                if("rtlPath" in reginfo["field"][f]):
                    return True
            return False
        else:
            return True

    def verify_reg_access_integrity(self, reg_access, dictionary_name, reg_file):
        for reg_type in reg_access:
            if ('dictionary' not in reg_access[reg_type]):
                dictionary_found_in_regAccInfo = True
                for regf in reg_access[reg_type]["RegisterFile"]:
                    if (re.search(regf, reg_file)):
                        return "True", reg_type
            else:
                if (reg_access[reg_type]['dictionary'] == dictionary_name):
                    dictionary_found_in_regAccInfo = True
                    for regf in reg_access[reg_type]["RegisterFile"]:
                        if (re.search(regf, reg_file)):
                            return "True", reg_type
