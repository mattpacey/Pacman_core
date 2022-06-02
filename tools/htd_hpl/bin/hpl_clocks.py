from htd_utilities import *
from htd_collaterals import *
import math
# --------------------------
'''
   Class providing an initilization and mode selection handling
   '''


class hpl_clocks(object):
    def __init__(self, cfg, uiptr):
        self.dutClocks = {}
        self.dutClocksRtlPath = {}
        self._default = "none"
        self.cfg = cfg
        if("HTD_Clocks" not in list(self.cfg.keys())):
            htdte_logger.error("Missing clock config (\"HTD_Clocks\") definition in te cfg")
        if("default" not in list(self.cfg["HTD_Clocks"].keys())):
            htdte_logger.error("Missing default clock config definition in \"HTD_Clocks\" - te cfg")
        for clk in self.cfg["HTD_Clocks"]:
            if(clk != "default"):
                htdte_logger.inform(("Adding htd clock - %s...") % (clk))

                if ("HTD_Clocks_dependency" in list(self.cfg.keys()) and clk in list(self.cfg["HTD_Clocks_dependency"].keys())):
                    # clock is calculated based on the dependency ratio if exists
                    # support for now is CFG key and CFG value (e.g FuseOverride:FUSE_RING_RATIO)
                    depends_l = self.cfg["HTD_Clocks_dependency"][clk].split(':')
                    if (depends_l[0] in list(self.cfg.keys()) and depends_l[1] in list(self.cfg[depends_l[0]].keys())):
                        (ret_str, depends_ratio) = util_get_int_value(self.cfg[depends_l[0]][depends_l[1]])
                        if (depends_ratio != 0):
                            default_clk = cfg["HTD_Clocks"]["default"]
                            new_clock_ratio = int(self.cfg["HTD_Clocks"][default_clk]) // depends_ratio
                            if (new_clock_ratio != 0):
                                htdte_logger.inform("Dependency in %s caused clk %s to change from %d to %d" % (self.cfg["HTD_Clocks_dependency"][clk], clk, self.cfg["HTD_Clocks"][clk], new_clock_ratio))
                                self.cfg["HTD_Clocks"][clk] = new_clock_ratio

                self.add_new_clock(clk)
                self.set_clock_rate(clk, self.cfg["HTD_Clocks"][clk])
                self.uiptr = uiptr
        self.set_default(cfg["HTD_Clocks"]["default"])
        # -----------------------
        if(os.environ.get('HTD_TE_HELP_MODE') == "1"):
            return
        # --------Training clock configuration
        self.train_clock_resolution = uiptr.hpl_to_dut_interface.train_tick_time()  # The minimal time in ps between each clock training
        self._last_train_clock_time_position = {}
        # -------------------------------
        htdte_logger.inform(("Setting default htd clock - %s...") % (self.cfg["HTD_Clocks"]["default"]))

    # --Add New clock
    def get_current_ui(self): return self.uiptr
# -----------------------------------------------------------------------------------

    def add_new_clock(self, clk):
        self.dutClocks[clk] = -1
        if(clk not in list(self.cfg["FlowSignals"].keys())):
            htdte_logger.error(("Missing clock path definition in CFG[\"FlowSignals\"] %s") % (("or signal file:%s") % (os.environ.get('HTD_SIGNALS_MAP')) if (os.environ.get('HTD_SIGNALS_MAP') is not None) else ""))
        self.dutClocksRtlPath[clk] = self.cfg["FlowSignals"][clk]
# -----------------------------------------------------------------------------------

    def get_clock_rtl_path(self, clk):
        return CFG["FlowSignals"][clk]
# -----------------------------------------------------------------------------------

    def get_all_clocks(self):
        return list(self.dutClocks.keys())
# -----------------------------------------------------------------------------------

    def is_clock(self, name):
        if(name in list(self.dutClocks.keys())):
            return 1
        else:
            return 0
# -----------------------------------------------------------------------------------

    def set_clock_rate(self, name, rate):
        if(name not in self.dutClocks):
            htdte_logger.error(("Trying to update a clock-%s rate , before the clock has been registered") % (name))
        self.dutClocks[name] = rate
# -----------------------------------------------------------------------------------

    def train_clock(self, clock_name):
        htdte_logger.error(("This is pure virtual method and should be overriden by class specification"))
# -----------------------------------------------------------------------------------

    def get_clock_period(self, name):
        if(name not in self.dutClocks):
            htdte_logger.error(("Trying to update a clock-%s period , before the clock has been registered") % (name))
            self.train_clock(clock_name)
            # return self.dutClocks[name]#nuber of cycles
        return int(self.dutClocks[name] * self.train_tick_time())  # =time #- clock time
# -----------------------------------------------------------------------------------

    def check_for_unassigned_clock_ratio(self):
        for clk in self.dutClocks:
            if(self.dutClocks[clk] < 0):
                htdte_logger.error(("Found not initialized  clock - %s, ratio was not defined.Pls. add \"-%s <ratio>\" to CMD. ") % (clk, clk))
# -----------------------------------------------------------------------------------

    def set_default(self, clk):
        if(not self.is_clock(clk)):
            htdte_logger.error(("Trying to set a not existent clock - \"%s\".Pls. add it first. ") % (clk))
        self._default = clk
# -----------------------------------------------------------------------------------

    def get_default(self):
        if(self._default == "none"):
            htdte_logger.error("The default clock is not defined yet.Pls. add it first. ")
        return self._default
# -----------------------------------------------------------------------------------

    def clock_transpose(self, from_clock, from_clock_cycles, to_clock):
        if(from_clock not in list(self.dutClocks.keys())):
            clock_by_rtl_path = ""
            for c in list(self.dutClocksRtlPath.keys()):
                if(self.dutClocksRtlPath[c] == from_clock):
                    clock_by_rtl_path = c
                # --Check if string is empty - i.e not found rtl path for currently asked clock
            if(len(clock_by_rtl_path) < 2):
                htdte_logger.error(("The original clock for conversion -\"%s\" is not defined in clocking list. Available clocks are : %s ") % (from_clock, list(self.dutClocks.keys())))
        else:
            clock_by_rtl_path = from_clock
        self.train_clock(from_clock)
        # ---Verify destination clock integrity
        if(to_clock not in list(self.dutClocks.keys())):
            htdte_logger.error(("The destination clock for conversion is not defined in clocking list. Available clocks are : %s ") % (to_clock, list(self.dutClocks.keys())))
        # if destination clock is same as an original , or source clock is not defined , return original cycles number---
        if(from_clock == to_clock or from_clock == "none"):
            return from_clock_cycles * self.dutClocks[to_clock]
        else:
            num_of_dest_clks = from_clock_cycles * self.dutClocks[to_clock] // self.dutClocks[from_clock]
            # --retrain destination clock---
        self.train_clock(to_clock)
        num_of_dest_clks = from_clock_cycles * self.dutClocks[to_clock] // self.dutClocks[from_clock]
        return (math.ceil(num_of_dest_clks) if(num_of_dest_clks > 1) else 1)


# -----------------------------------------------------------------------------------
# Inherited Sub-Classes to segregate the methods used by interactive and non interactive modes separately
# Non Interactive Class
# -----------------------------------------------------------------------------------
class hpl_non_interactive_clocks(hpl_clocks):

    def __init__(self, cfg, uiptr):
        if(uiptr.interactive_mode):
            htdte_logger.error(("Illegal interactive mode received at initialization of clock object : %s, this simulation mode limited for offline content mode only ") % (self.__class__.__name__))
        self.is_interactive = 0
        hpl_clocks.__init__(self, cfg, uiptr)
# -----------------------------------------------------------------------------------

    def wait_clock_modulo(self, clock_name, modulo_value): pass
# -----------------------------------------------------------------------------------

    def train_clocks(self): pass
    # This will train all clocks in Te_cfg or if use set up new clk(???)
# -----------------------------------------------------------------------------------

    def train_clock(self, clock_name): pass
    # Train from_clock and to_clock
# -----------------------------------------------------------------------------------

    def train_tick_time(self):
        if (CFG["HTD_Clocks_Settings"]["sim_time_unit"] == "fs"):
            multiplier = 1000
        if (CFG["HTD_Clocks_Settings"]["sim_time_unit"] == "ps"):
            multiplier = 1
        if (CFG["HTD_Clocks_Settings"]["sim_time_unit"] == "ns"):
            multiplier = 0.001
        if (CFG["HTD_Clocks_Settings"]["sim_time_unit"] == "us"):
            multiplier = 0.000001
        if (CFG["HTD_Clocks_Settings"]["sim_time_unit"] == "ms"):
            multiplier = 0.000000001
        # tick_time=(CFG["HTD_Clocks_Settings"]["sim_time_scale"])*(CFG["HTD_Clocks_Settings"]["sim_time_unit"])
        tick_time = (CFG["HTD_Clocks_Settings"]["sim_time_scale"]) * multiplier
        return tick_time
        # Train tick_time is 1ps currently
# -----------------------------------------------------------------------------------

    def get_clock_period(self, name):
        if(name not in self.dutClocks):
            htdte_logger.error(("Trying to update a clock-%s period , before the clock has been registered") % (name))
        self.train_clock(name)
        # return self.dutClocks[name]#nuber of cycles
        return int(self.dutClocks[name] * self.train_tick_time())  # =time #- clock time

# -----------------------------------------------------------------------------------


# -----------------------------------------------------------------------------------
# Intercative Class
# -----------------------------------------------------------------------------------
class hpl_interactive_clocks(hpl_clocks):

    def __init__(self, cfg, uiptr):
        hpl_clocks.__init__(self, cfg, uiptr)
    # -----------------------------------------------------------------------------------

    def train_clocks(self):
        return  # TODO -Meanwhile disabling
        current_time = self.get_current_ui().hpl_to_dut_interface.get_model_time()
        max_train_range = 0
        clk_training_tracker = {}
        for clk in list(self.dutClocks.keys()):
            if(self.dutClocks[clk] > max_train_range):
                max_train_range = self.dutClocks[clk]
            clk_training_tracker[clk] = {}
            clk_training_tracker[clk]["prev_state"] = -1
        # ---------------------------------------
        for i in range(1, max_train_range * 2):
            for clk in list(self.dutClocks.keys()):
                if("period" in list(clk_training_tracker[clk].keys())):
                    continue
                if((clk not in list(self._last_train_clock_time_position.keys())) or (self._last_train_clock_time_position[clk] - current_time) > 2 * max_train_range):
                    sig_path = HTD_INFO.signal_info.extract_full_signal_path(self.get_clock_rtl_path(clock_name), -1, -1, "")
                    curr_val = self.get_current_ui().hplSignalMgr.signal_peek(sig_path, -1, -1)
                    htdte_logger.inform(("Clk(%s)=%d") % (str(curr_val)))
                    if(clk_training_tracker[clk]["prev_state"] >= 0 and curr_val < clk_training_tracker[clk]["prev_state"]):
                        # falling edge
                        clk_training_tracker[clk]["start_pos"] = self.get_current_ui().hpl_to_dut_interface.get_model_time()
                    if(clk_training_tracker[clk]["prev_state"] >= 0 and curr_val > clk_training_tracker[clk]["prev_state"]):
                        # rising edge
                        clk_training_tracker[clk]["end_pos"] = self.get_current_ui().hpl_to_dut_interface.get_model_time()
                        clk_training_tracker[clk]["period"] = clk_training_tracker[clk]["end_pos"] - clk_training_tracker[clk]["start_pos"]
                        self.set_clock_rate(clock_name, clk_training_tracker[clk]["period"])
                    clk_training_tracker[clk]["prev_state"] = curr_val
            self.get_current_ui().hpl_to_dut_interface.wait_tick()
    # -----------------------------------------------------------------------------------

    def train_clock(self, clock_name):
        return  # TODO -Meanwhile disabling
        current_time = self.get_current_ui().hpl_to_dut_interface.get_model_time()
        if((clock_name not in list(self._last_train_clock_time_position.keys())) or (self._last_train_clock_time_position[clock_name] - current_time) > self.train_clock_resolution):
                # --Make a real training only if never done or previous clock training time exceed the minimal train clock resolution
                # wait for clock falling edge
                # savetime1
                # wait for clock rising edge
                # wait for clock faling edge
                # period = current time - savetime1
            sig_path = HTD_INFO.signal_info.extract_full_signal_path(self.get_clock_rtl_path(clock_name), -1, -1, "")
            if(self.get_clock_rtl_path(clock_name).find('.') < 0 and self.get_clock_rtl_path(clock_name).find("/") < 0):
                self.get_current_ui().hpl_to_dut_interface.signal_wait(sig_path, 0, 2 * self.dutClocks[clock_name])
                self.get_current_ui().hpl_to_dut_interface.signal_wait(sig_path, 1, 2 * self.dutClocks[clock_name])
                self.get_current_ui().hpl_to_dut_interface.signal_wait(sig_path, 0, 2 * self.dutClocks[clock_name])
                savetime1 = self.get_current_ui().hpl_to_dut_interface.get_model_time()
                self.get_current_ui().hpl_to_dut_interface.signal_wait(sig_path, 1, 2 * self.dutClocks[clock_name])
                self.get_current_ui().hpl_to_dut_interface.signal_wait(sig_path, 0, 2 * self.dutClocks[clock_name])
                period = self.get_current_ui().hpl_to_dut_interface.get_model_time() - savetime1
            else:
                self.get_current_ui().hpl_to_dut_interface.signal_wait(sig_path, 0, 2 * self.dutClocks[clock_name])
                self.get_current_ui().hpl_to_dut_interface.signal_wait(sig_path, 1, 2 * self.dutClocks[clock_name])
                self.get_current_ui().hpl_to_dut_interface.signal_wait(sig_path, 0, 2 * self.dutClocks[clock_name])
                savetime1 = self.get_current_ui().hpl_to_dut_interface.get_model_time()
                self.get_current_ui().hpl_to_dut_interface.signal_wait(sig_path, 1, 2 * self.dutClocks[clock_name])
                self.get_current_ui().hpl_to_dut_interface.signal_wait(sig_path, 0, 2 * self.dutClocks[clock_name])
                period = self.get_current_ui().hpl_to_dut_interface.get_model_time() - savetime1
            self.set_clock_rate(clock_name, period)
    # -----------------------------------------------------------------------------------

    def wait_clock_modulo(self, clock_name, modulo_value):
            # The method is to check if we to wait for clock modulo
        if(clock_name not in list(self.dutClocks.keys())):
            htdte_logger.error(("The original clock for conversion is not defined in clocking list. Available clocks are : %s ") % (clock_name, list(self.dutClocks.keys())))
            self.get_current_ui().hpl_to_dut_interface.signal_wait(self.get_clock_rtl_path(clock_name), 0, 2 * self.dutClocks[clock_name])
            self.get_current_ui().hpl_to_dut_interface.signal_wait(self.get_clock_rtl_path(clock_name), 1, 2 * self.dutClocks[clock_name])
            self.get_current_ui().hpl_to_dut_interface.signal_wait(self.get_clock_rtl_path(clock_name), 0, 2 * self.dutClocks[clock_name])  # wait for falling edge of clock
            return
    # -----------------------------------------------------------------------------------

    def train_tick_time(self):
        t1 = self.get_current_ui().hpl_to_dut_interface.get_model_time()
        # identify if SYS_CLK is its the fastest clock to get real tick in model from Shareek/Kasem - one tick step @SYS_CLK???? (wait 1tick)
        self.get_current_ui().hpl_to_dut_interface.wait_tick()
        t2 = self.get_current_ui().hpl_to_dut_interface.get_model_time()
        return t2 - t1  # convert to string with scale ps /ns
        # 1.t1=get_time()
        # 2.one tick
        # 3.t2=get_time()
        # Return t2-t1
        # ------------
# -----------------------------------------------------------------------------------
# -----------------------------------------------------------------------------------
