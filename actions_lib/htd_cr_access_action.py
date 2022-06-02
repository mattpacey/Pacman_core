from htd_basic_action import *
from htd_utilities import *
from htd_collaterals import *
from htd_player_top import *
XREG_ReadOnlyRegisterAccessEncoding = ["RO", "ro", "RO/V", "RO/P"]
# ---------------------------------------
#
# ---------------------------------------


class hpl_reg_history(object):
    def __init__(self):
        self.queue = {}

    def has(self, crname, regfile):
        return ((crname in list(self.queue.keys())) and (regfile in list(self.queue[crname].keys())))

    def add(self, crname, regfile, field, val):
        if (crname not in list(self.queue.keys())):
            self.queue[crname] = {}
        if (regfile not in list(self.queue[crname].keys())):
            self.queue[crname][regfile] = {}
        self.queue[crname][regfile][field] = val

    def has_field(self, crname, regfile, field):
        return ((crname in list(self.queue.keys())) and (regfile in list(self.queue[crname].keys())) and (
            field in list(self.queue[crname][regfile].keys())))

    def get(self, crname, regfile, field):
        return self.queue[crname][regfile][field]


Reg_history = hpl_reg_history()
# ---------------------------------------------


class XREG(htd_base_action):
    def __init__(self, action_name, source_file, source_lineno, currentFlow, is_internal):
        self.cr_address = -1
        self.cr_name = ""
        self.cr_name_filter = ""
        self.constrain_scope = ""
        self.registerfile = ""
        self.registerfileRegExp = ""
        self.register_access_name = ""
        self.express_mode = 0
        self.bfm_mode = "tap"
        self.missing_all_rtl_nodes = False
        self.instance_num = -1
        self.dictionary_name = ""
        self.regaccess_obj_handler = None
        self.regaccess_handler = None
        self.postfocus_delay = 0
        self.pscand_en = -1
        self.pscand_group_override = ""
        self.cfg_list_override = ""
        self.pscand_delay = 0 if ("pscand_delay" not in list(CFG["HPL"].keys())) else CFG["HPL"]["pscand_delay"]
        self.pscand_pins = "" if ("pscand_pins" not in list(CFG["HPL"].keys())) else CFG["HPL"]["pscand_pins"]
        self.port_id = -1
        self.regSpace = "NONE"
        # ----------------
        self.tap_param_container = htd_tap_params()
        self.register_def = {}
        htd_base_action.__init__(self, self.__class__.__name__, action_name, source_file, source_lineno, currentFlow,
                                 is_internal)
        self.arguments.set_argument("source", 1, "Specify which source for this action")
        self.arguments.declare_arg("reg", "The Control Register  name or adress                       ",
                                   "string_or_int", "", 1)
        self.arguments.declare_arg("scope",
                                   "In case of multiple cr register are matching to user given cr name, the filter used to select one of them ",
                                   "string_or_list", "", 0)
        self.arguments.declare_arg("portid", "The Control Register  portid                               ", "int", 0, 0)
        self.arguments.declare_arg("index", "Adress space index used to access a sequential registers.", "int", 0, 0)
        self.arguments.declare_arg("dro", "The expected PCU IO  DATA register shiftout (aligned to register length)",
                                   "int", -1, 0)
        self.arguments.declare_arg("dri", "The entire of PCU IO DATA register shiftout (aligned to register length)",
                                   "int", -1, 0)
        self.arguments.declare_arg("bfm_mode", "The bfm mode: express|injection|normal ",
                                   "string", "tap", 0)

        self.arguments.declare_arg("read_modify_write", "Read rtl and override user assignment ena/dis ", "bool", 1, 0)
        self.arguments.declare_arg("incremental_mode", "History incremental register initilization ena/dis ", "bool", 1,
                                   0)
        self.arguments.declare_arg("instance_num", "Control register instance number specification  ", "int", -1, 0)
        self.arguments.declare_arg("pscand_en", "Enable pscand on compare", "bool", 0, 0)
        self.arguments.declare_arg("pscand_group_override", "Override the automatic pscand group name", "string", "", 0)
        self.arguments.declare_arg("cfg_list_override", "Override the automatic cfg list name", "string", "", 0)
        self.arguments.declare_arg("compression", "Compression On/Off ", "bool",
                                   0 if("compression" not in list(CFG["HPL"].keys())) else int(CFG["HPL"]["compression"]), 0)
        self.arguments.declare_arg("broadcast", "broadcast the control regiser commands to multiple slices", "string", "", 0)
        self.arguments.declare_arg("explicit_scope", "take the scopes as they are, without trying to find if those are valid", "bool", 1, 0)
        self.arguments.declare_arg("compression", "Compression On/Off ", "bool",
                                   0 if("compression" not in list(CFG["HPL"].keys())) else int(CFG["HPL"]["compression"]), 0)
        self.arguments.declare_arg("specific_core", "Specific core to work on", "int", -1, 0)
        self.arguments.declare_arg(
            "postfocus_delay", "Adding delay of TCK cycles after focusing to target agent on TAP Network protocole", "int", 0, 0)
        self.arguments.declare_arg("regSpace", "Register Space for the current CSR ", "string_or_list", "NONE", 0)
        self.arguments.declare_arg("field_labels", "ena/dis instrumental per field label assignment ", "bool", 0, 0)
        if CFG["HPL"].get("NEW_LABEL_SPEC"):
            default_prefix = "ph%s__%s_" % (self.get_curr_flow().phase_name, action_name)
        else:
            default_prefix = ""
        self.arguments.declare_arg("label_prefix", "Label prefix to be added automatically to all generated labels ", "string", default_prefix, 0)
        self.arguments.declare_arg("label_reglen_offset_format", "Create labels for strobbing in format <label>_<chainlen>_<offset> ", "bool", 0, 0)
        self.arguments.declare_arg("GID", "Only used by stf2mci", "int", 0, 0)
        self.arguments.declare_arg("read_np_val", "non-posted read access", "int", -1, 0)
        self.arguments.declare_arg("capture", "insert CTV to capture the register readout directly", "bool", 0, 0)
        #self.arguments.declare_arg("CTL", "Define the controller to be used after an stf2mci conversion", ["dat","scan","sbft","tap"], "dat",0)

    def get_specific_html_help(self):
        html_string = "<p><h2>register specific parameters (can be overriden by action parameters)</h2></p>\n"
        registers_list = list(HTD_INFO.RegAccInfo.keys())
        for register in registers_list:
            for mode in list(HTD_INFO.RegAccInfo[register].keys()):
                if (isinstance(HTD_INFO.RegAccInfo[register][mode], dict) and "paramValues" in
                        list(HTD_INFO.RegAccInfo[register][mode].keys())):
                    all_regacc_params = HTD_INFO.RegAccInfo[register][mode]["paramValues"]
                    html_string += "<p><h3>register: %s</h3></p>\n" % (register)
                    html_string += '<table border="1">\n'
                    html_string += '<tr bgcolor="blue"><th><font color="white">Parameter</font></th><th><font color="white">Value</font></th></tr>\n'
                    for k, v in sorted(all_regacc_params.items()):
                        html_string += ('<tr bgcolor="00FC00" align="left"><th>%s</a></th><th>%s</th></tr>\n') % (k, v)
                    html_string += "</table>\n"

        return html_string

    # ----------------------------------
    def debug_readback(self):
        pass

    # ------------------------
    def get_action_not_declared_argument_names(self):
        return self.get_field_assignment_list()

    # ------------------------
    def get_field_assignment_list(self, allow_injection=False):
        all_regacc_params = []

        if (self.arguments.get_argument("bfm_mode") != "injection" or allow_injection):
            for mode in list(HTD_INFO.RegAccInfo[self.register_access_name].keys()):
                if (isinstance(HTD_INFO.RegAccInfo[self.register_access_name][mode], dict) and "params" in
                        list(HTD_INFO.RegAccInfo[self.register_access_name][mode].keys())):
                    all_regacc_params.extend(HTD_INFO.RegAccInfo[self.register_access_name][mode]["params"])
        return [x for x in self.arguments.get_not_declared_arguments() if (x not in all_regacc_params)]

    def get_ui_assignment_list(self):
        if (self.arguments.get_argument("bfm_mode") == "injection"):
            return self.arguments.get_not_declared_arguments()
        else:
            return [x for x in self.arguments.get_not_declared_arguments() if (x in HTD_INFO.RegAccInfo[self.register_access_name][self.arguments.get_argument("bfm_mode")]["params"])]

    # ------------------------
    def get_list_of_scopes_from_broadcast(self):
        final_scope_list = []
        broadcast_data = self.arguments.get_argument("broadcast")

        if ("RegisterBroadcast" in list(CFG.keys())):
            current_scope = self.arguments.get_argument("scope")
            indices_list = broadcast_data.split(',')

            # get the first key to find if scope is defined
            if (indices_list[0] in list(CFG["RegisterBroadcast"].keys())):
                broadcast_values = CFG["RegisterBroadcast"][str(indices_list[0])]
                broadcast_values_list = broadcast_values.split(',')

                broadcast_index = -1
                for index, broadcast_value in enumerate(broadcast_values_list):
                    if (broadcast_value in current_scope):
                        broadcast_index = index
                        break

                # generate the list of scopes
                if (broadcast_index >= 0):
                    for index_val in indices_list:
                        reg_values = CFG["RegisterBroadcast"][str(index_val)]
                        reg_values_l = reg_values.split(',')
                        new_scope = current_scope.replace(broadcast_values_list[broadcast_index], reg_values_l[broadcast_index], 1)
                        htdte_logger.inform("Adding new scope %s to list of broadcasts" % (new_scope))
                        final_scope_list.append(new_scope)
                else:
                    htdte_logger.error("Could not find matching index for requested scope '%s'" % (current_scope))
        return final_scope_list

    def get_final_list_of_scopes(self):
        final_scope_list = []
        broadcast_value = self.arguments.get_argument("broadcast")

        if (self.arguments.get_argument("scope") and broadcast_value != ""):
            return self.get_list_of_scopes_from_broadcast()

        if (self.arguments.get_argument("scope")):
            if (isinstance(self.arguments.get_argument("scope"), list)):
                scope_list = self.arguments.get_argument("scope")
                for scope in scope_list:
                    if (self.cr_name != "" and self.arguments.get_argument("explicit_scope") != 1):
                        internal_scope_l = HTD_INFO.cr_info.get_matching_crs_by_name(self.cr_name, self.reg_space, scope)
                        for internal_scope in internal_scope_l:
                            final_scope_list.append(internal_scope)
                    else:
                        final_scope_list.append(scope)
            else:  # string
                if (self.cr_name != "" and self.arguments.get_argument("explicit_scope") != 1):
                    scope_list = HTD_INFO.cr_info.get_matching_crs_by_name(self.cr_name, self.reg_space, self.arguments.get_argument("scope"))
                    for scope in scope_list:
                        final_scope_list.append(scope)
                else:
                    final_scope_list.append(self.arguments.get_argument("scope"))
        return final_scope_list
    # -----------------------------------
    #
    # -----------------------------------

    def verify_arguments(self):
        self.inform(("       Verifying %s::%s:%s:%d ....") % (htd_base_action.get_action_type(self),
                                                              htd_base_action.get_action_name(self),
                                                              htd_base_action.get_action_call_file(self),
                                                              htd_base_action.get_action_call_lineno(self)))

        HTD_INFO.verify_info_ui_existence(["signal_info", "cr_info"])
        self.postfocus_delay = self.arguments.get_argument("postfocus_delay")
        # ---------------------------------------------------------
        if (isinstance(self.arguments.get_argument("reg"), int)):
            self.cr_address = self.arguments.get_argument("reg")
        elif (type(self.arguments.get_argument("reg")) in [str, str]):
            if (isinstance(self.arguments.get_argument("reg"), int)):
                self.cr_address = int(self.arguments.get_argument("reg"), 2)
            else:
                self.cr_name = self.arguments.get_argument("reg")
        else:
            self.error(("Action's (%s) illegal argument -\"reg\" type - \"%s\".Expected int or str. ") % (
                self.__action_name__, type(self.arguments.get_argument("reg"))), 1)
            # --------------Check needed obligatory dictionaries-------------------------------------------
        if (self.arguments.get_argument("instance_num") > 0):
            self.instance_num = self.arguments.get_argument("instance_num")

        # get the list of scopes to work on
        scope_list = self.get_final_list_of_scopes()
        if (self.arguments.get_argument("broadcast") == "" and len(scope_list) > 1):
            self.error("Multiple scopes defined in XREG: %s, this is allowed only on broadcast mode" % (str(scope_list)), 1)
        if (len(scope_list) > 0):
            for scope in scope_list:
                self.verify_single_scope(scope)
        else:
            self.verify_single_scope("")

    def verify_single_scope(self, scope):
        if (self.cr_name == "" and self.cr_address < 0):
            self.error(("Missing one of obligatory CR  indentifiers - reg address or reg name . ") % (self.io_address),
                       self.dummy_mode)
        for reg_type in list(HTD_INFO.RegAccInfo.keys()):
            if("regSpace" in list(HTD_INFO.RegAccInfo[reg_type]["RegAccInfoProperties"].keys())):
                self.regSpace = HTD_INFO.RegAccInfo[reg_type]["RegAccInfoProperties"]["regSpace"]

        if (self.cr_name == ""):
            # ---Try out to open dummy status for statistics
            self.port_id = self.arguments.get_argument("portid")
            (self.cr_name, scope) = HTD_INFO.cr_info.get_cr_name_by_address(self.cr_address, self.regSpace,
                                                                            scope,
                                                                            self.port_id,
                                                                            -1, -1, -1,
                                                                            self.dummy_mode)
            if (self.cr_name < 0 and self.dummy_mode):
                self.documented = 0
                self.documented_details = "Missing CR name by addr"
                return
                # ---Find cr adress by CR name
        if (self.cr_address < 0 and self.dummy_mode):
            self.cr_address = HTD_INFO.cr_info.get_cr_address_by_name(self.cr_name, self.regSpace,
                                                                      scope,
                                                                      self.dummy_mode)
            if (self.cr_address < 0 and self.dummy_mode):
                self.documented = 0
                self.documented_details = "Missing CR address by name"
                return
                # ----------------

        (self.dictionary_name, self.registerfile) = HTD_INFO.cr_info.get_cr_info_and_regfile_name(self.cr_name, self.regSpace, scope)
        self.registerfileRegExp = ("^%s$") % self.registerfile
        # -----------------------
        # --Verify register file match in reg access--
        dictionary_found_in_regAccInfo = False

        (dictionary_found_in_regAccInfo, self.register_access_name) = HTD_INFO.cr_info.verify_reg_access_integrity(
            HTD_INFO.RegAccInfo, self.dictionary_name, self.registerfile)
        # ----------------------------
        # ---------------------Verify direct access fields----------------------------------------------------------------------
        if (self.arguments.get_argument("dri") >= 0 and len(self.get_field_assignment_list())):
            self.error((
                       "Action's (%s) illegal arguments combination: \"dri\"=%s argument could not be used with per field assignment: %s. ") % (
                       self.__action_name__, self.arguments.get_argument("dri"), self.get_field_assignment_list()), 1)
        if (self.arguments.get_argument("dro") >= 0 and len(self.get_field_assignment_list())):
            self.error((
                       "Action's (%s) illegal arguments combination: \"dro\"=%s argument could not be used with per field assignment: %s. ") % (
                       self.__action_name__, self.arguments.get_argument("dro"), self.get_field_assignment_list()), 1)
        if (self.arguments.get_argument("dro") >= 0 and (not self.arguments.get_argument("read_type"))):
            self.error((
                       "Action's (%s) illegal arguments combination: \"dro\"=%s argument should be used in couple with \"read_type\"=1 only. ") % (
                       self.__action_name__, self.arguments.get_argument("dro")), 1)
        if (self.arguments.get_argument("dro") >= 0):
            (dro_lsb, dro_msb) = self.arguments.get_argument_lsb_msb("dro", 0)
            if (dro_msb < 0 and dro_msb < 0):
                self.error((
                           "Action's (%s) illegal arguments combination: the indexation range should be applied on \"dro[msb:lsb]\" arguments in order to calculate shifted in sequence length. ") % (
                           self.__action_name__), 1)
        if (self.arguments.get_argument("dri") >= 0):
            (dri_lsb, dri_msb) = self.arguments.get_argument_lsb_msb("dri", 0)
            if (dri_msb < 0 and dri_msb < 0):
                self.error((
                           "Action's (%s) illegal arguments combination: the indexation range should be applied on \"dri[msb:lsb]\" arguments in order to calculate shifted in sequence length. ") % (
                           self.__action_name__), 1)
                # ----Provide all not declares - i.e dr fields parameters --------------------
        documented_size = HTD_INFO.cr_info.get_cr_property_by_name(self.cr_name, 'size', self.regSpace,
                                                                   self.arguments.get_argument("scope"))
        if (self.arguments.get_argument("dro") >= 0 and (
                int(self.arguments.get_argument("dro")) >= pow(2, documented_size))):
            self.error(
                ("The entire of register (\"%s\") read sequence (\dro\"=0x%x) exceed register size - %d bit  . ") % (
                    self.cr_name, int(self.arguments.get_argument("dro")), documented_size), 1)
        if (self.arguments.get_argument("dri") >= 0 and (
                int(self.arguments.get_argument("dri")) >= pow(2, documented_size))):
            self.error(
                ("The entire of register (\"%s\") read sequence (\dri\"=0x%x) exceed register size - %d bit  . ") % (
                    self.cr_name, int(self.arguments.get_argument("dri")), documented_size), 1)
            # --Verify dictionary found
        if (not dictionary_found_in_regAccInfo):
            self.error((
                       "Can't match the register dictionary - %s in any define registerAccess entries  .Pls. verify <RegAccess->dictionary> definition correctness.") % (
                       self.dictionary_name), self.dummy_mode)
        if (self.register_access_name == ""):
            if (self.dummy_mode):
                self.documented = 0
                self.documented_details = "Missing CR name by addr"
            self.error((
                       "Can't match the register - %s type access definition by register file - \"%s\".Pls. verify <RegAccess> definition corectness.") % (
                       self.cr_name, self.registerfile), self.dummy_mode)
        # Check if HPL[xreg_bfm_mode] is set
        if "xreg_bfm_mode" in CFG["HPL"] and not self.arguments.is_argument_assigned("bfm_mode"):
            self.arguments.set_argument("bfm_mode", CFG["HPL"]["xreg_bfm_mode"])
        if (not self.arguments.get_argument("bfm_mode") == "injection"):
            if (self.arguments.get_argument("bfm_mode") == "express"):
                self.express_mode = 1
            if (self.arguments.get_argument("bfm_mode") not in list(HTD_INFO.RegAccInfo[self.register_access_name].keys())):
                htdte_logger.error((
                                   "Missing bfm_mode - \"%s\" entry in RegAccInfo, for register type - %s. Pls review an TE_cfg.xml ") % (
                                   self.arguments.get_argument("bfm_mode"), self.register_access_name))
        # -------------------------------------
        fields_l = HTD_INFO.cr_info.get_cr_fields(self.cr_name, self.regSpace, scope)
        if (self.arguments.get_argument("read_type")):
            if(len(self.get_field_assignment_list()) == 0):
                for f in fields_l:
                    labels_str = ("%s_%s") % (self.arguments.get_argument("label_prefix"), f) if(
                        self.arguments.get_argument("label_prefix") != "") else f
                    if(self.arguments.get_argument("label_reglen_offset_format")):
                        (lsb, msb) = HTD_INFO.cr_info.get_cr_field_boundaries(f, self.cr_name, self.regSpace, self.cr_name_filter)
                        labels_str = ("%s_%d_%d") % (labels_str, msb - lsb + 1, 0)
                    self.arguments.set_argument(f, {"strobe": 1, "label": labels_str}, "cr_access_action SRC", True)
            else:
                for current_field in self.get_field_assignment_list():
                    for val in self.arguments.get_argument(current_field):
                        if(val.label != "" and val.label != -1):
                            labels_str = ("%s_%s") % (self.arguments.get_argument("label_prefix"), current_field) if(
                                self.arguments.get_argument("label_prefix") != "") else val.label
                        else:
                            labels_str = ("%s_%s") % (self.arguments.get_argument("label_prefix"), current_field) if(
                                self.arguments.get_argument("label_prefix") != "") else current_field
                        if(self.arguments.get_argument("label_reglen_offset_format")):
                            (lsb, msb) = HTD_INFO.cr_info.get_cr_field_boundaries(current_field, self.cr_name, self.regSpace, self.cr_name_filter)
                            labels_str = ("%s_%d_%d") % (labels_str, msb - lsb + 1, 0)
                        val.label = labels_str
        # ----------------------------
        for field in self.get_field_assignment_list():
            if ((field not in fields_l) and ((self.arguments.get_argument("bfm_mode") == "injection" and field in HTD_INFO.cr_info.get_cr_fields(self.cr_name, self.regSpace, scope))
                                             or (self.arguments.get_argument("bfm_mode") in list(HTD_INFO.RegAccInfo[self.register_access_name].keys()) and field not in HTD_INFO.RegAccInfo[self.register_access_name][self.arguments.get_argument("bfm_mode")]["params"]))):
                if (self.dummy_mode):
                    self.documented = 0
                    self.documented_details = ("Unknown CR field - %s") % field
                    return
                else:
                    htdte_logger.error(("Illegal field-\"%s\" name used in action(%s) .\nAvailable fields are : %s") % (
                        field, self.__action_name__, re.sub(r",", "\n", str(fields_l))))
                    # --Verify rtl signal definition
        self.cr_name_filter = scope
        self.missing_all_rtl_nodes = not HTD_INFO.cr_info.has_no_rtl_nodes(self.cr_name, self.regSpace,
                                                                           scope)
        missing_field_rtl = HTD_INFO.cr_info.get_missing_cr_fields_rtlnodes(self.cr_name, self.regSpace,
                                                                            scope)
        # --Verify dummy method statistic only
        for field in self.get_field_assignment_list():
            if (field in missing_field_rtl):
                self.explicit_rtl_nodes_exists = 0
                self.explicit_rtl_details = (self.explicit_rtl_details if (
                    self.explicit_rtl_details != "default") else "Missing RTL nodes fields:") + field
        for field in missing_field_rtl:
            if (field not in self.get_field_assignment_list()):
                self.implicit_rtl_nodes_exists = 0
                self.implicit_rtl_details = (self.explicit_rtl_details if (
                    self.explicit_rtl_details != "default") else "Missing RTL nodes fields:") + field
        if (self.dummy_mode):
            return
        # ---Verify rtl nodes vs parameter assignment
        if ((self.arguments.get_argument("read_modify_write") or self.arguments.get_argument("check")
             and (not self.arguments.get_argument("read_type")) and (htdPlayer.hplSignalMgr.is_interactive_mode())) or self.arguments.get_argument("bfm_mode") == "injection"):
            # --------Verifying that all assigned argumen---------------
            rtl_verify_fail = 0
            missing_fields_for_verification = {}
            # if bfm_mofr=injrction - expecting  all assignment fields rtl exists
            if (self.arguments.get_argument("bfm_mode") == "injection" or self.arguments.get_argument("check")):
                for field in self.get_field_assignment_list():
                    if (field in missing_field_rtl):
                        rtl_verify_fail = 1
                        argument_for_print = "check" if (self.arguments.get_argument("check")) else "injection-bfm_mode"
                        if (argument_for_print not in list(missing_fields_for_verification.keys())):
                            missing_fields_for_verification[argument_for_print] = []
                        missing_fields_for_verification[argument_for_print].append(field)
            if (self.arguments.get_argument("read_modify_write") and (htdPlayer.hplSignalMgr.is_interactive_mode())):
                for field in missing_field_rtl:
                    if (field not in self.get_field_assignment_list()):
                        rtl_verify_fail = 1
                        argument_for_print = "read_modify_write"
                        if (argument_for_print not in list(missing_fields_for_verification.keys())):
                            missing_fields_for_verification[argument_for_print] = []
                        missing_fields_for_verification[argument_for_print].append(field)
                if (rtl_verify_fail):
                    error_str = ""
                    for mode in list(missing_fields_for_verification.keys()):
                        error_str += (
                            "Trying to use %s - mode while RTL node is not defined for the field-\"%s.%s\".\n") % (
                            mode, self.cr_name, str(missing_fields_for_verification[mode]))
                    else:
                        htdte_logger.error((
                                           "%sPls. use a private \"backdoor_cr_info\" (with specified rtl path) collateral or change the mode argument") % (
                                           error_str))
        # -----Duplicate an instance of register access handler---
        self.regaccess_handler = HTD_INFO.RegAccInfo[self.register_access_name]
        if (self.arguments.get_argument("bfm_mode") != "injection"):
            self.regaccess_obj_handler = copy.deepcopy(self.regaccess_handler[self.arguments.get_argument("bfm_mode")]["obj"])
            self.regaccess_obj_handler.rtl_specification_set(self.cr_name, self.regSpace, scope)
        # --Verify signal integrity----------------------
        if ((self.arguments.get_argument("read_modify_write") or self.arguments.get_argument("check") or (
                self.arguments.get_argument("bfm_mode") == "injection")) and (not self.arguments.get_argument("read_type"))):
            misssing_rtl_nodes = []
            for field in fields_l:
                if (not HTD_INFO.cr_info.has_rtl_node(field, self.cr_name, self.regSpace, self.cr_name_filter)):
                    misssing_rtl_nodes.append(field)
            if (len(misssing_rtl_nodes)):
                if (self.arguments.get_argument("dummy")):
                    self.dummy_verification_status = (
                        ("Missing rtl node for following fields:%s, while accessing to register:\"%s\" ") % (
                            str(misssing_rtl_nodes), self.cr_name))
                else:
                    contradict_mode_str = ("%s%s") % (
                        " in injection mode" if self.arguments.get_argument("bfm_mode") == "injection" else
                        ((" in check mode," if (self.arguments.get_argument("check")) else ""),
                         (" in read_modify_write mode," if (self.arguments.get_argument("read_modify_write")) else "")))
                    htdte_logger.error(
                        ("[%s]:Missing rtl node for following fields:%s, while accessing to register:\"%s\"%s.") % (
                            self.__action_name__, str(misssing_rtl_nodes), self.cr_name, contradict_mode_str))
            if (not self.arguments.get_argument("dummy")):
                for field in fields_l:
                    sigs_l = HTD_INFO.cr_info.resolve_rtl_node(field, self.cr_name, self.regSpace, self.cr_name_filter,
                                                               self.instance_num)
                    for s in sigs_l:
                        self.inform(("Verifying rtl node:%s....") % (s))
                        htdPlayer.hplSignalMgr.signal_exists(s)
        # ----------------------
        for field in self.arguments.get_not_declared_arguments():
            if (field in fields_l):
                (lsb, msb) = HTD_INFO.cr_info.get_cr_field_boundaries(field, self.cr_name, self.regSpace, self.cr_name_filter)
                fsize = msb - lsb + 1  # from tapper???????
                for arg in self.arguments.get_argument(field):
                    if ((arg.lsb < 0) and (arg.msb < 0)):
                        max_val = int(pow(2, fsize) - 1)
                        if (arg.value > max_val):
                            htdte_logger.error((
                                               "field (%s) value is bigger than it's size: field size: %d bits, max val: 0x%x,  field value: 0x%x") % (
                                               field, fsize, max_val, arg.value))
                        if (arg.read_value > max_val):
                            htdte_logger.error((
                                               "field (%s) read value is bigger than it's size: field size: %d bits, max val: 0x%x,  field read value: 0x%x") % (
                                               field, fsize, max_val, arg.read_value))
                    else:
                        max_val = int(pow(2, arg.msb - arg.lsb + 1) - 1)
                        if (arg.lsb > msb or arg.msb > msb):
                            htdte_logger.error(("field (%s) sub range (%d:%d) exceed the field boundaries (%d:%d)") % (
                                field, arg.lsb, arg.msb, lsb, msb))
                        elif (arg.value > max_val):
                            htdte_logger.error((
                                               "field (%s[%d:%d]) value is bigger than it's subrange size:%d bits, max val: 0x%x,  field value: 0x%x") % (
                                               field, arg.lsb, arg.msb, arg.lsb - arg.msb + 1, max_val, arg.value))
                        if (arg.read_value > max_val):
                            htdte_logger.error((
                                               "field (%s) read value is bigger than it's subrange size: %d bits, max val: 0x%x,  field read value: 0x%x") % (
                                               field, arg.lsb - arg.msb + 1, max_val, arg.read_value))
                            # -------------------------------

        # -------------------------------------
        self.compression = self.arguments.get_argument("compression")
        self.expandata = self.arguments.get_argument("expandata")
        self.pscand_en = self.arguments.get_argument("pscand_en")
        self.pscand_group_override = self.arguments.get_argument("pscand_group_override")
        self.cfg_list_override = self.arguments.get_argument("cfg_list_override")

    def has_required_rtlNodes_info(self):
        return (HTD_INFO.cr_info.has_no_rtl_nodes(self.cr_name, self.regSpace, self.arguments.get_argument("scope")), self.cr_name)

    # ------------------
    #
    # -----------------
    def run(self):
        # FIXME - add actual action execution
        self.inform(("         Running %s::%s:%s:%d \n\n") % (
            htd_base_action.get_action_type(self),
            htd_base_action.get_action_name(self),
            htd_base_action.get_action_call_file(self),
            htd_base_action.get_action_call_lineno(self)))
        scope_list = self.get_final_list_of_scopes()
        if(not self.arguments.get_argument("compression")):
            htdPlayer.tap_compression_off()
        if (len(scope_list) > 0):
            for scope in scope_list:
                self.run_single_scope(scope)
        else:
            self.run_single_scope("")
        if(not self.arguments.get_argument("compression")):
            htdPlayer.tap_compression_on()

    def run_single_scope(self, scope):

        htdte_logger.inform("Execution of single scope register %s" % (scope))
        (self.dictionary_name, self.registerfile) = HTD_INFO.cr_info.get_cr_info_and_regfile_name(self.cr_name, self.regSpace, scope)
        self.registerfileRegExp = ("^%s$") % self.registerfile

        if (self.arguments.get_argument("bfm_mode") == "injection" and not self.arguments.get_argument("read_type")):
            # -------------------------------
            fields_l = self.get_field_assignment_list()
            doc_reg_fields = HTD_INFO.cr_info.get_cr_fields(self.cr_name, self.regSpace, scope)
            if (self.arguments.get_argument("dri", 1) < 0 and self.arguments.get_argument("dro", 1) < 0):
                for field in fields_l:
                    if(field not in doc_reg_fields):
                        continue
                    (lsb, msb) = (-1, -1)
                    for val in self.arguments.get_argument(field):
                        if (val.lsb > 0):
                            lsb = val.lsb
                        if (val.msb > 0):
                            msb = val.msb
                        sigs_l = HTD_INFO.cr_info.resolve_rtl_node(field, self.cr_name, self.regSpace, self.cr_name_filter,
                                                                   self.instance_num)
                        for s in sigs_l:
                            signal_path_override = 0
                            signal_path = s
                            (path, error) = self.get_signal_path_override(field)
                            if error:
                                htdte_logger.error("Wrong <Var> definition for signal path override in TE_cfg file - key: \"%s\": Missing "
                                                   "\"reg\" or \"field\" or \"path\" =<value> attribute ...." % self.registerfile)
                            elif path != "":
                                signal_path = path
                                signal_path_override = 1
                            (chunk_sig, chunk_val) = HTD_INFO.signal_info.normalize_to_32_bit_signals(signal_path, val.value,
                                                                                                      msb - lsb + 1)
                            for i in range(0, len(chunk_sig)):
                                htdPlayer.hplSignalMgr.signal_set(chunk_sig[i], -1, -1, chunk_val[i], signal_path_override=signal_path_override)
            elif (tap_params.dr.get_argument("dro", 1) == "N/A"):
                fields_l = get_cr_fields()
                for f in fields_l:
                    (lsb, msb) = (-1, -1)
                    for val in HTD_INFO.cr_info.arguments.get_argument(field):
                        if (val.lsb > 0):
                            lsb = val.lsb
                        if (val.msb > 0):
                            msb = val.msb
                        mask_hi = pow(2, msb) - 1
                        mask_lo = pow(2, lsb) - 1
                        mask = mask_hi ^ mask_lo
                        sigs_l = HTD_INFO.cr_info.resolve_rtl_node(field, self.cr_name, self.regSpace, self.cr_name_filter,
                                                                   self.instance_num)
                        for s in sigs_l:
                            signal_path = s
                            (path, error) = self.get_signal_path_override(field)
                            if error:
                                htdte_logger.error("Wrong <Var> definition for signal path override in TE_cfg file - key: \"%s\": Missing "
                                                   "\"reg\" or \"field\" or \"path\" =<value> attribute ...." % self.registerfile)
                            elif path != "":
                                signal_path = path
                            (chunk_sig, chunk_val) = HTD_INFO.signal_info.normalize_to_32_bit_signals(signal_path,
                                                                                                      self.arguments.get_argument(
                                                                                                          "dri") & mask,
                                                                                                      msb - lsb + 1)
                            for i in range(0, len(chunk_sig)):
                                htdPlayer.hplSignalMgr.signal_poke(chunk_sig[i], -1, -1, chunk_val[i])
        else:
            # --------BFM---------------
            data_by_field = {}
            user_assigned_fields = []
            fields_l = HTD_INFO.cr_info.get_cr_fields(self.cr_name, self.regSpace, scope)
            if (not self.arguments.get_argument("read_type")):
                if (htdPlayer.hplSignalMgr.is_interactive_mode() and self.arguments.get_argument("read_modify_write")):
                    if (self.arguments.get_argument("dri", 1) < 0 and self.arguments.get_argument("dro", 1) < 0):
                        for field in fields_l:
                            if (field not in self.get_field_assignment_list()):
                                data_by_field[field] = htdPlayer.htdPlayer.signal_peek(
                                    HTD_INFO.cr_info.resolve_rtl_node(field, self.cr_name, self.regSpace, self.cr_name_filter,
                                                                      self.instance_num)[0])
                    elif (self.arguments.get_argument("dri", 1) >= 0):
                        if (self.arguments.arg_l["dri"]["msb"] >= 0 and self.arguments.arg_l["dri"]["lsb"] >= 0):
                            for field in fields_l:
                                (lsb, msb) = HTD_INFO.cr_info.get_cr_field_boundaries(field, self.cr_name, self.regSpace,
                                                                                      self.cr_name_filter)
                                if (lsb > self.arguments.arg_l["dri"]["msb"] or (
                                        msb < self.arguments.arg_l["dri"]["lsb"])):
                                    data_by_field[field] = htdPlayer.htdPlayer.signal_peek(
                                        HTD_INFO.cr_info.resolve_rtl_node(field, self.cr_name, self.regSpace, self.cr_name_filter,
                                                                          self.instance_num)[0])
                # end of read_modify_write-----
                elif (self.arguments.get_argument("incremental_mode") and Reg_history.has(self.cr_name,
                                                                                          self.registerfile)):
                    for field in fields_l:
                        if (self.arguments.get_argument("dri", 1) < 0 and self.arguments.get_argument("dro", 1) < 0):
                            if (field not in self.get_field_assignment_list()):
                                data_by_field[field] = Tap_history.get(self.cr_name, self.registerfile, field)
                        elif (self.arguments.get_argument("dri", 1) >= 0):
                            for field in fields_l:
                                (lsb, msb) = HTD_INFO.cr_info.get_cr_field_boundaries(field, self.cr_name, self.regSpace,
                                                                                      self.cr_name_filter)
                                if (lsb > self.arguments.arg_l["dri"]["msb"] or (
                                        msb < self.arguments.arg_l["dri"]["lsb"])):
                                    data_by_field[field] = Tap_history.get(self.cr_name, self.registerfile, field)
                                    # end of incremental mode
                else:
                    for field in fields_l:
                        if (self.arguments.get_argument("dri", 1) < 0 and self.arguments.get_argument("dro", 1) < 0):
                            if (field not in self.get_field_assignment_list()):
                                data_by_field[field] = HTD_INFO.cr_info.get_cr_field_reset_val(field, self.cr_name, self.regSpace,
                                                                                               self.registerfileRegExp)
                        elif (self.arguments.get_argument("dri", 1) >= 0):
                            for field in fields_l:
                                (lsb, msb) = HTD_INFO.cr_info.get_cr_field_boundaries(field, self.cr_name, self.regSpace,
                                                                                      self.cr_name_filter)
                                if (lsb > self.arguments.arg_l["dri"]["msb"] or (
                                        msb < self.arguments.arg_l["dri"]["lsb"])):
                                    data_by_field[field] = HTD_INFO.cr_info.get_cr_field_reset_val(field, self.cr_name, self.regSpace,
                                                                                                   self.registerfileRegExp)
            # ----------Assign user requested fields-------------------------------------------------
            read_and_write_transaction = 0
            for field in fields_l:
                if (self.arguments.get_argument("dri", 1) < 0 and self.arguments.get_argument("dro", 1) < 0):
                    if (field in self.get_field_assignment_list()):
                        (lsb, msb) = HTD_INFO.cr_info.get_cr_field_boundaries(field, self.cr_name, self.regSpace, self.cr_name_filter)
                        for val in self.arguments.get_argument(field):
                            val.value = val.read_value if (self.arguments.get_argument("read_type")) else (val.value)
                            if (val.lsb >= 0 and val.msb >= 0):
                                mask = pow(2, val.msb + 1) - pow(2,
                                                                 val.lsb)  # make all msb bits are 1's :Example msb=5 : 0111111,
                                reversed_mask = (pow(2, msb - lsb + 1) - 1) ^ mask
                                data_by_field[field] = ((data_by_field[field] & reversed_mask) if (
                                    field in list(data_by_field.keys())) else 0) | ((val.value << val.lsb) & mask)
                            else:
                                data_by_field[field] = val.value
                        user_assigned_fields.append(field)
                elif (self.arguments.get_argument("dri", 1) >= 0):
                    (lsb, msb) = HTD_INFO.cr_info.get_cr_field_boundaries(field, self.cr_name, self.regSpace, self.cr_name_filter)
                    if (lsb > self.arguments.arg_l["dri"]["msb"] or (msb < self.arguments.arg_l["dri"]["lsb"])):
                        fields_l = HTD_INFO.cr_info.get_cr_fields(self.cr_name, self.regSpace, scope)
                        for f in fields_l:
                            (f_lsb, f_msb) = HTD_INFO.cr_info.get_cr_field_boundaries(f, self.cr_name, self.regSpace,
                                                                                      self.cr_name_filter)
                            data_by_field[f] = self.arguments.get_argument("dri") & util_calculate_range_mask(
                                self.arguments.get_argument("dri"), f_lsb, f_msb)
                        user_assigned_fields.append(field)
            # -------------------------
            for fld in data_by_field:
                self.capture_register_assignment_by_field(fld, data_by_field[fld])
            # -------------------------
            field_comments = {}
            for field in self.get_field_assignment_list():
                (field_lsb, field_msb) = HTD_INFO.cr_info.get_cr_field_boundaries(field, self.cr_name, self.regSpace,
                                                                                  self.cr_name_filter)
                if (data_by_field[field] >= 0):
                    field_comments[field_lsb] = " test content assignment: [%d:%d] %s=> 0x%x" % (field_lsb,
                                                                                                 field_msb,
                                                                                                 field,
                                                                                                 data_by_field[field])
                elif (self.arguments.get_argument(field)):
                    field_comments[field_lsb] = " test content assignment: [%d:%d] %s=> strobe" % (field_lsb,
                                                                                                   field_msb,
                                                                                                   field)
            for field in fields_l:
                if (field not in user_assigned_fields and not self.arguments.get_argument("read_type")):
                    (field_lsb, field_msb) = HTD_INFO.cr_info.get_cr_field_boundaries(field, self.cr_name,
                                                                                      self.regSpace,
                                                                                      self.cr_name_filter)

                    field_comments[field_lsb] = " default assignment:      [%d:%d] %s=> 0x%x" % (field_lsb,
                                                                                                 field_msb,
                                                                                                 field,
                                                                                                 data_by_field[field])
            # Print all the fields at once, so they can be neatly sorted by bitorder
            for key in sorted(field_comments):
                htdPlayer.hpl_to_dut_interface.add_comment(field_comments[key])
            # ------override regaccess ui parameters----------------
            if(self.arguments.get_argument("bfm_mode") != "injection"):
                for arg in self.get_ui_assignment_list():
                    setattr(self.regaccess_obj_handler, arg, self.arguments.get_argument(arg)[0].value)
                # -----------------
                if(1):
                    # try:
                    if (not self.arguments.get_argument("read_type")):
                        self.regaccess_obj_handler.write(self, self.get_curr_flow(), self.cr_name, self.regSpace, self.registerfileRegExp,
                                                         data_by_field, self.arguments, self.register_access_name, self.regaccess_handler,
                                                         self.express_mode)
                    else:
                        self.regaccess_obj_handler.read(self, self.get_curr_flow(), self.cr_name, self.regSpace, self.registerfileRegExp,
                                                        data_by_field, self.arguments, self.register_access_name, self.regaccess_handler,
                                                        self.arguments.get_argument("strobe_disable"), self.express_mode)
                # except AttributeError:
                #    traceback.print_exc()
                #    err_str = str(sys.exc_info()[1])
                #    m = re.match("'([A-z0-9_]+)'\s+object\s+has\s+no\s+attribute\s+'([A-z0-9_]+)'", err_str)
                #    if (m):
                #        self.error((
                #          	 "Unknown RegAcc attribute used in access (\"%s\") handler ,pls. verify if RegAcc(\"%s\") missing %s=\"<actual_project_value>\" attribute or miss spelled.\n") % (
                #          	 self.arguments.get_argument("bfm_mode"), self.register_access_name, m.groups()[1]), 1)
                #    else:
                #        self.error((
                #          	 "Unknown RegAcc attribute used in access handler ,pls. verify if RegAcc(\"%s:%s\") missing <attribute_name>=\"<actual_project_value>\" attribute or miss spelled.\n") % (
                #          	 self.register_access_name, self.arguments.get_argument("bfm_mode")), 1)

                    #htdte_logger.error(("Only injection bfm mode implemented so far "))
        # htdPlayer.tap_send_cmd(self.tap_param_container)
        # Verify rtl node and wait until completion to be executed by player
        if (not self.arguments.get_argument("read_type")):
            if (self.arguments.get_argument("check")):
                if (self.arguments.get_argument("bfm_mode") != "injection"):
                    sigs_l = []
                    sig_val_l = []
                    override_sigs_l = []
                    non_declared_args = list(self.arguments.get_not_declared_arguments().keys())
                    for field in list(data_by_field.keys()):
                        (lsb, msb) = HTD_INFO.cr_info.get_cr_field_boundaries(field, self.cr_name, self.regSpace, self.cr_name_filter)
                        if(HTD_INFO.cr_info.has_crfield_property_by_name(self.cr_name, field, 'access', self.regSpace, self.cr_name_filter)
                           and HTD_INFO.cr_info.get_crfield_property_by_name(self.cr_name, field, 'access', self.regSpace, self.cr_name_filter) in XREG_ReadOnlyRegisterAccessEncoding):
                            continue
                        sig_selector = "."
                        if (self.arguments.get_argument("specific_core") > -1):
                            sig_selector = "[%d]" % (self.arguments.get_argument("specific_core"))
                        signodes = HTD_INFO.cr_info.resolve_rtl_node(field, self.cr_name, self.regSpace, self.cr_name_filter,
                                                                     self.instance_num, sig_selector)

                        if (not self.field_should_be_verified(field, non_declared_args)):
                            continue
                        if (isinstance(signodes, list)):
                            for s in signodes:
                                signal_path_override = 0
                                signal_path = s
                                (path, error) = self.get_signal_path_override(field)
                                if error:
                                    htdte_logger.error("Wrong <Var> definition for signal path override in TE_cfg file - key: \"%s\": Missing "
                                                       "\"reg\" or \"field\" or \"path\" =<value> attribute ...." % self.registerfile)
                                elif path != "":
                                    signal_path = path
                                    signal_path_override = 1
                                (chunk_sig, chunk_val) = HTD_INFO.signal_info.normalize_to_32_bit_signals(signal_path,
                                                                                                          data_by_field[
                                                                                                              field],
                                                                                                          msb - lsb + 1)
                                sigs_l.extend(chunk_sig)
                                sig_val_l.extend(chunk_val)
                                if (signal_path_override == 1):
                                    override_sigs_l.extend(chunk_sig)
                        else:
                            signal_path_override = 0
                            signal_path = signodes
                            (path, error) = self.get_signal_path_override(field)
                            if error:
                                htdte_logger.error("Wrong <Var> definition for signal path override in TE_cfg file - key: \"%s\": Missing "
                                                   "\"reg\" or \"field\" or \"path\" =<value> attribute ...." % self.registerfile)
                            elif path != "":
                                signal_path = path
                                signal_path_override = 1
                            (chunk_sig, chunk_val) = HTD_INFO.signal_info.normalize_to_32_bit_signals(signal_path,
                                                                                                      data_by_field[
                                                                                                          field],
                                                                                                      msb - lsb + 1)
                            sigs_l.exend(chunk_sig)
                            sig_val_l.extend(chunk_val)
                            if (signal_path_override == 1):
                                override_sigs_l.extend(chunk_sig)

                    # ---If the size of field i.e signal exceed 32 bits, split it to different chunks
                    htdPlayer.hplSignalMgr.signalset_wait(htdPlayer.hplSignalMgr.signalset_pack(sigs_l, sig_val_l),
                                                          self.arguments.get_argument("waitcycles"),
                                                          self.arguments.get_argument("maxtimeout"),
                                                          self.arguments.get_argument("refclock"), 1, override_sigs_l = override_sigs_l)
            else:
                if(self.arguments.get_argument("waitcycles") != 0):
                    htdPlayer.hpl_to_dut_interface.wait_clock_num(self.arguments.get_argument("waitcycles"),
                                                                  self.arguments.get_argument("refclock"))
                else:
                    htdte_logger.inform("Wait time set to 0, thus, it will not be printed in itpp")
        else:
            if (self.arguments.get_argument("check")):
                field_counter = 0
                non_declared_args = list(self.arguments.get_not_declared_arguments().keys())
                for field in HTD_INFO.cr_info.get_cr_fields(self.cr_name, self.regSpace, scope):
                    (lsb, msb) = HTD_INFO.cr_info.get_cr_field_boundaries(field, self.cr_name, self.regSpace, self.cr_name_filter)
                    sig_val_l = []
                    sigs_l = []
                    override_sigs_l = []
                    if (self.arguments.get_argument("dro", 1) < 0):
                        if (field in self.get_field_assignment_list()):
                            # data assignment in read is negative (-1) only if "strobe" rtl value is assign(lsb,msb)=HTD_INFO.cr_info.get_cr_field_boundaries(field,self.cr_name,self.cr_name_filter)
                            if (data_by_field[field] >= 0):
                                sig_selector = "."
                                if (self.arguments.get_argument("specific_core") > -1 and re.match(r"CORE\d_CORE", self.regaccess_obj_handler.tap)):
                                    sig_selector = "[%d]" % (self.arguments.get_argument("specific_core"))
                                signodes = HTD_INFO.cr_info.resolve_rtl_node(
                                    field, self.cr_name, self.regSpace, self.cr_name_filter, self.instance_num, sig_selector)

                                if (not self.field_should_be_verified(field, non_declared_args)):
                                    continue
                                if (isinstance(signodes, list)):
                                    for s in signodes:
                                        signal_path_override = 0
                                        signal_path = s
                                        (path, error) = self.get_signal_path_override(field)
                                        if error:
                                            htdte_logger.error("Wrong <Var> definition for signal path override in TE_cfg file - key: \"%s\": Missing "
                                                               "\"reg\" or \"field\" or \"path\" =<value> attribute ...." % self.registerfile)
                                        elif path != "":
                                            signal_path = path
                                            signal_path_override = 1
                                        (chunk_sig, chunk_val) = HTD_INFO.signal_info.normalize_to_32_bit_signals(signal_path,
                                                                                                                  data_by_field[
                                                                                                                      field],
                                                                                                                  msb - lsb + 1)
                                        sigs_l.extend(chunk_sig)
                                        sig_val_l.extend(chunk_val)
                                        if (signal_path_override == 1):
                                            override_sigs_l.extend(chunk_sig)
                                else:
                                    signal_path_override = 0
                                    signal_path = signodes
                                    (path, error) = self.get_signal_path_override(field)
                                    if error:
                                        htdte_logger.error("Wrong <Var> definition for signal path override in TE_cfg file - key: \"%s\": Missing "
                                                           "\"reg\" or \"field\" or \"path\" =<value> attribute ...." % self.registerfile)
                                    elif path != "":
                                        signal_path = path
                                        signal_path_override = 1
                                    (chunk_sig, chunk_val) = HTD_INFO.signal_info.normalize_to_32_bit_signals(
                                        signal_path, data_by_field[field], msb - lsb + 1)
                                    sigs_l.extend(chunk_sig)
                                    sig_val_l.extend(chunk_val)
                                    if (signal_path_override == 1):
                                        override_sigs_l.extend(chunk_sig)
                                generic_wait_assign = 1 if (field_counter == 0) else 0
                                htdPlayer.hplSignalMgr.signalset_wait(htdPlayer.hplSignalMgr.signalset_pack(sigs_l, sig_val_l),
                                                                      self.arguments.get_argument("waitcycles"),
                                                                      self.arguments.get_argument(
                                                                          "maxtimeout"), self.arguments.get_argument("refclock"),
                                                                      generic_wait_assign, override_sigs_l=override_sigs_l)
                                field_counter = field_counter + 1

    def get_signal_path_override(self, field): 
        signal_path = ""
        error = 0
        if ("signal_path_override" in list(CFG.keys())):
            if (self.registerfile in list(CFG["signal_path_override"].keys())):
                if ("reg" not in list(CFG["signal_path_override"][self.registerfile].keys()) or "field" not in list(CFG["signal_path_override"][self.registerfile].keys()) or "path" not in list(CFG["signal_path_override"][self.registerfile].keys())):
                    error = 1
                    return (signal_path, error)
                elif (CFG["signal_path_override"][self.registerfile]["reg"] == self.cr_name and CFG["signal_path_override"][self.registerfile]["field"] == field and CFG["signal_path_override"][self.registerfile]["path"] != ""):
                    return (CFG["signal_path_override"][self.registerfile]["path"], error)
                else:
                    return (signal_path, error)
            else:
                return (signal_path, error)
        else:
            return (signal_path, error)

    def get_defined_label(self):
        documented_size = HTD_INFO.cr_info.get_cr_property_by_name(self.cr_name, 'size', self.regSpace,
                                                                   self.arguments.get_argument("scope"))
        htdte_logger.inform("flow %s phase %s" % (self.get_curr_flow(), self.get_curr_flow().phase_name))
        label_name = "%s__%s__0__%d__Phase%s" % (self.get_action_name(), self.cr_name, documented_size - 1,
                                                 self.get_curr_flow().phase_name if self.get_curr_flow().phase_name != "" else "None")
        return label_name

    def field_should_be_verified(self, field, non_declared_args):
        # not part of arguments
        if (field not in non_declared_args):
            return 1

        # part of arguments - check the verify value
        field_arg_verify = 1
        field_arg = self.arguments.get_argument(field)
        for field_val in field_arg:
            field_arg_verify = field_val.verify_arg
        return field_arg_verify
