from htd_basic_action import *


class EFSM (htd_base_action):
    def __init__(self, action_name, source_file, source_lineno, currentFlow, is_internal):
        htd_base_action.__init__(self, self.__class__.__name__, action_name, source_file, source_lineno, currentFlow, is_internal)
        self.arguments.set_argument("source", 1, "Specify which source for this action")
        self.arguments.declare_arg("FSM_STATE", "The FSM State to change to", "string", "none", 1)
        self.arguments.declare_arg("waitcycles", "Amout of time to wait for the state to change", "int", 0, 1)
        self.arguments.declare_arg("run_pin", "Pin used to initiate FSM change", "string", "yyinitrun", 0)
        self.arguments.declare_arg("ack_pin", "Pin used to acknowledge FSM change", "string", "yyINITACK", 0)
        self.arguments.declare_arg("tb_hack_hook", "Provide hook to output TB hacks in mid ation", "string", "", 0)

    def get_action_not_declared_argument_names(self): pass  # NA - all arguments declared in init

    def verify_arguments(self):
        self.inform(("       Verifying %s::%s:%s:%d ....") % (htd_base_action.get_action_type(self),
                                                              htd_base_action.get_action_name(self),
                                                              htd_base_action.get_action_call_file(self),
                                                              htd_base_action.get_action_call_lineno(self)))

        self.verify_obligatory_arguments()

        if self.arguments.get_argument("FSM_STATE") not in HTD_INFO.dict_EDRAM_STATES:
            htdte_logger.error("Invalid FSM State %s" % self.arguments.get_argument("FSM_STATE"))

        if self.arguments.get_argument("waitcycles") < 0:
            htdte_logger.error("Param waitcylcles must be positive")

    def run(self):

        self.get_curr_flow().exec_action({"op": "WAIT", "edram_te/edram/fuse/misctapconfigs/LRGInitFsmXnn1H": 1,
                                          "waitcycles": 1000}, "SIG", self.__class__.__name__, 0, self.get_action_name())

        fsm_state = self.arguments.get_argument("FSM_STATE")
        ack_pin = self.arguments.get_argument("ack_pin")
        run_pin = self.arguments.get_argument("run_pin")

        htdPlayer.hpl_to_dut_interface.label("EFSM_%s" % fsm_state)

        htdPlayer.hpl_to_dut_interface.set_pattern_info("INIT_DEBUG: Driving init for step=%s" % fsm_state)
        # Drive the 6 bit FSM_STATE on the RUN pin, and hold final 1
        for bit in '1' + format(HTD_INFO.dict_EDRAM_STATES[fsm_state], 'b').zfill(6) + '1':
            self.get_curr_flow().exec_action({"op": "SET", run_pin: bit}, "SIG", self.__class__.__name__, 0, self.get_action_name())

        # Parts of PRG TB need to be configured mid step
        if self.arguments.get_argument("tb_hack_hook") != "":
            htdPlayer.hpl_to_dut_interface.write_itpp_cmd(self.arguments.get_argument("tb_hack_hook"))

        # Wait for ACK to go high
        htdPlayer.hpl_to_dut_interface.set_pattern_info("INIT_DEBUG: Waiting for ack for step=%s" % fsm_state)
        self.get_curr_flow().exec_action({"op": "WAIT", ack_pin: 1, "waitcycles": self.arguments.get_argument(
            "waitcycles")}, "SIG", self.__class__.__name__, 0, self.get_action_name())
        htdPlayer.hpl_to_dut_interface.write_itpp_cmd("vector:  %s(H);" % ack_pin)
        htdPlayer.hpl_to_dut_interface.set_pattern_info("INIT_DEBUG: Got ack for step=%s" % fsm_state)

        # Release RUN
        self.get_curr_flow().exec_action({"op": "SET", run_pin: 0}, "SIG", self.__class__.__name__, 0, self.get_action_name())
        # Wait for ACK to clear
        self.get_curr_flow().exec_action({"op": "WAIT", ack_pin: 0, "waitcycles": 20}, "SIG", self.__class__.__name__, 0, self.get_action_name())
        htdPlayer.hpl_to_dut_interface.write_itpp_cmd("vector: %s(L);" % ack_pin)
