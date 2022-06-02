#!/usr/intel/pkgs/python3/3.6.3a/modules/r1/bin/python -Bu
import sys
import os
import math
import re
import inspect
import imp
# --------------------------

version = 1.0

# handle arguments that should stop the flow before actual execution


def __handle_te_cfg_env():
    htdte_logger.inform(
        "\n\n\n***********************TE CFG ENV ONLY MODE***************************************")
    sys.exit(0)


def __handle_collaterals_compile():
    htdte_logger.inform(
        "\n\n\n***********************COMPILING COLLATERALS ONLY MODE***************************************")
    sys.exit(0)


def __handle_info_ui_help():
    sys.exit(0)


def __handle_info_help(HTML_Help_dir):
    htdte_logger.inform(("\n\n\n***HTD_INFO HELP FILE CREATED:%s/htd_te_collaterals_help.html") % (HTML_Help_dir))
    sys.exit(0)


def __handle_general_help(exit_flag, HTML_Help_dir):
    htdPlayer.create_hpl_help(("%s/htd_hpl_help.html") % (HTML_Help_dir))
    htdte_logger.inform(("\n\n\n***HPL HELP FILE CREATED:%s/htd_hpl_help.html") % (HTML_Help_dir))
    if (exit_flag):
        sys.exit(0)


def __print_html_help_header(html_file):
    html_file.write("<!DOCTYPE html>\n<html>\n")
    html_file.write('<a name="top"></a>\n<body>')

    html_file.write('<br><a name="TE_COMMAND_LINE_USAGE"></a>\n')
    # ----------------------------
    html_file.write('<p><h1> Test Environment Manager Help: </h1></p>\n')
    html_file.write('<p><h3> Command Line Usage: </h3></p>\n')


def __handle_detailed_help(HTML_Help_dir, help_flag_raised):
    html_file = open(("%s/htd_te_help.html") % (HTML_Help_dir), 'w')

    # -----The short help is printed to screen , detailed help in html------------
    # --Create a bookmarks links for html
    __print_html_help_header(html_file)

    # get available flows
    available_flows = ""
    for cls in util_itersubclasses(htd_base_flow):
        available_flows = ("%s %s ") % (available_flows, cls.__name__)

    heading_separator = "\n\n\n\n\n*******************************************************************************************************************************************\n"
    te_cmd_help = ("\
    \thtd_te_manager.py [TestEnvironmentArguments] [-flow<FlowNum> -flow_name <FLOW_NAME> [<FlowArguments>] -flow<FlowNum>-]\n\n\
    \tFlowNum	  - integer from 1... represent an execution sequence of flows\n\
    \tFLOW_NAME	  - select a flow type name from a list of loaded flow types: %s\n\
    \tFlowArguments - [FlowArguments] [-<SegmentName>:<SegmentArgument> <value>] [-<ActionName>:<ActionArgument> <value>] [-<IpSegmentName>:<IpSegmentArgument> <value>]\n\
    \t                Explicit reference to declared argument reference : -declared:<Action|Segment|Ip name>:<argument_name> <argument_value>\n\n\n\
    ") % (available_flows)

    htdte_logger.inform(heading_separator + te_cmd_help)
    htdte_logger.inform("TestEnvironmentArguments:\n")

    manager_arguments.print_help()
    htdte_logger.inform(("\n\n\tFor more details pls. see %s/htd_te_help.html\n") % (HTML_Help_dir))

    html_help = te_cmd_help.replace("<", "&lt").replace(">", "&gt").replace("\n", "<br>").replace(
        "TestEnvironmentArguments", "<a href=\"#TestEnvironmentArguments\">Test Environment Arguments</a>")
    html_help = html_help.replace("[FlowArguments]", "<a href=\"#FlowArguments\">[FlowArguments]</a>")
    html_file.write(('<p>%s</p><br><hr>\n') % (html_help))

    # ---------Bookmarks--------------
    html_file.write("<p><h3> Quick bookmark links: </h3></p>\n")
    if (help_flag_raised):
        html_file.write('<a href="htd_te_collaterals_help.html">HTD_INFO HELP</a><br>\n')
        html_file.write('<a href="htd_hpl_help.html"> HPL HELP</a><br>\n')
    html_file.write('<hr>')
    # -------------------------------
    html_file.write('<p><h3> PACMAN Base Flow Interface: </h3></p>\n<table border="1">\n')
    temp_flow = eval("htd_base_flow")("HTML", -1)
    html_file.write('<tr bgcolor="blue"><th><td><font color="white">Method</font></td></th><th><td><font color="white">Description</font></td></th></tr>')
    html_file.write(temp_flow.html_help())
    html_file.write('</table>')
    html_file.write('<hr>')
    html_file.write('<p><h3> PACMAN Segment/IPSegment Interface: </h3></p>\n<table border="1">\n')
    temp_segment = eval("htd_segment")(None)
    html_file.write('<tr bgcolor="blue"><th><td><font color="white">Method</font></td></th><th><td><font color="white">Description</font></td></th></tr>')
    html_file.write(temp_segment.html_help())
    html_file.write('</table>\n')
    html_file.write('<hr>')

    # ----------------------------------
    html_file.write('<a href="#TestEnvironmentArguments">Test Environment Arguments</a><br><table border="1">\n')
    html_file.write(
        '<tr bgcolor="blue"><th><font color="white">TYPE</font></th><th><font color="white">NAME</font></th><th><font color="white">Module Path</font></th></tr>')

    # for each flow print the flow details
    for cls in util_itersubclasses(htd_base_flow):
        html_file.write((
            '<tr bgcolor="00FC00" align="left"><th>FLOW</th><th><a href="#%s_flow">%s</a></th><th>%s</th></tr>\n') % (
            cls.__name__, cls.__name__,
            inspect.getfile(cls).replace(os.environ.get('PACMAN_ROOT'), "$PACMAN_ROOT")))

    for user_segment in util_itersubclasses(htd_segment):
        html_file.write((
            '<tr bgcolor="FFCC33" align="left"><th>SEGMENT</th><th><a href="#%s_segment">%s</a></th><th>%s</th></tr>\n') % (
            user_segment.__name__, user_segment.__name__,
            inspect.getfile(user_segment).replace(os.environ.get('PACMAN_ROOT'), "$PACMAN_ROOT")))

    for user_action in util_itersubclasses(htd_base_action):
        html_file.write((
            '<tr bgcolor="00FCFF" align="left"><th>ACTION</th><th><a href="#%s_action">%s</a></th><th>%s</th></tr>\n') % (
            user_action.__name__, user_action.__name__,
            inspect.getfile(user_action).replace(os.environ.get('PACMAN_ROOT'), "$PACMAN_ROOT")))

    html_file.write('</table>')

    # -----------------------

    #htdte_logger.inform("***********************Available Clocks  default ratio:")
    html_file.write('<hr><p><h3> Available Clocks  default ratio:</h3></p><br>\n')
    for clk in htdPlayer.hplClockMgr.get_all_clocks():
        html_file.write(('<h5>%s</h5>\n') % (("%s - %d") % (clk, htdPlayer.hplClockMgr.dutClocks[clk])))

    manager_arguments.print_html_help(html_file, "TestEnvironmentArguments")

    # ---------------------------------
    html_file.write('<a name="FlowArguments"></a>\n<br><h2>FlowArguments</h2><br><br>\n')
    htdte_logger.set_supress_error()
    for cls in util_itersubclasses(htd_base_flow):
        try:
            temp_flow = eval(cls.__name__)(0)
            temp_flow.arguments.print_html_help(html_file, ("%s_flow") % (cls.__name__))
        except BaseException:
            pass
    # ------Segments----------------
    ips_l = util_itersubclasses(htd_ip_segment)
    for cls in util_itersubclasses_names(htd_segment):
        try:
            temp_segment = eval(cls)(temp_flow) if (cls != "htd_ip_segment") else eval(cls)(None, cls)
            temp_segment.arguments.print_html_help(html_file, ("%s_segment") % (cls))
        except BaseException:
            pass
    # ----------------------Actions
    for cls in util_itersubclasses_names(htd_base_action):
        temp_action = eval(cls)("help", "help", 0, None, False)
        temp_action.arguments.print_html_help(html_file, ("%s_action") % (cls), False)
        action_html = temp_action.get_specific_html_help()
        if (action_html != ""):
            html_file.write(action_html)
        html_file.write('<a href="#top">Top of Page</a>\n')
    htdte_logger.unset_supress_error()
    # -----------------------------------
    #html_file.write('<a>PACMAN Test content User Interface:</a><br><table border="1">\n')
    # html_file.write(
    #    '<tr bgcolor="blue"><th><font color="white">SCOPE</font></th><th><font color="white">MEHOD</font></th><th><font color="white">PROTOTYPE</font></th><th><font color="white">DESCRIPTION</font></th> </tr>')
    # for cl in HTD_Classes_Help.keys():
    #   for method in HTD_Classes_Help[cl].keys():
    #    html_file.write(('<tr bgcolor="00FC00" align="left"><th>%s</th><th>%s</a></th><th>%s</th></th><th>%s</th></tr>\n') % (cl,method,HTD_Classes_Help[cl][method]["prototype"],HTD_Classes_Help[cl][method]["description"]))
    # html_file.write('</table>')
    htdte_logger.inform("\n\n\n********************************************************************************")
    html_file.write('<br>\n</body>\n</html>\n')
    html_file.close()
    sys.exit(0)


def __check_htd_info_env():
    if (os.environ.get('HTD_INFO') is None):
        if (os.environ.get('PACMAN_ROOT') is not None and os.path.isdir(("%s/htd_info") % os.environ.get('PACMAN_ROOT'))):
            os.putenv('HTD_INFO', ("%s/htd_info") % os.environ.get('PACMAN_ROOT'))
            os.environ["HTD_INFO"] = ("%s/htd_info") % os.environ.get('PACMAN_ROOT')
        else:
            htdte_logger.error(
                'Missing obligatory unix environment ENV[HTD_INFO] - must point to HTD collaterals and configuration library location or $PACMAN_ROOT/htd_info directory stracture.')

    print((("Adding USER LIBRARY path=%s") % (os.environ.get('HTD_INFO'))))
    if (not os.path.isdir(os.environ.get('HTD_INFO'))):
        print((('\n\nERROR:  The given directory (%s) in ENV[HTD_INFO] - is not directory or not exists') % (
            os.environ.get('HTD_INFO'))))
        sys.exit(257)
    sys.path.append(os.environ.get('HTD_INFO'))


def __set_and_put_env(env_name, env_value):
    os.environ[env_name] = env_value
    os.putenv(env_name, env_value)


def __run_all_flows_for_signal_processing(flow_classes, flow_ignore):
    for fl in flow_classes:
        # --------
        if (fl in flow_ignore):
            continue
        htdte_logger.inform(("Processing flow-%s...") % (fl))
        flobj = eval(fl)(0)
        flobj.silent_mode = 1
        flobj.flow_override()
        flobj.verify_obligatory_arguments()
        flobj.verify_flow_arguments()
        flobj.flow_init()
        flobj.flow_run()


# ----------------------------------------------------------
def __execute_flow(flow_obj, manager_arg_list, verify_mode=False):
    if (verify_mode):
        flow_obj.set_verify_mode()
        htdte_logger.inform(
            ("Start Flow:%s flowId:%d Verification:") % (flow_obj.get_flow_type(), flow_obj.get_flow_num()))
        htdPlayer.hpl_to_dut_interface.print_header(
            ("*******************************************\n\tStart Flow:%s flowId:%d Verification:") % (
                flow_obj.get_flow_type(), flow_obj.get_flow_num()))
    else:
        flow_obj.silent_mode = GENERAL_SILENT_MODE
        htdte_logger.inform(
            ("---------Start Flow:%s flowId:%d------------") % (flow_obj.get_flow_type(), flow_obj.get_flow_num()))
        htdte_logger.inform(("Start Flow %s %d") % (flow_obj.get_flow_type(), flow_obj.get_flow_num()),
                            HTD_PRINT_INTERFACE_ONLY)
        # TODO
        # The additional print of seinfo below is purely to support dual trace in KBL
        # ITPP is used to drive simulation which generates the FSDB with signatures. Since all labels are removed in ITPP->FSDB, seinfo needed to mark the chop points for SE
        # Once this feature is no longer needed/supported, this line can be cleaned up. Flow chopper only looks at the Start Flow* | End Flow* keywords
        htdte_logger.inform("vc2_api.set_seinfo(seinfostr=HTD_TEST_START_%s)" % (flow_obj.get_flow_flavor().upper()), HTD_PRINT_INTERFACE_ONLY)

    # ------------------------------------------------------------------------
    if("debug_readback" in manager_arg_list):
        flow_obj.arguments.set_argument("debug_readback", manager_arguments.get_argument("debug_readback"), "CMD")
    if("check" in manager_arg_list):
        flow_obj.arguments.set_argument("check", manager_arguments.get_argument("check"), "CMD")
    if("express" in manager_arg_list):
        flow_obj.arguments.set_argument("express", manager_arguments.get_argument("express"), "CMD")
    if("silent_mode" in manager_arg_list):
        flow_obj.arguments.set_argument("silent_mode", manager_arguments.get_argument("silent_mode"), "CMD")
    # ----------------------
    flow_obj.flow_override()

    if (not verify_mode):
        flow_obj.print_flow_arguments()  # print flow arguments only on execution mode
    flow_obj.verify_obligatory_arguments()
    if (verify_mode):
        flow_obj.verify_flow_arguments()  # Make flow argument verify only once (at verification)
    if (not verify_mode):
        flow_obj.pre_flow_run()  # Pre run in executive mode only
    flow_obj.flow_init()
    flow_obj.flow_run()
    if (not verify_mode):
        flow_obj.post_flow_run()  # make post flow handler only in execution mode
    flow_obj.post_verify()
    if (flow_obj.arguments.get_argument("debug_readback")):
        flow_obj.debug_readback()
    # -----------------------
    if (verify_mode):
        flow_obj.unset_verify_mode()
        flow_obj.unset_stop_flow_mode()
        htdPlayer.hplSignalMgr.verify_all_collected_signals()
        htdte_logger.inform(
            ("End Flow Verification Flow:%s  flowId:%d ") % (flow_obj.get_flow_type(), flow_obj.get_flow_num()))
        htdPlayer.hpl_to_dut_interface.print_header(
            "End Flow Verification \n\t*******************************************")
    else:
        # end of execution - unset the silent mode for the player for next execution
        htdPlayer.unset_silent_mode()
        htdte_logger.inform("***********************End Flow*****************************")

        # TODO
        # The additional print of seinfo below is purely to support dual trace in KBL
        # ITPP is used to drive simulation which generates the FSDB with signatures. Since all labels are removed in ITPP->FSDB, seinfo needed to mark the chop points for SE
        # Once this feature is no longer needed/supported, this line can be cleaned up. Flow chopper only looks at the Start Flow* | End Flow* keywords
        htdte_logger.inform("vc2_api.set_seinfo(seinfostr=HTD_TEST_END_%s)" % (flow_obj.get_flow_flavor().upper()), HTD_PRINT_INTERFACE_ONLY)
        htdte_logger.inform(("End Flow %s %d") % (flow_obj.get_flow_type(), flow_obj.get_flow_num()),
                            HTD_PRINT_INTERFACE_ONLY)
    # clear the phase name when done
    flow_obj.clear_phase_name()

# ----------------------------------------------------------


def __verify_flows_location(te_logger):
    if (os.environ.get('HTD_FLOW_LOCATION') is None):
        te_logger.error(
            'Missing obligatory unix environment ENV[HTD_FLOW_LOCATION] - must point to user flow libraries location')
    te_logger.inform(("Adding USER LIBRARY path=%s") % (os.environ.get('HTD_FLOW_LOCATION')))
    if (not os.path.isdir(os.environ.get('HTD_FLOW_LOCATION'))):
        te_logger.error(('The given directory (%s) in ENV[HTD_FLOW_LOCATION] - is not directory or not exists') % (
            os.environ.get('HTD_FLOW_LOCATION')))

    if (os.environ.get('HTD_BABYSTEPS_LOCATION') is not None):
        te_logger.inform(("Adding USER LIBRARY path=%s") % (os.environ.get('HTD_BABYSTEPS_LOCATION')))
        if (not os.path.isdir(os.environ.get('HTD_BABYSTEPS_LOCATION'))):
            te_logger.error(('The given directory (%s) in ENV[HTD_BABYSTEPS_LOCATION] - is not directory or not exists') % (
                os.environ.get('HTD_BABYSTEPS_LOCATION')))

    if (os.environ.get('DRV_GLOBAL_TESTPLAN_DFX_FLOWS') is not None):
        te_logger.inform(("Adding USER LIBRARY path=%s") % (os.environ.get('DRV_GLOBAL_TESTPLAN_DFX_FLOWS')))
        if (not os.path.isdir(os.environ.get('DRV_GLOBAL_TESTPLAN_DFX_FLOWS'))):
            te_logger.error(('The given directory (%s) in ENV[DRV_GLOBAL_TESTPLAN_DFX_FLOWS] - is not directory or not exists') % (
                os.environ.get('DRV_GLOBAL_TESTPLAN_DFX_FLOWS')))

    if (os.environ.get('DRV_GLOBAL_TESTPLAN_RESET_FLOWS') is not None):
        te_logger.inform(("Adding USER LIBRARY path=%s") % (os.environ.get('DRV_GLOBAL_TESTPLAN_RESET_FLOWS')))
        if (not os.path.isdir(os.environ.get('DRV_GLOBAL_TESTPLAN_RESET_FLOWS'))):
            te_logger.error(('The given directory (%s) in ENV[DRV_GLOBAL_TESTPLAN_RESET_FLOWS] - is not directory or not exists') % (
                os.environ.get('DRV_GLOBAL_TESTPLAN_RESET_FLOWS')))
# -----------------------------------------------------------


def __get_te_manager_arguments():
    manager_arguments = htd_argument_containter(HTD_ARGUMENTS_DECLARED_ONLY)
    manager_arguments.declare_arg("misc_flow_module", "Dynamically load python module contain user defined flow definition.", "string")
    manager_arguments.declare_arg("misc_info_module", "Dynamically load python module for HTD_INFO modifications.", "string")
    manager_arguments.declare_arg(
        "debug_readback", "Debugability readback activity to be matched on DUT option, enforced on all flows/actions/segments..", "bool", 0)
    manager_arguments.declare_arg("check", "Enable/Disable checkers on entire of TE flows..", "bool", 1)
    manager_arguments.declare_arg("express", "Enable/Disable pound(express) mode on entire of TE flows..", "bool", 0)
    manager_arguments.declare_arg("silent_mode", "Disable any DUT activity (TE emulation mode)..", "bool", 0)
    manager_arguments.declare_arg("load_cfg", "Load additional XML cfg file..", "string", "")
    manager_arguments.declare_arg("collateral_compile", "Compile collaterals only ", "bool", 0)
    manager_arguments.declare_arg("collateral_exclude", "Exclude collaterals list from compiling (separated by ,) ", "string", 0)
    manager_arguments.declare_arg("cmd_help", "Print command line help", "none")
    manager_arguments.declare_arg("info_help", "Print all HTD_INFO content to htd_te_collaterals_help.html", "bool", 0)
    manager_arguments.declare_arg("hpl_help", "Print HTD Player  content to htd_te_collaterals_help.html", "bool", 0)
    manager_arguments.declare_arg(
        "info_ui_help", "Print INFO UI content (if available) in html format - the value of argument selct ui name", "string", 0)
    manager_arguments.declare_arg("help", "Print all dynamic help documents", "none")
    manager_arguments.declare_arg("tecfg", "Specify TE_cfg.xml location , different from ENV[HTD_TE_CFG]", "string", 0)
    manager_arguments.declare_arg("CFG:<category>:<key>", "Override TE_cfg configuration values defined by TE_cfg.xml.", "string", 0)
    manager_arguments.declare_arg(
        "ENV:<UNIX_env_name>", "Used to override UNIX environment <UNIX_env_name> by given value, override shell and TE_cfg assignment", "string", 0)
    manager_arguments.declare_arg(
        "collect_rtl_signals", "Enable signal collecting flow to file \"htd_rtl_signals_collection.sig\": iterate over all existent flow and collect all accessed signals.", "none")
    manager_arguments.declare_arg("ignore_flow_in_collecting_signals",
                                  "List of flow names to be ignored in rtl signal collector.\"<Flowtype1>,<Flowtype2>,..\"", "string", "")
    manager_arguments.declare_arg("reset_history", "Reset flow to flow history ", "bool", 0)
    manager_arguments.declare_arg("history_chkpt_file", "Pointer to history manager checkpoint file  ", "string", "")
    manager_arguments.declare_arg("force_history_chkpt", "Don't delete history checkpoint when flow1 exists", "bool", 0)

    return manager_arguments

# a function to get the list of classes that belongs to a specific file


def get_list_of_flows_in_file(flows_l, search_file_name):
    htdte_logger.inform("search corresponding flows in file %s" % (search_file_name))
    flow_names_found = []
    search_file_name = os.path.splitext(search_file_name)[0]
    for cls in flows_l:
        file_path = inspect.getfile(cls)
        file_name = os.path.basename(file_path)
        file_name = os.path.splitext(file_name)[0]
        flow_name = cls.__name__
        if (file_name == search_file_name):
            htdte_logger.inform("flow %s found in file %s" % (flow_name, file_name))
            flow_names_found.append(flow_name)
    return flow_names_found

# --------------------------------


def __collect_rtl_signals():
    __set_and_put_env("HTD_COLLECT_RTL_SIGNALS_MODE", "1")
    flow_classes = util_itersubclasses_names(htd_base_flow)
    args = format_arguments()
    ignore_list = []
    if ('arg' in list(args.keys())):
        if ("ignore_flow_in_collecting_signals" in list(args['arg'].keys())):
            ignore_list = args['arg']["ignore_flow_in_collecting_signals"][0].split(',')
        if ("ignore_flow_files_in_collecting_signals" in list(args['arg'].keys())):
            files_to_ignore = args['arg']["ignore_flow_files_in_collecting_signals"][0].split(",")
            for single_file in files_to_ignore:
                flows_classes = util_itersubclasses(htd_base_flow)
                ignore_list.extend(get_list_of_flows_in_file(flows_classes, single_file))

    htdte_logger.inform("list of classes to ignore %s" % (ignore_list))
    __run_all_flows_for_signal_processing(flow_classes, ignore_list)
    htdPlayer.close()
    sys.exit(0)
# ---


def __history_init(reset_history, checkpt_file):
    if CFG["HPL"].get("skip_history_file", 0):
        return
    if(1 in flow_seq and os.path.isfile(htd_history_mgr.get_chkpt_file_name()) and not manager_arguments.get_argument("force_history_chkpt")):
        htdte_logger.inform(("Checkpoint file(%s) found , deleting by FLOW1 sequence.") % (htd_history_mgr.get_chkpt_file_name()))
    else:
        htd_history_mgr.restore()
        htdte_logger.inform(("Restored CheckFileInfo: %s ") % (htd_history_mgr.get_chkpt_file_name()))
    if(reset_history):
        htd_history_mgr.clean_history()
    if(checkpt_file != ""):
        htd_history_mgr.load_history(checkpt_file)


def __validate_non_duplicate_flows_and_segments():
    # validate flows are not duplicated

    segment_file = set()
    available_flownames = util_itersubclasses_names(htd_base_flow)

    duplicate_flows = set([x for x in available_flownames if available_flownames.count(x) > 1])

    if (len(duplicate_flows) > 0):
        flows_classes = util_itersubclasses(htd_base_flow)
        for flow_class in flows_classes:
            if (flow_class.__name__ in duplicate_flows):
                htdte_logger.inform("duplicate flow '%s' found in file %s" % (flow_class.__name__, inspect.getfile(flow_class)))
        htdte_logger.error("the following flows are duplicated: %s" % (duplicate_flows))

    available_segments = util_itersubclasses_names(htd_flow_segment)
    duplicate_segments = set([x for x in available_segments if available_segments.count(x) > 1])

    if (len(duplicate_segments) > 0):
        segments_classes = util_itersubclasses(htd_flow_segment)
        for segment_class in segments_classes:
            if (segment_class.__name__ in duplicate_segments):
                htdte_logger.inform("duplicate segment '%s' found in file %s" % (segment_class.__name__, inspect.getfile(segment_class)))
                segment_file.add(os.path.basename(inspect.getfile(segment_class)).split(".")[0])
        htdte_logger.error("The following segments are duplicated: %s. \n\nPlease check your segment files in case you are importing the following segment (%s) in one of the files explicitly" % (duplicate_segments, segment_file))

    htdte_logger.inform("Validation of flows/segments duplication is done")


def __validate_non_duplicate_flows_and_segs_same_file():
    processed_files = []
    errors_list = []

    # flows
    flows_classes = util_itersubclasses(htd_base_flow)
    for flow_class in flows_classes:
        orig_file_name = inspect.getfile(flow_class)
        found_flows = []
        filename, file_extension = os.path.splitext(orig_file_name)
        if (file_extension == ".pyc"):
            orig_file_name = orig_file_name[:-1]
        if (orig_file_name in processed_files):
            #htdte_logger.inform("file %s was already proceessed" %(orig_file_name))
            continue
        found_flows = util_grep_file_classes(orig_file_name)
        #htdte_logger.inform("list of classes found in file %s: %s" %(orig_file_name, found_flows))

        duplicate_flows = set([x for x in found_flows if found_flows.count(x) > 1])
        if (len(duplicate_flows) > 0):
            error_msg = "the following flows in file %s are duplicated: %s" % (orig_file_name, duplicate_flows)
            errors_list.append(error_msg)

        processed_files.append(orig_file_name)

    # segments
    segments_classes = util_itersubclasses(htd_flow_segment)
    for segment_class in segments_classes:
        orig_file_name = inspect.getfile(segment_class)
        found_segments = []
        filename, file_extension = os.path.splitext(orig_file_name)
        if (file_extension == ".pyc"):
            orig_file_name = orig_file_name[:-1]
        if (orig_file_name in processed_files):
            #htdte_logger.inform("file %s was already proceessed" %(orig_file_name))
            continue
        found_segments = util_grep_file_classes(orig_file_name)
        #htdte_logger.inform("list of classes found in file %s: %s" %(orig_file_name, found_segments))

        duplicate_segments = set([x for x in found_segments if found_segments.count(x) > 1])
        if (len(duplicate_segments) > 0):
            error_msg = "the following segments in file %s are duplicated: %s" % (orig_file_name, duplicate_segments)
            errors_list.append(error_msg)

        processed_files.append(orig_file_name)

    if (len(errors_list) > 0):
        htdte_logger.error("The following duplication errors occured %s" % (str(errors_list)))


###################### End of private function ###############################################################

#-------------------------Main code execution -----------------------------------------#
# -----------HTML_Help_dir=("%s/html_help/")%(os.environ.get('PWD'))
# ---------Special handling for unix env handling from command line  in format -ENV:<Name> <Value>------------------------

# Check if you are running inside HTD_ROOT, and die if so.
# This is to prevent leaving lots of just in your HTD_ROOT you need to cleanup later
if re.match(os.getenv("HTD_ROOT", "HTD_ROOT"), os.getcwd()) or re.match(os.getenv("PACMAN_ROOT", "PACMAN_ROOT"), os.getcwd()):
    print("\n ERROR: Don't run htd_te_manager.py inside of HTD_ROOT or PACMAN_ROOT")
    exit(-1)

all_indexes = [x for x in range(len(sys.argv)) if re.search("^-ENV:", sys.argv[x])]
overriten_env_list_str = ""
delim = ""
te_exit_status = 0
for env_indx in all_indexes:
    m = re.match("-ENV:([A-z0-9_]+)", sys.argv[env_indx])
    if (not m):
        print(((
            "\n\nERROR: Illegal environment name given in command line %s, should match expression : -ENV:([A-z0-9_]+)") % (
            sys.argv[env_indx])))
    env_name = m.groups()[0]
    if (len(sys.argv) < env_indx + 2):
        print((("\n\nERROR: Missing Unix environment value argument in command line %s") % (sys.argv[env_indx])))
    env_value = sys.argv[env_indx + 1]
    print((("Setting UNIX ENV[\"%s\"]=\"%s\" by CMD..\n") % (env_name, env_value)))
    overriten_env_list_str = ("%s%s%s") % (overriten_env_list_str, delim, env_name)
    delim = ","
    __set_and_put_env(env_name, env_value)
os.environ["HTD_CMD_OVERRITEN_ENV_LIST"] = overriten_env_list_str

# -------Common utilities and Collaterals import---
__check_htd_info_env()

# -------------------------
sys.path.append(os.path.dirname(__file__))
if (("-help" in sys.argv) or ("-h" in sys.argv) or ("-cmd_help" in sys.argv)):
    __set_and_put_env("HTD_TE_HELP_MODE", "1")
    if ("-cmd_help" in sys.argv):
        __set_and_put_env("HTD_TE_CMD_HELP_MODE", "1")
# ------------------------------
if (("-info_help" in sys.argv) or ("-help" in sys.argv)):
    print("\n\n\n***********************HTD_INFO HELP MODE***************************************")
    os.environ["HTD_TE_COLLATERALS_HELP_MODE"] = "1"
# ------------------------------
if ("-te_cfg_env" in sys.argv):
    print("\n\n\n***********************TE CFG ENV ONLY MODE***************************************")
    os.environ["HTD_TE_CFG_ENV_ONLY"] = "1"

# ---Extracting dicrectly collateral_compile mode - need to be managed explicetly out of argument container once affecting on imported HTD INFO without post-control---
if ("-collateral_exclude" in sys.argv and "-collateral_compile" not in sys.argv):
    print("\n\nERROR:  Illegal -collateral_exclude usage, could not be used without -collateral_compile")
    sys.exit(257)
# -------------------------------------
if ("-collateral_compile" in sys.argv):
    print("\n\n\n***********************COMPILING COLLATERALS ONLY MODE***************************************")
    os.environ["HTD_TE_COLLATERALS_COMPILE_MODE"] = "1"
    if ("-collateral_exclude" in sys.argv):
        index = sys.argv.index("-collateral_exclude")
        if (len(sys.argv) < index + 2):
            print("\n\nERROR:  Missing arguments for -collateral_exclude <list of dictionaries separated by ','>")
            sys.exit(257)
        os.environ["HTD_TE_COLLATERALS_COMPILE_EXCLUDE"] = sys.argv[index + 1]
        print((("\n\n\n*******************EXCLUDING DICTIONARIES: %s") % (str(sys.argv[index + 1]))))
# --------------------------------
if ("-info_ui_help" in sys.argv):
    index = sys.argv.index("-info_ui_help")
    if (len(sys.argv) < index + 2):
        print("\n\nERROR:  Missing arguments for -info_ui_help  <name of UI>")
    print((
        ("\n\n\n***********************Extracting UI %s***************************************") % (
            sys.argv[index + 1])))
    os.environ["HTD_TE_INFO_UI_HELP"] = sys.argv[index + 1]

# -----Need to catch any run time error to close all sub processes
from htd_utilities import *
# try:
if(1):
    # --------------------------------
    from htd_te_manager_utilities import *

    htdte_logger.inform("Original Command: %s" % (" ".join(sys.argv)))
    parsing_command_line_for_tecfg()
    if ("-misc_info_module" in sys.argv):
        print("\n\n\n***********************LOADING INFO MISC Module***************************************")
        index = sys.argv.index("-misc_info_module")
        if (len(sys.argv) < index + 2):
            print("\n\nERROR:  Missing arguments for -misc_info_module <list of dictionaries separated by ','>")
        os.environ["HTD_TE_COLLATERALS_HACK"] = sys.argv[index + 1]

    # ---------------------
    from htd_collaterals import *
    #from htd_clocks import *

    # Do env checks on user to make sure this pacman run will succeed
    env_group_check()
    if (os.environ.get('REMOTE_GROUP_CHECK') is not None):
        for remote in (os.environ.get('REMOTE_GROUP_CHECK')).split(","):
            env_group_check(remote)
    env_os_check()

    if ("-te_cfg_env" in sys.argv):
        __handle_te_cfg_env()

    # -----------------------------------------------------------------------------------------------------------------
    #                                        MAIN
    # -----------------------------------------------------------------------------------------------------------------
    # -----CFG override resolved at initial state before importing everything in order to have an updated configuration
    # -----used for any internal scope initialization
    # -----------------------------
    htdte_logger.inform(("Executing -%s , version:%s") % (
        str(sys.argv).replace("['", "").replace("']", "").replace("', '", " "), str(version)))
    htdte_logger.add_header("--------------------------------------------------------")
    htdte_logger.add_header(("Generated by %s at %s %s") % (
        getpass.getuser(), datetime.datetime.now().time().isoformat(), os.environ.get('PWD')))
    htdte_logger.add_header(("%s") % (str(sys.argv).replace("['", "").replace("']", "").replace("', '", " ")))
    parsing_command_line_for_cfg(HTD_INFO)

    from htd_basic_flow import *
    from htd_basic_action import *
    #from htd_clocks import *
    from htd_player_top import *

    # -----------------FLOW LIBRARIES--------------

    # Using predefined ENV to load user top file - HTD_FLOW_LOCATION
    __verify_flows_location(htdte_logger)
    sys.path.append(os.environ.get('HTD_FLOW_LOCATION'))
    sys.path.append(os.path.dirname(__file__))

    # import babystep location (optional)
    if (os.environ.get('HTD_BABYSTEPS_LOCATION') is not None):
        sys.path.append(os.environ.get('HTD_BABYSTEPS_LOCATION'))
        sys.path.append(os.path.dirname(__file__))

    from htd_flow_library_top import *
    if (os.environ.get('HTD_BABYSTEPS_LOCATION') is not None):
        from htd_babysteps_library_top import *

    if (os.environ.get('DRV_GLOBAL_TESTPLAN_DFX_FLOWS') is not None):
        sys.path.append(os.environ.get('DRV_GLOBAL_TESTPLAN_DFX_FLOWS'))
        sys.path.append(os.path.dirname(__file__))

    from htd_flow_library_top import *
    if (os.environ.get('DRV_GLOBAL_TESTPLAN_DFX_FLOWS') is not None):
        from htd_global_dfx_flow_library_top import *

    if (os.environ.get('DRV_GLOBAL_TESTPLAN_RESET_FLOWS') is not None):
        sys.path.append(os.environ.get('DRV_GLOBAL_TESTPLAN_RESET_FLOWS'))
        sys.path.append(os.path.dirname(__file__))

    from htd_flow_library_top import *
    if (os.environ.get('DRV_GLOBAL_TESTPLAN_RESET_FLOWS') is not None):
        from htd_global_reset_flow_library_top import *

    # Define the main arguments HERE, those arguments will be recognized as a main declare parameters ,
    # otherwise  will be used to match a flow name -----------
    manager_arguments = __get_te_manager_arguments()

    # add pre_flow_runclock arguments
    for clk in htdPlayer.hplClockMgr.get_all_clocks():
        manager_arguments.declare_arg(clk, "Override defined by TE_cfg clock ratio", "int", 0)

    if ("-collateral_compile" in sys.argv):
        __handle_collaterals_compile()
    if ("-info_ui_help" in sys.argv):
        __handle_info_ui_help()
    if ("-info_help" in sys.argv):
        __handle_info_help(HTML_Help_dir)
    if (("-hpl_help" in sys.argv) or ("-help" in sys.argv)):
        exit_flag = True if "-hpl_help" in sys.argv else False
        __handle_general_help(exit_flag, HTML_Help_dir)
    if (("-cmd_help" in sys.argv) or ("-help" in sys.argv) or ("-h" in sys.argv)):
        help_flag_raised = True if ("-help" in sys.argv) else False
        __handle_detailed_help(HTML_Help_dir, help_flag_raised)

    # ------------Generate signal collection----------------------
    __set_and_put_env("HTD_COLLECT_RTL_SIGNALS_MODE", "0")
    if ("-collect_rtl_signals" in sys.argv):
        __collect_rtl_signals()
    # ----------------------
    else:
        if (len(sys.argv) % 2 != 1):
            htdte_logger.error("Wrong parenthesis of arguments in command line...")

        # ---Assign Flow execution sequence------
        (_htd_flows_list, misc_modules, manager_arg_list) = parse_flow_arguments_from_command_line(manager_arguments)
        htdPlayer.hplClockMgr.check_for_unassigned_clock_ratio()

        # -----------------Start Main logic-------------------
        htdte_logger.inform("---------MAIN CMD ARGUMENTS------------")
        for main_arg in list(manager_arguments.keys()):
            htdte_logger.inform("  -" + main_arg + "=" + str(manager_arguments.get_argument(main_arg, 1)))
        htdte_logger.inform("---------END MAIN CMD ARGUMENTS------------")

        __validate_non_duplicate_flows_and_segments()
        __validate_non_duplicate_flows_and_segs_same_file()

        # -------------Flows execution--------------------------------------
        start_flow_time = time.time()

        # ---------Verifying flows only - calling all actions.verify - only---------
        flow_seq = sorted(_htd_flows_list.keys())
        # ---------------
        __history_init(manager_arguments.get_argument("reset_history"), manager_arguments.get_argument("history_chkpt_file"))
        # ---Verification mode run-------
        htdte_logger.set_collect_all_errors_mode()
        if not CFG["HPL"].get("verify_at_runtime", 0) and ("check" not in manager_arg_list or manager_arguments.get_argument("check")):
            for flow_id in flow_seq:
                htdte_logger.set_collect_all_erros_message_prefix(("Flow:%s[%d] ") % (_htd_flows_list[flow_id]["obj"].get_flow_type(), flow_id))
                __execute_flow(_htd_flows_list[flow_id]["obj"], manager_arg_list, True)
            if(htdte_logger.has_collected_errors()):
                htdte_logger.inform("**************One or more fatal errors discovered during verification*****************")
                htdte_logger.print_collected_errors()
                htdte_logger.inform("**************************************************************************************")
                sys.exit(257)
        htdte_logger.set_collect_all_erros_message_prefix("")
        htdte_logger.unset_collect_all_errors_mode()

        # ---------Actual flow run--------
        __history_init(manager_arguments.get_argument("reset_history"), manager_arguments.get_argument("history_chkpt_file"))
        GENERAL_SILENT_MODE = manager_arguments.get_argument("silent_mode")
        current_flow_ptr = None
        if CFG["HPL"].get("verify_at_runtime", 0):
            htdte_logger.set_collect_all_errors_mode()
        for flow_id in flow_seq:
            current_flow_ptr = _htd_flows_list[flow_id]["obj"]
            __execute_flow(_htd_flows_list[flow_id]["obj"], manager_arg_list, False)
        if(htdte_logger.has_collected_errors()):
            htdte_logger.inform("**************One or more fatal errors discovered during verification*****************")
            htdte_logger.print_collected_errors()
            htdte_logger.inform("**************************************************************************************")
            sys.exit(257)
        # -------------------------------------------------------
        htdte_logger.inform("**************Successfully Finish Execution*****************")
        htdte_logger.inform("End of sequence", HTD_PRINT_INTERFACE_ONLY)
        end_flow_time = time.time()
        htdte_logger.inform(("Execution time in seconds:%d") % (end_flow_time - start_flow_time))
        if(current_flow_ptr is not None and not CFG["HPL"].get("skip_history_file", 0)):
            htd_history_mgr.save_history(("Last Flow:%s[%d],Created at %s: ") % (
                current_flow_ptr.get_flow_type(), current_flow_ptr.get_flow_num(), time.time()))
        htdPlayer.close()
        HTD_STATISTICS_MGR.snoop_csv_file()
        if ("-sample_run" in sys.argv):
            sys.path.append("%s/HTDIndicatorManagement" % os.environ['HTD_TOOLS'])
            from htd_indicator_gen import *
            ind_obj = htd_indicator_gen()
            ind_obj.run()

# except SystemExit as e:
#    if e.code == 0:
#       raise  # normal exit, let unittest catch it
#    else:
#       sys.exit(257)
# except:
#    print ("Unexpected RUNTIME error happen, killing all subproccesses...\n")
#    traceback.print_exc()
#    for pid in HTD_subroccesses_pid_tracker_list:
#       try:
#	  print ("Killing PID %d ...\n") % (pid)
#	  os.kill(pid, 0)
#       except:
#	  pass
#    try:
#       htdte_logger.error("Unexpected RUNTIME error happen, killing all subproccesses...\n")
#    except:
#       pass
#    sys.exit(257)

sys.exit(0)
