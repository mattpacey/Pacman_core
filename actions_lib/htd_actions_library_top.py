from htd_basic_action import *
from htd_utilities import *
from htd_collaterals import *
from htd_signal_action import *
from htd_clock_action import *
from htd_gen_action import *
from htd_tap_action import *
from htd_ubp_action import *
from htd_ubptrigger_action import *
from htd_stpl_mode import *
from htd_stf_action import *
from htd_spf_action import *
from htd_itpp_action import *
#from htd_pcuio_ascess_action import *
from htd_cr_access_action import *
from htd_sbftload_action import *
from htd_sbftload_kbl_action import *
from htd_uCPL_action import *
from htd_sig_readout_action import *
from htd_fivr_fuse_action import *
from htd_edram_fsm_action import *
from htd_mci_action import *
from htd_scratchpad_action import *
###

# --GEN action: wait cycles, SEINFO....
#
# ---------------------------------------
# def  exec_outbounded_action(obj,params,atype):
#     obj
#
#      execute_outbounded_action(self,inspect.getframeinfo(inspect.currentframe().f_back)[0:3],"gen",params)
#
#setattr(htd_base_flow,'exec_gen_action', exec_gen_action)
# ---------------
# def  exec_gen_action(params):
#     get_current_flow().execute_action(params,"GEN");

# ---------------------------------------------
# ---------------------------------------------
# def  exec_reg_action(params):
#     get_current_flow().execute_action(params,"REG");
# class REG(htd_base_action):
#    def __init__(self,action_name,source_file,source_lineno,currentFlow):
#        htd_base_action.__init__(self,self.__class__.__name__,action_name,source_file,source_lineno,currentFlow)
#    def verify_arguments(self):pass
#    def run(self):
#        self.inform( ("      Running REG::run:%s:%s:%s:%d \n\n") % (htd_base_action.get_action_name(self),
#	                                                  htd_base_action.get_action_type(self),
#							   htd_base_action.get_action_call_file(self),
#							     htd_base_action.get_action_call_lineno(self)))

# ---------------------------------------------
# def  exec_cachepload_action(obj,params):
#     get_current_flow().execute_action(params,"CACHEPLOAD");
# class CACHEPLOAD(htd_base_action):
#    def __init__(self,action_name,source_file,source_lineno,currentFlow):
#        htd_base_action.__init__(self,self.__class__.__name__,action_name,source_file,source_lineno,currentFlow)
#    def verify_arguments(self):pass
#    def run(self):
#        # FIXME - add actual action execution
#        self.inform( ("       Running %s::%s:%s:%d \n\n") % ( htd_base_action.get_action_type(self),
#                                                                  htd_base_action.get_action_name(self),
#							          htd_base_action.get_action_call_file(self),
#							          htd_base_action.get_action_call_lineno(self)))
