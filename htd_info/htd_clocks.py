from htd_utilities import *
import math
# --------------------------


class htd_clocks(object):
    def __init__(self, cfg, logger):
        self.dutClocks = {}
        self.dutClocksRtlPath = {}
        self.logger = logger
        self._default = "none"
        self.cfg = cfg
        if ("HTD_Clocks" not in list(self.cfg.keys())):
            self.logger.error("Missing clock config (\"HTD_Clocks\") definition in te cfg")
        if ("default" not in list(self.cfg["HTD_Clocks"].keys())):
            self.logger.error("Missing default clock config definition in CFG[\"HTD_Clocks\"]")
        for clk in self.cfg["HTD_Clocks"]:
            if (clk != "default"):
                self.logger.inform(("Adding htd clock - %s...") % (clk))

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
                                self.logger.inform("Dependency in %s caused clk %s to change from %d to %d" % (self.cfg["HTD_Clocks_dependency"][clk], clk, self.cfg["HTD_Clocks"][clk], new_clock_ratio))
                                self.cfg["HTD_Clocks"][clk] = new_clock_ratio

                self.add_new_clock(clk)
                self.set_clock_rate(clk, self.cfg["HTD_Clocks"][clk])

        self.set_default(cfg["HTD_Clocks"]["default"])
        self.logger.inform(("Setting default htd clock - %s...") % (self.cfg["HTD_Clocks"]["default"]))
        # --Add New clock

    def add_new_clock(self, clk):
        self.dutClocks[clk] = -1
        if (clk not in list(self.cfg["FlowSignals"].keys())):
            self.logger.error(("Missing clock path definition in CFG[\"FlowSignals\"] %s") % (
                ("or signal file:%s") % (os.environ.get('HTD_SIGNALS_MAP')) if (
                    os.environ.get('HTD_SIGNALS_MAP') is not None) else ""))
        self.dutClocksRtlPath[clk] = self.cfg["FlowSignals"][clk]
        # -----------------

    def get_clock_rtl_path(self, clk):
        return self.cfg["FlowSignals"][clk]

    def get_all_clocks(self):
        return list(self.dutClocks.keys())

    def is_clock(self, name):
        if (name in list(self.dutClocks.keys())):
            return 1
        else:
            return 0

    # ----------
    def set_clock_rate(self, name, rate):
        if (name not in self.dutClocks):
            self.logger.error(("Trying to update a clock-%s rate , before the clock has been registered") % (name))
        self.dutClocks[name] = rate

    # ---------------
    def check_for_unassigned_clock_ratio(self):
        for clk in self.dutClocks:
            if (self.dutClocks[clk] < 0):
                self.logger.error(
                    ("Found not initilized  clock - %s, ratio was not defined.Pls. add \"-%s <ratio>\" to CMD. ") % (
                        clk, clk))
                # -----------------------------

    def set_default(self, clk):
        if (not self.is_clock(clk)):
            self.logger.error(("Trying to set a not existent clock - \"%s\".Pls. add it first. ") % (clk))
        self._default = clk

    # ----------------------------
    def get_default(self):
        if (self._default == "none"):
            self.logger.error("The default clock is not defined yet.Pls. add it first. ")
        return self._default

    # -----------------------
    def clock_transpose(self, from_clock, from_clock_cycles, to_clock):
        if (from_clock not in list(self.dutClocks.keys())):
            clock_by_rtl_path = ""
            for c in list(self.dutClocksRtlPath.keys()):
                if (self.dutClocksRtlPath[c] == from_clock):
                    clock_by_rtl_path = c
            if (len(clock_by_rtl_path) < 2):
                self.logger.error((
                                  "The original clock for conversion -\"%s\" is not defined in clocking list. Available clocks are : %s ") % (
                                  from_clock, list(self.dutClocks.keys())))
            else:
                from_clock = clock_by_rtl_path
        if (to_clock not in list(self.dutClocks.keys())):
            self.logger.error(
                ("The destination clock for conversion is not defined in clocking list. Available clocks are : %s ") % (
                    to_clock, list(self.dutClocks.keys())))
        if (from_clock == to_clock or from_clock == "none"):
            return from_clock_cycles
        else:
            num_of_dest_clks = from_clock_cycles // self.dutClocks[from_clock] * self.dutClocks[to_clock]
            return (math.ceil(num_of_dest_clks + 0.5) if (num_of_dest_clks > 1) else 1)

    # --------------------
    def is_transposed_clock_modulo(self, from_clock, from_clock_cycles, to_clock):
        if (from_clock not in list(self.dutClocks.keys())):
            self.logger.error(
                ("The original clock for conversion is not defined in clocking list. Available clocks are : %s ") % (
                    from_clock, list(self.dutClocks.keys())))
        if (to_clock not in list(self.dutClocks.keys())):
            self.logger.error(
                ("The destination clock for conversion is not defined in clocking list. Available clocks are : %s ") % (
                    to_clock, list(self.dutClocks.keys())))
        if (from_clock == to_clock or from_clock == "none"):
            return 1
        else:
            num_of_dest_clks = from_clock_cycles // self.dutClocks[from_clock] * self.dutClocks[to_clock]
            if (int(num_of_dest_clks) == num_of_dest_clks):
                return 1
            else:
                return 0

# -------------------------------------
