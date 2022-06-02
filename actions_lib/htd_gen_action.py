from htd_basic_action import *
from htd_utilities import *
from htd_collaterals import *
from htd_player_top import *
# ---------------------------------------------


class GEN(htd_base_action):

    def __init__(self,action_name,source_file,source_lineno,currentFlow,is_internal):
        htd_base_action.__init__(self,self.__class__.__name__,action_name,source_file,source_lineno,currentFlow,is_internal)
        self.gen_action_types=["WAIT","PCOMMENT","PINFO","PLABEL","ITPP", "SPF", "RATIO", "execute", "start_clock", "stop_clock"]
        self.arguments.set_argument("source", 1, "Specify which source for this action")
        self.arguments.declare_arg("op"  ,("Gen action type.Supported types are: %s..")%(str(self.gen_action_types))              ,self.gen_action_types,"",1 )
        self.arguments.declare_arg("strvalue"  ,"Used as a string parameter for PINFO,PLABEL,PCOMMENT,RATIO"                              ,"string",             "",0 )
    #----------------------
    def get_action_not_declared_argument_names(self):pass 
    #---------------------
    def verify_arguments(self):
        self.inform(("       Verifying %s::%s:%s:%d ....") % (htd_base_action.get_action_type(self),
                                                              htd_base_action.get_action_name(self),
                                                              htd_base_action.get_action_call_file(self),
                                                              htd_base_action.get_action_call_lineno(self)))
        self.verify_obligatory_arguments()
        # --If SERIALSET is used , need to handle "width" parameter
        if(self.get_action_argument("op") == "WAIT"):
            self.arguments.set_obligatory("waitcycles")
            self.arguments.set_obligatory("refclock")
        elif(self.get_action_argument("op") in ["PCOMMENT", "PINFO", "PLABEL", "ITPP", "SPF", "RATIO", "execute", "start_clock", "stop_clock"]):
            self.arguments.set_obligatory("strvalue")
        else:
            self.error(("Action's (%s) : Unsupported action type found - %s") % (self.__action_name__, self.get_action_argument_value("op")), 1)
    # ------------------------------

    def run(self):
        self.inform(("      Running GEN::run:%s:%s:%s:%d \n\n") % (htd_base_action.get_action_name(self),
                                                                   htd_base_action.get_action_type(self),
                                                                   htd_base_action.get_action_call_file(self),
                                                                   htd_base_action.get_action_call_lineno(self)))
        if(self.get_action_argument("op") == "WAIT"):
            htdPlayer.wait_clock_num(self.get_action_argument("waitcycles"), self.get_action_argument("refclock"))
        elif(self.get_action_argument("op") == "PINFO"):
            htdPlayer.hpl_to_dut_interface.set_pattern_info(self.get_action_argument("strvalue"))
        elif(self.get_action_argument("op") == "PLABEL"):
            htdPlayer.hpl_to_dut_interface.label(self.get_action_argument("strvalue"), self.get_action_argument("label_domain"))
        elif(self.get_action_argument("op") == "PCOMMENT"):
            htdPlayer.hpl_to_dut_interface.add_comment(self.get_action_argument("strvalue"))
        elif(self.get_action_argument("op") == "SPF"):
            htdPlayer.hpl_to_dut_interface.write_spf_cmd(self.get_action_argument("strvalue"))
        elif(self.get_action_argument("op") == "ITPP"):
            htdPlayer.hpl_to_dut_interface.write_itpp_cmd(self.get_action_argument("strvalue"))
        elif(self.get_action_argument("op") == "execute"):
            htdPlayer.hpl_to_dut_interface.execute_signal(self.get_action_argument("strvalue"))
        elif(self.get_action_argument("op") == "RATIO"):
            self.ratio_command()
        elif(self.get_action_argument("op") == "start_clock" or self.get_action_argument("op") == "stop_clock"):
            if(self.get_action_argument("op") == "start_clock"):
                htdPlayer.hpl_to_dut_interface.start_clock(self.arguments.get_argument("strvalue"))
            elif(self.get_action_argument("op") == "stop_clock"):
                htdPlayer.hpl_to_dut_interface.stop_clock(self.arguments.get_argument("strvalue"))

            if (self.get_action_argument("waitcycles") != 0):
                htdPlayer.hpl_to_dut_interface.wait_clock_num(self.get_action_argument("waitcycles"), self.get_action_argument("refclock"))
        else:
            self.error(("Action's (%s) : Unsupported action type found - %s") % (self.__action_name__, self.get_action_argument("op")), 1)

    def ratio_command(self):
        ratio_clock = "xxtck" if "RatioClk" not in CFG["HPL"] else CFG["HPL"]["RatioClk"]
        strvalue = self.get_action_argument("strvalue")
        if (strvalue == "restore"):
            htdPlayer.restore_ratio()
        else:
            (success, ratio) = util_get_int_value(strvalue)
            if (success == 0):
                self.error("Can't set illegal integer value %s as ratio" % strvalue, 1)
            htdPlayer.set_ratio(ratio, ratio_clock)
