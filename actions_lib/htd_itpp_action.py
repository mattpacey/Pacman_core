from htd_basic_action import *
from htd_utilities import *
from htd_collaterals import *
from htd_player_top import *
import os
import re
# ---------------------------------------------
# Running spf sequence file
# -----------------------------------------------
#
#
#
# ------------------------------------------


class ITPP(htd_base_action):
    def __init__(self,action_name,source_file,source_lineno,currentFlow,is_internal):
     htd_base_action.__init__(self,self.__class__.__name__,action_name,source_file,source_lineno,currentFlow,is_internal)
     self.arguments.set_argument("source", 1, "Specify which source for this action")
     self.arguments.declare_arg("itpp_file"             ,"The path to file define a test sequence in ITPP format","string"      ,"none"  ,1 )  
    #----------------------
    def get_action_not_declared_argument_names(self):pass 
    def verify_arguments(self): pass
    # ------------------------

    def run(self):
        self.inform(("         Running ITPP_SEQUENCE itpp_file=%s \n\n") % (self.arguments.get_argument("itpp_file")))
        try:
            for line in open(self.arguments.get_argument("itpp_file"), 'r').readlines():
                htdPlayer.hpl_to_dut_interface.write_itpp_cmd(line)
        except IOError:
            htdte_logger.error("Can't open file %s" % (self.arguments.get_argument("itpp_file")))
        htdte_logger.inform('Done Reading ITPP')
