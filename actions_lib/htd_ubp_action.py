from htd_basic_action import *
from htd_utilities import *
from htd_collaterals import *
from htd_player_top import *
import re

# ---------------------------------------
#
# ---------------------------------------
# ---------------------------------------------


class UBP(htd_base_action):

    def __init__(self, action_name, source_file, source_lineno, currentFlow, is_internal):

        htd_base_action.__init__(self, self.__class__.__name__, action_name,
                                 source_file, source_lineno, currentFlow, is_internal)

        # Tap parameters
        self.manual = 0
        self.ir_name = ""
        self.ir_agent = ""
        self.fields = {}
        self.dr = "1"
        self.dr_size = 1
        self.check = 0
        self.read_modify_write = 0
        self.bfm_mode = "tap"
        self.parallel = 1

        self.reset = 0

        # internal paramenters
        self.tap_cmds = []
        self.ubp_action = ""
        self.mbp_pin = -1
        self.action_dr = ""
        self.action_param = ""

        # flow parameters
        self.HistoryLabel = "UBP_history"
        self.Actions_Dictionary = {}

     # BRK Arguments
        self.arguments.set_argument("source", 1, "Specify which source for this action")
        self.arguments.declare_arg("Ubp_action", "uBP action to perform        ", "string", "", 0)
        self.arguments.declare_arg("reset", "uBP action to perform        ", "string", 0, 0)
        self.arguments.declare_arg("disable", "param to disable everything        ", "string", 0, 0)
        self.arguments.declare_arg("Ip", "Ip where you want to configure the BRK ", "string", "", 0)
        self.arguments.declare_arg("BrkId", "Id of the BRKCTL you want to configure ", "int", 0, 0)
        self.arguments.declare_arg("allow_shared_trigger", "Allow shared trigger ", "bool", 0, 0)

     # Direct IR arguments
        self.arguments.declare_arg(
            "ir", "The TAP destintation CMD name or binary CMD code      ", "string_or_int", "", 0)
        self.arguments.declare_arg("agent", "The TAP link destination agent name .", "string", "", 0)
        self.arguments.declare_arg("bfm_mode", "The bfm mode: express|injection|normal ",
                                   ["express", "injection", "normal"], "normal", 0)
        self.arguments.declare_arg(
            "parallel_mode", "Used to dis/ena taplink parallel/specific taplink endpoint access  ", "bool", 1, 0)
        self.arguments.declare_arg("read_modify_write", "Read rtl and override user assignment ena/dis ", "bool", 0, 0)

     # General Arguments
        self.arguments.declare_arg("read_modify_write",
                                   "Read rtl and override user assignment ena/dis ", "bool", 1, 0)
        self.arguments.declare_arg("bfm_mode", "The bfm mode: express|injection|normal ", [
                                   "express", "injection", "tap"], "tap", 0)

        self.tap_protocol = ""
        if("HPL" in list(CFG.keys())):
            if("tap_mode" in list(CFG["HPL"].keys())):
                self.tap_protocol = CFG["HPL"]["tap_mode"]
            if("TE" in list(CFG.keys())):
                if("tap_mode" in list(CFG["TE"].keys())):
                    self.tap_protocol = CFG["TE"]["tap_mode"]
                if(self.tap_protocol not in ["tapnetwork", "taplink"]):
                    self.error(("Action's (%s) : Illegal TAP protocol type selection in CFG[\"TE\"][\"tap_mode\"]: expected \"tapnetwork\" or \"taplink\" ,received - \"%s\" ") % (
                        self.__action_name__, self.tap_protocol), 1)

    def debug_readback(self): pass

    def get_action_not_declared_argument_names(self): pass

    def check_tap_var(self):
        # CHECK irname has ircode associated:
        if(0):
            # if(self.ir_name!=""):
            self.ircode = HTD_INFO.tap_info.get_ir_opcode_int(self.ir_name, self.ir_agent, self.dummy_mode)
            if(self.ircode == 0):
                self.documented = 0
                self.documented_details = (("Unknown TAP agent:register - %s:%s") % (self.ir_agent, self.ir_name))
                return
            if(self.ircode > 0):
                self.ir_name = HTD_INFO.tap_info.get_ir_name(self.ircode, self.ir_agent, self.dummy_mode)
                if(self.ir_name == ""):
                    self.documented = 0
                    self.documented_details = (("Cant get TAP agent:ircode - %s:0x%x") % (self.ir_agent, self.ircode))
                    return
        # Check Irname exist in IR Agent provided
        fields_list = list(self.fields.keys())

    def send_tap_flow(self):

        # regacctype=HTD_INFO.RegAccInfo["brk_tap"]

        # regacctype[self.arguments.get_argument("bfm_mode")]["obj"].write(self,self.get_curr_flow(),self.ir_name,self.ir_agent,self.fields,regacctype,0)

        params = {}
        params["ir"] = self.ir_name
        htdPlayer.hpl_to_dut_interface.add_comment(("Sending TAP ir: %s") % (self.ir_name))
        params["agent"] = self.ir_agent
        htdPlayer.hpl_to_dut_interface.add_comment(("Sending TAP agent: %s") % (self.ir_agent))
        params["check"] = 0
        params["parallel_mode"] = self.parallel

        ir_fields = HTD_INFO.tap_info.get_ir_fields(self.ir_name, self.ir_agent)

        for dr_write in self.fields:
            counter = 0
            for dr_ir in ir_fields:
                matchObj = re.match(dr_write, dr_ir, re.M | re.I)
                if(matchObj):
                    counter = counter + 1
                    if(counter == 1):
                        params[dr_ir] = str(self.fields[dr_write]).lower()
                        htdPlayer.hpl_to_dut_interface.add_comment(
                            ("Sending TAP field: %s with value = %s") % (dr_ir, self.fields[dr_write]))
                    else:
                        htdte_logger.error(("More that 1 hit for %s") % (dr_write))
            # warning since not all fields in all agents answer the convention (mainly IPU accumulator TAP)
            if(counter == 0):
                htdte_logger.warn(("%s didn't find a match, the available fields are: %s") % (dr_write, ir_fields))

        self.get_curr_flow().exec_action(params, "TAP", self.__class__.__name__, 0, self.get_action_name())

    def action_config(self):

        Action_Tmp = {}
        Action_Tmp = self.Actions_Dictionary[self.ubp_action]
        Action_Tmp["CONFIGURED"] = 1
        self.Actions_Dictionary[self.ubp_action] = Action_Tmp

        agents = str(Action_Tmp["IP"]).split(",")
        # BRK_CTL chain
        for agent in agents:
            self.ir_agent = agent

            # Get Closer IR:
            ir_list = HTD_INFO.tap_info.get_ir_commands(self.ir_agent)
            irname = Action_Tmp["UBP"]

            for ir in ir_list:
                if irname in ir:
                    self.ir_name = ir

            self.manual = 1
            self.check = self.arguments.get_argument("check")
            self.read_modify_write = self.arguments.get_argument("read_modify_write")
            self.bfm_mode = self.arguments.get_argument("bfm_mode")
            actions = Action_Tmp["ACTION"]

            self.fields = {}
            for field in list(actions.keys()):
                if "trigger" in field or "action" in field:
                    if "[" in field:
                        fields_splitted = field.split("[")
                        field_name = fields_splitted[0]
                        # Remapping of field offset
                        power = fields_splitted[1].replace("]", "")
                        actions[field] = int(math.pow(2, int(power)))
                    else:
                        field_name = field
                else:
                    if "detect" in field:
                        field_name = ".*(CO)?.*" + field.replace(" ", "") + ".*"
                    else:
                        field_name = ".*(ACT|CO).*" + r"[\.|_]" + field.replace(" ", "") + ".*"

                self.fields[field_name] = actions[field]

            actions = Action_Tmp["TRIGGER"]

            # GET BRKPTCTL number + SETUP THE ARM
            if(Action_Tmp["REARM"] == 1):
                m = re.search(r'.+BRKPTCTL(\d+)', self.ir_name)
                if m:
                    BRKPCTL_number = m.group(1)
                    Bit2prog = 2**int(BRKPCTL_number)
                    self.fields[".*CONTROLLER_ARM.*"] = Bit2prog

            for field in list(actions.keys()):
                field_name = ""
                if "CHORD" in field:
                    field_name = field.replace("CHORD", r"\.TRIGGER")
                else:
                    if "trigger" in field:
                        field_name = field
                    else:
                        field_name = "TRIGGER.*" + field

                field_name = ".*" + field_name + ".*"
                self.fields[field_name] = actions[field]

            # MBP ACTIONS Special code for this action because allow together
            MBP_Action = Action_Tmp["MBP_ACTION"]
            if "MBP" in MBP_Action:
                MBP_Action = MBP_Action.replace("MBP:", "")
                self.fields[".*ACTIONS.MBP|fabric_actions"] = MBP_Action

            self.check_tap_var()
            tap_cmd = {}
            tap_cmd["manual"] = 1
            tap_cmd["ir"] = self.ir_name
            tap_cmd["agent"] = self.ir_agent
            tap_cmd["check"] = self.check
            tap_cmd["rmw"] = self.read_modify_write
            tap_cmd["bfm"] = self.bfm_mode
            tap_cmd["fields"] = self.fields

            self.tap_cmds.append(tap_cmd)

    def action_enable(self):

        #Ubp_action  = self.arguments.get_argument("Ubp_action")
        Action_Tmp = {}
        Action_Tmp = self.Actions_Dictionary[self.ubp_action]
        Action_Tmp["ENABLED"] = self.enable_action
        self.Actions_Dictionary[self.ubp_action] = Action_Tmp

        # BRK_EN chain
        if "BRK" in Action_Tmp["UBP"]:
            agents = str(Action_Tmp["IP"]).split(",")
            # BRK_CTL chain
            for agent in agents:
                self.ir_agent = agent

                ir_list = HTD_INFO.tap_info.get_ir_commands(self.ir_agent)
                irname = Action_Tmp["UBP"]
                irname = irname.replace("CTL", "EN")

                for ir in ir_list:
                    if irname in ir:
                        self.ir_name = ir

                self.manual = 1
                self.check = self.arguments.get_argument("check")
                self.read_modify_write = self.arguments.get_argument("read_modify_write")
                self.bfm_mode = self.arguments.get_argument("bfm_mode")
                self.fields = {}
                self.fields[".*ENABLE.*|.*brk.*en.*"] = self.enable_action

                self.check_tap_var()
                tap_cmd = {}
                tap_cmd["manual"] = 1
                tap_cmd["ir"] = self.ir_name
                tap_cmd["agent"] = self.ir_agent
                tap_cmd["check"] = self.check
                tap_cmd["rmw"] = self.read_modify_write
                tap_cmd["bfm"] = self.bfm_mode
                tap_cmd["fields"] = self.fields

                self.tap_cmds.append(tap_cmd)

    def verify_ubp_action(self):
        if(self.arguments.get_argument("Ubp_action") == ""):
            htdte_logger.error("Missing tap sequence \"bit0\" index...")
        self.ubp_action = self.arguments.get_argument("Ubp_action")

        if(self.ubp_action not in list(self.Actions_Dictionary.keys())):
            htdte_logger.error("UBP action not defined")

    def verify_arguments(self):
        self.inform(("       Verifying %s::%s:%s:%d ....") % (htd_base_action.get_action_type(self),
                                                              htd_base_action.get_action_name(self),
                                                              htd_base_action.get_action_call_file(self),
                                                              htd_base_action.get_action_call_lineno(self)))
        HTD_INFO.verify_info_ui_existence(["tap_info", "signal_info"])
        self.verify_obligatory_arguments()

        # Get profuct TE_CFG
        self.get_product_setup()
        self.parallel = self.arguments.get_argument("parallel_mode")

        # Verify if ubp direct tap action was trigger
        self.ir_name = self.arguments.get_argument("ir")
        if (self.arguments.get_argument("ir") != ""):
            self.manual = 1
            self.ir_name = self.arguments.get_argument("ir")
            self.ir_agent = self.arguments.get_argument("agent")
            self.check = self.arguments.get_argument("check")
            self.read_modify_write = self.arguments.get_argument("read_modify_write")
            self.bfm_mode = self.arguments.get_argument("bfm_mode")
            self.parallel = self.arguments.get_argument("parallel_mode")
            for field in list(self.arguments.get_not_declared_arguments().keys()):
                for arg in self.arguments.get_argument(field):
                    value = arg.value
                    self.fields[field] = value
            self.check_tap_var()

        elif(self.arguments.get_argument("reset") == "1" or self.arguments.get_argument("disable") == "1"):
            pass
        else:
            self.verify_ubp_action()

        # Verify Ubp_action exists in TE_cfg file

    def verify_last_config(self): pass

    def send_tap_array(self):

        for tap_cmd in self.tap_cmds:
            self.ir_name = tap_cmd["ir"]

            self.ir_agent = tap_cmd["agent"]
            self.check = tap_cmd["check"]
            self.read_modify_write = tap_cmd["rmw"]
            self.bfm_mode = tap_cmd["bfm"]
            self.fields = tap_cmd["fields"]
            fields_list = list(self.fields.keys())

            self.labels = {}
            self.mask = {}
            self.strobe = {}
            self.capture = {}

            self.send_tap_flow()

    def get_product_setup(self):

        Action_Tmp = {}

        # LOAD from pickel if exist
        if(htd_history_mgr.parametric_has_table(self.HistoryLabel) and self.arguments.get_argument("reset") != "1"):
            self.Actions_Dictionary = htd_history_mgr.parametric_table_get(self.HistoryLabel)
        # if os.path.isfile( "ubp_action.pickle") and os.access( "ubp_action.pickle", os.R_OK) and self.arguments.get_argument("reset") != "1":
        #	self.Actions_Dictionary = pickle.load( open( "ubp_action.pickle", "rb" ) )
        # Parse TE_CFG file
        for action in list(CFG["UBP_actions"].keys()):
            if action in list(self.Actions_Dictionary.keys()):

                Action_Tmp = {}
                Action_Tmp = self.Actions_Dictionary[action]
                if(Action_Tmp["IP"] != CFG["UBP_actions"][action]["IP"]):
                    htdte_logger.error("IP in this action diff from TE_CFG to pickle")
                if(Action_Tmp["UBP"] != CFG["UBP_actions"][action]["UBP"]):
                    htdte_logger.error("UBP in this action diff from TE_CFG to pickle")
                if(Action_Tmp["TRIGGER_STR"] != CFG["UBP_actions"][action]["TRIGGER"]):
                    htdte_logger.error("TRIGGER in this action diff from TE_CFG to pickle")
                if(Action_Tmp["ACTION_STR"] != CFG["UBP_actions"][action]["ACTION"]):
                    htdte_logger.error("ACTION in this action diff from TE_CFG to pickle")
                if(Action_Tmp["REARM"] != CFG["UBP_actions"][action]["REARM"]):
                    htdte_logger.error("REARM in this action diff from TE_CFG to pickle")
                if(Action_Tmp["ALLOW_TOG"] != CFG["UBP_actions"][action]["ALLOW_TOG"]):
                    htdte_logger.error("Allow together in this action diff from TE_CFG to pickle")

            else:
                Action_Tmp = {}
                Action_Tmp["IP"] = CFG["UBP_actions"][action]["IP"]
                Action_Tmp["UBP"] = CFG["UBP_actions"][action]["UBP"]
                Action_Tmp["TRIGGER_STR"] = CFG["UBP_actions"][action]["TRIGGER"]
                # Parsing triggers into dictionary
                Action_str = Action_Tmp["TRIGGER_STR"]
                triggers_dictionary = {}
                if "," in str(Action_str):
                    triggers = Action_str.split(",")
                    triggers_dictionary = {}
                    for trigger in triggers:
                        actions = trigger.split(":")
                        triggers_dictionary[actions[0]] = actions[1]
                else:
                    actions = Action_str.split(":")
                    triggers_dictionary[actions[0]] = actions[1]

                Action_Tmp["TRIGGER"] = triggers_dictionary
                Action_Tmp["ACTION_STR"] = CFG["UBP_actions"][action]["ACTION"]
                Action_str = Action_Tmp["ACTION_STR"]
                triggers_dictionary = {}
                if "," in str(Action_str):
                    triggers = Action_str.split(",")
                    triggers_dictionary = {}
                    for trigger in triggers:
                        actions = trigger.split(":")
                        triggers_dictionary[actions[0]] = actions[1]
                else:
                    actions = Action_str.split(":")
                    triggers_dictionary[actions[0]] = actions[1]

                Action_Tmp["ACTION"] = triggers_dictionary
                Action_Tmp["REARM"] = CFG["UBP_actions"][action]["REARM"]
                Action_Tmp["MBP_ACTION"] = CFG["UBP_actions"][action]["MBP_ACTION"] if(
                    "MBP_ACTION" in list(CFG["UBP_actions"][action].keys())) else ""
                Action_Tmp["ALLOW_TOG"] = CFG["UBP_actions"][action]["ALLOW_TOG"]if(
                    "ALLOW_TOG" in list(CFG["UBP_actions"][action].keys())) else ""
                Action_Tmp["ENABLED"] = 0
                Action_Tmp["CONFIGURED"] = 0
                self.Actions_Dictionary[action] = Action_Tmp

    def print_current_ubps(self):
        htdPlayer.hpl_to_dut_interface.add_comment(
            "-------------------------------------------------------------------------------------------------------------------------------------")
        htdPlayer.hpl_to_dut_interface.add_comment(
            "|        ACTION           |         AGENT      |     UBP MACHINE    |ENABLED | CONFIGURED |                TRIGGERS                 |")
        htdPlayer.hpl_to_dut_interface.add_comment(
            "-------------------------------------------------------------------------------------------------------------------------------------")
        for key in list(self.Actions_Dictionary.keys()):
            Action_Tmp = self.Actions_Dictionary[key]
            Enabled = Action_Tmp["ENABLED"]
            Config = Action_Tmp["CONFIGURED"]
            agent_str = Action_Tmp["IP"]
            agent_l = []
            agent_l = agent_str.split(",")
            first_agent = 1
            space = " "
            for agent in agent_l:
                if (first_agent == 0):
                    key = space

                first_trig = 1
                first_agent = 0
                for trig in Action_Tmp["TRIGGER"]:
                    if first_trig:
                        first_trig = 0
                        htdPlayer.hpl_to_dut_interface.add_comment(("|%-25s|%-20s|%-20s|%5s    |%6s      |%-27s = %10s|") % (
                            key, agent, Action_Tmp["UBP"], Enabled, Config, trig, Action_Tmp["TRIGGER"][trig]))
                    else:
                        htdPlayer.hpl_to_dut_interface.add_comment(
                            ("|%-25s|%-20s|%-20s|%5s    |%6s      |%-27s = %10s|") % (space, space, space, space, space, trig, Action_Tmp["TRIGGER"][trig]))
        htdPlayer.hpl_to_dut_interface.add_comment(
            "-------------------------------------------------------------------------------------------------------------------------------------")

    def run(self):
        self.inform(("         Running %s::%s:%s:%d \n\n") % (
            htd_base_action.get_action_type(self),
            htd_base_action.get_action_name(self),
            htd_base_action.get_action_call_file(self),
            htd_base_action.get_action_call_lineno(self)))
        self.get_product_setup()
        htdPlayer.hpl_to_dut_interface.add_comment("UBP actions status at start of action")
        self.print_current_ubps()

        if(self.arguments.get_argument("ir") == "" and self.arguments.get_argument("disable") != "1" and self.arguments.get_argument("reset") != "1"):
            Action_Tmp = {}
            Action_Tmp = self.Actions_Dictionary[self.ubp_action]
            if(Action_Tmp["ENABLED"] == 1):
                # DO Nothing because is enabled
                htdPlayer.hpl_to_dut_interface.add_comment(("uBP action already enabled: %s") % (self.ubp_action))
            else:
                for key in list(self.Actions_Dictionary.keys()):
                    Action_Tmp_2 = {}
                    Action_Tmp_2 = self.Actions_Dictionary[key]
                    if(Action_Tmp_2["ENABLED"] == 1):
                        if(Action_Tmp_2["TRIGGER_STR"] == Action_Tmp["TRIGGER_STR"] and not self.arguments.get_argument("allow_shared_trigger")):
                            Temp_ubp_action = self.ubp_action
                            self.ubp_action = key
                            htdPlayer.hpl_to_dut_interface.add_comment(
                                ("Disabling uBP action because conflict with same MBP pin enabled: %s") % (self.ubp_action))
                            self.enable_action = 0
                            self.action_enable()
                            # Send disable

                            self.ubp_action = Temp_ubp_action
                    if(Action_Tmp_2["UBP"] == Action_Tmp["UBP"] and key != self.ubp_action):
                        if(Action_Tmp_2["IP"] == Action_Tmp["IP"]):
                            Action_Tmp_2["CONFIGURED"] = 0
                            htdPlayer.hpl_to_dut_interface.add_comment(
                                ("Setting uBP action as de-configured because conflict with same UBP in use: %s") % (self.ubp_action))
                            self.Actions_Dictionary[key] = Action_Tmp_2

                if(Action_Tmp["CONFIGURED"] == 0):
                    self.action_config()
                    htdPlayer.hpl_to_dut_interface.add_comment(("Configuring uBP action: %s") % (self.ubp_action))
                else:
                    htdPlayer.hpl_to_dut_interface.add_comment(
                        ("uBP action already configured: %s") % (self.ubp_action))
                self.enable_action = 1
                self.action_enable()
                htdPlayer.hpl_to_dut_interface.add_comment(("Enabling uBP action: %s") % (self.ubp_action))
        # Disabling logic:

        if(self.arguments.get_argument("disable") == "1"):
            for key in list(self.Actions_Dictionary.keys()):
                Action_Tmp_2 = {}
                Action_Tmp_2 = self.Actions_Dictionary[key]
                if(Action_Tmp_2["ENABLED"] == 1 and (self.arguments.get_argument("Ubp_action") == key or self.arguments.get_argument("Ubp_action") == "")):  # mask the Ubp_action given or mask all Ubp action if Ubp_action not set
                    self.ubp_action = key
                    htdPlayer.hpl_to_dut_interface.add_comment(("Disabling uBP action %s") % (self.ubp_action))
                    self.enable_action = 0
                    self.action_enable()                

        if self.arguments.get_argument("ir") != "":
            self.send_tap_flow()
        else:
            self.send_tap_array()

        #if(not self.get_curr_flow().is_verification_mode()): pickle.dump(self.Actions_Dictionary, open( "ubp_action.pickle", "wb" ) )
        htd_history_mgr.parametric_table_capture(self.HistoryLabel, self.Actions_Dictionary)

        htdPlayer.hpl_to_dut_interface.add_comment("UBP actions status at end of action")
        self.print_current_ubps()
