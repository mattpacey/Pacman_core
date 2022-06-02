import socket
import sys
import re
import os
import subprocess
import random
from htd_tap_info import *
from htd_utilities import *
from htd_collaterals import *


class htd_dfx_tap_info(htd_tap_info):
    def __init__(self):
        htd_tap_info.__init__(self)
        if(os.environ.get('HTD_PROJ') is None):
            htdte_logger.error('Missing obligatory unix environment ENV[HTD_PROJ] ')
        proj = os.environ.get('HTD_PROJ').upper()
        step = os.environ.get('step_is')
        # ------------------------
        if(os.environ.get('TAP_LINK_SERVER_CMD') is None):
            htdte_logger.error('Missing obligatory unix environment ENV[TAP_LINK_SERVER_CMD] - must point to TAP link server provided by DFX team')
        if(os.environ.get('TAP_LINK_SERVER_ARGS') is None):
            htdte_logger.error('Missing obligatory unix environment ENV[TAP_LINK_SERVER_AGRS] - must specify swithes for ENV[TAP_LINK_SERVER_CMD] ')
        # if(os.environ.get('TAP_LINK_SOCKET_FILE_DIR')==None):
        #     htdte_logger.error( 'Missing obligatory unix environment ENV[TAP_LINK_SOCKET_FILE_DIR] - must point to TAP link server provided by DFX team')
        #tap_server_path=os.environ.get('TAP_LINK_SERVER').split(" ")
        #htdte_logger.inform(("Using TAP server path=%s")%(tap_server_path[0]))
        if(not os.path.exists(os.environ.get('TAP_LINK_SERVER_CMD'))):
            htdte_logger.error(('The TAP server command (%s) given in ENV[TAP_LINK_SERVER_CMD] - is not legal') % (os.environ.get('TAP_LINK_SERVER_CMD')))
        # --------------------------------
        socket_file = ("%s/DfxTapLinkInfoServerSocket%d") % (os.environ.get('TAP_LINK_SOCKET_FILE_DIR') if os.environ.get('TAP_LINK_SOCKET_FILE_DIR') is not None else "./", os.getpid())
        server_command = ("%s%s -server %s -proj %s  -step  %s -gift %s") % (os.environ.get('TAP_LINK_SERVER_CMD'), os.environ.get('TAP_LINK_SERVER_ARGS'), "%s", proj, step, "-unix_domain_socket")
        if ("server_retry_times" in list(CFG["INFO"].keys())):
            self.set_server_retry(int(CFG["INFO"]["server_retry_times"]))
        if ("server_timeout" in list(CFG["INFO"].keys())):
            self.set_server_timeout(int(CFG["INFO"]["server_timeout"]))
        self.StartServer("TapLinkInfoServerDfx", socket_file, server_command, 10, 4)
        if(self.GetServerProcessId() > 0):
            HTD_subroccesses_pid_tracker_list.append(self.GetServerProcessId())
    # --------Automatically discovered method , called by help if exists----------------

    def html_content_help(self, file_name):
        html_file = open(file_name, 'w')
        html_file.write("<!DOCTYPE html>\n<html>\n")
        html_file.write('<a name="top"></a>\n<body>')
        html_file.write('<p><h1> DFX Tap Link UI Content </h1></p><hr>\n')
        agents = self.get_tap_agents()
        agents = sorted(set(agents))  # unique values
        for agent in agents:
            html_file.write(('<a href="#%s">%s</a><br>\n') % (agent, agent))
        html_file.write('<br><hr>\n')
        # -------------------------
        ignore_agents_or_cmds = []
        if("TapInfoHelpIgnore" in list(CFG["HPL"].keys())):
            ignore_agents_or_cmds = CFG["HPL"]["TapInfoHelpIgnore"].replace(" ", "").split(",")
        # ----------------------
        for agent in agents:
            if(agent in ignore_agents_or_cmds):
                htdte_logger.inform(("Ignoring TAP info for controller: %s (ignored by CFG[\"HPL\"][\"TapInfoHelpAgntIgnore\"])") % (agent))
                continue
            htdte_logger.inform(("Extracting TAP info for controller: %s") % (agent))
            try:
                irs_str = self.send_receive_message(('<server_get_tap_irs> %s \n') % (agent))
            except BaseException:
                html_file.write(('<p><h3> TAP Controller: %s is not accessable by DFT TAP Link server</h3></p><hr>\n') % agent)
                continue
            # ------------------
            html_file.write(('<a name="%s"></a>\n') % (agent))
            html_file.write(('<p><h3> TAP Controller: %s </h3></p><hr>\n') % agent)
            html_file.write('<table border="1">\n')
            html_file.write('<tr bgcolor="blue"><th><font color="white">CMD</font>\
	 		     </th><th><font color="white">OPCODE</font></th>\
	 		     <th><font color="white">FIELD</font></th>\
	 		     <th><font color="white">LSB:MSB</font></th>\
	 		     <th><font color="white">RESET</font></th>\
	 		     <th><font color="white">RTL Node</font></th>\
	 		     <th><font color="white">Comments</font></th></tr>')
            for ir in irs_str.split("\n"):
                ir = ir.replace(("%s.") % (agent), "")
                if(ir in ignore_agents_or_cmds):
                    htdte_logger.inform(("Ignoring TAP CMD info : %s (ignored by CFG[\"HPL\"][\"TapInfoHelpIgnore\"])") % (ir))
                    continue
                html_file.write(('<tr align="left" bgcolor="yellow"><th>%s</th><th>%s</th> <th></th><th></th><th></th><th></th><th></th></tr>') % (ir, util_int_to_binstr(self.get_ir_opcode_int(ir, agent), self.get_ir_size(agent))))
                # ----------Fields
                for field in self.get_ir_fields(ir, agent):
                    html_file.write(('<tr align="left"><th></th><th></th> <th>%s</th><th>%d:%d</th><th>0x%x</th><th>%s</th><th>%s</th></tr>') % (field, self.get_field_lsb(ir, agent, field),
                                                                                                                                                 self.get_field_msb(ir, agent, field), self.get_field_reset_value(ir, agent, field),
                                                                                                                                                 self.get_rtl_endpoint(ir, agent, field) if (self.rtl_node_exists(ir, agent, field)) else "",
                                                                                                                                                 self.get_tap_field_comments(ir, agent, field)))

            html_file.write('</table>\n')
        html_file.write('<hr>\n<a href="#top">Top of Page</a>\n')
        html_file.write('<br>\n</body>\n</html>\n')
        html_file.close()
    # ------------------------

    def get_tap_agents(self):
        message = ("<server_get_tap_types>\n")
        agents_str = self.send_receive_message(message)
        if(re.search("ERROR", agents_str)):
            htdte_logger.error((" <server_get_tap_types> error ::%s'") % (agents_str))
        agents = sorted(set(agents_str.split("\n")))  # unique values
        return agents if agents is not None else []
     # ------------------------

    def get_ir_commands(self, agent):
        message = ("<server_get_tap_irs> %s\n") % (agent)
        irs_str = self.send_receive_message(message)
        if(re.search("ERROR", irs_str)):
            htdte_logger.error((" <server_get_tap_irs> error ::%s'") % (irs_str))
        res = set(irs_str.split("\n")) if irs_str is not None else []
        return [x.replace(("%s.") % (agent), "") for x in res]

   # ---------------------------------
    def normalize_field_name(self, IR, agent, field):
        return field
    # -----------------------------------

    def get_tap_field_comments(self, IR, agent, field):
        #message = ("<server_get_field_comment> %s.%s.%s \n")%(agent,IR,field)
        # return self.send_receive_message(message)
        return "NA_yet"
    # -------------------------

    def get_field_msb(self, IR, agent, field):
        if(field == ""):
            return -1
        if(self.tap_reg_backdoor_exists(IR, agent)):
            return self.tap_reg_backdoor_get_field_msb(IR, agent, field)
        field_range = self.send_receive_message(("<server_get_field_range> %s.%s.%s \n") % (agent, IR, field))
        if(re.search("<server_error>", field_range) or field_range == "[:]"):
            field_range = self.send_receive_message(("<server_get_field_range> %s.%s \n") % (IR, field))
            if(re.search("<server_error>", field_range) or field_range == "[:]"):
                htdte_logger.error((" <server_get_field_range> error : Can't find field info for agent:%s cmd:%s'") % (agent, IR))
        m = re.search(r'\[(\d+):(\d+)\]', field_range)
        if m:
            field_msb = m.group(1)
            field_lsb = m.group(2)
        else:
            htdte_logger.error((r" <get_field_lsb> error : return %s , while expected format: \[(\d+):(\d+)\]'") % (field_range))
        if((agent in list(self.ir_field_size_override.keys())) and (IR in self.ir_field_size_override[agent]) and (field in list(self.ir_field_size_override[agent][IR].keys()))):
            return int(field_msb) + self.ir_field_size_override[agent][IR][field] - 1
        else:
            return int(field_msb)
    # ------------------------------

    def get_field_lsb(self, IR, agent, field):
        if(field == ""):
            return -1
        if(self.tap_reg_backdoor_exists(IR, agent)):
            return self.tap_reg_backdoor_get_field_lsb(IR, agent, field)
        field_range = self.send_receive_message(("<server_get_field_range> %s.%s.%s \n") % (agent, IR, field))
        if(re.search("<server_error>", field_range) or field_range == "[:]"):
            field_range = self.send_receive_message(("<server_get_field_range> %s.%s \n") % (IR, field))
            if(re.search("<server_error>", field_range) or field_range == "[:]"):
                htdte_logger.error((" <server_get_field_range> error : Can't find field info for agent:%s cmd:%s'") % (agent, IR))
        m = re.search(r'\[(\d+):(\d+)\]', field_range)
        if m:
            field_msb = m.group(1)
            field_lsb = m.group(2)
        else:
            htdte_logger.error((r" <get_field_lsb> error: return %s , while expected format: \[(\d+):(\d+)\]'") % (field_range))
        return int(field_lsb)
    # --------------------

    def get_field_reset_value(self, IR, agent, field):
        if(self.tap_reg_backdoor_exists(IR, agent)):
            return self.tap_reg_backdoor_get_field_reset_value(IR, agent, field)
        field_default_value = self.send_receive_message(("<server_get_field_default_value> %s.%s.%s \n") % (agent, IR, field))
        if(re.search("<server_error>", field_default_value) or field_default_value == "''"):
            field_default_value = self.send_receive_message(("<server_get_field_default_value> %s.%s \n") % (IR, field))
            if(re.search("<server_error>", field_default_value)):
                htdte_logger.error((" Fail to get a field reset value (%s.%s): %s") % (agent, IR, field_default_value))
        # ---------------------
        val_str = field_default_value.replace("'", "")
        m = re.search("([0-1]+)b$", val_str)
        if(m):
            return int(m.groups()[0], 2)
        # ---------------------
        if(re.search(r"\d+x[0-9a-fA-F]+$", val_str)):
            return int(val_str, 16)
        # --------------------
        m = re.search(r'(\d+)', field_default_value)
        if m:
            field_value_str = m.group(1)
        else:
            field_value_str = 0
        field_lsb = self.get_field_lsb(IR, agent, field)
        field_msb = self.get_field_msb(IR, agent, field)
        num_of_bits = field_msb - field_lsb + 1
        scale = 10
        # dec-->bin + scaling to field's size (e.g. to get 010 instead of 10)
        field_bin_value = bin(int(field_value_str, scale))[2:].zfill(num_of_bits)
        return int(field_bin_value)
    # ----------------------------------------------------

    def get_ir_opcode_string(self, IR, agent, err_suppress=0):
        if(agent not in self.get_tap_agents()):
            if(err_suppress):
                return 0
            else:
                htdte_logger.error((" <server_get_ir_opcode> error : Illegal agent name:%s,\nAvailable tap agents are:%s'") % (agent, self.get_tap_agents()))

        IR = IR.replace(("%s.") % (agent), "")
        opcode = self.send_receive_message(("<server_get_ir_opcode> %s.%s \n") % (agent, IR))
        if(re.search("<server_error>", opcode)):
            opcode = self.send_receive_message(("<server_get_ir_opcode> %s \n") % (IR))
            if(re.search("<server_error>", opcode)):
                if(err_suppress):
                    return opcode
                else:
                    htdte_logger.error((" <server_get_ir_opcode> error : Can't find opcode for agent:%s cmd:%s'") % (agent, IR))
        return opcode

    def get_ir_opcode_int(self, IR, agent, err_suppress=0):
        str_val = self.get_ir_opcode_string(IR, agent, err_suppress)
        if(str_val == 0 and err_suppress > 0):
            return 0
        if(re.search("<server_error>", str_val)):
            IR = ("%s.%s") % (agent, IR)  # trying to find format "agent.cmd"
            str_val = self.get_ir_opcode_string(IR, agent, err_suppress)
            if(re.search("<server_error>", str_val)):
                if(err_suppress > 0):
                    return 0
                else:
                    irs_str = self.send_receive_message("<server_get_tap_irs> " + agent + "\n").split("\n")
                    htdte_logger.error((" Can't find a tap instruction :%s.%s.Available instructions are : %s") % (agent, IR, str(irs_str)))
        return int(self.get_ir_opcode_string(IR, agent, err_suppress), 2)
    # ---------------------------------------------

    def get_ir_field_details(self, IR, agent):
        if(self.tap_reg_backdoor_exists(IR, agent)):
            return self.tap_reg_backdoor_get_field_details(IR, agent)
        # if(IR=="BYPASS"):
        #  return {"msb":0,"lsb":0}
        ir_fields_str = self.send_receive_message(("<server_get_ir_details> %s.%s \n") % (agent, IR))
        if(re.search("<server_error>", ir_fields_str)):
            ir_fields_str = self.send_receive_message(("<server_get_ir_details> %s \n") % (IR))
            if(re.search("<server_error>", ir_fields_str)):
                htdte_logger.error(("<get_ir_field_details> Can't find an ir by   agent:%s cmd:%s.") % (agent, IR))

        fields_l = ir_fields_str.split("\n")
        res = {}
        for field in fields_l:
            match = re.match(r"\s*\[\s*(\d+):(\d+)\s*\]\s+([A-z0-9_.]+)\s+'(.+)'$", field)
            if(match):
                field_name = match.groups()[2]
                field_msb = match.groups()[0]
                field_lsb = match.groups()[1]
            else:
                htdte_logger.error((r"Wrong get_ir_fields response format. Expected format: [\d+:\d+]  <NAME>  '<Description>', received - \"%s\"") % (field))
            res[field_name] = {"msb": field_msb, "lsb": field_lsb}
        return res

    def insensitive_case_doc_field_name_match(self, irname, agent, field):
        doc_fields_l = self.get_ir_fields(irname, agent)
        doc_field_name = field
        if(field not in doc_fields_l):
            if (field.upper() in doc_fields_l):
                doc_field_name = field.upper()
            elif (field.lower() in doc_fields_l):
                doc_field_name = field.lower()
            else:
                doc_field_name = ""
                htdte_logger.error(("Illegal field-\"%s\" name used in tap access %s:%s.\nAvailable fields are : %s") % (
                    field, agent, irname, ",".join(str(doc_fields_l).rsplit("\n", 1))))
        return doc_field_name

    def get_ir_fields(self, IR, agent):
        return list(self.get_ir_field_details(IR, agent).keys())
    # --------------------------------------

    def get_dr_total_length(self, IR, agent):
        if(self.tap_reg_backdoor_exists(IR, agent)):
            return self.get_tap_reg_backdoor_size(IR, agent)
        ir_details = self.send_receive_message(("<server_get_ir_details> %s.%s \n") % (agent, IR))
        if(re.search("<server_error>", ir_details)):
            ir_details = self.send_receive_message(("<server_get_ir_details> %s \n") % (IR))
            if(re.search("<server_error>", ir_details)):
                htdte_logger.error(("<get_ir_field_details> Can't find an ir by   agent:%s cmd:%s.") % (agent, IR))

        dr_fields = ir_details.rsplit('\n')
        dr_length = 0
        for f in dr_fields:
            m = re.search(r'\[(\d+):(\d+)\]\s+(\S+)', f)
            if(not m):
                htdte_logger.error(r" <get_dr_total_length> error: expected format is [(\d+):(\d+)]\s+(\S+)")
            lsb = m.group(2)
            msb = m.group(1)
            fld = m.group(3)
            if((agent in list(self.ir_field_size_override.keys())) and (IR in self.ir_field_size_override[agent]) and (fld in list(self.ir_field_size_override[agent][IR].keys()))):
                dr_length = dr_length + self.ir_field_size_override[agent][IR][fld]
            else:
                dr_length = dr_length + int(msb) - int(lsb) + 1
        return dr_length
    # --------------------------

    def verify_tap_cmd(self, agnt, cmd):
        self.get_ir_opcode_int(cmd, agnt)
    # ---------------------------------

    def verify_tap_register_field(self, agent, cmd, field):
        if(field not in self.get_ir_fields(cmd, agent)):
            htdte_logger.error(("Illegal field - %s applied on TAP agent - %s, CMD:%s") % (field, agent, cmd))
    # ------------------------------

    def rtl_node_exists(self, IR, agent, field):
        if(os.environ.get('HTD_TE_INFO_UI_HELP') is not None):
            return 0
        rtl_endpoint_str = self.send_receive_message("<server_get_rtl_node> " + agent + "." + IR + "." + field + "\n")
        if(re.search("error", rtl_endpoint_str) or not rtl_endpoint_str):
            return self.rtl_node_backdoor_exists(agent, IR, field)
        fub_path_str = self.send_receive_message("<server_get_fub_path> " + agent + "." + IR + "." + field + "\n")
        if(re.search("error", fub_path_str) or not fub_path_str):
            return self.rtl_node_backdoor_exists(agent, IR, field)
        if(not HTD_INFO.signal_info.signal_module_exists(fub_path_str)):
            return self.rtl_node_backdoor_exists(agent, IR, field)
        else:
            return 1
    # ------------------------------------------------------

    def get_rtl_endpoint(self, IR, agent, field):
        if(self.rtl_node_backdoor_exists(agent, IR, field)):
            return self.get_rtl_node_backdoor(agent, IR, field)
        else:
            rtl_endpoint_str = self.send_receive_message("<server_get_rtl_node> " + agent + "." + IR + "." + field + "\n")
            if(re.search("error", rtl_endpoint_str) or not rtl_endpoint_str):
                htdte_logger.error((" <server_get_rtl_node> Cant find rtl node by agent:%s cmd:%s field:%s.\n %s") % (agent, IR, field, rtl_endpoint_str))
        # ------------------------
        fub_path_str = self.send_receive_message("<server_get_fub_path> " + agent + "." + IR + "." + field + "\n")
        if(re.search("error", fub_path_str) or not fub_path_str):
            htdte_logger.error((" <server_get_fub_path> Cant find fub path by agent:%s cmd:%s field:%s.\n %s") % (agent, IR, field, fub_path_str))

        if(not HTD_INFO.signal_info.signal_module_exists(("%s") % (fub_path_str))):
            htdte_logger.error((" <server_get_rtl_node> Cant find IP tap rtl module: \"%s\"") % (fub_path_str))
        return ("%s/%s") % (fub_path_str, rtl_endpoint_str)

    # --------------------------
    def get_full_dr(self, IR, agent, field, field_dr):
        ir_fields = self.get_ir_fields(s, IR)
        splitted_list = ir_fields.rsplit('\n')
        list_len = len(splitted_list)
        DR = ''
        for index in range(0, list_len - 1):
            m = re.search(r'\]\s*(\S+)', splitted_list[index])
            if m:
                field_name = m.group(1)
                if (field_name == field):
                    get_ir_opcodeDR = field_dr + DR
                else:
                    DR = get_field_reset_value(s, IR, field_name) + DR
        return DR
     # --------------------------

    def get_tap_PARIR(self, agent):
        message = "<server_get_tap_link_cmd_name> " + agent + ".PARIR\n"
        PARIR = self.send_receive_message(message)
        return int(PARIR, 2)
     # --------------------------

    def get_tap_PARDR(self, TAP):
        message = "<server_get_tap_link_cmd_name> " + agent + ".PARDR\n"
        PARDR = self.send_receive_message(message)
        return int(PARDR, 2)
     # --------------------------

    def get_tap_SERIR(self, agent, slice_num):
        #message = "<server_get_tap_link_cmd_name> " + agent + ".PARIR\n"
        #PARIR = self.send_receive_message(message)
        return -1
     # --------------------------

    def get_tap_SERDR(self, TAP, slice_num):
        #message = "<server_get_tap_link_cmd_name> " + agent + ".PARDR\n"
        #PARDR = self.send_receive_message(message)
        return -1

    # ---------------------------------------
    def get_ir_name(self, ircode, agent, errsuppress=0):
        message = "<server_get_tap_irs> " + agent + "\n"
        irs_str = self.send_receive_message(message)
        tap_cmd_l = irs_str.replace(("%s.") % (agent), "").split("\n")
        for cmd in tap_cmd_l:
            if(self.get_ir_opcode_int(cmd, agent, 1) == ircode):
                return cmd
        if(errsuppress):
            return ""
        else:
            htdte_logger.error((" Can't match a tap instruction matching to ir code - 0x%x") % (ircode))
    # -----------------------------

    def get_ir_size(self, agent):
        message = "<server_get_tap_irs> " + agent + "\n"
        irs_str = self.send_receive_message(message)
        tap_cmd_l = irs_str.split("\n")
        if(len(tap_cmd_l) < 1):
            tdte_logger.error((" Can't find any opcode in tap controller  - %s") % (agent))
        cmd = tap_cmd_l[0].replace(("%s.") % (agent), "")
        op = self.get_ir_opcode_string(cmd, agent)
        if(not re.search("not found", op)):
            return len(op)
        htdte_logger.error((" Can't find any opcode for agent  - %s") % (agent))
    # ------------------------------
    #
    # -----------------------------

    def get_tap_link_PARIR(self, TAP):
        message = "<server_get_tap_link_cmd_name> " + TAP + ".PARIR\n"
        irname = self.send_receive_message(message)
        if(re.search("error", irname)):
            htdte_logger.error((" Can't find a %s.IR - field") % (TAP))
        m = re.search(r"([A-z0-9_]+)\.([A-z0-9_]+)", irname)
        if(not m):
            htdte_logger.error((" Illegal tap link ir server response: \"%s\", expected \"<agent>.<taplink_ir_cmd>\" format") % (irname))
        agent = m.groups()[0]
        irname = m.groups()[1]
        return (agent, irname, "IR")

    def get_tap_link_PARDR(self, TAP):
        message = "<server_get_tap_link_cmd_name> " + TAP + ".PARDR\n"
        irname = self.send_receive_message(message)
        if(re.search("error", irname)):
            htdte_logger.error((" Can't find a %s.IR - field") % (TAP))
        m = re.search(r"([A-z0-9_]+)\.([A-z0-9_]+)", irname)
        if(not m):
            htdte_logger.error((" Illegal tap link dr server response: \"%s\", expected \"<agent>.<taplink_dr_cmd>\" format") % (irname))
        agent = m.groups()[0]
        irname = m.groups()[1]
        return (agent, irname, "DR")

    def has_tap_link_parallel_support(self, TAP):
        message = "<server_get_tap_link_cmd_name> " + TAP + ".PARIR\n"
        resp = self.send_receive_message(message)
        if(re.search("PARIR not found", resp)):
            return 0
        else:
            return 1

    def get_tap_link_IR(self, TAP):
        message = "<server_get_tap_link_cmd_name> " + TAP + ".IR\n"
        irname = self.send_receive_message(message)
        if(re.search("error", irname)):
            htdte_logger.error((" Can't find a %s.IR - field") % (TAP))
        m = re.search(r"([A-z0-9_]+)\.([A-z0-9_]+)", irname)
        if(not m):
            htdte_logger.error((" Illegal tap link ir server response: \"%s\", expected \"<agent>.<taplink_ir_cmd>\" format") % (irname))
        agent = m.groups()[0]
        irname = m.groups()[1]
        return (agent, irname, "IR")

    def get_tap_link_DR(self, TAP):
        message = "<server_get_tap_link_cmd_name> " + TAP + ".DR\n"
        irname = self.send_receive_message(message)
        if(re.search("error", irname)):
            htdte_logger.error((" Can't find a %s.DR - field") % (TAP))
        m = re.search(r"([A-z0-9_]+)\.([A-z0-9_]+)", irname)
        if(not m):
            htdte_logger.error((" Illegal tap link dr server response: \"%s\", expected \"<agent>.<taplink_dr_cmd>\" format") % (irname))
        agent = m.groups()[0]
        irname = m.groups()[1]
        return (agent, irname, "DR")

    def is_taplink_remote_tap(self, agent):
        message = ("<server_get_tap_link_type>  %s \n") % (agent)
        resp = self.send_receive_message(message)
        if(re.search(r"remote\s+taplink\s+controller", resp)):
            return 1
        elif(re.match(r"local\s+taplink\s+controller", resp)):
            return 0
        else:
            htdte_logger.error((r" Improper <server_get_tap_link_type %s > result format - expcted <(local|remote)\s+taplink\s+co/subIP/dfx_rtl/config_mod_dntroller> , received - \"%s\" ") % (agent, resp))

    def get_taplink_parallel_agents_by_agents(self, agent):
        message = "<server_get_list_of_instances> " + agent + "\n"
        agents = self.send_receive_message(message)
        if(re.match("^ERROR", agents)):
            htdte_logger.error(('Failed to determine parallel_agents_by_agent for Agent:  (%s)') % (agent))
            sys.exit(1)
        return agents.split(",")

    def get_real_agent(self, agent, IR):
        return agent
