#!/usr/intel/pkgs/python3/3.6.3a/modules/r1/bin/python  -B
import sys
import os
import math
import re
import inspect
import imp
from htd_utilities import *
from htd_arguments_container import *
single_paretness_arguments = ["te_cfg_env", "collateral_compile", "collateral_exclude", "info_help", "collect_rtl_signals"]
# **************************************************************************************************
# *****************************METHOD DEFINITIONS***************************************************
# **************************************************************************************************
# --------------------------------------------------------------------------------------------------
# ---Parsing pair of CMD arguments for matchin -argument <value> [-flow\d <arguments> -flow\d-]
# --------------------------------------------------------------------------------------------------
# ------------------------------


def format_arguments():
    result = {}
    arg_pairs = str(sys.argv[1:len(sys.argv)]).replace("', '", " ").replace("['", " ").replace("']", "").split(" -")
    flow_num_in_progress = -1
    flow_name_found = 0
    for argtoken in arg_pairs:
        if(len(argtoken) == 0):
            pass
        elif(re.match(r"^flow_\d+$", argtoken) or re.match(r"^flow\d+$", argtoken)):
            flow_name_found = 0
            matchFlowToken = re.match(r"^flow_(\d+)\s*$", argtoken)
            if not matchFlowToken:
                matchFlowToken = re.match(r"^flow(\d+)\s*$", argtoken)
                if not matchFlowToken:
                    htdte_logger.error(
                        ("Missing flow number in  flow class name- \"%s\" requested format -FLOW_TYPE_NAME_flow_execution_index 'Flow parameters'") % (argtoken))
            flow_num_in_progress = int(matchFlowToken.groups()[0])
        # -------------------------------
        elif(re.match(("^flow_%d-+$") % (flow_num_in_progress), argtoken) or re.match(("^flow%d-+$") % (flow_num_in_progress), argtoken)):
            if(("flow_name" not in list(result["flows"][flow_num_in_progress].keys()))):
                htdte_logger.error(("Missing obligatory flow name(type) argument - \"-flow%d -flow_name <NAME OF FLOW REPRESENTING CLASS> -flow%d-\"  ") %
                                   (flow_num_in_progress, flow_num_in_progress))
            flow_num_in_progress = -1
        # ----------------
        elif(flow_num_in_progress >= 0):
            if("flows" not in list(result.keys())):
                result["flows"] = {}
            farg = argtoken.split(" ")
            if(len(farg) != 2):
                htdte_logger.error(("Missing flow argument value or improper single argument name - \"-%s\" winthin -flow%d ... -flow%s- (Pls. run -cmd_help to get a complete list of supported arguments)") %
                                   (argtoken, flow_num_in_progress, flow_num_in_progress))
            if(flow_num_in_progress not in list(result["flows"].keys())):
                result["flows"][flow_num_in_progress] = {}
            result["flows"][flow_num_in_progress][farg[0]] = farg[1]
        # --------------------------
        else:
            marg = argtoken.split(" ")
            if(argtoken == "help" or argtoken == "h" or argtoken == "cmd_help"):
                if("arg" not in list(result.keys())):
                    result["arg"] = {}
                result["arg"]["help"] = [1]
                # --If help mode - the silent_mode is enabled--
                result["arg"]["silent_mode"] = [1]
            elif(argtoken in single_paretness_arguments):
                pass
            else:
                if(len(marg) != 2):
                    htdte_logger.error(
                        ("Missing argument value or improper single argument name- \"-%s\" (Pls. run -cmd_help to get a complete list of supported arguments) ") % (argtoken))
                if("arg" not in list(result.keys())):
                    result["arg"] = {}
                if(marg[0] not in list(result["arg"].keys())):
                    result["arg"][marg[0]] = []
                result["arg"][marg[0]].append(marg[1])
    # --------
    if(flow_num_in_progress >= 0):
        htdte_logger.error(("Missing -field%d- argument (cmd integrity error)...  ") % (flow_num_parameters_in_progress))
    return result
# ------------------------------------
# extracting tecfg override from command line
# ------------------------------------


def parsing_command_line_for_tecfg():
    cmd_args = format_arguments()
    if("arg" in list(cmd_args.keys())):
        manager_args = cmd_args["arg"]
        for manager_arg in list(manager_args.keys()):
            for argvalue in manager_args[manager_arg]:
                if(manager_arg == "tecfg" or manager_arg == "te_cfg"):
                    htdte_logger.inform(("Setting ENV[HTD_TE_CFG] based on CMD line parameter - testcfg <%s>.\n") % (argvalue))
                    if(not os.path.isfile(argvalue)):
                        htdte_logger.error(
                            "ERROR: Illegal TE_cfg.xml path applied on CMD line parameter (not exists or not readable) - testcfg <%s>.\n") % (argvalue)
                    os.environ["HTD_TE_CFG"] = argvalue
                    os.putenv("HTD_TE_CFG", argvalue)
                    TE_Cfg_override = argvalue
                # ----------------
                elif(re.match(r"^CFG:\w+", manager_arg)):
                    # Sub-keys read in here, but acual parsing is done later in htd_collaterals_parser
                    varcfg_match = re.match(r"^CFG:([A-z0-9_]+):([A-z0-9_\.\~\/:]+)", manager_arg)
                    category = varcfg_match.groups()[0]
                    key = varcfg_match.groups()[1]
                    if(category not in list(HTD_Cfgs_Cmd_Override.keys())):
                        HTD_Cfgs_Cmd_Override[category] = {}
                    HTD_Cfgs_Cmd_Override[category][key] = argvalue
# -------------------------------------
#
# -------------------------------------


def parsing_command_line_for_cfg(info_obj_override=None):
    info_obj = info_obj_override if(info_obj_override is not None) else HTD_INFO
    cmd_args = format_arguments()
    cfg_override = {}
    if("arg" in list(cmd_args.keys())):
        manager_args = cmd_args["arg"]
        for manager_arg in list(manager_args.keys()):
            for argvalue in manager_args[manager_arg]:
                if(manager_arg == "load_cfg"):
                    info_obj.read_cfg_file(argvalue)
                    # exec(info_obj.get_dynamic_cfg_methods_string())
# -----------------------------------------------------
# Get code source line info
# ---------------------------------------------------


def _line():
    info = inspect.getframeinfo(inspect.currentframe().f_back)[0:3]
    return '[%s:%d]' % (info[2], info[1])
# --------------------------------------------------------------------------------------------------
# Parsing command line and extracting te_manager declared arguments, or flow arguments assignment
# --------------------------------------------------------------------------------------------------


def parse_flow_arguments_from_command_line(manager_declared_arguments):
    import importlib
    globals().update(importlib.import_module('htd_basic_flow').__dict__)  #error on CFG not found if use exec()
    globals().update(importlib.import_module('htd_basic_action').__dict__)
    globals().update(importlib.import_module('htd_flow_library_top').__dict__)
    globals().update(importlib.import_module('htd_external_test').__dict__)

    if (os.environ.get('HTD_BABYSTEPS_LOCATION') is not None):
        globals().update(importlib.import_module('htd_babysteps_library_top').__dict__)
    if (os.environ.get('DRV_GLOBAL_TESTPLAN_DFX_FLOWS') is not None):
        globals().update(importlib.import_module('htd_global_dfx_flow_library_top').__dict__)
    if (os.environ.get('DRV_GLOBAL_TESTPLAN_RESET_FLOWS') is not None):
        globals().update(importlib.import_module('htd_global_reset_flow_library_top').__dict__)
    flows_list = {}
    manager_arg_list = []
    misc_modules = {}
    # globals=globals()
    # ------------------
    cmd_args = format_arguments()
    if("arg" in list(cmd_args.keys())):
        manager_args = cmd_args["arg"]
        if("misc_flow_module" in list(manager_args.keys())):
            for module in manager_args["misc_flow_module"]:
                mname, py_mod = LoadExtModule(module)
                misc_modules[mname] = py_mod
        # -----Verify corectness of manager argument
        for marg in list(manager_args.keys()):
            for argvalue in manager_args[marg]:
                if(marg == "tecfg" or marg == "te_cfg"or marg == "help" or marg == "collect_rtl_signals"):
                    pass
                elif(re.match(r"^ENV:\w+", marg)):
                    pass
                elif(re.match(r"^CFG:\w+", marg)):
                    pass
                elif(re.match("^sample_run", marg)):
                    pass
                # elif(marg=="misc_flow_module"):pass
                # elif(marg=="load_cfg"):pass
                elif(htdPlayer.hplClockMgr.is_clock(marg)):
                    for argvalue in manager_args[marg]:
                        # ----------Extracting and assign project clocks------
                        htdPlayer.hplClockMgr.set_clock_rate(marg, int(argvalue))
                elif(marg in list(manager_declared_arguments.keys())):
                    manager_arg_list.append(marg)
                    manager_declared_arguments.set_argument(marg, argvalue)
                else:
                    htdte_logger.error(
                        (" Unknown htd_manager argument - \"%s\" found in command line ,supported arguments are: -help,-te_cfg,-load_cfg,-misc_flow_module,-CFG<category>:<key>,-<clock_name> ") % (marg))
    # -------------------------
    if("flows" in list(cmd_args.keys())):
        for flow_num in list(cmd_args["flows"].keys()):
            if("flow_name" not in list(cmd_args["flows"][flow_num].keys())):
                htdte_logger.error(
                    ("Missing obligatory field type argument - \"-flow_name <name_of_flow_class_for_execution>\" winthin -flow%d ... -flow%s- ") % (flow_num))
            # ----------
            flow_type = cmd_args["flows"][flow_num]["flow_name"]
            flow_original_name = flow_type
            Flow_rev = ""
            if("FLOWREV_TABLE" in list(CFG.keys()) and flow_type in list(CFG["FLOWREV_TABLE"].keys())):
                if("rev" not in list(CFG["FLOWREV_TABLE"][flow_type].keys())):
                    htdte_logger.error(
                        (" Illegal usage FLOW revisioning table in TE_cfg.xml: missing \"rev\" attribute in <CFG category=\"FLOWREV_TABLE\" \n\t\t<Var key=\"%s\" \"rev\"=<REVSTRING>....") % (flow_type))
                if(len(list(CFG["FLOWREV_TABLE"][flow_type].keys())) > 1):
                    htdte_logger.error((" Illegal usage FLOW revisioning table in TE_cfg.xml: unknown attribute- [%s] \n in <CFG category=\"FLOWREV_TABLE\" \n\t\t<Var key=\"%s\" \"rev\"=<REVSTRING>....") % (
                        str([x for x in list(CFG["FLOWREV_TABLE"][flow_type].keys()) if(x != "rev")]), flow_type))
                Flow_rev = CFG["FLOWREV_TABLE"][flow_type]["rev"]
                flow_type = ("%s_Rev%s") % (flow_type, Flow_rev)
            # ---Collectin flow parameters--
            flow_params = {}
            for farg in list(cmd_args["flows"][flow_num].keys()):
                if(farg != "flow_name"):
                    if(re.match(r"^ENV:\w+", farg) or re.match(r"^CFG:\w+", farg)):
                        htdte_logger.error((" Illegal usage global arguments \"-CFG\" or \"-ENV\" is forbidden in flow scope: -flow%d ...-%s %s ...-flow%d- ") %
                                           (flow_num, farg, cmd_args["flows"][flow_num][farg], flow_num))
                    flow_params[farg] = cmd_args["flows"][flow_num][farg]
            # --Check for external test source---
            if (flow_type == "EXTERNAL_TEST" and "src" in flow_params):
                ext_test = flow_params["src"]

                local_file_search = 0  # SRC command should have exact path, unless cmdline
                pacman_parse = 0

                if ext_test == "cmdline":

                    # cmdline, no -src switch provided so figure out which source to load based on EnvVars
                    # TEST_FULL_NAME contains full path plus, filetype extensions; Will point to Vault Folder
                    # TESTNAME only contains filename, no extensions or paths
                    # Use TEST_FULL_NAME to populate:
                    #  **** file_type
                    #  **** file_name/testname
                    # If TEST_FULL_NAME does not exist, or file does not eixst,  or filetype is OBJ
                    #  search in the folder for first matching entry
                    # Then when loading check the local folder first for the file before the path
                    local_file_search = 1  # File is commind from commandline, have to search local folders
                    if 'TEST_FULL_NAME' not in os.environ:
                        if 'TESTNAME' not in os.environ:
                            htdte_logger.error('ERROR: Cannot find TEST_FULL_NAME or TESTNAME and external test source is cmdline')
                        else:
                            #ext_test = os.environ['TESTNAME']
                            # add in this code to call specific environment that defined by PACMAN_NAME
                            ext_test_en = os.path.basename(os.getenv['TESTNAME'])
                            os.environ['TESTNAME'] = ext_test_en
                            ext_test = os.getenv('TESTNAME')
                            htdte_logger.inform((" EXTERNAL_TEST getting env TESTNAME as : %s ") % (ext_test))
                    else:
                        ext_test = os.environ['TEST_FULL_NAME']
                        htdte_logger.inform((" EXTERNAL_TEST getting env TEST_FULL_NAME as : %s ") % (ext_test))

                # Save flow flavor to restore it after squashing the flow_params
                flow_flavor = None
                if ("flow_flavor" in flow_params):
                    flow_flavor = flow_params["flow_flavor"]
                flow_params = {}
                flow_params["flow_flavor"] = flow_flavor
                (file_base, file_type) = os.path.splitext(os.path.basename(ext_test))
                # Strip off any extra dot extentions for .PAC file check below
                # Python doesn't like file names with '.' in them, since it is module seperator
                file_base_no_dots = file_base.split('.')[0]

                # cgoh21 : Facing multiple HTD ticket, added rule to disable file type rule as needed
                #          Default all file type rule is enable, setenv in TE cfg <EnvVar>="disable" for rule not needed
                #          http://htd_tvpv_help.intel.com/Ticket/6334 => .espf
                #          http://htd_tvpv_help.intel.com/Ticket/6309 => .obj
                #          http://htd_tvpv_help.intel.com/Ticket/4827 => .empty

                flag_htd_file_type_espf = 1
                if 'HTD_FILE_TYPE_ESPF' in os.environ:
                    if os.environ['HTD_FILE_TYPE_ESPF'] == 'disable':
                        flag_htd_file_type_espf = 0
                flag_htd_file_type_itpp = 1
                if 'HTD_FILE_TYPE_ITPP' in os.environ:
                    if os.environ['HTD_FILE_TYPE_ITPP'] == 'disable':
                        flag_htd_file_type_itpp = 0
                flag_htd_file_type_pac = 1
                if 'HTD_FILE_TYPE_PAC' in os.environ:
                    if os.environ['HTD_FILE_TYPE_PAC'] == 'disable':
                        flag_htd_file_type_pac = 0
                flag_htd_file_type_py = 1
                if 'HTD_FILE_TYPE_PY' in os.environ:
                    if os.environ['HTD_FILE_TYPE_PY'] == 'disable':
                        flag_htd_file_type_py = 0
                flag_htd_file_type_e = 1
                if 'HTD_FILE_TYPE_E' in os.environ:
                    if os.environ['HTD_FILE_TYPE_E'] == 'disable':
                        flag_htd_file_type_e = 0
                flag_htd_file_type_sv = 1
                if 'HTD_FILE_TYPE_SV' in os.environ:
                    if os.environ['HTD_FILE_TYPE_SV'] == 'disable':
                        flag_htd_file_type_sv = 0
                flag_htd_file_type_obj = 1
                if 'HTD_FILE_TYPE_OBJ' in os.environ:
                    if os.environ['HTD_FILE_TYPE_OBJ'] == 'disable':
                        flag_htd_file_type_obj = 0

                # Exact Search
                htdte_logger.inform(" EXTERNAL_TEST - Exact File Search -")
                if os.path.isfile(ext_test):
                    if file_type == '.spf':
                        flow_params['test_path'] = ext_test
                        htdte_logger.inform(" EXTERNAL_TEST parse exact file : %s " % ext_test)
                    elif file_type == '.espf' and flag_htd_file_type_espf == 1:
                        flow_params['test_path'] = ext_test
                        htdte_logger.inform(" EXTERNAL_TEST parse exact file : %s " % ext_test)
                    elif file_type == '.itpp' and flag_htd_file_type_itpp == 1:
                        flow_params['test_path'] = ext_test
                        htdte_logger.inform(" EXTERNAL_TEST parse exact file : %s " % ext_test)
                    elif file_type == '.pac' and flag_htd_file_type_pac == 1:
                        pacman_parse = 1
                        htdte_logger.inform(" EXTERNAL_TEST parse exact file : %s " % ext_test)
                    elif file_type == '.py' and flag_htd_file_type_py == 1:
                        pacman_parse = 1
                        htdte_logger.inform(" EXTERNAL_TEST parse exact file : %s " % ext_test)
                    elif file_type == '.e' and flag_htd_file_type_e == 1:
                        htdte_logger.inform(" EXTERNAL_TEST ignored file type : %s " % ext_test)
                        continue  # Ignore sim based types
                    elif file_type == '.sv' and flag_htd_file_type_sv == 1:
                        htdte_logger.inform(" EXTERNAL_TEST ignored file type : %s " % ext_test)
                        continue  # Ignore sim based types
                    elif file_type == '.obj' and flag_htd_file_type_obj == 1:
                        htdte_logger.inform(" EXTERNAL_TEST ignored file type : %s " % ext_test)
                        continue  # Ignore sim based types

                    else:
                        # Test is not a valid sequence for Pacman, search for valid sequences
                        htdte_logger.inform(" EXTERNAL_TEST file not in any known file type (%s)" % file_type)
                        htdte_logger.inform(" EXTERNAL_TEST enable local file search")
                        local_file_search = 1
                        ext_test = ""  # This will correctly identify Error in the next block
                else:
                    htdte_logger.inform(" EXTERNAL_TEST file not exist at : %s " % ext_test)
                    htdte_logger.inform(" EXTERNAL_TEST enable local file search")
                    local_file_search = 1
                    ext_test = ""  # This will correctly identify Error in the next block

                if (local_file_search):
                    htdte_logger.inform(" EXTERNAL_TEST - Local File Search -")
                    if os.path.isfile(file_base + ".spf"):
                        #                        flow_type = 'EXTERNAL_TEST'
                        flow_params['test_path'] = file_base + ".spf"
                        ext_test = file_base + ".spf"
                        pacman_parse = 0
                        htdte_logger.inform(" EXTERNAL_TEST override with local file : %s " % ext_test)
                    elif os.path.isfile(file_base + ".espf") and flag_htd_file_type_espf == 1:
                        #                        flow_type = 'EXTERNAL_TEST'
                        flow_params['test_path'] = file_base + ".espf"
                        ext_test = file_base + ".espf"
                        pacman_parse = 0
                        htdte_logger.inform(" EXTERNAL_TEST override with local file : %s " % ext_test)
                    elif os.path.isfile(file_base + ".itpp") and flag_htd_file_type_itpp == 1:
                        #                        flow_type = 'EXTERNAL_TEST'
                        flow_params['test_path'] = file_base + ".itpp"
                        ext_test = file_base + ".itpp"
                        pacman_parse = 0
                        htdte_logger.inform(" EXTERNAL_TEST override with local file : %s " % ext_test)
                    # .pac and .py must use the no_dots version, because of how python treats dots in imports
                    elif os.path.isfile(file_base_no_dots + ".pac") and flag_htd_file_type_pac == 1:
                        pacman_parse = 1
                        ext_test = file_base_no_dots + ".pac"
                        os.environ['TESTNAME'] = ext_test
                        htdte_logger.inform(" EXTERNAL_TEST override with local file : %s " % ext_test)
                    elif os.path.isfile(file_base_no_dots + ".py") and flag_htd_file_type_py == 1:
                        pacman_parse = 1
                        ext_test = file_base_no_dots + ".py"
                        htdte_logger.inform(" EXTERNAL_TEST override with local file : %s " % ext_test)
                    else:
                        if not os.path.isfile(ext_test):
                            # NO Abosulte path, and no local copies
                            htdte_logger.inform(" EXTERNAL_TEST No known file type at source and local search")
                            htdte_logger.error(" ERROR: Unknown test type: %s" % ext_test)
                        else:
                            # Abosulte path, and no local copies
                            htdte_logger.inform(" EXTERNAL_TEST Test available at source, no local file found")
                            htdte_logger.inform(" EXTERNAL_TEST Parse exact file: %s" % ext_test)

                if (pacman_parse):
                    htdte_logger.inform(" EXTERNAL_TEST - Pacman Parse -")
                    mname, py_mod = LoadExtModule(ext_test)
                    misc_modules[mname] = py_mod
                    if 'PACMAN_NAME' in os.environ:
                        flow_original_name = flow_type = os.environ['PACMAN_NAME']
                        htdte_logger.inform(" EXTERNAL_TEST pacman parse PACMAN_NAME : %s " % flow_original_name)
                    elif 'TESTNAME' in os.environ:
                        # Need to strip off file extension for flowname.
                        flow_original_name, _ = flow_type, _ = os.path.splitext(os.environ['TESTNAME'])
                        htdte_logger.inform(" EXTERNAL_TEST pacman parse TESTNAME : %s " % flow_original_name)
                    else:
                        htdte_logger.error('ERROR: Cannot find either TESTNAME or PACMAN_NAME ENV vars')
                    if 'PACMAN_ARGS' in os.environ:
                        # Apply leading space before parsing, since split is on ' -', and first char is normally '-'
                        for argtoken in str(" " + os.environ['PACMAN_ARGS']).replace("', '", " ").replace("['", " ").replace("']", "").split(" -"):
                            if(len(argtoken) != 0):
                                farg = argtoken.split(" ")
                                if(len(farg) != 2):
                                    htdte_logger.error(("Missing flow argument value or improper single argument name - EXTERNAL FLOW"))
                                flow_params[farg[0]] = farg[1]
                        htdte_logger.inform(" EXTERNAL_TEST pacman parse PACMAN_ARGS : %s " % os.environ['PACMAN_ARGS'])

            # ---Initilize flow objects--------
            flow_classes = util_itersubclasses_names(htd_base_flow)
            if(flow_type not in flow_classes):
                errstr = (("ERROR:Illegal flow class name -%s%s requested in command line -flow\d -flow_name FLOW_TYPE_NAME -flow\d++ \n") %
                          (flow_original_name, ("(Rev:%s->%s)") % (Flow_rev, flow_type) if(Flow_rev != "") else ""))
                errstr = errstr + ("Pls. check that your htd_flow_library_top.phy importing the flow definitions or check argument name correctness.\n")
                errstr = errstr + ("Available FLOW classes are : \n")
                for cls in flow_classes:
                    errstr = errstr + ("%s,\n") % (cls)
                htdte_logger.error(("%s***********CMD ERROR****************") % (errstr))
            # --------
            exec_str = flow_type if (flow_type not in list(misc_modules.keys())) else ("%s.%s") % (misc_modules[flow_type], flow_type)
            if(re.search("^<module '([A-z0-9_]+)' from ", exec_str)):
                m = re.search("^<module '([A-z0-9_]+)' from ", exec_str)
                exec(("import %s") % (m.groups()[0]))
                exec_str = ("%s.%s") % (m.groups()[0], flow_type)
            obj = eval(exec_str)(flow_num)
            obj.set_flow_arguments(flow_params, "CMD")
            if(flow_num not in list(flows_list.keys())):
                flows_list[flow_num] = {}
            flows_list[flow_num]["obj"] = obj
    return (flows_list, misc_modules, manager_arg_list)


def LoadExtModule(module):
    htdte_logger.inform((" Loading User MISC module : \"-misc_flow_module %s\" ") % (module))
    if(not os.path.exists(module)):
        htdte_logger.error(("Attempt to load not existent MISC module - %s given in command line : \"-misc_flow_module\" ") % (module))
    status, mname, py_mod = util_dynamic_load_external_module(module)
    if(not status):
        htdte_logger.error((" Not existent MISC module - %s given in command line : \"-misc_flow\" ") % (module))
    try:
        command_module = __import__(mname, globals()['__name__'])
        keys = command_module.__all__
    except AttributeError:
        keys = dir(command_module)
        for key in keys:
            if not key.startswith('_'):
                globals()[key] = getattr(command_module, key)
    except ImportError:
        htdte_logger.error((" Fail to load  MISC module - %s given in command line : \"-misc_flow\" ") % (module))
    return mname, py_mod
