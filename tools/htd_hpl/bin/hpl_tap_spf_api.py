import socket
import sys
import re
import os
import subprocess
from htd_utilities import *
from htd_collaterals import *
from hpl_tap_engine_structs import *
import subprocess
import time

# ---------------------------------


class HplTapSpfApi(object):
    def __init__(self):
        self.spf_transact_counter = 0
        # --Check if current direcrory has a files spf_seq_transaction_*itpp, remove them
        spf_filesIndir = [f for f in os.listdir(os.environ.get('PWD')) if (os.path.isfile(("%s/%s") % (os.environ.get('PWD'), f)) and re.search(r"spf_seq_transaction_\d+.seq", f))]
        for f in spf_filesIndir:
            os.remove(f)

        # ---------------------------------------
        # ---------------------------------------------
#   def get_itpp_code(self,spf_code):
#    spf_file = open(spf_code)
#    print spf_file
#    spf_content = spf_file.read()
#    print spf_content
#    subprocess.call(["$SPF_ROOT/bin/spf", "--tapSpecFile BXT.tap.spfspec --testSeqFile /nfs/sc/proj/skx/skx_rtl127/mggomezc/HVMPL_VT/htd.spf  --itppFile output.itpp --templateFile /nfs/sc/disks/ivytown29/tvpv/cache/fchan4/spf/spf_includes/spf.template"])

    def parse_instrumental_comment(self, line, active_agent):
        active_agents_l = {}  # keep length of sequence per agent in network chain
        active_agent_index = 0  # store an active agent in all network chain
        active_agent_index = []
        current_bit_index = 0
        # agents=[]
        # irs=[]
        # ----------------------
        if(re.search(r"rem:\s+", line)):
            instrumental_comment_line = line.replace("rem: ", "")
            if (re.match(r"IR_REGISTERS:\s*", instrumental_comment_line)):
                instrumental_comment_line_clean = instrumental_comment_line.replace("IR_REGISTERS:", "")
            elif(re.match(r"DR_SHIFT:\s*", instrumental_comment_line)):
                instrumental_comment_line_clean = instrumental_comment_line.replace("DR_REGISTERS:", "")
            agents_str_l = instrumental_comment_line_clean.split(" + ")
            #print agents_str_l
            for agent_str in agents_str_l:
                agent_token_match = re.search(r"\s*([A-z0-9_]+)\s*=>\s*([A-z0-9_]+)\s*\[(\d+)\]", agent_str)
                if(agent_token_match):
                    current_agent = agent_token_match.groups()[0]
                    current_agent_instruction = agent_token_match.groups()[1]
                    current_agent_seq_length = int(agent_token_match.groups()[2])
                    if(current_agent == active_agent and (not current_agent_instruction == "BYPASS")):
                        return (current_bit_index, current_bit_index, 1)
                        # return (current_bit_index-1,current_bit_index-1,1)
                    else:
                        current_bit_index += current_agent_seq_length
                else:
                    htdte_logger.error((r"Not expected Instrumental line format : %s\n Expected: rem:\s+([A-z0-9_]+)\s*=>\s*([A-z0-9_]+)\s*\[(\d+)\]") % (agent_str))
            return (0, 0, 0)
            #htdte_logger.error(("Can't match an active agent-\"%s\" in instrumental comment - %s")%(line))
        else:
            htdte_logger.error((r"Not expected Instrumental line format : %s\n Expected: rem:\s+....") % (line))

    # def run_single_spf_instruction(self,agent,irname):
    def get_tap_transactions(self, irname, agent, drsequence, sequence_length, dr_by_fields, assigned_fields, parallel=0, read_mode=False, pad_left=0, pad_rigth=0, dronly=0):
        # -------------------------
        result_transactor_l = []
        if("tap_mode" in list(CFG["HPL"].keys()) and CFG["HPL"]["tap_mode"] == "taplink"):
            parallel_tap_agents = HTD_INFO.tap_info.get_taplink_parallel_agents_by_agents(agent)
        else:
            parallel_tap_agents = []
        # 1. Create SPF seq file - file name dynamically changed
        spf_seq_file = ("spf_seq_transaction_%d.seq") % (self.spf_transact_counter)
        prev_seq_file = ("spf_seq_transaction_%d.seq") % (self.spf_transact_counter - 1)
        #print prev_seq_file

        spf_sequencer_fh = open(spf_seq_file, "w", 1)
        spf_sequencer_fh.write("@set tap_auto_unfocus off;\n")

        if (dronly):
            spf_sequencer_fh.write("@set tap_skip_ir on;\n")

        if(parallel and parallel_tap_agents is not None and len(parallel_tap_agents) > 1):
            focus_agents = ""
            for a in parallel_tap_agents:
                focus_agents += (" %s") % (a)
            spf_sequencer_fh.write(("focus_tap %s;\n") % (focus_agents))
        else:
            spf_sequencer_fh.write(("focus_tap %s;\n") % (agent))
        # -----------------------------
        dr_length = HTD_INFO.tap_info.get_dr_total_length(irname, agent)
        ir_access = HTD_INFO.tap_info.get_ir_access(irname, agent)

        #dr_val=1 | (1<<(dr_length-1))
        if(len(list(dr_by_fields.keys())) < 1):
            if (ir_access == "RO"):
                spf_sequencer_fh.write(("compare %s = 'b%s ;\n") % (irname, drsequence))
            else:
                spf_sequencer_fh.write(("set %s = 'b%s ;\n") % (irname, drsequence))
        else:
            for key in list(dr_by_fields.keys()):
                if(key not in ["dri", "dro"]):
                    if (ir_access == "RO"):
                        spf_sequencer_fh.write(('compare %s->%s = \'h%x;\n') % (irname, key, dr_by_fields[key] if dr_by_fields[key] >= 0 else 0))
                    else:
                        spf_sequencer_fh.write(('set %s->%s = \'h%x;\n') % (irname, key, dr_by_fields[key] if dr_by_fields[key] >= 0 else 0))

        # ------------------------
        spf_sequencer_fh.write("flush;\n")
        spf_sequencer_fh.close()
        htdte_logger.inform('Done Writing SPF')
        # ---Execute SPF----
        chkpt_option = (("--checkPointFile %s.chkpt --restoreCheckPoint %s.chkpt ") % (spf_seq_file, prev_seq_file)) if (self.spf_transact_counter > 0) else (("--checkPointFile  %s.chkpt") % (spf_seq_file))
        # BXT doesnt allow safe restore
        command_line = ("%s/bin/spf --tapSpecFile %s --testSeqFile %s --itppFile %s.itpp --templateFile %s  %s") % (os.environ.get('SPF_ROOT'), os.environ.get("HTD_SPF_TAP_SPEC_FILE"), spf_seq_file, spf_seq_file, os.environ.get("HTD_SPF_TEMPLATE_FILE"), chkpt_option)
        #command_line=("%s/bin/spf --tapSpecFile %s --testSeqFile %s --itppFile %s.itpp --templateFile %s  ")%(os.environ.get('SPF_ROOT'),os.environ.get("HTD_SPF_TAP_SPEC_FILE"),spf_seq_file,spf_seq_file,os.environ.get("HTD_SPF_TEMPLATE_FILE"))
        htdte_logger.inform(('Running:%s') % (command_line))
        itppHand = subprocess.Popen(command_line, shell=True, stdout=subprocess.PIPE)
        HTD_subroccesses_pid_tracker_list.append(itppHand.pid)
        status = itppHand.communicate()
        # check status and call htd_logger.error if not successfull
        # print "ALEXSE:" + str(status) Error while parsing Test Sequence
        if (status[len(status) - 1] is None and (not re.search("Error while parsing Test Sequence", str(status)))):
            #htdte_logger.inform( ('Status:%s')%(status[len(status)-2]))
            htdte_logger.inform('Done Running SPF, generated ITPP')
        else:
            htdte_logger.error(("SPF run didnt finish correctly\n%s") % (status[len(status) - 2]))

        # ------------------
        # Read fopen of itpp, parse it and convert to
        line_num = 0
        content = []
        ir = ""
        epir_flag = 1
        # while line:
        instrumental_comment_line = ""  # tobe save in transactor for final itpp
        for line in open(("%s.itpp") % (spf_seq_file), 'r').readlines():
            #print line
            # ----------------------
            line_num = line_num + 1
            if(re.search(r"rem:\s+", line)):
                #instrumental_comment_line=line.replace("rem: ","")
                instrumental_comment_line = line
            elif(re.search(r"scani:\s*([0-1_]+)", line)):
                scani = re.search(r"scani:\s*([0-1_]+)", line)
                ir = "".join(scani.groups(0))  # contain a string of x_x_x_......<data>
                ircode_str = ir.replace("_", "")
                (bit0_drv, bit0_strb, isMainTx) = self.parse_instrumental_comment(instrumental_comment_line, agent)
                #print ircode_str
                ircode = "".join(ircode_str)
                #print "ircode %s" % ircode
                result_transactor_l.append(hpl_tap_transactor_entry("ir", int(str(ircode_str), 2), len(ircode_str), "root", bit0_drv, bit0_strb, instrumental_comment_line, isMainTx))
            elif(re.search(r"scand:\s*([0-1_]+)", line)):
                scand = re.search(r"scand:\s*([0-1_]+)", line)
                dr = "".join(scand.groups(0))
                drcode_str = dr.replace("_", "")
                (bit0_drv, bit0_strb, isMainTx) = self.parse_instrumental_comment(instrumental_comment_line, agent)
                if(HTD_INFO.tap_info.is_taplink_remote_tap(agent) and (epir_flag == 1)):
                    result_transactor_l.append(hpl_tap_transactor_entry("dr", int(str(drcode_str), 2), len(drcode_str), "epir", bit0_drv, bit0_strb, instrumental_comment_line, isMainTx))
                    epir_flag = 0
                else:
                    result_transactor_l.append(hpl_tap_transactor_entry("dr", int(str(drcode_str), 2), len(drcode_str), "root", bit0_drv, bit0_strb, instrumental_comment_line, isMainTx))
            elif(re.search("^#", line) or re.search(r"^\s*\n", line)):
                # next(
                continue
            else:
                result_transactor_l[len(result_transactor_l) - 1].mid_transaction_queue.append(line)
            #htdte_logger.inform(( 'Line %s')%(line))
        htdte_logger.inform('Done Reading ITPP')
        if(os.environ.get('HTD_SPF_DEBUG') is None or os.environ.get('HTD_SPF_DEBUG') == "0"):
            os.remove(("%s.itpp") % (spf_seq_file))
            os.remove(("%s") % (spf_seq_file))
            # entry={}
            # entry["ir"]=ir
            # entry["dr"]=dr
        # content.append(entry)

        # read and prse itppp
        # return all transaction
        # ==================
        self.spf_transact_counter = self.spf_transact_counter + 1
        return result_transactor_l

# def get_tap_transactions(self,tap_params):
#  return []
