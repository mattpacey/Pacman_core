from htd_basic_action import *
from htd_tap_action import *
from htd_utilities import *
from htd_collaterals import *
from htd_player_top import *

# ---------------------------------------
#
# ---------------------------------------
# ---------------------------------------------

# FIXME: inconsistent of usage of self.error/self.inform and htdte.logger.error/inform makes code hard to comprehend


class UBPTRIGGER(htd_base_action):

    def __init__(self, action_name, source_file, source_lineno, currentFlow, is_internal):

        htd_base_action.__init__(self, self.__class__.__name__, action_name,
                                 source_file, source_lineno, currentFlow, is_internal)

        # Tap parameters
        self.manual = 0
        self.ir_name = ""
        #self.ir_agent = ""
        self.fields = {}
        self.dr = "1"
        self.dr_size = 1
        self.check = 0
        self.read_modify_write = 0
        self.bfm_mode = "tap"
        self.parallel = 1
        self.vector = []
        #self.enable_action = 0

        # internal paramenters
        self.tap_cmds = []
        self.ubp_action_l = []
        self.mbp_pin_triggers = {}
        self.chord_pin_triggers = {}
        #self.mbp_pin = -1
        self.action_dr = ""
        self.action_param = ""
        self.cluster_model_mode = (self.get_curr_flow() is not None
                                   and self.get_curr_flow().cluster_model_mode)
        # --Generate MBP by TAP instruction
        self.mbp_tap_triggers = {}  # used to generate MBP pulsee by TAP instruction
        # flow parameters
        self.Actions_Dictionary = {}
        self.HistoryLabel = "UBP_history"

     # BRK Arguments
        # FIXME: Ip and BrkId are defined but not used!
        self.arguments.set_argument("source", 1, "Specify which source for this action")
        self.arguments.declare_arg("Ubp_action", "uBP action to perform        ", "string", "", 0)
        self.arguments.declare_arg("Ip", "Ip where you want to configure the BRK ", "string", "", 0)
        self.arguments.declare_arg("BrkId", "Id of the BRKCTL you want to configure ", "int", 0, 0)
        self.arguments.declare_arg("trigger_by_tap", "Emulate MBP trigger by TAP instruction ", "bool", 0, 0)

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
        self.arguments.declare_arg("force_enable",
                                   "Parameter to force writing the enable bit", "bool", 0, 0)
     #Jitbit #22185: Add new MBP operation "PULSE" to generate number of delay vectors following the domain of the pin, instead of existing "FORCE" which is TCK vector. The default MBP operation type will be "FORCE".
        self.arguments.declare_arg("MBP_type",
                                   "The MBP type: FORCE|PULSE ", ["FORCE", "PULSE"], "FORCE", 0)

        self.tap_protocol = ""
        # FIXME: conditioning and priority between TE and HPL is not clear
        # FIXME: code is giving TE higher priority to override, is this the case?
        # FIXME: if yes, if conditioning can be improved
        if("HPL" in list(CFG.keys())):
            if("tap_mode" in list(CFG["HPL"].keys())):
                self.tap_protocol = CFG["HPL"]["tap_mode"]
            if("TE" in list(CFG.keys())):
                if("tap_mode" in list(CFG["TE"].keys())):
                    self.tap_protocol = CFG["TE"]["tap_mode"]
                if(self.tap_protocol not in ["tapnetwork", "taplink"]):
                    self.error(("Action's (%s) : Illegal TAP protocol type selection in CFG[\"TE\"][\"tap_mode\"]: expected \"tapnetwork\" or \"taplink\" ,received - \"%s\" ") % (
                        self.__action_name__, self.tap_protocol), 1)

    def send_tap_flow(self):
        """
        executing TAP action with info from:
             ir_name, ir_agent, fields

        modify: none
        :return: none
        """

        # regacctype=HTD_INFO.RegAccInfo["brk_tap"]

        # regacctype[self.arguments.get_argument("bfm_mode")]["obj"].write(self,self.get_curr_flow(),self.ir_name,self.ir_agent,self.fields,regacctype,0)

        params = {}
        params["ir"] = self.ir_name
        htdPlayer.hpl_to_dut_interface.add_comment(("Sending TAP ir: %s") % (self.ir_name))
        params["agent"] = self.ir_agent
        htdPlayer.hpl_to_dut_interface.add_comment(("Sending TAP agent: %s") % (self.ir_agent))
        params["check"] = 0
        params["parallel_mode"] = self.arguments.get_argument("parallel_mode")

        ir_fields = HTD_INFO.tap_info.get_ir_fields(self.ir_name, self.ir_agent)

        # compare each input field to valid field from register
        # if matches, setup to params[dr_ir] for TAP action write
        for dr_write in self.fields:
            for dr_ir in ir_fields:
                matchObj = re.match(dr_write, dr_ir, re.M | re.I)
                if(matchObj):
                    params[dr_ir] = str(self.fields[dr_write]).lower()
                    htdPlayer.hpl_to_dut_interface.add_comment(
                        ("Sending TAP field: %s with value = %s") % (dr_ir, self.fields[dr_write]))
        self.get_curr_flow().exec_action(params, "TAP", self.__class__.__name__, 0, self.get_action_name())

    def send_tap_array(self):
        """
        loop through self.tap_cmds to get all the TAP actions needed,
        assign to respective self.<var>, calls send_tap_flow for exec

        modify: self.ir_name, ir_agent etc. for TAP action usage
        :return: none
        """

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

    def check_tap_var(self):
        # FIXME: this looks like some setup for other script usage that doesn't affect functionality
        #        could this be handled differently?
        #       self.ir_name is not assigned prior to running this function
        """
        Base on self.ir_name, set documented and documented_details respectively
        documented and documented_details are for used in htd_statstic.py

        :return: none
        """
        # CHECK irname has ircode associated:
        if(self.ir_name != ""):
            self.ircode = HTD_INFO.tap_info.get_ir_opcode_int(self.ir_name, self.ir_agent, self.dummy_mode)
            if(self.ircode == 0):
                self.documented = 0
                self.documented_details = (("Unknown TAP agent:register - %s:%s") % (self.ir_agent, self.ir_name))
                return
            # FIXME: should the below be elif?
            if(self.ircode > 0):
                # FIXME: uses ir_name to get ircode, using back ircode to get ir_name, redundant?
                self.ir_name = HTD_INFO.tap_info.get_ir_name(self.ircode, self.ir_agent, self.dummy_mode)
                if(self.ir_name == ""):
                    self.documented = 0
                    self.documented_details = (("Cant get TAP agent:ircode - %s:0x%x") % (self.ir_agent, self.ircode))
                    return
        # FIXME: comment says check Irname existance, but code is just getting keys from self.fields
        # Check Irname exist in IR Agent provided
        fields_list = list(self.fields.keys())

    def action_enable(self, ubp_action, enable_action):
        """
        Setup Set/Unset BRKPTEN register of the corresponding action into self.tap_cmds

        modify: self.tap_cmds, self.Actions_Dictionary[ubp_action]["ENABLED"]
        :param ubp_action: str, UBP action name to configure
        :param enable_action: bool, disable or enable UBP
        :return: none
        """
        resolved_agent = ""
        resolved_irname = ""
        #Ubp_action  = self.arguments.get_argument("Ubp_action")
        # update ENABLED field in Actions_Dictionary as defined from TE_cfg
        Action_Tmp = {}
        # FIXME: assigning dictionary resulted in a pointer, check if this is the intended usage
        # FIXME: should have been a direct assign to self.Actions_Dictionary[ubp_action]["ENABLED"]
        Action_Tmp = self.Actions_Dictionary[ubp_action]
        Action_Tmp["ENABLED"] = enable_action
        self.Actions_Dictionary[ubp_action] = Action_Tmp

        # BRK_EN chain
        # FIXME: is there any other cases without BRK?
        if "BRK" in Action_Tmp["UBP"]:
            # definition in TE_cfg supports multiple IP for same action
            agents = str(Action_Tmp["IP"]).split(",")
            # BRK_CTL chain
            for agent in agents:

                resolved_agent = agent
                ir_list = HTD_INFO.tap_info.get_ir_commands(agent)
                irname = Action_Tmp["UBP"]
                irname = irname.replace("CTL", "EN")

                # get exact UBP reg name from full list
                for ir in ir_list:
                    if irname in ir:
                        resolved_irname = ir

                self.manual = 1
                self.check = self.arguments.get_argument("check")
                self.read_modify_write = self.arguments.get_argument("read_modify_write")
                self.bfm_mode = self.arguments.get_argument("bfm_mode")
                self.fields = {}
                self.fields[".*ENABLE.*|.*brk.*en.*"] = enable_action

                self.check_tap_var()
                tap_cmd = {}
                tap_cmd["manual"] = 1
                tap_cmd["ir"] = resolved_irname
                tap_cmd["agent"] = resolved_agent
                tap_cmd["check"] = self.check
                tap_cmd["rmw"] = self.read_modify_write
                tap_cmd["bfm"] = self.bfm_mode
                tap_cmd["fields"] = self.fields

                self.tap_cmds.append(tap_cmd)
    # ------------------------------------------

    def debug_readback(self): pass

    def get_action_not_declared_argument_names(self): pass
    # ------------------------------------------

    def mbp_to_trigger(self, ubp_action_l):
        """
        For each ubp_action_l, base on config in self.Actions_Dictionary,
         setup the corresponding MBP pin and vector pulse, store into self.mbp_pin_triggers/self.chord_pin_triggers.
         cluster_model is active high, 10 pulse; for active low, 01 pulse

        :param ubp_action_l: list of Ubp_action as defined during action call, should match TE_cfg setup
        modify: self.mbp_pin_triggers, self.chord_pin_triggers
        :return: none
        """
        # --Browse all actions and merge triggers--
        prev_triggers = {}
        for ubp_action in ubp_action_l:
            Action = {}
            Action_Tmp = {}
            Action = self.Actions_Dictionary[ubp_action]
            Action_Tmp = Action["TRIGGER"]

            # Check MBP to trigger

            if "FIRST_INSTRUCTION_FETCH" in list(Action_Tmp.keys()):
                htdte_logger.error("Can't Trigger a Fist Fetch action from itpp")

            # "MBP" and "fabric_triggers" are keywords for MBP pin toggle, as defined in TE_cfg
            # checks for BRK as oppose to CHORD
            if ("MBP" in list(Action_Tmp.keys()) or "fabric_triggers" in list(Action_Tmp.keys())) and "BRK" in Action["UBP"]:
                # TRIGGER="MBP:0x2"
                # translates into {"MBP": 0x2}
                if "MBP" in list(Action_Tmp.keys()):
                    MBP = Action_Tmp["MBP"]
                # FIXME: should this be elif? since MBP will get overwritten
                # FIXME: get_product_setup allows multiple trigger, but otherwise here
                if "fabric_triggers" in list(Action_Tmp.keys()):
                    MBP = Action_Tmp["fabric_triggers"]
                # FIXME: below is to get bit position for 'b1 value in MBP, could it be done in a better way?
                # FIXME: the logic only allow one-hot MBP, to figure out what's the desired usage model (one-hot or not)
                # FIXME: and probably filter and error out during get_product_setup if only one-hot
                MBP = MBP.replace("0x", "")
                MBP_binary = list(bin(int(float(MBP))))
                MBP_binary.reverse()
                mbp_pin = MBP_binary.index("1")
                if(not self.arguments.get_argument("trigger_by_tap")):
                    # init mbp_pin
                    if(mbp_pin not in list(self.mbp_pin_triggers.keys())):
                        self.mbp_pin_triggers[mbp_pin] = []
                    # multiple actions could use same trigger, if same trigger used, skip the repeat setup
                    # FIXME: prev_triggers can just be a list instead of dict, then the if conditioning can be cleaner
                    if("MBP" not in list(prev_triggers.keys()) or mbp_pin not in prev_triggers["MBP"]):
                        # pulsing 1 or 0 depending on active low or high
                        # (esherer) IPFication:  If we're driving an IP at cluster model then we're active high, otherwise, active low
                        if (self.cluster_model_mode):
                            self.mbp_pin_triggers[mbp_pin].append(1)
                            self.mbp_pin_triggers[mbp_pin].append(0)
                        else:
                            self.mbp_pin_triggers[mbp_pin].append(0)
                            self.mbp_pin_triggers[mbp_pin].append(1)

                        if(not self.get_curr_flow().is_verification_mode()):
                            htdPlayer.hpl_to_dut_interface.add_comment(("Generating a MBP TRIGGER = %s") % (MBP))
                            htdPlayer.hpl_to_dut_interface.add_comment(
                                ("Generating a VECTORS = %s") % (str(self.mbp_pin_triggers[mbp_pin])))
                        if("MBP" not in list(prev_triggers.keys())):
                            prev_triggers["MBP"] = []
                        prev_triggers["MBP"].append(mbp_pin)
                else:
                    # -----Trigger by tap cmd
                    # --Final merged trigger entry stored in self.mbp_tap_triggers[trigger_agent][trigger_ir]["actionName"],self.mbp_tap_triggers[trigger_agent][trigger_ir]["field"]=val
                    if("TAP_TRIGGER_CMD" not in list(Action.keys())):
                        htdte_logger.error(
                            "Trying to asssign MBP trigger bt TAP cmd , \
                            while missing Action[\"TAP_TRIGGER_CMD\"] definition.\
                            Pls. verify action definition corectness in TE_cfg.xml")
                    trigger_agent = Action["TAP_TRIGGER_CMD"]["agent"]
                    trigger_ir = Action["TAP_TRIGGER_CMD"]["ir"]
                    if(trigger_agent not in list(self.mbp_tap_triggers.keys())):
                        self.mbp_tap_triggers[trigger_agent] = {}
                    if(trigger_ir not in list(self.mbp_tap_triggers.keys())):
                        self.mbp_tap_triggers[trigger_agent][trigger_ir] = {}
                    updated = False
                    # other than "agent", "ir", "actionName", the rest are TAP register field
                    for param in [x for x in list(Action["TAP_TRIGGER_CMD"].keys())
                                  if (x not in ["agent", "ir", "actionName"])]:
                        # populates TE_cfg params into mbp_tap_triggers
                        if(param not in list(self.mbp_tap_triggers[trigger_agent][trigger_ir].keys())):
                            self.mbp_tap_triggers[trigger_agent][trigger_ir][param] = Action["TAP_TRIGGER_CMD"][param]
                            updated = True
                    if(updated):
                        # piping actionName for all ubp_action_l
                        self.mbp_tap_triggers[trigger_agent][trigger_ir]["actionName"] = ("%s_%s") % \
                            (self.mbp_tap_triggers[trigger_agent][trigger_ir]["actionName"] if(
                                "actionName" in list(self.mbp_tap_triggers[trigger_agent][trigger_ir].keys())) else "",
                             Action["TAP_TRIGGER_CMD"]["actionName"])
            # --------------------------------------------------
            # FIXME: should this be elif?
            if "CHORD" in Action["UBP"]:
                # FIXME: why hardcode to 0?
                # FIXME: why even use this level on chord_pin_trigger, can this be trimmed one level down?
                mbp_pin = 0
                # FIXME: the method of extraction of value is not consistent with MBP
                MBP = Action_Tmp["CHORD"]
                MBP_int = int(MBP, 0)
                if(mbp_pin not in list(self.chord_pin_triggers.keys())):
                    self.chord_pin_triggers[mbp_pin] = {}
                if(MBP_int not in list(self.chord_pin_triggers[mbp_pin].keys())):
                    self.chord_pin_triggers[mbp_pin][MBP_int] = []
                # FIXME: prev_triggers can just be a list, there is no need to combine CHORD and MBP to a dict
                if("CHORD" not in list(prev_triggers.keys()) or MBP_int not in prev_triggers["CHORD"]):
                    # FIXME: the method of generation of pulse is not consistent with MBP
                    if (self.cluster_model_mode):
                        MBP_int = MBP_int ^ 0xF
                        self.chord_pin_triggers[mbp_pin][MBP_int] = list("0{:04b}1".format(MBP_int))
                    else:
                        self.chord_pin_triggers[mbp_pin][MBP_int] = list("1{:04b}0".format(MBP_int))
                    self.chord_pin_triggers[mbp_pin][MBP_int].reverse()
                    if(not self.get_curr_flow().is_verification_mode()):
                        htdPlayer.hpl_to_dut_interface.add_comment(("Generating a CHORD = %s") % (MBP))
                        htdPlayer.hpl_to_dut_interface.add_comment(
                            ("Generating a VECTORS = %s") % (str(self.chord_pin_triggers[mbp_pin][MBP_int])))
                    if("CHORD" not in list(prev_triggers.keys())):
                        prev_triggers["CHORD"] = []
                    prev_triggers["CHORD"].append(MBP_int)
    # --------------------------------------------------------

    def verify_ubp_action(self):
        """
        Process "Ubp_action" into list and call mbp_to_trigger

        :return: none
        """
        if(self.arguments.get_argument("Ubp_action") == ""):
            htdte_logger.error("Missing tap sequence \"bit0\" index...")
        self.ubp_action_l = self.arguments.get_argument("Ubp_action").split(",")

        for ubp_action in self.ubp_action_l:
            if(ubp_action not in list(self.Actions_Dictionary.keys())):
                htdte_logger.error(("UBP action - \"%s\" not defined") % (ubp_action))
        # --Check and programming all triggers
        self.mbp_to_trigger(self.ubp_action_l)
    # --------------------------------------------------------

    def verify_arguments(self):
        """
        Check mandatory config/argument/setup, includes:
            TE_cfg CFG[INFO]: tap_info, signal_info
            self.argument: arguments with obligatory key
        Parse and verify ubp config from TE_cfg CFG["UBP_actions"]
        Check TAP_TRIGGER_CMD setup in TE_cfg to qualify trigger_by_tap requirement

        :return: none
        """
        self.inform(("       Verifying %s::%s:%s:%d ....") % (htd_base_action.get_action_type(self),
                                                              htd_base_action.get_action_name(self),
                                                              htd_base_action.get_action_call_file(self),
                                                              htd_base_action.get_action_call_lineno(self)))
        # check if the UI is defined in TE_cfg under INFO
        HTD_INFO.verify_info_ui_existence(["tap_info", "signal_info"])

        # check if obligatory arguments are defined & dual_read_write_mode
        # each argument is a dictionary with a "obligatory" key
        # error out if obligatory arguments are not "assigned"
        # dual_read_write is to read and set to a different value concurrently
        # depends on if mode is enable
        # FIXME: verify_obligatory_arguments is called under htd_basic_flow.htd_base_flow.exec_action_obj,
        # FIXME: which is excuted right after verify_arguments, do we still need it here?
        self.verify_obligatory_arguments()
        self.get_product_setup()

        # option to force trigger by TAP via TE_cfg configuration
        if("TE"in list(CFG.keys()) and "ubp_trigger_by_tap_only" in list(CFG["TE"].keys()) and CFG["TE"]["ubp_trigger_by_tap_only"]):
            self.inform((" Found CFG[\"TE\"][\"ubp_trigger_by_tap_only\"]=1... Enforcing ubp_trigger_by_tap_only=1.. "))
            self.arguments.set_argument("trigger_by_tap", 1)

        self.verify_ubp_action()

        # if forced trigger by TAP, check if UBP_action config in TE_cfg is setup with TAP_TRIGGER_CMD
        # FIXME: should this be in part of the qualification above? does this has any dependency on verify_ubp_action?
        # FIXME: or will it error out during verify_ubp_action and this is redundant?
        # FIXME: or should we catch the error inside verify_ubp_action instead?
        if(self.arguments.get_argument("trigger_by_tap")):
            for action in list(CFG["UBP_actions"].keys()):
                # can't trigger by tap if TRIGGER of the action uses MBP pin, but TAP_TRIGGER_CMD is not defined
                # FIXME: Actions_Dictionary is obtained from TE_cfg, is the first condition needed?
                if(action in list(self.Actions_Dictionary.keys()) and "MBP" in self.Actions_Dictionary[action]["TRIGGER"]):
                    if("TAP_TRIGGER_CMD" not in list(self.Actions_Dictionary[action].keys()) or self.Actions_Dictionary[action]["TAP_TRIGGER_CMD"] == ""):
                        htdte_logger.error(
                            ("Trying to use trigger by tap cmd , while missing CFG[\"UBP_actions\"][\"%s\"][\"TAP_TRIGGER_CMD\"]...") % (action))

    def parse_tap_trigger_cmd(self, action, entry):
        """
        Process input entry into TAP action compliance input with
            actionName, agent, ir, <fields>

        :param action: str, UBP action name
        :param entry: str, trigger detail with format <agent>.<reg>:<field1>=<val1>[,<fieldN>=<valN>]
        :return: dict containing the necessary arguments for TAP action
        """
        # format <agent>.<cmd>:<field1>=<val1>[,<fieldN>=<valN>]
        pair_cmd_fields_l = entry.replace(" ", "").split(":")
        if(len(pair_cmd_fields_l) != 2):
            htdte_logger.error(
                ("Improper format found for CFG[\"UBP_actions\"][\"%s\"][\"TAP_TRIGGER_CMD\"].\nExpected format <agent>.<cmd>:<field1>=<val1>[,<fieldN>=<valN>] , while received - %s") % (action, entry))
        cmd_entry = pair_cmd_fields_l[0]
        fields_entries_l = pair_cmd_fields_l[1].split(",")

        # process cmd_entry into agent and ir
        tap_action_params = {}
        m = re.match(r"^([A-z0-9_\.]+)\.(.+)$", cmd_entry)
        if(not m):
            htdte_logger.error(
                ("Improper TAP cmd format found for CFG[\"UBP_actions\"][\"%s\"][\"TAP_TRIGGER_CMD\"].\nExpected cmd format <agent>.<cmd>:... , while received - %s") % (action, cmd_entry))
        tap_action_params["actionName"] = ("UbpAction%s_TriggerByTap") % (action)
        tap_action_params["agent"] = m.groups()[0]
        tap_action_params["ir"] = m.groups()[1]

        # process every fields_entries into field:value pairs
        for f in fields_entries_l:
            m = re.match(r"^([A-z0-9_]+)=(\d*[bx]*[A-Fa-f0-9]+)$", f)
            if(not m):
                htdte_logger.error(
                    ("Improper TAP cmd:field format found for CFG[\"UBP_actions\"][\"%s\"][\"TAP_TRIGGER_CMD\"].\nExpected cmd format <agent>.<cmd>:([A-z0-9_]+)=(\d*[bx]*[A-Fa-f0-9]+)... , while received - %s") % (action, f))
            else:
                tap_action_params[m.groups()[0]] = m.groups()[1]
        # --------
        return tap_action_params
    # -------------------------------

    def get_product_setup(self):
        """
        get ubp config setup either from pickle or TE_cfg
        store into Actions_Dictionary[action]

        modify: self.Actions_Dictionary
        :return: none
        """
        Action_Tmp = {}

        # get from <chkptfile> as defined in TE_cfg at output dir
        # LOAD from pickel if exist
        if(htd_history_mgr.parametric_has_table(self.HistoryLabel)):
            self.Actions_Dictionary = htd_history_mgr.parametric_table_get(self.HistoryLabel)
        # if os.path.isfile( "ubp_action.pickle") and os.access( "ubp_action.pickle", os.R_OK):
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
                # FIXME: multiple trigger is allowed here, but not handled under mbp_to_trigger
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
                # FIXME: ALLOW_TOG is not used
                Action_Tmp["ALLOW_TOG"] = CFG["UBP_actions"][action]["ALLOW_TOG"]
                Action_Tmp["ENABLED"] = 0
                Action_Tmp["CONFIGURED"] = 0
            # -------------------
            # TODO: why does the following needs to be outside of else? does pickle dont have TAP_TRIGGER_CMD? why?
            if("TAP_TRIGGER_CMD" in list(CFG["UBP_actions"][action].keys()) and CFG["UBP_actions"][action]["TAP_TRIGGER_CMD"] != ""):
                Action_Tmp["TAP_TRIGGER_CMD"] = self.parse_tap_trigger_cmd(
                    action, CFG["UBP_actions"][action]["TAP_TRIGGER_CMD"])
            self.Actions_Dictionary[action] = Action_Tmp

    def print_current_ubps(self):
        """
        print current UBP configuration w.r.t. setup in TE_cfg
        all relevant information is getting from Actions_Dictionary hash

        :return : none
        """

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

    # ----------------------------------------------------------
    def setsignal(self):
        """
        Generates MBP pulse/TAP command for triggering, base upon values set in mbp_to_trigger of the three dict:
         mbp_pin_triggers, chord_pin_triggers, mbp_tap_triggers
         Output as exec_sig_action

        :return: none
        """
        self.MBP_type = self.arguments.get_argument("MBP_type")
        for mbp in list(self.mbp_pin_triggers.keys()):
            for value in self.mbp_pin_triggers[mbp]:
                mbp_pin = "MBP%i" % mbp
                # (esherer) IPFication:  resolve IP name - IP MBP naming convention in signals.sig should be <IPNAME>MBP#
                if (self.cluster_model_mode):
                    if(self.get_curr_flow().get_current_segment() is not None):
                        mbp_pin = self.get_curr_flow().get_current_segment().get_ip_name() + mbp_pin
                    else:
                        mbp_pin = self.get_curr_flow().get_ip_name() + mbp_pin
                
                params = {}
                params["op"] = "FORCE"
                params["check"] = 0
                params[SIGMAP(mbp_pin)] = value
                params["waitcycles"] = 1
                params["refclock"] = "bclk"
                if(not self.get_curr_flow().is_verification_mode()):
                    if(self.MBP_type == "FORCE"):
                        self.get_curr_flow().exec_action(params, "SIG", self.__class__.__name__, 0, self.get_action_name())
                    # MBP pulse cycle length, n-1 since this is a TMS wait
                    # FIXME: waitcycle can be combined into SIG with op=toggle
                    if((value == 0) and ("MBP_setting" in list(CFG.keys())) and (CFG["MBP_setting"]["MBP_WAITCYCLES"] is not None)):
                        # Jitbit #22185: the delay(wait cycles) will follow the domain of the mbp pin (requested by ICXSP)
                        if(self.MBP_type == "PULSE"):
                            self.get_curr_flow().exec_action({"op": "PULSE", "waitcycles": CFG["MBP_setting"]["MBP_WAITCYCLES"], "refclock": "tclk",
                                                              SIGMAP(mbp_pin): value}, "SIG", self.__class__.__name__, 0, self.get_action_name())
                        # else wait cycles will be defaults to TCK vector.
                        else:    
                            self.get_curr_flow().exec_action({"op": "WAIT", "waitcycles": CFG["MBP_setting"]["MBP_WAITCYCLES"], "refclock": "tclk",
                                                              "postalignment": 0, "postdelay": 0}, "GEN", self.__class__.__name__, 0, self.get_action_name())
                if(self.cluster_model_mode):
                    self.get_curr_flow().exec_action({"op": "WAIT", "waitcycles": 13, "refclock": "tclk",
                                                      "postalignment": 0, "postdelay": 0}, "GEN", self.__class__.__name__, 0, self.get_action_name())
        for chord in list(self.chord_pin_triggers.keys()):
            for mbp_pin in list(self.chord_pin_triggers[chord].keys()):
                for value in self.chord_pin_triggers[chord][mbp_pin]:
                    mbp_pin_name = ("MBP0")
                    # (esherer) IPFication:  resolve IP name - IP MBP naming convention in signals.sig should be <IPNAME>MBP#
                    # FIXME: mbp_pin is not used at all, is this the artifact if copying from mbp above?
                    if (self.cluster_model_mode):
                        if(self.get_curr_flow().get_current_segment() is not None):
                            mbp_pin = self.get_curr_flow().get_current_segment().get_ip_name() + mbp_pin
                        else:
                            mbp_pin = self.get_curr_flow().get_ip_name() + mbp_pin
                    params = {}
                    params["op"] = "FORCE"
                    params["check"] = 0
                    params[SIGMAP(mbp_pin_name)] = value
                    params["waitcycles"] = 1
                    params["refclock"] = "bclk"
                    if(not self.get_curr_flow().is_verification_mode()):
                        self.get_curr_flow().exec_action(params, "SIG", self.__class__.__name__, 0, self.get_action_name())
                    #self.get_curr_flow().exec_action({"op":"WAIT",  "waitcycles":1, "refclock":"tclk", "postalignment":0, "postdelay":0},"GEN",self.__class__.__name__,0,self.get_action_name())
        # ---TAP cmd trigger
        for tap_trigger_agnt in list(self.mbp_tap_triggers.keys()):
            for tap_trigger_ir in list(self.mbp_tap_triggers[tap_trigger_agnt].keys()):
                action_param = {}
                for param in list(self.mbp_tap_triggers[tap_trigger_agnt][tap_trigger_ir].keys()):
                    action_param[param] = self.mbp_tap_triggers[tap_trigger_agnt][tap_trigger_ir][param]
                action_param["agent"] = tap_trigger_agnt
                action_param["ir"] = tap_trigger_ir
                action_param["incremental_mode"] = 1
                self.get_curr_flow().exec_action(action_param, "TAP", self.__class__.__name__, 0, self.get_action_name())
    # ----------------------------------------------------------

    def run(self):
        """

        :return:
        """
        self.inform(("         Running %s::%s:%s:%d \n\n") % (
            htd_base_action.get_action_type(self),
            htd_base_action.get_action_name(self),
            htd_base_action.get_action_call_file(self),
            htd_base_action.get_action_call_lineno(self)))
        # setup ubp from TE_cfg, store to Action_Dictionary
        self.get_product_setup()
        # print ubp setup info from Action_Dictionary
        self.print_current_ubps()
        # self.ubp_action_l is populated by verify_ubp_action(), input from self.arguments
        for ubp_action in self.ubp_action_l:
            # DISABLE actins if needed:
            Action_Tmp = {}
            # FIXME: assigning dictionary results in a pointer, confirm if this is the intended use case
            Action_Tmp = self.Actions_Dictionary[ubp_action]
            # force reenable of UBP regardless of value from self.Actions_Dictionary
            # could be useful when unsure of DUT current state
            if self.arguments.get_argument("force_enable") == 1:
                htdte_logger.inform("Setting mbp enable tracker to 0")
                Action_Tmp["ENABLED"] = 0   # Set ENABLED on the action to 0 so that it will be re-enabled automatically
            if(Action_Tmp["ENABLED"] == 1 and not self.get_curr_flow().is_verification_mode()):
                # DO Nothing because is enabled
                htdPlayer.hpl_to_dut_interface.add_comment(("uBP action already enabled: %s") % (ubp_action))
            else:
                # cross check with all other enabled ubp actions
                # if having same trigger, disable the conflicting ubpactions (not the targeted one)
                for key in list(self.Actions_Dictionary.keys()):
                    Action_Tmp_2 = {}
                    Action_Tmp_2 = self.Actions_Dictionary[key]
                    if(Action_Tmp_2["ENABLED"] == 1):
                        if(Action_Tmp_2["TRIGGER_STR"] == Action_Tmp["TRIGGER_STR"] and key not in self.ubp_action_l):
                            # FIXME: Temp_ubp_action switching is redundant
                            Temp_ubp_action = ubp_action
                            ubp_action = key
                            htdPlayer.hpl_to_dut_interface.add_comment(
                                ("Disabling uBP action because conflict with same MBP pin enabled: %s") % (ubp_action))
                            #self.enable_action = 0
                            # setup tap action disable, actual action run is below at send_tap_array()
                            self.action_enable(ubp_action, 0)
                            # Send disable
                            ubp_action = Temp_ubp_action
            # FIXME: why update Action_Tmp
            Action_Tmp = self.Actions_Dictionary[ubp_action]
            if self.arguments.get_argument("force_enable") == 1:
                htdte_logger.inform("Setting mbp enable tracker to 0 again")
                Action_Tmp["ENABLED"] = 0   # Set ENABLED on the action to 0 so that it will be re-enabled automatically
            # ----------------------------
            if(Action_Tmp["ENABLED"] == 1 and Action_Tmp["CONFIGURED"] == 1):
                # self.setsignal()
                if(Action_Tmp["REARM"] == 1):
                    Action_Tmp["ENABLED"] = 1
                else:
                    Action_Tmp["ENABLED"] = 0
                # FIXME: the previous assign/define of Action_Tmp resulted in a pointer to original dictionary
                # FIXME: need to revisit implementation if the intention is just to update/replace original statement
                self.Actions_Dictionary[ubp_action] = Action_Tmp

            elif(Action_Tmp["ENABLED"] == 0 and Action_Tmp["CONFIGURED"] == 1):
                #self.enable_action = 1
                self.action_enable(ubp_action, 1)
                self.send_tap_array()
                # self.setsignal()
                Action_Tmp["ENABLED"] = 0
                # FIXME: pointer Action_Tmp as described above
                self.Actions_Dictionary[ubp_action] = Action_Tmp
            else:
                if(Action_Tmp["ENABLED"] == 0):
                    enabled = " Not Enabled"
                else:
                    enabled = " Enabled"
                # FIXME: there wouldn't be any case of configured
                if(Action_Tmp["CONFIGURED"] == 0):
                    configured = " Not Configured"
                else:
                    configured = " Configured"

                htdte_logger.error("You're trying to trigger (%s) an action %s and %s  please review your ubp actions" % (
                    ubp_action, enabled, configured))

            htd_history_mgr.parametric_table_capture(self.HistoryLabel, self.Actions_Dictionary)
            #if(not self.get_curr_flow().is_verification_mode()): pickle.dump(self.Actions_Dictionary, open( "ubp_action.pickle", "wb" ) )
        # -------------------------------
        # send trigger
        self.setsignal()
