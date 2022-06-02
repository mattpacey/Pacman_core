import socket
import sys
import re
import os
import time
import subprocess
from hpl_tap_engine_structs import *
from htd_utilities import *
from htd_collaterals import *
import random
# ---------------------------------
# class hpl_tap_engine_params(object):
#   def __init__(self,irname,agent,read_type):
#      self.irname=""
#      self.agent=""
#      self.read_type=0
#      self.dr={}  #dict["field"]=val or just
#      self.dri=-1
#      self.dro=-1
#      self.drsize=-1


class HplTapDfxApi(object):
    def __init__(self): pass
    # -------------------------------
    #
    # -------------------------------

    def get_tap_transactions(self, irname, agent, drsequence, sequence_length, dr_by_field, assigned_fields, parallel_mode=1, read_mode=False, pad_left=0, pad_rigth=0, dronly=0):
        res = []

        # --------TapLink only
        if(not HTD_INFO.tap_info.is_taplink_remote_tap(agent)):
            # ---Link ROOT ep, direct ir/dr
            res.append(hpl_tap_transactor_entry("ir", HTD_INFO.tap_info.get_ir_opcode_int(irname, agent), HTD_INFO.tap_info.get_ir_size(agent), "root", 0))
            res.append(hpl_tap_transactor_entry("state", 0, 0, "IDLE"))
            res.append(hpl_tap_transactor_entry("dr", drsequence, sequence_length, "root", 0))
            res.append(hpl_tap_transactor_entry("state", 0, 0, "IDLE"))
            res.append(hpl_tap_transactor_entry("state", 0, 0, "IDLE"))
        else:
            (taplink_ir_agent, taplink_ir_name, taplink_ir_fname) = HTD_INFO.tap_info.get_tap_link_PARIR(agent) if (parallel_mode and HTD_INFO.tap_info.has_tap_link_parallel_support(agent)) else HTD_INFO.tap_info.get_tap_link_IR(agent)
            taplink_ir = HTD_INFO.tap_info.get_ir_opcode_int(taplink_ir_name, taplink_ir_agent)
            taplink_ir_size = HTD_INFO.tap_info.get_ir_size(taplink_ir_agent)
            (taplink_dr, taplink_dr_size, taplink_by_field_dr) = HTD_INFO.tap_info.get_final_data_register_sequence(taplink_ir_name, taplink_ir_agent, {taplink_ir_fname: HTD_INFO.tap_info.get_ir_opcode_int(irname, agent)})
            (taplink_dr_cmd_agent, taplink_dr_cmd_name, taplink_dr_field_name) = HTD_INFO.tap_info.get_tap_link_PARDR(agent) if (parallel_mode and HTD_INFO.tap_info.has_tap_link_parallel_support(agent)) else HTD_INFO.tap_info.get_tap_link_DR(agent)
            taplink_dr_cmd = HTD_INFO.tap_info.get_ir_opcode_int(taplink_dr_cmd_name, taplink_dr_cmd_agent)

            if(not dronly):  # dronly used for optimization mode - if the IR of remote tap is not changes - back to back same agent , same IR access
                # ---Link ep
                res.append(hpl_tap_transactor_entry("ir", taplink_ir, taplink_ir_size, "epir", 0))
                res.append(hpl_tap_transactor_entry("state", 0, 0, "IDLE"))
                # -----DR - remote ep IR
                res.append(hpl_tap_transactor_entry("dr", taplink_dr, taplink_dr_size, "epir", HTD_INFO.tap_info.get_field_lsb(taplink_ir_name, taplink_ir_agent, taplink_ir_fname)))
                res.append(hpl_tap_transactor_entry("state", 0, 0, "IDLE"))
                # ----Ir - remote DR
                res.append(hpl_tap_transactor_entry("ir", taplink_dr_cmd, taplink_ir_size, "epdr", 0))
                res.append(hpl_tap_transactor_entry("state", 0, 0, "IDLE"))
            # ----DR - remote DR
            HTD_INFO.tap_info.change_ir_field_size(taplink_dr_cmd_name, taplink_dr_cmd_agent, taplink_dr_field_name, len(drsequence))  # the defaul field DR size is 1 bit , need to be reformatted to actual ep DR length
            bit0_pos = HTD_INFO.tap_info.get_field_lsb(taplink_dr_cmd_name, taplink_ir_agent, taplink_dr_field_name)
            (taplink_dr, taplink_dr_size, taplink_by_field_dr) = HTD_INFO.tap_info.get_final_data_register_sequence(taplink_dr_cmd_name, taplink_dr_cmd_agent, {taplink_dr_field_name: drsequence})
            res.append(hpl_tap_transactor_entry("dr", taplink_dr, taplink_dr_size, "epdr", bit0_pos, bit0_pos))
            res.append(hpl_tap_transactor_entry("state", 0, 0, "IDLE"))
            res.append(hpl_tap_transactor_entry("state", 0, 0, "IDLE"))
            # ---------
        return res
