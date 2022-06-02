from htd_basic_action import *
from htd_utilities import *
from htd_collaterals import *
from htd_player_top import *
# ---------------------------------------------


class SIG(htd_base_action):

    def __init__(self, action_name, source_file, source_lineno, currentFlow, is_internal):
        htd_base_action.__init__(self, self.__class__.__name__, action_name, source_file, source_lineno, currentFlow,
                                 is_internal)
        self.arguments.set_argument("source", 1, "Specify which source for this action")
        self.signal_action_types = ["WAIT", "SERIALSET", "CHECK", "CHECKNOT", "PULSE", "FORCE", "UNFORCE",
                                    "START_MONITOR", "STOP_MONITOR", "SET", "GET"]
        self.arguments.declare_arg("op",
                                   ("Signal action type.Supported types are: %s..") % (str(self.signal_action_types)),
                                   self.signal_action_types, "", 1)
        self.arguments.declare_arg("sel",
                                   "Used as a wildcard in regexp to filter in actual signals from multiple module matching	",
                                   "string", "", 0)
        self.arguments.declare_arg("peeksignal_disable", "Disable peek_signal printout", "bool", 0, 0)
        # ---Set global argument postalignment to 0 - no alignment for signal actions need
        self.arguments.set_argument("postalignment", 0, "SIG action restriction")
        self.arguments.set_argument("postdelay", 0, "SIG action restriction")
        # ---------Define unique action indexing by declared arguments ------------------
        self.assign_action_indexing(["op"])

    def arguments_override(self):
        # ---Set global argument postalignment to 0 - no alignment for signal actions need
        self.arguments.set_argument("postalignment", 0, "SIG action restriction")
        self.arguments.set_argument("postdelay", 0, "SIG action restriction")

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
        # --If SERIALSET is used , need to handle "width" parameter
        if (self.get_action_argument("op") == "SERIALSET"):
            self.arguments.declare_arg("width", "Serial sequece set length..", "int", 0, 1)
        # ------Exit in dummy mode
        if (self.dummy_mode):
            return
        # ---Verify Signal path existence
        status_ver = True
        for sig in self.get_not_declared_arguments():
            for s in HTD_INFO.signal_info.extract_full_signal_path(sig, -1, -1, self.get_action_argument("sel")):
                stat = htdPlayer.hplSignalMgr.signal_exists(sig)
                self.inform(("       Verifying signal %s....%s") % (s, ("PASS" if (stat) else "FAIL")))
                status_ver = status_ver and stat
        if (not status_ver):
            self.error(("       Verification fail (one or more signals are not exists on current DUT model."), 1)

    # ------------------------------------------------------------------------
    def run(self):
        # FIXME - add actual action execution
        self.inform(("         Running %s::%s:%s:%d \n\n") % (
            htd_base_action.get_action_type(self),
            htd_base_action.get_action_name(self),
            htd_base_action.get_action_call_file(self),
            htd_base_action.get_action_call_lineno(self)))

        sigs_l = {}
        # --------------------------------------------------------------
        if (self.get_action_argument("op") == "WAIT"):
            for sig in self.get_not_declared_arguments():
                if (sig not in list(sigs_l.keys())):
                    sigs_l[sig] = {}
                for s in self.get_action_argument(sig):
                    if (s.lsb not in list(sigs_l[sig].keys())):
                        sigs_l[sig][s.lsb] = {}
                    sigs_l[sig][s.lsb][s.msb] = int(s.value)

            htdPlayer.hplSignalMgr.signalset_wait(sigs_l, int(self.get_action_argument("waitcycles")),
                                                  self.arguments.get_argument("maxtimeout"),
                                                  self.get_action_argument("refclock"), 1,
                                                  self.get_action_argument("sel"),
                                                  peeksignal_disable = self.get_action_argument("peeksignal_disable"))
        # -------------------------
        elif (self.get_action_argument("op") == "SERIALSET"):
            if (not self.argument_exists("width")):
                self.error(("Action's (%s) missing obligatory argument - \"width\" for \"op\"=SERIALSET") % (
                    self.__action_name__), 1)
            for sig in self.get_not_declared_arguments():
                if (sig not in list(sigs_l.keys())):
                    sigs_l[sig] = {}
                for s in self.get_action_argument(sig):
                    if (s.lsb not in list(sigs_l[sig].keys())):
                        sigs_l[sig][s.lsb] = {}
                    sigs_l[sig][s.lsb][s.msb] = int(s.value)
            htdPlayer.hplSignalMgr.signalset_serial_set(sigs_l, int(self.get_action_argument("width")),
                                                        self.get_action_argument("sel"))
        # ---------------------
        elif (self.get_action_argument("op") == "CHECK"):
            for sig in self.get_not_declared_arguments():
                for s in self.get_action_argument(sig):
                    check_value = "z" if (s.zmode == 1) else ("x" if (s.xmode == 1) else int(s.value))
                    if ((not (htdPlayer.hplSignalMgr.signal_check(sig, s.lsb, s.msb, check_value,
                                                                  self.get_action_argument("sel")))) and (
                            self.get_action_argument("check"))):
                        self.error(("Action's (%s) fail signal check: %s%s") % (self.__action_name__, sig,
                                                                                (("[%d:%d]") % (s.lsb, s.msb)) if (
                                                                                    s.lsb >= 0 and s.msb >= 0) else ""), 1)
        # ---------------------
        elif (self.get_action_argument("op") == "CHECKNOT"):
            for sig in self.get_not_declared_arguments():
                for s in self.get_action_argument(sig):
                    check_value = "z" if (s.zmode == 1) else ("x" if (s.xmode == 1) else int(s.value))
                    if ((not (htdPlayer.hplSignalMgr.signal_check_not(sig, s.lsb, s.msb, check_value,
                                                                      self.get_action_argument("sel")))) and (
                            not self.get_action_argument("check"))):
                        self.error(("Action's (%s) fail signal check: %s%s!=%s ") % (self.__action_name__, sig,
                                                                                     (("[%d:%d]") % (s.lsb, s.msb)) if (
                                                                                         s.lsb >= 0 and s.msb >= 0) else ""),
                                   1)
        # ----------------------
        elif (self.get_action_argument("op") == "PULSE"):
            for sig in self.get_not_declared_arguments():
                if (sig not in list(sigs_l.keys())):
                    sigs_l[sig] = {}
                for s in self.get_action_argument(sig):
                    if (s.lsb not in list(sigs_l[sig].keys())):
                        sigs_l[sig][s.lsb] = {}
                    sigs_l[sig][s.lsb][s.msb] = int(s.value)
            htdPlayer.hplSignalMgr.signalset_pulse(sigs_l, int(self.get_action_argument("waitcycles")),
                                                   self.get_action_argument("refclock"),
                                                   self.get_action_argument("sel"))

        # -----------------------------
        elif (self.get_action_argument("op") == "FORCE"):
            for sig in self.get_not_declared_arguments():
                if (sig not in list(sigs_l.keys())):
                    sigs_l[sig] = {}
                for s in self.get_action_argument(sig):
                    if (s.lsb not in list(sigs_l[sig].keys())):
                        sigs_l[sig][s.lsb] = {}
                    sigs_l[sig][s.lsb][s.msb] = "z" if (s.zmode == 1) else ("x" if (s.xmode == 1) else int(s.value))
            htdPlayer.hplSignalMgr.signalset_force(sigs_l, self.get_action_argument("sel"))
        # -------------------------------
        elif (self.get_action_argument("op") == "UNFORCE"):
            for sig in self.get_not_declared_arguments():
                if (sig not in list(sigs_l.keys())):
                    sigs_l[sig] = {}
                for s in self.get_action_argument(sig):
                    if (s.lsb not in list(sigs_l[sig].keys())):
                        sigs_l[sig][s.lsb] = {}
                    sigs_l[sig][s.lsb][s.msb] = "z" if (s.zmode == 1) else ("x" if (s.xmode == 1) else int(s.value))
            htdPlayer.hplSignalMgr.signalset_unforce(sigs_l, self.get_action_argument("sel"))
        # ----------------------------------------------------
        elif (self.get_action_argument("op") == "START_MONITOR"):
            pass
        elif (self.get_action_argument("op") == "STOP_MONITOR"):
            pass
        # ----------------------------------------------------
        elif (self.get_action_argument("op") == "SET"):
            for sig in self.get_not_declared_arguments():
                if (sig not in list(sigs_l.keys())):
                    sigs_l[sig] = {}
                for s in self.get_action_argument(sig):
                    if (s.lsb not in list(sigs_l[sig].keys())):
                        sigs_l[sig][s.lsb] = {}
                    sigs_l[sig][s.lsb][s.msb] = "z" if (s.zmode == 1) else ("x" if (s.xmode == 1) else int(s.value))
            htdPlayer.hplSignalMgr.signalset_set(sigs_l, self.get_action_argument("sel"))
        # ----------------------------------------------------
        elif (self.get_action_argument("op") == "GET"):
            for sig in self.get_not_declared_arguments():
                for s in self.get_action_argument(sig):
                    return htdPlayer.hplSignalMgr.signal_peek(sig, s.lsb, s.msb, self.get_action_argument("sel"))
        else:
            self.error(("Action's (%s) illegal/unsupported SIGNAL opcode - \"op\"=\"%s\" found %s") % (
                self.__action_name__, self.get_action_argument("op")), 1)

    def get_defined_label(self):
        label_name = "%s__%s" % (self.get_action_name(), self.get_action_argument("op"))
        return label_name
