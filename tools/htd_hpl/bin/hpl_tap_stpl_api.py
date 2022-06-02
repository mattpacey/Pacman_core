import socket
import sys
import re
import os
import subprocess
from htd_utilities import *
from htd_collaterals import *
from hpl_tap_engine_structs import *
from htd_basic_action import *

import subprocess
import time

# ---------------------------------


class HplTapStplApi(object):
    def __init__(self):
        self.spf_transact_counter = 0
        self.spf_seq_file = ""
        self.prev_seq_file = ""
        self.actual_itpp_seq_file = ""
        self.prev_itpp_seq_file = ""
        self.spf_sequencer_fh = ""
        self.context = ""
        self.context_index = ""
        spf_filesIndir = [f for f in os.listdir(os.environ.get('PWD')) if (os.path.isfile(("%s/%s") % (os.environ.get('PWD'), f)) and re.search(r"stpl_seq_transaction_\d+.seq", f))]
        for f in spf_filesIndir:
            os.remove(f)
        # ---------------------------------------------
        # ---------------------------------------------

    def get_final_data_register(self, irname, agent, fields_in):
        dr_size = HTD_INFO.tap_info.get_dr_total_length(irname, agent)
        dr_sequence = ("0" * dr_size)
        for f in fields_in:
            lsb = HTD_INFO.tap_info.get_field_lsb(irname, agent, f)
            msb = HTD_INFO.tap_info.get_field_msb(irname, agent, f)
            dr_sequence = dr_sequence[:-msb - 1] + int_to_binstr(fields_in[f].value, msb - lsb + 1) + dr_sequence[-lsb:]
        return (dr_sequence, len(dr_sequence))
        # ---------------------------------------------
        # ---------------------------------------------

    def parse_instrumental_comment(self, line, active_agent):
        active_agents_l = {}  # keep length of sequence per agent in network chain
        active_agent_index = 0  # store an active agent in all network chain
        active_agent_index = []
        current_bit_index = 0
        if(re.search(r"rem:\s+", line)):
            instrumental_comment_line = line.replace("rem: ", "")
            if (re.match(r"IR_REGISTERS:\s*", instrumental_comment_line)):
                instrumental_comment_line_clean = instrumental_comment_line.replace("IR_REGISTERS:", "")
            elif(re.match(r"DR_SHIFT:\s*", instrumental_comment_line)):
                instrumental_comment_line_clean = instrumental_comment_line.replace("DR_REGISTERS:", "")
            agents_str_l = instrumental_comment_line_clean.split(" + ")
            print(agents_str_l)
            for agent_str in agents_str_l:
                agent_token_match = re.search(r"\s*([A-z0-9_]+)\s*=>\s*([A-z0-9_]+)\s*\[(\d+)\]", agent_str)
                if(agent_token_match):
                    current_agent = agent_token_match.groups()[0]
                    current_agent_seq_length = int(agent_token_match.groups()[2])
                    if(current_agent == active_agent and (not current_agent_instruction == "BYPASS")):
                        return (current_bit_index - 1, current_bit_index - 1, 1)
                    else:
                        current_bit_index += current_agent_seq_length
                else:
                    htdte_logger.error((r"Not expected Instrumental line format : %s\n Expected: rem:\s+([A-z0-9_]+)\s*=>\s*([A-z0-9_]+)\s*\[(\d+)\]") % (agent_str))
            return (0, 0, 0)
        else:
            htdte_logger.error((r"Not expected Instrumental line format : %s\n Expected: rem:\s+....") % (line))

    def write_context(self, IR, dr_by_fields, assigned_fields):
        if (self.context != "empty" and IR != "NOA_CONFIG"):
            self.spf_sequencer_fh.write(("set CONTEXT%s = %s;\n") % (self.context_index, self.context))
        if (IR == "NOA_CONFIG"):
            context = list(self.context)
            value = ""
            if("cbo_tdo_on_noa" in assigned_fields):
                value = value + str(dr_by_fields["cbo_tdo_on_noa"])
            if("minitap_tdo_on_noa" in assigned_fields):
                value = value + str(dr_by_fields["minitap_tdo_on_noa"])
            if("fivr_on_noa" in assigned_fields):
                value = value + str(dr_by_fields["fivr_on_noa"])
            value = hex(int(value, 2))
            context[len(context) - 13] = value.replace("0x", "")
            self.context = ''.join(context)
            self.spf_sequencer_fh.write(("set CONTEXT%s = %s;\n") % (self.context_index, self.context))

    def get_context(self, ir, dr_by_fields, assigned_fields):
        self.context = "empty"
        if (self.spf_transact_counter > 0):
            for line in open(("%s") % (self.prev_itpp_seq_file), 'r').readlines():
                if(re.search(r"^#\s*CONTEXT(\[\d+:\d+])\s*=\s*(\'[dhb]\w+)", line)):
                    match = re.search(r"^#\s*CONTEXT(\[\d+:\d+])\s*=\s*(\'[dhb]\w+)\s*", line)
                    self.context_index = match.groups()[0]
                    self.context = match.groups()[1]
        htdte_logger.inform('Done Reading ITPP for context')
        self.write_context(ir, dr_by_fields, assigned_fields)
        # ---------------------------------------------
        # ---------------------------------------------

    def get_tap_transactions(self, irname, agent, drsequence, sequence_length, dr_by_fields, assigned_fields, parallel=0, read_mode=False, stpl_mode=0):
        result_transactor_l = []
        self.spf_seq_file = ("stpl_seq_transaction_%d.seq.stpl") % (self.spf_transact_counter)
        self.prev_seq_file = ("stpl_seq_transaction_%d.seq.stpl") % (self.spf_transact_counter - 1)
        self.actual_itpp_seq_file = ("stpl_seq_transaction_%d.seq.itpp") % (self.spf_transact_counter)
        self.prev_itpp_seq_file = ("stpl_seq_transaction_%d.seq.itpp") % (self.spf_transact_counter - 1)
        self.spf_sequencer_fh = open(self.spf_seq_file, "a", 1)
        IR = irname
        if(not stpl_mode):
            if(not isinstance(IR, dict)):
                match = re.match(r"(\w+)_(\w+)", IR)
                if(match):
                    clustername = match.groups()[0].lower()
                    irname = match.groups()[1].lower()
                else:
                    htdte_logger.error(("Expected format: <AGENT>_<IRNAME>', received - \"%s\"") % (IR))

        # self.get_context(IR,dr_by_fields,assigned_fields)

        # ----------Write Stpl file------------------
                dr_length = HTD_INFO.tap_info.get_dr_total_length(IR, agent)
                if(IR in ["LR_FIVRCOREFCM", "CORE_TAPSTATUS", "CBO_PLLCORESTAT", "CBO_TAPSTATUS"]):
                    self.spf_sequencer_fh.write("context;\n")
                    self.spf_sequencer_fh.write("pass itpp \"#pscand_nextdr = cha\"\n")
                if(len(list(dr_by_fields.keys())) < 1):
                    full_dr_name = IR.replace("_", ".")
                    msb = dr_length - 1
                    self.spf_sequencer_fh.write(("label %s\n") % (IR.lower()))
                    if (read_mode):
                        self.spf_sequencer_fh.write(("compare %s[%s:0] = 'h%s ;\n") % (full_dr_name, msb, drsequence))
                    else:
                        self.spf_sequencer_fh.write(("set %s[%s:0] = 'h%s ;\n") % (full_dr_name, msb, drsequence))
                else:
                    self.spf_sequencer_fh.write(("label %s\n") % (IR.lower()))
                    for key in assigned_fields:
                        if(key not in ["dri", "dro", "fivr_on_noa", "minitap_tdo_on_noa", "cbo_tdo_on_noa"] and key in dr_by_fields):
                            # -------------------------------
                            lsb = HTD_INFO.tap_info.get_field_lsb(IR, agent, key)
                            msb = HTD_INFO.tap_info.get_field_msb(IR, agent, key)
                            field_length = msb - lsb + 1

                # Field info
                            field_lsb = 0
                            field_msb = msb - lsb

                # Field value
                            dr_field_value = ("0x%x") % (dr_by_fields[key])
                            match = re.match(r"0[xb](\w+)", dr_field_value)
                            if(match):
                                dr_field2print = match.groups()[0].lower()
                            else:
                                htdte_logger.error((r"Expected format: 0[xb](\w+)', received - \"%s\"") % (IR))

                # If field lenght is 1 then do not use indexation
                            if (field_length == 1):
                                # ------------
                                # Preparing field_name
                                full_field_name = "%s.%s.%s" % (clustername, irname, key)  # Full Field Name
                            else:
                                # ------------
                                # Preparing field_name

                                full_field_name = "%s.%s.%s[%s:%s]" % (clustername, irname, key, field_msb, field_lsb)  # Full Field Name
                            if (read_mode):
                                if(key == "triggers.ext_func_triggers"):
                                    self.spf_sequencer_fh.write(('compare %-100s = %s\'h%s;\n') % (full_field_name.replace("[23:0]", "[8]"), 1, "1"))

                                else:
                                    self.spf_sequencer_fh.write(('compare %-100s = %s\'h%s;\n') % (full_field_name, field_length, dr_field2print))
                            else:
                                self.spf_sequencer_fh.write(('set %-100s = %s\'h%s;\n') % (full_field_name, field_length, dr_field2print))
        # ------------------------
                self.spf_sequencer_fh.write("flush;\n")
                self.spf_sequencer_fh.write("context;\n")
                self.spf_sequencer_fh.close()
                htdte_logger.inform('Done Writing STPL')
            else:
                if(IR["op"] == "WAIT"):
                    self.spf_sequencer_fh.write(('cycle %s;\n') % (IR['waitcycles']))
                elif(IR["op"] == "ITPP"):
                    self.spf_sequencer_fh.write(('pass itpp "pass itpp %s"\n') % (IR['strvalue']))
                elif(IR["op"] == "PLABEL"):
                    self.spf_sequencer_fh.write(('label %s\n flush \n') % (IR['strvalue']))
                elif(IR["op"] == "PCOMMENT"):
                    self.spf_sequencer_fh.write(('#%s \n') % (IR['strvalue']))
        if(stpl_mode):
            command_line = ("%s/tools/convert_to_itpp.pl -gen_pp -chop UTC %s  ") % (os.environ.get('STPL_ROOT'), self.spf_seq_file)
            htdte_logger.inform(('Running:%s') % (command_line))
            itppHand = subprocess.Popen(command_line, shell=True, stdout=subprocess.PIPE)
            HTD_subroccesses_pid_tracker_list.append(itppHand.pid)
            status = itppHand.communicate()
            if (status[len(status) - 1] is None and (not re.search("Error while parsing Test Sequence", str(status)))):
                #htdte_logger.inform( ('Status:%s')%(status[len(status)-2]))
                htdte_logger.inform('Done Running STPL, generated ITPP')
            else:
                htdte_logger.error(("STPL run didnt finish correctly\n%s") % (status[len(status) - 2]))

        # ------------------
        # Read fopen of itpp, parse it and convert to
            line_num = 0
            content = []
            ir = ""
            # while line:
            instrumental_comment_line = ""  # tobe save in transactor for final itpp
            for line in open(("%s") % (self.actual_itpp_seq_file), 'r').readlines():
                #print line
                # ----------------------
                line_num = line_num + 1
                # if(re.search("rem:\s+",line)):
                #instrumental_comment_line=line.replace("rem: ","")
                # instrumental_comment_line=line
                if(re.search("^to_state: .*", line)):
                    result_transactor_l.append(hpl_tap_transactor_entry("state", 0, 0, "IDLE"))
                elif(re.search("^tap_instruction_size:.*", line)):
                    tapsize = re.search(r"^tap_instruction_size:\s*(\d+).*", line)
                    result_transactor_l.append(hpl_tap_transactor_entry("tap_size", 0, 0, tapsize.groups()[0]))
                elif(re.search(r"^label:\s*(.*)", line)):
                    # labelIR=""
                    # labelDR=""
                    label = re.search(r"^label:\s*(.*)", line)
                    # match=re.search("IR",label.groups()[0])
                    # if(match):
                    result_transactor_l.append(hpl_tap_transactor_entry("label", 0, 0, label.groups()[0]))
                    # else:
                    # labelDR=label.groups()[0]
                elif(re.search(r"^scani:\s*['bh]*([0-1_]+)", line)):
                    scani = re.search(r"scani:\s*['bh]*([0-1_]+)", line)
                    ir = "".join(scani.groups(0))  # contain a string of x_x_x_......<data>
                    ircode_str = ir.replace("_", "")
                    #print ircode_str
                    ircode = "".join(ircode_str)
                    #print "ircode %s" % ircode
                    # KSERRANO TODO result_transactor_l.append( hpl_tap_transactor_entry("ir",int(str(ircode_str),2),len(ircode_str),"root",bit0_drv,bit0_strb,instrumental_comment_line,isMainTx))
                    result_transactor_l.append(hpl_tap_transactor_entry("ir", int(str(ircode_str), 2), len(ircode_str), "root", 0, 0, instrumental_comment_line, 1, 0, 0))
                # elif(re.search("^#\s*DR_SHIFT:\s*(\w+_\w+)\s*=\s*(.*)",line)):
                    # line=re.sub('\[\d+\]',"",line)
                    # topology= re.search("^#\s*DR_SHIFT:\s*(\w+_\w+)\s*=\s*(.*)",line)
                    #topology_ir=topology.groups() [0]
                    #topology_dr_list= topology.groups()[1].replace('+',"").split(" ")
                    # index=topology_dr_list.index(topology_ir.replace('_','.'))
                    # pad_left=topology_dr_list[:index].count('PAD')
                    # pad_rigth=topology_dr_list[index+1:].count('PAD')
                elif(re.search(r"^scand:\s*([0-1_]+)\s*,\s*([XHL]+)", line)):

                    pad_left = 0
                    pad_rigth = 0
                    scand = re.search(r"^scand:\s*([0-1_]+)\s*,\s*([XHL]+)", line)
                    dr = scand.groups()[0]
                    strobes = scand.groups()[1]
                    # drcode_str=dr.replace("_","")
                    result_transactor_l.append(hpl_tap_transactor_entry("dr", int(str(dr), 2), len(dr), "root", 0, 0, instrumental_comment_line, 1, pad_left, pad_rigth, strobes))
                elif(re.search(r"^pscand:\s*(.*)", line)):
                    pscand = re.search(r"pscand:\s*(.*)", line)
                    result_transactor_l.append(hpl_tap_transactor_entry("pscand", 0, 0, pscand.groups()[0]))
                elif(re.search(r"^vector:\s*TMS\(0\),\s*(\d+)", line)):
                    waitcycles = re.search(r"^vector:\s*TMS\(0\),\s*(\d+)", line)
                    result_transactor_l.append({"op": "WAIT", "waitcycles": int(waitcycles.groups()[0])})
                elif(re.search(r"^pass\s*itpp(.*)", line)):
                    itpp = re.search(r"^pass\s*itpp\s*(.*)", line)
                    result_transactor_l.append({"op": "ITPP", "strvalue": itpp.groups()[0]})

            htdte_logger.inform('Done Reading ITPP')
            self.spf_transact_counter = self.spf_transact_counter + 1
        return result_transactor_l
