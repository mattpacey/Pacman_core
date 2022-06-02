import re
import pkgutil
from htd_utilities import *
from htd_collaterals import *
from htd_te_shared import *
from htd_basic_action import *
from htd_basic_segment import *
from htd_basic_flow import *
import collections

# -------------------
# internal functions
# -------------------


def htd_segment_naming_convention_verify(segment_name):
    if (not re.match(r"^([A-z0-9_]+)_Stage(\d+)_Rev([A-z0-9\.]+)$", segment_name)):
        htdte_logger.error((
                           "Illegal sequence name \"%s\"- not aligned with naming convention format <TargetDut>_Stage<Num>_Rev<RevString>  ...") % (
                           segment_name))


def htd_segment_naming_disassembly(segment_name):
    m = re.match(r"^([A-z0-9_]+)_Stage(\d+)_Rev([A-z0-9\.]+)$", segment_name)
    if (not m and os.environ.get('HTD_TE_HELP_MODE') == "1"):
        return (segment_name, "0", "0")
    if (not m):
        htdte_logger.error((
                           "Illegal sequence name \"%s\"- not aligned with naming convention format <TargetDut>_Stage<Num>_Rev<RevString>  ...") % (
                           segment_name))
    return (m.groups()[0], m.groups()[1], m.groups()[2])


def htd_segment_get_full_name(partial_segment_name, rev):
    return ("%s_Rev%s") % (partial_segment_name, rev)
# ------------------------------------------
# class htd_segment_action_override_container
# --------------------------------------------


class htd_segment_action_override(object):

    def __init__(self, override_src):
        self.__value = None
        self.__argname = ""
        self.__overrides = {}
        self.__container = None
        self.__src = override_src

    def add(self, container, argname, value, source):
        self.__container = container
        if(argname not in list(self.__overrides.keys())):
            self.__overrides[argname] = {}
        self.__overrides[argname]["val"] = value
        self.__overrides[argname]["src"] = source

    def get_source(self): return self.__src

    def get_override_parameters(self): return list(self.__overrides.keys())

    def is_delete_arguments_override(self, argname):
        if(argname not in list(self.__overrides.keys())):
            htdte_logger.error(("Trying to access to not existent action argument (%s) override .. ") % (argname))
        return True if(self.__overrides[argname]["val"] == "__delete__") else False

    def get_replace_argument_override(self, argname):
        if(argname not in list(self.__overrides.keys())):
            htdte_logger.error(("Trying to access to not existent action argument (%s) override .. ") % (argname))
        overrides = self.__overrides[argname]["val"]
        if(not isinstance(self.__overrides[argname]["val"], str)):
            return None
        m = re.search(r"__rename__:([A-z0-9_\.]+)", self.__overrides[argname]["val"])
        if(m):
            m = re.search(r"__rename__:([A-z0-9_\.]+)", self.__overrides[argname]["val"])
            return m.groups()[0]
        else:
            return None

    def get_assignment_override(self, argname):
        if(argname not in list(self.__overrides.keys())):
            htdte_logger.error(("Trying to access to not existent action argument value (%s) override .. ") % (argname))
        return self.__overrides[argname]["val"]


class htd_segment_action_override_container(object):

    def __init__(self):
        self.__per_action_arguments = {}

    def add_action_override(self, actionName, override_params, loc_string):
        if(not isinstance(override_params, dict)):
            htdte_logger.error(
                ("Improper action extension parameters argument type received : Expected dictionary type , while received - %s .. ") % (str(type(override_params))))
        if("description" not in list(override_params.keys())):
            htdte_logger.error(("Missing \"description\" obligatory argument for action extension parameters list ..(Given arguments are: %s) ") % (
                str(list(override_params.keys()))))
        # --------------
        if(actionName not in list(self.__per_action_arguments.keys())):
            self.__per_action_arguments[actionName] = {}
            self.__per_action_arguments[actionName]["accessed"] = 0
            self.__per_action_arguments[actionName]["description"] = override_params["description"]
            self.__per_action_arguments[actionName]["obj"] = htd_segment_action_override(loc_string)
        for arg in list(override_params.keys()):
            if(arg != "description"):
                self.__per_action_arguments[actionName]["obj"].add(self, arg, override_params[arg], loc_string)

    def get_action_extend_params(self, actionName):
        if(actionName in list(self.__per_action_arguments.keys())):
            self.__per_action_arguments[actionName]["accessed"] = 1
            return self.__per_action_arguments[actionName]["obj"]
        else:
            return None

    def get_action_extend_description(self, actionName):
        if(actionName in list(self.__per_action_arguments.keys())):
            return self.__per_action_arguments[actionName]["description"]
        else:
            return ""

    def verify_all_overrides_accessed(self):
        not_accessed_actions = [(x, x["src"]) for x in list(self.__per_action_arguments.keys()) if(self.__per_action_arguments[x]["accessed"] == 0)]
        if(len(not_accessed_actions) > 0):
            htdte_logger.error(("Not all actions assigned for override/extend are consumed..:%s ") % (str(not_accessed_actions)))


# --------------------------------
# class htd_segment
# --------------------------------
class htd_segment(object):

    def __init__(self, current_flow, location_str=""):
        # self.name=segment_name
        self.checker = 1
        self.__current_flow = current_flow
        self.rev_tag = ""
        self.phase_name = ""
        self.__per_action_arguments = htd_segment_action_override_container()
        # self.__stop_segment=False
        self.__sequence_extend_per_action = {}
        self.arguments = htd_argument_containter(HTD_ARGUMENTS_DECLARED_ONLY)  # data container storing the flow declared parameters
        self.arguments.declare_arg("segment", "segment name given in flow sequence execution handler..", "string", 1)
        self.arguments.declare_arg("description", "Segment usage mode description by flow integrator..", "string", 1)
        self.arguments.declare_arg("disable_segment", "Disable segment option..", "bool", 0, 0)
        self.arguments.declare_arg(
            "debug_readback", "Debugability readback activity to be matched on DUT option, enforced on all actions/segments..", "bool", 0)
        self.arguments.declare_arg("check", "Enable/Disable checkers on entire of TE flows..", "bool", 1)
        self.arguments.declare_arg("express", "Enable/Disable pound(express) mode on entire of TE flows..", "bool", 0)
        self.arguments.declare_arg("silent_mode", "Disable any DUT activity (TE emulation mode) on entire of flow..", "bool", 0)
        self.arguments.declare_arg(
            "constraint", "Define action execution constrain, conditioning on rtl module existence or CFG.<Category>[<VarName]<==|!=|<=|>=><VarValue> .", "string_or_int", "")
        self.arguments.declare_arg(
            "post_module", "Used as a python source path for loading dynamic external method flow_run() just after current action .", "string", "")
        self.arguments.declare_arg("refactor", "Used to mark a current action for refactoring .", "bool", 0)
        self.arguments.declare_arg("dummy", "Used to create a dummy - template action for future usage - prevent any run or validation", "string", 0)
        self.arguments.declare_arg("stop_flow", "Used to stop flow run after the action execution", "bool", 0)
        self.arguments.declare_arg("stop_segment_at_action", "Used to stop segment run after the action execution", "string", "")
        self.arguments.declare_arg("phase", "Used to override the segment phase name (given in TE_cfg.xml)", "string", "")
        self.name = ""
        self.connected_ips = []

        # ---------------------
        (segment_name, stage, self.rev_tag) = htd_segment_naming_disassembly(self.__class__.__name__)
        self.name = ("%s_Stage%s") % (segment_name, stage)
        # --------------------------
        if((("SEGMENTS" not in list(list(CFG.keys()))) or (self.name not in list(list(CFG["SEGMENTS"].keys())))) and (
                self.__class__.__name__ not in ["htd_segment", "htd_ip_segment"]) and (
                os.environ.get('HTD_TE_HELP_MODE') != "1")):
            htdte_logger.error(("(%s)Missing Segment revision definition in CFG[\"SEGMENTS\"][\"%s\"].Pls provide the configuration in TE_cfg.xml or command line ...") % (
                location_str, self.__class__.__name__))
        # ------------------------
        self.segment_init()
        # ------------------
        current_content_phase = ""
        if("SEGMENTS" in list(list(CFG.keys())) and self.name in list(list(CFG["SEGMENTS"].keys())) and "phase" in list(list(CFG["SEGMENTS"][self.name].keys()))):
            if(self.arguments.get_argument("phase") != ""):
                current_content_phase = self.arguments.get_argument("phase")
            else:
                current_content_phase = CFG["SEGMENTS"][self.name]["phase"]
            htdte_logger.setPhaseName(current_content_phase)
            self.phase_name = current_content_phase
        if(self.__current_flow is not None):
            self.__current_flow.phase_name = current_content_phase
        (seg, stage, self.rev_tag) = htd_segment_naming_disassembly(self.__class__.__name__)
    # -----------------------

    def html_help(self):
        str_result = ""
        str_result += add_class_help_description("htd_segment", "pre_segment_verification", "Segment handler to be manged/extended by user segment content and used for pre segment execution verificaion/readout  ",
                                                 "pre_segment_verification():Called internally by segment manager: segment_extend()-pre_segment_verification()-segment_run()-debug_readback() ")
        str_result += add_class_help_description("htd_segment", "debug_readback", "Segment handler to be manged/extended by user segment content and used for post segment  debug readout  ",
                                                 "debug_readback():Called internally by segment manager: segment_extend()-pre_segment_verification()-segment_run()-debug_readback() ")
        str_result += add_class_help_description("htd_segment", "segment_run", "Segment handler to be manged/extended by user segment content  ",
                                                 "segment_run():Called internally by segment manager: segment_extend()-pre_segment_verification()-segment_run()-debug_readback() ")
        str_result += add_class_help_description("htd_segment", "segment_extend", "Segment handler to be manged/extended by user to extend previously defined/inhereted sequece (usually used for design variability handling)   ",
                                                 "segment_extend():Called internally by segment manager: segment_extend()-pre_segment_verification()-segment_run()-debug_readback() \
                                         Normally used to execute action_extend(),disable_action(),sequence_extend()")
        str_result += add_class_help_description("htd_segment", "action_extend",
                                                 "Action parametric override by new argument list by following concept: \
                                          \n1. &lt;paramName1&gt;:&lt;integer|string&gt; - simply override existent callback in sequence for a new/modified parameter: self.exec_&lt;type&gt;_action({\"actionName\":\"&lt;ActionName&gt;\",...\"paramName1\":&lt;integer value&gt;})\
                                          \n2  &lt;paramName1&gt;:\"__rename__:&lt;paramName2 string&gt\"; - substitute assigned argument/field name &lt;paramName1&gt; by new  &lt;paramName2&gt;\
                                          \n3  &lt;paramName1&gt;:\"__delete__\" - remove the existent argument/field assignment (if disappear on current design step",
                                                 "self.action_extend(&lt;ActionName&gt;,{&lt;param1&gt;:&lt;param1Val&gt;[,&lt;param2&gt;:&lt;param2Val&gt;]})")
        str_result += add_class_help_description("htd_segment", "disable_action",
                                                 "Disabling the specified action run from current segment execution sequence ", "self.disable_action(&lt;ActionName)")
        str_result += add_class_help_description("htd_segment", "sequence_extend",
                                                 "Extending sequence handler to be managed by content writer (injecting subsequence) starting from given action name ", "self.sequence_extend(&lt;ActionName&gt;,&lt;NameOfFunctionToExecuteAfterTheAction&gt;[pre|post])")
        str_result += add_class_help_description("htd_segment", "get_previously_running_action_argument_val", "Retrieve argument assignment from specified action (executed previously) ",
                                                 ("self.get_previously_running_action_argument_val(&lt;action_name&gt;,&lt;actionType:%s&gt;,&lt;argumentName-requested_argument_name&gt;)") % (str(util_itersubclasses_names(htd_base_action))))
        str_result += add_class_help_description("htd_segment", "get_previously_running_action_fields", "Retrieve field assignment set on specified action (executed previously) ",
                                                 ("self.get_previously_running_action_fields(&lt;action_name&gt;,&lt;actionType:%s&gt;)") % (str(util_itersubclasses_names(htd_base_action))))
        str_result += add_class_help_description("htd_segment", "has_previously_running_action_argument_val", "Evaluate argument assignment on specified action (executed previously) ",
                                                 ("self.has_previously_running_action_argument_val(&lt;action_name&gt;,&lt;actionType:%s&gt;,&lt;argumentName-requested_argument_name&gt;)") % (str(util_itersubclasses_names(htd_base_action))))
        for action_type in util_itersubclasses_names(htd_base_action):
            str_result += add_class_help_description("htd_segment", ("self.exec_%s_action") % (action_type.lower()),
                                                     "Running action sequence: verify_action_arguments()- pre_run_place_holder()-run()-post_run_place_holder()\
                                         \n- declared arguments : predefined arguments with predefined types (sting,bool,int,string_or_int) and predefined initial values\
					 \n- not declared arguments: design dependent arguments , usually register fields , assumed by integre/long type only ",
                                                     ("self.exec_%s_action({&lt;action_name&gt;,&lt;actionType:%s&gt;[,&lt;action_argument&gt;:&lt;value&gt;][,declared:&lt;action_argument&gt;:&lt;value&gt;][,notdeclared:&lt;action_argument&gt;:&lt;value&gt;]})") % (action_type.lower(), action_type.lower()))

        return str_result
    # ---------------------------------------

    def is_ipsegment(self):
        return False

    # ---------------------------------------
    def declare_arg(self, name, description, type_str, default, obligatory=1):
        self.arguments.declare_arg(name, description, type_str, default, obligatory)

    # ---------------------------------------
    def get_argument(self, name):
        return self.arguments.get_argument(name)

    # ---------------------------------------
    def print_interface_arguments(self):
        self.arguments.print_help()

    def print_segment_arguments(self):
        self.arguments.print_arguments(("Segment Parameters %10s,") % (self.__class__.__name__))

    def get_currentflow(self):
        """
        Returns the current flow object

        :rtype: htd_base_flow
        """
        return self.__current_flow

    def verify_obligatory_arguments(self):
        self.arguments.verify_obligatory_arguments(("Segment:%s") % (self.__class__.__name__))

    # ---------------------------
    def assign_arguments_container(self, container, arguments, object_type, location):
        for arg in list(list(arguments.keys())):
            if (arg not in list(list(container.keys()))):
                htdte_logger.error(("(%s)Illegal %s interface call argument -%s .\n\t\tAvailable arguments are: %s") % (
                    location, object_type, arg, list(list(container.keys()))))
            container.set_argument(arg, arguments[arg], ("%s") % (location))
        container.verify_obligatory_arguments(("%s:%s:%s") % (object_type, location, self.__class__.__name__))

    # ----------------------------------
    def pre_segment_verification(self):
        pass

    def debug_readback(self):
        pass

    # -----------------------------
    def segment_init(self):
        currently_running_segment = self
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
            for scls in util_itersubclasses(htd_segment):
                setattr(scls, ('exec_%s_action') % (acls.__name__.lower()),
                        per_action_type_callbacks[acls.__name__.upper()])

    # ------------------------------
    def exec_action(self, params, atype="none", location_file_str="none", location_file_lineno=0, calling_action="", override_arguments=None, override_arguments_description=""):

        info = inspect.getframeinfo(inspect.currentframe().f_back)[0:3]
        _path_tokens = info[0].split('/')
        location_file_str = _path_tokens[len(_path_tokens) - 1] if(location_file_str == "none") else location_file_str
        location_file_lineno = info[1] if(location_file_str == "none") else location_file_lineno
        if (("actionName" not in params) and (calling_action == "")):
            htdte_logger.error("Illegal action call argument - Missing action type argument -\"actionName\".")
        actionName = params["actionName"] if (calling_action == "") else ("internal_%s") % (calling_action)

        if (self.get_currentflow().get_stop_all_segments_at_action()):
            htdte_logger.inform(("!!!stop_segment detected - ignoring action - \"%s\"") % (actionName))
            return

        # --------------------------------------
        # --checking pre action subsequence
        if(actionName in list(list(self.__sequence_extend_per_action.keys()))):
            for sub_seq in self.__sequence_extend_per_action[actionName]:
                if(sub_seq["post"] == 0):
                    sub_seq["accessed"] = 1
                    method_obj = getattr(self, sub_seq["sequence"])
                    if sub_seq["params"] is None:
                        method_obj()
                    else:
                        method_obj(sub_seq["params"])
        # -----------------------
        result = self.get_currentflow().exec_action(params, atype, location_file_str, location_file_lineno, calling_action, self.__per_action_arguments.get_action_extend_params(actionName),
                                                    self.__per_action_arguments.get_action_extend_description(actionName))
        # ---Post action execute
        if(actionName in list(list(self.__sequence_extend_per_action.keys()))):
            for sub_seq in self.__sequence_extend_per_action[actionName]:
                if(sub_seq["post"] == 1):
                    sub_seq["accessed"] = 1
                    method_obj = getattr(self, sub_seq["sequence"])
                    if sub_seq["params"] is None:
                        method_obj()
                    else:
                        method_obj(sub_seq["params"])

        if(actionName != "" and actionName == self.arguments.get_argument("stop_segment_at_action") and not self.__current_flow.is_verification_mode()):
            self.get_currentflow().set_stop_all_segments_at_action(True)
        if (self.get_currentflow().get_stop_all_segments_at_action()):
            htdte_logger.inform(("!!!stop_segment detected - ignoring action - \"%s\" and ALL segments following it") % (actionName))
    # -----------------------------

    def segment_run(self):
        htdte_logger.error(("Trying to execute base htd_segment forbiden, pls. verify that inhereted class (%s) override segment_run() method.. ") % (
            str(util_itersubclasses_names(htd_segment))))
    # ----------------------

    def segment_extend(self): pass
    # ------------------------------

    def execute_segment(self):
        if (self.get_currentflow().get_stop_all_segments_at_action()):
            htdte_logger.inform("!!!stop_segment detected - ignoring segment %s" % (self.name))
            return
        self.segment_extend()
        self.pre_segment_verification()
        self.segment_run()
    # ---------------------------
    # Param - "existing or new action"???????

    def action_extend(self, action_name, params):
        info = inspect.getframeinfo(inspect.currentframe().f_back)[0:3]
        loc_string = ("%s:%d") % (info[0], info[1])
        self.__per_action_arguments.add_action_override(action_name, params, loc_string)
    # ---------------------------------

    def sequence_extend(self, actionName_to_inject_sequence, NameOfMethodToExecuteSubSequence, exec_order="post", params=None):
        info = inspect.getframeinfo(inspect.currentframe().f_back)[0:3]
        loc_string = ("%s:%d") % (info[0], info[1])
        if(exec_order != "post" and exec_order != "pre"):
            htdte_logger.error(("Illegal execution order given: %s (expected action \"pre\" or \"post\").. ") % (exec_order))
        all_methods = [method for method in dir(self) if isinstance(getattr(self, method), collections.Callable)]
        if(NameOfMethodToExecuteSubSequence not in all_methods):
            htdte_logger.error(("Illegal subsequence method name given : %s (not callable method of the class,available:%s).. ") %
                               (NameOfMethodToExecuteSubSequence, str(all_methods)))
        # Check that argument list of method is void)
        method_obj = getattr(self, NameOfMethodToExecuteSubSequence)
        arguments_of_method = inspect.getargspec(method_obj)[0]
        if(len(arguments_of_method) > 2):
            htdte_logger.error(("Illegal subsequence method used for sequence extension..(Expected method with 2 arguments at most (self + 1 arg), while given %s(%s) ") % (
                NameOfMethodToExecuteSubSequence, str(arguments_of_method).replace("self", "")))
        # --------------------
        if(actionName_to_inject_sequence not in list(list(self.__sequence_extend_per_action.keys()))):
            self.__sequence_extend_per_action[actionName_to_inject_sequence] = []
        new_entry = {}
        new_entry["src"] = loc_string
        new_entry["sequence"] = NameOfMethodToExecuteSubSequence
        new_entry["accessed"] = 0
        new_entry["post"] = 1 if(exec_order == "post") else 0
        new_entry["params"] = params
        self.__sequence_extend_per_action[actionName_to_inject_sequence].append(new_entry)
    # ---------------------------------

    def disable_action(self, action_name):
        info = inspect.getframeinfo(inspect.currentframe().f_back)[0:3]
        loc_string = ("%s:%d") % (info[0], info[1])
        self.__per_action_arguments.add_action_override(action_name, {"disable_action": 1, "description": (
            "Disabled action %s by segment.disable_action():%s") % (action_name, loc_string)}, loc_string)

    # ----------------------------
    def error(self, msg, exit):
        info = inspect.getframeinfo(inspect.currentframe().f_back)[0:3]
        self.error_bysrc(info[0], info[1], msg, exit)

    # ------------------------
    def error_bysrc(self, currfile, currline_no, msg, exit):
        self.get_currentflow().error_bysrc(currfile, currline_no, msg, exit)

    # ------------------------
    def sequence_extend_check_on_finish(self):
        htdte_logger.clrPhaseName()
        for act in list(list(self.__sequence_extend_per_action.keys())):
            for sub_seq in self.__sequence_extend_per_action[act]:
                if(sub_seq["accessed"] == 0 and self.get_currentflow().get_stop_all_segments_at_action() == False):
                    htdte_logger.error(
                        ("The sequence_extension defined at %s was never triggered.Pls. check an action refrence %s is get executed .") % (sub_seq["src"], act))

    def get_previously_running_action_argument_val(self, actionName, actionType, argumentName):
        return self.__current_flow.get_previously_running_action_argument_val(actionName, actionType, argumentName)

    def get_previously_running_action_argument(self, actionName, actionType):
        return self.__current_flow.get_previously_running_action_argument(actionName, actionType)

    def has_previously_running_action_argument(self, actionName, actionType, argumentName):
        return self.__current_flow.has_previously_running_action_argument(actionName, actionType, argumentName)

    def get_previously_running_action_fields(self, actionName, actionType):
        return self.__current_flow.get_previously_running_action_fields(actionName, actionType)

    def report_status_to_traceinfo(self, ip_name, info):
        """
        Add tag to trace_info.py to indicate if this trace has a (fusestring, unlock, etc),or if one of it's preceeding
        flows do
        This allows TVPV set the correct tracebits for the fuse team to match on
        See K-brief: https://palantir.intel.com/sites/PalantirHome/Knowledge%20Briefs/KB-007243.docx

        :param string ip_name: The specific data to append to trace_info.py
        :param string info: What kind of thing to report (fusestring, unlock, etc)

        :return: None
        """

        # Exit in verification mode, otherwise the tag gets printed twice
        if self.get_currentflow().is_verification_mode():
            return

        # This check essentially determines if we're in the flow that will get trace_saved, or something before it
        flow_flavor = self.get_currentflow().get_flow_flavor()
        if os.getenv("HTD_TRACEFLOW", "").lower() == flow_flavor.lower():
            # This segment will be tracesaved
            tag = "TRACE_HAS_%s_%s=True\n" % (ip_name.upper(), info.upper())
        else:
            # This segment will be cut by flow_chopper
            tag = "MY_PARENT_HAS_%s_%s=True\n" % (ip_name.upper(), info.upper())

        with open('trace_info.py', 'a') as info_file:
            info_file.write(tag)


# ----------------------------------------------------------------------
# Just encapsulating ip base class to separate from a regular segments
# ---------------------------------------------------------------------
class htd_ip_segment(htd_segment):

    def __init__(self, current_flow, ip_name):
        self.ip_name = ip_name
        self.ip_enabled = 0
        htd_segment.__init__(self, current_flow)

    def get_ip_name(self):
        return self.ip_name

    def enable_ip_segment(self):
        self.ip_enabled = 1

    def is_ip_segment_enabled(self):
        return self.ip_enabled

    def is_ipsegment(self):
        return True

    def get_ip_name(self):
        return self.ip_name

# ----------------------------------------------------------------------
# Just encapsulating ip base class to separate from a regular segments
# ---------------------------------------------------------------------


class htd_flow_segment(htd_segment):

    def __init__(self, current_flow, location_str=""):
        htd_segment.__init__(self, current_flow, location_str)
        # -----Action error callback

    def error(self, msg, exit):
        info = inspect.getframeinfo(inspect.currentframe().f_back)[0:3]
        self.error_bysrc(info[0], info[1], msg, exit)

    def error_bysrc(self, currfile, currline_no, msg, exit):
        self.get_currentflow().error_bysrc(currfile, currline_no, msg, exit)


# ------------------------------------------------
