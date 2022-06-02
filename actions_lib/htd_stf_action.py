from htd_basic_action import *
from htd_utilities import *
from htd_collaterals import *
from htd_player_top import *
import copy
import json
import pprint

# Tracking info to make sure we don't verify more than once
stf_action_init_tracking = {}

valid_select_modes = ["OUTPUT_ENABLED", "LISTEN_ONLY", "BIFURCATED", "OUTPUT_ENABLED_DATALOG", "LISTEN_ONLY_DATALOG", "BIFURCATED_DATALOG", "RESET_STF_NETWORK"]

STF_NUM_USROPS = 4

# napounde - TODO - import hpl_stf_op
# from hpl_stf_op import *

##############################################
# Require CFG category=STF_packet defined as in example:
# <CFG category="STF_packet">
#   <Var key="size"   value="42"/>
#   <Var key="packet" INPUT_VALID="0:0" OUTPUT_VALID="1:1" OPCODE="2:5" GID="6:9" PID="10:25" GID_BANK="26:26" DATA="10:41"/>
#   <Var key="OPCODE" NOP="4'b0000" SELECT="4'b0100" SELECT_MASK="4'b0110" REPLACE="4'b1000" CONTROL="4'b1010" DATA="4'b1011" USROP1="4'b1100" USROP2="4'b1101" USROP3="4'b1110" USROP4="4'b1111" />
# </CFG>
################################################

##########################################################
# Example STF Action Calls
##########################################################
# select
# self.exec_stf_action({"actionName":"SelectAction1", "op":"select", "agent":"clst_scan_ccf_sb,stf_csi2_endpoint", "gid":5, "gid_bank":1})
# self.exec_stf_action({"actionName":"SelectAction2", "op":"select", "agent":"clst_scan_ccf_sb", "gid":3})
#
# select_mask
# self.exec_stf_action({"actionName":"SelectMaskAction1", "op":"select_mask", "pid_mask":0x43AB, "pid_sel":0x110A, "gid":5, "gid_bank":0})
# self.exec_stf_action({"actionName":"SelectMaskAction2", "op":"select_mask", "pid_mask":0x43AB, "pid_sel":0x110A, "gid":5})
#
# map_usrop
# self.exec_stf_action({"actionName":"MapUsropAction1", "op":"map_usrop", "agent":"clst_scan_ccf_sb,stf_csi2_endpoint", "usrop":1 "reg":"RegA", "gid":4})
# self.exec_stf_action({"actionName":"MapUsropAction2", "op":"map_usrop", "agent":"clst_scan_ccf_sb,stf_csi2_endpoint", "usrop":1 "reg":"RegA"})
#
# write_read
# Write to specific fields
# self.exec_stf_action({"actionName":"WriteAction1, "op":"write_read", "agent":"clst_scan_ccf_sb,stf_csi2_endpoint", "reg":"RegA", "field1":0x2, ..., "gid":4"})
# self.exec_stf_action({"actionName":"WriteAction2, "op":"write_read", "agent":"clst_scan_ccf_sb,stf_csi2_endpoint", "reg":"RegA", "field1":0x2, ...})
#
# Read specific fields
# self.exec_stf_action({"actionName":"ReadAction1, "op":"write_read", "agent":"clst_scan_ccf_sb,stf_csi2_endpoint", "reg":"RegA", "field1":0x2, ..., "gid":4", "read_type":1})
# self.exec_stf_action({"actionName":"ReadAction2, "op":"write_read", "agent":"clst_scan_ccf_sb,stf_csi2_endpoint", "reg":"RegA", "field1":0x2, ..., "read_type":1})
#
# Write and Read specific fields
# self.exec_stf_action({"actionName":"WriteReadAction1, "op":"write_read", "agent":"clst_scan_ccf_sb,stf_csi2_endpoint", "reg":"RegA",
#                       "field1":{"write_value":0x2, "read_value":0x1, "access_type":HTD_VALUE_RW_ACCESS},
#                       "field2":{"write_value":0x2, "access_type":HTD_VALUE_WRITE_ACCESS} ..., "gid":4", "read_type":1})
#
# TBD: add replace example
#
# Write and Read entire reg
# self.exec_stf_action({"actionName":"WriteReadAction1, "op":"write_read", "agent":"clst_scan_ccf_sb,stf_csi2_endpoint", "reg":"RegA",
#                       "write_value":0xdead,
#                       "read_value":0xaced, "gid":4", "read_type":1})
#
# nop
# self.exec_stf_action({"actionName":"NopAction1", "op":"nop", "agent":"clst_scan_ccf_sb,stf_csi2_endpoint", "gid":4, "num":5}) - send 5 nops to gid 4
# self.exec_stf_action({"actionName":"NopAction2", "op":"nop", "agent":"clst_scan_ccf_sb,stf_csi2_endpoint"}) - send 1 nop to agents listed
#
# null
# self.exec_stf_action({"actionName":"NullAction1", "op":"null", "num":5}) - send 5 nulls
# self.exec_stf_action({"actionName":"NullAction2", "op":"null"}) - send 1 null
# ##########################################################


class STF(htd_base_action):

    def __init__(self, action_name, source_file, source_lineno, currentFlow, is_internal):

        self.direct_packet = {}
        self.direct_packet_mode = False

        # Create instance variable for tracking the required steps for this operation
        self.ops = []

        # ----------------
        htd_base_action.__init__(self, self.__class__.__name__, action_name,
                                 source_file, source_lineno, currentFlow, is_internal)

        # -----------------
        self.size = 0

        # History Tracking
        self.history_container = "stf_history"

        # ---STF access by agent.register.field
        # napounde - TODO - Need to cleanup the arguments here and add the ones we need (op, gid, endpoints (agent), bank, type (write, read, write/read), usrop)
        # napounde - TODO - don't need the agent, register, and field as they are because they aren't used by the existing action
        # Arguments needed:
        #  op - string - required
        #    valid_values: select, select_mask, nop, null, map_usrop, write_read, replace, direct_packet
        #    default_value: direct_packet (this is equivilent of the original stf action)
        #  agent - list
        #    list of string or int (hex, bin)
        #    default_value: none
        #  gid - int
        #    The gid that is to be used for this op
        #    default_value: none
        #  gid_bank - int
        #    The gid_bank that should be used
        #    default_value: 0
        #  usrop - int
        #    The usrop to map, only used in the map_usrop op
        #    default_value: none
        #  reg - string
        #    The name of the register to use in a map_usrop
        #    default_value: none
        #  pid_mask - int
        #    The pid mask to use for mask_select
        #    default_value: none
        #  pid_sel - int
        #    The pid to select during select_mask
        #    default_value: none
        #  write - dict
        #    A dictionary containing all of the field/value pairs to write in this action
        #    default_value: none
        #  read - dict
        #    A dictionary containing all of the field/value pairs to read in this action
        #    default_value: none
        #  num - int
        #    The number of null/nop operations
        #    default_value: 1
        #
        #  incremental_mode - int
        #    History incremental register initilization ena/dis
        #    default_value: 0
        #
        self.arguments.set_argument("source", 1, "Specify which source for this action")
        self.arguments.declare_arg("op", "The STF operation to be completed", [
                                   "select", "select_mask", "nop", "null", "map_usrop", "write_read", "replace", "direct_packet", "stf2mci"], "direct_packet", 1)
        self.arguments.declare_arg(
            "agent", "The agent(s) to talk to specified as a string, int, or list of strings/ints", "string_or_list", "", 0)
        self.arguments.declare_arg(
            "gid", "The group to talk to, specified as an int", "int_or_list", None, 0)
        self.arguments.declare_arg(
            "output_gid", "The output GID for REPLACE packets in inout replace_mode, specified as an int", "int_or_list", None, 0)
        # ticket 4008: per bit strobe on replace op
        # self.arguments.declare_arg(
        #    "output_data", "The output data for REPLACE packets in inout replace_mode, specified as an int", "int","")
        self.arguments.declare_arg(
            "gid_bank", "The gid_bank to program. Only used on select and select_mask", "int_or_list", 0, 0)
        self.arguments.declare_arg(
            "serial_mode", "Description: This parameter should go with select op, it can turn the current grouping cmd's ep list into serial mode, no hub programming needed.",
            ["on", "off"], "off", 0)
        self.arguments.declare_arg(
            "print_group_cmd", "Description: This parameter should go with select op, it can turn off grouping cmd printing in spf file.",
            ["on", "off"], "on", 0)
        self.arguments.declare_arg(
            "select_mode", "Description: this parameter should go with select op, when stf_network == 1, it select options for grouping cmd",
            "string_or_list", "LISTEN_ONLY", 0)
        self.arguments.declare_arg(
            "usrop", "The usrop to map, only used on the map_usrop operation", [1, 2, 3, 4], 1, 0)
        self.arguments.declare_arg(
            "partial_usrop", "If only wanting to map part(s) of a wide register, provide a list of address offsets (e.g. 0: ADDRESS0, 1: ADDRESS 1, etc)", "int_or_list", None, 0)
        self.arguments.declare_arg(
            "reg", "The register to use. Used in map_usrop to specify the register to map the usrop to, also used in write_read to specify the register to write/read", "string", "", 0)
        self.arguments.declare_arg(
            "pid_mask", "The mask to apply during select_mask op", "int", 0, 0)
        self.arguments.declare_arg(
            "pid_sel", "The pid to select during select_mask only. For normal select, use agent", "int", 0, 0)
#        self.arguments.declare_arg("reg_val", "The value of the register in write_read if specifying the whole reg value and not fields", "int", None, 0)
        self.arguments.declare_arg("num", "The number of times to repeat a nop/null", "int", 1, 0)
        self.arguments.declare_arg(
            "incremental_mode", "Specify whether incremental mode is to take place or not", "bool", 0, 0)
        self.arguments.declare_arg("replace_mode", "Specify the mode to generate replace packets in either input or inout", [
                                   "input", "inout"], "input", 0)
        self.arguments.declare_arg(
            "output_iv", "The value of the input valid on the output replace packet. Only used when replace_mode is inout", [0, 1], "")
        self.arguments.declare_arg(
            "output_ov", "The value of the output valid on the output replace packet. Only used when replace_mode is inout", [0, 1], "")
        self.arguments.declare_arg("stf_waitcycles", "Number of nulls to be generated after the current action", "int", 0, 0)

        # Old arguments for direct_packet_mode
        self.arguments.declare_arg(
            "register", "The STF register (name or address) argument used by  agent.register.field access.   ", "string_or_int", "", 0)
        self.arguments.declare_arg(
            "field", "The STF field (name) argument used by  agent.register.field access.   ", "string", "", 0)
        self.arguments.declare_arg(
            "OPCODE", "The STF OPCODE (name) argument used by", "string", "", 0)

        # STF2MCI new arguments
        self.arguments.declare_arg(
            "IR", "The IR that you want to write to the agent", "string", None, 0)
        # self.arguments.declare_arg("agent", "The agent that you want to write to", "string", "", 0)
        self.arguments.declare_arg("DR", "The DR that you want to write", "int", None, 0)
        self.arguments.declare_arg(
            "mci_packet", "The mcipacket that you want to write", "string", None, 0)
        self.arguments.declare_arg(
            "ddr_vector", "The ddr_vector that you want to write", "string", None, 0)
        self.arguments.declare_arg("InstSel", "The Instance of the agent to write", "int", 31, 0)
        # Removing self.arguments.declare_arg("AgentID"         ,"Agent ID","int",13,0 )
        self.arguments.declare_arg("MCI_NOPs", "Send three MCI NOPs thru STF", "int", -1, 0)
        self.arguments.declare_arg("CTL", "Define the controller to be used after an stf2mci conversion", [
                                   "dat", "scan", "sbft", "tap"], "dat", 0)

        # add checking if htd_base_action__current_flow = None, assign an empty hash to stf_gid_track_init
        # this happen when running htd_te_manager.py -cmd_help
        stf_gid_track_init = self._htd_base_action__current_flow.arguments.get_argument('stf_gid_track') if self._htd_base_action__current_flow != None else {}
        self.arguments.declare_arg("stf_gid_track", "note STF endpoint per gid&bank in a dict structure", "dict", stf_gid_track_init, 0)
        self.gid_usage_tracking = self.arguments.get_argument('stf_gid_track')

        # EJSNATIL Rmoving this is on XREG self.arguments.declare_arg("scope", "Define the scope to be used during stf2mci transactions","string",None,0 )
        # STF Direct Packet

        # The bulk of the existing action verify should go here
        # napounde - TODO - probably put this next section into an if statement
        # that is only run if in direct_packet_mode
        if("STF_packet" in list(CFG.keys())):
            if("size" in list(CFG["STF_packet"].keys())):
                if(isinstance(CFG["STF_packet"]["size"], int)):
                    self.size = int(CFG["STF_packet"]["size"])

        # ------Access by OPCODE arguments----------
        if("STF_packet" in list(CFG.keys())):
            if("packet" in list(CFG["STF_packet"].keys())):
                if("OPCODE" in list(CFG["STF_packet"]["packet"].keys()) and "packet_default_values" in list(CFG["STF_packet"].keys())):
                    for packet_field in list(CFG["STF_packet"]["packet"].keys()):
                        self.arguments.declare_arg(packet_field, ("The STF \"%s\" - field argument , used f r direct stf command programming ") % ("opcode or name" if (packet_field not in list(CFG["STF_packet"].keys())) else "opcode"),
                                                   "int" if (packet_field not in list(CFG["STF_packet"].keys())) else "string_or_int", -1, 0)

        self.stf_network = 0
        if("STF_packet" in list(CFG.keys())):
            if("stf_network" in list(CFG["STF_packet"].keys())):
                self.stf_network = CFG["STF_packet"]["stf_network"]

        self.output_auto_en = 1
        if("HPL" in list(CFG.keys())):
            if("STF_output_auto_en" in list(CFG["HPL"].keys())):
                self.output_auto_en = int(CFG["HPL"]["STF_output_auto_en"])

        # Master container for storing all of the operations that need to be done for this action
        self.ops = []

        # Instance variables for easier tracking
        self.agents = []
        self.gid = -1
        self.gid_bank = 0
        self.prev_gids = []
        self.scratchpad_gid = 1
        self.scratchpad_gid_bank = 0
        self.desired_hub_state = {}
        self.stf2mci_mode = False

        if (self.get_curr_flow() is not None):
            self.tracking_key = ("%s_%s") % (htd_base_action.get_action_name(
                self), self.get_curr_flow().get_flow_num())
        else:
            self.tracking_key = ("%s_0") % (htd_base_action.get_action_name(self))
        self.pp = pprint.PrettyPrinter(indent=4)

    def __getstate__(self):
        self.pp = None
        return self.__dict__

    def __setstate__(self, d):
        self.__dict__ = d
        self.pp = pprint.PrettyPrinter(indent=4)

    def get_action_not_declared_argument_names(self): pass

    def verify_arguments(self):
        # TODO: Remove this later once sync_to_modulo_clock is fixed for SPF output on CNL
        self.arguments.set_argument("postalignment", 0)

        # Verify again as different developers may put same action name unintentionaly, so the configuration for latter STF action will overwrite any previous configuration if their action names are same (following current TAP action behaviour)!
        if self.tracking_key in list(stf_action_init_tracking.keys()):
            if (self.arguments.get_argument("op") != "direct_packet" and self.arguments.get_argument("op") != "stf2mci"):
                pass
            else:
                self.arguments.set_argument("postalignment", 0, "STF action restriction")
                self.arguments.set_argument("postdelay", 0, "STF action restriction")

        self.inform(("       Verifying %s::%s:%s:%d ....") % (htd_base_action.get_action_type(self),
                                                              htd_base_action.get_action_name(self),
                                                              htd_base_action.get_action_call_file(
                                                                  self),
                                                              htd_base_action.get_action_call_lineno(self)))

        # -----Verifying needed env-------------
        # napounde - TODO - I'm not sure that we need to force postalignment and
        # postdelay to 0 here, but it isn't hurting anything
        # stang25 - move them upfront for backward compatibility
        #self.arguments.set_argument("postalignment", 0, "STF action restriction")
        #self.arguments.set_argument("postdelay", 0, "STF action restriction")

        self.arguments.print_arguments()

        # napounde - TODO - should check op argument first and verify things based on op argument
        # set op argument to variable self.op for easier access later
        self.op = self.arguments.get_argument("op")

        # Arguments per op
        #  SELECT
        #    required_args: agent(s), gid
        #    optional_args: gid_bank - defaults to 0 otherwise
        #    Additional verification requirements:
        #      -
        #  SELECT_MASK
        #    SELECT = 1 if ((PID ^ SELECT_PID) & ~PID_MASK (agent) == 0) else 0
        #        PID_MASK = 'b1110 (only look at the LSB of the PID)
        #        SELECT_PID (agent) = 'b0001 (only select when the LSB is a 1)
        #
        #        EXAMPLES:
        #        PID = 0101
        #        (0101 ^ ~1110) & 0001 = (0101 ^ 0001) & 0001 = 0100 & 0001 = 0000 (selected)
        #
        #        PID = 0110
        #        (0110 ^ ~1110) & 0001 = (0110 ^ 0001) & 0001 = 0111 & 0001 = 0001 (not selected)
        #
        #
        #    required_args: select_mask, gid, agent (this is the value to select after applying the mask)
        #    optional_args: gid_bank - defaults to 0 otherwise
        #  MAP_USROP
        #    required_args: agent, usrop, reg
        #    optional_args: gid - will use any gid programmed for the specified agents
        #    Additional verification requirements:
        #      - make sure all of the agents specified exist in the gid specified
        #      - if the endpoints listed are not in a common group then an error should be thrown
        #      - if any endpoint listed is not in a group then an error should be thrown
        #      - Need to check how many usrops the specified register needs to be completely written and make sure we have enough usrops available in this register
        #    WRITE_READ
        #      required_args: agent, reg, write_read list with register_field/values
        #      optional_args: gid - will use any gid programmed for the specified agents
        #      Additional verification requirements:
        #        - make sure all of the agents specified exist in the gid specified
        #        - if the gid specified consists of more than just the agent(s) specified a warning/error should be thrown
        #        - if any endpoints listed are not in a common group then an error should be thrown
        #        - if any endpoint listed is not in a group then an error should be thrown
        #        - Verify the registers/fields and lengths are correct for the agent(s) specified
        #    NOP
        #      required_args: num - default to 1
        #      optional_args: agent, gid, num
        #      Either agent(s) or gid is required.
        #    NULL
        #      required_args: num - default to 1
        #    REPLACE
        #      TBD: need to actually fill this in
        #      ???
        #    HUB_MODE
        #      Future expansion to support changing and tracking the hub mode (Normal, Bypass, Series)
        #    HUB_RATIO
        # Future expansion to support changing and tracking the hub ratio -
        # currently we assume a 1:1 ratio

        # Big if statement for each op type
        if (self.op == "select"):
            # SELECT
            # required_args: agent(s), gid

            # Check that agent(s) are supplied
            # Generate the agent list
            self.generate_agent_list(self.arguments.get_argument("agent"))

            # Check the gid
            self.check_gid()

            # Check the select mode
            self.check_select_mode()

            # Get prev_gids if we are deselecting an agent
            self.get_prev_gids()

            self.select_agents(self.agents, self.gid, self.gid_bank, self.select_mode)

        elif (self.op == "select_mask"):
            pass
            # SELECT = 1 if ((PID ^ SELECT_PID) & ~PID_MASK (agent) == 0) else 0
            # PID_MASK = 'b1110 (only look at the LSB of the PID)
            # SELECT_PID (agent) = 'b0001 (only select when the LSB is a 1)

            # EXAMPLES:
            # PID = 0101
            # (0101 ^ ~1110) & 0001 = (0101 ^ 0001) & 0001 = 0100 & 0001 = 0000 (selected)

            # PID = 0110
            # (0110 ^ ~1110) & 0001 = (0110 ^ 0001) & 0001 = 0111 & 0001 = 0001 (not selected)

            # required_args: pid_mask, gid, pid_sel (this is the value to select after applying the mask)
            # optional_args: gid_bank - defaults to 0 otherwise
            # Check that required arguments are provided

            # Call self.get_select_mask_agents(pid_mask, pid_sel) to get a list of
            # agents that will be

            # Call self.select_agents(agent, gid, gid_bank, self.serial_mode) function to generate the select routine

        elif (self.op == "nop"):
            pass
            # required_args: agent
            # Check that required arguments are provided
            self.generate_agent_list(self.arguments.get_argument("agent"))

            # optional_args: gid, num - default to 1
            # Adjust the gid to a list if needed
            if not self.arguments.get_argument("gid") is None:
                self.check_gid(required=0)
            else:
                self.gid = self.common_gid_of_agents(self.agents)

            # will verify if this is a valid agents and gid list
            self.are_agents_in_group(self.agents, self.gid)
            self.check_num_of_repeats()
           # Add info about the nop to self.ops
            self.generate_nops(self.gid, self.num)

        elif (self.op == "null"):
            pass
            # required_args: none
            # Check that required arguments are provided

            # optional_args: num - default to 1
            self.check_num_of_repeats()

            # Add info about the null to self.ops
            self.generate_nulls(self.num)

        elif (self.op == "map_usrop"):
            pass
            # required_args: agent, usrop, reg
            # optional_args: gid - will use any gid programmed for the specified agents
            # Check that the required args are supplied
            self.generate_agent_list(self.arguments.get_argument("agent"))

            # Additional verification requirements:
            #  - make sure all of the agents specified exist in the gid specified
            #  - if the endpoints listed are not in a common group then an error should be thrown
            #  - if any endpoint listed is not in a group then an error should be thrown
            # Adjust the gid to a list if needed
            if not self.arguments.get_argument("gid") is None:
                self.check_gid(required=0)
            else:
                self.gid = self.common_gid_of_agents(self.agents)

            self.are_agents_in_group(self.agents, self.gid)

            # Check that all agents specified have the register specified and that the
            # address is the same
            if (self.arguments.get_argument("reg") == ""):
                self.error("Argument 'reg' is required for map_usrop operation!", 1)

            # Make sure the specified reg exists in all agents at the same address
            reg = self.arguments.get_argument("reg")
            self.check_agents_have_reg(reg)

            # Create ops for mapping the usrops
            self.assign_usrop_to_reg(reg, self.arguments.get_argument("usrop"))

        elif (self.op == "write_read"):
            # required_args: agent, reg, write_read values, read_type (defaults to 0 in basic_action)
            # optional_args: gid - will use any gid programmed for the specified agents
            # Check that the required args are specified
            self.generate_agent_list(self.arguments.get_argument("agent"))

            # Adjust the gid to a list if needed
            if not self.arguments.get_argument("gid") is None:
                self.check_gid(required=0)
            else:
                self.gid = self.common_gid_of_agents(self.agents)

            # Additional verification requirements:
            #     - make sure all of the agents specified exist in the gid specified
            #     - if the gid specified consists of more than just the agent(s) specified a warning/error should be thrown
            #     - if any endpoints listed are not in a common group then an error should be thrown
            #     - if any endpoint listed is not in a group then an error should be thrown
            # Check that all of the agents are in the groups specified or a common
            # group if gid is not specified
            self.are_agents_in_group(self.agents, self.gid)

            # Make sure reg is defined
            if (self.arguments.get_argument("reg") == ""):
                self.error("Argument 'reg' is required for write_read operation!", 1)

            # Make sure the specified reg exists in all agents at the same address
            reg = self.arguments.get_argument("reg")
            self.check_agents_have_reg(reg)

            reg_size = HTD_INFO.stf_info.get_register_size(self.agents[0], reg)
            reg_max_val = int(pow(2, reg_size)) - 1

            # Verify the registers/fields and lengths are correct for the agent(s) specified
            read_vals = {}
            write_vals = {}
            not_declared_args = self.arguments.get_not_declared_arguments()
            # Check reg_val mode
            if "reg_val" in list(not_declared_args.keys()):
                reg_val = self.arguments.get_argument("reg_val")
                for arg in reg_val:
                    # Check the value against the max val
                    if arg.value >= 0:
                        if arg.value > reg_max_val:
                            self.error("Specified register value %d is greater than the max possible value of %d for register %s" % (
                                arg.value, reg_max_val, reg), 1)
                        if self.arguments.get_argument("read_type") == 0:
                            write_vals = self.break_value_into_fields(
                                self.agents[0], reg, arg.value)
                        else:
                            read_vals = self.break_value_into_fields(self.agents[0], reg, arg.value)
                    else:
                        if arg.write_value is not -1:
                            if arg.write_value > reg_max_val:
                                self.error("Specified register write value %d is greater than the max possible value of %d for register %s" % (
                                    arg.write_value, reg_max_val, reg), 1)
                            write_vals = self.break_value_into_fields(
                                self.agents[0], reg, arg.write_value)

                        if arg.read_value is not -1:
                            if arg.read_value > reg_max_val:
                                self.error("Specified register read value %d is greater than the max possible value of %d for register %s" % (
                                    arg.read_value, reg_max_val, reg), 1)
                            read_vals = self.break_value_into_fields(
                                self.agents[0], reg, arg.read_value)

            else:
                # Check Field specification mode
                field_l = HTD_INFO.stf_info.get_register_fields(self.agents[0], reg)
                for field in not_declared_args:
                    for arg in self.arguments.get_argument(field):
                        if arg.lsb < 0 and arg.msb < 0:
                            # Check that field exists
                            if field not in list(field_l.keys()):
                                self.error("Field %s does not exist in register %s" %
                                           (field, reg), 1)

                            msb = HTD_INFO.stf_info.get_field_msb(self.agents[0], reg, field)
                            lsb = HTD_INFO.stf_info.get_field_lsb(self.agents[0], reg, field)
                            fsize = msb - lsb + 1

                            stf_size = 32

                            max_val = int(pow(2, fsize) - 1)
                            # Value check for hexa and binary format
                            if (type(arg.value) in [int] and arg.value > max_val):
                                htdte_logger.error((
                                    "field (%s) value is bigger than it's size: field size: %d bits, max val: 0x%x,  field value: 0x%x") % (field, fsize, max_val, arg.value))
                            elif (isinstance(arg.value, str) and len(str(arg.value)) != stf_size):
                                htdte_logger.error((
                                    "field (%s) value is not the same as it's size: field size: %d bits, field value: 'b%s") % (field, fsize, arg.value))

                            # Read_value check for hexa and binary format
                            if (type(arg.read_value) in [int] and arg.read_value > max_val):
                                htdte_logger.error((
                                    "field (%s) read value is bigger than it's size: field size: %d bits, max val: 0x%x,  field read value: 0x%x") % (field, fsize, max_val, arg.read_value))
                            elif (isinstance(arg.read_value, str) and len(str(arg.read_value)) != stf_size):
                                htdte_logger.error((
                                    "field (%s) read value is not the same as it's size: field size: %d bits, field read value: 'b%s") % (field, fsize, arg.read_value))

                            # Write_value check for hexa and binary format
                            if (type(arg.write_value) in [int] and arg.write_value > max_val):
                                htdte_logger.error((
                                    "field (%s) write_value is bigger than it's size: field size: %d bits, max val: 0x%x,  field write value: 0x%x") % (field, fsize, max_val, arg.write_value))
                            elif (isinstance(arg.write_value, str) and len(str(arg.write_value)) != stf_size):
                                htdte_logger.error((
                                    "field (%s) write_value is not the same as it's size: field size: %d bits, field write value: 'b%s") % (field, fsize, arg.write_value))

                            # Maybe fix it for empty strings
                            if (arg.value >= 0 and arg.value != '') and self.arguments.get_argument("read_type") == 0:
                                write_vals[field] = arg.value
                            elif (arg.value >= 0 and arg.value != '') and self.arguments.get_argument("read_type") == 1:
                                read_vals[field] = arg.value
                            else:
                                if (arg.write_value is not -1 and arg.write_value != ''):
                                    write_vals[field] = arg.write_value

                                if (arg.read_value is not -1 and arg.write_value != ''):
                                    read_vals[field] = arg.read_value

                        else:
                            # Regname[msb:lsb] format
                            msb = HTD_INFO.stf_info.get_register_size(self.agents[0], reg)
                            lsb = 0
                            max_val = int(pow(2, arg.msb - arg.lsb + 1) - 1)
                            if (arg.lsb > msb or arg.msb > msb):
                                htdte_logger.error(("field (%s) sub range (%d:%d) exceed the register boundaries (%d:%d)") % (
                                    field, arg.lsb, arg.msb, lsb, msb))
                            elif (arg.value > max_val):
                                htdte_logger.error(("field (%s[%d:%d]) value is bigger than it's subrange size:%d bits, max val: 0x%x,  field value: 0x%x") % (
                                    field, arg.lsb, arg.msb, arg.lsb - arg.msb + 1, max_val, arg.value))
                            if (arg.read_value > max_val):
                                htdte_logger.error(("field (%s) read value is bigger than it's subrange size: %d bits, max val: 0x%x,  field read value: 0x%x") % (
                                    field, arg.lsb, arg.msb, arg.lsb - arg.msb + 1, max_val, arg.read_value))
                            if (arg.write_value > max_val):
                                htdte_logger.error(("field (%s) write value is bigger than it's subrange size: %d bits, max val: 0x%x,  field write value: 0x%x") % (
                                    field, arg.lsb, arg.msb, arg.lsb - arg.msb + 1, max_val, arg.write_value))

                            if arg.value >= 0 and self.arguments.get_argument("read_type") == 0:
                                write_vals = self.adjust_msb_lsb_to_field(
                                    self.agents[0], reg, field, arg.msb, arg.lsb, arg.value, write_vals)
                            elif arg.value >= 0 and self.arguments.get_argument("read_type") == 1:
                                read_vals = self.adjust_msb_lsb_to_field(
                                    self.agents[0], reg, field, arg.msb, arg.lsb, arg.value, read_vals)
                            else:
                                if (arg.write_value is not -1):
                                    write_vals = self.adjust_msb_lsb_to_field(
                                        self.agents[0], reg, field, arg.msb, arg.lsb, arg.write_value, write_vals)

                                if (arg.read_value is not -1):
                                    read_vals = self.adjust_msb_lsb_to_field(
                                        self.agents[0], reg, field, arg.msb, arg.lsb, arg.read_value, read_vals)

                # Handle incremental mode of the other fields
                # Loop over all fields and assign the ones that aren't already assigned,
                # or at least save them in the history
                for field in list(field_l.keys()):
                    # If this field is already in write_vals continue
                    if field in list(write_vals.keys()):
                        continue

                    cur_val = self.get_incremental_or_default_value(self.agents[0], reg, field)
                    if (self.arguments.get_argument("incremental_mode") == 1):
                        write_vals[field] = cur_val
                        # no change to the history
                    else:
                        # History is changing and we should record that this field now how the
                        # default value
                        for agent in self.agents:
                            htd_history_mgr.history_capture(
                                self, [agent, reg], {field: cur_val}, container_type=self.history_container, save_non_arg_data=1)

            # TODO: Figure out the USROP stuff (usrop op type needs to be complete first)
            # Check if this register is aliased to USROP(s) and get the corresponding usrop sequence
            # can use get_usrop_sequence to determine this sequence

            # Store the write in self.ops
            # This function also saves the write values in the history
            self.write_field_values(self.agents, self.gid, reg, write_vals, read_vals)

        elif (self.op == "replace"):
            # required_args: agent
            # Check that required arguments are provided
            self.generate_agent_list(self.arguments.get_argument("agent"))

            # optional_args: gid, num - default to 1
            # Adjust the gid to a list if needed
            if not self.arguments.get_argument("gid") is None:
                self.check_gid(required=0)
            else:
                self.gid = self.common_gid_of_agents(self.agents)
                # It will error out f a common single gid is not found or there are more
                # agents matching that gid than the list provided

            if not self.arguments.get_argument("output_gid") is None:
                self.output_gid = self.arguments.get_argument("output_gid")

            self.replace_mode = self.arguments.get_argument("replace_mode")
            if (self.replace_mode == "input"):
                self.output_data = ""
            else:
                # ticket 4008: per bit strobe on replace op
                # init output_data to 32 bits of X
                self.output_data = 32 * "X"

                for tmp_input in self.arguments.get_argument("output_data"):
                    tmp_msb = tmp_input.msb
                    tmp_lsb = tmp_input.lsb
                    
                    if (tmp_msb == -1 or tmp_lsb == -1):
                        tmp_value = bin(tmp_input.value)[2:][::-1]
                        self.output_data = bin(tmp_input.value)[2:][::-1] + self.output_data[len(bin(tmp_input.value)[2:]):]
                    else:
                        tmp_len = tmp_msb - tmp_lsb + 1
                        tmp_value = bin(tmp_input.value)[2:].zfill(tmp_len)[::-1]  # strip 0b, zero fill and reverse

                        self.output_data = self.output_data[:tmp_lsb] + tmp_value + self.output_data[tmp_msb + 1:]

                self.output_data = self.output_data[::-1]

            if not self.arguments.get_argument("output_iv") is None:
                self.output_iv = self.arguments.get_argument("output_iv")
            if not self.arguments.get_argument("output_ov") is None:
                self.output_ov = self.arguments.get_argument("output_ov")

            self.replace_mode = self.arguments.get_argument("replace_mode")
            self.inform("replace mode is : %s" % (self.replace_mode))

            # will verify if this is a valid agents and gid list
            self.are_agents_in_group(self.agents, self.gid)
            # checks to see if arg "num" is > 0 if it is defined
            self.check_num_of_repeats()
            # Add info about the nop to self.ops
            self.generate_replace(self.gid, self.num)

        # if the opcode is "direct_packet", build stf data and strobes to be sent in run()
        elif (self.op == "direct_packet"):

            # -----------------

            self.inform("OPCODE = %s" % (self.arguments.get_argument("OPCODE")))
            if(self.arguments.get_argument("OPCODE") != -1):
                self.direct_packet_mode = True
                for packet_field in list(CFG["STF_packet"]["packet"].keys()):

                    if(packet_field not in list(self.direct_packet.keys())):
                        self.direct_packet[packet_field] = {}

                    # ---Extract msb and lsb of field
                    match = re.match(r"(\d+)\s*:(\d+)", CFG["STF_packet"]["packet"][packet_field])

                    if(not match):
                        self.error(("Action's (%s) : Wrong packet definition value found for field: \"%s\" in TE_cfg.xml definition .(Expected format is: \"<lsb>:<msb>\", while found - \"%s\"") % (
                            self.__action_name__, packet_field, CFG["STF_packet"]["packet"][packet_field]), 1)

                    self.direct_packet[packet_field]["lsb"] = int(match.groups()[0])
                    msb = int(match.groups()[1])

                    if (msb < self.direct_packet[packet_field]["lsb"]):
                        self.direct_packet[packet_field][
                            "msb"] = self.direct_packet[packet_field]["lsb"]
                        self.direct_packet[packet_field]["lsb"] = msb
                        msb = self.direct_packet[packet_field]["msb"]
                    else:
                        self.direct_packet[packet_field]["msb"] = msb

                    if (msb >= self.size):
                        self.error(("Action's (%s) : Wrong packet definition range found for field: \"%s\" in TE_cfg.xml definition .([%s] - Exceed packet size-%d)") % (
                            self.__action_name__, packet_field, CFG["STF_packet"]["packet"][packet_field], self.size), 1)

                    # --Packet field not given in arguments- taking default from CFG["STF_packet"]["packet_default_values"]
                    if(self.arguments.get_argument(packet_field) == -1):
                        if(packet_field not in list(CFG["STF_packet"]["packet_default_values"].keys())):
                            self.error(("Action's (%s) : Missing packet \"%s\"-field argument (havn't default assignment in CFG[\"STF_packet\"][\"packet\"] table in TE_cfg.xml definition .(Used to define a STF direct packet access") % (
                                self.__action_name__, packet_field), 1)
                        (isInt, val) = util_get_int_value(
                            CFG["STF_packet"]["packet_default_values"][packet_field])
                        if(not isInt):
                            self.error(("Action's (%s) : Wrong %s field value type found in opcode table- %s, expected digital format.  .(Used to define a STF direct packet access") % (
                                self.__action_name__, packet_field, CFG["STF_packet"][packet_field]), 1)
                        self.direct_packet[packet_field]["val"] = val
                    else:
                        # ---Packet field given in arguments
                        if(isinstance(self.arguments.get_argument(packet_field), int)):
                            self.direct_packet[packet_field][
                                "val"] = self.arguments.get_argument(packet_field)
                        else:
                            if(packet_field not in list(CFG["STF_packet"].keys())):
                                self.error(("Action's (%s) : Trying to assign field (%s) by enumerated string: %s=\"%s\"  ,\
                                 while missing field enumeration table in TE_cfg.xml: CFG[\"STF_packet\"][\"%s\"] definition .(Used to define a STF direct packet access)") % (self.__action_name__,
                                                                                                                                                                               packet_field, packet_field, self.arguments.get_argument(packet_field)), 1)
                            if(self.arguments.get_argument(packet_field) not in list(CFG["STF_packet"][packet_field].keys())):
                                self.error(("Action's (%s) : Trying to assign field by illegal enumerated string: %s=\"%s\". Available field enumerations are:%s") % (
                                    self.__action_name__, packet_field, self.arguments.get_argument(packet_field), str(list(CFG["STF_packet"][packet_field].keys()))), 1)
                            (isInt, val) = util_get_int_value(CFG["STF_packet"][
                                packet_field][self.arguments.get_argument(packet_field)])
                            if(not isInt):
                                self.error(("Action's (%s) : Wrong %s field value type found in opcode table- %s, expected digital format.  .(Used to define a STF direct packet access") % (
                                    self.__action_name__, packet_field, CFG["STF_packet"][packet_field][self.arguments.get_argument(packet_field)]), 1)
                            self.direct_packet[packet_field]["val"] = val

                    if(self.direct_packet[packet_field]["val"] > pow(2, (self.direct_packet[packet_field]["msb"] - self.direct_packet[packet_field]["lsb"] + 1)) - 1):
                        self.error(("Action's (%s) : Wrong %s field value - 0x%x given in parameters:Exceed field width limit-%d (max value-0x%x)") % (self.__action_name__, packet_field,
                                                                                                                                                       (self.direct_packet[packet_field][
                                                                                                                                                        "msb"] - self.direct_packet[packet_field]["lsb"] + 1),
                                                                                                                                                       pow(2, (self.direct_packet[packet_field]["msb"] - self.direct_packet[packet_field]["lsb"] + 1)) - 1), 1)
                    if("packet_default_strobe" not in list(CFG["STF_packet"].keys())):
                        self.error(
                            ("Action's (%s) : Missing default strobe assignment for a STF packet <field>=\"1\" - to be strobbed .") % (self.__action_name__), 1)
        elif (self.op == "stf2mci"):
            self.stf2mci_mode = True

            agents = HTD_INFO.tap_info.get_tap_agents()

            self.mci_packts = []
            MCI_NOP = "100000000000000000000"  # MCI DAT NOP
            data_by_field = {}

            for reg_type in list(HTD_INFO.RegAccInfo.keys()):
                if("regSpace" in list(HTD_INFO.RegAccInfo[reg_type]["RegAccInfoProperties"].keys())):
                    self.regSpace = HTD_INFO.RegAccInfo[reg_type][
                        "RegAccInfoProperties"]["regSpace"]

            if(self.arguments.get_argument("MCI_NOPs") > 0):
                if(self.arguments.get_argument("agent") not in agents):
                    self.error(("There's not %s defined in tap specs") %
                               (self.arguments.get_arguments("agent")))

                for i in range(0, self.arguments.get_argument("MCI_NOPs")):
                    self.mci_packts.append(MCI_NOP)
                while (len(self.mci_packts) % 3 != 0):
                    self.mci_packts.append(MCI_NOP)

            elif(self.arguments.get_argument("DR") is not None and self.arguments.get_argument("CTL") == "sbft"):
                # SBFT agent doesn't have a controller, meaning that not MCI encoding is defined
                self.error("There's not MCI encoding defined for SBFT")
            elif(self.arguments.get_argument("DR") is not None and self.arguments.get_argument("CTL") == "scan"):
                # To be developed.
                self.error("Scan controller is not supported yet")
            elif(self.arguments.get_argument("DR") is not None and self.arguments.get_argument("CTL") == "dat"):
                DR = str(self.arguments.get_argument("DR"))[::-1]
                self.cr_address = DR[36:47]
                self.cr_address = (30 - len(self.cr_address)) * "0" + self.cr_address[::-1] + "00"
                self.cr_data = DR[4:36]
                self.cr_data = self.cr_data[::-1]

                DATA_CMD = "1"

                # Address - MCI pkt 1
                Opcode = "0001"
                MCI_Packet = DATA_CMD + Opcode + self.cr_address[16:len(self.cr_address)]
                self.mci_packts.append(MCI_Packet)

                # Address - MCI pkt 2
                Opcode = "0010"
                MCI_Packet = DATA_CMD + Opcode + self.cr_address[0:16]
                self.mci_packts.append(MCI_Packet)

                # NOP
                self.mci_packts.append(MCI_NOP)

                # DATA - MCI pkt 1
                Opcode = "1000"
                MCI_Packet = DATA_CMD + Opcode + self.cr_data[16:len(self.cr_data)]
                self.mci_packts.append(MCI_Packet)

                # DATA - MCI pkt 2
                Opcode = "0000"
                MCI_Packet = DATA_CMD + Opcode + self.cr_data[0:16]
                self.mci_packts.append(MCI_Packet)

                # NOP
                self.mci_packts.append(MCI_NOP)

            elif(self.arguments.get_argument("reg") is not None and self.arguments.get_argument("CTL") == "dat"):

                if (self.arguments.get_argument("scope")):
                    scope_list = HTD_INFO.cr_info.get_matching_crs_by_name(
                        str(self.arguments.get_argument("reg")), self.regSpace, self.arguments.get_argument("scope"))
                else:
                    scope_list = [""]
                for scope in scope_list:
                    (reginfo, regfile) = HTD_INFO.cr_info.get_cr_info_by_name(
                        self.arguments.get_argument("reg"), self.regSpace, scope, 1)
                    self.cr_address = self.get_reg_address(
                        self.arguments.get_argument("reg"), self.regSpace, scope)

                    self.cr_data = self.get_reg_bin_data(
                        reginfo, self.arguments.get_argument("reg"), self.regSpace, regfile)
                    self.cr_data = self.cr_data[::-1]

                    DATA_CMD = "1"

                    # Address - MCI pkt 1
                    Opcode = "0001"
                    MCI_Packet = DATA_CMD + Opcode + self.cr_address[16:len(self.cr_address)]
                    self.mci_packts.append(MCI_Packet)

                    # Address - MCI pkt 2
                    Opcode = "0010"
                    MCI_Packet = DATA_CMD + Opcode + self.cr_address[0:16]
                    self.mci_packts.append(MCI_Packet)

                    # NOP
                    self.mci_packts.append(MCI_NOP)

                    # DATA - MCI pkt 1
                    Opcode = "1000"
                    MCI_Packet = DATA_CMD + Opcode + self.cr_data[16:len(self.cr_data)]
                    self.mci_packts.append(MCI_Packet)

                    # DATA - MCI pkt 2
                    Opcode = "0000"
                    MCI_Packet = DATA_CMD + Opcode + self.cr_data[0:16]
                    self.mci_packts.append(MCI_Packet)

                    # NOP
                    self.mci_packts.append(MCI_NOP)

            elif(self.arguments.get_argument("DR") is not None and self.arguments.get_argument("CTL") == "tap"):
                # MCI CMD PACKET - Not fully tested
                if(self.arguments.get_argument("agent") not in agents):
                    self.error(("There's not %s defined in tap specs") %
                               (self.arguments.get_arguments("agent")))

                self.ir = HTD_INFO.tap_info.get_ir_opcode_string(
                    self.arguments.get_argument("IR"), self.arguments.get_argument("agent"))

                IR = self.arguments.get_argument("IR")
                DR = self.arguments.get_argument("DR")
                agent = self.arguments.get_argument("agent")

                # Get full IR size:
                fields = HTD_INFO.tap_info.get_ir_fields(IR, agent)
                size = 0
                for field in fields:
                    size += HTD_INFO.tap_info.get_field_msb(IR, agent, field) - \
                        HTD_INFO.tap_info.get_field_lsb(IR, agent, field) + 1

                DR_Str = str(DR)
                # Fix ScanD size
                Pad_Dr = size - len(str(DR))
                DR_Str = (Pad_Dr * "0") + DR_Str

                #Agent_ID = "01101"
                AgentID = self.arguments.get_argument("AgentID")
                Agent_ID = str(bin(AgentID))
                Agent_ID = Agent_ID.replace("0b", "")
                Pad_Agent = 5 - len(Agent_ID)
                Agent_ID = (Pad_Agent * "0") + Agent_ID
                InstSel = self.arguments.get_argument("InstSel")

                InstSel_Str = str(bin(InstSel))
                InstSel_Str = InstSel_Str.replace("0b", "")

                Pad_Dr = 5 - len(InstSel_Str)
                InstSel_Str = (Pad_Dr * "0") + InstSel_Str

                # 1st MCI packet =
                DATA_CMD = "0"
                EOC = "1"
                Opcode = self.ir
                Pad_Dr = 9 - len(str(Opcode))
                Opcode = (Pad_Dr * "0") + Opcode

                MCI_Packet = str(DATA_CMD + EOC + Opcode + InstSel_Str + Agent_ID)
                self.mci_packts.append(MCI_Packet)

                # Increasing Size of the DR to match MCI Packt
                while (len(DR_Str) % 19 != 0):
                    DR_Str = "0" + DR_Str

                mci_packts_temp = []
                while (len(DR_Str) > 0):
                    DATA = DR_Str[0:19]
                    DR_Str = DR_Str[19:len(DR_Str)]
                    MCI_Packet = DATA_CMD + EOC + DATA
                    mci_packts_temp.append(MCI_Packet)

                # Adding EOC:
                temp_str = mci_packts_temp[0]
                temp_str = temp_str[:1] + "0" + temp_str[2:]
                mci_packts_temp[0] = temp_str

                mci_packts_temp.reverse()

                for MCI_PACK in mci_packts_temp:
                    self.mci_packts.append(MCI_PACK)

                while (len(self.mci_packts) % 3 != 0):
                    self.mci_packts.append(MCI_NOP)

            elif(self.arguments.get_argument("mci_packet") is not None):
                mci_pkt = bin(int(self.arguments.get_argument("mci_packet"), 16))
                mci_pkt = mci_pkt.replace("0b", "")
                self.mci_packts.append(mci_pkt)
            elif(self.arguments.get_argument("ddr_vector") is not None):
                self.mci_packts.insert(self.arguments.get_argument("0000000"))
                self.mci_packts.insert(self.arguments.get_argument("0000001"))
                self.mci_packts.insert(self.arguments.get_argument("0000002"))

            else:
                self.error("Wrong arguments for stf2mci definition")

        else:
                # ERROR
            self.error(("Action's (%s) : The op chosen (%s) is invalid") %
                       (self.__action_name__, self.op), 1)

        self.check_stf_waitcycles()

        stf_action_init_tracking[self.tracking_key] = self.ops

    # ------------------------------------------
    #
    # -------------------------------
    def run(self):
        # FIXME - add actual action execution
        self.inform(("     Running %s::%s:%s:%d \n\n") % (
            htd_base_action.get_action_type(self),
            htd_base_action.get_action_name(self),
            htd_base_action.get_action_call_file(self),
            htd_base_action.get_action_call_lineno(self)))

        # Restore ops
        self.ops = stf_action_init_tracking[self.tracking_key]

        if(self.direct_packet_mode):
            final_data = 0
            strobes = {}  # range assigned by user arguments key-lsb, val-msb
            for field in list(self.direct_packet.keys()):
                final_data = final_data | (self.direct_packet[field][
                                           "val"] << self.direct_packet[field]["lsb"])
                if(field in list(CFG["STF_packet"]["packet_default_strobe"].keys()) and CFG["STF_packet"]["packet_default_strobe"][field] > 0 and self.arguments.get_argument("read_type")):
                    field_read_l = list(util_int_to_binstr(final_data, self.direct_packet[
                                        field]["msb"] - self.direct_packet[field]["lsb"] + 1))

                    for i in range(self.direct_packet[field]["lsb"], self.direct_packet[field]["msb"] + 1):
                        if(field_read_l[i - self.direct_packet[field]["lsb"]] == '1'):
                            strobes[i] = "H"
                        else:
                            strobes[i] = "L"

            # ----------------------------
            if(self.arguments.get_argument("read_type")):
                htdPlayer.hpl_to_dut_interface.StfITPPPacket(self.size, 0, final_data, strobes)
            else:
                htdPlayer.hpl_to_dut_interface.StfITPPPacket(self.size, final_data, 0)

        elif(self.stf2mci_mode):
            # STF_STF2MCI_REG Control
            params = {}
            params['OPCODE'] = 0xA
            params['op'] = "direct_packet"
            params['GID'] = self.arguments.get_argument("GID")
            params['agent'] = self.arguments.get_argument("agent")
            params['DATA'] = 0b0010000
            self.get_curr_flow().exec_action(params, "STF", self.__class__.__name__, 0, self.get_action_name())
            # Pack MCI into 3s
            counter_packts = 0
            stf_pack = ""
            params = {}
            params['OPCODE'] = 0xB
            params['op'] = "direct_packet"
            params['GID'] = self.arguments.get_argument("GID")
            for index, mci_pack in enumerate(self.mci_packts):
                counter_packts = counter_packts + 1
                self.get_curr_flow().exec_action({"op": "PCOMMENT", "strvalue": "MCI_PKT" + str(
                    index) + " " + str(mci_pack)}, "GEN", self.__class__.__name__, 0, self.get_action_name())
                mci_pack = mci_pack[::-1]

                for bit in mci_pack:
                    stf_pack = bit + stf_pack
                    if(len(stf_pack) == self.size - 10):
                        params['DATA'] = int(stf_pack, 2)
                        self.get_curr_flow().exec_action(params, "STF", self.__class__.__name__, 0, self.get_action_name())
                        stf_pack = ""

                if(counter_packts == 3):
                    Pad_stf = (self.size - 10) - len(str(stf_pack))
                    stf_pack = (Pad_stf * "0") + stf_pack
                    params['DATA'] = int(stf_pack, 2)
                    self.get_curr_flow().exec_action(params, "STF", self.__class__.__name__, 0, self.get_action_name())
                    stf_pack = ""
                    counter_packts = 0

            if(len(stf_pack) > 0):
                Pad_stf = (self.size - 10) - len(str(stf_pack))
                stf_pack = (Pad_stf * "0") + stf_pack
                params['DATA'] = int(stf_pack, 2)
                self.get_curr_flow().exec_action(params, "STF", self.__class__.__name__, 0, self.get_action_name())

        else:
            # Loop over self.ops and have if statements for each op type
            n = 0
            for op in self.ops:
                if (op["op"] == "select"):
                    serial_mode = self.arguments.get_argument("serial_mode")
                    select_mode = ""

                    if len(self.ops) == 1 or not self.stf_network:
                        print_group_cmd = self.arguments.get_argument("print_group_cmd")
                    else:  # stf program grouping is turn on
                        # if there is more than 1 op(list), print at the last op
                        if n == (len(self.ops) - 1):
                            print_group_cmd = "on"
                        else:
                            print_group_cmd = "off"
                            n += 1

                    if self.stf_network:
                        select_mode = op["select_mode"]
                        self.update_gid_tracking(op["gid"], op["gid_bank"], op["agent"], select_mode)
                    htdPlayer.hpl_to_dut_interface.stf_select(
                        op["gid"], op["gid_bank"], serial_mode, print_group_cmd, select_mode,  op["agent"], self.gid_usage_tracking, op["comment"])
                elif (op["op"] == "select_mask"):
                    pass
                    # call htdPlayer.hpl_to_dut_interface.stf_select_mask(pid_mask)
                elif (op["op"] == "nop"):
                    pass
                    htdPlayer.hpl_to_dut_interface.stf_nop(op["gid"], (op["num"] - 1))
                elif (op["op"] == "null"):
                    pass
                    # Should always send a GID of 0
                    htdPlayer.hpl_to_dut_interface.stf_nop(0, (op["num"] - 1))
                elif (op["op"] == "map_usrop"):
                    # call htdPlayer.hpl_to_dut_interface.stf_map_usrop(agent, usrop, gid,
                    # reg, address_field)
                    htdPlayer.hpl_to_dut_interface.stf_map_usrop(
                        op["agents"], op["gids"], op["usrops_to_program"])

                elif (op["op"] == "write_read"):
                    # op should have the following keys
                    #     op - The type of operation
                    #     agent - the agent(s) name
                    #     gid - the gid to write to
                    #     write_by_field - dict of fields and values
                    #     read_by_field - dict of fields and values
                    #     capture - FUTURE SUPPORT
                    #     mask - FUTURE SUPPORT

                    # Can be multiple agents
                    #htdPlayer.hpl_to_dut_interface.stf_write_read(agent, gid, write_by_field, read_by_field, comment, capture, mask, usrop_seq, data_seq);
                    htdPlayer.hpl_to_dut_interface.stf_write_read(op["agent"], op["gid"], op["reg"], op.get(
                        "write_by_field", None), op.get("read_by_field", None), comment=op.get("comment", ""))
                elif (op["op"] == "replace"):
                    self.inform("Replace bits - mode: {} gid: {} gid2: {} data2: {} num: {} iv: {} ov: {}".format(op["mode"], op["gid"], op["gid2"], op["data2"], op["num"], op["iv"], op["ov"]))
                    htdPlayer.hpl_to_dut_interface.stf_replace(op["mode"], op["gid"], op["gid2"], op[
                                                               "data2"], op["num"], op["iv"], op["ov"])
                    # call htdPlayer.hpl_to_dut_interface.stf_select_mask(pid_mask)
                elif (op["op"] == "comment"):
                    htdPlayer.hpl_to_dut_interface.stf_print_comment(op.get("comment", ""))
                else:
                    # ERROR
                    self.error(("Action's (%s) : The op chosen (%s) is invalid") %
                               (self.__action_name__, self.op), 1)

    def debug_readback(self): pass

    # Additional functions to write
    def generate_agent_list(self, agent_to_check):
        if (agent_to_check):
            if (isinstance(agent_to_check, str) and "," not in agent_to_check):
                # Make sure the stop exists
                HTD_INFO.stf_info.has_stop(agent_to_check, throwError=True)
                self.agents.append(agent_to_check)
            elif (isinstance(agent_to_check, int)):
                agent_name = HTD_INFO.stf_info.get_stop_name_by_pid(agent_to_check)
                if (not HTD_INFO.stf_info.has_stop(agent_name)):
                    self.error("There is not agent specified by pid %d" % (agent_to_check), 1)
                self.agents.append(agent_name)
            elif (isinstance(agent_to_check, str) and "," in agent_to_check):
                agents_lst = agent_to_check.split(",")
                for agent in agents_lst:
                    if agent in self.agents:
                        self.inform(
                            "Agent %s was specified multiple times, only using the first." % (agent))
                        continue
                    self.agents.append(agent)
            elif (isinstance(agent_to_check, list)):
                self.agents = agent_to_check
            else:
                self.error(("Agent specified %s is not a string, int, or list of strings/ints!" % agent_to_check), 1)

    def check_gid(self, required=1):
        # Check that a gid is supplied
        if (self.arguments.get_argument("gid") is None and required):
            self.error("Argument gid is required for op type %s! Please specify a gid value" % (self.op), 1)
        elif (self.arguments.get_argument("gid") == self.scratchpad_gid):
            self.error("GID has been specified to be %d! This GID is used as a scratchpad to help during programming the network. Please specify a different gid." % (
                self.scratchpad_gid), 1)
        else:
            # Do some checking and expand into a list to match the length of the agents list
            self.gid = self.arguments.get_argument("gid")
#            self.gid_bank = self.arguments.get_argument("gid_bank")
            if isinstance(self.gid, int):
                temp_gid = self.gid
                self.gid = [temp_gid] * len(self.agents)

            # Check to make sure self.gid is the right length
            if len(self.gid) != len(self.agents):
                self.error("The number of gids provided (%d) does not match the number of agents provided (%d)!" % (
                    len(self.gid), len(self.agents)), 1)

            # Check for gid_bank
            self.gid_bank = self.arguments.get_argument("gid_bank")
            if type(self.gid_bank) is int:
                if not self.gid_bank in [0, 1]:
                    self.error("The provided gid_bank %s is not valid! List of allowed gid bank are [0, 1]." % (self.gid_bank), 1)
                temp_gid_bank = self.gid_bank
                self.gid_bank = [temp_gid_bank] * len(self.agents)

            if len(self.gid_bank) != len(self.agents):
                self.error("The number of gid_banks provided (%d) does not match the number of agents provided (%d)!" % (
                    len(self.gid_bank), len(self.agents)), 1)
        # Check that a gid is supplied

    def check_select_mode(self):
        # check the select_mode
        if self.arguments.get_argument("select_mode") is None:
            self.select_mode = ["LISTEN_ONLY"] * len(self.agents)
        else:
            # Do some checking and expand into a list to match the length of the agents list
            self.select_mode = self.arguments.get_argument("select_mode")
            if type(self.select_mode) is str:
                self.is_mode_valid(self.select_mode)
                self.select_mode = [self.select_mode] * len(self.agents)
            elif type(self.select_mode) is list:
                for select_mode in self.select_mode:
                    self.is_mode_valid(select_mode)
            if len(self.select_mode) != len(self.agents):
                self.error("The number of select_mode provided (%d) does not match the number of agents provided (%d)!" % (
                    len(self.select_mode), len(self.agents)), 1)
            if len(self.select_mode) > 1 and "RESET_STF_NETWORK" in self.select_mode:
                    self.error("Should not use RESET_STF_NETWORK select mode for complex group setup!", 1)

    def is_mode_valid(self, mode):
        if mode in valid_select_modes:
            return
        else:
            self.error("The provided select_mode %s is not valid! List of allowed mode are %s." % (mode, valid_select_modes), 1)

    def get_gid_bank_key(self, gid_bank):
        return "bank%d" % (gid_bank)

    def update_gid_tracking(self, gid, gid_bank, agent, select_mode):
        #gid = self.gid[0]
        #gid_bank = self.gid_bank[0]
        if (select_mode == "RESET_STF_NETWORK"):
	    # the gid_usage_tracking has the following structure, gid : list of modes: with gid bank0 & 1
            for group_id in range(0, 16):
                for mode in valid_select_modes:
                    for bank_num in range(0,2):
                        if (mode != "RESET_STF_NETWORK"):
                            prev_endpoints = self.gid_usage_tracking[group_id][mode].get(bank_num, [])
                            del prev_endpoints[:]
        else:
            if gid == 0:
                # loop through self.gid_usage_tracking hash, remove endpoint from that list
                for group_id in range(1, 16):
                    prev_endpoints = self.gid_usage_tracking[group_id][select_mode].get(gid_bank, [])
                    if agent in prev_endpoints:
                        prev_endpoints.remove(agent)
            else:
                # remove any agent in gid0
                prev_agents = self.gid_usage_tracking[gid][select_mode].get(gid_bank, [])
                if agent in prev_agents:
                    pass  #do nothing
                else:
                    for m in valid_select_modes:
                        if (m != "RESET_STF_NETWORK"):
                            temp_prev_agents = self.gid_usage_tracking[gid][m].get(gid_bank, [])
                            if agent in temp_prev_agents:
                                temp_prev_agents.remove(agent)
                    prev_agents = prev_agents.append(agent)

    def get_prev_gids(self):

        for (i, agent) in enumerate(self.agents):
            gid_bank = self.gid_bank[i]
            gid = self.gid[i]

            # Check if this is a deselect
            if gid == 0:
                # Check that this bank is currently programmed to something other than 0
                bank_key = self.get_gid_bank_key(gid_bank)
                if not htd_history_mgr.history_has(self, [agent, "GID"], bank_key, container_type=self.history_container):
                    self.error("Trying to deselect agent %s on GID bank %d, but that GID bank is already unprogrammed!" % (
                        agent, gid_bank), 1)

                bank_gid = htd_history_mgr.history_get(
                    self, [agent, "GID"], bank_key, container_type=self.history_container)
                self.prev_gids.append(bank_gid)
            else:
                self.prev_gids.append(0)

    # Function to take a gid and a list of agents and check the agent_list against all agents currently in group (gid).
    # Pass conditions:
    #     GID contains all of the agents specified and no others
    #     return 1
    # Error conditions:
    #     Any agents in list are not in gid
    #     GID group has one or more agents not in the agent list
    #     return 0
    def are_agents_in_group(self, agent_list, gid):
        pass
        if (isinstance(gid, int)):
            self.error("There are more than one gids in common with this list of agents.", 1)
        elif (self.gid_list_and_agents_match(agent_list, gid)):
            pass
            # Search gid list to see if all agents are in this gid
            self.gid = gid
        else:
            self.error("Look at previous errors", 1)
        # use agents_in_group(gid)

    # Function to take a gid and return a list of agents currently assigned to that gid
    # return:
    #     list of agents belonging to gid
    def agents_in_group(self, gid):
        pass
        return htd_history_mgr.history_get(self, ["GID"], gid, container_type=self.history_container)

    # Function to get current gids associated with an agent
    def gids_for_agent(self, agent):
        # use htd_history_mgr.history_has(self, [agent, "GID"], container_type=self.history_container) -> checks if this agent has any GID history
        # returns the stored GIDs for this agent {"gid0":<gid>, "gid1":<gid>}
        if htd_history_mgr.history_has(self, [agent, "GID"], container_type=self.history_container):
            return htd_history_mgr.history_get(self, [agent, "GID"], container_type=self.history_container)
        else:
            self.error("Agent %s is not currently programmed into any Groups!" % (agent), 1)

    # Function to assign gid to agent (along with the bank) for tracking purposes
    #
    # Saves the GID in the history two ways
    #   1. history-><agent>->"GID"->bank0/1-><gid>
    #   2. history->"GID"->0,1,2,3,4...->[agent1, agent2, ...]
    def assign_gid_to_agent(self, gid, agent, bank, prev_gid, select_mode="LISTEN_ONLY"):
        self.ops.append({"op": "select", "agent": agent, "gid": gid,
                         "gid_bank": bank, "select_mode": select_mode, "comment": "Configure %s" % (agent)})

        # use htd_history_mgr.history_capture(self, [agent, "GID"], "bank%d"%(bank), gid, container_type=self.history_container) to save GID in history
        #
        # Be sure to remove agents from this list when they are reassigned to group 0
        bank_key = self.get_gid_bank_key(bank)
        opp_bank = 1 if bank == 0 else 0
        opp_bank_key = self.get_gid_bank_key(opp_bank)
        if (gid != 0):
            if htd_history_mgr.history_has(self, ["GID"], gid, container_type=self.history_container):
                agent_list = htd_history_mgr.history_get(
                    self, ["GID"], gid, container_type=self.history_container)
            else:
                agent_list = []
            if agent not in agent_list:
                agent_list.append(agent)
            htd_history_mgr.history_capture(
                self, ["GID"], {gid: agent_list}, container_type=self.history_container, save_non_arg_data=1)

            # Check the opposite bank as well and make sure something is saved there

            if not htd_history_mgr.history_has(self, [agent, "GID"], opp_bank_key, container_type=self.history_container):
                htd_history_mgr.history_capture(
                    self, [agent, "GID"], {opp_bank_key: 0}, container_type=self.history_container, save_non_arg_data=1)

        htd_history_mgr.history_capture(
            self, [agent, "GID"], {bank_key: gid}, container_type=self.history_container, save_non_arg_data=1)

        if (prev_gid != 0):
            gids = self.gids_for_agent(agent)

            if (bank_key in gids and opp_bank_key in gids and gids[bank_key] != gids[opp_bank_key]) or (bank_key not in gids or opp_bank_key not in gids):
                if htd_history_mgr.history_has(self, ["GID"], prev_gid, container_type=self.history_container):
                    agent_list = htd_history_mgr.history_get(
                        self, ["GID"], prev_gid, container_type=self.history_container)
                    agent_list.remove(agent)
                else:
                    agent_list = []
                htd_history_mgr.history_capture(
                    self, ["GID"], {prev_gid: agent_list}, container_type=self.history_container, save_non_arg_data=1)

    # This function is used when no gid list is provided - it will find the
    # common gid of a list of agents and it will return a list of that gid
    def common_gid_of_agents(self, agent_list):
        gid_in_common = False
        count = False
        agent_with_gids = {}
        for agent in agent_list:
            bank_and_gid = self.gids_for_agent(agent)
            agent_with_gids[agent] = [bank_and_gid.get("bank0"), bank_and_gid.get("bank1")]

        for agent, gids in list(agent_with_gids.items()):
            if count is False:
                com = set(gids)
            if com and (count is True):
                com = set(com) & set(gids)
            count = True
            if not com:
                agent_not_in_gid = agent
                break
        if com:
            gid_in_common = True
        list_gids = list(com)

        if (0 in list_gids):
            list_gids.remove(0)

        if gid_in_common is True:
            if (len(list_gids) == 1):
                temp_gid = list_gids[0]
                list_gids = [temp_gid] * len(agent_list)
                return list_gids
            elif (len(list_gids) > 1):
                for x in range(len(list_gids)):
                    temp_gid = list_gids[x]
                    possible_common_gid = [temp_gid] * len(agent_list)
                    if (self.gid_list_and_agents_match(agent_list, possible_common_gid)):
                        return possible_common_gid
            else:
                self.error(
                    "There are more than one gids in common with this list of agents, or a single agent was specified without a gid.", 1)
                return 0
        else:
            return self.error(("GID was not specified. Agent %s is not set to a common group" % agent), 1)

    # Function checks if the gid list that was sent has the same agents that
    # are being sent in the agent_list
    def gid_list_and_agents_match(self, agent_list, gids):
        match = False
        for x in range(len(agent_list)):
            bank_and_gid = self.gids_for_agent(agent_list[x])
            gids_for_an_agent = [bank_and_gid.get("bank0"), bank_and_gid.get("bank1")]
            if (gids[x] not in gids_for_an_agent):
                self.error(
                    "The gid list and agent list pairing do not match correctly. The gid list was programmed incorrectly.", 1)
                return match
        distinct_gids = []
        for gid in gids:
            distinct_gids.append(gid)
        set_of_gids = set(distinct_gids)
        list_distinct_gids = list(set_of_gids)
        incremental_agents = []
        for gid in list_distinct_gids:
            temp_agents = set(self.agents_in_group(gid))
            if not (temp_agents & set(incremental_agents)):
                for agent in temp_agents:
                    incremental_agents.append(agent)
            else:
                self.error(
                    "There are one or more agents that are not mutually exclusive based on the given gid list.", 1)
                return match
        for agent in agent_list:
            if (agent not in incremental_agents):
                self.error(
                    "The agent list given and the agent list generated per the gid list do not match.", 1)
                return match
            else:
                match = True
                return match

    # Check default num of repeat to set repeat value
    def check_num_of_repeats(self):
        if (self.arguments.get_argument("num") <= 0):
            self.error("Invalid number of repeats. Must be greater than 0.", 1)
        else:
            self.num = self.arguments.get_argument("num")

        # Check that stf_waitcycles has a valid amount
    def check_stf_waitcycles(self):
        temp_stf_waitcycles = self.arguments.get_argument("stf_waitcycles")
        if (temp_stf_waitcycles < 0):
            self.error("Invalid number of stf wait cycles. It should be greater than 0.", 1)
        elif (temp_stf_waitcycles == 0):
            pass
        else:
            self.generate_nulls(temp_stf_waitcycles)

    def generate_nops(self, list_of_gids, num_of_repeats):
        if (isinstance(list_of_gids, int)):
            self.error("Agents don't have common group", 1)
        else:
            self.pp.pprint(list_of_gids)
            distinct_gids = []
            for gid in list_of_gids:
                distinct_gids.append(gid)
            set_of_gids = set(distinct_gids)
            list_distinct_gids = list(set_of_gids)
            for gid in list_distinct_gids:
                self.ops.append({"op": "nop", "gid": gid, "num": num_of_repeats})

    def generate_nulls(self, num_of_repeats):
        self.generate_nops([0], num_of_repeats)

    def generate_replace(self, list_of_gids, num_of_repeats):
        if (isinstance(list_of_gids, int)):
            self.error("Agents don't have common group", 1)
        else:
            self.pp.pprint(list_of_gids)
            distinct_gids = []
            for gid in list_of_gids:
                distinct_gids.append(gid)
            set_of_gids = set(distinct_gids)
            list_distinct_gids = list(set_of_gids)
            for gid in list_distinct_gids:
                if not self.arguments.get_argument("output_gid") is None:
                    self.ops.append({"op": "replace", "mode": self.replace_mode, "gid": gid, "gid2": self.output_gid,
                                     "data2": self.output_data, "iv": self.output_iv, "ov": self.output_ov, "num": num_of_repeats})
                else:
                    self.ops.append({"op": "replace", "mode": self.replace_mode, "gid": gid, "gid2": gid,
                                     "data2": self.output_data, "iv": self.output_iv, "ov": self.output_ov, "num": num_of_repeats})

    # Function to check how many usrops a register requires
    # return: number of usrops required for a register
    def num_usrops_for_reg(self, agent, reg):
        # Get the width of the reg
        reg_width = float(HTD_INFO.stf_info.get_register_size(agent, reg))

        # Get the width of the data payload
        # Get the parent hubs payload attribute
        parent_hub = HTD_INFO.stf_info.get_stop_parent(agent)
        payload_width = float(HTD_INFO.stf_info.get_stop_attribute(parent_hub, "PAYLOAD"))

        # num_usrops = ceiling(<Width of reg>/<width of network bus>)
        return int(math.ceil(reg_width / payload_width))

    # Function to determine the usrop sequence for a particular register
    def get_usrop_sequence(self, agent, reg):
        pass
        # Call num_usrops_for_reg
        # Determine how to map the usrops and which databits should be applied to each usrop

    # Need to check how many usrops the specified register needs to be completely written and make sure
    # we have enough usrops available in this agent
    # Function to assign a usrop to a reg address. Includes pickle tracking
    def assign_usrop_to_reg(self, reg, usrop):
        usrops_to_program = {}


        # Check how many usrops this reg will take
        # Call self.num_usrops_for_reg to check the number of usrops required
        num_usrops = self.num_usrops_for_reg(self.agents[0], reg)

        # Handle partial usrop mapping
        partial_usrop = self.arguments.get_argument("partial_usrop")
        if partial_usrop is not None:
            if isinstance(partial_usrop, int):
                # turn into a list
                partial_usrop = [partial_usrop]

            if len(partial_usrop) > num_usrops:
                htdte_logger.error("Attempting to do a partial usrop mapping, but number of address "
                                   "indexes given ({}) is larger than the number required to map the "
                                   "entire register ({})!".format(len(partial_usrop), num_usrops))

            # Check to make sure we don't go past the highest address index needed
            for idx in partial_usrop:
                if idx >= num_usrops:
                    htdte_logger.error("Attempting to map address index {} which is higher "
                                       "than the max address index ({}) for this register".format(idx, num_usrops-1))

            num_usrops = len(partial_usrop)

        # Make sure there are enough usrops for this reg
        if num_usrops > STF_NUM_USROPS:
            self.error("Register %s will require %d usrops to completely program it which is greater than the available usrops %d. Maybe you should consider using the AUTO_INC STF feature instead." % (
                reg, num_usrops, STF_NUM_USROPS), 1)

        # Determine which way we should set usrops
        addrs = []
        if partial_usrop is None:
            action_addr = HTD_INFO.stf_info.get_stop_reg_attribute(self.agents[0], reg, "ACTION_ADDR") if (
                HTD_INFO.stf_info.has_stop_reg_attribute(self.agents[0], reg, "ACTION_ADDR")) else "H"

            # Just double check that Action Addr is set to something other than none, use the default value otherwise
            if action_addr is None:
                action_addr = "H"

            if action_addr.upper() == "H":
                for i in range(0, num_usrops):
                    addrs.append(i)
            elif action_addr.upper() == "L":
                for i in range(num_usrops - 1, -1, -1):
                    addrs.append(i)
            else:
                self.error(("Unsupported ACTION_ADDR value %s!" % action_addr), 1)

            if not HTD_INFO.stf_info.has_stop_reg_attribute(self.agents[0], reg, "ACTION_ADDR") and num_usrops > 1:
                self.error(
                    "Register %s does not appear to be defined as a wide register and we cannot assign multiple usrops to write to this register!" % reg, 1)
        else:
            # If partial usrop mapping is in effect then we sshould map the address indexes that were passed in
            addrs = partial_usrop

        # Loop over the usrops
        for i in range(0, num_usrops):
            cur_usrop = usrop + i
            if cur_usrop > STF_NUM_USROPS:
                cur_usrop -= STF_NUM_USROPS

            address_str = "@ADDRESS%s" % (addrs[i]) if addrs[i] > 0 else "@ADDRESS"

            usrops_to_program[cur_usrop] = "%s->%s" % (reg, address_str)

            # Need to save info for all agents
            for agent in self.agents:
                if i == 0:
                    htd_history_mgr.history_capture(
                        self, [agent, reg], {"USROP_SEQ": []}, container_type=self.history_container, save_non_arg_data=1)

                cur_seq = htd_history_mgr.history_get(
                    self, [agent, reg], "USROP_SEQ", container_type=self.history_container)
                cur_seq.append(cur_usrop)

                # Check if this usrop is already programmed to something else
                # TODO: THIS IS ALL FOR FUTURE SUPPORT
                usrop_cur_reg_addr = ""
                if htd_history_mgr.history_has(self, [agent, "USROPS"], cur_usrop, container_type=self.history_container):
                    usrop_cur_reg_addr = htd_history_mgr.history_get(
                        self, [agent, "USROPS"], cur_usrop, container_type=self.history_container)

                # Check if this is not an empty string
                if usrop_cur_reg_addr != "":
                    pass
                    # TODO: FUTURE SUPPORT
                    # Split the reg and addr and go blank out the reg USROP_SEQ because it is
                    # no longer valid

                htd_history_mgr.history_capture(self, [agent, "USROPS"], {
                                                cur_usrop: address_str}, container_type=self.history_container, save_non_arg_data=1)

        # Append this to self.ops
        self.ops.append({"op": "map_usrop", "agents": self.agents, "gids": self.gid,
                         "usrops_to_program": copy.deepcopy(usrops_to_program)})
        self.pp.pprint(usrops_to_program)

    # Function to check a list of agents against agents in a group
    # To return pass the following criteria must be met
    #   1. The agents passed in are all in the group passed in
    #   2. The group contains no other agents than the ones specified
    #
    # Return Value:
    #   The gid of the group to use
    def check_agents_in_common_group(self, agents, gid=-1):
        pass
        # if gid is not None or undefined (need to check what a non-defaulted value is get_arg("gid")
        # only criteria 1 above applies

        # If gid is set, both above criteria apply

        # If either of the required criteria are not met error

        # return GID

    # Function to loop over a list of agents and select them and then print out a summary
    def select_agents(self, agents, gids, gid_banks, select_mode):
        # Check that we are either all select or all deselect
        if (gids.count(0) > 0 and gids.count(0) != len(gids)):
            self.error("Cannot do select (gid > 0) and deslect (gid = 0) at the same time!", 1)

        # Loop over specified agents/pids
        self.hubs_setup = []
        if self.stf_network:
            #using stf network configuration : stf_program_network grouping
            self.generate_select_requirements_stf_network(agents, gids, gid_banks)
        else:
            #legacy method to connect and disconnet hub
            self.desired_hub_state = self.determine_desired_hubs_state(agents, gids)
            self.generate_select_requirements(agents, gids, gid_banks)

    # Function to determine desired hub state
    # TODO: enable this in the future when we support setting multiple gids at once or interleaving
    def determine_desired_hubs_state(self, agents, gids):
        parent_hubs = {}
        parent_hubs["PROGRAM_ORDER"] = []
        parent_hubs["HUBS"] = {}

        # Get the existing info about all of the parents
        for (agent, gid) in zip(agents, gids):
            i = agents.index(agent)
            prev_gid = self.prev_gids[i]
            gid_bank = self.gid_bank[i]

            # Check if this agent is already programed for this gid in this bank
            bank_key = self.get_gid_bank_key(gid_bank)
            if htd_history_mgr.history_has(self, [agent, "GID"], bank_key, container_type=self.history_container):
                if htd_history_mgr.history_get(self, [agent, "GID"], bank_key, container_type=self.history_container) == gid:
                    self.inform("Attempting to assign agent %s into group %d on bank %d, but this agent is already in that group on that bank! Skipping this agent!" % (
                        agent, gid, gid_bank))
                    continue

            stop_parent_hubs = HTD_INFO.stf_info.get_stop_parent_hubs(agent)
            stop_parent_hubs.reverse()

            comment = "Programming Agent %s into group %d on bank %d.\n" % (agent, gid, gid_bank)
            comment += "Agent hierarchy: " + "->".join(stop_parent_hubs) + "->%s\n" % (agent)
            self.ops.append({"op": "comment", "comment": comment})

            # If the agent is a hub we should program the tracker delay and groups for
            # this agent as well before moving on
            if HTD_INFO.stf_info.is_stop_a_hub(agent):
                stop_parent_hubs.append(agent)

            # Flip program order if this is select since we want to program from the top down
            # On delect we want to program from the bottom up
            if (gid == 0):
                stop_parent_hubs.reverse()

            for parent_hub in stop_parent_hubs:
                if HTD_INFO.stf_info.is_stop_a_controller(parent_hub):
                    continue

                if parent_hub in list(parent_hubs.keys()):
                    continue

                # Get current membership/response info
                self.setup_group_reg_info(parent_hub, "group_membership", parent_hubs)
                self.setup_group_reg_info(parent_hub, "group_responder", parent_hubs)

                # Set the hub programming order
                if parent_hub not in parent_hubs["PROGRAM_ORDER"]:
                    parent_hubs["PROGRAM_ORDER"].append(parent_hub)

                # Determine the group membership and responder info based on gid
                if gid != 0:
                    # Add to the agent count for this hub
                    parent_hubs["HUBS"][parent_hub]["group_membership"][gid]["COUNT"] += 1
                    htd_history_mgr.history_capture(self, [parent_hub, "group_membership"], {gid: parent_hubs["HUBS"][parent_hub][
                                                    "group_membership"][gid]["COUNT"]}, container_type=self.history_container, save_non_arg_data=1)
                    parent_hubs["HUBS"][parent_hub]["group_responder"][gid]["COUNT"] += 1
                    htd_history_mgr.history_capture(self, [parent_hub, "group_responder"], {gid: parent_hubs["HUBS"][parent_hub][
                                                    "group_responder"][gid]["COUNT"]}, container_type=self.history_container, save_non_arg_data=1)

                    if parent_hubs["HUBS"][parent_hub]["group_membership"][gid]["VALUE"] != 1:

                        parent_hubs["HUBS"][parent_hub]["group_membership"][gid]["VALUE"] = 1
                        parent_hubs["HUBS"][parent_hub]["group_responder"][gid]["VALUE"] = 1
                        parent_hubs["HUBS"][parent_hub]["group_membership"]["NUM"] += 1
                        parent_hubs["HUBS"][parent_hub]["group_responder"]["NUM"] += 1

                    parent_hubs["HUBS"][parent_hub]["group_membership"][gid]["UPDATED"] = 1
                    parent_hubs["HUBS"][parent_hub]["group_responder"][gid]["UPDATED"] = 1

                # Need to remove from old group if it wasn't 0
                if (gid == 0) or (prev_gid != 0):
                    # subtract from the agent count for this hub
                    parent_hubs["HUBS"][parent_hub]["group_membership"][prev_gid]["COUNT"] -= 1
                    htd_history_mgr.history_capture(self, [parent_hub, "group_membership"], {prev_gid: parent_hubs["HUBS"][parent_hub][
                                                    "group_membership"][prev_gid]["COUNT"]}, container_type=self.history_container, save_non_arg_data=1)
                    parent_hubs["HUBS"][parent_hub]["group_responder"][prev_gid]["COUNT"] -= 1
                    htd_history_mgr.history_capture(self, [parent_hub, "group_responder"], {prev_gid: parent_hubs["HUBS"][parent_hub][
                                                    "group_responder"][prev_gid]["COUNT"]}, container_type=self.history_container, save_non_arg_data=1)

                    # Only disable the membership/responder if the agent count for this group is 0
                    if parent_hubs["HUBS"][parent_hub]["group_membership"][prev_gid]["COUNT"] < 1:
                        parent_hubs["HUBS"][parent_hub]["group_membership"][prev_gid]["VALUE"] = 0
                        parent_hubs["HUBS"][parent_hub]["group_responder"][prev_gid]["VALUE"] = 0
                        parent_hubs["HUBS"][parent_hub]["group_membership"]["NUM"] -= 1
                        parent_hubs["HUBS"][parent_hub]["group_responder"]["NUM"] -= 1

        # Now that all of the responder/membership groups are in place determine tracker latencies

        for hub in list(parent_hubs["HUBS"].keys()):

            if parent_hubs["HUBS"][hub]["group_membership"]["NUM"] > 0:
                tracker = self.get_tracker_delay(hub)

                parent_hubs["HUBS"][hub]["tracker_delay"] = tracker
                parent_hubs["HUBS"][hub]["tracker_en"] = 1
                parent_hubs["HUBS"][hub]["group_membership"][self.scratchpad_gid]["VALUE"] = 1
            else:
                parent_hubs["HUBS"][hub]["tracker_delay"] = 0
                parent_hubs["HUBS"][hub]["tracker_en"] = 0
                parent_hubs["HUBS"][hub]["group_membership"][self.scratchpad_gid]["VALUE"] = 0

            # Organize the values a little differently too for easier access later
            for reg_group in ["group_membership", "group_responder"]:
                if "REGS" not in list(parent_hubs["HUBS"][hub][reg_group].keys()):
                    parent_hubs["HUBS"][hub][reg_group]["REGS"] = {}

                for cur_gid in list(parent_hubs["HUBS"][hub][reg_group].keys()):
                    if not isinstance(cur_gid, int):
                        continue

                    reg = parent_hubs["HUBS"][hub][reg_group][cur_gid]["REG"]
                    field = parent_hubs["HUBS"][hub][reg_group][cur_gid]["FIELD"]

                    if reg not in list(parent_hubs["HUBS"][hub][reg_group]["REGS"].keys()):
                        parent_hubs["HUBS"][hub][reg_group]["REGS"][reg] = {}

                    if not parent_hubs["HUBS"][hub][reg_group][cur_gid]["VALUE"] is None:
                        parent_hubs["HUBS"][hub][reg_group]["REGS"][reg][
                            field] = parent_hubs["HUBS"][hub][reg_group][cur_gid]["VALUE"]

        return parent_hubs

    def setup_group_reg_info(self, hub, reg, hubs_dict):
        # Get the group mem reg/field all gids
        cur_gid = 1

        if hub not in list(hubs_dict["HUBS"].keys()):
            hubs_dict["HUBS"][hub] = {}

        if reg not in list(hubs_dict["HUBS"][hub].keys()):
            hubs_dict["HUBS"][hub][reg] = {}

        hubs_dict["HUBS"][hub][reg]["NUM"] = 0

        while (HTD_INFO.stf_info.has_stop_register_spec(hub, reg, cur_gid)):
            group_mem_reg, group_mem_field = HTD_INFO.stf_info.get_stop_register_spec(
                hub, reg, cur_gid).split("->")

            if cur_gid not in list(hubs_dict["HUBS"][hub][reg].keys()):
                hubs_dict["HUBS"][hub][reg][cur_gid] = {}

            # Get the historical count if it exists
            prev_count = 0
            if htd_history_mgr.history_has(self, [hub, reg], cur_gid, container_type=self.history_container):
                prev_count = htd_history_mgr.history_get(
                    self, [hub, reg], cur_gid, container_type=self.history_container)

            # Save the reg/field to hubs dict
            hubs_dict["HUBS"][hub][reg][cur_gid]["REG"] = group_mem_reg
            hubs_dict["HUBS"][hub][reg][cur_gid]["FIELD"] = group_mem_field
            hubs_dict["HUBS"][hub][reg][cur_gid]["UPDATED"] = 0
            hubs_dict["HUBS"][hub][reg][cur_gid]["VALUE"] = None
            hubs_dict["HUBS"][hub][reg][cur_gid]["COUNT"] = prev_count

            # Get the saved value if any
            saved_val = self.get_prev_reg_field_value(hub, group_mem_reg, group_mem_field)
            if saved_val is None:
                saved_val = 0

            hubs_dict["HUBS"][hub][reg][cur_gid]["VALUE"] = saved_val
            # We don't really want to save the scratchpad number
            if saved_val == 1 and cur_gid != self.scratchpad_gid:
                hubs_dict["HUBS"][hub][reg]["NUM"] += 1

            # Need to count the agents on each hub not just the number of groups!

            cur_gid += 1

    def set_oe_bif_oe(self, agent, gid_bank, gid_to_use, val):
        group_oe_reg, group_oe_field = HTD_INFO.stf_info.get_stop_register_spec(
            agent, "group%d_oe" % (gid_bank)).split("->")
        group_bif_oe_reg, group_bif_oe_field = HTD_INFO.stf_info.get_stop_register_spec(
            agent, "group%d_bif_oe" % (gid_bank)).split("->")
        if (group_oe_reg == group_bif_oe_reg):
            self.write_field_values(agent, gid_to_use, group_oe_reg, {
                                    group_oe_field: val, group_bif_oe_field: val})
        else:
            self.write_field_values(agent, gid_to_use, group_oe_reg, {group_oe_field: val})
            self.write_field_values(agent, gid_to_use, group_oe_reg, {group_bif_oe_field: val})

    def get_oe_val_history(self, agent, gid_bank):
        group_oe_reg, group_oe_field = HTD_INFO.stf_info.get_stop_register_spec(
            agent, "group%d_oe" % (gid_bank)).split("->")

        field_vals = self.get_prev_reg_values(agent, group_oe_reg)
        return field_vals

    # Function to do the actual selecting and hub programming
    def generate_select_requirements(self, agents, gids, gid_banks):

        # Turn off all endpoints that need to be turned off
        turn_off_index = [i for i, x in enumerate(gids) if x == 0]
        for i in turn_off_index:
            agent_index = turn_off_index[i]
            agent = agents[agent_index]
            gid = gids[agent_index]
            gid_bank = gid_banks[agent_index]
            prev_gid = self.prev_gids[agent_index]

            # Write the endpoint to turn off output endpoint
            self.set_oe_bif_oe(agent, gid_bank, prev_gid, 0)

            # Configure the endpoint
            self.assign_gid_to_agent(gid, agent, gid_bank, prev_gid)

        # Do all of the required hub programming
        for parent_hub in self.desired_hub_state["PROGRAM_ORDER"]:

            # Check if this hub already has a gid in the scrath gid_bank
            restore_gid = 0
            restore_oe = 0
            if htd_history_mgr.history_has(self, [parent_hub, "GID"], "bank%s" % (self.scratchpad_gid_bank), container_type=self.history_container):
                restore_gid = htd_history_mgr.history_get(self, [parent_hub, "GID"], "bank%d" % (
                   self.scratchpad_gid_bank), container_type=self.history_container)
                restore_oe = self.get_oe_val_history(parent_hub, self.scratchpad_gid_bank)

                if (1 in list(restore_oe.values())):
                    # Turn off OE for this hub - should restore it later
                    self.set_oe_bif_oe(parent_hub, self.scratchpad_gid_bank, restore_gid, 0)

                self.ops.append({"op": "comment", "comment": "Overriding GID Bank %d with scratchpad gid. Will restore GID to %d when done" % (
                                self.scratchpad_gid_bank, restore_gid)})

            # Put the hub into the scratch group
            self.ops.append({"op": "select", "agent": parent_hub, "gid": self.scratchpad_gid,
                            "gid_bank": self.scratchpad_gid_bank, "comment": "Put the hub into the scratch group"})

            # Disable scratch gid as member
            scratchpad_mem_reg = self.desired_hub_state["HUBS"][
                                parent_hub]["group_membership"][self.scratchpad_gid]["REG"]
            scratchpad_mem_field = self.desired_hub_state["HUBS"][
                                parent_hub]["group_membership"][self.scratchpad_gid]["FIELD"]

            self.write_field_values(parent_hub, self.scratchpad_gid, scratchpad_mem_reg, {
                                   scratchpad_mem_field: 0}, comment="Disable scratch gid as member")

            # Get tracker enable reg/field
            tkr_en_reg, tkr_en_field = HTD_INFO.stf_info.get_stop_register_spec(
                parent_hub, "tracker_enable").split("->")

            # Get tracker delay reg/field
            tkr_dly_reg, tkr_dly_field = HTD_INFO.stf_info.get_stop_register_spec(
                parent_hub, "tracker_delay").split("->")

            # Get the tracker setup
            tracker_delay = self.desired_hub_state["HUBS"][parent_hub]["tracker_delay"]
            tracker_en = self.desired_hub_state["HUBS"][parent_hub]["tracker_en"]

            # Need a NOP to ensure the scratchpad disable has propogated through the entire ring
            self.generate_nulls(tracker_delay + 1)

            # Write the tracker delay and tracker enable fields
            self.write_field_values(parent_hub, self.scratchpad_gid, tkr_dly_reg, {
                                   tkr_dly_field: tracker_delay}, comment="Setup the tracker")
            self.write_field_values(parent_hub, self.scratchpad_gid,
                                   tkr_en_reg, {tkr_en_field: tracker_en})

            # Get previous values for the Group Responder reg
            rsp_regs = copy.deepcopy(self.desired_hub_state["HUBS"][
                                     parent_hub]["group_responder"]["REGS"])

            for reg in list(rsp_regs.keys()):
                self.write_field_values(parent_hub, self.scratchpad_gid, reg, copy.deepcopy(
                    rsp_regs[reg]), comment="Enable membership for scratch gid and any groups under this ring")


            # Enable membership for scratch gid and any groups under this ring
            # TODO: Need to add logic around these settings to check if we are deselecting the endpoint to set these to 0
            #       and if any other endpoint is still active under this hub with this group
            mem_regs = copy.deepcopy(self.desired_hub_state["HUBS"][
                                     parent_hub]["group_membership"]["REGS"])

            for reg in list(mem_regs.keys()):
                self.write_field_values(parent_hub, self.scratchpad_gid,
                                        reg, copy.deepcopy(mem_regs[reg]))

            # Remove the HUB from the scratch group
            if (restore_gid == 0):
                self.ops.append({"op": "select", "agent": parent_hub, "gid": 0,
                                "gid_bank": self.scratchpad_gid_bank, "comment": "Remove the HUB from the scratch group"})
            else:
                self.ops.append({"op": "select", "agent": parent_hub, "gid": restore_gid,
                                "gid_bank": self.scratchpad_gid_bank, "comment": "Restoring previously programmed GID after scratch usage"})

                if (1 in list(restore_oe.values())):
                    group_oe_reg, group_oe_field = HTD_INFO.stf_info.get_stop_register_spec(
                                                    parent_hub, "group%d_oe" % (self.scratchpad_gid_bank)).split("->")
                    self.write_field_values(parent_hub, restore_gid, group_oe_reg, restore_oe,
                                        comment="Restoring output enable values to pre-scratchpad values")

        # Turn on all endpoints that need to be turned on

        turn_on_index = [i for i, x in enumerate(gids) if x != 0]

        for i in turn_on_index:
            agent_index = turn_on_index[i]
            agent = agents[agent_index]
            gid = gids[agent_index]
            gid_bank = gid_banks[agent_index]
            prev_gid = self.prev_gids[agent_index]

            # Configure the endpoint
            self.assign_gid_to_agent(gid, agent, gid_bank, prev_gid)

            if(self.output_auto_en):
                # Set output enable and bifurcation output enable
                self.set_oe_bif_oe(agent, gid_bank, gid, 1)

    # Function to do the actual selecting and hub programming
    # this is to support stf_network grouping request from jitbit23670
    # http://htd_tvpv_help.intel.com/Ticket/23670
    # to make sure backward compatible, remain the legacy method and create a separate method for this
    def generate_select_requirements_stf_network(self, agents, gids, gid_banks):

        # Turn off all endpoints that need to be turned off
        turn_off_index = [i for i, x in enumerate(gids) if x == 0]
        for i in turn_off_index:
            agent_index = turn_off_index[i]
            agent = agents[agent_index]
            gid = gids[agent_index]
            gid_bank = gid_banks[agent_index]
            prev_gid = self.prev_gids[agent_index]

            select_mode = self.select_mode[agent_index]

            # Configure the endpoint
            self.assign_gid_to_agent(gid, agent, gid_bank, prev_gid, select_mode)

        turn_on_index = [i for i, x in enumerate(gids) if x != 0]

        for i in turn_on_index:
            agent_index = turn_on_index[i]
            agent = agents[agent_index]
            gid = gids[agent_index]
            gid_bank = gid_banks[agent_index]
            prev_gid = self.prev_gids[agent_index]
            select_mode = self.select_mode[agent_index]

            # Configure the endpoint
            self.assign_gid_to_agent(gid, agent, gid_bank, prev_gid, select_mode)

    def write_field_values(self, agent, gid, reg, write_values, read_values={}, comment=""):
        if not isinstance(agent, list):
            agent = [agent]

        if not isinstance(gid, list):
            gid = [gid] * len(agent)

        self.ops.append({"op": "write_read", "agent": agent, "gid": gid, "reg": reg, "write_by_field": copy.deepcopy(
            write_values), "read_by_field": copy.deepcopy(read_values), "comment": comment})

        # Store field values in history
        for field, value in write_values.items():
            for cur_agent in agent:
                htd_history_mgr.history_capture(self, [cur_agent, reg], {
                                                field: value}, container_type=self.history_container, save_non_arg_data=1)

    def get_prev_reg_values(self, agent, reg):
        reg_fields = HTD_INFO.stf_info.get_register_fields(agent, reg)
        field_vals = {}

        for field in reg_fields:
            #            self.inform("Checking for history of %s=>%s->%s"%(agent, reg, field))
            if(htd_history_mgr.history_has(self, [agent, reg], field, container_type=self.history_container)):
                field_vals[field] = htd_history_mgr.history_get(
                    self, [agent, reg], field, container_type=self.history_container)

        return field_vals

    def get_prev_reg_field_value(self, agent, reg, field):
        field_val = None

#        self.inform("Checking for history of %s=>%s->%s"%(agent, reg, field))
        if(htd_history_mgr.history_has(self, [agent, reg], field, container_type=self.history_container)):
            field_val = htd_history_mgr.history_get(
                self, [agent, reg], field, container_type=self.history_container)

        return field_val

    def break_value_into_fields(self, agent, reg, val):
        field_l = HTD_INFO.stf_info.get_register_fields(agent, reg)
        ret_val = {}

        if (list(field_l.keys()) is None or len(list(field_l.keys())) == 0):
            ret_val[reg] = val
            ret_val["whole_reg"] = 1
        else:
            for field in list(field_l.keys()):
                # Get MSB and LSB
                msb = HTD_INFO.stf_info.get_field_msb(agent, reg, field)
                lsb = HTD_INFO.stf_info.get_field_lsb(agent, reg, field)
                field_len = msb - lsb + 1
                field_max_val = int(pow(2, field_len) - 1)
                # compute the field value
                # val >> lsb & max_field_val
                field_val = (val >> lsb) & field_max_val

                ret_val[field] = field_val

        return ret_val

    def adjust_msb_lsb_to_field(self, agent, reg, field_name, msb, lsb, val, field_vals_dict):
        field_l = HTD_INFO.stf_info.get_register_fields(agent, reg)

        normalized_msb = msb - lsb
        normalized_lsb = lsb - lsb
        val_max_msb = msb - lsb

        # Loop over the fields
        for field in list(field_l.keys()):
            # Get the msb and lsb of the field
            field_msb = HTD_INFO.stf_info.get_field_msb(agent, reg, field)
            field_lsb = HTD_INFO.stf_info.get_field_lsb(agent, reg, field)

            # Check if there is overlap of msb/lsb with the field msb/lsb
            overlap_len = 0

            # Bit numbers overlapping inside field [FIELD_LEN-1:0]
            field_overlap_msb = -1
            field_overlap_lsb = -1
            # Bit numbers overlapping in reg bits [REG_LEN-1:0]
            reg_overlap_msb = -1
            reg_overlap_lsb = -1
            # Bit numbers overlapping in value bits [VAL_LEN-1:0]
            val_overlap_msb = -1
            val_overlap_lsb = -1

            # Check for overlap and compute overlap field bits
            if (lsb <= field_lsb and msb >= field_lsb) or (msb >= field_msb and lsb <= field_msb) or \
               (lsb >= field_lsb and lsb <= field_msb) or (msb <= field_msb and msb >= field_lsb):
                field_overlap_msb = msb - \
                    field_lsb if (field_msb - msb > 0) else field_msb - field_lsb
                field_overlap_lsb = lsb - field_lsb if (lsb - field_lsb >= 0) else 0
                field_overlap_bits = list(range(field_overlap_lsb, field_overlap_msb + 1))
                overlap_len = field_overlap_msb - field_overlap_lsb + 1

                reg_overlap_msb = field_lsb + field_overlap_msb
                reg_overlap_lsb = field_lsb + field_overlap_lsb

                val_overlap_msb = val_max_msb - (msb - reg_overlap_msb)
                val_overlap_lsb = reg_overlap_lsb - lsb
                val_overlap_bits = list(range(val_overlap_lsb, val_overlap_msb + 1))

            else:
                # No overlap, move onto next field
                continue

            # Get the current field value in the following hierarchical order
            # 1. Value currently in field_values_dict
            # 2. Saved value from htd_history_mgr if incremental mode is set to true
            # 3. Default value from API if available
            # 4. All 0s
            cur_field_val = 0
            if (field in list(field_vals_dict.keys())):
                cur_field_val = field_vals_dict[field]
            else:
                cur_field_val = self.get_incremental_or_default_value(agent, reg, field)

            # Update the values according to the bit field positions
            for i in range(0, overlap_len):
                field_overlap_bit_pos = field_overlap_bits[i]
                val_overlap_bit_val = (val >> val_overlap_bits[i]) & 1

                # Create a mask for index at field_overlap_bit_pos
                mask = 1 << field_overlap_bit_pos

                # Set the bit in index i to 0
                cur_field_val &= ~mask

                if val_overlap_bit_val:
                    cur_field_val |= mask

            if field == field_name and msb >= 0 and lsb >= 0:
                if msb == lsb and msb <= field_msb:
                    field_vals_dict[field + "[" + str(msb) + "]"] = val
                elif msb <= field_msb:    
                    field_vals_dict[field + "[" + str(msb) + ":" + str(lsb) + "]"] = val
                else:
                    field_vals_dict[field] = val
            else:
                field_vals_dict[field] = cur_field_val

        return field_vals_dict

    def get_incremental_or_default_value(self, agent, reg, field):
        if (self.arguments.get_argument("incremental_mode") == 1):
            if htd_history_mgr.history_has(self, [agent, reg], field, container_type=self.history_container):
                val = htd_history_mgr.history_get(
                    self, [agent, reg], field, container_type=self.history_container)
                return val

        # This can't be an else if because if we are in incremental mode but this
        # field has never been written before we need to provide the default
        if (HTD_INFO.stf_info.field_has_default(agent, reg, field)):
            val = HTD_INFO.stf_info.get_field_default(agent, reg, field)
            return val

        return 0

    # Function to calculate tracker delay for a hub
    # return: tracker delay as int
    # might be better off in the STF INFO code
    # Check out code in
    # /nfs/site/disks/mdo_skl_005/spf_root/eng.2016.ww19a_nick_hack/lib/perl5/SPF/Helper/STF.pm
    def get_tracker_delay(self, hub):
        # TODO: Assuming 1:1 clock ratio for now, for ease of coding. Need to take
        # into account clock ratio in the future
        tracker_value = 5

        # Determine all responder groups for this hub

        # TODO - Calculate interleaving ratio based on ratio of group responders in interleaving group list
        # (# of responder groups in the interleave groups)/(# of interleave groups)
        # For now assume interleave ratio is 1
        interleave_ratio = 1

        # TODO: here's the code for calculating inteleave ratio
        # Need to define interleave state and get_interleave_group_list
        '''
        if (self.has_interleave_state):
            interleave_groups = self.get_interleave_group_list

            int_resp_groups = 0
            for resp_group in responder_groups:
                if resp_group in interleave_groups:
                    int_resp_groups++

            interleave_ratio = int_resp_groups/len(interleave_groups)
        '''

        # Get deskew fifo value if available
        # get_deskew_fifo_size_register_spec
        # If it is an int that is the deskew value,
        # Else, it is giving us a reg/field path see if that reg/field is saved,
        # elif default value exists set to default value, else 5
        deskew = 5
        if (HTD_INFO.stf_info.stop_has_deskew_fifo_size_reg_spec(hub)):
            hub_deskew = HTD_INFO.stf_info.get_stop_deskew_fifo_size_reg_spec(hub)
            if (re.match(r'^\d+$', hub_deskew)):
                deskew = int(hub_deskew)
            else:
                # Should read the value of the register
                # Currently SPF doesn't do this branch either - skip for now
                pass

        # Get the latency that the tracker needs to hide
        # We aren't supporting other clock ratios just yet
        # TODO: change 1 to actual clock ratio when we have that supported
        packet_latency = self.get_tracker_hidden_delay(hub, 1, deskew)

        # Tracker value is the latency adjusted by the interleaving ratio
        tracker_value = 1 + math.ceil(packet_latency * interleave_ratio)

        # Return tracker delay
        return tracker_value

    # Function to determine the tracker_hidden_delay
    # Returns the latency in number of parent clocks
    def get_tracker_hidden_delay(self, hub, ratio, deskew):

        childring_delay = HTD_INFO.stf_info.get_child_ring_delay_parts(hub)
        parent_contribution = childring_delay["parent"] + (childring_delay["child"] * ratio)

        child_contribution = HTD_INFO.stf_info.get_child_ring_latency(hub) * ratio

        latency = parent_contribution + child_contribution + deskew

        return latency

    # Function to return all agents matching a pid mask
    # return: list of agents matching pid mask
    def get_select_mask_agents(self, pid_mask, pid_sel):
        matching_agents = []

        # Loop over all agents
        # SELECT = 1 if ((PID ^ SELECT_PID) & ~PID_MASK (agent) == 0) else 0
        #         PID_MASK = 'b1110 (only look at the LSB of the PID)
        #         SELECT_PID (agent) = 'b0001 (only select when the LSB is a 1)

        #         EXAMPLES:
        #         PID = 0101
        #         (0101 ^ ~1110) & 0001 = (0101 ^ 0001) & 0001 = 0100 & 0001 = 0000 (selected)

        #         PID = 0110
        #         (0110 ^ ~1110) & 0001 = (0110 ^ 0001) & 0001 = 0111 & 0001 = 0001 (not selected)
        all_agents = HTD_INFO.stf_info.get_stf_stop_names()

        for agent in all_agents:
            pid = HTD_INFO.stf_info.get_stop_pid_by_name(agent)
            select_b = (pid ^ pid_sel) & ~pid_mask

            if (select_b == 0):
                # This agent will be selected
                matching_agents.append(agent)

        return matching_agents

    def check_agents_have_reg(self, reg):
        reg_size = HTD_INFO.stf_info.get_register_size(self.agents[0], reg)
        if reg == "":
            self.error("reg is a required argument for the write_read op type!", 1)
        reg_address = -1
        for agent in self.agents:
            if not HTD_INFO.stf_info.stop_has_register(agent, reg):
                self.error("Agent %s does not have a register named %s" % (agent, reg), 1)

            # Check that the address is the same
            reg_address_cur = HTD_INFO.stf_info.get_register_address_decimal(agent, reg)

            if reg_address != -1 and reg_address_cur != reg_address:
                self.error("The address for register %s on agent %s is %d, but does not match the address (%d) for the same register on other selected agents!" % (
                    reg, agent, reg_address_cur, reg_address), 1)

            reg_address = reg_address_cur

            # Check that the size of the registers is the same
            if HTD_INFO.stf_info.get_register_size(agent, reg) != reg_size:
                self.error("The size of register %s on agent %s is %d, expecting size %d!" % (
                    reg, agent, HTD_INFO.stf_info.get_register_size(agent, reg), reg_size), 1)

    def get_actual_assignment_boundaries(self, field, reg_name, reg_space, reg_file, parent_container, value):
        res = []
        if(not parent_container.arguments.is_argument_assigned(field)):
            (lsb, msb) = HTD_INFO.cr_info.get_cr_field_boundaries(
                field, reg_name, reg_space, reg_file)
            return [(lsb, msb, value, 0, 0)]
        else:
            for val in parent_container.arguments.get_argument(field):
                if(val.lsb >= 0):
                    #mask_hi = pow(2, val.msb) - 1
                    #mask_lo = pow(2, val.lsb) - 1
                    #mask = mask_hi ^ mask_lo
                    #value= (value & mask) >> val.lsb
                    (flsb, fmsb) = HTD_INFO.cr_info.get_cr_field_boundaries(
                        field, reg_name, reg_space, reg_file)
                    res.append((flsb + val.lsb, flsb + val.msb, 0 if(val.capture > 1) else val.value,
                                1 if(val.capture > 0) else 0, 1 if(val.mask > 0) else 0))
                else:
                    (lsb, msb) = HTD_INFO.cr_info.get_cr_field_boundaries(
                        field, reg_name, reg_space, reg_file)
                    res.append((lsb, msb, 0 if(val.capture > 0) else val.value,
                                1 if(val.capture > 0) else 0, 1 if(val.mask > 0) else 0))
        return res

    def get_direct_label_assignment(self, field, current_lsb):
        if(field not in list(self.arguments.arg_l.keys())):
            return ""
        for val in self.arguments.get_argument(field):
            if(val.lsb >= 0 and current_lsb == val.lsb and val.label != "" and val.label != -1):
                return val.label
            elif(val.lsb < 0 and val.label != "" and val.label != -1):
                return val.label
        return ""

    def get_reg_address(self, reg_name, reg_space, scope):
        address = str(bin(HTD_INFO.cr_info.get_cr_address_by_name(reg_name, reg_space, scope)))
        address = address.replace("0b", "")
        address = address + "00"
        address = ((32 - len(address)) * "0") + address
        return address

    def get_reg_bin_data(self, reg_info, reg_name, reg_space, reg_file, max_data_size=32):
        size = 0
        for field in list(reg_info["field"].keys()):
            (lsb, msb) = HTD_INFO.cr_info.get_cr_field_boundaries(
                field, reg_name, reg_space, reg_file)
            size += msb - lsb + 1

        if(size > int(max_data_size)):
            self.error("The size of register %s is not supported for %transactions, expecting size %d!" % (
                reg_name, self.arguments.get_argument("op"), max_data_size), 1)

        data = size * "1"

        for field in list(reg_info["field"].keys()):
            lsb = int(reg_info["field"][field]["bitOffset"])
            msb = lsb + int(reg_info["field"][field]["bitWidth"]) - 1
            if(self.arguments.is_argument_assigned(field)):
                for val in self.arguments.get_argument(field):
                    new_val = str(bin(val.value))
                    new_val = new_val.replace("0b", "")
                    new_val = ((int(reg_info["field"][field]["bitWidth"]) -
                                len(new_val)) * "0") + new_val
                    data = data[0:lsb] + new_val[::-1] + data[msb + 1:len(data)]
            else:
                reset_val = str(bin(HTD_INFO.cr_info.get_cr_field_reset_val(
                    field, reg_name, reg_space, reg_file)))
                reset_val = reset_val.replace("0b", "")
                reset_val = ((int(reg_info["field"][field]["bitWidth"]) -
                              len(reset_val)) * "0") + reset_val
                data = data[0:lsb] + reset_val[::-1] + data[msb + 1:len(data)]

        data = data + ((int(max_data_size) - len(data)) * "0")
        return data
# return data
