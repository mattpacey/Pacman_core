from htd_basic_action import *
from htd_utilities import *
from htd_collaterals import *
from htd_player_top import *
# ---------------------------------------------


class CLOCK(htd_base_action):

    def __init__(self, action_name, source_file, source_lineno, currentFlow, is_internal):
        htd_base_action.__init__(self, self.__class__.__name__, action_name, source_file, source_lineno, currentFlow,
                                 is_internal)
        self.clock_action_types = ["WAIT", "CHECK"]
        self.arguments.set_argument("source", 1, "Specify which source for this action")
        self.arguments.declare_arg("op", ("Clock action type.Supported types are: %s..") % (str(self.clock_action_types)), self.clock_action_types, "", 1)
        self.arguments.declare_arg("sel", "Used as a wildcard in regexp to filter in actual clocks from multiple module matching	", "string", "", 0)
        self.arguments.declare_arg("clock", "Used as a wildcard in regexp to filter in actual clocks from multiple module matching	", "string", "", 1)
        self.arguments.declare_arg("freq", "Used as a wildcard in regexp to filter in actual clocks from multiple module matching	", "string", "", 1)
        self.arguments.declare_arg("average", "Number of cycles on which we check the average length of the clock", "int", "", 1)
        # ---Set global argument postalignment to 0 - no alignment for clock actions need
        # ---------Define unique action indexing by declared arguments ------------------
        self.assign_action_indexing(["op"])

    def arguments_override(self):
        pass
        # ---Set global argument postalignment to 0 - no alignment for clock actions need

    # ----------------------
    def get_action_not_declared_argument_names(self):
        pass

    # ------------------
    def verify_arguments(self):
        self.inform(("       Verifying %s::%s:%s:%d ....") % (htd_base_action.get_action_type(self),
                                                              htd_base_action.get_action_name(self),
                                                              htd_base_action.get_action_call_file(self),
                                                              htd_base_action.get_action_call_lineno(self)))
        HTD_INFO.verify_info_ui_existence(["signal_info"])
        if (self.dummy_mode):
            return
        # ---Verify Clock path existence
        status_ver = True
        for clock in self.get_not_declared_arguments():
            for s in HTD_INFO.signal_info.extract_full_signal_path(clock, -1, -1, self.get_action_argument("sel")):
                stat = htdPlayer.hplSignalMgr.signal_exists(clock)
                self.inform(("       Verifying clock %s....%s") % (s, ("PASS" if (stat) else "FAIL")))
                status_ver = status_ver and stat
        if (not status_ver):
            self.error(("       Verification fail (one or more clocks are not exists on current DUT model."), 1)

    def check_clock_value(self, clock, freq):
        if (isinstance(freq, str)):
            self.inform("freq {} is string ".format(freq))
            if(re.search('ghz', freq, re.IGNORECASE) is not None):
                frequency_unit = "Ghz"
            if(re.search('mhz', freq, re.IGNORECASE) is not None):
                frequency_unit = "Mhz"
            if(re.search('khz', freq, re.IGNORECASE) is not None):
                frequency_unit = "Khz"

            frequency = re.search(r'\d+', freq).group(0)

            self.inform("Expected clock frequency is {} in {} ".format(frequency, frequency_unit))
        else:
            self.error(("Actions's (%s) illegal clock value of %s, only supports  <frequency><Ghz/Mhz/Khz> s.a. 100Mhz for %s " % (self.__action_name__, freq, clock)), 1)

    # ------------------------------------------------------------------------

    def run(self):
        # FIXME - add actual action execution
        self.inform(("         Running %s::%s:%s:%d \n\n") % (
            htd_base_action.get_action_type(self),
            htd_base_action.get_action_name(self),
            htd_base_action.get_action_call_file(self),
            htd_base_action.get_action_call_lineno(self)))

        waitcycles = int(self.get_action_argument("waitcycles"))
        maxtimeout = int(self.arguments.get_argument("maxtimeout"))
        refclock = self.get_action_argument("refclock")
        clock = self.get_action_argument("clock")
        freq = self.get_action_argument("freq")
        selector = self.get_action_argument("sel")
        opcode = self.get_action_argument("op")
        average = self.get_action_argument("average")
        self.inform("htd_clock_action: Expected clock {} frequency is {} ".format(clock, freq))
        # --------------------------------------------------------------

        if (self.get_action_argument("op") == "WAIT"):
            self.check_clock_value(clock, freq)
            htdPlayer.hplSignalMgr.clock_wait(clock, freq, waitcycles, maxtimeout, refclock, selector)
        # ---------------------
        elif (opcode == "CHECK"):
            self.check_clock_value(clock, freq)
            htdPlayer.hplSignalMgr.clock_check_average(clock, freq, waitcycles, refclock, average, selector)
        else:
            self.error((("Action's (%s) illegal/unsupported CLOCK opcode - \"op\"=\"%s\" ") % (self.__action_name__, opcode)), 1)

    def get_defined_label(self):
        label_name = "%s__%s" % (self.get_action_name(), self.get_action_argument("op"))
        return label_name
