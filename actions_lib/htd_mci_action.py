from htd_basic_action import *
from htd_utilities import *
from htd_collaterals import *
from htd_player_top import *


class MCI(htd_base_action):

    def __init__(self, action_name, source_file, source_lineno, currentFlow, is_internal):

        htd_base_action.__init__(self, self.__class__.__name__, action_name,
                                 source_file, source_lineno, currentFlow, is_internal)
        self.arguments.set_argument("source", 1, "Specify which source for this action")
        self.arguments.declare_arg("mci_mode", "The mode MCI is in (io or ii or serial)", ["io", "ii", "serial"], "", 1)
        self.arguments.declare_arg("mci_in", "The mci input packets", "int_or_list", [], 1)
        self.arguments.declare_arg("mci_out", "The mci out packets. Only required in io mode. "
                                              "Must be the same length as mci_in.", "int_or_list", [], 1)
        self.arguments.declare_arg("transform", "The transform to use in SPF mode", "string", "", 1)

        self.mci_in = None
        self.mci_out = None

    def get_action_not_declared_argument_names(self):
        pass

    def verify_arguments(self):
        # TODO: Remove this later once sync_to_modulo_clock is fixed for SPF output on CNL
        self.arguments.set_argument("postalignment", 0)

        # Check mci_in packets
        self.check_packets_int("mci_in")
        self.mci_in = self.arguments.get_argument("mci_in")

        # Make sure mci_in and mci_out are the same length in io mode
        if self.arguments.get_argument("mci_mode") in ["io", "serial"]:
            if len(self.arguments.get_argument("mci_in")) != len(self.arguments.get_argument("mci_out")):
                self.error("mci_in and mci_out must be the same length in io mode", 1)

            # Check mci_out packets
            self.check_packets_int("mci_out")
            self.mci_out = self.arguments.get_argument("mci_out")

        elif self.arguments.get_argument("mci_mode") == "ii":
            self.mci_out = []

    def check_packets_int(self, arg):
        for p in self.arguments.get_argument(arg):
            if not isinstance(p, int):
                self.error("Packets in %s list must be of type int not %s" % (arg, type(p)), 1)

    def run(self):
        htdPlayer.hpl_to_dut_interface.MciPackets(self.mci_in,
                                                  self.mci_out,
                                                  self.arguments.get_argument("transform"))
