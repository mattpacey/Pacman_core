from htd_basic_action import *
from htd_utilities import *
from htd_collaterals import *
import htd_arguments_container
import htd_patmod_manager
from htd_player_top import *
import re
# ---------------------------------------------


class TAP_activity_logger(object):

    def __init__(self):
        if ("TapActivityLogger" in list(CFG.keys()) and "enabled" in list(CFG["TapActivityLogger"].keys()) and CFG["TapActivityLogger"]["enabled"] == 1):
            if ("logger_filename" in list(CFG["TapActivityLogger"].keys())):
                self.__logName = CFG["TapActivityLogger"]["logger_filename"]
            else:
                self.__logName = "TapLogger.csv"
            self.__logObject = open(self.__logName, 'w')
            self.__logObject.write("action,agent,pattern label,stimulus length,stimulus value,expected length,expected_value\n")
        else:
            self.__logName = ""
            self.__logObject = None

    def __del__(self):
        if (self.__logObject is not None):
            self.__logObject.close()

    def write_data(self, action, agent, pattern_label, stimulus_value, expected_value):
        if (self.__logObject is not None):

            label_index_str = ""
            delim = ""
            for l in list(pattern_label.keys()):
                label_index_str = ("%s%s%s@%d") % (label_index_str, delim, pattern_label[l], l)
                delim = ";"

            self.__logObject.write("%s,%s,%s,%d,0b%s,%d,%s\n" % (action, agent, label_index_str,
                                                                 len(stimulus_value), stimulus_value, len(expected_value), expected_value))

    def enabled(self):
        return (self.__logObject is not None)


class TAP(htd_base_action):
    # static member - initalized once
    tap_activity_logger = TAP_activity_logger()

    def __init__(self, action_name, source_file, source_lineno, currentFlow, is_internal):
        self.ircode = -1
        self.irname = ""
        self.agent = ""
        self.parallel = 1
        self.drsize = -1
        self.irsize = -1
        self.mask_dro = -1
        self.assigned_fields = {}
        # pscand_en pscand_delay and pscand_pins depreciated. Please set these using the TE_cfg NoaOffsets.
        self.pscand_delay = CFG["HPL"].get("pscand_delay", 0)
        self.pscand_pins = CFG["HPL"].get("pscand_pins", "")
        self.pscand_en = -1
        self.field_labels_ena = 0
        self.automatic_labels_ena = CFG["HPL"]["automatic_labels_ena"] if("automatic_labels_ena" in list(CFG["HPL"].keys())) else 0
        self.instr_interface_print_ena = 0
        # ----------------
        htd_base_action.__init__(self, self.__class__.__name__, action_name, source_file, source_lineno, currentFlow,
                                 is_internal)
        self.arguments.set_argument("source", 1, "Specify which source for this action")
        self.arguments.declare_arg("ir", "The TAP destintation CMD name or binary CMD code      ", "string_or_int", "", 1)
        self.arguments.declare_arg("agent", "The TAP link destination agent name .", "string", "", 1)
        self.arguments.declare_arg("dri", "The TAP register entire DATA assignment (aligned to register length) ", "int", -1, 0)
        self.arguments.declare_arg("dro", "The expected TAP DATA register shiftout (aligned to register length)", "int", -1, 0)
        self.arguments.declare_arg("mask_dro", "The expected TAP DATA register shiftout mask (aligned to register length)", "int", -1, 0)
        self.arguments.declare_arg("drsize", "Enforce user dr length (used in conjunction with dri/dro)  ", "int", -1, 0)
        self.arguments.declare_arg("bfm_mode", "The bfm mode: express|injection|normal ", ["express", "injection", "normal"], "normal", 0)
        self.arguments.declare_arg("parallel_mode", "Used to dis/ena taplink parallel/specific taplink endpoint access  ", "bool", 1, 0)
        self.arguments.declare_arg("read_modify_write", "Read rtl and override user assignment ena/dis ", "bool", 0, 0)
        self.arguments.declare_arg("field_labels", "ena/dis instrumental per field label assignment ", "bool", 0, 0)
        self.arguments.declare_arg("field_labels_per_action", "Enable default field labels per action ", "bool", 0, 0)
        self.arguments.declare_arg(
            "man_field_labels", "ena manual instrumental per field label assignment on specified labels", "string_or_list", 0, 0)
        self.arguments.declare_arg("incremental_mode", "History incremental register initilization ena/dis ", "bool", 0, 0)
        self.arguments.declare_arg("compression", "Compression On/Off ", "bool",
                                   0 if("compression" not in list(CFG["HPL"].keys())) else int(CFG["HPL"]["compression"]), 0)
        self.arguments.declare_arg("expandata", "Slow TCLK for this instruction by this multiplier", "int", -1, 0)
        # pscand_en depreciated. Please set these using the TE_cfg NoaOffsets.
        self.arguments.declare_arg("pscand_en", "Enable pscand on compare", "bool", 0, 0)
        self.arguments.declare_arg(
            "postfocus_delay", "Adding delay of TCK cycles after focusing to target agent on TAP Network protocol", "int", 0, 0)
        self.arguments.declare_arg("shadow_agents", "List of shadow tap agents in TAP Network hierarchy", "string", "", 0)
        if CFG["HPL"].get("NEW_LABEL_SPEC"):
            default_prefix = "ph%s__%s_" % (self.get_curr_flow().phase_name, action_name)
        else:
            default_prefix = ""
        self.arguments.declare_arg("label_prefix", "Label prefix to be added automatically to all generated labels ", "string", default_prefix, 0)
        self.arguments.declare_arg("label_reglen_offset_format", "Create labels for strobbing in format <label>_<chainlen>_<offset> ", "bool", 0, 0)
        self.arguments.declare_arg("first_rdbit_label", "Assign label on first read bit", "string", "", 0)
        self.arguments.declare_arg("dronly", "Prevent IR select on remote controller (if has been choosed previously)", "bool", 0, 0)
        self.arguments.declare_arg("print_unset_defaults", "Enables/disables adding default value that aren't specifically set in the action to the output",
                                   "bool", 1 if ("print_unset_defaults" not in CFG["HPL"]) else CFG["HPL"]["print_unset_defaults"], 0)

        self.arguments.declare_arg("pscand_group_override", "Override the automatic pscand group name", "string", "", 0)
        self.arguments.declare_arg("cfg_list_override", "Override the automatic cfg list name", "string", "", 0)
        self.arguments.declare_arg("overshift_en", "enable overshift mode", "bool", 0, 0)
        self.arguments.declare_arg("overshift_marker", "overshift marker value in overshift mode", "string", None, 0)
        self.arguments.declare_arg("ir_tdi_align_label", "Align IR label to TDI data", "bool", 0, 0)
        self.arguments.declare_arg("dba_mode", "Used to dis/ena Dynamic Base Address directive in focus_tap", "bool", 0, 0)

        # ------------------------
        self.arguments.enable_dual_read_write_mode()
        # ---------Define unique action indexing by declared arguments ------------------
        self.assign_action_indexing(["agent", "ir"])
        self.assign_action_indexing(["agent", "dri"])
        # ----------------------------
        self.tap_protocol = ""
        if ("HPL" in list(CFG.keys())):
            if ("tap_mode" in list(CFG["HPL"].keys())):
                self.tap_protocol = CFG["HPL"]["tap_mode"]
        if ("TE" in list(CFG.keys())):
            if ("tap_mode" in list(CFG["TE"].keys())):
                self.tap_protocol = CFG["TE"]["tap_mode"]
        if (self.tap_protocol not in ["tapnetwork", "taplink"]):
            self.error((
                       "Action's (%s) : Illegal TAP protocol type selection in CFG[\"TE\"][\"tap_mode\"]: expected \"tapnetwork\" or \"taplink\" ,received - \"%s\" ") % (
                       self.__action_name__, self.tap_protocol), 1)
            # ------------------------

    #
    # ------------------------
    def get_action_not_declared_argument_names(self):
        return HTD_INFO.tap_info.get_ir_fields(self.irname, self.agent)

    # ------------------------
    #
    # ------------------------
    def verify_arguments(self):

        self.inform(("       Verifying %s::%s:%s:%d ....") % (htd_base_action.get_action_type(self),
                                                              htd_base_action.get_action_name(self),
                                                              htd_base_action.get_action_call_file(self),
                                                              htd_base_action.get_action_call_lineno(self)))

        HTD_INFO.verify_info_ui_existence(["tap_info", "signal_info"])
        self.verify_obligatory_arguments()
        # -----------------------------------------
        if (type(self.arguments.get_argument("ir")) == int):
            self.ircode = self.arguments.get_argument("ir")
        elif (type(self.arguments.get_argument("ir")) in [str, str]):
            if (isinstance(self.arguments.get_argument("ir"), int)):
                self.ircode = int(self.arguments.get_argument("ir"), 2)
            else:
                self.irname = self.arguments.get_argument("ir")
        else:
            self.error(("Action's (%s) illegal argument -\"ir\" type - \"%s\".Expected int or str. ") % (
                self.__action_name__, type(self.arguments.get_argument("ir"))), 1)
            # ---------------------Verify fields----------------------------------------------------------------------
        if (self.arguments.get_argument("dri") >= 0 and len(list(self.arguments.get_not_declared_arguments().keys()))):
            self.error((
                       "Action's (%s) illegal arguments combination: \"dri\"=%s argument could not be used with per field assignment: %s. ") % (
                       self.__action_name__, self.arguments.get_argument("dri"),
                       list(self.arguments.get_not_declared_arguments().keys())), 1)
        if (self.arguments.get_argument("mask_dro") >= 0 and len(list(self.arguments.get_not_declared_arguments().keys()))):
            self.error((
                       "Action's (%s) illegal arguments combination: \"mask_dro\"=%s argument could not be used with per field assignment: %s. ") % (
                       self.__action_name__, self.arguments.get_argument("mask_dro"),
                       list(self.arguments.get_not_declared_arguments().keys())), 1)
        if (self.arguments.get_argument("dro") >= 0 and len(list(self.arguments.get_not_declared_arguments().keys()))):
            self.error((
                       "Action's (%s) illegal arguments combination: \"dro\"=%s argument could not be used with per field assignment: %s. ") % (
                       self.__action_name__, self.arguments.get_argument("dro"),
                       list(self.arguments.get_not_declared_arguments().keys())), 1)
        if (self.arguments.get_argument("dro") >= 0 and (not self.arguments.get_argument("read_type"))):
            self.error((
                       "Action's (%s) illegal arguments combination: \"dro\"=%s argument should be used in couple with \"read_type\"=1 only. ") % (
                       self.__action_name__, self.arguments.get_argument("dro")), 1)
            # ---------------------
        if (self.irname == "" and self.ircode < 0):
            htdte_logger.error(
                ("Illegal  action(%s) definition:  no irname and no ircode has been assigned") % (self.__action_name__))
        if (self.irname != ""):
            self.ircode = HTD_INFO.tap_info.get_ir_opcode_int(self.irname, self.arguments.get_argument("agent"),
                                                              self.dummy_mode)
            if (self.ircode == 0):
                self.documented = 0
                self.documented_details = (
                    ("Unknown TAP agent:register - %s:%s") % (self.arguments.get_argument("agent"), self.irname))
                return
                # if(HTD_INFO.tap_info.get_ir_name( self.ircode,self.arguments.get_argument("agent"),self.dummy_mode)!=self.irname):
                #    htdte_logger.error(("%s:Tap info integrity error : irname(%s)->ircode(0x%x)!=irname(%s)")%(self.__action_name__,self.irname,self.ircode,HTD_INFO.tap_info.get_ir_name( self.ircode,self.arguments.get_argument("agent"),self.dummy_mode)))
        if (self.ircode > 0 and self.irname == ""):
            self.irname = HTD_INFO.tap_info.get_ir_name(self.ircode, self.arguments.get_argument("agent"),
                                                        self.dummy_mode)
            if (self.irname == ""):
                self.documented = 0
                self.documented_details = (
                    ("Cant get TAP agent:ircode - %s:0x%x") % (self.arguments.get_argument("agent"), self.ircode))
                return
        # ----------------------------
        self.agent = self.arguments.get_argument("agent")

        list_of_execluded_parallel_agents = []
        if ("excluded_parallel_agents" in CFG["HPL"]):
            list_of_execluded_parallel_agents = CFG["HPL"]["excluded_parallel_agents"].split(',')

        self.parallel = self.arguments.get_argument("parallel_mode")

        if (self.agent in list_of_execluded_parallel_agents):
            htdte_logger.inform("Agent %s can't run in parallel, setting it to run in serial" % (self.agent))
            self.parallel = 0
        # If is a read and parallel mode is enabled but pscan is not check if autoswitch is set and change to serial
        # TODO find out if this should be set by default
        elif self.parallel == 1 and self.noa_offset_mode_needed() == 0 and self.arguments.get_argument("read_type") and CFG["HPL"].get("switch_par2ser_pscand_dis") == 1:
            htdte_logger.inform("Auto switching action to serial mode as this is a read and pscand is not enabled!")
            self.parallel = 0

        self.drsize = self.arguments.get_argument("drsize") if (self.arguments.get_argument(
            "drsize") > 0) else HTD_INFO.tap_info.get_dr_total_length(self.irname, self.agent)
        if (self.arguments.get_argument("dri", 1) >= 0 and self.arguments.arg_l["dri"]["msb"] > 0):
            if (self.arguments.arg_l["dri"]["msb"] >= self.arguments.get_argument("drsize")):
                htdte_logger.error(("Trying to assign tap raw data (\"dri\[lsb:%d]\") out of register size -%d") % (
                    self.arguments.arg_l["dri"]["msb"], self.arguments.get_argument("drsize")))
            self.drsize = self.arguments.arg_l["dri"]["msb"] if(self.arguments.arg_l["dri"]["msb"] > self.drsize) else self.drsize
        if (self.arguments.get_argument("dro", 1) >= 0 and self.arguments.arg_l["dro"]["msb"] > 0):
            if (self.arguments.arg_l["dro"]["msb"] >= self.arguments.get_argument("drsize")):
                htdte_logger.error((
                                   "Trying to assign tap output raw data (\"dro[%d:%d]\") out of register size (\"drsize\"):%d.Pls. review documented size or override by argument \"drsize\":%d ") % (
                                   self.arguments.arg_l["dro"]["msb"], self.arguments.arg_l["dro"]["lsb"],
                                   self.arguments.get_argument("drsize"), self.arguments.arg_l["dro"]["msb"] + 1))
            self.drsize = self.arguments.arg_l["dro"]["msb"] if(self.arguments.arg_l["dro"]["msb"] > self.drsize) else self.drsize
        self.irsize = HTD_INFO.tap_info.get_ir_size(self.agent)
        # -----------------------
        fields_l = HTD_INFO.tap_info.get_ir_fields(self.irname, self.agent)
        fields_l_uppercase = [x.upper() for x in fields_l]
        fields_l_lowercase = [x.lower() for x in fields_l]
        doc_missing_fields = ""
        for field in self.arguments.get_not_declared_arguments():
            if ((field not in fields_l) and (field not in fields_l_uppercase) and (field not in fields_l_lowercase) and (field not in ["dri", "dro"])):
                if (self.dummy_mode):
                    doc_missing_fields = doc_missing_fields + field + ";"
                else:
                    htdte_logger.error(("Illegal field-\"%s\" name used in action(%s) definition at %s.\nAvailable fields are : %s") % (
                                       field, self.__action_name__, self.arguments.get_argument_src(field), ",".join(str(fields_l).rsplit("\n", 1))))
        if (self.dummy_mode and doc_missing_fields != ""):
            self.documented = 0
            self.documented_details = (("Cant get TAP agent:ir fields - %s:%s->%s") % (
                self.arguments.get_argument("agent"), self.irname, doc_missing_fields))
            return
        # ------if read_modify_write enable the rtl node should exist--------------
        fields_l = HTD_INFO.tap_info.get_ir_fields(self.irname, self.arguments.get_argument("agent"))
        message = "Missing RTL nodes for fields:"
        for field in fields_l:
            if (not HTD_INFO.tap_info.rtl_node_exists(self.irname, self.arguments.get_argument("agent"), field)):
                if (field not in self.arguments.get_not_declared_arguments()):
                    self.implicit_rtl_nodes_exists = 0
                    self.implicit_rtl_details = message if (self.implicit_rtl_details == "") else ("%s:%s") % (
                        self.implicit_rtl_details, field)
                else:
                    self.explicit_rtl_nodes_exists = 0
                    self.explicit_rtl_details = message if (self.explicit_rtl_details == "") else ("%s:%s") % (
                        self.explicit_rtl_details, field)

        #---------------
        if (self.arguments.get_argument("read_modify_write") and htdPlayer.hplSignalMgr.is_interactive_mode() and not self.dummy_mode):
            for field in fields_l:
                if (field not in self.arguments.get_not_declared_arguments()):
                    if (
                            not HTD_INFO.tap_info.rtl_node_exists(self.irname, self.arguments.get_argument("agent"), field)):
                        htdte_logger.error((
                                           "Missing documented field-\"%s\"(action:\"%s\") rtl node , while read_modify_write mode enabled ") % (
                                           field, self.__action_name__))
                    if (not htdPlayer.hplSignalMgr.signal_exists(
                            HTD_INFO.tap_info.get_rtl_endpoint(self.irname, self.arguments.get_argument("agent"),
                                                               field))):
                        htdte_logger.error((
                                           "Rtl field integrity error-\"%s\"(action:\"%s\") rtl node , while read_modify_write mode enabled ") % (
                                           field, self.__action_name__))
        # ---------------------------------------
        if (self.arguments.get_argument("incremental_mode") and (not self.is_internal)):
            # --------------------------------------
            if(htd_history_mgr.history_has(self, [self.agent, self.irname])):
                entry = htd_history_mgr.history_get(self, [self.agent, self.irname])
                for f in list(entry.keys()):
                    if((f not in list(self.arguments.get_not_declared_arguments().keys()) or self.arguments.get_argument("read_type"))  # f is not given to write
                            and f not in htd_history_mgr.special_keys):
                        self.arguments.set_argument(f, htd_history_mgr.history_get(self, [self.agent, self.irname], f), "INCREMENTAL", False, HTD_VALUE_WRITE_ACCESS if(
                            not self.arguments.get_argument("read_type")) else HTD_VALUE_RW_ACCESS)
        # check field value size if it is fit the field size
        for field in list(self.arguments.get_not_declared_arguments().keys()):
            field_final_name = HTD_INFO.tap_info.insensitive_case_doc_field_name_match(self.irname, self.agent, field)
            msb = HTD_INFO.tap_info.get_field_msb(self.irname, self.agent, field_final_name)
            lsb = HTD_INFO.tap_info.get_field_lsb(self.irname, self.agent, field_final_name)
            fsize = msb - lsb + 1  # from tapper
            for arg in self.arguments.get_argument(field):
                if ((arg.lsb < 0) and (arg.msb < 0)):
                    max_val = int(pow(2, fsize) - 1)
                    if (arg.value > max_val):
                        htdte_logger.error((
                                           "field (%s) value is bigger than it's size: field size: %d bits, max val: 0x%x,  field value: 0x%x") % (
                                           field, fsize, max_val, arg.value))
                    if ((arg.read_value > max_val) and (arg.mask < 0)):
                        htdte_logger.error((
                                           "field (%s) read value is bigger than it's size: field size: %d bits, max val: 0x%x,  field read value: 0x%x") % (
                                           field, fsize, max_val, arg.read_value))
                    if (arg.write_value > max_val):
                        htdte_logger.error((
                                           "field (%s) write_value is bigger than it's size: field size: %d bits, max val: 0x%x,  field write value: 0x%x") % (
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
                    if ((arg.read_value > max_val) and (arg.mask < 0)):
                        htdte_logger.error((
                                           "field (%s) read value is bigger than it's subrange size: %d bits, max val: 0x%x,  field read value: 0x%x") % (
                                           field, arg.lsb, arg.msb, arg.lsb - arg.msb + 1, max_val, arg.read_value))
                    if (arg.write_value > max_val):
                        htdte_logger.error((
                                           "field (%s) write value is bigger than it's subrange size: %d bits, max val: 0x%x,  field write value: 0x%x") % (
                                           field, arg.lsb, arg.msb, arg.lsb - arg.msb + 1, max_val, arg.write_value))
       # ---Check dri/dro mode
        if (self.arguments.get_argument("dri", 1) >= 0):
            max_val = int(pow(2, self.drsize) - 1)
            if (self.arguments.get_argument("dri", 1) > max_val):
                htdte_logger.error((
                                   "The tap input raw data assignment (\"dri\":0x%x) exceed register size - %d bit..Pls. modify the data value or redefine register size: \"drsize\":<value>") % (
                                   self.arguments.get_argument("dri", 1), self.drsize))
            if (self.arguments.get_argument("mask_dro", 1) > max_val):
                htdte_logger.error((
                                   "The tap input raw data assignment (\"mask_dro\":0x%x) exceed register size - %d bit..Pls. modify the data value or redefine register size: \"drsize\":<value>") % (
                                   self.arguments.get_argument("mask_dro", 1), self.drsize))
        if (self.arguments.get_argument("dro", 1) >= 0):
            max_val = int(pow(2, self.drsize) - 1)
            if(self.arguments.get_argument("mask_dro", 1) < 0):
                self.mask_dro = max_val
            else:
                self.mask_dro = self.arguments.get_argument("mask_dro", 1)
            if (self.arguments.get_argument("dro", 1) > max_val):
                htdte_logger.error((
                                   "The tap input raw data assignment (\"dro\":0x%x) exceed register size - %d bit..Pls. modify the data value or redefine register size: \"drsize\":<value>") % (
                                   self.arguments.get_argument("dro", 1), self.drsize))

        # ----------------------------------------
        if (self.arguments.get_argument("check") and not self.dummy_mode):
            for field in fields_l:
                if (field in self.arguments.get_not_declared_arguments() or field.upper() in self.arguments.get_not_declared_arguments()):
                    if (not HTD_INFO.tap_info.rtl_node_exists(self.irname, self.arguments.get_argument("agent"), field)):
                        htdte_logger.error(("Missing documented %s->%s (action:\"%s\") rtl node , while check mode enabled ") % (
                            self.irname, field, self.__action_name__))
                    if (not htdPlayer.hplSignalMgr.signal_exists(HTD_INFO.tap_info.get_rtl_endpoint(self.irname, self.arguments.get_argument("agent"), field))):
                        htdte_logger.error(("Rtl field integrity error %s->%s (action:\"%s\") rtl node , while check mode enabled ") %
                                           (self.irname, field, self.__action_name__))

        # --------------------------------------
        # Check if HPL[tap_bfm_mode] is set
        if "tap_bfm_mode" in CFG["HPL"] and not self.arguments.is_argument_assigned("bfm_mode"):
            self.arguments.set_argument("bfm_mode", CFG["HPL"]["tap_bfm_mode"])

        if (self.arguments.get_argument("bfm_mode") == "injection" and (
                self.arguments.get_argument("read_type") and self.arguments.get_argument("check")) and not self.dummy_mode):
            for field in fields_l:
                if (field in self.arguments.get_not_declared_arguments()):
                    if (
                            not HTD_INFO.tap_info.rtl_node_exists(self.irname, self.arguments.get_argument("agent"), field)):
                        htdte_logger.error((
                                           "Missing documented %s:%s (action:\"%s\") rtl node , while bfm_mode=injection and read=1 ") % (
                                           self.irname, field, self.__action_name__))
                    if (not htdPlayer.hplSignalMgr.signal_exists(
                            HTD_INFO.tap_info.get_rtl_endpoint(self.irname, self.arguments.get_argument("agent"),
                                                               field))):
                        htdte_logger.error((
                                           "Rtl field integrity error %s:%s (action:\"%s\") rtl node , while bfm_mode=injection and read=1 ") % (
                                           self.irname, field, self.__action_name__))

        # -------------------------------------
        # DEPRECIATED - Please use updated pscand methodology using TE_cfg NoaOffsets table
        self.pscand_en = self.arguments.get_argument("pscand_en")

        # -------------------------------------

        if (self.arguments.get_argument("field_labels") or self.arguments.get_argument("field_labels_per_action")):
            self.field_labels_ena = 1
        elif CFG["HPL"].get("NEW_LABEL_SPEC") is 1:
            self.field_labels_ena = 0
        elif ("automatic_labels_ena" in list(CFG["HPL"].keys())):
            self.field_labels_ena = CFG["HPL"]["automatic_labels_ena"]
        elif ("automatic_field_labels_ena" in list(CFG["HPL"].keys())):
            self.field_labels_ena = CFG["HPL"]["automatic_field_labels_ena"]
        else:
            self.field_labels_ena = 0

        if (self.arguments.get_argument("man_field_labels")):
            self.man_field_labels = self.arguments.get_argument("man_field_labels").split(",")
        else:
            self.man_field_labels = None
    # -------------------------------
    #
    # -------------------------------

        if (self.arguments.get_argument("overshift_en") == 1):
            if (self.arguments.get_argument("overshift_marker") is None and self.tap_protocol == "taplink"):
                htdte_logger.error(("The tap protocol %s requires an overshift marker as a binary string") % (self.tap_protocol))

    def update_bitlistrange(self, lsb, msb, orig_list):
        res_l = orig_list
        for x in range(lsb, msb + 1):
            if (x not in res_l):
                res_l.append(x)
        return res_l

    # -------------------------------
    #
    # -------------------------------
    def is_duplicate_field_already_set(self, field, field_duplicate_tracker, dr):
        for dup_field in field_duplicate_tracker[field]:
            if dup_field in dr:
                return (1, dup_field)
        return (0, None)

    def get_field_default_val(self, field):
        field_default_val = 0
        if (self.arguments.get_argument("read_modify_write") and htdPlayer.hplSignalMgr.is_interactive_mode() and (not self.is_internal)):
            # --Real read modify write on "interactive simulation"
            field_default_val = htdPlayer.signal_peek(
                HTD_INFO.tap_info.get_rtl_endpoint(self.irname, self.agent, field), -1, -1)
        else:
            # --Take reset values if non interactive mode and read_modify_write=1
            field_default_val = int(HTD_INFO.tap_info.get_field_reset_value(self.irname, self.agent, field))

        return field_default_val

    def get_final_tap_data_register(self):
        accamulated_dr = {}
        write_dr = {}
        read_dr = {}
        fields_l = HTD_INFO.tap_info.get_ir_fields(self.irname, self.agent)
        doc_dr_size = HTD_INFO.tap_info.get_dr_total_length(self.irname, self.agent)
        ordered_fields_hash = {}
        field_duplicate_tracker = {}
        field_default_tracker = {}
        bit_field_tracker = [[] for i in range(doc_dr_size)]

        for field in fields_l:
            msb = HTD_INFO.tap_info.get_field_msb(self.irname, self.agent, field)
            lsb = HTD_INFO.tap_info.get_field_lsb(self.irname, self.agent, field)

            # Initialize the field_duplicate_tracker for this field
            field_duplicate_tracker[field] = []

            # Check to see if this field overlaps any other fields
            for bit in range(lsb, msb + 1):
                if len(bit_field_tracker[bit]) > 0:
                    # This bit has already been defined by another field.
                    # Add these fields to the field_duplicate_tracker
                    for dup_field in bit_field_tracker[bit]:
                        if dup_field not in field_duplicate_tracker[field]:
                            field_duplicate_tracker[field].append(dup_field)

                        if field not in field_duplicate_tracker[dup_field]:
                            field_duplicate_tracker[dup_field].append(field)

                # Append this field to the bit
                bit_field_tracker[bit].append(field)

            # Save the default value for this field
            field_default_tracker[field] = self.get_field_default_val(field)

            # Generate the ordered fields hash
            ordered_fields_hash[lsb] = field
        ordered_field_l = []
        for f in sorted(ordered_fields_hash):
            ordered_field_l.append(ordered_fields_hash[f])
        # -----------------------
        dri = -1
        dro = -1
        read_bitmap = []

        # if (self.arguments.get_argument("dri", 1) < 0 and self.arguments.get_argument("dro", 1) < 0):
        # --By field name
        # ----------------------------
        for field in ordered_field_l:
            lsb = HTD_INFO.tap_info.get_field_lsb(self.irname, self.agent, field)
            msb = HTD_INFO.tap_info.get_field_msb(self.irname, self.agent, field)
            field_default_val = field_default_tracker[field]

            # ------------------------------
            if (not self.arguments.get_argument("read_type")):
                # --In read mode no need to assign the rest bits (not strobbed)
                accamulated_dr[field] = field_default_val

                # --Override by user values------------------------------------
        # If read_type=1 and read_val<0 , the writen value is 0,read_val=write_val argument
        # if read_value given, the writent value is stay untached
        # 1. check if read values assigned - i,e both write and read needed to ve transacted
        read_and_write_transaction = 0
        for field in list(self.arguments.get_not_declared_arguments().keys()):
            for val in self.arguments.get_argument(field):
                if (val.read_value >= 0 and val.value >= 0):
                    read_and_write_transaction = 1
        # -------------------

        # DR assignment trackers
        write_dr = {}
        read_dr = {}

        # In read or read/write mode we only want to print the fields that we are specifically setting
        if self.arguments.get_argument("read_type"):
            self.arguments.set_argument("print_unset_defaults", 0)

        for field in self.arguments.get_not_declared_arguments():
            doc_field_name = HTD_INFO.tap_info.insensitive_case_doc_field_name_match(self.irname, self.agent, field)

            if (doc_field_name not in fields_l and not self.arguments.get_argument("read_type")):
                htdte_logger.error(("Trying to override not existent field name - \"%s\" while available are: %s") % (field, fields_l))

            lsb = HTD_INFO.tap_info.get_field_lsb(self.irname, self.agent, doc_field_name)
            msb = HTD_INFO.tap_info.get_field_msb(self.irname, self.agent, doc_field_name)
            # -------------------------------------------
            orig_field_name = field
            write_dr[doc_field_name] = field_default_tracker[doc_field_name]
            self.assigned_fields[doc_field_name] = orig_field_name

            # Check if a duplicate field is already set
            (duplicate_set, duplicate_field) = self.is_duplicate_field_already_set(doc_field_name, field_duplicate_tracker, write_dr)
            if (duplicate_set):
                htdte_logger.error("Cannot set field %s, because a field (%s) that overlaps it has already been set!" %
                                   (doc_field_name, duplicate_field))

            for val in self.arguments.get_argument(orig_field_name):
                if(val.write_value >= 0 and (not self.arguments.get_argument("read_type") or val.read_value < 0)):
                    val.access_type = HTD_VALUE_WRITE_ACCESS
                    val.value = val.write_value
                if((val.value >= 0 or val.write_value >= 0) and val.read_value >= 0 and self.arguments.get_argument("read_type") and val.access_type in [HTD_VALUE_DEFAULT_ACCESS, HTD_VALUE_RW_ACCESS]):
                    val.access_type = HTD_VALUE_RW_ACCESS
                    # update value only if value is not set
                    if (val.value < 0):
                        val.value = val.write_value

                if (val.lsb >= 0 and val.msb >= 0):
                    mask = int(pow(2, val.msb + 1) - 1)  # make all msb bits are 1's :Example msb=5 : 0111111,
                    unmask = int(pow(2, val.lsb) - 1)  # make all lsb bits are 1's ::Example lsb=3 : 0111
                    mask = mask ^ unmask  # Example lsb=3 and msb=5 : 0111111 xor 0111 = 0111000
                    reversed_mask = (pow(2, doc_dr_size + 1) - 1) ^ mask
                    if (not self.arguments.get_argument("strobe_disable") and self.arguments.get_argument("read_type") and val.access_type != HTD_VALUE_WRITE_ACCESS and (val.strobe or val.value >= 0 or val.read_value >= 0)):
                        #                    if (not self.arguments.get_argument("strobe_disable") and self.arguments.get_argument("read_type") and val.access_type != HTD_VALUE_WRITE_ACCESS and (val.strobe >= 0 or val.read_value >= 0)):
                        read_bitmap = self.update_bitlistrange(lsb + val.lsb, lsb + val.msb, read_bitmap)
                else:
                    #                    if (not self.arguments.get_argument("strobe_disable") and self.arguments.get_argument("read_type") and val.access_type != HTD_VALUE_WRITE_ACCESS and (val.strobe or val.value >= 0 or val.read_value >= 0)):
                    if (not self.arguments.get_argument("strobe_disable") and self.arguments.get_argument("read_type") and val.access_type != HTD_VALUE_WRITE_ACCESS and (val.strobe >= 0 or val.read_value >= 0)):
                        read_bitmap = self.update_bitlistrange(lsb, msb, read_bitmap)
                # --write_value-----------------
                if (val.value >= 0 and (not self.arguments.get_argument("read_type") or val.access_type in [HTD_VALUE_WRITE_ACCESS, HTD_VALUE_RW_ACCESS])):
                    if (val.lsb < 0 and val.msb < 0):
                        write_dr[doc_field_name] = val.value
                    else:
                        write_dr[doc_field_name] = (write_dr[doc_field_name] & reversed_mask) | (val.value << val.lsb)
                # --read_value
                if(self.arguments.get_argument("read_type") and (val.value >= 0 and val.access_type in [HTD_VALUE_READ_ACCESS, HTD_VALUE_DEFAULT_ACCESS] or val.read_value >= 0)):
                    # ---strobe value
                    read_val = val.read_value if (val.read_value >= 0) else (val.value)
                    if (val.access_type != HTD_VALUE_WRITE_ACCESS and not self.arguments.get_argument("strobe_disable")):
                        if (val.lsb < 0 and val.msb < 0):
                            read_dr[field] = read_val
                        else:
                            read_dr[field] = ((read_dr[field] if (field in read_dr) else 0) & reversed_mask) | (read_val << val.lsb)

        # Add default field values for fields not explicitly set
        if self.arguments.get_argument("print_unset_defaults"):
            for field in ordered_field_l:
                (duplicate_set, duplicate_field) = self.is_duplicate_field_already_set(field, field_duplicate_tracker, write_dr)
                if (field not in write_dr and not duplicate_set):
                    write_dr[field] = field_default_tracker[field]

        # entire of dr input or output given in parameters explicetly
        # else:???
        if (self.arguments.get_argument("dri", 1) >= 0 and self.arguments.get_argument("dro", 1) >= 0):
            self.drsize = self.arguments.arg_l["dri"]["msb"] + 1 if (
                self.arguments.arg_l["dri"]["msb"] >= 0) else self.drsize
            self.drsize = self.arguments.arg_l["dro"]["msb"] + 1 if (
                self.arguments.arg_l["dro"]["msb"] >= 0) else self.drsize
            dro = self.arguments.get_argument("dro")
            dri = self.arguments.get_argument("dri")

            if(not self.arguments.get_argument("strobe_disable")):
                read_bitmap = list(range(
                    self.arguments.arg_l["dro"]["lsb"] if (self.arguments.arg_l["dro"]["lsb"] >= 0) else 0,
                    self.arguments.arg_l["dro"]["msb"] + 1 if (
                        self.arguments.arg_l["dro"]["msb"] >= 0) else self.drsize))
        elif (self.arguments.get_argument("dro", 1) >= 0 and not self.arguments.get_argument("strobe_disable")):
            self.drsize = self.arguments.arg_l["dro"]["msb"] + 1 if (
                self.arguments.arg_l["dro"]["msb"] >= 0) else self.drsize
            dro = self.arguments.get_argument("dro")
            read_bitmap = list(range(
                self.arguments.arg_l["dro"]["lsb"] if (self.arguments.arg_l["dro"]["lsb"] >= 0) else 0,
                self.arguments.arg_l["dro"]["msb"] + 1 if (
                    self.arguments.arg_l["dro"]["msb"] >= 0) else self.drsize))
        elif(self.arguments.get_argument("dri", 1) >= 0):
            self.drsize = self.arguments.arg_l["dri"]["msb"] + 1 if (
                self.arguments.arg_l["dri"]["msb"] >= 0) else self.drsize
            dri = self.arguments.get_argument("dri")
        return (write_dr, read_dr, dri, dro, self.drsize, read_bitmap)
        # ----------------------

    #
    # ----------------------
    def transactor_label_assignment(self, labels, label_index, label_str):
        if (label_index in list(labels.keys())):
            labels[label_index] = ("%s__%s") % (label_str, labels[label_index])
        else:
            labels[label_index] = label_str
        # if NEW_LABEL_ENABLE_BIT:

    # --------------------------------
    #
    # --------------------------------
    def check_tap_ep(self, assigned_fields, dr_assignment, dri, waitcycles, refclock, timeout):
        if (dri < 0):
            sig_val_l = []
            sigs_l = []
            override_sigs_l = []
            error = 0
            for field in dr_assignment:
                if (field in assigned_fields and HTD_INFO.tap_info.rtl_node_exists(self.irname, self.agent, field)):
                    lsb = HTD_INFO.tap_info.get_field_lsb(self.irname, self.agent, field)
                    msb = HTD_INFO.tap_info.get_field_msb(self.irname, self.agent, field)

                    # check if this specific field needs to be verified. By
                    if (self.field_should_be_verified(assigned_fields[field])):
                        signal_path_override = 0
                        signal_path = ""
                        if ("signal_path_override" in list(CFG.keys())):
                            if (self.agent in list(CFG["signal_path_override"].keys())):
                                if ("reg" not in list(CFG["signal_path_override"][self.agent].keys()) or "field" not in list(CFG["signal_path_override"][self.agent].keys()) or "path" not in list(CFG["signal_path_override"][self.agent].keys())):
                                    error = 1
                                    break
                                elif (CFG["signal_path_override"][self.agent]["reg"] == self.irname and CFG["signal_path_override"][self.agent]["field"] == field and CFG["signal_path_override"][self.agent]["path"] != ""):
                                    signal_path = CFG["signal_path_override"][self.agent]["path"]
                                    signal_path_override = 1
                                else:
                                    signal_path = HTD_INFO.tap_info.get_rtl_endpoint(self.irname, self.agent, field)  
                            else:
                                signal_path = HTD_INFO.tap_info.get_rtl_endpoint(self.irname, self.agent, field)
                        else:
                            signal_path = HTD_INFO.tap_info.get_rtl_endpoint(self.irname, self.agent, field)                
                        (chunk_sig, chunk_val) = HTD_INFO.signal_info.normalize_to_32_bit_signals(signal_path,
                                                                                                  dr_assignment[field],
                                                                                                  msb - lsb + 1)
                        sigs_l.extend(chunk_sig)
                        sig_val_l.extend(chunk_val)
                        if (signal_path_override == 1):
                            override_sigs_l.extend(chunk_sig)
            if (error == 1):
                htdte_logger.error("Wrong <Var> definition for signal path override in TE_cfg file - agent: \"%s\": Missing "
                                   "\"reg\" or \"field\" or \"path\" =<value> attribute ...." % self.agent)
            selector = self.agent.lower() if (self.parallel == 0) else ""
            htdPlayer.hplSignalMgr.signalset_wait(htdPlayer.hplSignalMgr.signalset_pack(sigs_l, sig_val_l), waitcycles,
                                                  timeout, refclock, 1, selector, override_sigs_l)

    # ----------------------
    #
    # ----------------------
    def field_should_be_verified(self, field):
        field_arg_verify = 1
        field_arg = self.arguments.get_argument(field)
        for field_val in field_arg:
            field_arg_verify = field_val.verify_arg
        return field_arg_verify

    # ----------------------
    #
    # ----------------------
    def transactor_strobe_properties_assignment(self, properties, index, val):
        properties[index] = val

    # -----------------------
    #
    # ------------------------
    def TransactShiftIr(self, bin, size, bit0, labels):  # {5:Start_Ir,10:EndIr}
        labels_with_bit0_offset = {}
        for l in labels:
            labels_with_bit0_offset[l + bit0] = labels[l]
        htdPlayer.hpl_to_dut_interface.ShiftIr(bin, size, labels_with_bit0_offset)
        # -----------------------

    #
    # ------------------------
    def TransactShiftDr(self, bin_i, size, bit0, strobe_bit0, labels={}, masks={}, captures={}, strobes={}, pad_left=0,
                        pad_rigth=0):
        initial_strobe_bit0 = strobe_bit0

        labels_with_bit0_offset = {}
        for l in list(labels.keys()):
            labels_with_bit0_offset[l + bit0] = labels[l]
        if(self.arguments.get_argument("first_rdbit_label") != ""):
            labels_with_bit0_offset[bit0] = self.arguments.get_argument("first_rdbit_label")
        masks_with_bit0_offset = {}
        if strobe_bit0 < 0:
            strobe_bit0 = 0
        for l in list(masks.keys()):
            masks_with_bit0_offset[l + strobe_bit0] = masks[l]
        strobes_with_bit0_offset = {}
        for l in list(strobes.keys()):
            strobes_with_bit0_offset[l + strobe_bit0] = strobes[l]
        captures_with_bit0_offset = {}
        for l in list(captures.keys()):
            captures_with_bit0_offset[l + strobe_bit0] = captures[l]

        if (TAP.tap_activity_logger.enabled()):
            stim_value = util_int_to_binstr(bin_i, size)
            expected_value = 'X' * size
            expected_value_l = list(expected_value)
            for strobe_key, strobe_val in list(strobes_with_bit0_offset.items()):
                expected_value_l[int(strobe_key)] = strobe_val
            expected_value = "".join(expected_value_l)
            TAP.tap_activity_logger.write_data(self.get_action_name(), self.agent, labels, stim_value, expected_value)

        if (not self.noa_offset_mode_needed(initial_strobe_bit0) or ("DisableTapParallelOutput" in list(CFG["FlowGen"].keys()) and CFG["FlowGen"]["DisableTapParallelOutput"])):
            htdPlayer.hpl_to_dut_interface.ShiftDr(bin_i, size, labels_with_bit0_offset, masks_with_bit0_offset,
                                                   captures_with_bit0_offset, strobes_with_bit0_offset, pad_left, pad_rigth)
        else:
            # get the noa pins and offsets
            (noa_pins_l, noa_offsets_l) = self.get_noa_offset_pins_and_delay()

            # no NOA pins - write as is
            strobe_offset_l = []
            final_noa_l = []

            active_slices_list = self.get_slices_list("slices_index", use_default_if_no_cfg=0)
            for idx, value in enumerate(noa_offsets_l):
                if (idx in active_slices_list):
                    strobe_offset_l.append(initial_strobe_bit0 - int(noa_offsets_l[idx]))
                    final_noa_l.append(noa_pins_l[idx])

            htdPlayer.hpl_to_dut_interface.ShiftParallelDr(bin_i, size, labels_with_bit0_offset, masks_with_bit0_offset,
                                                           final_noa_l,
                                                           captures_with_bit0_offset, strobes_with_bit0_offset, strobe_offset_l)

    # -----------------------
    #
    # ------------------------
    def noa_offset_mode_needed(self, strobe_bit0=0):
        # not read or read in serial or it is non-strobed transaction
        if (self.parallel == 0 or strobe_bit0 < 0 or not self.arguments.get_argument("read_type")):
            return 0

        noa_offset_enabled = self.noa_offset_enabled()
        if (noa_offset_enabled):
            tap_agent_supports_noa = (self.agent in CFG["NoaOffsets"]["supported_taps"].split(','))
            return tap_agent_supports_noa
        return 0

    # -----------------------
    #
    # ------------------------
    def noa_offset_enabled(self):
        # on simulation disable noa_offsets if key was set
        if ("disable_pscand" in list(CFG["HPL"].keys()) and CFG["HPL"]["disable_pscand"] == 1):
            htdte_logger.inform("Pscand was disabled by setting 'disable_pscand' key. Will use scand instead")
            return 0
        if ("NoaOffsets" in list(CFG.keys()) and "enabled" in CFG["NoaOffsets"] and CFG["NoaOffsets"]["enabled"] == 1):
            return 1
        return 0

    # -----------------------
    #
    # ------------------------
    def get_pscan_type(self):
        # First return value is prefix used in CFG["NoaOffsets"] to lookup which pins and offsets
        # Second return value is name of entry in CFG["SliceInfo"], containing enabled/disbled pins
        # This allows selective disabling of certain pscan pins, such as core_disables from rules file

        # Needs to be expanded to detect other types of pscan grouped taps

        pscand_group_name = None
        cfg_list_name = None

        if "NoaOffsets" in list(CFG.keys()):
            if "pscand_group_lookup" in CFG["NoaOffsets"]:
                for pscand_group_mapping in CFG["NoaOffsets"]["pscand_group_lookup"].split(","):
                    tap_regex, pscand_group = pscand_group_mapping.split(":")

                    if re.match(tap_regex, self.agent):
                        pscand_group_name = pscand_group

            if "cfg_list_lookup" in CFG["NoaOffsets"]:
                for cfg_list_mapping in CFG["NoaOffsets"]["cfg_list_lookup"].split(","):
                    tap_regex, cfg_list = cfg_list_mapping.split(":")

                    if re.match(tap_regex, self.agent):
                        cfg_list_name = cfg_list

        if pscand_group_name is None or cfg_list_name is None:
            if self.agent.startswith("CORE"):
                if pscand_group_name is None:
                    pscand_group_name = "core"
                if cfg_list_name is None:
                    if ("SliceInfo" in CFG and "cores_index" in CFG["SliceInfo"]):
                        cfg_list_name = "cores_index"
                    else:
                        cfg_list_name = "slices_index"
            elif self.agent.startswith("CBO"):
                if pscand_group_name is None:
                    pscand_group_name = "cbo"
                if cfg_list_name is None:
                    cfg_list_name = "slices_index"
            elif self.agent.startswith("ICEBO_HIP"):
                if pscand_group_name is None:
                    pscand_group_name = "icebo"
                if cfg_list_name is None:
                    cfg_list_name = "icebos_index"
        
        return pscand_group_name, cfg_list_name

    #
    # ------------------------

    def get_noa_offset_pins_and_delay(self):

        pscand_group, _ = self.get_pscan_type()

        if self.arguments.get_argument("pscand_group_override"):
            pscand_group = self.arguments.get_argument("pscand_group_override")

        if pscand_group is None:
            htdte_logger.error("NOA offset pins and offsets for tap agent %s were not found" % (self.agent))

        noa_pins_value_l = CFG["NoaOffsets"][pscand_group + "_noa_pins"].split(',')
        offset_value_l = CFG["NoaOffsets"][pscand_group + "_offsets"].split(',')

        # Check if a specific offset is specified
        if "offset_lookup" in CFG["NoaOffsets"] and not self.arguments.get_argument("pscand_group_override"):
            for offset_mapping in CFG["NoaOffsets"]["offset_lookup"].split(","):
                tap_regex, offset_key = offset_mapping.split(":")

                if re.match(tap_regex, self.agent) and offset_key in CFG["NoaOffsets"]:
                    offset_value_l = CFG["NoaOffsets"][offset_key].split(',')

        return (noa_pins_value_l, offset_value_l)

    # -----------------------
    #
    # ------------------------
    def TransactGotoState(tap_state):
        htdPlayer.hpl_to_dut_interface.to_state(tap_state)
        # -----------------------------------------------------

    #
    # ------------------------------------------------------
    def low_level_tap_bfm_transactor(self, transactions, labels, mask, strobe, capture):
        self.counter = 0
        for t in transactions:
            if (len(t.comment)):
                htdPlayer.hpl_to_dut_interface.add_comment(t.comment)
            # --------------------
            if (t.state == "state"):
                htdPlayer.hpl_to_dut_interface.to_tap_state(t.tag)
            elif (t.state == "ir"):
                irlabels = {0: htdPlayer.get_indexed_label(("StartIr_%s_%s") % (self.agent, self.irname)),
                            HTD_INFO.tap_info.get_ir_size(self.agent) - 1: htdPlayer.get_indexed_label(("EndIr__%s__%s") % (self.agent, self.irname))} if(t.tag == "root" and self.automatic_labels_ena) else {}
                self.TransactShiftIr(t.sequence, t.sequence_size, t.bit0, irlabels if (t.main_tx) else {})
            elif (t.state == "dr"):
                # ----------------Label assignment ----------------epir,epdr
                if (t.bit0 < 0):
                    htdte_logger.error("Missing tap sequence \"bit0\" index...")
                if (t.tag == "epir"):
                    irlabels = irlabels = {0: ("StartIr__%s__%s") % (self.agent, self.irname), HTD_INFO.tap_info.get_ir_size(
                        self.agent) - 1: htdPlayer.get_indexed_label(("EndIr__%s__%s") % (self.agent, self.irname))}
                    self.TransactShiftDr(t.sequence, t.sequence_size, t.bit0, t.strobe_bit0, irlabels if (t.main_tx) else {}, {}, {}, {})
                elif (t.tag == "root" or t.tag == "epdr"):
                    drsize = HTD_INFO.tap_info.get_dr_total_length(self.irname, self.agent) - \
                        1 if(not self.arguments.get_argument("drsize")) else self.drsize
                    if (t.main_tx and self.automatic_labels_ena):
                        self.transactor_label_assignment(labels, 0, htdPlayer.get_indexed_label(
                            ("StartDr__%s__%s__%d") % (self.agent, self.irname, drsize)))
                    if (t.main_tx and self.automatic_labels_ena):
                        self.transactor_label_assignment(
                            labels, drsize - 1, htdPlayer.get_indexed_label(("EndDr__%s__%s") % (self.agent, self.irname)))
                    if (t.main_tx):
                        self.TransactShiftDr(t.sequence, t.sequence_size, t.bit0, t.strobe_bit0,
                                             labels, mask, capture, strobe, t.pad_left, t.pad_rigth)
                    else:
                        self.TransactShiftDr(t.sequence, t.sequence_size, t.bit0, t.strobe_bit0)
            elif (t.state == "tap_size"):
                htdPlayer.hpl_to_dut_interface.tap_instruction_size(t.tag)
            elif (t.state == "pscand"):
                htdPlayer.hpl_to_dut_interface.pscand(t.tag)
            else:
                htdte_logger.error("Unsupported transaction tag - \"%s\".Expected[\"epir\",\"epdr\",\"root\"]...")
            # ----Printing the rest between transaction actions
            for a in t.mid_transaction_queue:
                htdPlayer.hpl_to_dut_interface.send_action(a)

    # -----------------------------------------------------
    # gets pscand parameters
    # take into account the case where pscand pins and offset
    # are extracted from the CFG file
    # -----------------------------------------------------
    def get_pscand_params(self):
        # support the case where pscand_en and pscand_pins, pscan_offsets are not specified
        # self.pscand_en, self.pscand_pins, self.pscand_delay are DEPRECIATED
        # Please set these using the TE_cfg NoaOffsets (which is the below if block)

        final_pscand_en = (self.pscand_en or self.noa_offset_mode_needed())
        final_pscand_pins = self.pscand_pins.split(",")
        final_pscand_delay = [self.pscand_delay] * len(final_pscand_pins)

        # if pscand is enabled and no pscand pins - extract them from config
        if (final_pscand_en == 1 and (final_pscand_pins == "" or self.pscand_pins == "")):
            (noa_pins_l, noa_offsets_l) = self.get_noa_offset_pins_and_delay()
            final_pscand_delay = []
            final_pscand_pins = []

            _, cfg_list = self.get_pscan_type()
            if self.arguments.get_argument("cfg_list_override"):
                cfg_list = self.arguments.get_argument("cfg_list_override")
            active_slices_list = self.get_slices_list(cfg_list, use_default_if_no_cfg=0)

            # Make sure the length of the delay is the the same as the length of the pins list
            if (len(noa_offsets_l) == 1 and len(noa_pins_l) > 1):
                # Replicate the offset for as many pins as there are
                noa_offsets_l = [noa_offsets_l[0]] * len(noa_pins_l)

            # Make sure the length of the offsets is the same a length of the pins
            if (len(noa_offsets_l) != len(noa_pins_l)):
                htdte_logger.error("Noaoffsets list length is not the same as the length of the noa pins list. Please check your TE_cfg")

            for idx, value in enumerate(noa_pins_l):
                if (idx in active_slices_list):
                    final_pscand_pins.append(value)
                    final_pscand_delay.append(noa_offsets_l[idx])
        return (final_pscand_en, final_pscand_pins, final_pscand_delay)

    # -----------------------------------------------------
    # ,bfm mode support - inject
    # -----------------------------------------------------
    def send_cmd(self, read_mode):
        (dr_by_fields, dr_read_byfield, dri, dro, drsize, read_bitmap) = self.get_final_tap_data_register()
        for field in list(dr_by_fields.keys()):
            self.capture_register_assignment_by_field(field, dr_by_fields[field])
        # -----------------------------
        # if (not self.arguments.get_argument("read_type")):
        (drsequence, drsequence_length, dr_per_field) = HTD_INFO.tap_info.get_final_data_register_sequence(
            self.irname, self.agent, dr_by_fields, dri, dro, drsize)
        # else:
        #    (drsequence, drsequence_length, dr_per_field) = HTD_INFO.tap_info.get_final_data_register_sequence(self.irname, self.agent, dr_read_byfield, dri, dro, drsize)

        if (self.arguments.get_argument("bfm_mode") in ["normal", "express"]):
            if("tap_activity_in_scan_memory" in list(CFG["TE"].keys()) and CFG["TE"]["tap_activity_in_scan_memory"]):
                htdPlayer.start_scan_memory()
            # ----------------------
            if (htdPlayer.hpl_to_dut_interface.tap_command_low_level_mode_enabled()):
                # if (not self.arguments.get_argument("read_type")):
                transactions = htdPlayer.hpl_tap_api.get_tap_transactions(self.irname, self.agent, drsequence,
                                                                          drsequence_length, dr_by_fields,
                                                                          list(self.arguments.get_not_declared_arguments().keys()),
                                                                          self.parallel, read_mode, 0, 0, self.arguments.get_argument("dronly"))
                # else:
                #    transactions = htdPlayer.hpl_tap_api.get_tap_transactions(self.irname, self.agent, drsequence,
                #                                                              drsequence_length, dr_read_byfield,
                #                                                              self.arguments.get_not_declared_arguments().keys(),
                #                                                              self.parallel, read_mode)
            # htdPlayer.hpl_to_dut_interface.tap_parameters_instrumetal_print(self.irname,self.agent,self.parallel,dr_by_fields,self.arguments.get_not_declared_arguments())
            # ------------------------------
            mask = {}
            strobe = {}
            capture = {}
            labels = {}
            # ----------------Label assignment ----------------epir,epdr
            fields_l = HTD_INFO.tap_info.get_ir_fields(self.irname, self.agent)
            for field in self.arguments.get_not_declared_arguments():
                doc_field_name = HTD_INFO.tap_info.insensitive_case_doc_field_name_match(self.irname, self.agent, field)
                field_lsb = HTD_INFO.tap_info.get_field_lsb(self.irname, self.agent, doc_field_name)
                field_msb = HTD_INFO.tap_info.get_field_msb(self.irname, self.agent, doc_field_name)
                # ---------------------------------
                for v in self.arguments.get_argument(field):
                    if (htdPlayer.hpl_to_dut_interface.tap_command_low_level_mode_enabled()):
                        if (v.label != -1):
                            self.transactor_label_assignment(labels, (v.lsb if v.lsb >= 0 else 0) + field_lsb, v.label)
                        curr_index = 0
                        for i in range(field_lsb, field_msb + 1):
                            abs_lsb = v.lsb + field_lsb
                            abs_msb = v.msb + field_lsb
                            if (read_mode and i in read_bitmap):  # assign to strobe , the RTL check if value is matching expectation to be done by interface (interactive)
                                if (field in dr_read_byfield):
                                    self.transactor_strobe_properties_assignment(strobe, i, "X" if (dr_read_byfield[field] < 0) else (
                                        "H" if (dr_read_byfield[field] & pow(2, curr_index)) else "L"))
                                elif (((i >= abs_lsb and i <= abs_msb) or (abs_lsb < 0 or abs_msb < 0)) and v.strobe > 0):
                                    self.transactor_strobe_properties_assignment(strobe, i, "S")
                            if (((i >= abs_lsb and i <= abs_msb) or (abs_lsb < 0 or abs_msb < 0)) and v.mask > 0):
                                self.transactor_strobe_properties_assignment(mask, i, 1)
                            if (((i >= abs_lsb and i <= abs_msb) or (abs_lsb < 0 or abs_msb < 0)) and v.capture > 0):
                                self.transactor_strobe_properties_assignment(capture, i, 1)
                            curr_index = curr_index + 1
                    else:
                        # --High level tap instruction assignment (by field)---
                        if (v.mask > 0):
                            #mask[field] = 1
                            #ticket_26285
                            field_mask = field
                            if (v.lsb > -1 and v.msb > -1):
                                if (((v.msb - v.lsb) + 1) != ((field_msb - field_lsb) + 1)):
                                    if ((v.msb - v.lsb) > (field_msb - field_lsb)):
                                        if (v.lsb + (field_msb - field_lsb) > (field_msb - field_lsb)):
                                            field_mask = "%s[%s:%s]" % (field, v.lsb, field_msb - field_lsb)
                                        else:
                                            field_mask = "%s[%s:%s]" % (field, v.lsb, v.lsb + (field_msb - field_lsb))
                                    else:
                                        field_mask = "%s[%s:%s]" % (field, v.lsb, v.msb) 
                            mask[field_mask] = 1

                        if (v.capture > 0):
                            capture[field] = 1

                        if (v.label != -1):
                            #if(v.lsb>=0 or v.msb>=0): htdte_logger.error(("High level tap transactor forbids label  assignment by resolution under field boundaries.(action:%s) ")%(self.__action_name__))
                            index = field_lsb + (v.lsb if v.lsb >= 0 else 0)
                            if (index not in list(labels.keys())):
                                labels[index] = v.label
                            else:
                                if(labels[index] != v.label):
                                    labels[index] = ("%s_%s") % (labels[index], v.label)
            # -----Automatic per field labels---------------------------
            #self.field_labels_ena = 0
            if (self.field_labels_ena):
                for field in fields_l:
                    labels_str = field
                    if(not self.is_internal):
                        labels_str = ("%s_%s") % (self.arguments.get_argument("label_prefix"), labels_str) if(
                            self.arguments.get_argument("label_prefix") != "") else labels_str
                        if(self.arguments.get_argument("label_reglen_offset_format")):
                            labels_str = ("%s_%d_%d") % (labels_str[:80], HTD_INFO.tap_info.get_field_msb(
                                self.irname, self.agent, field) - HTD_INFO.tap_info.get_field_lsb(self.irname, self.agent, field) + 1, 0)
                    if(HTD_INFO.tap_info.get_field_lsb(self.irname, self.agent, field) not in list(labels.keys())):
                        self.transactor_label_assignment(labels, HTD_INFO.tap_info.get_field_lsb(self.irname, self.agent, field), ("%s") % (labels_str))
                        if(HTD_INFO.tap_info.get_field_lsb(self.irname, self.agent, field) == 0):
                            labels[0] = ("%s__%s__%s__%s") % (labels[0], self.agent, self.irname, self.drsize)
                        elif(HTD_INFO.tap_info.get_field_lsb(self.irname, self.agent, field) == (self.drsize - 1)):
                            labels[self.drsize - 1] = ("%s__%s__%s__%s") % (labels[self.drsize - 1], self.agent, self.irname, self.drsize)
            elif (self.man_field_labels is not None):
                for field in self.man_field_labels:
                    field = field.upper()
                    field_orig = field.upper()
                    if ":" in field_orig:
                        field, labels_str = field.split(":")
                    else:
                        labels_str = field

                    if (self.arguments.get_argument("dri") == -1) or not field.isdigit():
                        found = False
                        for item in fields_l:
                            if re.search(field, item) is not None:
                                found = True
                                if ":" in field_orig:
                                    field, labels_str = field_orig.split(":")
                                    field = item
                                else:
                                    labels_str = item

                                if (not self.is_internal):
                                    labels_str = ("%s_%s") % (self.arguments.get_argument("label_prefix"), labels_str) if(
                                        self.arguments.get_argument("label_prefix") != "") else labels_str
                                    if(self.arguments.get_argument("label_reglen_offset_format")):
                                        labels_str = ("%s_%d_%d") % (labels_str, HTD_INFO.tap_info.get_field_msb(self.irname, self.agent,
                                                                                                                 item) - HTD_INFO.tap_info.get_field_lsb(self.irname, self.agent, item) + 1, 0)
                                self.transactor_label_assignment(labels, HTD_INFO.tap_info.get_field_lsb(
                                    self.irname, self.agent, item), ("%s") % (labels_str))
                        if not found:
                            htdte_logger.error(("Field %s does not exist for this IR") % (field))
                    else:
                        labels_str = ("%s_%s") % (self.arguments.get_argument("label_prefix"), labels_str) if(
                            self.arguments.get_argument("label_prefix") != "") else labels_str
                        if (int(float(field)) >= self.arguments.get_argument("drsize")):
                            htdte_logger.error("Bit %s is out of range!" % (field))
                        self.transactor_label_assignment(labels, int(float(field)), ("%s") % (labels_str))
            # ----------------
            mask_str = ""
            if (self.arguments.get_argument("dro") >= 0):
                for i in range(0, len(drsequence)):
                    strobe_flag = True if(self.arguments.arg_l["dro"]["lsb"] < 0) else (
                        i >= self.arguments.arg_l["dro"]["lsb"] and i <= self.arguments.arg_l["dro"]["msb"])
                    #mask_str = bin(self.mask_dro)
                    mask_str = bin(self.mask_dro)[2:].zfill(len(drsequence))
                    mask_str = mask_str[::-1]
                    # if(mask_str[i] == "1"):
                    if(i < len(mask_str) and (mask_str[i] == "1")):
                        self.transactor_strobe_properties_assignment(strobe, i, ("X" if(not strobe_flag) else (
                            "H" if ((self.arguments.get_argument("dro") >> i) & 1) else "L")))
                    else:
                        self.transactor_strobe_properties_assignment(strobe, i, ("X"))
                if(self.arguments.get_argument("mask_dro") >= 0):
                    mask = mask_str
            # ----------------
            if (self.instr_interface_print_ena):
                htdPlayer.hpl_to_dut_interface.tap_parameters_instrumetal_print(self.irname, self.agent, self.parallel,
                                                                                dr_by_fields,
                                                                                self.arguments.get_not_declared_arguments(),
                                                                                labels, mask, strobe, capture, labels)

            # ---limiting labels to CFG["HPL"]["label_length_limit"] if given , if not to 90chars
            label_limit = 90 if("label_length_limit" not in list(CFG["HPL"].keys()) or CFG["HPL"][
                                "label_length_limit"] < 1) else CFG["HPL"]["label_length_limit"]
            for l in list(labels.keys()):
                labels[l] = labels[l][:label_limit].replace(".", "_")

            # ------------------
            if (htdPlayer.hpl_to_dut_interface.tap_command_low_level_mode_enabled()):
                self.low_level_tap_bfm_transactor(transactions, labels, mask, strobe, capture)
            else:
                read_expected_per_field_values = dr_read_byfield if (self.arguments.get_argument("read_type") or read_mode) else {}
                if not self.is_internal and CFG["HPL"].get("NEW_LABEL_SPEC") is 1:
                    for field in read_expected_per_field_values:

                        doc_field_name = HTD_INFO.tap_info.insensitive_case_doc_field_name_match(self.irname, self.agent, field)
                        field_lsb = HTD_INFO.tap_info.get_field_lsb(self.irname, self.agent, doc_field_name)
                        labels[field_lsb] = "ph%s__%s_%s_%s_strobe" % (self.get_curr_flow().phase_name, self.get_action_name().replace(" ", "_"), self.irname, field)
                        labels[field_lsb] = labels[field_lsb].replace('.', '_')

                # support the case where pscand_en and pscand_pins, pscan_offsets are not specified
                (final_pscand_en, final_pscand_pins, final_pscand_delay) = self.get_pscand_params()
                if (final_pscand_en == 1 and final_pscand_pins == ""):
                    htdte_logger.error("Can't perform pscand commands while pscand_pins are not defined")

                # Get any relevant patmods for this action
                final_patmods = list()

                if (dri < 0 and dro < 0):
                    # We should be using dr_by_fields and checking at field level for writes
                    patmod_in = 1 - int(self.arguments.get_argument("read_type"))
                    patmod_out = int(self.arguments.get_argument("read_type"))
                    for f in dr_by_fields:
                        # make sure this is actually a field we are manually assigning
                        if f not in self.assigned_fields:
                            continue

                        if dr_by_fields[f] < 0:
                            # If we aren't actually setting this field to anything, continue to next field
                            continue
                        
                        temp_patmods = self.get_patmods_for_register_field(f, patmod_in, patmod_out)
                        for pm in temp_patmods:
                            # Pacman does not handle mixed case fields very well, so need to restore
                            if not f.isupper() and not f.islower():
                                pm["reg_field"] = f
                                pm["field"] = f 
                            if pm not in final_patmods:
                                final_patmods.append(pm)

                    # We should be using dr_by_fields and checking at field level for reads
                    for f in read_expected_per_field_values:
                        # make sure this is actually a field we are manually assigning
                        if f not in self.assigned_fields:
                            continue

                        if read_expected_per_field_values[f] < 0:
                            # If we aren't actually setting this field to anything, continue to next field
                            continue
                        temp_patmods = self.get_patmods_for_register_field(f, 0, 1)
                        for pm in temp_patmods:
                            if pm not in final_patmods:
                                final_patmods.append(pm)
                else:
                    # Patmod support
                    # dri/dro
                    if dri >= 0:
                        final_patmods = final_patmods + self.get_patmods_for_register(1, 0)

                    elif dro >= 0:
                        final_patmods = final_patmods + self.get_patmods_for_register(0, 1)

                # Make sure there are no labels in the same range as the patmods for this field
                # If there are labels on the same field as a patmod SPF complains
                for patmod in final_patmods:
                    labels_to_remove = list()
                    if patmod["reg_field"] is not None and patmod["reg_field"] != "DR":
                        field = patmod["reg_field"]
                        field_msb = HTD_INFO.tap_info.get_field_msb(self.irname, self.agent, field)
                        field_lsb = HTD_INFO.tap_info.get_field_lsb(self.irname, self.agent, field)

                        # Loop over labels and remove labels that overlap
                        for label_index in labels:
                            if field_lsb <= label_index <= field_msb:
                                labels_to_remove.append(label_index)
                    elif patmod["bits"] is not None and patmod["bits"] != "":
                        # Use the bits
                        bit_str = patmod["bits"]
                        for msb_lsb in bit_str.split(","):
                            (msb, lsb) = msb_lsb.split(":")
                            msb = int(msb)
                            lsb = int(lsb)

                            # Loop over labels and remove labels that overlap
                            for label_index in labels:
                                if lsb <= label_index <= msb:
                                    labels_to_remove.append(label_index)

                    else:
                        self.error("Expecting matching patmod to have either field or bits (or both) defined")

                    # Have to do this in two steps as you can't change the size of a dict while you are looping over it
                    for label_index in labels_to_remove:
                        labels.pop(label_index)
                
                final_patmodgroups = set()
                for patmod in final_patmods:
                    for group in HTD_INFO.patmods.get_patmodgroups():
                        for member in group.get_members():
                            if member == patmod["name"]:
                                final_patmodgroups.add(group)

                htdPlayer.hpl_to_dut_interface.high_level_tap_bfm_transactor(self.irname, self.ircode, self.irsize,
                                                                             self.drsize, self.agent, dr_by_fields,
                                                                             read_expected_per_field_values, dri, dro,
                                                                             self.parallel, labels, mask, capture,
                                                                             read_bitmap, final_pscand_en, final_pscand_delay, final_pscand_pins,
                                                                             final_patmods, final_patmodgroups, self.arguments.get_argument("ir_tdi_align_label"), self.arguments.get_argument("field_labels_per_action"), self.arguments.get_argument("label_domain"), self.__action_name__,
                                                                             self.arguments.get_argument("shadow_agents"),
                                                                             self.arguments.get_argument("postfocus_delay"),
                                                                             self.arguments.get_argument("dronly"), self.arguments.get_argument("overshift_en"),
                                                                             self.arguments.get_argument("overshift_marker"),
                                                                             self.arguments.get_argument("dba_mode"))
            # ------------------------------------------------
            if("tap_activity_in_scan_memory" in list(CFG["TE"].keys()) and CFG["TE"]["tap_activity_in_scan_memory"]):
                htdPlayer.stop_scan_memory()
                htdPlayer.hpl_to_dut_interface.wait_clock_num(1, self.arguments.get_argument("refclock"))
            if(not self.arguments.get_argument("read_type") and (not read_mode)):
                # -------------Update history --------------------
                for f in list(dr_by_fields.keys()):
                    if ((f in self.arguments.get_not_declared_arguments() or
                         f.upper() in self.arguments.get_not_declared_arguments() or
                         f.lower() in self.arguments.get_not_declared_arguments()) and
                            not self.get_curr_flow().is_verification_mode()):
                        htd_history_mgr.history_capture(self, [self.agent, self.irname], f, dr_by_fields[f])
                # ----------Wait until verification------------
                if (not self.arguments.get_argument("read_type") and (not read_mode)):
                    if (self.arguments.get_argument("check")):
                        self.check_tap_ep(self.assigned_fields, dr_by_fields, dri,
                                          self.arguments.get_argument("waitcycles"),
                                          self.arguments.get_argument("refclock"),
                                          self.arguments.get_argument("maxtimeout"))
                    elif CFG["HPL"].get("ConservativeDelays") == 1:
                        htdPlayer.hpl_to_dut_interface.wait_clock_num(self.arguments.get_argument("waitcycles"), self.arguments.get_argument("refclock"))
        # ---------------------------------------------------------
        elif (self.arguments.get_argument("bfm_mode") == "injection"):
            if (not self.arguments.get_argument("read_type") or self.arguments.get_argument("check")):
                if (dri < 0 and dro < 0):
                    if (read_mode):
                        self.check_tap_ep(self.assigned_fields, dr_by_fields, dri,
                                          self.arguments.get_argument("waitcycles"),
                                          self.arguments.get_argument("refclock"),
                                          self.arguments.get_argument("maxtimeout"))
                    else:
                        for f in list(dr_by_fields.keys()):
                            if (f in list(self.arguments.get_not_declared_arguments().keys())):
                                lsb = HTD_INFO.tap_info.get_field_lsb(self.irname, self.agent, f)
                                msb = HTD_INFO.tap_info.get_field_msb(self.irname, self.agent, f)
                                if (not HTD_INFO.tap_info.rtl_node_exists(self.irname, self.agent, f)):
                                    htdte_logger.error((
                                                       "Can't set %s.%s.%s in injection mode due to missing RTL node documentation. Try to add missing RTL node in CFG[TAP_RTL_NODES_BACKDOOR][<tapagent_name>.<tap_cmd_name>][<field>]") % (
                                                       self.agent, self.irname, f))
                                (chunk_sig, chunk_val) = HTD_INFO.signal_info.normalize_to_32_bit_signals(
                                    HTD_INFO.tap_info.get_rtl_endpoint(self.irname, self.agent, f), dr_by_fields[f],
                                    msb - lsb + 1)
                                for i in range(0, len(chunk_sig)):
                                    htdPlayer.hplSignalMgr.signal_set(chunk_sig[i], -1, -1, chunk_val[i], ".+")
                                    # TODO Need to support parallel on/off mode - > currently only parallel - operate by "."
                                    #htdPlayer.hplSignalMgr.signal_poke( HTD_INFO.tap_info.get_rtl_endpoint(self.irname,self.agent,f),-1,-1,dr_by_fields[f],".+")
                elif (dri < 0):
                    if (read_mode):
                        self.check_tap_ep(self.assigned_fields, dr_by_fields, dri,
                                          self.arguments.get_argument("waitcycles"),
                                          self.arguments.get_argument("refclock"),
                                          self.arguments.get_argument("maxtimeout"))
                    else:
                        fields_l = HTD_INFO.tap_info.get_ir_fields(self.irname, self.agent)
                        for f in fields_l:
                            lsb = HTD_INFO.tap_info.get_field_lsb(self.irname, self.agent, field)
                            msb = HTD_INFO.tap_info.get_field_msb(self.irname, self.agent, field)
                            mask_hi = pow(2, msb) - 1
                            mask_lo = pow(2, lsb) - 1
                            mask = mask_hi ^ mask_lo
                            # TODO Need to support parallel on/off mode - > currently only parallel- operate by "."
                            (chunk_sig, chunk_val) = HTD_INFO.signal_info.normalize_to_32_bit_signals(
                                HTD_INFO.tap_info.get_rtl_endpoint(self.irname, self.agent, f), dri & mask,
                                msb - lsb + 1)
                            for i in range(0, len(chunk_sig)):
                                htdPlayer.hplSignalMgr.signal_poke(chunk_sig[i], -1, -1, chunk_val[i], ".+")
        else:
            htdte_logger.error("Illegal bfm mode received - \"%s\", expected [normal,express,injection]")
            # ------------------------------------------

    def get_patmods_for_register_field(self, field, patmod_in, patmod_out):
        """
        Wrapper around code for getting patmods for a specific register field
        :param field: The name of field to look for
        :param bool patmod_in:
        :param bool patmod_out:
        :return: list of patmods
        :rtype [htd_patmod_manager.HtdPatmod]
        """
        final_patmods = list()

        # Patmod support
        if self.patmod_en == 1 and HTD_INFO.patmods.global_patmods_enabled():
            # Get the patmods for this field for patmod_in
            all_field_patmods = list()

            # Check if this field is in the not declared args
            if field.upper() in self.arguments.get_not_declared_arguments():
                f = field.upper()
            elif field in self.arguments.get_not_declared_arguments():
                f = field
            else:
                return final_patmods

            # Get all argument containers for this field
            f_args = self.arguments.get_argument(f)

            # Make sure this is a list - get_argument will sometimes return a single argument container if there is
            # only 1 associated with this field.
            if not isinstance(f_args, list):
                f_args = [f_args]

            # Generate a complete list of patmod_vars to look for
            patmod_vars = self.patmod_vars

            # Loop over all argument containers found for this field
            for f_arg in f_args:

                # Update patmod_vars if specified for this argument_container
                if f_arg.patmod_var is not None:
                    patmod_vars.append(f_arg.patmod_var)

                # only continue on this argument container if patmod_en is 1
                if f_arg.patmod_en == 1:
                    # Get the msb/lsb specified in this argument container
                    msb = f_arg.msb if f_arg.msb is not None and f_arg.msb >= 0 else None
                    lsb = f_arg.lsb if f_arg.lsb is not None and f_arg.lsb >= 0 else None
                    found_patmods = HTD_INFO.patmods.get_patmods_for_register_field("tap", self.agent,
                                                                                    self.irname, field,
                                                                                    patmod_in, patmod_out,
                                                                                    self.get_action_name(),
                                                                                    patmod_vars, msb, lsb)

                    # # We should only ever find 1 patmod per MSB/LSB or field
                    # if len(found_patmods) > 1:
                    #     if msb is not None and lsb is not None:
                    #         htdte_logger.error("Found %d patmods for field[%d:%d] %s, expected 1 at the most" % (
                    #             len(found_patmods), field, msb, lsb))
                    #     else:
                    #         htdte_logger.error("Found %d patmods for field %s, expected 1 at the most" % (
                    #             len(found_patmods), field))

                    # Add this patmod to the list of all patmods found for this field. We can end up with more than
                    # 1 patmod on the field level if found separate patmod matches for various msb/lsb combos
                    if len(found_patmods) > 0:
                        for patmod in found_patmods:
                            # Make sure we haven't preivously found this patmod
                            if patmod not in all_field_patmods:
                                # Add the patmod to all found for this field
                                all_field_patmods.append(patmod)

            # Check if there were no patmods found
            if all_field_patmods is None or len(all_field_patmods) <= 0:
                # This returns an empty list
                return final_patmods

            # Add this patmod to the final patmods
            final_patmods = final_patmods + all_field_patmods

        # Return the final patmods
        return final_patmods

    def get_patmods_for_register(self, patmod_in, patmod_out):
        """
        Wrapper around code for getting patmods for a specific register
        :param bool patmod_in:
        :param bool patmod_out:
        :return: list of patmods
        :rtype [htd_patmod_manager.HtdPatmod]
        """
        final_patmods = list()
        bit_tracker = dict()

        if self.patmod_en == 1 and HTD_INFO.patmods.global_patmods_enabled():
            # Patmod support
            reg_patmods = HTD_INFO.patmods.get_patmods_for_register("tap", self.agent, self.irname,
                                                                    patmod_in, patmod_out, self.get_action_name(),
                                                                    self.patmod_vars)

            # Loop over reg_patmods
            for patmod in reg_patmods:
                msb_lsb = list()

                if patmod["field"] is None or patmod["field"] == "" or patmod["field"] == "DR":
                    bits = patmod["bits"]
                    msb_lsb = [(int(msb), int(lsb)) for (msb, lsb) in [i.split(":") for i in bits.split(",")]]
                else:
                    # Get the field msb and lsb for this patmod
                    msb = HTD_INFO.tap_info.get_field_msb(self.irname, self.agent, patmod["field"])
                    lsb = HTD_INFO.tap_info.get_field_lsb(self.irname, self.agent, patmod["field"])
                    msb_lsb.append((msb, lsb))

                # Detect if bits are being set by multiple patmads
                err_bits = list()
                for bit_pair in msb_lsb:
                    (msb, lsb) = bit_pair
                    for i in range(lsb, msb + 1):
                        if i not in bit_tracker:
                            bit_tracker[i] = patmod['name']
                        else:
                            err_bits.append(str(i))

                    if len(err_bits) > 0:
                        htdte_logger.error("Bits %s found in multiple patmods. Pleas use patmod_var action param to  "
                                           "specify which variables to use" % (", ".join(err_bits)))

                # Set the field to DR and specify the bits
                patmod["field"] = "DR"
                patmod["bits"] = ",".join("%d:%d" % (msb, lsb) for (msb, lsb) in msb_lsb)

                # Add this patmod to the final patmods
                final_patmods.append(patmod)

        return final_patmods

    #
    # -------------------------------
    def run(self):
        # FIXME - add actual action execution
        self.inform(("         Running %s::%s:%s:%d \n\n") % (
            htd_base_action.get_action_type(self),
            htd_base_action.get_action_name(self),
            htd_base_action.get_action_call_file(self),
            htd_base_action.get_action_call_lineno(self)))

        self.patmod_en = self.arguments.get_argument("patmod_en")
        self.patmod_vars = self.arguments.get_argument("patmod_vars")
        if type(self.patmod_vars) in [str, str]:
            self.patmod_vars = [self.patmod_vars]

        tckpin = "xxTCK" if ("TCKPin" not in CFG["HPL"]) else CFG["HPL"]["TCKPin"]

        if(self.arguments.get_argument("expandata") > 1):
            htdPlayer.tap_expandata(tckpin, self.arguments.get_argument("expandata"))
        if(not self.arguments.get_argument("compression")):
            htdPlayer.tap_compression_off()
        self.send_cmd(self.arguments.get_argument("read_type"))
        # Verify rtl node and wait until completion to be executed by player
        if(not self.arguments.get_argument("compression")):
            htdPlayer.tap_compression_on()
        if(self.arguments.get_argument("expandata") > 1):
            htdPlayer.tap_expandata(tckpin, 1)

    # ----------------------------
    def debug_readback(self):
        if (not self.arguments.get_argument("read_type")):
            self.inform(("         Running Debug ReadBack %s::%s:%s:%d \n\n") % (
                htd_base_action.get_action_type(self),
                htd_base_action.get_action_name(self),
                htd_base_action.get_action_call_file(self),
                htd_base_action.get_action_call_lineno(self)))

            self.send_cmd(1)

    def get_defined_label(self):
        label_name = "%s__%s__%s__0__%d__Phase%s" % (self.get_action_name(), self.agent, self.irname, self.drsize - 1,
                                                     self.get_curr_flow().phase_name if self.get_curr_flow().phase_name != "" else "None")
        return label_name

    def get_slices_list(self, cfg_list, use_default_if_no_cfg=1):
        if ("SliceInfo" in list(CFG.keys()) and cfg_list in list(CFG["SliceInfo"].keys())):
            results = CFG["SliceInfo"][cfg_list].split(',')
            results = [int(i) for i in results]
            return results

        if (use_default_if_no_cfg == 1):
            return util_get_slices_list()

        htdte_logger.error("failed to obtain the slices to use")
