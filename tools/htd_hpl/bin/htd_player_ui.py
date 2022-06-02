from htd_utilities import *
from htd_collaterals import *
from hpl_clocks import *
from htd_hpl_itpp_interface import *
from htd_hpl_signal_manager import *
from htd_hpl_sbftload_manager import *
from hpl_tap_spf_api import *
from hpl_tap_stpl_api import *
from hpl_tap_dfx_api import *
from htd_hpl_interactive_socket_interface import *
from htd_hpl_spf_interface import *
from htd_hpl_xdp_interface import *
from htd_history_manager import *
# -------------------------------------------------------------------------------------------------------
# This class is used as a data container for passing arguments from TE Tap action toward HPL Tap manager
# -------------------------------------------------------------------------------------------------------


class htd_tap_params(object):
    def __init__(self):
        self.ircode = -1
        self.irname = ""
        self.agent = ""
        self.read_modify_write = 0
        self.bfm_mode = "normal"
        self.check = 1
        self.refclock = ""
        self.read_type = 0
        self.waitcycles = -1
        self.eptarget = ""
        self.dr = htd_argument_containter()  # data container storing fields and dri/dro assignment
        # arguments.get_argument("VIK"): ->  [ "VIK[0:2]=2","VIK[5:7]=7"..... ]


# --------------------------------------------------------------------
# This class is used as an isolation interface between HPL and TE
# --------------------------------------------------------------------
class htd_player_ui(object):

    def __init__(self):
        htdte_logger.callBack_for_extensions = self.add_comment
        self.current_action = None
        self.silent_mode = False
        self.interactive_mode = False
        self.labels_history_table_name = "HPL_Labels"
        self.current_ratio = 1
        self.default_ratio = 1
        self.ratio_clk = ""
        self.scan_memory_in_progress = 0
        # --------Clock managment
        # Take it from TE_cfg.....self.hpl_to_dut_interface
        clock_class_name = ("hpl_%s_clocks") % ("interactive" if (self.interactive_mode) else "non_interactive")
        # --------------------------------
        if(os.environ.get('HTD_TE_HELP_MODE') == "1"):
            self.hplClockMgr = eval(clock_class_name)(CFG, self)
            return  # No low level object initilization in HELP arguments mode
        # -----------------------------
        if("HPL" not in list(CFG.keys())):
            htdte_logger.error("Missing HPL configuration category in global CFG structure . ")
        if("execution_mode" not in list(CFG["HPL"].keys())):
            htdte_logger.error("Missing \"execution_mode\" configuration entry in  CFG[HPL] structure . ")
        # -------Interfaces--------
        self.hpl_to_dut_interface = None
        if(CFG["HPL"]["execution_mode"] == "itpp"):
            self.hpl_to_dut_interface = hpl_itpp_interface(self.get_interface_file_name(), self)
            self.interactive_mode = False
        elif(CFG["HPL"]["execution_mode"] == "interactive_socket"):
            self.hpl_to_dut_interface = hpl_interactive_socket_interface(self)
            self.interactive_mode = True
            htdte_logger.setErrHndlrInterface(self.hpl_to_dut_interface)
        elif(CFG["HPL"]["execution_mode"] == "spf"):
            self.hpl_to_dut_interface = hpl_spf_interface(self.get_interface_file_name(), self)
        elif(CFG["HPL"]["execution_mode"] == "xdp"):
            self.hpl_to_dut_interface = hpl_xdp_interface(self.get_interface_file_name(), self)
        else:
            htdte_logger.error(("Not supported execution mode value -\"%s\" found in  CFG[HPL][execution_mode]. Expected modes are: itpp") % (CFG["HPL"]["execution_mode"]))
        # ---------Plsyer BFM manager----
        self.hplSignalMgr = eval(("hpl_SignalManager_%s") % (("interactive" if (self.interactive_mode) else "non_interactive")))(self.hpl_to_dut_interface, self)
        # ----------------------------------------
        self.hplSbftLoadMgr = eval("hpl_SbftLoadManager")(self.hpl_to_dut_interface, self)
        # ----------------------------------------
        if("tap_api_selector" not in list(CFG["HPL"].keys())):
            htdte_logger.error("Missing TAP API selector (expected in  CFG[HPL][tap_api_selector]. ")
        self.hpl_tap_api = eval(cfg_HPL("tap_api_selector"))()
        # -----------------------
        clock_class_name = ("hpl_%s_clocks") % ("interactive" if (self.interactive_mode) else "non_interactive")
        self.hplClockMgr = eval(clock_class_name)(CFG, self)
        # --Simoptimization
        if("signal_wait_mode" not in list(CFG["HPL"].keys())):
            htdte_logger.error((" Missing obligatory CFG[\"HPL\"][\"signal_wait_mode\"] definition in TE_cfg.xml (Valid values are:sim_time or silicon).... "))
        if(CFG["HPL"]["signal_wait_mode"] not in ["sim_time", "silicon"]):
            htdte_logger.error((" Invalid CFG[\"HPL\"][\"signal_wait_mode\"]=\"%s\" definition in TE_cfg.xml (Valid values are:sim_time or silicon).... ") % (CFG["HPL"]["signal_wait_mode"]))
        self.signal_wait_mode = CFG["HPL"]["signal_wait_mode"]
        # --------------------
        # Sync Enable
        if "sync_enabled" in CFG["HPL"]:
            self.sync_enabled = CFG["HPL"]["sync_enabled"]
            htdte_logger.inform("HPL Sync: %d" % (self.sync_enabled))
        else:
            self.sync_enabled = 1
            htdte_logger.inform("HPL Sync Enabled by default")
        htdte_logger.set_message_signal = self.set_message_signal
    # --------------------------------------------------

    def get_interface_file_name(self):
        mode = CFG["HPL"]["execution_mode"]
        if(mode == "itpp"):
            return "htd_test_stimulus.itpp" if("ItppOutputFileName" not in list(CFG["HPL"].keys())) else cfg_HPL("ItppOutputFileName")
        elif(mode == "spf"):
            return "htd_test_stimulus.spf" if("SpfOutputFileName" not in list(CFG["HPL"].keys())) else cfg_HPL("SpfOutputFileName")
        elif(mode == "xdp"):
            return "htd_test_stimulus.py" if("XdpOutputFileName" not in list(CFG["HPL"].keys())) else cfg_HPL("XdpOutputFileName")
        else:
            htdte_logger.error(("Not supported execution mode value -\"%s\" found in  CFG[HPL][execution_mode]. Expected modes are: itpp") % (CFG["HPL"]["execution_mode"]))

    def get_indexed_label(self, label, agent_filter=""):
        if(not htd_history_mgr.parametric_has(self.labels_history_table_name, [label + agent_filter])):
            htd_history_mgr.parametric_capture(self.labels_history_table_name, [label + agent_filter], 0, "HPL_ui")
            return label
        else:
            indx = htd_history_mgr.parametric_get(self.labels_history_table_name, [label + agent_filter]) + 1
            htd_history_mgr.parametric_capture(self.labels_history_table_name, [label + agent_filter], indx, "HPL_ui")
            #htdte_logger.inform("current %s index is %d filter %s" %(label, indx, agent_filter))
            return ("%s_%d") % (label, indx)

    def set_current_action(self, actionObj):
        self.current_action = actionObj

    def get_current_action(self): return self.current_action

    def close(self):
        self.hpl_to_dut_interface.close()

    def set_silent_mode(self):
        self.hpl_to_dut_interface.set_silent_mode()
        self.silent_mode = True

    def unset_silent_mode(self):
        self.hpl_to_dut_interface.unset_silent_mode()
        self.silent_mode = False
    # -------------------------------
    # Create HTML formatted help file
    # -------------------------------

    def create_hpl_help(self, file_name):
        html_file = open(file_name, 'w')
        # -----The short help is printed to screen , detailed help in html------------
        # --Create a bookmarks links for html
        html_file.write("<!DOCTYPE html>\n<html>\n")
        html_file.write('<a name="top"></a>\n<body>')
        html_file.write('<p><h1> HTD Player (Output Interface) Help: </h1></p>\n')
        # --------------
        util_get_methods_prototypes_of_class(self.__class__.__name__).print_html(html_file, HelpListStreamEnum_all)
        html_file.close()
    # -------------------------------------------------------------------------------------------------------------------------
    # --To be used for comments printout to transactor : ITPP file or SIM/EMU  or pattern comment to make a flow clarification
    # -------------------------------------------------------------------------------------------------------------------------

    def add_comment(self, line):
        self.hpl_to_dut_interface.add_comment(line)
    # -------------------------------------------------------------
    # Passing pattern information through Simulation,EMU or DP
    # -------------------------------------------------------------

    def set_pattern_info(self, message):
        self.hpl_to_dut_interface.set_pattern_info(message)
    # ---------------------------------------------------------
    # ---TAP CallBacks
    # --------------------------------------------------------
    # def tap_send_cmd(self,tap_obj): # todo vik close interface with (this is the entry point fomr htd_te end)
    #   return self.hpl_tap.send_cmd(tap_obj)

    def get_ir_opcode_int(self, cmd, agent):
        return HTD_INFO.tap_info.get_ir_opcode_int(cmd, agent)

    def get_ir_name(self, ircode, agent):
        # return self.hpl_tap.api.get_ir_name(ircode,agent)
        return HTD_INFO.tap_info.get_ir_name(ircode, agent)

    def get_tapreg_fields(self, cmd, agent, eptarget):
        # return self.hpl_tap.api.get_ir_fields(cmd,agent)
        return HTD_INFO.tap_info.get_ir_fields(cmd, agent, eptarget)

    def tap_send_cmd(self, tap_params):  # /nfs/iil/proj/mpgbd/vbhutani/CNL/HTD_TE/repo_latest/tools//htd_hpl/bin/htd_player_ui.pytodo vik close interface with (this is the entry point fomr htd_te end)
        return self.hpl_tap.send_cmd(tap_params)

    def verify_tap_eptarget(self, agent, eptarget):
        return self.hpl_tap.verify_tap_eptarget(agent, eptarget)

    def rtl_node_exists(self, cmd, agent, field):
        # return self.hpl_tap.api.rtl_node_exists(cmd,agent,field)
        return HTD_INFO.tap_info.rtl_node_exists(cmd, agent, field)
    # ---------------------------------------------------------
    # ---Signal CallBacks
    # ---------------------------------------------------------

    def is_intractive_simulation(self):
        return self.hplSignalMgr.is_interactive_mode()

    def get_full_signal_path(self, signal, lsb=-1, msb=-1, selector=""):
        return HTD_INFO.signal_info.extract_full_signal_path(signal, lsb, msb, selector)

    def signal_module_exists(self, search_signal_or_module):
        return HTD_INFO.signal_info.signal_module_exists(search_signal_or_module)

    # ------------------------------------------------------------------------------------------------------------------------------------
    def wait_clock_num(self, cycles, clock="none"):
        if (cycles == 0):
            return
        self.hpl_to_dut_interface.wait_clock_num(cycles, clock)
    # ---SYNC API
    # ------------------------------------------------------------------------------------------------------------------------------------

    def wait_clock_edge(self, clock, edge):
        supported_edges = ["ar", "br", "af", "bf"]
        if(edge not in supported_edges):
            htdte_logger.error(("Not supported edge value received: \"%s\" - supported:% ") % (edge, supported_edges))
        delay = self.hplClockMgr.get_clock_edge_delay(clock_name, edge)  # return a delay for a requested edge
        if(delay):
            self.hpl_to_dut_interface.wait_clock_num(delay, clock)
    # ------------------------------------------------------------------------------------------------------------------------------------

    def sync_to_clock_modulo(self, clock, modulo):
        # TODO Vik to fix in HPL_Clock colck Modulo API.
        # Make a delay until the target clock modulo constrain
        # moduloPatVecClock=self.hplClockMgr.clock_transpose(clock,modulo,CFG["HPL"]["PatVecClock"])
        # self.hplClockMgr.wait_clock_modulo(clock,modulo) #Get the number of Pattern vector clock ("bclks") until the target clock will be modulo , Example core clock 1:22, requirement modulo 8 -> 3 bclk
        self.hpl_to_dut_interface.wait_clock_modulo(clock, modulo)

    #-------------- ratio commands----------------#
    def set_ratio(self, ratio, clock):
        if (self.ratio_clk != "" and self.ratio_clk != clock):
            htdte_logger.inform("ratio was set on clock %s, can't modify it to other clock %s" % (self.ratio_clk, clock))
        if (ratio != self.current_ratio):
            self.tap_expandata(clock, ratio)
            self.current_ratio = ratio
            self.ratio_clk = clock

    def restore_ratio(self):
        if (self.ratio_clk == ""):
            htdte_logger.error("ratio clock was not set, can't restore properly")

        if (self.current_ratio != self.default_ratio):
            self.tap_expandata(self.ratio_clk, self.default_ratio)
            self.current_ratio = self.default_ratio

    # ------------------------------------------------------------------------------------------------------------------------------------
    def write_itpp_cmd(self, cmd):
        self.hpl_to_dut_interface.write_itpp_cmd(cmd)

    def start_scan_memory(self):
        if("scan_group" not in list(CFG["HPL"].keys()) or CFG["HPL"]["scan_group"] != ""):
            htdte_logger.inform("Trying to use start_scan command while the scan group is not defined in CFG[\"HPL\"][\"scan_group\"]")
        if(self.scan_memory_in_progress):
            htdte_logger.inform("Trying to use start_scan command during active scan mode - (already has been called without stop_scan)")
        self.write_itpp_cmd(("start_scan: %s;\n") % (CFG["HPL"]["scan_group"]))
        self.scan_memory_in_progress = 1

    def stop_scan_memory(self):
        if("scan_group" not in list(CFG["HPL"].keys()) or CFG["HPL"]["scan_group"] != ""):
            htdte_logger.inform("Trying to use stop_scan command while the scan group is not defined in CFG[\"HPL\"][\"scan_group\"]")
        if(self.scan_memory_in_progress == 0):
            htdte_logger.inform("Trying to call stop_scan cmd , while not started previously.")
        self.write_itpp_cmd(("stop_scan: %s;\n") % (CFG["HPL"]["scan_group"]))
        self.scan_memory_in_progress = 0
    # ------------------------------------------------------------------------------------------------------------------------------------

    def set_message_signal(self, message_val):
        if("hvm_flow_tracking_signal" in list(CFG["HPL"].keys()) and CFG["HPL"]["hvm_flow_tracking_signal"] != ""):
            for i in range(0, 16):
                val = util_get_int_sub_range(i * 32, (i + 1) * 32 - 1, message_val)
                self.hplSignalMgr.signal_set(CFG["HPL"]["hvm_flow_tracking_signal"], i * 32, (i + 1) * 32 - 1, val)
    # --------------------

    def tap_compression_on(self): self.hpl_to_dut_interface.tap_compression_on()

    def tap_compression_off(self): self.hpl_to_dut_interface.tap_compression_off()

    def tap_expandata(self, clock, value):
        self.write_itpp_cmd("expandata: %s,%d;" % (clock, value))
        self.write_itpp_cmd("delay: %s(%d);" % (self.hplClockMgr.get_clock_rtl_path(CFG["HPL"]["PatVecClock"]), 10))
