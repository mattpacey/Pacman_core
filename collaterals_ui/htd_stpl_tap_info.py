import socket
import sys
import re
import os
import subprocess
from htd_tap_info import *
from htd_utilities import *
from htd_collaterals import *


class htd_stpl_tap_info(htd_tap_info):
    def __init__(self):
        htd_tap_info.__init__(self)
        if(os.environ.get('HTD_PROJ') is None):
            htdte_logger.error('Missing obligatory unix environment ENV[HTD_PROJ] ')
        proj = os.environ.get('HTD_PROJ').upper()
    # --------------------------

    def verify_tap_cmd(self, agnt, cmd):
        self.get_ir_opcode_int(cmd, agnt)
    # ---------------------------------

    def verify_tap_register_field(self, agnt, cmd, field):
        if(field not in self.get_ir_fields(cmd, agnt)):
            htdte_logger.error(("Illegal field - %s applied on TAP agent - %s, CMD:%s") % (field, agent, IR))
    # ------------------------

    def get_field_msb(self, IR, agent, field):

        # -- Reading IR and breaking it up into clustername + irname
        match = re.match(r"(\w+)_(\w+)", IR)
        if(match):
            clustername = match.groups()[0].lower()
            irname = match.groups()[1].lower()
        else:
            htdte_logger.error(("Expected format: <AGENT>_<IRNAME>', received - \"%s\"") % (IR))

        # -- Processing  entry in field
        field_offset = str(dict_ir_information[clustername]['entry'][irname]['DrInfo'][field]["FieldLocation"])
        match_single = re.match(r"^(\d+)$", field_offset)
        if(match_single):
            field_msb = match_single.groups()[0]
            field_lsb = match_single.groups()[0]
        match_double = re.match(r"^(\d+):(\d+)$", field_offset)
        if(match_double):
            field_msb = match_double.groups()[0]
            field_lsb = match_double.groups()[1]
        if (not (match_double or match_single)):
            htdte_logger.error((r"Expected FieldLocation format: [\d+:\d+]  or [\d+]', received - \"%s\"") % (field_offset))

        return int(field_msb)
    # ------------------------------

    def get_field_lsb(self, IR, agent, field):

        # -- Reading IR and breaking it up into clustername + irname
        match = re.match(r"(\w+)_(\w+)", IR)
        if(match):
            clustername = match.groups()[0].lower()
            irname = match.groups()[1].lower()
        else:
            htdte_logger.error(("Expected format: <AGENT>_<IRNAME>', received - \"%s\"") % (IR))

        # -- Processing  entry in field
        field_offset = str(dict_ir_information[clustername]['entry'][irname]['DrInfo'][field]["FieldLocation"])
        match_single = re.match(r"^(\d+)$", field_offset)
        if(match_single):
            field_msb = match_single.groups()[0]
            field_lsb = match_single.groups()[0]
        match_double = re.match(r"^(\d+):(\d+)$", field_offset)
        if(match_double):
            field_msb = match_double.groups()[0]
            field_lsb = match_double.groups()[1]
        if (not (match_double or match_single)):
            htdte_logger.error((r"Expected FieldLocation format: [\d+:\d+]  or [\d+]', received - \"%s\"") % (field_offset))

        return int(field_lsb)
    # --------------------

    def get_field_reset_value(self, IR, agent, field):

        # -- Reading IR and breaking it up into clustername + irname
        match = re.match(r"(\w+)_(\w+)", IR)
        if(match):
            clustername = match.groups()[0].lower()
            irname = match.groups()[1].lower()
        else:
            htdte_logger.error(("Expected format: <AGENT>_<IRNAME>', received - \"%s\"") % (IR))

        field_defvalue = str(dict_ir_information[clustername]['entry'][irname]['DrInfo'][field]["FieldDefValue"])

        return int(field_defvalue)

    #message = "<server_get_field_reset_value> "  + IR + " " + agent + " " + field + "\n"
    #reset_value = self.send_receive_message(message)
    # if(re.match("/^ERROR/",reset_value)):
    #    htdte_logger.error(( 'Failed to determine reset value for Agent: (%s) IR: (%s) Field: (%s)')%(agent,IR,field))
    #    sys.exit(1)
    # return int(reset_value)
    # ----------------------------------------------------
    def get_ir_opcode_string(self, IR, agent, err_suppress=0):
        if(agent not in list(dict_ir_table.keys())):
            if(err_suppress):
                return 0
            htdte_logger.error(("Illegal agent name: %s - not recognized as valid tapcontroller\nValid controllers are : %s") % (agentt, (list(dict_ir_table.keys()))))
        if(IR not in list(dict_ir_table[agent]["irname"].keys())):
            if(err_suppress):
                return 0
            htdte_logger.error(("Illegal IR name: %s - not recognized as valid tap instruction in tap controller-%s") % (IR, agent))
        return ("%d") % (dict_ir_table[agent]["irname"][IR]["code"])
    # ----------------------------------------------------

    def get_ir_opcode_int(self, IR, agent, err_suppress=0):
        str_val = self.get_ir_opcode_string(IR, agent)
        if(str_val == 0 and err_suppress > 0):
            return 0
        return int(str_val, 2)
    # ---------------------------------------------

    def get_ir_fields(self, IR, agent):

        # -- Reading IR and breaking it up into clustername + irname
        match = re.match(r"(\w+)_(\w+)", IR)
        if(match):
            clustername = match.groups()[0].lower()
            irname = match.groups()[1].lower()
        else:
            htdte_logger.error(("Expected format: <AGENT>_<IRNAME>', received - \"%s\"") % (IR))

        res = {}
        # -- Getting dictionary
        fields_l = list(dict_ir_information[clustername]['entry'][irname]['DrInfo'].keys())

        # -- Processing each entry in field list and generating hash for next steps
        for field in fields_l:

            field_name = field
            field_offset = str(dict_ir_information[clustername]['entry'][irname]['DrInfo'][field_name]["FieldLocation"])
            match_single = re.match(r"^(\d+)$", field_offset)
            if(match_single):
                field_msb = match_single.groups()[0]
                field_lsb = match_single.groups()[0]
            match_double = re.match(r"^(\d+):(\d+)$", field_offset)
            if(match_double):
                field_msb = match_double.groups()[0]
                field_lsb = match_double.groups()[1]
            if (not (match_double or match_single)):
                htdte_logger.error((r"Expected FieldLocation format: [\d+:\d+]  or [\d+]', received - \"%s\"") % (field_offset))

            res[field_name] = {"msb": field_msb, "lsb": field_lsb}
        return res
    # --------------------------

    def get_dr_total_length(self, IR, agent):

        # -- Reading IR and breaking it up into clustername + irname
        match = re.match(r"(\w+)_(\w+)", IR)
        if(match):
            clustername = match.groups()[0].lower()
            irname = match.groups()[1].lower()
        else:
            htdte_logger.error(("Expected format: <AGENT>_<IRNAME>', received - \"%s\"") % (IR))

        res = {}
        # -- Getting dictionary
        fields_l = list(dict_ir_information[clustername]['entry'][irname]['DrInfo'].keys())

        current_msb = 0
        current_lsb = 999999  # kserrano - not that good
        # -- Processing each entry in field list and extracting max msb and min lsb
        for field in fields_l:
            lsb = self.get_field_lsb(IR, agent, field)
            msb = self.get_field_msb(IR, agent, field)
            if (current_msb < msb):
                current_msb = msb
            if (current_lsb > lsb):
                current_lsb = lsb

        if (current_lsb != 0):
            htdte_logger.error(("Expected LSB to be 0: - something not good in this loop - received - \"%s\"") % (current_lsb))

        dr_size = current_msb - current_lsb + 1

        return int(dr_size)

    #message = "<server_get_dr_size> " + IR + " " + agent + "\n"
    #dr_size = self.send_receive_message(message)
    # if(re.match("/^ERROR/",dr_size)):
    #    htdte_logger.error(( 'Failed to determine dr_size for Agent: (%s) IR: (%s)')%(agent,IR))
    #    sys.exit(1)
    # --------------------------
    def rtl_node_exists(self, IR, agent, field):
        message = "<server_get_rtl_struct> " + agent + "." + IR + "." + field + "\n"
        # rtl_endpoint_str = self.send_receive_message(message)
        # TODO should be closed with OZ (fub,node)=rtl_endpoint_str.split(":")
    # only for taplink ????
        return 1

    def get_rtl_endpoint(self, IR, agent, field):
        message = "<server_get_rtl_struct> " + agent + "." + IR + "." + field + "\n"
        # rtl_endpoint_str = self.send_receive_message(message)
        # TODO should be closed with OZ (fub,node)=rtl_endpoint_str.split(":")
        return ("soc_tb.soc.TODO_Oz_NOT_SUPPORTING_YET__%s__%s__%s") % (agent, IR, field.replace(".", "_"))
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
        found = 0
        for irname in list(dict_ir_table[agent]["irname"].keys()):
            ircode_local = HTD_INFO.tap_info.get_ir_opcode_int(irname, agent)
            #print ("Comparing %s -- %d->%d")%(irname,ircode_local,ircode)
            if(ircode_local == ircode):
                return irname
        if(errsuppress):
            return ""
        else:
            htdte_logger.error((" Can't find IR name by  ir code - 0x%x") % (ircode))
    # -----------------------------

    def get_ir_size(self, agent):
        # -----------
        # -- Needs to be fixed -- Not sure how to handle Core + Uncore
        ir_size = 11
        return int(ir_size)

    def get_real_agent(self, agent, IR):
        return agent
