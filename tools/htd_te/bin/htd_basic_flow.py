import re
import pkgutil
import inspect
from htd_utilities import *
from htd_collaterals import *
from htd_te_shared import *
from htd_basic_action import *
import io

# enum declaration


def enum_flow(**named_values):
    return type('Enum', (), named_values)


currently_running_flow = None
module = sys.modules[__name__]
flowTypeEnum = enum_flow(N_A='N_A', MLC_SBFT='MLC_SBFT', SLC_SBFT='SLC_SBFT', FC_SBFT='FC_SBFT', FC='FC')

# a function to verify that the segments that were loaded match their location as specified
# in the configuration file
# currently throws a warning if there is no match. might be changed later to an error


def verify_segments_location(segments_l, segment_type):
    htdte_logger.inform("Verifying location %s segments" % (segment_type))
    for cls in segments_l:
        file_path = inspect.getfile(cls)
        file_name = os.path.basename(file_path)
        file_name = os.path.splitext(file_name)[0]
        class_name = cls.__name__

        # remove the _Rev from class
        rev_location = class_name.find("_Rev")
        if (rev_location > 0):
            class_name_no_rev = class_name[:rev_location]
        else:
            class_name_no_rev = class_name

        if class_name_no_rev in list(CFG["SEGMENTS"].keys()):
            expected_segment_file = CFG["SEGMENTS"][class_name_no_rev]["module"]
            # get rid of extension
            expected_segment_file = os.path.splitext(expected_segment_file)[0]
            htdte_logger.debug("Segment %s loaded from file : %s expected file :%s" % (class_name_no_rev, file_name, expected_segment_file), 0)
            if (expected_segment_file != file_name):
                htdte_logger.warn("class name %s loaded from file: %s (full path %s) while expected file is: %s" %
                                  (class_name_no_rev, file_name, file_path, CFG["SEGMENTS"][class_name_no_rev]["module"]))
    htdte_logger.inform("Done verifying %s segments" % (segment_type))


# ---------------ACTIONS LIBRARY SETUP----------
if (os.environ.get('HTD_ACTIONS_LOCATION') is None):
    htdte_logger.error(
        'Missing obligatory unix environment ENV[HTD_ACTIONS_LOCATION] - must point to user actions libraries location')
htdte_logger.inform(("Adding USER LIBRARY path=%s") % (os.environ.get('HTD_ACTIONS_LOCATION')))
sys.path.append(os.environ.get('HTD_ACTIONS_LOCATION'))
if (not os.path.isdir(os.environ.get('HTD_ACTIONS_LOCATION'))):
    htdte_logger.error(('The directory (%s) given in ENV[HTD_ACTIONS_LOCATION] - is not directory or not exists') % (
        os.environ.get('HTD_ACTIONS_LOCATION')))
sys.path.append(os.path.dirname(__file__))
from htd_actions_library_top import *
# -----------------------------------
from htd_basic_segment import *
# ------------------------------------------------
# -----------------SEGMENT IP LIBRARIES--------------
# Using predefined ENV to load user top file - HTD_SEGMENTS_LOCATION
if (os.environ.get('HTD_SEGMENTS_LOCATION') is None):
    htdte_logger.error(
        'Missing obligatory unix environment ENV[HTD_SEGMENTS_LOCATION] - must point to user flow segments libraries location')

# set seg lib path here
segment_lib_path = os.environ.get('HTD_SEGMENTS_LOCATION')
# split into array
segment_lib_path_list = segment_lib_path.split(";")

# for loop over next set of checks
for path in segment_lib_path_list:
    htdte_logger.inform(("Adding USER LIBRARY path=%s") % (path))
    sys.path.append(path)
    if (not os.path.isdir(path)):
        htdte_logger.error(('The given directory (%s) in ENV[HTD_SEGMENTS_LOCATION] - is not directory or not exists') % (dir))
    sys.path.append(os.path.dirname(__file__))
# end for loop

#from htd_segments_library_top import *
if (os.environ.get('HTD_IPS_LOCATION') is None):
    htdte_logger.error(
        'Missing obligatory unix environment ENV[HTD_IPS_LOCATION] - must point to user IP libraries location')

# set ip lib path here
ipsegment_lib_path = os.environ.get('HTD_IPS_LOCATION')
# split into array
ipsegment_lib_path_list = ipsegment_lib_path.split(";")

# for loop over next set of checks
for path in ipsegment_lib_path_list:
    htdte_logger.inform(("Adding USER LIBRARY path=%s") % (path))
    if (not os.path.isdir(path)):
        htdte_logger.error(('The given directory (%s) in ENV[HTD_IPS_LOCATION] - is not directory or does not exist') % (path))
    sys.path.append(path)
    sys.path.append(os.path.dirname(__file__))
# end for loop

# ----------------------
loaded_modules = []

# combine segment and ip list
ip_segment_combined_list = segment_lib_path_list + ipsegment_lib_path_list

htdte_logger.inform(("combined segments = %s") % (ip_segment_combined_list))
if ("SEGMENTS" in list(CFG.keys())):
    for seg_module in list(CFG["SEGMENTS"].keys()):

        module_location = ""
        module_count = 0
        for segs in ip_segment_combined_list:
            combined_module = ("%s/%s") % (segs, CFG["SEGMENTS"][seg_module]["module"])
            if (os.path.exists(combined_module)):
                module_location = combined_module
                module_count += 1

        if (module_count == 0):
            htdte_logger.error((
                               'The segment module (%s) given in TE_cfg.xml:CFG["SEGMENTS"][%s] is not found found in  SEGMENT(%s) or IP(%s) directories') % (seg_module, seg_module, segment_lib_path, ipsegment_lib_path))
        if (module_count > 1):
            htdte_logger.error((
                'The segment module (%s) given in TE_cfg.xml:CFG["SEGMENTS"][%s] is found in multiple SEGMENT(%s) and IP(%s) directories') % (
                seg_module, seg_module, segment_lib_path, ipsegment_lib_path))
            # --------------
        if (module_location not in loaded_modules):
            status, mname, py_mod = util_dynamic_load_external_module(module_location)
            if (not status):
                htdte_logger.error((" Can't load segment module - %s ") % (module_location))
            exec((("from %s import *") % (mname)), globals())
            htdte_logger.inform(("Successfully loaded segment module=%s") % (module_location))
            loaded_modules.append(module_location)

# make sure there is 1:1 match between seg name and the path
segements_classes = util_itersubclasses(htd_flow_segment)
verify_segments_location(segements_classes, "Flow")

ip_classes = util_itersubclasses(htd_ip_segment)
verify_segments_location(ip_classes, "IP")

# ---------------------------------
for acls in util_itersubclasses(htd_base_action):
    act_type = acls.__name__.upper()
    # setattr(module,('%s_action')%(acls.__name__.lower()),
    #  (lambda x,params,atype=act_type: currently_running_flow.exec_action(params,atype,inspect.getframeinfo(inspect.currentframe().f_back)[0],inspect.getframeinfo(inspect.currentframe().f_back)[1])))
    exec ((
          "def %s_action(params): currently_running_flow.exec_action(params,\"%s\",inspect.getframeinfo(inspect.currentframe().f_back)[0],inspect.getframeinfo(inspect.currentframe().f_back)[1])") % (
          acls.__name__.lower(), act_type))
    print(
        "def %s_action(params): currently_running_flow.exec_action(params,\"%s\",inspect.getframeinfo(inspect.currentframe().f_back)[0],inspect.getframeinfo(inspect.currentframe().f_back)[1])" % (
        acls.__name__.lower(), act_type))
# ---------------------------
#
# ---------------------------


class htd_base_flow(object):
    description = "The htd_base_flow is a base flow class that will be inherited into the rest htd flows "
    author = "alexse"
    __stop_all_segments = False

    def set_stop_all_segments_at_action(self, flag):
        htd_base_flow.__stop_all_segments = flag

    def get_stop_all_segments_at_action(self):
        return htd_base_flow.__stop_all_segments

    # ----------------------
    def __init__(self, flow_type, flow_num):
        self.check = 1
        self.express = 0
        self.silent_mode = 0
        self.__flow_type__ = flow_type
        self.__flow_num__ = flow_num
        self.__stop_flow = False
        self.__current_action = None
        self.__flowEnum = flowTypeEnum.N_A
        self.phase_name = ""
        self.arguments = htd_argument_containter(1)  # data container storing the flow declared parameters
        self.arguments.declare_arg("debug_readback",
                                   "Debugability readback activity to be matched on DUT option, enforced on current segment..",
                                   "bool", 0)
        self.arguments.declare_arg("check", "Enable/Disable checkers on entire of segment..", "bool", 1)
        self.arguments.declare_arg("express", "Enable/Disable pound(express) mode on entire of segment..", "bool", 0)
        self.arguments.declare_arg("bfm_mode", "Toggle different bfm modes..", ["normal", "injection", "mci", "stf"],
                                   "normal")
        self.arguments.declare_arg("silent_mode", "Disable any DUT activity (TE emulation mode) on entire of segment..",
                                   "bool", 0)
        self.arguments.declare_arg("disable_segment", "Disable segment by name on entire of segment..", "bool", 0)
        self.arguments.declare_arg("post_module",
                                   "Used as a python source path for loading dinamic external method flow_run() just after current segment .",
                                   "string", "")
        self.arguments.declare_arg("post_alignment", "Enable/Disable Post flow run sync to modulo clocks (like SAL) ..",
                                   "bool", 1)
        self.arguments.declare_arg("pre_alignment", "Enable/Disable Pre flow run sync to modulo clocks (like SAL) ..",
                                   "bool", 1)
        self.arguments.declare_arg("disable_readout", "Disable all actions execution with active read_type argument ..",
                                   "bool", 0)
        self.arguments.declare_arg("flow_flavor", "Flow flavor could be Pre/Precat/Mid/Midcat/Test ..",
                                   "string", "UndefinedFlavor", 0)
        self.arguments.declare_arg("expandata", "Slow TCLK for this instruction by this multiplier", "int", -1, 0)

        # init stf gid/bank usage tracking dict, group 0~ 15, bank 0~1, create 32 keys str(gid) + str(gid_bank)
        self.select_mode = ["OUTPUT_ENABLED", "LISTEN_ONLY", "BIFURCATED", "OUTPUT_ENABLED_DATALOG", "LISTEN_ONLY_DATALOG", "BIFURCATED_DATALOG"]
        stf_gid_track_init = self.init_stf_gid_track(15, 1, self.select_mode)
        self.arguments.declare_arg("stf_gid_track", "note STF endpoint per gid&bank in a dict structure", "dict", stf_gid_track_init, 0)

        self.__per_action_arguments = {}  #data container storing the action override parameters[ <val>,<origin source of argument>]
        self.__current_obj_ = self
        self.__ip_segments_ = {}
        self.__ip_segments_exec_verify = {}
        self.__existent_action = {}
        self.__current_segment = None
        self.cluster_model_mode = False
        self.__ip_segment_execution_tracker = []
        if ("cluster_model_mode" not in list(CFG["TE"].keys())):
            #htdte_logger.error((" Missing CFG[\"TE\"][\"cluster_model_mode\"] - parameter used to enable/disable cluster(partial mode) model mode: all \"vertical\" segment are masked , only relevant IP segments are running. "))
            htdte_logger.inform(
                " Missing CFG[\"TE\"][\"cluster_model_mode\"] - parameter used to enable/disable cluster(partial mode) model mode: all \"vertical\" segment are masked , only relevant IP segments are running.  IPFication disabled in this run ")
        else:
            self.cluster_model_mode = CFG["TE"]["cluster_model_mode"]
        if (self.cluster_model_mode):
            htdte_logger.inform(
                "WARNING!!! **************************************************************************************************!!!WARNING")
            htdte_logger.inform(
                "WARNING!!!   CLUSTER MODE ENABLED : ALL VERTICAL SEGMENTS ARE GATED , ONLY RELEVANT IP SEGMENTS ARE EXECUTED !!!WARNING")
            htdte_logger.inform(
                "WARNING!!! **************************************************************************************************!!!WARNING")
        # -------Verify "IPENABLE" integrity ,could be done only after flow and segments classes declaration----------------------------
        if ("IPENABLE" in list(CFG.keys())):
            for ip in list(CFG["IPENABLE"].keys()):
                ip_name_found = False
                for ipsegment in util_itersubclasses_names(htd_ip_segment):
                    (seg, stage, rev) = htd_segment_naming_disassembly(ipsegment)
                    full_seg_name = ("%s_Stage%s") % (seg, stage)
                    if (full_seg_name in list(CFG["SEGMENTS"].keys()) and CFG["SEGMENTS"][full_seg_name]["rev"] == rev):
                        us = eval(ipsegment)(self)
                        if (us.get_ip_name() == ip):
                            ip_name_found = True
                            break
                if (not ip_name_found):
                    htdte_logger.error(
                        (" Illegal/unknown ip name -\"%s\" found in CFG[\"IPENABLE\"] - ip enable table ") % (ip))
    # -----------------------
        self.unset_verify_mode()

    def html_help(self):
        str_result = ""
        str_result += add_class_help_description("htd_base_flow", "exec_segment", "Executing a segment(pre_segment_verification()->segment_run()->debug_readback()) sequence ",
                                                 "self.exec_segment({\"segment\":&lt;segment_name&gt;,\"description\":&lt;obligatory segment description&gt;[,&lt;segment_arg&gt;:&lt;arg_value&gt;][,\"disable_segment\":&lt;0|1&gt;]")
        str_result += add_class_help_description("htd_base_flow", "get_previously_running_action_argument_val", "Retrieve argument assignment from one of previously running actions ",
                                                 ("self.get_previously_running_action_argument_val(&lt;action_name&gt;,&lt;actionType:%s&gt;&lt;argumentName-requested_argument_name&gt;)") % (str(util_itersubclasses_names(htd_base_action))))
        for action_type in util_itersubclasses_names(htd_base_action):
            str_result += add_class_help_description("htd_base_flow", ("self.exec_%s_action") % (action_type.lower()),
                                                     "Running action sequence: verify_action_arguments()-> pre_run_place_holder()->run()->post_run_place_holder()\
					 - declared arguments : predefined arguments with predefined types (sting,bool,int,string_or_int) and predefined initial values\
					 - not declared arguments: design dependent arguments , usually register fields , assumed by integre/long type only ",
                                                     ("self.exec_%s_action({&lt;action_name&gt;,&lt;actionType:%s&gt;[,&lt;action_argument&gt;:&lt;value&gt;][,declared:&lt;action_argument&gt;:&lt;value&gt;][,notdeclared:&lt;action_argument&gt;:&lt;value&gt;]})") % (action_type.lower(), action_type.lower()))
        return str_result
    # ---------------------------------------------------------

    def init_stf_gid_track(self, gid_range, gid_bank_range, select_mode_list):
        gid_usage_track = {}
        for gid in range(0, gid_range + 1):
            gid_usage_track[gid] = {}
            for mode in select_mode_list:
                gid_usage_track[gid][mode] = {}
                for gid_bank in range(0, gid_bank_range + 1):
                    gid_usage_track[gid][mode][gid_bank] = []

        return gid_usage_track

    def clear_phase_name(self):
        self.phase_name = ""

    def clear_current_segment(self):
        self.__current_segment = None

    def clear_names(self):
        self.clear_phase_name()
        self.clear_current_segment()
        htdte_logger.clrPhaseName()

    def set_current_segment(self, segment):
        self.__current_segment = segment

    def is_flow_stop_rised(self):
        return self.__stop_flow

    def get_ip_name(self):
        return self.ip_name

    def get_current_action(self):
        return self.__current_action

    def get_current_segment(self):
        return self.__current_segment

    def disable_stop_segment_at_action(self):
        if (self.__current_segment is not None):
            self.__current_segment.unset_stop_all_segments()

    def set_verify_mode(self):
        self.__verification_mode = True

    def unset_verify_mode(self):
        self.clear_names()
        self.__verification_mode = False

    def unset_stop_flow_mode(self):
        self.__stop_flow = False

    def is_verification_mode(self):
        return self.__verification_mode

    def help_cmd(self):
        self.inform(("----------Base flow arguments: %s---------\n") % (segmentName))

    def debug_readback(self):
        htdte_logger.error((
                           " debug_readback() method is used to create SI readback activity to verify flow -\"%s_%d\" success criteria and should be overriten by inherited flow object. ") % (
                           self.__flow_type__, self.__flow_num__))

    def i_am_htd_base_flow_object():
        return 1

    def get_flow_type(self):
        return self.__flow_type__

    def get_flow_num(self):
        return self.__flow_num__

    def get_flow_flavor(self):
        return self.arguments.get_argument("flow_flavor")

    def get_flow_type_enum(self):
        return self.__flowEnum

    def set_flow_type_enum(self, flowEnum):
        self.__flowEnum = flowEnum

    def verify_obligatory_arguments(self):
        self.arguments.verify_obligatory_arguments(("Flow:%s:%d") % (self.__flow_type__, self.__flow_num__))

    def verify_flow_arguments(self):
        pass

    def get_per_action_cmd_arguments(self):
        return self.__per_action_arguments
        # -----Action inform callback

    def inform(self, msg, distribute_to_interface=0, level=0, prefix="Inform"):
        info = inspect.getframeinfo(inspect.currentframe().f_back)[0:3]
        self.inform_bysrc(info[0], info[1], msg, level, prefix)

    def inform_bysrc(self, currfile, currline_no, msg, distribute_to_interface=0, level=0, prefix="Inform"):
        htdte_logger.inform(
            (" [%s:%d:%s:%d] %s") % (self.__flow_type__, self.__flow_num__, currfile, currline_no, msg),
            distribute_to_interface, level, prefix)

    def evaluate_action_in_blacklist(self, action_type, act):
        if(not htd_history_mgr.blacklist_has_type(action_type)):
            return
        action_indexing = act.get_action_indexing()
        if(len(action_indexing) > 0):
            lock_entry = {}
            if(htd_history_mgr.blacklist_has(act, action_indexing)):
                lock_entry = htd_history_mgr.blacklist_get(act, action_indexing)
                for p in act.arguments.not_declared_keys():
                    if(p in list(lock_entry.keys())):
                        param = act.arguments.get_argument(p)
                        if(isinstance(param, list)):
                            param = param[len(param) - 1].value
                        if(lock_entry[p] != param):
                            htdte_logger.error((" Trying to override previously locked action argument: locked_by:%s:%d,%s=%s(previously assigned to %s)\n Could be suppressed by \"action_unlock\"=1 - action argument \n") % (
                                lock_entry["filesrc"], lock_entry["fileslineno"], p, str(param), str(lock_entry[p])))
    # -----Action error callback

    def error(self, msg, exit):
        info = inspect.getframeinfo(inspect.currentframe().f_back)[0:3]
        self.error_bysrc(info[0], info[1], msg, exit)

    def error_bysrc(self, currfile, currline_no, msg, exit):
        if exit:
            htdte_logger.error(
                (" [%s:%d:%s:%d] %s") % (self.__flow_type__, self.__flow_num__, currfile, currline_no, msg))
        else:
            htdte_logger.error_str(
                (" [%s:%d:%s:%d] %s") % (self.__flow_type__, self.__flow_num__, currfile, currline_no, msg))

            # --------

    def actions_override(self):
        pass

    def post_verify(self):
        # ---Verifying that all IP's are connected withing flow , has been executed-----------
        status_pass = 1
        for segment in list(self.__ip_segments_exec_verify.keys()):
            for seg_method in list(self.__ip_segments_exec_verify[segment].keys()):
                for ipname in list(self.__ip_segments_exec_verify[segment][seg_method].keys()):
                    if (self.__ip_segments_[segment][seg_method][0]["ip"].is_ip_segment_enabled()):
                        for ipmethod in list(self.__ip_segments_exec_verify[segment][seg_method][ipname].keys()):
                            if (not self.__ip_segments_exec_verify[segment][seg_method][ipname][ipmethod]):
                                self.error(("IP:%s:%s() is connected to segment:%s%s() but never executed.\n") % (
                                    segment, seg_method, ipname, ipmethod), 0)
                                status_pass = 0
                                # -------Verify that all CMD parameters was mapped/accesed to actions.segments------
        for act in self.__per_action_arguments:
            for arg in list(self.__per_action_arguments[act].keys()):
                if (not self.__per_action_arguments[act][arg]["accessed"] and not re.match("^not_declared:", arg) and not re.match("disable_segment", arg) and not re.match("disable_action", arg)):
                    self.error((
                               "Specified argument [-%s:%s] in flow[%d]: \"%s\", while there is no such action/segment (%s) within the flow scope...\n") % (
                               act, arg, self.__flow_num__, self.__flow_type__, act), 0)
                    status_pass = 0
        # ------------------
        if (not status_pass):
            self.error("POST VERIFY FAIL", 1)

            # ---Store a Flow related parameters - there are 2 types of parameters : flow global parameters and action related
            # ---Flow global parameters are expected  , arguments are given in fomrta [-argname [value]],-action_name param1=val param2=val2,-action_name2 -param1=val -param2=val

    def set_flow_arguments(self, arguments, src):
        for argname in list(arguments.keys()):
            if (self.arguments.is_declared_argument(argname)):
                self.arguments.set_argument(argname, arguments[argname], "CMD")
            else:
                # ---Action argument appear in format -<ActionName>:<actionArgument> <value>
                actionNameRef = ""
                actionArgRef = ""
                if (re.match(r"^(declared|not_declared):([A-z0-9_\.\[\]]+):([A-z0-9_\.\[\:\]]+)$", argname)):
                    matchObj = re.match(r"^(declared|not_declared):([A-z0-9_\.\[\]]+):([A-z0-9_\.\[\:\]]+)$", argname)
                    actionNameRef = matchObj.groups()[1]
                    actionArgRef = ("%s:%s") % (matchObj.groups()[0], matchObj.groups()[2])
                elif (re.match(r"^([A-z0-9_.]+):([A-z0-9_\.\[\:\]]+)$", argname)):
                    matchObj = re.match(r"^([A-z0-9_\.\[\]]+):([A-z0-9_\.\[\:\]]+)$", argname)
                    actionNameRef = matchObj.groups()[0]
                    actionArgRef = matchObj.groups()[1]
                else:
                    htdte_logger.error((
                                       "Wrong action argument:\"%s\".Expected format -\"-[<declared|not_declared>:]<actionName>:<actionArgumentName> <argumentValue>\"") % (
                                       argname))
                if (actionNameRef not in list(self.__per_action_arguments.keys())):
                    self.__per_action_arguments[actionNameRef] = {}  # htd_argument_containter()
                self.__per_action_arguments[actionNameRef][actionArgRef] = {"val": arguments[argname], "src": src,
                                                                            "accessed": 0}
                # -------------------------------------

    def print_flow_arguments_help(self):
        htdte_logger.inform(
            "\n\n\nFLOW Arguments : [(<global_argument_name>=<val>)+] [<ActionName>:<ActionParameter>=<val>]")
        self.arguments.print_help()
        htdte_logger.inform(
            "\n\n\n----------------------------SEGMENT INTERFACE API--------------------------------------------------------------------")
        htdte_logger.inform("\n\n\nGENERAL (BASE) SEGMENT PARAMETERS:")
        #htdte_logger.inform( "self.declare_interface({HASH}), while HASH stucture is :")
        segment = htd_segment(self)
        segment.print_interface_arguments()
        # --For each all segment - > all inherited from htd_segment
        for user_segment in util_itersubclasses_names(htd_segment):
            if (user_segment not in ["htd_ip_segment", "htd_flow_segment"]):
                user_ip_segments = util_itersubclasses_names(htd_ip_segment)
                htdte_logger.inform(("\n\n\nUSER-DEFINED \"%s\" %sSEGMENT PARAMETERS:") % (
                    user_segment, ("IP ") if (user_segment in user_ip_segments) else ""))
                us = eval(user_segment)(self)
                us.print_interface_arguments()

    def print_flow_arguments(self):
        self.arguments.print_arguments(("Flow %d Parameters      ") % (self.__flow_num__))

        # ------------------------------------------------------------------------------
        # Action parameters override
        # --------------------------------------------------
        # def action_override(self,actionName,paramName,value,lsb=-1,msb=-1):
        #    info = inspect.getframeinfo(inspect.currentframe().f_back)[0:3]
        #    _path_tokens=info[0].split('/')
        #    location_file_str=_path_tokens[len(_path_tokens)-1]
        # 3    location_file_lineno= info[1]
        #    if(actionName not in self.__per_action_arguments):
        #	    self.__per_action_arguments[actionName]={}#htd_argument_containter()
        #    if(paramName not in self.__per_action_arguments[actionName][paramName].keys()):
        #       self.__per_action_arguments[actionName][paramName]={"val":[(value,src)],"accessed":0}
        #    self.__per_action_arguments[actionName].overrideSingleArgument(paramName,value,("%s:%s")%(location_file_str,location_file_lineno),lsb,msb)
        # ------------Main Action Exec Callback-------------------------------------------------------------------
        # Receive string argument in format : aname=<actionName>,atype=<action_class_type>,<param>=val,......
        #   aname- Unique action name string
        #   atype- Name of action class
        # --------------------------------------------------------------------------------------------------------

    def exec_action(self, params, atype="none", location_file_str="none", location_file_lineno=0, calling_action="", override_arguments=None, override_arguments_description=""):
        if (location_file_str == "none"):
            info = inspect.getframeinfo(inspect.currentframe().f_back)[0:3]
            location_file_lineno = info[1]
            _path_tokens = info[0].split('/')
            location_file_str = _path_tokens[len(_path_tokens) - 1]
        # --------------
        # ---Create Automatic name of action if not prvided in parameters : <TYPE>_<MODULE>[_<index>]
        if (("actionName" not in params) and (calling_action == "")):
            self.error_bysrc(location_file_str, location_file_lineno,
                             "Illegal action call argument - Missing action type argument -\"actionName\".", 1)
        actionName = params["actionName"] if (calling_action == "") else ("internal_%s") % (calling_action)
        # ------
        if (self.__current_segment is not None and not self.__current_segment.is_ipsegment() and self.cluster_model_mode):
            if (not self.silent_mode):
                htdte_logger.inform(
                    "WARNING!!! **************************************************************************************************!!!WARNING")
                htdte_logger.inform((
                                    "WARNING!!!   CLUSTER MODE  : Action \"%s\" (%s:%d) is not executed (on cluster model)                        !!!WARNING") % (
                                    actionName, location_file_str, location_file_lineno))
                htdte_logger.inform(
                    "WARNING!!! **************************************************************************************************!!!WARNING")
            return None
        # ---------------
        if (atype != "none"):
            params["actionType"] = atype
        self.exec_action_obj(location_file_str, location_file_lineno, params, calling_action, override_arguments, override_arguments_description)
        # ------------------------------------------------------------------------------------------

    def print_action_header(self, actionName, actionType, arguments, PhaseName="", calling_location=""):

        param_str = ("(actionName=\"%s\"") % (actionName)
        for p in sorted(arguments.keys()):
            param_str += (",\n\t\t%s=\"%s\"") % (p, str(arguments[p]))
        param_str += ")"
        htdPlayer.hpl_to_dut_interface.print_header(
            ("\n\nExecuting action \n\t\texec_%s_action%s") % (actionType.lower(), param_str))

        htdte_logger.inform(("\n Start Action %s[%d]%s->%s %s") % (self.__flow_type__, self.__flow_num__,
                                                                   ("->%s%s") % (self.__current_segment.name, PhaseName) if(self.__current_segment is not None) else "", actionName, calling_location), 2)

        # -----------------------------------------------------------------------------------------

    def exec_action_obj(self, location_file_str, location_file_lineno, arguments, calling_action="", override_arguments=None, override_arguments_description=""):

        actionParams = {}
        PhaseName = ""
        # ----------------------
        if (not isinstance(arguments, dict)):
            self.error_bysrc(location_file_str, location_file_lineno,
                             "Illegal action call argument type - expected \"DICT\" type.", 1)
        # -----------
        if ("actionType" not in arguments):
            self.error_bysrc(location_file_str, location_file_lineno,
                             "Illegal action call argument - Missing action type argument -\"actionType\".", 1)
            # ---Create Automatic name of action if not prvided in parameters : <TYPE>_<MODULE>[_<index>]
        if (("actionName" not in arguments) and (calling_action == "")):
            self.error_bysrc(location_file_str, location_file_lineno,
                             "Illegal action call argument - Missing action type argument -\"actionName\".", 1)
            # -------
        actionName = arguments["actionName"] if (calling_action == "") else ("internal_%s") % (calling_action)
        actionType = arguments["actionType"]
        if ("actionName" in list(arguments.keys())):
            del arguments["actionName"]
        del arguments["actionType"]
        # ------------------------------------------------------
        action_classes = []
        for cls in util_itersubclasses(htd_base_action):
            action_classes.append(cls.__name__)
        if (actionType in action_classes):
            action = eval(actionType)(actionName, location_file_str, location_file_lineno, self.__current_obj_, (calling_action != ""))
            self.__current_action = action
            htdPlayer.set_current_action(action)
        else:
            self.error_bysrc(location_file_str, location_file_lineno, ("Illegal action class name-%s.") % (actionType), 0)
            self__current_action.error_bysrc(location_file_str, location_file_lineno,
                                             "Pls. check that your htd_actions_library_top.py  importing the actions definitions and contain this type of action.",
                                             0)
            msg = "Available action classes are : \
        "
            for cls in action_classes:
                msg = ("{0} ,{1}").format(msg, cls)
            self.error_bysrc(location_file_str, location_file_lineno, msg, 0)
            self.error_bysrc(location_file_str, location_file_lineno, "***********CMD ERROR****************", 1)
            # -----Action source parameters---------

        read_type = False
        if ("read_type" in list(arguments.keys()) and int(arguments["read_type"]) > 0):
            read_type = True
        # --------Save input arguments to internal arguments container---
        for glob_arg in self.arguments.declared_keys():
            if (glob_arg in action.arguments.declared_keys()):
                if (self.arguments.argument_is_assigned(glob_arg)):
                    action.arguments.set_argument(glob_arg, self.arguments.get_argument(glob_arg), "CMD")
        # -------------------
        for param in arguments:
            action.arguments.set_argument(param, arguments[param],
                                          ("%s:%d") % (location_file_str, location_file_lineno), read_type)
        # --------Per action parameters inherited from flow/manager cmd----
        if (actionName in list(self.__per_action_arguments.keys())):
            # action.arguments.overrideByOtherArgumentContainer(self.__per_action_arguments[actionName])
            for arg in list(self.__per_action_arguments[actionName].keys()):
                action.arguments.set_argument(arg, self.__per_action_arguments[actionName][arg][
                                              "val"], self.__per_action_arguments[actionName][arg]["src"], read_type)
                self.__per_action_arguments[actionName][arg]["accessed"] = 1
        # -----Action extension override
        if(override_arguments is not None):
            action.arguments.set_argument("description", ("%s:%s") % (action.arguments.get_argument("description"), override_arguments_description))
            for arg in override_arguments.get_override_parameters():
                if(override_arguments.is_delete_arguments_override(arg)):
                    action.arguments.delete_argument(arg, override_arguments.get_source())
                elif(override_arguments.get_replace_argument_override(arg) is not None):
                    action.arguments.change_argument_name(arg, override_arguments.get_replace_argument_override(arg), override_arguments.get_source())
                else:
                    action.arguments.set_argument(arg, override_arguments.get_assignment_override(arg), override_arguments.get_source(), read_type)
        # -------------------------
        if (self.__stop_flow):
            htdte_logger.inform(("!!!stop_flow detected - ignoring action - \"%s\"") % (
                actionName if (calling_action == "") else ("internal_%s") % (calling_action)))
            return None
            # ----------------------------------------------
        action.set_calling_action(calling_action)
        # ---------------------------------
        action.arguments_override()
        # ----------------------------------------------
        if (action.arguments.get_argument("stop_flow")):
            self.__stop_flow = True
        # --------------------------------------------
        if (action.arguments.get_argument("disable_action")):
            htdte_logger.inform(("***********************Action %s disabled by %s") % (
                actionName, action.arguments.get_argument_src("disable_action")))
            if (len(action.arguments.get_argument("post_module")) > 1):
                post_module_path = action.arguments.get_argument("post_module")
                status, mname, py_mod = util_dynamic_load_external_module(post_module_path)
                if (not status):
                    htdte_logger.error((
                                       " Not existent \"post_module\" module - %s given in command line : \"-<action>:post_module\" ") % (
                                       post_module_path))
                util_execute_all_flow_in_module(self, py_mod, mname)
            return
        # ---------------------------
        if (evaluate_constrain_condition(action.arguments.get_argument("constraint"), ("%s:%d") % (action.get_action_call_file(), action.get_action_call_lineno()))):
            if (self.arguments.get_argument("disable_readout") and action.arguments.get_argument("read_type")):
                htdte_logger.inform((" Action %s gated by flow \"disable_readout\" argument... ") % (actionName), 1)
            else:
                PhaseName = ("[phase:%s]") % (self.phase_name) if(self.__current_segment is not None and self.phase_name != "") else ""
                calling_location = ("(%s:%d)") % (action.get_action_call_file(), action.get_action_call_lineno())
                if (self.__verification_mode and calling_action == ""):
                    htdte_logger.inform(("\n Runtime Verifying Action %s[%d]%s->%s %s ") % (self.__flow_type__, self.__flow_num__,
                                                                                            ("->%s%s") % (self.__current_segment.name,
                                                                                                          PhaseName) if(self.__current_segment is not None) else "",
                                                                                            actionName, calling_location))
                    #htdPlayer.hpl_to_dut_interface.print_header(("\n Runtime Verifying Action %s[%d]->%s ")%(self.__flow_type__,self.__flow_num__,actionName))
                # ----------------------
                action.verify_action_arguments()
                action.verify_obligatory_arguments()
                if (self.__verification_mode and calling_action == ""):
                    htdPlayer.set_silent_mode()
                if ((not self.arguments.get_argument("silent_mode")) and (not self.silent_mode)):
                    if (not action.is_inner_action() and not action.arguments.get_argument("dummy") and not action.arguments.get_argument("silent_mode") and not self.__verification_mode):
                        self.print_action_header(actionName, actionType, action.arguments.get_arguments_table(), PhaseName, calling_location)
                        action.print_action_arguments()
                    action.pre_run()
                    if (not action.arguments.get_argument("dummy")):
                        action.set_result(action.run())
                        action.post_run()
                    else:
                        htdte_logger.inform(("!!!Action %s is running in dummy mode.") % (actionName))
                        action.post_run()
                        if (self.__verification_mode and calling_action == ""):
                            htdPlayer.unset_silent_mode()
                        return action.get_result()
                    if (calling_action == "" and not self.__verification_mode):
                        if (not action.arguments.get_argument("action_unlock")):
                            self.evaluate_action_in_blacklist(actionType, action)
                        if(action.arguments.get_argument("action_lock") and (not action.arguments.get_argument("read_type"))):
                            htd_history_mgr.blacklist_capture(action, action.get_action_indexing(), {}, location_file_str, location_file_lineno)
                        htdte_logger.inform((" End Action %s \n") % (actionName), 0)
                        htdte_logger.inform((" -----------------------------------------------------\n"), 0)
        else:
            htdte_logger.inform((" Action %s gated by constraint - \'%s\'... ") % (
                actionName, action.arguments.get_argument("constraint")), 1)
            # ----------------	-----------------------------
        if (action.arguments.get_argument("check")):
            action.verify_action()
        if (action.arguments.get_argument("debug_readback")):
            if (not self.arguments.get_argument("silent_mode") and (not self.silent_mode)):
                action.debug_readback()
        # ----------------------------------------------
        if (len(action.arguments.get_argument("post_module")) > 1):
            post_module_path = action.arguments.get_argument("post_module")
            status, mname, py_mod = util_dynamic_load_external_module(post_module_path)
            if (not status):
                htdte_logger.error(
                    (" Not existent \"post_module\" module - %s given in command line : \"-<action>:post_module\" ") % (
                        post_module_path))
            util_execute_all_flow_in_module(self, py_mod, mname)
        # ----------------------
        if (self.__verification_mode and calling_action == ""):
            htdPlayer.unset_silent_mode()
        # --Saving action object in sequence history
        if(not htd_history_mgr.parametric_has("ActionResults", [actionName, actionType])):
                # ---Zeroing all file members: - could not bee pickled
            copy_action = deepcopy(action)
            for x in dir(copy_action):
                if(isinstance(getattr(copy_action, x), io.IOBase)):
                    setattr(copy_action, x, None)
            htd_history_mgr.parametric_capture("ActionResults", [actionName, actionType, "obj"], copy_action)
            # ---------------
            htd_history_mgr.parametric_capture("ActionResults", [actionName, actionType, "src"],
                                               ("%s:%s") % (location_file_str, location_file_lineno))
        return action.get_result()
    # -----------------------------------
    # Get action assigned argument by name and type of action
    # ----------------------------------

    def get_previously_running_action_argument_val(self, actionName, actionType, argumentName):
        if(not htd_history_mgr.parametric_has("ActionResults", [actionName])):
            htdte_logger.error((" Trying to retrieve not existent actionName - \"%s\" from action sequence history.  ") % (actionName))
        if(not htd_history_mgr.parametric_has("ActionResults", [actionName, actionType])):
            htdte_logger.error((" Trying to retrieve not existent %s:actionType - \"%s\" from action sequence history.  ") % (actionName, actionType))
        if(not htd_history_mgr.parametric_get("ActionResults", [actionName, actionType, "obj"]).has_register_assignment_by_field(argumentName)):
            htdte_logger.error((" Trying to retrieve not existent %s:%s:<ParametricField> - \"%s\" from action sequence history.  ") %
                               (actionName, actionType, argumentName))
        return htd_history_mgr.parametric_get("ActionResults", [actionName, actionType, "obj"]).get_register_assignment_by_field(argumentName)

    def has_previously_running_action_argument(self, actionName, actionType, argumentName):
        if(not htd_history_mgr.parametric_has("ActionResults", [actionName])):
            return False
        if(not htd_history_mgr.parametric_has("ActionResults", [actionName, actionType])):
            return False
        if(htd_history_mgr.parametric_get("ActionResults", [actionName, actionType, "obj"]).has_register_assignment_by_field(argumentName)):
            return False
        return True

    def get_previously_running_action_fields(self, actionName, actionType):
        if(not htd_history_mgr.parametric_has("ActionResults", [actionName])):
            htdte_logger.error((" Trying to retrieve not existent actionName - \"%s\" from action sequence history.  ") % (actionName))
        if(not htd_history_mgr.parametric_has("ActionResults", [actionName, actionType])):
            htdte_logger.error((" Trying to retrieve not existent %s:actionType - \"%s\" from action sequence history.  ") % (actionName, actionType))
        return htd_history_mgr.parametric_get("ActionResults", [actionName, actionType, "obj"]).get_register_assignment()

    # -----------------------------------
    # Add new segment api
    # ----------------------------------
    def exec_segment(self, arguments):
        info = inspect.getframeinfo(inspect.currentframe().f_back)[0:3]
        location_file_str = info[0]
        location_file_lineno = info[1]
        if (self.__stop_flow):
            htdte_logger.inform(("!!!stop_flow detected - ignoring segment - \"%s\"") % (arguments["segment"]))
            return
            # ----------------------
        if (not isinstance(arguments, dict)):
            htdte_logger.error(
                ("Wrong argument type detected in calling segment at %s:%d , Expected dictionary argument type....") % (
                    location_file_str, location_fileno))
        if ("segment" not in list(arguments.keys())):
            htdte_logger.error("Missing segment name parameter - \"segment\":<segment name>. ...")
        if ("description" not in list(arguments.keys())):
            htdte_logger.error(
                "Missing segment description usage parameter - \"description\":<description string>. ...")
        segmentName = arguments["segment"]
        del (arguments["segment"])
        if ("SEGMENTS" not in list(CFG.keys())):
            htdte_logger.error(
                "Missing Segment  revision table  CFG[\"SEGMENTS\"].Pls provide the configuration in TE_cfg.xml or command line ...")
            # for segment in util_itersubclasses_names(htd_segment):
            #	 ignore_l=["htd_ip_segment","htd_flow_segment"]
        if (segmentName not in list(CFG["SEGMENTS"].keys())):
            htdte_logger.error((
                "Missing Segment - \"%s\" revision definition in CFG[\"SEGMENTS\"][\"%s\"].Pls provide the configuration in TE_cfg.xml or command line ...") % (
                segmentName, segmentName))
        if ("rev" not in CFG["SEGMENTS"][segmentName]):
            htdte_logger.error((
                               "Missing Segment \"rev\" property in TE_cfg.xml : <CFG category=\"SEGMENTS\"> -> <Var key=\"%s\" rev=<revString>  ...") % (
                               segmentName))
        if ("phase" not in CFG["SEGMENTS"][segmentName]):
            htdte_logger.error((
                               "Missing Segment \"phase\" property in TE_cfg.xml : <CFG category=\"SEGMENTS\"> -> <Var key=\"%s\" rev=<revString>  ...") % (
                               segmentName))
            # --------------------------
        # try:
        final_segment_name = htd_segment_get_full_name(segmentName, CFG["SEGMENTS"][segmentName]["rev"])
        if (final_segment_name not in util_itersubclasses_names(
                htd_flow_segment) and final_segment_name not in util_itersubclasses_names(htd_ip_segment)):
            htdte_logger.inform((
                                "The assigned segment definition class - \"%s\" is not loaded/recognized. Pls. check tecfg:CFG[\"SEGMENTS\"][\"%s\"][\"module\"]=\"%s\" definition.") % (
                                final_segment_name, segmentName, CFG["SEGMENTS"][segmentName]["module"]))
        # --------------------
        segment = eval(final_segment_name)(self.__current_obj_, ("%s:%d") % (location_file_str, location_file_lineno))
        self.set_current_segment(segment)
        # --------------------
        if (not segment.is_ipsegment() and self.cluster_model_mode):
            if (not self.silent_mode):
                htdte_logger.inform(
                    "WARNING!!! **************************************************************************************************!!!WARNING")
                htdte_logger.inform((
                                    "WARNING!!!   CLUSTER MODE  : Segment \"%s\" (%s:%d) is not executed (on cluster model)                       !!!WARNING") % (
                                    final_segment_name, location_file_str, location_file_lineno))
                htdte_logger.inform(
                    "WARNING!!! **************************************************************************************************!!!WARNING")
            return
            # ----------
        # --Set segment arguments---
        for arg in arguments:
            segment.arguments.set_argument(arg, arguments[arg],
                                           ("SRC:%s:%d") % (location_file_str, location_file_lineno))
        segment_arguments = arguments
        # --------Save input arguments to internal segment container---
        for glob_arg in self.arguments.declared_keys():
            if (glob_arg in segment.arguments.declared_keys()):
                if (self.arguments.argument_is_assigned(glob_arg)):
                    segment.arguments.set_argument(glob_arg, self.arguments.get_argument(glob_arg), "CMD")
        # --------Per action parameters inherited from flow/manager cmd----
        if (segmentName in list(self.__per_action_arguments.keys())):
            # segment_arguments.overrideByOtherArgumentContainer(self.__per_action_arguments[segmentName])
            for arg in list(self.__per_action_arguments[segmentName].keys()):
                segment.arguments.set_argument(arg, self.__per_action_arguments[segmentName][arg]["val"],
                                               self.__per_action_arguments[segmentName][arg]["src"])
                self.__per_action_arguments[segmentName][arg]["accessed"] = 1

        # ---------------------------------------
        segment.verify_obligatory_arguments()
        # dis_exists,dis_value,dis_src=segment_arguments.get_action_argument_value("disable_segment")
        if (segment.arguments.get_argument("disable_segment")):
            self.clear_names()
            htdte_logger.inform(("***********************Segment %s disabled by %s") %
                                (segmentName, segment.arguments.get_argument_src("disable_segment")), 0, 0, "")
            post_module_path = segment.arguments.get_argument("post_module")
            if (post_module_path != ""):
                status, mname, py_mod = util_dynamic_load_external_module(post_module_path)
                if (not status):
                    htdte_logger.error((
                                       " Not existent \"post_module\" module - %s given in command line : \"<segment>:post_module\" ") % (
                                       post_module))
                util_execute_all_flow_in_module(self, py_mod, mname)
            return
        # --Check if segment is ip type and disabled--
        if (segment.is_ipsegment()):
            if ("IPENABLE" in list(CFG.keys())):
                if (segment.get_ip_name() in list(CFG["IPENABLE"].keys())):
                    if (not isinstance(CFG["IPENABLE"][segment.get_ip_name()], dict)):
                        if (CFG["IPENABLE"][segment.get_ip_name()] in [0, False, "False", "FALSE"]):
                            htdte_logger.inform((" IP:%s is masked , disabling segment:%s.. ") % (
                                segment.get_ip_name(), final_segment_name))
                            self.clear_names()
                            return
                    elif (isinstance(CFG["IPENABLE"][segment.get_ip_name()], dict) and "enable" in list(CFG["IPENABLE"][
                        segment.get_ip_name()].keys()) and CFG["IPENABLE"][segment.get_ip_name()]["enable"] in [0, False,
                                                                                                               "False",
                                                                                                               "FALSE"]):
                        htdte_logger.inform((" IP:%s is masked , disabling segment:%s.. ") % (
                            segment.get_ip_name(), final_segment_name))
                        self.clear_names()
                        return
        # -------------------
        if ("constraint" not in arguments or evaluate_constrain_condition(segment.arguments.get_argument("constraint"),
                                                                          ("%s:%d") % (
                                                                          location_file_str, location_file_lineno))):
            if (not self.__verification_mode):
                self.add_pattern_indicators()
                htdte_logger.inform(("*********Executing:Segment:%s - (%s)*******") % (
                    final_segment_name, segment.arguments.get_argument("description")), 0, 0, "SEGMENT Inform")
                segment.print_segment_arguments()
                htdte_logger.inform(("Start Segment %s") % (segmentName), 1, 0, "SEGMENT Inform")
                if(segment.is_ipsegment() and self.cluster_model_mode and len(self.__ip_segment_execution_tracker) == 0):
                    htdte_logger.inform(("*********Executing IP Segment Cluster reset handler - %s:cluster_reset().. ") %
                                        (final_segment_name), 0, 0, "SEGMENT Inform")
                    func_l = util_get_class_method_names(segment)
                    if("cluster_model_reset" in func_l):
                        htdte_logger.inform(("Cluster Reset Method found : calling %s:cluster_reset().. ") % (final_segment_name), 0, 0, "")
                        segment.cluster_model_reset()
                    elif(len(self.__ip_segment_execution_tracker) == 0):
                        htdte_logger.error(("Cluster Reset Method not found in first IP(%s) segment in execution sequence %s:cluster_model_reset() - found the following functionals:%s ") % (
                            segment.get_ip_name(), final_segment_name, ','.join(func_l)))

            segment.execute_segment()
            # --------------------------------------------------------------------------------------------------------------------------------
            if (self.arguments.get_argument("debug_readback") or segment.arguments.get_argument("debug_readback")):
                segment.debug_readback()
            # -----------------------------------------------------------------------------------------------------------------------------------
            if (not self.__verification_mode):
                htdte_logger.inform(
                    ("***********************End of segment: %s****************************\n") % (segmentName), 0, 0,
                    "SEGMENT Inform")
                htdte_logger.inform(("End of segment: %s\n") % (segmentName), 1, 0, "SEGMENT Inform")
            if (not self.__verification_mode and "post_segment_delay" in list(CFG["TE"].keys()) and CFG["TE"]["post_segment_delay"] > 0):
                htdte_logger.inform("applying a post delay of %d to segment %s" % (CFG["TE"]["post_segment_delay"], segmentName))
                htdPlayer.hpl_to_dut_interface.wait_clock_num(CFG["TE"]["post_segment_delay"], CFG["HTD_Clocks"]["default"])
        else:
            htdte_logger.inform((" Segment %s (%s) gated by constraint- \"%s\"... ") % (
                segmentName, (("%s:%d") % (location_file_str, location_file_lineno)),
                segment.arguments.get_argument("constraint")), 1)
            # ------------------------------
        post_module_path = segment.arguments.get_argument("post_module")
        if (post_module_path != ""):
            status, mname, py_mod = util_dynamic_load_external_module(post_module_path)
            if (not status):
                htdte_logger.error(
                    (" Not existent \"post_module\" module - %s given in command line : \"<segment>:post_module\" ") % (
                        post_module))
            util_execute_all_flow_in_module(self, py_mod, mname)
        # --------------------------
        if (segment.arguments.get_argument("stop_flow")):
            self.__current_flow.__stop_flow = True
        # ------Clear segment tracker-----------------------------
        self.set_current_segment(None)
        if (not self.__verification_mode and segment.is_ipsegment()):
            self.__ip_segment_execution_tracker.append(segment.get_ip_name())
        segment.sequence_extend_check_on_finish()

    def add_pattern_indicators(self):
        pattern_indicators_enabled = 0
        if ("ActionPatternIndicators" in list(CFG.keys())):
            if ("enabled" in CFG["ActionPatternIndicators"] and CFG["ActionPatternIndicators"]["enabled"] == 1):
                pattern_indicators_enabled = 1

            if (pattern_indicators_enabled == 1):
                if ("pre_segment_comment" in CFG["ActionPatternIndicators"]):
                    htdPlayer.hpl_to_dut_interface.add_comment(CFG["ActionPatternIndicators"]["pre_segment_comment"])
                if ("pre_segment_label" in CFG["ActionPatternIndicators"]):
                    htdPlayer.hpl_to_dut_interface.label(CFG["ActionPatternIndicators"]["pre_segment_label"])

    # -----------------------------------------
    #
    # -----------------------------------------
    def ip_activate(self, ip_name, ena):
        info = inspect.getframeinfo(inspect.currentframe().f_back)[0:3]
        location_file_str = info[0]
        location_file_lineno = info[1]
        # ----------------------
        for segment in self.__ip_segments_:
            for method in list(self.__ip_segments_[segment].keys()):
                for entry in self.__ip_segments_[segment][method]:
                    if (entry["ip"].get_ip_name() == ip_name):
                        if (((isinstance(ena, str)) and (ena == "TRUE" or ena == "true")) or (
                                (isinstance(ena, int)) and (ena > 0))):
                            self.inform_bysrc(("--Activating IP:%s linked to segment:%s:%s() ...") % (
                                entry["ip"].get_ip_name(), segment, method), location_file_lineno, location_file_str)
                            entry["ip"].enable_ip_segment()
                            # --------------------------------------------------

    #
    # --------------------------------------------------
    def flow_init(self):
        currently_running_flow = self
        # -----Connecting dynamic flow functions ---
        per_action_type_callbacks = {}
        for acls in util_itersubclasses(htd_base_action):
            act_type = acls.__name__.upper()
            per_action_type_callbacks[acls.__name__.upper()] = (
                lambda x, params, atype=act_type: self.exec_action(params, atype,
                                                                   inspect.getframeinfo(inspect.currentframe().f_back)[0],
                                                                   inspect.getframeinfo(inspect.currentframe().f_back)[1]))
            # ----------
        for acls in util_itersubclasses(htd_base_action):
            for fcls in util_itersubclasses(htd_base_flow):
                setattr(fcls, ('exec_%s_action') % (acls.__name__.lower()),
                        per_action_type_callbacks[acls.__name__.upper()])
            # for scls in util_itersubclasses(htd_segment):
            #    #self.inform( ("--Mapping \"%s\"  action methods to \"%s\"...")%(('exec_%s_action')%(acls.__name__),scls.__name__))
            #    setattr(scls, ('exec_%s_action') % (acls.__name__.lower()),
            #            per_action_type_callbacks[acls.__name__.upper()])
                #   #setattr(module,('%s_action')%(acls.__name__.lower()), per_action_type_callbacks_glob[acls.__name__.upper()])
                #   #??eval(("%s_action")%(acls.__name__.lower()))=per_action_type_callbacks_glob[acls.__name__.upper()]
            #msg=("{0} ,{1}").format(msg,cls.__name__)

    # -----------------------------------------
    # Automatic callback for future extension
    # -----------------------------------------
    def pre_flow_run_place_holder(self):
        pass

    def post_flow_run_place_holder(self):
        pass

    def pre_flow_run(self):
        currently_running_flow = self
        htdPlayer.hplClockMgr.train_clocks()
        self.pre_flow_run_place_holder()
        if (self.arguments.get_argument("pre_alignment")):
            if ("sync_modulo_cycles" not in CFG["TE"]):
                self.error((
                           "Missing  CFG[\"TE\"][\"sync_modulo_cycles\"] -  modulo cycles number for alignment at between actions/flows") % (),
                           1)
            if ("sync_modulo_clock" not in CFG["TE"]):
                self.error((
                           "Missing  CFG[\"TE\"][\"sync_modulo_clock\"] -  clock name referencied for alignment at between actions/flows") % (),
                           1)
            htdPlayer.sync_to_clock_modulo(CFG["TE"]["sync_modulo_clock"], int(CFG["TE"]["sync_modulo_cycles"]))
            # ------------------------------------------------------
            if (self.arguments.get_argument("silent_mode")):
                htdPlayer.set_silent_mode()
            else:
                htdPlayer.unset_silent_mode()

        if (self.arguments.get_argument("stf_gid_track")):
            self.arguments.set_argument("stf_gid_track", self.init_stf_gid_track(15, 1, self.select_mode))
            # self.stf_gid_track = self.init_stf_gid_track(15, 1, self.select_mode)


    def post_flow_run(self):
        self.post_flow_run_place_holder()
        if (self.arguments.get_argument("post_alignment")):
            if ("sync_modulo_cycles" not in CFG["TE"]):
                self.error((
                           "Missing  CFG[\"TE\"][\"sync_modulo_cycles\"] -  modulo cycles number for alignment at between actions/flows") % (),
                           1)
            if ("sync_modulo_clock" not in CFG["TE"]):
                self.error((
                           "Missing  CFG[\"TE\"][\"sync_modulo_clock\"] -  clock name referencied for alignment at between actions/flows") % (),
                           1)
            htdPlayer.sync_to_clock_modulo(CFG["TE"]["sync_modulo_clock"], int(CFG["TE"]["sync_modulo_cycles"]))
        if("post_flow_delay" in CFG["TE"] and CFG["TE"]["post_flow_delay"] > 0):
            htdPlayer.wait_clock_num(int(CFG["TE"]["post_flow_delay"]), CFG["HTD_Clocks"]["default"])

    def flow_run(self):
        pass

    # ----------------------------------------------------------------------------------------
    # Default callback used to override an actions per each flow type (in inheretence tree
    # ---------------------------------------------------------------------------------------
    def flow_override(self):
        pass

    # ---------------------------------------------------------------------------------------
    # load external segment function
    # ---------------------------------------------------------------------------------------
    def load_external_seg(self, arguments):
                # Sanity check inputs here
        if ("seg_name" not in list(arguments.keys())):
            htdte_logger.error("Missing segment name parameter in load_external_seg function. please provide a segment name")
        if ("rev" not in list(arguments.keys())):
            htdte_logger.error("Missing rev name parameter in load_external_seg function. please provide a rev")
        if ("Phase" not in list(arguments.keys())):
            htdte_logger.error("Missing phase parameter load_external_seg function. please provide a phase")
        if ("filename" not in list(arguments.keys())):
            htdte_logger.error("Missing filename parameter load_external_seg function. please provide a valid path to a module containing your segment")

        filename = arguments["filename"]
        seg_name = arguments["seg_name"]
        rev = arguments["rev"]
        phase = arguments["Phase"]

        # check to see if module file exists
        if(not os.path.exists(filename)):
            htdte_logger.error(("the path %s does not exist") % (filename))

        # check if module file is a .py file
        if re.search(".py$", filename) is None:
            htdte_logger.error(("%s does not have a python extension") % (filename))

        if (seg_name in list(CFG["SEGMENTS"].keys())):
            htdte_logger.error(("Segment - \"%s\" revision definition in CFG[\"SEGMENTS\"][\"%s\"] Already exists, cannot override existing segment ...") % (
                seg_name, seg_name))

        CFG["SEGMENTS"][seg_name] = {}
        CFG["SEGMENTS"][seg_name]["rev"] = rev
        CFG["SEGMENTS"][seg_name]["phase"] = phase
        CFG["SEGMENTS"][seg_name]["module"] = filename

        final_segment_name = htd_segment_get_full_name(seg_name, CFG["SEGMENTS"][seg_name]["rev"])

        status, mname, py_mod = util_dynamic_load_external_module(filename)
        if (not status):
            htdte_logger.error((" Can't load segment module - %s ") % (filename))
        exec((("from %s import %s") % (mname, final_segment_name)), globals())
        htdte_logger.inform(("Successfully loaded segment module=%s") % (filename))
