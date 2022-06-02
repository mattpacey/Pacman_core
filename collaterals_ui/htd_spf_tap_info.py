import socket
import sys
import re
import os
import subprocess
from htd_tap_info import *
from htd_utilities import *
from htd_collaterals import *


class htd_spf_tap_info(htd_tap_info):
    def __init__(self):
        htd_tap_info.__init__(self)
        if(os.environ.get('HTD_PROJ') is None):
            htdte_logger.error('Missing obligatory unix environment ENV[HTD_PROJ] ')
        proj = os.environ.get('HTD_PROJ').upper()
        # ------------------------
        if(os.environ.get('TAP_SPF_SERVER') is None):
            htdte_logger.error('Missing obligatory unix environment ENV[TAP_SPF_SERVER] - must point to TAP link server provided by DFX team')
        htdte_logger.inform(("Using TAP server path=%s") % (os.environ.get('TAP_SPF_SERVER')))
        if(not os.path.exists(os.environ.get('TAP_SPF_SERVER'))):
            htdte_logger.error(('The TAP server path (%s) given in ENV[TAP_SPF_SERVER] - is not exists') % (os.environ.get('TAP_SPF_SERVER')))
        # --------------------------------
        if(os.environ.get('SPF_ROOT') is None):
            htdte_logger.error('Missing SPF_ROOT env. (should it  be set in TE_cfg or in xterm ?')
        LdLibraryPath = ("%s/lib/perl5%s") % (os.environ.get('SPF_ROOT'), ("" if (os.environ.get('LD_LIBRARY_PATH') is None) else (":%s") % (os.environ.get('LD_LIBRARY_PATH'))))
        os.environ['LD_LIBRARY_PATH'] = LdLibraryPath
        htdte_logger.inform(('SPF setup done: setenv LD_LIBRARY_PATH %s') % (os.environ.get('LD_LIBRARY_PATH')))
        # --------------------------------
        if(os.environ.get('HTD_SPF_TAP_SPEC_FILE') is None):
            htdte_logger.error('Missing obligatory TE_cfg.cml parameter HTD_SPF_TAP_SPEC_FILE.')
        htdte_logger.inform(("Using HTD_SPF_TAP_SPEC_FILE file=%s") % (os.environ.get('HTD_SPF_TAP_SPEC_FILE')))
        self.spec_file = os.environ.get('HTD_SPF_TAP_SPEC_FILE')
        # ---------------------------------------
        ld_library = os.environ.get('LD_LIBRARY_PATH')
        ld_library_l = ld_library.split(":")
        if(("%s/lib") % os.environ.get('SPF_ROOT') not in ld_library_l):
            new_ld_library_path = ("%s/lib") % os.environ.get('SPF_ROOT')
            htdte_logger.inform(('Modifying LD_LIBRARY_PATH =%s') % (new_ld_library_path))
            os.environ["LD_LIBRARY_PATH"] = new_ld_library_path
            os.putenv("LD_LIBRARY_PATH", new_ld_library_path)
        # --------------------------------
        socket_file = ("%s/SpfTapNtwrkInfoSrvrSckt%d") % (self.get_socket_path(), os.getpid())
        server_command = ("%s -sock %s -spec %s -silent 1") % (os.environ.get('TAP_SPF_SERVER'), "%s", self.spec_file)
        if ("server_retry_times" in list(CFG["INFO"].keys())):
            self.set_server_retry(int(CFG["INFO"]["server_retry_times"]))
        if ("server_timeout" in list(CFG["INFO"].keys())):
            self.set_server_timeout(int(CFG["INFO"]["server_timeout"]))
        self.StartServer("TapSpfServer", socket_file, server_command, 1200, 4)
        if(self.GetServerProcessId() > 0):
            HTD_subroccesses_pid_tracker_list.append(self.GetServerProcessId())
      # ---------------------------------

    def get_socket_path(self):
        socket_path = ""
        if ("socket_file_location" in list(CFG["INFO"].keys())):
            socket_path = CFG["INFO"]["socket_file_location"]
        else:  # use /tmp if exist else use current working directory
            if os.path.exists("/tmp"):
                socket_path = "/tmp"
            else:
                socket_path = os.environ.get('PWD')
        return socket_path

    # ----------------------------------------------------
    def verify_tap_cmd(self, agnt, cmd):
        self.get_ir_opcode_int(cmd, agnt)
    # ---------------------------------

    def verify_tap_register_field(self, agnt, cmd, field):
        if(field not in self.get_ir_fields(cmd, agnt)):
            htdte_logger.error(("Illegal field - %s applied on TAP agent - %s, CMD:%s") % (field, agnt, IR))
    # ------------------

    def get_ir_commands(self, agent):
        message = ("<server_get_tap_irs> %s\n") % (agent)
        irs_str = self.send_receive_message(message)
        if(re.search("^ERROR", irs_str)):
            htdte_logger.error((" <server_get_tap_irs> error ::%s'") % (irs_str))
        return set(irs_str.split("\n")) if irs_str is not None else []
      # ---------------------------------------------

    def get_ir_field_details(self, IR, agent):
        if(self.tap_reg_backdoor_exists(IR, agent)):
            return self.tap_reg_backdoor_get_field_details(IR, agent)
        # if(IR=="BYPASS"):
        #  return {"msb":0,"lsb":0}
        ir_fields_str = self.send_receive_message(("<server_get_ir_details> %s %s \n") % (IR, agent))
        if(re.search("<server_error>", ir_fields_str)):
            htdte_logger.error(("<get_ir_field_details> Can't find an ir by   agent:%s cmd:%s.") % (agent, IR))

        fields_l = ir_fields_str.split("\n")
        res = {}
        for field in fields_l:
            match = re.match(r"\s*\[\s*(\d+):(\d+)\s*\]\s+([A-z0-9_.]+)\s+'(.*)'$", field)
            if(match):
                field_name = match.groups()[2]
                field_msb = match.groups()[0]
                field_lsb = match.groups()[1]
            else:
                htdte_logger.error((r"Wrong get_ir_fields response format. Expected format: [\d+:\d+]  <NAME>  '<Description>', received - \"%s\"") % (field))
            res[field_name] = {"msb": field_msb, "lsb": field_lsb}
        return res
        # -----------------------------------

    def get_tap_field_comments(self, IR, agent, field):
        #message = ("<server_get_field_comment> %s.%s.%s \n")%(agent,IR,field)
        # return self.send_receive_message(message)
        return "NA_yet"
    # ------------------------

    def get_tap_agents(self):
        message = ("<server_get_tap_types>\n")
        agents_str = self.send_receive_message(message)
        if(re.search("^ERROR", agents_str)):
            htdte_logger.error((" <server_get_tap_types> error :%s'") % (agents_err))
        agents = sorted(set(agents_str.split("\n")))  # unique values
        return agents if agents is not None else []
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
        ignore_agents_or_cmds = []
        if("TapInfoHelpIgnore" in list(CFG["HPL"].keys())):
            ignore_agents_or_cmds = CFG["HPL"]["TapInfoHelpIgnore"].replace(" ", "").split(",")
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
    # def __del__(self):
    # htd_tap_info.__del__(self)
    # ------------------------

    def get_field_msb(self, IR, agent, field):
        if(self.tap_reg_backdoor_exists(IR, agent)):
            return self.tap_reg_backdoor_get_field_msb(IR, agent, field)
        message = "<server_get_field_msb> " + IR + " " + agent + " " + field + "\n"
        msb = self.send_receive_message(message)
        if(re.match("^ERROR", msb)):
            htdte_logger.error(('Failed to determine msb for Agent: (%s) IR: (%s) Field: (%s): \n %s') % (agent, IR, field, msb))
            sys.exit(1)
        if((agent in list(self.ir_field_size_override.keys())) and (IR in self.ir_field_size_override[agent]) and (field in list(self.ir_field_size_override[agent][IR].keys()))):
            return int(msb) + self.ir_field_size_override[agent][IR][field] - 1
        else:
            return int(msb)
    # ------------------------------

    def get_field_lsb(self, IR, agent, field):
        if(self.tap_reg_backdoor_exists(IR, agent)):
            return self.tap_reg_backdoor_get_field_lsb(IR, agent, field)
        message = "<server_get_field_lsb> " + IR + " " + agent + " " + field + "\n"
        lsb = self.send_receive_message(message)
        if(re.match("^ERROR", lsb)):
            htdte_logger.error(('Failed to determine lsb for Agent: (%s) IR: (%s) Field: (%s)') % (agent, IR, field))
            sys.exit(1)
        return int(lsb)
    # --------------------

    def get_field_reset_value(self, IR, agent, field, err_suppress=0):
        message = "<server_get_field_reset_value> " + IR + " " + agent + " " + field + "\n"
        reset_value = self.send_receive_message(message)
        if(re.match("^ERROR", reset_value)):
            if(err_suppress):
                return 0
            htdte_logger.error(('Failed to determine reset value for Agent: (%s) IR: (%s) Field: (%s)') % (agent, IR, field))
            sys.exit(1)
        return int(reset_value, 2)
    # ----------------------------------------------------

    def get_ir_opcode_string(self, IR, agent, err_suppress=0):
        if(err_suppress):
            return 0
        message = "<server_get_ir_opcode> " + agent + " " + IR + "\n"
        opcode = self.send_receive_message(message)
        if(re.match("^ERROR", opcode)):
            if(err_suppress):
                return 0
            htdte_logger.error(('Failed to determine opcode for Agent: (%s) IR: (%s) :[%s]') % (agent, IR, opcode))
            sys.exit(1)
        return opcode
    # ----------------------------------------------------

    def get_ir_opcode_int(self, IR, agent, err_suppress=0):
        str_val = self.get_ir_opcode_string(IR, agent, err_suppress)
        if(str_val == 0 and err_suppress > 0):
            if(err_suppress):
                return 0
            else:
                return 0
        if(re.match("<server_error>.+", str_val) or str_val == 0):
            if(err_suppress):
                return 0
            else:
                htdte_logger.error((" Can't find a tap instruction :%s.%s") % (agent, IR))
        return int(self.get_ir_opcode_string(IR, agent, err_suppress), 2)
    # ---------------------------------------------

    def get_ir_fields(self, IR, agent):
        if(self.tap_reg_backdoor_exists(IR, agent)):
            return list(self.tap_reg_backdoor_get_field_details(IR, agent).keys())
        message = "<server_get_ir_fields> " + IR + " " + agent + "\n"
        fields_str = self.send_receive_message(message)
        if(re.match("^ERROR", fields_str)):
            htdte_logger.error(('Failed to determine fields for Agent: (%s) IR: (%s)') % (agent, IR))
            sys.exit(1)
        fields_l = fields_str.split("\n")
        res = {}
        for field in fields_l:
            match = re.match(r"\s*\[\s*(\d+):(\d+)\s*\]\s+([A-Za-z0-9_.]+)\s+'(.*)'$", field)
            if(match):
                field_name = match.groups()[2]
                field_msb = match.groups()[0]
                field_lsb = match.groups()[1]
            else:
                htdte_logger.error((r"Expected format: [\d+:\d+]  <NAME>  '<Description>', received - \"%s\"") % (field))
            res[field_name] = {"msb": field_msb, "lsb": field_lsb}
        return res
    # --------------------------

    def get_dr_total_length(self, IR, agent):
        if(self.tap_reg_backdoor_exists(IR, agent)):
            return self.get_tap_reg_backdoor_size(IR, agent)
        ir_details = self.send_receive_message(("<server_get_ir_details> %s %s \n") % (IR, agent))
        if(re.search("<server_error>", ir_details)):
            htdte_logger.error(("<get_ir_field_details> Can't find an ir by   agent:%s cmd:%s.") % (agent, IR))

        dr_fields = ir_details.rsplit('\n')
        dr_length = 0
        for f in dr_fields:
            m = re.search(r'\[(\d+):(\d+)\]\s+(\S+)', f)
            if(not m):
                htdte_logger.error((r" <get_dr_total_length> error: expected format is [(\d+):(\d+)]\s+(\S+), received :%s") % (f))
            lsb = m.group(2)
            msb = m.group(1)
            fld = m.group(3)
            if((agent in list(self.ir_field_size_override.keys())) and (IR in self.ir_field_size_override[agent]) and (fld in list(self.ir_field_size_override[agent][IR].keys()))):
                dr_length = dr_length + self.ir_field_size_override[agent][IR][fld]
            else:
                msb_int = int(msb)
                lsb_int = int(lsb)
                if (msb_int < lsb_int):
                    temp = lsb_int
                    lsb_int = msb_int
                    msb_int = temp
                dr_length = dr_length + msb_int - lsb_int + 1
        return dr_length
    # --------------------------

    def rtl_node_exists(self, IR, agent, field):
            # message = "<server_get_rtl_struct> " + agent + "." + IR + "." + field + "\n"?????????????
            # --In future SPF should manage signals , meanwile checking in dictionary if exists
        try:
            # --Trying getting the rtl node information from processed dictionary
            rtl_nodes_dict = list(dict_tap_rtl_info.keys())
            if(agent in list(dict_tap_rtl_info.keys())):
                if("cmd" not in dict_tap_rtl_info[agent]):
                    htdte_logger.error(('tap_rtl_info[\"%s\"][\"cmd\"]') % (agent))
                ircode = self.get_ir_opcode_int(IR, agent)
                if(ircode in list(dict_tap_rtl_info[agent]["cmd"].keys())):
                    if("field" not in list(dict_tap_rtl_info[agent]["cmd"][ircode].keys())):
                        htdte_logger.error(('tap_rtl_info[\"%s\"][\"cmd\"][0x%x][\"field\"]') % (agent, ircode))
                    if(field in list(dict_tap_rtl_info[agent]["cmd"][ircode]["field"].keys())):
                        if("rtlPath" in list(dict_tap_rtl_info[agent]["cmd"][ircode]["field"][field].keys())):
                            return 1
                    elif(field.replace(".", "_") in list(dict_tap_rtl_info[agent]["cmd"][ircode]["field"].keys())):
                        if("rtlPath" in list(dict_tap_rtl_info[agent]["cmd"][ircode]["field"][field.replace(".", "_")].keys())):
                            return 1
            return self.rtl_node_backdoor_exists(agent, IR, field)
        except NameError:
                # --trying getting rtl node from spf
            if(os.environ.get('HTD_TE_INFO_UI_HELP') is not None):
                return 0
            rtl_endpoint_str = self.send_receive_message("<server_get_rtl_node> " + agent + "." + IR + "." + field + "\n")
            if(re.search("error", rtl_endpoint_str) or not rtl_endpoint_str):
                return self.rtl_node_backdoor_exists(agent, IR, field)
            fub_path_str_l = rtl_endpoint_str.replace(".", "/").split("/")
            if(len(fub_path_str_l) > 0 and not HTD_INFO.signal_info.signal_module_exists(("%s") % (fub_path_str_l[0]))):
                return self.rtl_node_backdoor_exists(agent, IR, field)
            else:
                return 1
            # rtl_endpoint_str = self.send_receive_message(message)
            # TODO should be closed with OZ (fub,node)=rtl_endpoint_str.split(":")
            # only for taplink ????
    # --------------------------------------------

    def is_taplink_remote_tap(self, agent):
        message = ("<server_get_tap_link_type>  %s \n") % (agent)
        resp = self.send_receive_message(message)
        if(re.search(r"remote\s+taplink\s+controller", resp)):
            return 1
        elif(re.match(r"local\s+taplink\s+controller", resp)):
            return 0
        else:
            htdte_logger.error((r" Improper <server_get_tap_link_type %s > result format - expcted <(local|remote)\s+taplink\s+co/subIP/dfx_rtl/config_mod_dntroller> , received - \"%s\" ") % (agent, resp))

    def has_tap_link_parallel_support(self, TAP):
        message = "<server_get_tap_link_cmd_name> " + TAP + ".PARIR\n"
        resp = self.send_receive_message(message)
        if(re.search("PARIR not found", resp)):
            return 0
        else:
            return 1

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

    def get_tap_link_IR(self, TAP):
        message = "<server_get_tap_link_cmd_name> " + TAP + ".IR\n"
        irname = self.send_receive_message(message)
        if(re.search("error", irname)):
            htdte_logger.error((" Can't find a %s.IR - field: (%s)") % (TAP, irname))
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
    # --------------------------

    def change_ir_field_size(self, IR, agent, field, new_size):
        if(agent not in list(self.ir_field_size_override.keys())):
            self.ir_field_size_override[agent] = {}
        if(IR not in list(self.ir_field_size_override[agent].keys())):
            self.ir_field_size_override[agent][IR] = {}
        self.ir_field_size_override[agent][IR][field] = new_size
    # ---------------------------------------

    def get_rtl_endpoint(self, IR, agent, field):
        # --In future SPF should manage signals , meanwile checking in dictionary if exists
        # message = "<server_get_rtl_struct> " + agent + "." + IR + "." + field + "\n"
            # rtl_endpoint_str = self.send_receive_message(message)
            # TODO should be closed with OZ (fub,node)=rtl_endpoint_str.split(":")
        # return ("soc_tb.soc.TODO_Oz_NOT_SUPPORTING_YET__%s__%s__%s")%(agent,IR,field.replace(".","_"))
        try:
            # --Trying getting the rtl node information from processed dictionary
            rtl_nodes_dict = list(dict_tap_rtl_info.keys())
            if(agent in list(dict_tap_rtl_info.keys())):
                if("cmd" not in dict_tap_rtl_info[agent]):
                    htdte_logger.error(('tap_rtl_info[\"%s\"][\"cmd\"]') % (agent))
                ircode = self.get_ir_opcode_int(IR, agent)
                if(ircode in list(dict_tap_rtl_info[agent]["cmd"].keys())):
                    if("field" not in list(dict_tap_rtl_info[agent]["cmd"][ircode].keys())):
                        htdte_logger.error(('tap_rtl_info[\"%s\"][\"cmd\"][0x%x][\"field\"]') % (agent, ircode))
                    if(field in list(dict_tap_rtl_info[agent]["cmd"][ircode]["field"].keys())):
                        fab = "" if ("rtlFub" not in list(dict_tap_rtl_info[agent]["cmd"][ircode]["field"][field].keys())) else ("%s/") % dict_tap_rtl_info[agent]["cmd"][ircode]["field"][field]["rtlFub"]
                        if("rtlPath" in list(dict_tap_rtl_info[agent]["cmd"][ircode]["field"][field].keys())):
                            return ("%s%s") % (fab, dict_tap_rtl_info[agent]["cmd"][ircode]["field"][field]["rtlPath"])
                    elif(field.replace(".", "_") in list(dict_tap_rtl_info[agent]["cmd"][ircode]["field"].keys())):
                        fab = "" if ("rtlFub" not in list(dict_tap_rtl_info[agent]["cmd"][ircode]["field"][field.replace(".", "_")].keys())) else ("%s/") % dict_tap_rtl_info[agent]["cmd"][ircode]["field"][field.replace(".", "_")]["rtlFub"]
                        if("rtlPath" in list(dict_tap_rtl_info[agent]["cmd"][ircode]["field"][field.replace(".", "_")].keys())):
                            return ("%s%s") % (fab, dict_tap_rtl_info[agent]["cmd"][ircode]["field"][field.replace(".", "_")]["rtlPath"])

        except NameError:
            if(self.rtl_node_backdoor_exists(agent, IR, field)):
                return self.get_rtl_node_backdoor(agent, IR, field)
            else:
                rtl_endpoint_str = self.send_receive_message("<server_get_rtl_node> " + agent + "." + IR + "." + field + "\n")
                if(re.search("error", rtl_endpoint_str) or not rtl_endpoint_str):
                    htdte_logger.error((" <server_get_rtl_node> Cant find rtl node by agent:%s cmd:%s field:%s.\n %s") % (agent, IR, field, rtl_endpoint_str))
            # ---------------
            if(self.rtl_node_backdoor_exists(agent, IR, field)):
                return self.get_rtl_node_backdoor(agent, IR, field)
            else:
                fub_path_str_l = rtl_endpoint_str.replace(".", "/").split("/")
                if(len(fub_path_str_l) > 0 and not HTD_INFO.signal_info.signal_module_exists(("%s") % (fub_path_str_l[0]))):
                    htdte_logger.error((" <server_get_rtl_node> Cant find IP tap rtl module: \"%s\"") % (fub_path_str_l[0]))
                return rtl_endpoint_str
    # --------------------------

    def get_full_dr(self, IR, agent, field, field_dr):
        htdte_logger.error('get_full_dr not supported yet')
      # Ask Alex about this -> does it come from DFX API
        #ir_fields = get_ir_fields(s,IR)
        #splitted_list = ir_fields.rsplit('\n')
        #list_len = len(splitted_list)
        #DR = ''
        # for index in range(0,list_len-1):
        # m = re.search(r'\]\s*(\S+)', splitted_list[index])
        # if m:
        # 	field_name = m.group(1)
        # 	if (field_name == field):
        # 		get_ir_opcodeDR = field_dr + DR
        # 	else:
        # 		DR = get_field_reset_value(s,IR,field_name) + DR
        # return DR
        # --------------------------

    def get_tap_PARIR(self, agent):
        htdte_logger.error('get_tap_PARIR not supported for TAP Network')
        # --------------------------

    def get_tap_PARDR(self, TAP):
        htdte_logger.error('get_tap_PARDR not supported for TAP Network')
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
        #binircode = bin(ircode)
        #final_code = binircode.replace("0b","")
        final_code = format(ircode, ('0%db') % self.get_ir_size(agent))
        message = "<server_get_ir_name> " + final_code + " " + agent + "\n"
        irname = self.send_receive_message(message)
        if(re.match("^ERROR", irname)):
            if(errsuppress):
                return ""
            htdte_logger.error((" Can't find IR name for  ir code - 0x%x") % (ircode))
            sys.exit(1)
        return irname
    # -----------------------------

    def get_ir_size(self, agent):
        message = "<server_get_ir_size> " + agent + "\n"
        ir_size = self.send_receive_message(message)
        if(re.match("^ERROR", ir_size)):
            htdte_logger.error(('Failed to determine ir_size for Agent: (%s)') % (agent))
            sys.exit(1)
        return int(ir_size)
    # -------------------------------------

    def get_ir_access(self, IR, agent):
        message = "<server_get_ir_access> " + IR + " " + agent + "\n"
        ir_access = self.send_receive_message(message)
        if(re.match("^ERROR", ir_access)):
            htdte_logger.error(('Failed to determine ir_access for Agent: (%s) IR: (%s)') % (agent, IR))
            sys.exit(1)
        return ir_access
    # ----------------------------

    def get_taplink_parallel_agents_by_agents(self, agent):
        message = "<server_get_parallel_taplink_agents> " + agent + "\n"
        agents = self.send_receive_message(message)
        if(re.match("^ERROR", agents)):
            htdte_logger.error(('Failed to determine parallel_agents_by_agent for Agent:  (%s)') % (agent))
            sys.exit(1)
        return agents.split(",")

    # workaround for agent name as some command PARDR/PARIR/LINKIR/LINKDR/TAPSTAUTS/CFG
    # belong to glue tap when referring to CLTAP
    # need to be enhanced to support all types
    def get_real_agent(self, agent, IR):
        if (agent != "CLTAP" or not IR.endswith("_TAPSTATUS")):
            return agent

        tapstatus_index = IR.find("_TAPSTATUS")
        agent = IR[0: tapstatus_index]
        agent = "GLUE_%s_TAP" % (agent)
        agent = agent.replace("CLTAP_", "")
        htdte_logger.inform("Agent was changed to %s" % (agent))
        return agent
