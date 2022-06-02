import socket
import sys
import re
import os
import subprocess
import random
import signal
from htd_utilities import *
from htd_collaterals import *
from htd_unix_socket import *
from stat import *


# ------------------------------
class htd_tap_info(htd_info_server):

    def __init__(self, norun=0):
        htd_info_server.__init__(self, norun)
        self.tap_rtl_backdoor_validated = False
        self.tap_reg_backdoor_validated = False
        self.tap_reg_backdoor_mapping = {}
        self.tap_reg_backdoor_regsize = {}
        self.suppress_backdor = False
        self.ir_field_size_override = {}
    # --------------------------

    def change_ir_field_size(self, IR, agent, field, new_size):
        if(agent not in list(self.ir_field_size_override.keys())):
            self.ir_field_size_override[agent] = {}
        if(IR not in list(self.ir_field_size_override[agent].keys())):
            self.ir_field_size_override[agent][IR] = {}
        self.ir_field_size_override[agent][IR][field] = new_size
        # --Update backdoor resize-
        if(self.tap_reg_backdoor_exists(IR, agent)):
            self.tap_reg_backdoor_field_resize(IR, agent, field, new_size)
    # -------------------------------

    def verify_tap_cmd(self, agnt, cmd):
        htdte_logger.error(("This method should be overriden by base class- %s") % (self.__class__.__name__))

    def verify_tap_register_field(self, agnt, cmd, field):
        htdte_logger.error(("This method should be overriden by base class- %s") % (self.__class__.__name__))

    def get_dr_total_length(self, agnt, cmd):
        htdte_logger.error(("This method should be overriden by base class- %s") % (self.__class__.__name__))

    def get_ir_field_details(self, agnt, cmd):
        htdte_logger.error(("This method should be overriden by base class- %s") % (self.__class__.__name__))

    def insensitive_case_doc_field_name_match(self, irname, agent, field):
        doc_fields_l = HTD_INFO.tap_info.get_ir_fields(irname, agent)
        doc_field_name = field
        if(field not in doc_fields_l):
            matched_doc_fields = [x for x in list(doc_fields_l.keys()) if(x.upper() == field.upper())]
            if(len(matched_doc_fields) == 1):
                doc_field_name = matched_doc_fields[0]
            else:
                htdte_logger.error(("Illegal field-\"%s\" name used in tap access %s:%s.\nAvailable fields are : %s") % (
                    field, agent, irname, ",".join(str(doc_fields_l).rsplit("\n", 1))))
        return doc_field_name

    def normalize_field_name(self, IR, agent, field):
        fields_l = HTD_INFO.tap_info.get_ir_fields(IR, agent)
        for f in fields_l:
            if(f.upper() == field.upper()):
                return f
            if(f.lower() == field.lower()):
                return f
        htdte_logger.error((" Can't match field name - \"%s\" by %s->%s , Available fields are : %s") % (field, agent, IR, fields_l))
    # --------------------------------------------------------------------------
    # Return dr sequence binary string + per field binary assignment
    # -------------------------------------------------------------

    def get_final_data_register_sequence(self, irname, agent, dr_by_fields, dri=-1, dro=-1, drsize=-1):
        dr_per_field = {}
        dr_size = HTD_INFO.tap_info.get_dr_total_length(irname, agent)
        dr_lsb_delta = 0
        if (drsize > 0):
            dr_lsb_delta = (drsize - dr_size) if (drsize >= dr_size) else 0
            dr_size = drsize
            dr_per_field = {}
        # -------------------
        # if (dri < 0 and dro < 0):
        dr_sequence = ("0" * dr_size)
        dr_sequence_l = list(dr_sequence)
        for f in dr_by_fields:  # Build dr_sequence from indiviual field values
            doc_field_name = self.insensitive_case_doc_field_name_match(irname, agent, f)
            lsb = HTD_INFO.tap_info.get_field_lsb(irname, agent, doc_field_name)
            msb = HTD_INFO.tap_info.get_field_msb(irname, agent, doc_field_name)
            if (type(dr_by_fields[f]) in [int, int]):
                field_val = list(util_int_to_binstr(dr_by_fields[f] if dr_by_fields[f] >= 0 else 0, msb - lsb + 1))
            else:
                field_val = list(
                    util_int_to_binstr(int(dr_by_fields[f] if dr_by_fields[f] >= 0 else 0, 2), msb - lsb + 1))

            # Both dr_sequence and field_val are ordered lsb:msb, so the below insert has to use -msb and -lsb
            field_val = field_val[-(msb - lsb + 1):]  # Truncate field_val to msb:lsb length
            dr_sequence_l[lsb:msb + 1] = field_val[::-1]
        dr_sequence = "".join(dr_sequence_l[::-1])
        # --------------------
        if (dr_lsb_delta > 0):
            dr_sequence = ("%s%s") % (dr_sequence, ("0" * dr_lsb_delta))  # adding preceeding zeroes on right side
        if (dr_size < self.get_dr_total_length(irname, agent)):
            htdte_logger.error((
                               "Illegal user-defined data register size -%d: undershift from documented size -%d , while tap access by field.") % (
                               dr_size, self.get_dr_total_length(irname, agent)))
            # ----------------
        # elif (dri < 0):
        #    dr_sequence = ("0" * dr_size)
        if(dri >= 0):
            dr_sequence = util_int_to_binstr(dri, dr_size)
            # --Create per field partitioning , overshift bits from lsb are removed
            if (dr_size >= HTD_INFO.tap_info.get_dr_total_length(irname, agent)):
                overshift_less_sequence = dr_sequence[:-dr_lsb_delta]
                for field in self.get_ir_fields(irname, agent):
                    msb = HTD_INFO.tap_info.get_field_msb(irname, agent, field)
                    lsb = HTD_INFO.tap_info.get_field_lsb(irname, agent, field)
                    dr_per_field[field] = overshift_less_sequence[
                        len(overshift_less_sequence) - 1 - msb:len(overshift_less_sequence) - lsb]
        return (dr_sequence, len(dr_sequence), dr_per_field)

    # --------------------------------------------
    # TAP register override backdor
    # require definition in CFG["TAP_REG_BACKDOR"]:
    #   <Var key="<agent>.<cmd_name>" tap_reg_size=<reg_size> field_name1="<msb>:<lsb>" field_name2="<msb>:<lsb>" ...  field_nameN="<msb>:<lsb>"/>
    # -------------------------------------
    #
    # -------------------------------------------------
    def verify_tap_reg_backdoor(self):
        if (self.tap_reg_backdoor_validated):
            return
        if ("TAP_REG_BACKDOR" not in list(CFG.keys())):
            return
        if (self.suppress_backdor):
            return
        self.suppress_backdor = True
        for cmd in list(CFG["TAP_REG_BACKDOR"].keys()):
            if (len(cmd.split(".")) < 2):
                htdte_logger.error((
                                   "Illegal CFG[TAP_REG_BACKDOR] definition : key token should be define in format <tap_agent>.<tap_instruction> while found - %s") % (
                                   cmd))
            (tap_agent, tap_cmd) = cmd.split(".", 1)
            self.verify_tap_cmd(tap_agent, tap_cmd)
            curr_reg_details = self.get_ir_field_details(tap_cmd, tap_agent)
            self.tap_reg_backdoor_mapping[cmd] = {}
            if ("tap_reg_size" not in list(CFG["TAP_REG_BACKDOR"][cmd].keys())):
                htdte_logger.error((
                                   "Illegal CFG[TAP_REG_BACKDOR] definition : missing tap register dr size override attribute - <Var key=\"%s\" tap_reg_size=\"<new_size\"...") % (
                                   cmd))
            self.tap_reg_backdoor_regsize[cmd] = int(CFG["TAP_REG_BACKDOR"][cmd]["tap_reg_size"])
            for field in list(CFG["TAP_REG_BACKDOR"][cmd].keys()):
                if (field == "tap_reg_size"):
                    continue
                match = re.match(r"(\d+)\s*:\s*(\d+)", CFG["TAP_REG_BACKDOR"][cmd][field])
                if (not match):
                    htdte_logger.error((
                                       "Illegal CFG[\"TAP_REG_BACKDOR\"][%s][%s] format : expected  \"<msb>:<lsb>\" format , received - \"%s\".") % (
                                       cmd, field, CFG["TAP_REG_BACKDOR"][cmd][field]))
                if (int(match.groups()[0]) > int(match.groups()[1])):
                    self.tap_reg_backdoor_mapping[cmd][field] = {"msb": int(match.groups()[0]),
                                                                 "lsb": int(match.groups()[1])}
                else:
                    self.tap_reg_backdoor_mapping[cmd][field] = {"msb": int(match.groups()[1]),
                                                                 "lsb": int(match.groups()[0])}
                    # --Check if size is not exceed
            range_check_map = [0] * self.tap_reg_backdoor_regsize[cmd]
            for f in list(self.tap_reg_backdoor_mapping[cmd].keys()):
                if (self.tap_reg_backdoor_mapping[cmd][f]["msb"] >= len(range_check_map)
                        or self.tap_reg_backdoor_mapping[cmd][f]["lsb"] >= len(range_check_map)):
                    htdte_logger.error((
                                       "Illegal CFG[\"TAP_REG_BACKDOR\"][%s][%s] range: %s - exceed register size - %d.(Pls. review the field range or specify register size override") % (
                                       cmd, f, CFG["TAP_REG_BACKDOR"][cmd][f],
                                       self.tap_reg_backdoor_regsize[cmd]))
                for i in range(self.tap_reg_backdoor_mapping[cmd][f]["lsb"],
                               self.tap_reg_backdoor_mapping[cmd][f]["msb"] + 1):
                    if (range_check_map[i]):
                        htdte_logger.error((
                                           "Illegal CFG[\"TAP_REG_BACKDOR\"][%s][%s] range: %s - overlap with previously defined field on bit - %d.(Pls. review  fields bit range specification)") % (
                                           cmd, field, CFG["TAP_REG_BACKDOR"][cmd][field], i))
                    range_check_map[i] = 1
            # ------------------------
            for i in range(0, len(range_check_map)):
                if (not range_check_map[i]):
                    htdte_logger.error(
                        ("Illegal CFG[\"TAP_REG_BACKDOR\"][%s] override , missing field definition for bit-%d") % (
                            cmd, i))
            self.suppress_backdor = False
            self.tap_reg_backdoor_validated = True

    # -------------------------------------------
    def tap_reg_backdoor_update_from_xml(self, path):
        HTD_INFO.read_cfg_file(path)
        self.tap_reg_backdoor_validated = False
        self.verify_tap_reg_backdoor()

    def tap_reg_backdoor_entry_remove(self, ir, agent):
        cmd = ("%s.%s") % (agent, ir)
        if (cmd not in list(self.tap_reg_backdoor_mapping.keys())):
            return
        del(self.tap_reg_backdoor_mapping[cmd])
        if ("TAP_REG_BACKDOR" not in list(CFG.keys())):
            return
        if (cmd not in list(CFG["TAP_REG_BACKDOR"].keys())):
            return
    # -------------------------------------------

    def tap_reg_backdoor_exists(self, ir, agent):
        if (not self.tap_reg_backdoor_validated):
            self.verify_tap_reg_backdoor()
        # ---------------------------------
        cmd = ("%s.%s") % (agent, ir)
        if (cmd not in list(self.tap_reg_backdoor_mapping.keys())):
            return False
        return True
        # ------------------------------------------

    def get_tap_reg_backdoor_size(self, ir, agent):
        if (not self.tap_reg_backdoor_exists(ir, agent)):
            htdte_logger.error(("Trying getting not existent TAP register backdoor %s->%s") % (agent, ir))
        cmd = ("%s.%s") % (agent, ir)
        if (cmd not in list(self.tap_reg_backdoor_regsize.keys())):
            return self.get_dr_total_length(ir, agent)
        return self.tap_reg_backdoor_regsize[cmd]

    # -----------------------------------------
    def tap_reg_backdoor_get_field_msb(self, ir, agent, field):
        if (not self.tap_reg_backdoor_exists(ir, agent)):
            htdte_logger.error(("Trying getting not existent TAP register backdoor %s->%s") % (agent, ir))
        cmd = ("%s.%s") % (agent, ir)
        if cmd not in self.tap_reg_backdoor_mapping:
            htdte_logger.error(("Trying getting not existent TAP register backdoor field msb- %s") % (cmd))
        if field not in self.tap_reg_backdoor_mapping[cmd]:
            htdte_logger.error(("Trying getting not existent TAP register backdoor field msb- %s->%s") % (cmd, field))
        return self.tap_reg_backdoor_mapping[cmd][field]["msb"]

    # ---------------------------
    def tap_reg_backdoor_get_field_lsb(self, ir, agent, field):
        if (not self.tap_reg_backdoor_exists(ir, agent)):
            htdte_logger.error(("Trying getting not existent TAP register backdoor %s->%s") % (agent, ir))
        cmd = ("%s.%s") % (agent, ir)
        if cmd not in self.tap_reg_backdoor_mapping:
            htdte_logger.error(("Trying getting not existent TAP register backdoor field lsb- %s") % (cmd))
        if field not in self.tap_reg_backdoor_mapping[cmd]:
            htdte_logger.error(("Trying getting not existent TAP register backdoor field lsb- %s->%s") % (cmd, field))
        return self.tap_reg_backdoor_mapping[cmd][field]["lsb"]

    # ----------------------------------------
    def tap_reg_backdoor_get_field_details(self, ir, agent):
        if (not self.tap_reg_backdoor_exists(ir, agent)):
            htdte_logger.error(("Trying getting not existent TAP register backdoor %s->%s") % (agent, ir))
        cmd = ("%s.%s") % (agent, ir)
        if (cmd not in list(self.tap_reg_backdoor_mapping.keys())):
            htdte_logger.error(
                ("Trying getting not existent TAP register backdoor fields details for cmd - %s") % (cmd))
        return self.tap_reg_backdoor_mapping[cmd]

    # -----------------------------------------------
    def tap_reg_backdoor_get_field_reset_value(self, ir, agent, field):
        if (not self.tap_reg_backdoor_exists(ir, agent)):
            htdte_logger.error(("Trying getting not existent TAP register backdoor %s->%s") % (agent, ir))
        return 0
    # -------------------------------

    def tap_reg_backdoor_field_resize(self, ir, agent, field, new_size):
        if (not self.tap_reg_backdoor_exists(ir, agent)):
            htdte_logger.error(("Trying resize not existent TAP register backdoor %s->%s") % (agent, ir))
        cmd = ("%s.%s") % (agent, ir)
        if (field not in list(self.tap_reg_backdoor_mapping[cmd].keys())):
            htdte_logger.error(("Trying resize not existent TAP register backdoor field  %s->%s") % (cmd, field))
        delta_size = new_size - self.tap_reg_backdoor_mapping[cmd][field]["msb"] + self.tap_reg_backdoor_mapping[cmd][field]["lsb"] - 1
        change_index = self.tap_reg_backdoor_mapping[cmd][field]["msb"]
        self.tap_reg_backdoor_mapping[cmd][field]["msb"] = self.tap_reg_backdoor_mapping[cmd][field]["lsb"] + new_size - 1
        self.tap_reg_backdoor_regsize[cmd] = self.tap_reg_backdoor_regsize[cmd] + delta_size
        for f in list(self.tap_reg_backdoor_get_field_details(ir, agent).keys()):
            if(self.tap_reg_backdoor_mapping[cmd][f]["lsb"] > change_index):
                self.tap_reg_backdoor_mapping[cmd][f]["lsb"] = self.tap_reg_backdoor_mapping[cmd][f]["lsb"] + delta_size
                self.tap_reg_backdoor_mapping[cmd][f]["msb"] = self.tap_reg_backdoor_mapping[cmd][f]["msb"] + delta_size

    # ---------------------------------------------------------------------
    # TAP RTL nodes info backdoor override in CFG[TAP_RTL_NODES_BACKDOOR]
    #    <Var key="<agent>.<cmd_name>"  field_name1="rtlnode" field_name2="rtlnode" ...  field_nameN="rtlnode"/>
    #
    #
    # ---------------------------------------------
    def rtl_node_backdoor_validate(self):
        if (self.tap_rtl_backdoor_validated):
            return
        if ("TAP_RTL_NODES_BACKDOOR" not in list(CFG.keys())):
            return
        for cmd in list(CFG["TAP_RTL_NODES_BACKDOOR"].keys()):
            if (len(cmd.split(".")) < 2):
                htdte_logger.error((
                                   "Illegal CFG[TAP_RTL_NODES_BACKDOOR] definition : key token should be define in format <tap_agent>.<tap_instruction> while found - %s") % (
                                   cmd))
            (tap_agent, tap_cmd) = cmd.split(".", 1)
            self.verify_tap_cmd(tap_agent, tap_cmd)
            for field in list(CFG["TAP_RTL_NODES_BACKDOOR"][cmd].keys()):
                self.verify_tap_register_field(tap_agent, tap_cmd, field)
        self.tap_rtl_backdoor_validated = True

    # ---------------------------------------------
    def rtl_node_backdoor_exists(self, agent, ir, field):
        if ("TAP_RTL_NODES_BACKDOOR" not in list(CFG.keys())):
            return False
        self.rtl_node_backdoor_validate()
        cmd = ("%s.%s") % (agent, ir)
        if (cmd not in list(CFG["TAP_RTL_NODES_BACKDOOR"].keys())):
            return False
        if (field not in list(CFG["TAP_RTL_NODES_BACKDOOR"][cmd].keys())):
            return False
        return True

    def get_rtl_node_backdoor(self, agent, ir, field):
        cmd = ("%s.%s") % (agent, ir)
        return CFG["TAP_RTL_NODES_BACKDOOR"][cmd][field]

    def get_real_agent(self, agent, IR):
        return agent
