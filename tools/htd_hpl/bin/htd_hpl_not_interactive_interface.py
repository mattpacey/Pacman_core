from htd_utilities import *
from htd_collaterals import *
import re
# ---------------------------------------------------
# Parent Class for Non-Iteractive(Itpp+SPF interface)
# ---------------------------------------------------


class hpl_not_interactive_interface(object):
    def __init__(self, uiptr):
        if("HTD_Clocks" not in list(CFG.keys())):
            htdte_logger.error(("Missing clock definition category in TE_cfg.xml - CFG[\"HTD_Clocks\"]"))
        if("sim_time_scale" not in list(CFG["HTD_Clocks_Settings"].keys())):
            htdte_logger.error(("Missing \"sim_time_scale\" - simulation time scale definition in \"HTD_Clocks\" category at TE_cfg.xml - CFG[\"HTD_Clocks\"][\"sim_time_scale\"]"))
        if("sim_time_unit" not in list(CFG["HTD_Clocks_Settings"].keys())):
            htdte_logger.error(("Missing \"sim_time_unit\" - simulation time scale units definition in \"HTD_Clocks\" category at TE_cfg.xml - CFG[\"HTD_Clocks\"][\"sim_time_unit\"]"))
        if(CFG["HTD_Clocks_Settings"]["sim_time_unit"] not in list(CFG["HTD_Clocks_Settings"].keys())):
            htdte_logger.error(("Missing \"sim_time_unit\" value - (\"%s\") definition in \"HTD_Clocks\" category at TE_cfg.xml - CFG[\"HTD_Clocks\"][\"%s\"]") % (CFG["HTD_Clocks"]["sim_time_unit"]))
        self.uiptr = uiptr
        self.time_scale = self.train_tick_time()  # The resolution of scale is always 1p
        if("HTD_Clocks_Settings" not in list(CFG.keys())):
            htdte_logger.error("Missing \"HTD_Clocks_Settings\" value - (\"%s\") category at TE_cfg.xml - Used for clock definitions")
        if("sim_time_scale" not in list(CFG["HTD_Clocks_Settings"].keys())):
            htdte_logger.error("Missing \"sim_time_scale\" definition in CFG[HTD_Clocks_Settings] - category at TE_cfg.xml - Used for clock simulation clock scale definition")

    # ----------------------------------------------------------------------------------------------------------------------------------------
    def get_model_time(self):
        return 0
    # ----------------------------------------------------------------------------------------------------------------------------------------

    def train_tick_time(self):
        return CFG["HTD_Clocks_Settings"]["sim_time_scale"] * CFG["HTD_Clocks_Settings"]["sim_time_unit"]
    # ----------------------------------------------------------------------------------------------------------------------------------------

    def train_clocks(self): pass
    # ----------------------------------------------------------------------------------------------------------------------------------------

    def train_clock(self, clock_name): pass
