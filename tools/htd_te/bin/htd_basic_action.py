import re
import os
from htd_utilities import *
from htd_collaterals import *
from htd_te_shared import *
import datetime
from htd_statistics import *

FLOW_VERIFY_ONLY_MODE = 1
FLOW_RUN_MODE = 0
# -------------------------------------------
# ---------------HTD_PLAYER LIB--------------
if(os.environ.get('HTD_PLAYER_LOCATION') is None):
    htdte_logger.error('Missing obligatory unix environment ENV[HTD_PLAYER_LOCATION] - must point to user actions libraries location')
htdte_logger.inform(("Adding USER LIBRARY path=%s") % (os.environ.get('HTD_PLAYER_LOCATION')))
sys.path.append(os.environ.get('HTD_PLAYER_LOCATION'))
if(not os.path.isdir(os.environ.get('HTD_PLAYER_LOCATION'))):
    htdte_logger.error(
        ('The directory (%s) given in ENV[HTD_PLAYER_LOCATION] - is not directory or not exists') % (os.environ.get('HTD_PLAYER_LOCATION')))
sys.path.append(os.path.dirname(__file__))
from htd_player_top import *
# ------------------------------------------------------------------
# Global constrain verify method - used in action and segment class
# ------------------------------------------------------------------


def evaluate_constrain_condition(condition, src):
    if(re.match(r"<type\s+'int'>", str(type(condition)))):
        return 1 if(condition > 0) else 0
    if(re.match(r"<type\s+'bool'>", str(type(condition)))):
        return condition
    if(len(condition) == 0):
        return 1
    # ---------------
    constrain_str = condition.replace(" ", "")
    if(condition in [1, "TRUE", "true"]):
        return 1
    if(condition in [0, "FALSE", "false"]):
        return 1
    # ---Module
    module = constrain_str
    if(htdPlayer.signal_module_exists(constrain_str)):
        return 1
    else:
        return 0
# -----------------------
#
# ------------------------


class htd_base_action(object):
        # ----------------------

    def __init__(self, action_type, action_name, locfile, loclinenum, currentFlow, is_internal):

	#import pdb; pdb.set_trace()
        self.arguments = htd_argument_containter() #data container storing the flow global parameters
        
        self.arguments.declare_arg("source", "Specify which source for this action", "int", 0, 0)
        self.arguments.declare_arg(
            "debug_readback", "Debugability readback activity to be matched on DUT option, enforced on current action ..", "bool", 0)
        self.arguments.declare_arg(
            "action_lock", "Locking setting for following override. (Asserting error if trying override the setting)", "bool", 0)
        self.arguments.declare_arg("action_unlock", "UnLocking previously locked register fields. (Suppressing locked action capability)", "bool", 0)
        self.arguments.declare_arg("check", "Enable/Disable checkers on current action..", "bool", 1)
        self.arguments.declare_arg("express", "Enable/Disable pound(express) mode on current action ..", "bool", 0)
        self.arguments.declare_arg("postalignment", "Enable/Disable Post action run sync to modulo clocks (like SAL) ..", "bool", 1)
        self.arguments.declare_arg("postdelay", "Enable/Disable Post action delay in clocks defined by TE_cfg.xml ..", "bool", 1)
        self.arguments.declare_arg("silent_mode", "Disable any DUT activity (TE emulation mode) on current action..", "bool", 0)
        self.arguments.declare_arg("read_type", "Select readback mode on external DUT pins for current action functionality", "bool", 0)
        self.arguments.declare_arg(
            "waitcycles", "Define action verification range (error asserted if range exceed) or waiting cycles number.", "int", cfg_TE("inf_waitcycle_time"))
        self.arguments.declare_arg("refclock", "Define action verification clock resolution (accuracy)  .",
                                   "string", htdPlayer.hplClockMgr.get_default())
        self.arguments.declare_arg("maxtimeout", "Define action simulation FATAL error timeout.", "int", -1)
        self.arguments.declare_arg(
            "constraint", "Define action execution constraint, conditioning on rtl module existence or CFG.<Category>[<VarName]<=|==|!=|<=|>=><VarValue> .", "string_or_int", "")
        self.arguments.declare_arg("description", "Free string used for current action usage mode description  .", "string", "", ((
            "TE" in list(CFG.keys())) and ("obligatory_descripion_argument" in list(CFG["TE"].keys())) and CFG["TE"]["obligatory_descripion_argument"]))
        self.arguments.declare_arg(
            "post_module", "Used as a python source path for loading dynamic external method flow_run() just after current action .", "string", "")
        self.arguments.declare_arg("refactor", "Used to mark a current action for refactoring .", "bool", 0)
        self.arguments.declare_arg("disable_action", "Used disable a current action execution .", "bool", 0)
        self.arguments.declare_arg("dummy", "Used to create a dummy - template action for future usage - prevent any run or validation", "string", 0)
        self.arguments.declare_arg("stop_flow", "Used to stop flow run after the action execution", "bool", 0)
        self.arguments.declare_arg("stpl_mode", "Disable/Enable the stpl_mode optimization", "bool", 0)
        self.arguments.declare_arg("label", "Add label prior to the start of the action", "string", "")
        self.arguments.declare_arg("strobe_disable", "Strobe disable enforcement", "bool", 0)
        self.arguments.declare_arg("plabel", "Put predefined label prior to the start of the action", "bool", 0)
        self.arguments.declare_arg("expandata", "Slow TCLK for this instruction by this multiplier", "int", -1, 0)
        self.arguments.declare_arg("patmod_en", "Enable/Disable patmod support on this action", "int", 1, 0)
        self.arguments.declare_arg("patmod_vars", "Specify which patmod vars to use for this action", "string_or_list", "", 0)
        self.arguments.declare_arg(
            "action_status", "Argument use to track the status of the correponding action in the HTD Indicator Data Base. Possible value HVM|Injection|PlaceHolder|Unknown", "string", "Unknown", 0)
        self.arguments.declare_arg("label_domain", "Print field labels at specified domain only", "string", None, 0)

        # ---------------------

        self.__base_action_declared_arguments = self.arguments.declared_keys()
        self.__action_unique_key = []
        self.__action_name__ = action_name
        self.__action_type__ = action_type
        self.__location_file_ = locfile
        self.__location_line_ = loclinenum
        self.__dynamic_arguments_ = {}
        self.__current_flow = currentFlow
        self.__result = 0
        self.__action_indexing = []
        self.calling_action = ""
        self.action_time_start = 0
        self.action_time_end = 0
        self.action_model_time_start = 0
        self.action_model_time_end = 0
        self.dummy_mode = 0
        self.is_internal = is_internal
        self.documented = 1
        self.implicit_rtl_nodes_exists = 1
        self.explicit_rtl_nodes_exists = 1
        self.documented_details = "-"
        self.implicit_rtl_details = "-"
        self.explicit_rtl_details = "-"
        self.__final_register_assignment_by_field = {}
        #self.stf_gid_track = self.argument.get_argument('stf_gid_track')

        # init stf gid/bank usage tracking dict, group 0~ 15, bank 0~1, create 32 keys str(gid) + str(gid_bank)
        # stf_gid_track_init = self.init_stf_gid_track(15, 1)

    description = "The htd_base_action is a base flow class that will be inhereted into the rest htd action classes "
    author = "alexse"


    def get_base_action_declared_arguments_list(self): return self.__base_action_declared_arguments

    def capture_register_assignment_by_field(self, field_name, val):
        if(not self.arguments.get_argument("read_type")):
            self.__final_register_assignment_by_field[field_name] = val

    def get_register_assignment(self): return deepcopy(self.__final_register_assignment_by_field)

    def get_register_assignment_by_field(self, field_name):
        if(field_name not in list(self.__final_register_assignment_by_field.keys())):
            htdte_logger.error((" [%s:%s:%d] Trying to retrieve not existent register field name - \"%s\"") % (self.__action_name__,
                                                                                                               re.sub(r"[A-z0-9_]*/", "", self.get_action_call_file()), self.get_action_call_lineno(), field_name))
        return self.__final_register_assignment_by_field[field_name]

    def has_register_assignment_by_field(self, field_name): return (field_name in list(self.__final_register_assignment_by_field.keys()))

    def get_register_assignment_fields(self): return list(self.__final_register_assignment_by_field[field_name].keys())

    # --------------------------------------------------
    def is_inner_action(self): return False if(self.calling_action == "") else True

    def set_calling_action(self, calling_action_name): self.calling_action = calling_action_name

    def arguments_override(self): pass

    def i_am_htd_base_action_object(self):
        return 1

#    def get_action_stf_gid_trk(self):
#	    return self.stf_gid_track

    def get_action_name(self):
        return self.__action_name__

    def get_action_type(self):
        return self.__action_type__

    def get_action_call_file(self):
        return re.sub(r"[A-z0-9_\-]*/", "", self.__location_file_)

    def get_action_call_lineno(self):
        return self.__location_line_

    def get_arguments(self):
        return self.arguments

    def verify_obligatory_arguments(self):
        self.arguments.verify_obligatory_arguments(("Action:%s") % (self.__action_name__))

    def set_result(self, res):
        self.__result = res

    def get_result(self):
        return self.__result

    def get_curr_flow(self): return self.__current_flow
 # ------------------------------------

    def assign_action_indexing(self, action_indexing):
        if(not isinstance(action_indexing, list)):
            htdte_logger.error(("Illegal indexing type:%s, while expected list of string indexes (list of declared_arguments representing unique action assignment)") % (
                type(action_indexing)))
        self.__action_indexing.append(action_indexing)

    def get_action_indexing(self):  # return list of unique indexing
        # --proceed over all indexes and verify existence in assignment
        for i in range(0, len(self.__action_indexing)):
            index_used = True
            for k in range(0, len(self.__action_indexing[i])):
                if(not self.arguments.is_argument_assigned(self.__action_indexing[i][k])):
                    index_used = False
                    break
            if(index_used):
                self.__action_unique_key = [self.arguments.get_argument(x) for x in self.__action_indexing[i]]
                return self.__action_unique_key
        return []
 # -----Action inform callback

    def inform(self, msg):
        info = inspect.getframeinfo(inspect.currentframe().f_back)[0:3]
        htdte_logger.inform((" [%s:%s:%d] %s") % (self.__action_name__, re.sub(
            r"[A-z0-9_]*/", "", self.get_action_call_file()), self.get_action_call_lineno(), msg))

    def inform_nosrc(self, msg):
        htdte_logger.inform((" [%s::%s] %s") % (self.__current_flow.get_flow_type(), self.__action_name__, msg))
 # -----Action error callback

    def error(self, msg, exit):
        info = inspect.getframeinfo(inspect.currentframe().f_back)[0:3]
        self.error_bysrc(re.sub(r"[A-z0-9_]*/", "", self.get_action_call_file()), info[1], msg, exit)

    def error_bysrc(self, srcfile, srcline, msg, exit):
        if exit:
            htdte_logger.error((" [%s:%s:%d] %s") % (self.__action_name__, self.get_action_call_file(), self.get_action_call_lineno(), msg))
        else:
            htdte_logger.error_str((" [%s:%s:%d] %s") % (self.__action_name__, self.get_action_call_file(), self.get_action_call_lineno(), msg))
    # -------------------------------------

    def verify_obligatory_arguments(self):
        info = inspect.getframeinfo(inspect.currentframe().f_back)[0:3]
        loc_string = ("%s:%d") % (info[0], info[1])
        self.arguments.verify_obligatory_arguments(("Action:%s") % (self.__action_name__), loc_string)
        # ---Verify that all given arguments are matching dual_read_write_mode restriction
        if(not self.arguments.is_enabled_dual_read_write_mode()):
            for nda_key in self.arguments.not_declared_keys():
                for val in self.arguments.arg_l[nda_key]["val"]:
                    if(val.value >= 0 and val.read_value >= 0):
                        htdte_logger.error((" [%s:%s:%d] %s") % (self.__action_name__, self.get_action_call_file(), self.get_action_call_lineno(),
                                                                 ("Trying to assign a dual write and read mode in \"%s\"-action , while this action is not enabled for this mode.\n(Use self.arguments.enable_dual_read_write_mode() in action class to enable this option). ") % (self.__action_type__)))
    # ----------------

    def get_declared_arguments(self):
        return self.arguments.declared_keys()

    def get_not_declared_arguments(self):
        return self.arguments.not_declared_keys()

    def get_all_arguments(self):
        return list(self.arguments.arg_l.keys())

    def argument_exists(self, name):
        return (name in list(self.arguments.keys()))

    def get_action_argument(self, name):
        if(self.argument_exists(name)):
            return self.arguments.get_argument(name)
        else:
            self.error(("Accessing to non existent action (%s) argument - \"%s\"") % (self.__action_name__, name), 1)

    def get_action_argument_last_entry(self, name):
        s = self.get_action_argument(name)
        return self.arguments.get_argument(name)[len(s) - 1]

    # ---------------------------------------------
    # def get_action_argument_value(self,name):
    #    return self.get_action_arguments(name)[0].value
    # --------------------------------------------------
    def print_action_arguments(self):
        self.arguments.print_arguments(("Action Parameters %10s, type %5s") % (self.__action_name__, self.__action_type__))

    def print_action_arguments_help(self):
        self.arguments.print_help()
    # -------------------------------------------------------------

    def has_required_rtlNodes_info(self): return (1, "")
    # -----------------------------------------------------------

    def get_action_not_declared_argument_names(self):
        self.error(("This method has no specification in action %s class - should return a list of specific action arguments like register (design) fields .. ") % (self.__action_name__), 1)
    # -----------------------------------------------------------

    def verify_action_arguments(self):
        self.action_time_start = datetime.datetime.now().time()
        if(not self.arguments.get_argument("dummy")):
            self.verify_arguments()
            self.verify_obligatory_arguments()
            # ---Verify constraint: could be a reference  to CFG.<category>[==,!=,>,<,>=,<=]<val>,
            evaluate_constrain_condition(self.arguments.get_argument("constraint"), ("%s:%d") %
                                         (self.get_action_call_file(), self.get_action_call_lineno()))
            # --Verify conflict between declared and not declared arguments--------
            not_dec_arguments = self.get_action_not_declared_argument_names()
            if(isinstance(not_dec_arguments, list)):
                for da in self.get_declared_arguments():
                    if(self.arguments.is_argument_assigned(da) and (da in not_dec_arguments)):
                        self.error(("Action's (%s) argument - \"%s\" is defined as declared and not_declared (design field) parameter , pls specify \"<delared|not_declared>:%s\" reference to specify the target parametrization type. ") % (self.__action_name__, da), 1)
            # ---verify Clockref---
            if(not htdPlayer.hplClockMgr.is_clock(self.arguments.get_argument("refclock"))):
                self.error(("Action's (%s) argument - \"refclock\"=\"%s\" doesn't match any known clocks: %s") %
                           (self.__action_name__, self.arguments.get_argument("refclock"), str(htdPlayer.hplClockMgr.get_all_clocks())), 1)
        else:
            self.inform(("!!!!!Running the action-%s in \"dummy\" mode..") % (self.__class__.__name__))
            self.dummy_mode = 1
            self.verify_arguments()
            self.verify_obligatory_arguments()
        # ---Verify if action_lock given, indexing must be defined
        if(self.arguments.get_argument("action_lock")):
            if(len(self.get_action_indexing()) == 0):
                self.error(("Action's (%s) \"action_lock\"  argument given while no unique keys are %s .Pls verify that action type-%s has self.assign_action_indexing([<keys_list>])assignment") % (self.__action_name__,
                                                                                                                                                                                                     ("matched (from %s)") % (str(self.__action_indexing)) if(
                                                                                                                                                                                                         len(self.__action_indexing)) else "defined at action.assign_action_indexing..",
                                                                                                                                                                                                     self.get_action_type()), 1)
    # -------------------------------------------------------------
    # --Callback methods to be overriten by specific action type
    # -------------------------------------------------------------

    def verify_arguments(self):
        self.error(("The action class \"%s\" is not allowed for direct calling , pls use an inhereted per action type objects") % (self.__class__.__name__))
        #self.inform( ("Running htd_base_action::verify_arguments:%s:%s:%s:%d") % (self.__action_name__,self.__action_type__,self.__location_file_,self.__location_line_))

    def post_run_place_holder(self): pass

    def post_run(self):
        if(not self.arguments.get_argument("dummy")):
            self.post_run_place_holder()
            if(self.arguments.get_argument("postdelay")):
                if("post_action_wait_clock" not in CFG["TE"]):
                    self.error(
                        ("Missing  CFG[\"TE\"][\"post_action_wait_clock\"] -  clock name referencied to make a delay between actions/flows") % (), 1)
                if("post_action_wait_cycles" not in CFG["TE"]):
                    self.error(
                        ("Missing  CFG[\"TE\"][\"post_action_wait_cycles\"] -  clock cycles number referencied to make a delay between  actions/flows"), 1)
                if CFG["HPL"].get("NEW_LABEL_SPEC") is 1 and int(CFG["TE"]["post_action_wait_cycles"]) > 0:
                    htdPlayer.hpl_to_dut_interface.label("ph%s__%s__postdelay" % (self.get_curr_flow().phase_name, self.get_action_name()))
                htdPlayer.wait_clock_num(int(CFG["TE"]["post_action_wait_cycles"]), CFG["TE"]["post_action_wait_clock"])

            if(self.arguments.get_argument("postalignment")):
                if("sync_modulo_cycles" not in CFG["TE"]):
                    self.error(("Missing  CFG[\"TE\"][\"sync_modulo_cycles\"] -  modulo cycles number for alignment at between actions/flows") % (), 1)
                if("sync_modulo_clock" not in CFG["TE"]):
                    self.error(("Missing  CFG[\"TE\"][\"sync_modulo_clock\"] -  clock name referencied for alignment at between actions/flows") % (), 1)
                htdPlayer.sync_to_clock_modulo(CFG["TE"]["sync_modulo_clock"], int(CFG["TE"]["sync_modulo_cycles"]))
            if(self.arguments.get_argument("stop_flow")):
                self.inform("!!!!!!!!!!!stop_flow - argument detected : Breaking flow execution on this point...!!!!!!!!!!!!!!!")
                self.__current_flow.__stop_flow = True
        if(self.arguments.get_argument("silent_mode") and not self.__current_flow.is_verification_mode()):
            htdPlayer.unset_silent_mode()
        # --------------------------
        #self.inform(("Running htd_base_action::pre_run:%s:%s:%s:%d") % (self.__action_name__,self.__action_type__,self.__location_file_,self.__location_line_))
        self.action_time_end = datetime.datetime.now().time()
        self.action_model_time_end = htdPlayer.hpl_to_dut_interface.get_model_time()
        HTD_STATISTICS_MGR.capture_statistics(self)
    # ----------------------------

    def pre_run_place_holder(self): pass

    def pre_run(self):
        if(self.arguments.get_argument("silent_mode")):
            htdPlayer.set_silent_mode()
            self.inform("!!!!!!!!!!!Running Action in DUT silent mode...!!!!!!!!!!!!!!!")
        self.pre_run_place_holder()
        self.action_model_time_start = htdPlayer.hpl_to_dut_interface.get_model_time()
        #self.inform( ("Running htd_base_action::pre_action_run:%s:%s:%s:%d") % (self.__action_name__,self.__action_type__,self.__location_file_,self.__location_line_))
        self.add_pattern_indicators()

    def run(self):
        self.error(("The action class \"%s\" is not allowed for direct calling , pls use an inhereted per action type objects") % (self.__class__.__name__))
        #self.inform( ("Running htd_base_action::run:%s:%s:%s:%d") % (self.__action_name__,self.__action_type__,self.__location_file_,self.__location_line_))

    def add_pattern_indicators(self):
        pattern_indicators_enabled = 0

        if (self.arguments.get_argument("label")):
            htdPlayer.hpl_to_dut_interface.label(self.arguments.get_argument("label"), self.arguments.get_argument("label_domain"))
        if (self.arguments.get_argument("plabel")):
            htdPlayer.hpl_to_dut_interface.label(self.get_defined_label(), self.arguments.get_argument("label_domain"))
        if ("ActionPatternIndicators" in list(CFG.keys())):
            if ("enabled" in CFG["ActionPatternIndicators"] and CFG["ActionPatternIndicators"]["enabled"] == 1):
                pattern_indicators_enabled = 1

            if (pattern_indicators_enabled == 1):
                if ("pre_action_comment" in CFG["ActionPatternIndicators"]):
                    htdPlayer.hpl_to_dut_interface.add_comment(CFG["ActionPatternIndicators"]["pre_action_comment"])
                if ("pre_action_label" in CFG["ActionPatternIndicators"]):
                    htdPlayer.hpl_to_dut_interface.label(CFG["ActionPatternIndicators"]["pre_action_label"], self.arguments.get_argument("label_domain"))

        if (CFG["HPL"].get("NEW_LABEL_SPEC") == 1 and
                not self.is_internal and
                self.__class__.__name__ != "STF" and
                self.arguments.get_argument("label", noerr=1) in ["N/A", ""] and
                self.arguments.get_argument("op", noerr=1) not in ["FORCE", "CHECK", "PLABEL", "PINFO", "ITPP"]):
            htdPlayer.hpl_to_dut_interface.label(self.get_new_label(), self.arguments.get_argument("label_domain"))

    def get_defined_label(self):
        return self.__action_name__

    def get_new_label(self):
        if(self.get_curr_flow().phase_name != ""):
            label_reset_phase = self.get_curr_flow().phase_name
        else:
            label_reset_phase = 'none'

        return "ph%s__%s" % (label_reset_phase, self.get_action_name())

    def debug_readback(self): pass

    def verify_action(self): pass

    def get_specific_html_help(self): return ""


#####################################################################
from htd_history_manager import *
