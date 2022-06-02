from htd_basic_action import *
from htd_utilities import *
from htd_collaterals import *
from htd_player_top import *


class STPL(htd_base_action):
    def __init__(self, action_name, source_file, source_lineno, currentFlow, is_internal):
        htd_base_action.__init__(self, self.__class__.__name__, action_name, source_file, source_lineno, currentFlow,
                                 is_internal)
        self.arguments.set_argument("source", 1, "Specify which source for this action")
        self.ircode = -1
        self.irname = ""
        self.agent = ""
        self.parallel = 1
        self.drsize = -1
        self.irsize = -1
        self.stpl_mode = 0
        self.field_labels_ena = 0
        self.instr_interface_print_ena = 0
        self.gen_action_types = ["WAIT", "PCOMMENT", "PINFO", "PLABEL", "ITPP"]
        self.arguments.declare_arg("op", ("Gen action type.Supported types are: %s..") % (str(self.gen_action_types)), self.gen_action_types, "", 0)
        self.arguments.declare_arg("strvalue", "Used as a string parameter for PINFO,PLABEL,PCOMMENT", "string", "", 0)
        self.arguments.declare_arg("ir", "The TAP destintation CMD name or binary CMD code      ", "string_or_int", "",
                                   0)
        self.arguments.declare_arg("agent", "The TAP link destination agent name .", "string", "", 0)
        self.arguments.declare_arg("dri", "The TAP register entire DATA assignment (aligned to register length) ",
                                   "int", -1, 0)
        self.arguments.declare_arg("dro", "The expected TAP DATA register shiftout (aligned to register length)", "int",
                                   -1, 0)
        self.arguments.declare_arg("drsize", "Enforce user dr length (used in conjunction with dri/dro)  ", "int", -1,
                                   0)
        self.arguments.declare_arg("bfm_mode", "The bfm mode: express|injection|normal ",
                                   ["express", "injection", "normal"], "normal", 0)
        self.arguments.declare_arg("parallel_mode",
                                   "Used to dis/ena taplink parallel/specific taplink endpoint access  ", "bool", 1, 0)
        self.arguments.declare_arg("read_modify_write", "Read rtl and override user assignment ena/dis ", "bool", 0, 0)
        self.arguments.declare_arg("field_labels", "ena/dis instrumental per field label assignment ", "bool", 0, 0)
        self.arguments.declare_arg("incremental_mode", "History incremental register initilization ena/dis ", "bool", 0,
                                   0)
        self.arguments.declare_arg("dronly", "Prevent IR select on remote controller (if has been choosed previously)", "bool", 0, 0)

        self.arguments.enable_dual_read_write_mode()
    #----------------------

    def get_action_not_declared_argument_names(self):pass 
    #---------------------
    
    def verify_arguments(self):
        self.inform(("       Verifying %s::%s:%s:%d ....") % (htd_base_action.get_action_type(self),
                                                              htd_base_action.get_action_name(self),
                                                              htd_base_action.get_action_call_file(self),
                                                              htd_base_action.get_action_call_lineno(self)))

        HTD_INFO.verify_info_ui_existence(["tap_info", "signal_info"])
        # self.verify_obligatory_arguments()
        # -----------------------------------------
        if (isinstance(self.arguments.get_argument("ir"), int)):
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
        self.agent = self.arguments.get_argument("agent")
        self.parallel = self.arguments.get_argument("parallel_mode")

    def get_final_tap_data_register(self):
        accamulated_dr = {}
        write_dr = {}
        read_dr = {}
        fields_l = HTD_INFO.tap_info.get_ir_fields(self.irname, self.agent)
        doc_dr_size = HTD_INFO.tap_info.get_dr_total_length(self.irname, self.agent)
        ordered_fields_hash = {}
        for field in fields_l:
            msb = HTD_INFO.tap_info.get_field_msb(self.irname, self.agent, field)
            lsb = HTD_INFO.tap_info.get_field_lsb(self.irname, self.agent, field)
            ordered_fields_hash[lsb] = field
        ordered_field_l = []
        for f in sorted(ordered_fields_hash):
            ordered_field_l.append(ordered_fields_hash[f])
        # -----------------------
        dri = -1
        dro = -1
        read_bitmap = []
        if (self.arguments.get_argument("dri", 1) < 0 and self.arguments.get_argument("dro", 1) < 0):
            # --By field name
            # ----------------------------
            for field in ordered_field_l:
                lsb = HTD_INFO.tap_info.get_field_lsb(self.irname, self.agent, field)
                msb = HTD_INFO.tap_info.get_field_msb(self.irname, self.agent, field)

                field_default_val = 0
                if (self.arguments.get_argument(
                        "read_modify_write") and htdPlayer.hplSignalMgr.is_interactive_mode() and (
                        not self.is_internal)):
                    # --Real read modify write on "interactive simulation"
                    field_default_val = htdPlayer.signal_peek(
                        HTD_INFO.tap_info.get_rtl_endpoint(self.irname, self.agent, field), -1, -1)
                else:
                    # --Take reset values if non interactive mode and read_modify_write=1
                    field_default_val = int(HTD_INFO.tap_info.get_field_reset_value(self.irname, self.agent, field))
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
            write_dr = accamulated_dr if (
                read_and_write_transaction or (not self.arguments.get_argument("read_type"))) else {}
            read_dr = {}  # No initial read without user assignment ... accamulated_dr if (read_and_write_transaction or (self.arguments.get_argument("read_type"))) else {}
            for field in list(self.arguments.get_not_declared_arguments().keys()):
                if (field not in list(accamulated_dr.keys()) and not self.arguments.get_argument("read_type")):
                    htdte_logger.error(
                        ("Trying to override not existent field name - \"%s\" while available are: %s") % (
                            field, list(accamulated_dr.keys())))
                lsb = HTD_INFO.tap_info.get_field_lsb(self.irname, self.agent, field)
                msb = HTD_INFO.tap_info.get_field_msb(self.irname, self.agent, field)
                # -----------------------------------------------
                write_dr[field] = accamulated_dr[field] if (field in list(accamulated_dr.keys())) else 0
                for val in self.arguments.get_argument(field):
                    if (val.lsb >= 0 and val.msb >= 0):
                        mask = int(pow(2, val.msb + 1) - 1)  # make all msb bits are 1's :Example msb=5 : 0111111,
                        unmask = int(pow(2, val.lsb) - 1)  # make all lsb bits are 1's ::Example lsb=3 : 0111
                        mask = mask ^ unmask  # Example lsb=3 and msb=5 : 0111111 xor 0111 = 0111000
                        reversed_mask = (pow(2, doc_dr_size + 1) - 1) ^ mask
                       # if (self.arguments.get_argument("read_type") and val.access_type != HTD_VALUE_WRITE_ACCESS and (
                        # val.strobe or val.value >= 0 or val.read_value >= 0)):
                        #read_bitmap = self.update_bitlistrange(lsb + val.lsb, lsb + val.msb, read_bitmap)
                    # else:
                    #    if (self.arguments.get_argument("read_type") and val.access_type != HTD_VALUE_WRITE_ACCESS and (
                        # val.strobe or val.value >= 0 or val.read_value >= 0)):
                        #read_bitmap = self.update_bitlistrange(lsb, msb, read_bitmap)
                        # --write_value-----------------
                    if (val.value >= 0 and (not self.arguments.get_argument("read_type") or val.access_type in [HTD_VALUE_WRITE_ACCESS, HTD_VALUE_RW_ACCESS])):
                        if (val.lsb < 0 and val.msb < 0):
                            write_dr[field] = val.value
                        else:
                            write_dr[field] = (write_dr[field] & reversed_mask) | (val.value << val.lsb)
                    # --read_value
                    else:
                        # ---strobe value
                        read_val = val.read_value if (val.read_value >= 0) else (val.value)
                        if (val.access_type != HTD_VALUE_RW_ACCESS and val.access_type != HTD_VALUE_WRITE_ACCESS):
                            if (val.lsb < 0 and val.msb < 0):
                                read_dr[field] = read_val
                            else:
                                read_dr[field] = ((read_dr[field] if (
                                    field in list(read_dr.keys())) else 0) & reversed_mask) | (read_val << val.lsb)

        # entire of dr input or output given in parameters
        else:
            if (self.arguments.get_argument("dri", 1) >= 0 and self.arguments.get_argument("dro", 1) >= 0):
                self.drsize = self.arguments.arg_l["dri"]["msb"] + 1 if (
                    self.arguments.arg_l["dri"]["msb"] >= 0) else self.drsize
                self.drsize = self.arguments.arg_l["dro"]["msb"] + 1 if (
                    self.arguments.arg_l["dro"]["msb"] >= 0) else self.drsize
                dro = self.arguments.get_argument("dro")
                dri = self.arguments.get_argument("dri")
                read_bitmap = list(range(
                    self.arguments.arg_l["dro"]["lsb"] if (self.arguments.arg_l["dri"]["lsb"] >= 0) else 0,
                    self.arguments.arg_l["dro"]["msb"] + 1 if (
                        self.arguments.arg_l["dri"]["msb"] >= 0) else self.drsize))
            elif (self.arguments.get_argument("dro", 1) >= 0):
                self.drsize = self.arguments.arg_l["dro"]["msb"] + 1 if (
                    self.arguments.arg_l["dro"]["msb"] >= 0) else self.drsize
                dro = self.arguments.get_argument("dro")
                read_bitmap = list(range(
                    self.arguments.arg_l["dro"]["lsb"] if (self.arguments.arg_l["dro"]["lsb"] >= 0) else 0,
                    self.arguments.arg_l["dro"]["msb"] + 1 if (
                        self.arguments.arg_l["dro"]["msb"] >= 0) else self.drsize))
            else:
                self.drsize = self.arguments.arg_l["dri"]["msb"] + 1 if (
                    self.arguments.arg_l["dri"]["msb"] >= 0) else self.drsize
                dri = self.arguments.get_argument("dri")

        return (write_dr, read_dr, dri, dro, self.drsize, read_bitmap)

    def TransactShiftIr(self, bin, size, bit0, labels):  # {5:Start_Ir,10:EndIr}
        htdPlayer.hpl_to_dut_interface.ShiftIr(bin, size, labels)
    # ------------------------

    def TransactShiftDr(self, bin_i, size, bit0, strobe_bit0, labels={}, masks={}, captures={}, strobes={}, pad_left=0,
                        pad_rigth=0):
        htdPlayer.hpl_to_dut_interface.ShiftDr(bin_i, size, labels, masks, captures, strobe_bit0, pad_left, pad_rigth)

    def TransactGotoState(tap_state):
        htdPlayer.hpl_to_dut_interface.to_state(tap_state)
    #
    # ------------------------------------------------------

    def low_level_tap_bfm_transactor(self, transactions, labels, mask, strobe, capture):
        for t in transactions:
            if (isinstance(t, dict)):
                if(t["op"] == "WAIT"):
                    htdPlayer.wait_clock_num(t["waitcycles"], "tclk")
                elif(t["op"] == "PINFO"):
                    htdPlayer.hpl_to_dut_interface.set_pattern_info(t["strvalue"])
                elif(t["op"] == "PLABEL"):
                    htdPlayer.hpl_to_dut_interface.label(t["strvalue"])
                elif(t["op"] == "PCOMMENT"):
                    htdPlayer.hpl_to_dut_interface.add_comment(t["strvalue"])
                elif(t["op"] == "ITPP"):
                    htdPlayer.hpl_to_dut_interface.write_itpp_cmd(t["strvalue"])

            # --------------------
            else:
                if (len(t.comment)):
                    htdPlayer.hpl_to_dut_interface.add_comment(t.comment)
                if (t.state == "state"):
                    htdPlayer.hpl_to_dut_interface.to_tap_state(t.tag)
                elif (t.state == "ir"):
                    self.TransactShiftIr(t.sequence, t.sequence_size, t.bit0, labels if (t.main_tx) else {})
                elif (t.state == "dr"):
                    # ----------------Label assignment ----------------epir,epdr
                    if (t.bit0 < 0):
                        htdte_logger.error("Missing tap sequence \"bit0\" index...")
                    if (t.tag == "root" or t.tag == "epdr"):
                        if (t.main_tx):
                            strobe = {}
                            index_strobes = 0
                            t.strobes[::-1]
                            for s in t.strobes:
                                if(s != "X"):
                                    strobe[t.sequence_size - index_strobes - 1] = s
                                    index_strobes += 1
                                else:
                                    index_strobes += 1
                            self.TransactShiftDr(t.sequence, t.sequence_size, t.bit0, strobe, labels, mask, capture,
                                                 strobe, t.pad_left, t.pad_rigth)
                        else:
                            self.TransactShiftDr(t.sequence, t.sequence_size, t.bit0, t.strobe_bit0)
                elif (t.state == "label"):
                    htdPlayer.hpl_to_dut_interface.label(t.tag)
                elif (t.state == "tap_size"):
                    htdPlayer.hpl_to_dut_interface.tap_instruction_size(t.tag)
                elif (t.state == "pscand"):
                    htdPlayer.hpl_to_dut_interface.pscand(t.tag)
                else:
                    htdte_logger.error("Unsupported transaction tag - \"%s\".Expected[\"epir\",\"epdr\",\"root\"]...")
                # ----Printing the rest between transaction actions

    # -----------------------------------------------------
    # ,bfm mode support - inject
    # -----------------------------------------------------
    def run_stpl_mode(self):
        self.stpl_mode = self.arguments.get_argument("stpl_mode")
        self.run()

    def send_cmd(self, read_mode):
        if (self.arguments.get_argument("ir", 1) != ""):
            actionType = "TAP"
        else:
            actionType = "GEN"
        if(actionType == "TAP"):
            (dr_by_fields, dr_read_byfield, dri, dro, drsize, read_bitmap) = self.get_final_tap_data_register()
            if (not self.arguments.get_argument("read_type")):
                (drsequence, drsequence_length, dr_per_field) = HTD_INFO.tap_info.get_final_data_register_sequence(
                    self.irname, self.agent, dr_by_fields, dri, dro, drsize)
            else:
                (drsequence, drsequence_length, dr_per_field) = HTD_INFO.tap_info.get_final_data_register_sequence(
                    self.irname, self.agent, dr_read_byfield, dri, dro, drsize)
            if (self.arguments.get_argument("bfm_mode") in ["normal", "express"]):
                if (not self.arguments.get_argument("read_type")):
                    transactions = htdPlayer.hpl_tap_api.get_tap_transactions(self.irname, self.agent, drsequence,
                                                                              drsequence_length, dr_by_fields,
                                                                              list(self.arguments.get_not_declared_arguments().keys()),
                                                                              self.parallel, read_mode, self.stpl_mode, 0, self.arguments.get_argument("dronly"))
                else:
                    transactions = htdPlayer.hpl_tap_api.get_tap_transactions(self.irname, self.agent, drsequence,
                                                                              drsequence_length, dr_read_byfield,
                                                                              list(self.arguments.get_not_declared_arguments().keys()),
                                                                              self.parallel, read_mode, self.stpl_mode, 0, self.arguments.get_argument("dronly"))
            # htdPlayer.hpl_to_dut_interface.tap_parameters_instrumetal_print(self.irname,self.agent,self.parallel,dr_by_fields,self.arguments.get_not_declared_arguments())
            # ------------------------------
        else:
            if(self.get_action_argument("op") == "WAIT"):
                transactions = htdPlayer.hpl_tap_api.get_tap_transactions({"op": "WAIT", "waitcycles": self.get_action_argument("waitcycles")}, "", "", 0, {}, [], 0, 0, self.stpl_mode, self.arguments.get_argument("dronly"))
            elif(self.get_action_argument("op") == "ITPP"):
                transactions = htdPlayer.hpl_tap_api.get_tap_transactions({"op": "ITPP", "strvalue": self.get_action_argument("strvalue")}, "", "", 0, {}, [], 0, 0, self.stpl_mode, self.arguments.get_argument("dronly"))
            elif(self.get_action_argument("op") == "PLABEL"):
                transactions = htdPlayer.hpl_tap_api.get_tap_transactions({"op": "PLABEL", "strvalue": self.get_action_argument("strvalue")}, "", "", 0, {}, [], 0, 0, self.stpl_mode, self.arguments.get_argument("dronly"))
            elif(self.get_action_argument("op") == "PCOMMENT"):
                transactions = htdPlayer.hpl_tap_api.get_tap_transactions({"op": "PCOMMENT", "strvalue": self.get_action_argument("strvalue")}, "", "", 0, {}, [], 0, 0, self.stpl_mode, self.arguments.get_argument("dronly"))
        mask = {}
        strobe = {}
        capture = {}
        labels = {}
        if (htdPlayer.hpl_to_dut_interface.tap_command_low_level_mode_enabled()):
            self.low_level_tap_bfm_transactor(transactions, labels, mask, strobe, capture)

      # ------------------------------------------

    #
    # -------------------------------
    def run(self):
        # FIXME - add actual action execution
        self.inform(("         Running %s::%s:%s:%d \n\n") % (
            htd_base_action.get_action_type(self),
            htd_base_action.get_action_name(self),
            htd_base_action.get_action_call_file(self),
            htd_base_action.get_action_call_lineno(self)))

        self.send_cmd(self.arguments.get_argument("read_type"))
