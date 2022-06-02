from htd_basic_action import *
from htd_utilities import *
from htd_collaterals import *
from htd_player_top import *
import re
import os
from os.path import basename
import threading
from importlib import import_module
import subprocess
from shutil import copyfile
import multiprocessing
# ---------------------------------------------
cpl_actions_init_tracking = {}

if ('cpl_logger' not in locals()):
    cpl_logger = Logger("htd_uCPL.log")
    #cpl_logger = htdte_logger


def process_flow_py_file(threadID, filename, testname):
    fh = open("thread%d.log" % threadID, "w")
    sys.stderr = fh
    sys.stdout = fh
    output = "thread%s.spf" % threadID
    sys.path.append(os.getcwd())
    flow = import_module(filename.replace(".py", ""))
    flow_obj = getattr(flow, "CREATE_CPL_FLOW")
    pacman_obj = flow_obj(1)
    pacman_obj.flow_init()
    htdPlayer.hpl_to_dut_interface.logStream = open(output, "w", 1)
    htdPlayer.hpl_to_dut_interface.current_stream = htdPlayer.hpl_to_dut_interface.logStream
    htdPlayer.hpl_to_dut_interface.add_comment("--Thread%d for %s has Started---" % (threadID, testname))
    HTD_INFO.tap_info.__init__()
    HTD_INFO.stf_info.__init__()
    pacman_obj.flow_run()
    fh.close()


class UCPL(htd_base_action):
    SBFT_MODE_MLC = 0
    SBFT_MODE_SLC = 1
    SBFT_MODE_FCS = 2
    OUTPUT_FILE_NAME_L = {}

    def __init__(self, action_name, source_file, source_lineno, currentFlow, is_internal):
        htd_base_action.__init__(self, self.__class__.__name__, action_name, source_file, source_lineno, currentFlow, is_internal)
        self.arguments.set_argument("source", 1, "Specify which source for this action")
        self.arguments.declare_arg("input_file", ".32.obj or .obj input file's name .", "string", "", 1)
        #self.arguments.declare_arg("cpl_input_file"  ,".32.obj or .obj input file's name ." ,"string","",1 )
        self.arguments.declare_arg("sbft_mode", "The sbft mode: mlc|slc|fcs ", ["mlc", "slc", "fcs", "slc_burst"], "mlc", 0)
        self.arguments.declare_arg("engine", "The cpl type: ldat|hecl", ["ldat", "hecl"], "ldat", 0)
        self.arguments.declare_arg("way_mask", "ways to be masked coded HEX", "int", 0, 0)
        self.arguments.declare_arg("pad", "padding length ", "int", 0, 0)
        self.arguments.declare_arg("pad_val", "padding value", "string", "00", 0)
        self.arguments.declare_arg("sbft_state", "mlc cache state", "string", "E", 0)
        self.arguments.declare_arg("number_of_caches", "number of cache slices (for fcs sbft)", "int", 1, 0)
        self.arguments.declare_arg("core0_only", "preload only core0", "bool", 1, 0)
        self.arguments.declare_arg("express_mode", "preload using express mode", "bool", 0, 0)
        self.arguments.declare_arg("bfm_mode", "The bfm mode: injection_svtb|injection_te|stf|stf_serial|mci|mci_serial|tap|dynamic_cache_preload", ["injection_svtb", "injection_te", "stf", "stf_serial", "mci", "mci_serial", "tap", "dynamic_cache_preload", "stf2mci"], "injection_svtb", 0)
        self.arguments.declare_arg("mci_config_ch", "The mci config - channels: ii (2 channels input)|io (1 channel input)", ["ii", "io"], "ii", 0)
        self.arguments.declare_arg("mci_config_freq", "The mci config - freq: 0:100|1:200|3:400 Mhz ", ["0", "1", "3"], "0", 0)
        self.arguments.declare_arg("run_post_proc", "run post processing tool - pp_ItppParser", "bool", 1, 0)
        self.arguments.declare_arg("pad_for_real_mode", "pad for real mode", "bool", 0, 0)
        self.arguments.declare_arg("dynamic_preload_en_padding", "enable padding or not", "bool", 0, 0)
        self.arguments.declare_arg("thread_opt", "thread_opt", "bool", 0, 0)
        self.arguments.declare_arg("unload", "read/unload data written to cache memory through the specified engine", "bool", 0, 0)
        self.arguments.declare_arg("direct_spf", "generate cpl spf directly without pacman", "bool", 0, 0)
        self.verify_flag = 0
        self.set_verify_mode = False
        self.input_file = ""
        #self.cpl_input_file = ""
        self.output_file = ""
        self.sorted_file = ""
        self.cpl_file = ""
        self.ldat_py_file = ""
        self.hecl_py_file = ""
        self.inst_signal_inj = ""
        self.sbft_mlc_option = ""
        self.sbft_modes = {"mlc": UCPL.SBFT_MODE_MLC, "slc": UCPL.SBFT_MODE_SLC, "fcs": UCPL.SBFT_MODE_FCS}
        self.tracking_key = ""

    # ----------------------
    def get_action_not_declared_argument_names(self): pass
    # ----------------------

    def verify_arguments(self):

        cpl_logger.inform(("       Verifying %s::%s:%s:%d ....") % (htd_base_action.get_action_type(self),
                                                                    htd_base_action.get_action_name(self),
                                                                    htd_base_action.get_action_call_file(self),
                                                                    htd_base_action.get_action_call_lineno(self)))

        self.sbft_mode = self.sbft_modes[self.arguments.get_argument("sbft_mode")]

        if(os.environ.get('HTD_COLLECT_RTL_SIGNALS_MODE') == "1"):
            return
        HTD_INFO.verify_info_ui_existence(["signal_info"])
        # FIXME: need to enable for stf/mci HTD_INFO.verify_info_ui_existence(["cr_info"])

        # verify CPL env' variable from TE_cfg.xml:

        if(os.environ.get('VTTSTSRC') is None):
            cpl_logger.error('Missing obligatory unix environment ENV[VTTSTSRC] - must setup HDK environment. i.e. source /p/hdk/rtl/hdk.rc -cfg shdk74')

        if(os.environ.get('HTD_SBFT_UCPL_LOCATION') is None):
            cpl_logger.error('Missing obligatory unix environment ENV[HTD_SBFT_UCPL_LOCATION] - must point to HTD CPL path')

        if(os.environ.get('HTD_SBFT_CPL_TRIGGER_SIGNAL') is None):
            cpl_logger.error('Missing obligatory unix environment ENV[HTD_SBFT_CPL_TRIGGER_SIGNAL] - must provide Trigger signal for CPL/SLP handshake')
        else:
            self.inst_signal_inj = os.environ.get('HTD_SBFT_CPL_TRIGGER_SIGNAL')

        if(os.environ.get('HTD_SBFT_UCPL_MLC_OPTION') is None):
            cpl_logger.error('Missing obligatory unix environment ENV[HTD_SBFT_UCPL_MLC_OPTION] - must indicate the type on cache on the Core IP: L2 or MLC, needed for injections')
        else:
            self.sbft_mlc_option = os.environ.get('HTD_SBFT_UCPL_MLC_OPTION')

       # if(os.environ.get('HTD_SBFT_CPL_TRIGGER_SIGNAL')==None):
       #     cpl_logger.error( 'Missing obligatory unix environment ENV[HTD_SBFT_CPL_TRIGGER_SIGNAL] - sinst signal for triggering sv hvm sbft loading  ')
        if(os.environ.get('HTD_SBFT_CPL_OUTPUT_FILE_NAME') is None):
            cpl_logger.error('Missing obligatory unix environment ENV[HTD_SBFT_CPL_OUTPUT_FILE_NAME] - cpl default name ')

        if (re.search(".32.obj", str(self.arguments.get_argument("input_file")))):  # MAV
            self.input_file = re.split(r'\.', re.split(r'\/', self.arguments.get_argument("input_file"))[-1])[0] + ".32.obj"
        else:
            copyfile(os.environ['TESTNAME'], "%s/%s" % (os.getcwd(), os.path.basename(os.environ['TESTNAME'])))
            self.input_file = re.split(r'\.', re.split(r'\/', self.arguments.get_argument("input_file"))[-1])[0] + ".obj"

        # check input file & generate cpl collateral files name:
        match = re.search(r'([a-zA-Z0-9_]+[\.32]*\.obj)', self.input_file)
        obj_file = match.group(0)
        self.cpl_file = re.sub(".obj", ".cpl", obj_file)

        # Check to see if CPL file already exists
        self.cpl_file_exists = 0
        self.check_for_cpl_file(self.cpl_file)

        if (not os.path.exists(self.input_file) and self.cpl_file_exists != 1 and not self.dummy_mode):
            cpl_logger.error(("input file %s does not exist") % (self.input_file))

        output_file_name = ("%s%s") % (os.environ.get('HTD_SBFT_CPL_OUTPUT_FILE_NAME'), ("" if CFG["HPL"]["execution_mode"] == "itpp" else "." + CFG["HPL"]["execution_mode"]))
        temp_output_filename = ("%s%s") % (os.environ.get('HTD_SBFT_CPL_OUTPUT_FILE_NAME'), ("" if CFG["HPL"]["execution_mode"] == "itpp" else "." + CFG["HPL"]["execution_mode"]))

        self.verify_obligatory_arguments()
        self.tracking_key = ("%s_%s") % (htd_base_action.get_action_name(self), self.get_curr_flow().get_flow_num())
        cpl_logger.inform(("tracking key is:%s") % (self.tracking_key))
        if(self.tracking_key not in list(cpl_actions_init_tracking.keys())):
            cpl_actions_init_tracking[self.tracking_key] = 0

            # This is currently only used in the mci mode, but it is also valid for stf and maybe tap
#        self.iswat_dir = "iswat_"+self.get_action_name()+"_"+self.arguments.get_argument("bfm_mode")

        if self.dummy_mode:
            self.inform("%s running at dummy mode" % (self.__class__.__name__))
        elif (not cpl_actions_init_tracking[self.tracking_key]):
            counter = 0
            while os.path.exists(temp_output_filename):
                counter = counter + 1
                temp_output_filename = output_file_name + "." + str(counter)
            UCPL.OUTPUT_FILE_NAME_L[self.tracking_key] = temp_output_filename
            cpl_logger.inform("UCPL.OUTPUT_FILE_NAME_L[%s]: %s" % (self.tracking_key, UCPL.OUTPUT_FILE_NAME_L[self.tracking_key]))

            # -------------------------------------INJECION-------------------------------------------------------------------
            if(self.arguments.get_argument("bfm_mode") == "injection_svtb" or self.arguments.get_argument("bfm_mode") == "injection_te"):
                self.output_file = re.sub(r'.obj', r'.txt', self.input_file)

                self.run_obj2image(self.input_file, self.cpl_file)

             # --------------------------------------- MCI ---------------------------------------------------------------------
                # MAV - Commenting this out as MCI is not currently supported by UCPL
#            elif (self.arguments.get_argument("bfm_mode")=="mci" or self.arguments.get_argument("bfm_mode")=="mci_serial"):
#                self.output_file = self.get_output_file_name_mci(cpl_file)
#
#                self.run_obj2image(self.input_file,cpl_file)
#                if self.arguments.get_argument("bfm_mode")=="mci":
#		    self.run_image2mci(cpl_file, "mci")
#    	    	else:
#		    self.run_image2mci(cpl_file, "serial")
#                # Flow integration
#                self.run_flow_integ()
#                os.symlink(self.output_file, UCPL.OUTPUT_FILE_NAME_L[self.tracking_key])
#                UCPL.OUTPUT_FILE_NAME_L[self.tracking_key] = self.output_file # mavindas

            # --------------------------------------- dynamic cache preloading ---------------------------------------------------------------------
            # --------------------------------------- TAP ---------------------------------------------------------------------
                # MAV - Need to decide if the dynamic_cache_preload bfm mode should be removed as this is legacy only (SKL/KBL)
            elif (self.arguments.get_argument("bfm_mode") == "tap" or self.arguments.get_argument("bfm_mode") == "stf"):
                self.output_file = self.get_output_file_name_mci(self.cpl_file)

                self.run_obj2image(self.input_file, self.cpl_file)
#                self.run_image2tap(cpl_file)

                # Flow integration
                # self.run_flow_integ()  # MAV: What is this for??
                if os.path.lexists(UCPL.OUTPUT_FILE_NAME_L[self.tracking_key]):
                    os.remove(UCPL.OUTPUT_FILE_NAME_L[self.tracking_key])
                os.symlink(self.output_file, UCPL.OUTPUT_FILE_NAME_L[self.tracking_key])
                UCPL.OUTPUT_FILE_NAME_L[self.tracking_key] = self.output_file  # mavindas

            elif (self.arguments.get_argument("bfm_mode") == "dynamic_cache_preload"):
                if (self.arguments.get_argument("sbft_mode") == "m"):
                    tmp_sbft_type = "MLC"
                elif (self.arguments.get_argument("sbft_mode") == "l"):
                    tmp_sbft_type = "SLC_LLC"
                elif (self.arguments.get_argument("sbft_mode") == "f"):
                    tmp_sbft_type = "FC_LLC"

                f = open('dynamic_preload.txt', 'w')
                f.write(("rem: run_cache_preload %s %s %s %s %s %s %s %s %s %s %s ;") % (self.arguments.get_argument("pad"),
                                                                                         "TRUE",
                                                                                         "TRUE",
                                                                                         os.environ.get('TESTNAME'),
                                                                                         ("TRUE" if (self.arguments.get_argument("pad_for_real_mode") == 1) else "FALSE"),
                                                                                         self.arguments.get_argument("way_mask"),
                                                                                         ("TRUE" if (self.arguments.get_argument("core0_only") == 1) else "FALSE"),
                                                                                         self.arguments.get_argument("sbft_state"),
                                                                                         tmp_sbft_type,
                                                                                         ("TRUE" if (self.arguments.get_argument("dynamic_preload_en_padding") == 1) else "FALSE"),
                                                                                         "TRUE"))
                f.close()
                self.output_file = "dynamic_preload.txt"
                UCPL.OUTPUT_FILE_NAME_L[self.tracking_key] = self.output_file  # mavindas

            # ------------------------------- once more bfm_mode will be supported---------------------------------------------------------------
            else:
                cpl_logger.error(("Unsupported action bfm_mode:%s, UCPL action support only these bfm_mode: injection_svtb, injection(te) and mci") % (self.arguments.get_argument("bfm_mode")))

            cpl_actions_init_tracking[self.tracking_key] = 1
            cpl_logger.inform("UCPL.OUTPUT_FILE_NAME_L[self.tracking_key]: %s" % (UCPL.OUTPUT_FILE_NAME_L[self.tracking_key]))
        else:
            self.output_file = UCPL.OUTPUT_FILE_NAME_L[self.tracking_key]

    def run(self):
        cpl_logger.inform(("      Running UCPL::run:%s:%s:%s:%d \n\n") % (htd_base_action.get_action_name(self),
                                                                          htd_base_action.get_action_type(self),
                                                                          htd_base_action.get_action_call_file(self),
                                                                          htd_base_action.get_action_call_lineno(self)))

        # napounde - this line only needs to be insertted in modes where the maintrace is a fsdb but the cache load sequence is still in an itpp file to be insertted by TVPV. For traces where the cache load is in the trace this might break vcf.  Needs to be re-visited
        #        htdPlayer.add_comment("vc2_api.insert_itpp_file(itpp_file=%s)" %(self.output_file))
        test_name = os.path.basename(self.input_file).replace(".obj", "")
        if(os.environ.get('HTD_COLLECT_RTL_SIGNALS_MODE') == "1"):
            return
        if(self.arguments.get_argument("bfm_mode") != "stf"):
            htdPlayer.hplSbftLoadMgr.set_mode(self.arguments.get_argument("bfm_mode"))
            cpl_logger.inform("          Loading cache with file %s" % (self.output_file))
#        htdPlayer.hplSbftLoadMgr.load_cache(self.output_file)  # MAV: Temporarily commenting this out,  this is need to set up the instrumentation signal for preload handshake

        if(self.arguments.get_argument("bfm_mode") == "tap" or self.arguments.get_argument("bfm_mode") == "stf"):
            if(self.arguments.get_argument("engine") == "ldat"):
                self.ldat_py_file = re.sub(r'.obj', r'_ldat.py', self.input_file)
                if (self.sbft_mode == UCPL.SBFT_MODE_MLC):
                    cpl_logger.inform(" Creating TAP programming sequence for Cache Preloading ...")
                    if (not os.path.exists(self.ldat_py_file)):
                        cpl_logger.error(("File <%s> not found!!") % (self.ldat_py_file))
                    else:
                        cpl_logger.inform((" Processing file <%s> ...") % (self.ldat_py_file))
                        if(self.arguments.get_argument("direct_spf")):
                            spf_file = "%s_intermediate.spf" % test_name
                            try:
                                fh = open(spf_file)
                            except BaseException:
                                cpl_logger.error("Cannot open %s" % spf_file)
                            else:
                                spf_lines = fh.readlines()
                                fh.close()
                            for line in spf_lines:
                                params = {}
                                params["op"] = "SPF"
                                params["strvalue"] = line
                                self.get_curr_flow().exec_action(params, "GEN", self.__class__.__name__, 0, "DIRECT_SPF_CRATION")

                        elif(self.arguments.get_argument("thread_opt")):
                            thread_counter = 0
                            threads = []
                            for file in os.listdir('.'):
                                matchline = re.match(r"%s_ldat_th(\d+)\.py$" % test_name, file)
                                if(matchline):
                                    thread = multiprocessing.Process(target=process_flow_py_file, args=(int(matchline.groups()[0]), file, test_name))
                                    threads.append(thread)
                                    thread_counter = thread_counter + 1
                            for thread in threads:
                                thread.start()

                            # Wait for all of them to finish
                            for thread in threads:
                                thread.join()

                            for counter in range(0, thread_counter):
                                file = "thread%s.spf" % (counter)
                                if("thread" in file and "spf" in file):
                                    spf_file = open(file)

                                    for line in spf_file.readlines():
                                        if "CREATE_HECL_FLOW" not in line:
                                            params = {}
                                            params["op"] = "SPF"
                                            params["strvalue"] = line
                                            self.get_curr_flow().exec_action(params, "GEN", self.__class__.__name__, 0, "CPL_MULTI_TH")

                        else:
                            self.process_ldat_py_file(self.ldat_py_file)  # EJSANTIL HERE CALL THE LDAT
            else:
                self.hecl_py_file = re.sub(r'.obj', r'_hecl.py', self.input_file)
                if ((self.sbft_mode == UCPL.SBFT_MODE_SLC) or (self.sbft_mode == UCPL.SBFT_MODE_FCS)):
                    cpl_logger.inform(" Creating TAP programming sequence for Cache Preloading ...")
                    if (not os.path.exists(self.hecl_py_file)):
                        cpl_logger.error(("File <%s> not found!!") % (self.hecl_py_file))
                    else:
                        cpl_logger.inform((" Processing file <%s> ...") % (self.hecl_py_file))
                        if(self.arguments.get_argument("direct_spf")):
                            spf_file = "%s_intermediate.spf" % test_name
                            try:
                                fh = open(spf_file)
                            except BaseException:
                                cpl_logger.error("Cannot open %s" % spf_file)
                            else:
                                spf_lines = fh.readlines()
                                fh.close()
                            for line in spf_lines:
                                params = {}
                                params["op"] = "SPF"
                                params["strvalue"] = line
                                self.get_curr_flow().exec_action(params, "GEN", self.__class__.__name__, 0, "DIRECT_SPF_CRATION")

                        elif(self.arguments.get_argument("thread_opt")):
                            thread_counter = 0
                            # Get all files
                            threads = []
                            for file in os.listdir('.'):
                                matchline = re.match(r"%s_hecl_th(\d+)\.py$" % test_name, file)
                                if(matchline):
                                    thread = multiprocessing.Process(target=process_flow_py_file, args=(int(matchline.groups()[0]), file, test_name))
                                    threads.append(thread)
                                    thread_counter = thread_counter + 1

                            for thread in threads:
                                thread.start()
                            # Wait for all of them to finish
                            for thread in threads:
                                thread.join()
                            for counter in range(0, thread_counter):
                                file = "thread%s.spf" % counter
                                if("thread" in file and "spf" in file):
                                    spf_file = open(file)

                                    for line in spf_file.readlines():
                                        if "CREATE_HECL_FLOW" not in line:
                                            params = {}
                                            params["op"] = "SPF"
                                            params["strvalue"] = line
                                            self.get_curr_flow().exec_action(params, "GEN", self.__class__.__name__, 0, "CPL_MULTI_TH")

                        else:

                            self.process_hecl_py_file(self.hecl_py_file)  # EJSANTIL HERE CALL THE HECL

        if(self.arguments.get_argument("bfm_mode") == "injection_svtb" or self.arguments.get_argument("bfm_mode") == "injection_te"):
            if (self.sbft_mode == UCPL.SBFT_MODE_MLC):
                if (self.sbft_mlc_option == "MLC"):
                    self.run_image2inj(self.cpl_file)
                elif (self.sbft_mlc_option == "L2"):
                    self.run_l2_preload(self.cpl_file)

                # if (os.path.exists(UCPL.OUTPUT_FILE_NAME_L[self.tracking_key])): #Remove old file if exists prior to symlinking
                #    os.remove(UCPL.OUTPUT_FILE_NAME_L[self.tracking_key])
                #os.symlink(self.output_file, UCPL.OUTPUT_FILE_NAME_L[self.tracking_key])
                self.sorted_file = open(self.output_file)

                for line in sorted(self.sorted_file.readlines()):
                    split_line = re.split(r"\s+", line)
                    cpl_logger.inform((" Verifying signal for cpl %s....") % (split_line[0]))
                    htdPlayer.hplSignalMgr.signal_exists(split_line[0])

                    params = {}
                    params["actionName"] = "CPL_Injection"
                    params["op"] = "SET"
                    params[split_line[0]] = split_line[1]
                    self.get_curr_flow().exec_action(params, "SIG", self.__class__.__name__, 0, self.get_action_name())

            if ((self.sbft_mode == UCPL.SBFT_MODE_SLC) or (self.sbft_mode == UCPL.SBFT_MODE_FCS)):
                if (os.path.exists("htd_test_stimulus.cpl")):
                    os.remove("htd_test_stimulus.cpl")
                os.symlink(self.cpl_file, "htd_test_stimulus.cpl")

                params = {}
                params["actionName"] = "Wait3tclk"
                params["op"] = "WAIT"
                params["waitcycles"] = 3
                params["refclock"] = "tclk"
                params["postalignment"] = 0
                params["postdelay"] = 0
                self.get_curr_flow().exec_action(params, "GEN", self.__class__.__name__, 0, self.get_action_name())

                params = {}
                params["actionName"] = "Wait_CPL_SLP_Alive"
                params["op"] = "WAIT"
                params[self.inst_signal_inj] = 0x01471
                params["waitcycles"] = 50
                params["refclock"] = "tclk"
                self.get_curr_flow().exec_action(params, "SIG", self.__class__.__name__, 0, self.get_action_name())

                params = {}
                params["actionName"] = "Init_CPL_Handshake"
                params["op"] = "FORCE"
                params[self.inst_signal_inj] = 0x01474
                self.get_curr_flow().exec_action(params, "SIG", self.__class__.__name__, 0, self.get_action_name())

                params = {}
                params["actionName"] = "Wait1tclk"
                params["op"] = "WAIT"
                params["waitcycles"] = 1
                params["refclock"] = "tclk"
                params["postalignment"] = 0
                params["postdelay"] = 0
                self.get_curr_flow().exec_action(params, "GEN", self.__class__.__name__, 0, self.get_action_name())

                params = {}
                params["actionName"] = "Wait_CPL_SLP_Done"
                params["op"] = "WAIT"
                params[self.inst_signal_inj] = 0x01475
                params["waitcycles"] = 600
                params["refclock"] = "tclk"
                self.get_curr_flow().exec_action(params, "SIG", self.__class__.__name__, 0, self.get_action_name())

                params = {}
                params["actionName"] = "Init_CPL_Handshake"
                params["op"] = "FORCE"
                params[self.inst_signal_inj] = 0x01476
                self.get_curr_flow().exec_action(params, "SIG", self.__class__.__name__, 0, self.get_action_name())

                params = {}
                params["actionName"] = "Wait1tclk"
                params["op"] = "WAIT"
                params["waitcycles"] = 1
                params["refclock"] = "tclk"
                params["postalignment"] = 0
                params["postdelay"] = 0
                self.get_curr_flow().exec_action(params, "GEN", self.__class__.__name__, 0, self.get_action_name())

                params = {}
                params["actionName"] = "Release_CPL_Handshake"
                params["op"] = "UNFORCE"
                params[self.inst_signal_inj] = 0x01476
                self.get_curr_flow().exec_action(params, "SIG", self.__class__.__name__, 0, self.get_action_name())

    # ------------------------------- FUNCTIONS -----------------------------------------------------------------------------------------

    def run_image2inj(self, cpl_file):
        if (self.sbft_mode == UCPL.SBFT_MODE_MLC):  # if mlc sbft mode
            command_line = ("%s/dft_sbft_icl/image2inj_snc.py -f %s -d %s -o %s") % (os.environ.get('HTD_SBFT_UCPL_LOCATION'), cpl_file, os.environ.get('MODEL_SBFT_CPL_SERVER_TABLE_LOCATION'), self.output_file)
        else:  # else llc/fcs sbft mode
            cpl_logger.error("image2inj_snc.py only supports MLC. LLC is supported via SLP\n")
            #command_line=("%s/image2inj.py -f %s -d %s -o %s -s %s -l")%(os.environ.get('HTD_SBFT_UCPL_LOCATION') ,cpl_file, os.environ.get('HTD_SBFT_UCPL_LOCATION'), self.output_file, os.environ.get('HTD_SBFT_CPL_NUM_OF_CORES'))
        sbftHand = subprocess.Popen(command_line, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        cpl_logger.inform("Running image2inj_snc.py:")
        cpl_logger.inform(command_line)
        status = sbftHand.communicate()
        cpl_logger.inform(command_line)
        if (re.search("Error", str(status))):
            cpl_logger.error(("image2inj_snc.py run did not finish correctly\n%s") % (status[len(status) - 1]))
        elif (re.search("ERROR", str(status)) or re.search("error", str(status))):  # this error found  in the printout
            cpl_logger.error(("ipp_ItppParsermage2inj.py run did not finish correctly\n%s") % (status[len(status) - 2]))
        else:
            cpl_logger.inform("image2inj.py run finish successfully\n")

    def run_l2_preload(self, cpl_file):
        if (self.sbft_mode == UCPL.SBFT_MODE_MLC):  # if mlc sbft mode
            command_line = ("%s/knh/knhcpu/scripts/l2_preload/l2_preload.pl %s -f txt -top \"\" -s . | grep -v \"^#\" | awk '{if (NF) {print $1 \" \" $3}}' > %s") % (os.environ.get('VTTSTSRC'), cpl_file, self.output_file)
            # command_line=("%s/l2_preload.pl %s -f txt -top \"\" -s . | grep -v \"^#\" | awk '{if (NF) {print $1 \" \" $3}}' > %s")%(os.environ.get('HTD_SBFT_UCPL_LOCATION') ,cpl_file, self.output_file)
        else:  # else llc/fcs sbft mode
            cpl_logger.error("l2_preload.pl only supports L2. LLC is supported via SLP\n")

        sbftHand = subprocess.Popen(command_line, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        cpl_logger.inform("Running l2_preload.pl:")
        cpl_logger.inform(command_line)
        status = sbftHand.communicate()
        cpl_logger.inform(command_line)
        if (re.search("Error", str(status))):
            cpl_logger.error(("l2_preload.pl run did not finish correctly\n%s") % (status[len(status) - 1]))
        elif (re.search("ERROR", str(status)) or re.search("error", str(status))):  # this error found  in the printout
            cpl_logger.error(("l2_preload.pl run did not finish correctly\n%s") % (status[len(status) - 2]))
        else:
            cpl_logger.inform("l2_preload.pl run finish successfully\n")

    def run_image2mci(self, cpl_file, drive_mode):
        command_line = ""
        # ISWAT
        # execute iswat & igo cmd
       # if (self.sbft_mode == UCPL.SBFT_MODE_MLC):   #if mlc sbft mode
       #    command_line=("iswat -bypass_smart_rtl -array %s -sbft -xstate_xml %s -eval -run_mode offline -drive -drive_mode %s -format igo -dut %s -cpl2alfa %s -cpl_type mlc -bypass_cmd_ext -bypass_inst_sigs -gen_spf -outpath ./%s %s")%(os.environ.get('HTD_SBFT_ISWAT_MLC_ARRAY'), os.environ.get('HTD_SBFT_ISWAT_MLC_XSTATE_XML'), drive_mode, os.environ.get('HTD_SBFT_ISWAT_MLC_DUT') ,cpl_file, self.iswat_dir, os.environ.get('HTD_SBFT_ISWAT_MLC_ADDITIONAL_SWITCHES'))
       #
       #    # DTS_32_fill_forSBFT_MLC_DAT_fc.spf - <testname>_<ISWAT_ARRAY>_<ISWAT_DUT>.spf
       # else:                                                   #else llc/fcs sbft mode
       #    command_line=("iswat -bypass_smart_rtl -array %s -sbft -xstate_xml %s -no_compile_xstate -eval -run_mode offline -drive -drive_mode %s -format igo -dut %s -cpl2alfa %s -cpl_type llc -bypass_cmd_ext -bypass_inst_sigs -gen_spf -outpath ./%s %s")%(os.environ.get('HTD_SBFT_ISWAT_LLC_ARRAY'), os.environ.get('HTD_SBFT_ISWAT_LLC_XSTATE_XML'), drive_mode, os.environ.get('HTD_SBFT_ISWAT_LLC_DUT'), cpl_file, self.iswat_dir, os.environ.get('HTD_SBFT_ISWAT_LLC_ADDITIONAL_SWITCHES'))
       #
       #self.run_iswat(cpl_file, command_line)

    def run_image2tap(self, cpl_file):
        command_line = ""
        # ISWAT
        # execute iswat & igo cmd
       # if (self.sbft_mode == UCPL.SBFT_MODE_MLC):   #if mlc sbft mode
       #    command_line=("iswat -array %s -sbft -xstate_xml %s -eval -run_mode offline -drive -drive_mode tap -format igo -dut %s -cpl2alfa %s -cpl_type mlc -bypass_cmd_ext -bypass_inst_sigs -gen_spf -outpath ./%s %s")%(os.environ.get('HTD_SBFT_ISWAT_MLC_ARRAY'), os.environ.get('HTD_SBFT_ISWAT_MLC_XSTATE_XML'), os.environ.get('HTD_SBFT_ISWAT_MLC_DUT') ,cpl_file, self.iswat_dir, os.environ.get('HTD_SBFT_ISWAT_MLC_ADDITIONAL_SWITCHES'))
       #
       #    # DTS_32_fill_forSBFT_MLC_DAT_fc.spf - <testname>_<ISWAT_ARRAY>_<ISWAT_DUT>.spf
       # else:                                                   #else llc/fcs sbft mode
       #    command_line=("iswat -array %s -sbft -xstate_xml %s -no_compile_xstate -eval -run_mode offline -drive -drive_mode tap -format igo -dut %s -cpl2alfa %s -cpl_type llc -bypass_cmd_ext -bypass_inst_sigs -gen_spf -outpath ./%s %s")%(os.environ.get('HTD_SBFT_ISWAT_LLC_ARRAY'), os.environ.get('HTD_SBFT_ISWAT_LLC_XSTATE_XML'), os.environ.get('HTD_SBFT_ISWAT_LLC_DUT'), cpl_file, self.iswat_dir, os.environ.get('HTD_SBFT_ISWAT_LLC_ADDITIONAL_SWITCHES'))
       #
       #self.run_iswat(cpl_file, command_line)

    # def run_iswat(self, cpl_file, command_line):
    #    cpl_logger.inform("Running iswat cmd:")
    #    cpl_logger.inform(command_line)
    #    sbftHand = subprocess.Popen(command_line, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    #    HTD_subroccesses_pid_tracker_list.append(sbftHand.pid)
    #    status = sbftHand.communicate()
    #    if ( re.search("error",str(status)) or re.search("ERROR",str(status)) or sbftHand.returncode != 0):
    #        cpl_logger.error(("iswat run did not finish correctly\n%s")%(str(status)))
    #    cpl_logger.inform("iswat run finish successfully\n")
    #
    #    # Copy the spf file for tracesaver purposes
    #    cpl_logger.inform("Copying sbftload spf file:")
    #    command_line = "cp %s/%s ."%(self.iswat_dir, self.spf_file)
    #    cpl_logger.inform(command_line)
    #    cpHand = subprocess.Popen(command_line, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    #    HTD_subroccesses_pid_tracker_list.append(cpHand.pid)
    #    status = cpHand.communicate()
    #    if (cpHand.returncode != 0):
    #        cpl_logger.error("could not copy spf file!")
    #    cpl_logger.inform("copy sbftload spf file finish successfully\n")

    def check_for_cpl_file(self, cpl_file):
        # if TID-specific CPL file exists, create soft link
        tid_cpl_file = re.sub(".cpl", ("_%s.cpl") % (os.environ.get('CATS_ID')), cpl_file)
        if (os.path.exists(tid_cpl_file)):
            cpl_logger.inform(("check_for_cpl_file has detected tid_cpl_file existance <%s> - creating a link to cpl_file <%s>") % (tid_cpl_file, cpl_file))
            if (os.path.exists(cpl_file)):  # Seed takes priority so remove non-seed version prior to symlinking
                os.remove(cpl_file)
            os.symlink(tid_cpl_file, cpl_file)

        # if CPL file already exists, do not run force run obj2image but instead, use the existing CPL
        if (os.path.exists(cpl_file)):
            cpl_logger.inform(("check_for_cpl_file has detected cpl_file existance certains checks and parts of conversion will be skipped cpl_file:  %s") % (cpl_file))
            self.cpl_file_exists = 1
            return

    def process_ldat_py_file(self, ldat_py_file):
        ldat_file = open(self.ldat_py_file)
#        params = {}
#        params["actionName"] = "Sdat_Write"
#        params["reg"] = "Sdat"
#        params["scope"] = "core/ml2"
#        params["STAGE_EN"] = 0x0
#        params["STREAM_EN"] = 0x0
#        params["DWORD"] = 0x0
#        params["BANKSEL"] = 0x0
#        params["MPMAP"] = 0x0
#        params["REP"] = 0x0
#        params["RSVD"] = 0x0
#        params["ARRAYSEL"] = 0x0
#        params["ADDR_LIM"] = 0x0
#        params["SHADOW"] = 0x0
#        params["MPBOFFSET"] = 0x0
#        params["CMP"] = 0x0
#        params["MODE"] = 0x1
#        params["check"] = 0
#        params["read_modify_write"] = 0
#        params["bfm_mode"] = "tap"
#        self.get_curr_flow().exec_action(params,"XREG",self.__class__.__name__,0,self.get_action_name())

#        params = {}
#        params["actionName"] = "DATIN2_Write"
#        params["reg"] = "DATIN2"
#        params["scope"] = "core/ml6"
#        params["DATIN"] = 0x00000000FECF93E0
#        params["check"] = 0
#        params["read_modify_write"] = 0
#        params["bfm_mode"] = "tap"
#        self.get_curr_flow().exec_action(params,"XREG",self.__class__.__name__,0,self.get_action_name())

        for line in ldat_file.readlines():
            tmp_cmd_list = re.search(r'self.exec_xreg_action\({(.+?)}\)', line)
            if tmp_cmd_list:
                cmd_list = re.sub("\"", "", tmp_cmd_list.group(1))
                cmdline = cmd_list.split(',')
                params = {}
                for item in cmdline:
                    cmd_pair = item.split(':')
                    params[cmd_pair[0]] = cmd_pair[1]
                params["scope"] = CFG["LDATScopes"][params["reg"]]
                if "DATIN" in params["reg"]:
                    params["DATIN"] = int(params["DATIN"], 16)
                self.get_curr_flow().exec_action(params, "XREG", self.__class__.__name__, 0, self.get_action_name())
                cpl_logger.inform(("Cmd found %s....") % (item))
                cmdline = ""
        ldat_file.close()

    def process_hecl_py_file(self, hecl_py_file):
        cpl_logger.inform("I reached hecl file def\n")
        hecl_file = open(self.hecl_py_file)
        for line in hecl_file.readlines():
            tmp_cmd_list_hecl = re.search(r'self.exec_xreg_action\({(.+?)}\)', line)
            if tmp_cmd_list_hecl:
                cmd_list_hecl = re.sub("\"", "", tmp_cmd_list_hecl.group(1))
                cmdline_hecl = cmd_list_hecl.split(',')
                params = {}
                for item_hecl in cmdline_hecl:
                    cmd_pair_hecl = item_hecl.split(':')
                    params[cmd_pair_hecl[0]] = cmd_pair_hecl[1]
                params["scope"] = CFG["HECLScopes"][params["reg"]]

                self.get_curr_flow().exec_action(params, "XREG", self.__class__.__name__, 0, params["actionName"])
                #cpl_logger.inform( ("Cmd found %s....")%(item))

                cmdline = ""
        hecl_file.close()

    def run_obj2image(self, input_file, cpl_file):
        if (self.cpl_file_exists == 1):
            cpl_logger.inform("run_obj2image has detected cpl_file existance, run_obj2image will be skipped")
            return

        if(self.arguments.get_argument("unload")):
            cpl_logger.inform("Unloading mode is active\n")
            unload_mode = "-unload"
        else:
            unload_mode = ""
        if(self.arguments.get_argument("engine") == "ldat"):
            cpl_logger.inform("I am in ldat mode\n")
            bfm_mode = self.arguments.get_argument("bfm_mode")
            if(bfm_mode == "stf"):
                bfm_mode = "stf2mci"
            command_line = ("%s/obj2image.pl -file %s -obj -die %s -sbft_mode %s -sbft_state %s -way_mask %s -bpad %s -pad %s -num_of_caches %s -bfm_mode %s") % (os.environ.get('HTD_SBFT_UCPL_LOCATION'), input_file, os.environ.get('HTD_SBFT_UCPL_SEGMENT'), self.arguments.get_argument("sbft_mode"), self.arguments.get_argument("sbft_state"), str(self.arguments.get_argument("way_mask")), str(self.arguments.get_argument("pad")), str(self.arguments.get_argument("pad")), str(self.arguments.get_argument("number_of_caches")), str(bfm_mode))
            if(bfm_mode == "stf2mci"):
                bfm_mode = "stf"
            sbftHand = subprocess.Popen(command_line, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            cpl_logger.inform("Running obj2image.pl:")
            cpl_logger.inform(command_line)
            HTD_subroccesses_pid_tracker_list.append(sbftHand.pid)
            status = sbftHand.communicate()
            if (re.search(r"compilation\s+errors", str(status)) or re.search("ERROR", str(status)) or re.search(r"compilation\s+aborted", str(status))):
                cpl_logger.error(("obj2image.pl run did not finish correctly\n%s") % (status[len(status) - 1]))
            elif (re.search("-E-", str(status))):  # this error found  in the printout
                cpl_logger.error(("obj2image.pl run did not finish correctly\n%s") % (status[len(status) - 2]))
            else:
                cpl_logger.inform("obj2image.pl run finish successfully\n")  # FIXME: once more bfm_mode will be supported

            if(self.arguments.get_argument("thread_opt")):
                command_line = ("%s/ldat4cpl.pm -file %s -die %s -sbft_mode %s -sbft_state %s -num_of_caches %s -cfg %s -engine %s -bfm_mode %s -thread_opt 1 %s") % (os.environ.get('HTD_SBFT_UCPL_LOCATION'), cpl_file, os.environ.get('HTD_SBFT_UCPL_SEGMENT'), self.arguments.get_argument("sbft_mode"), self.arguments.get_argument("sbft_state"), str(self.arguments.get_argument("number_of_caches")), os.environ.get('HTD_SBFT_CPL_DEF_FILE_PATH'), self.arguments.get_argument("engine"), str(self.arguments.get_argument("bfm_mode")), unload_mode)
            else:
                command_line = ("%s/ldat4cpl.pm -file %s -die %s -sbft_mode %s -sbft_state %s -num_of_caches %s -cfg %s -engine %s -bfm_mode %s %s") % (os.environ.get('HTD_SBFT_UCPL_LOCATION'), cpl_file, os.environ.get('HTD_SBFT_UCPL_SEGMENT'), self.arguments.get_argument("sbft_mode"), self.arguments.get_argument("sbft_state"), str(self.arguments.get_argument("number_of_caches")), os.environ.get('HTD_SBFT_CPL_DEF_FILE_PATH'), self.arguments.get_argument("engine"), str(self.arguments.get_argument("bfm_mode")), unload_mode)

            sbftHand = subprocess.Popen(command_line, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            cpl_logger.inform("Running ldat4cpl.pm:")
            cpl_logger.inform(command_line)
            HTD_subroccesses_pid_tracker_list.append(sbftHand.pid)
            status = sbftHand.communicate()
        else:
            cpl_logger.inform("I am in hecl mode\n")
            optm_cpl_file = re.sub(".cpl", ".optm.cpl", cpl_file)
            command_line = ("%s/obj2image.pl -file %s -obj -die %s -sbft_mode %s -sbft_state %s -way_mask %s -bpad %s -pad %s -num_of_caches %s -bfm_mode %s") % (os.environ.get('HTD_SBFT_UCPL_LOCATION'), input_file, os.environ.get('HTD_SBFT_UCPL_SEGMENT'), self.arguments.get_argument("sbft_mode"), self.arguments.get_argument("sbft_state"), str(self.arguments.get_argument("way_mask")), str(self.arguments.get_argument("pad")), str(self.arguments.get_argument("pad")), str(self.arguments.get_argument("number_of_caches")), str(self.arguments.get_argument("bfm_mode")))
            sbftHand = subprocess.Popen(command_line, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            cpl_logger.inform("Running obj2image.pl:")
            cpl_logger.inform(command_line)
            HTD_subroccesses_pid_tracker_list.append(sbftHand.pid)
            status = sbftHand.communicate()
            if (re.search(r"compilation\s+errors", str(status)) or re.search("ERROR", str(status)) or re.search(r"compilation\s+aborted", str(status))):
                cpl_logger.error(("obj2image.pl run did not finish correctly\n%s") % (status[len(status) - 1]))
            elif (re.search("-E-", str(status))):  # this error found  in the printout
                cpl_logger.error(("obj2image.pl run did not finish correctly\n%s") % (status[len(status) - 2]))
            else:
                cpl_logger.inform("obj2image.pl run finish successfully\n")  # FIXME: once more bfm_mode will be supported

            if(self.arguments.get_argument("thread_opt")):
                command_line = ("%s/hecl4cpl.pm -file %s -die %s -sbft_mode %s -sbft_state %s -num_of_caches %s -cfg %s -engine %s -bfm_mode %s -th_opt %s") % (os.environ.get('HTD_SBFT_UCPL_LOCATION'), optm_cpl_file, os.environ.get('HTD_SBFT_UCPL_SEGMENT'), self.arguments.get_argument("sbft_mode"), self.arguments.get_argument("sbft_state"), str(self.arguments.get_argument("number_of_caches")), os.environ.get('HTD_SBFT_CPL_HECL_DEF_FILE_PATH'), self.arguments.get_argument("engine"), str(self.arguments.get_argument("bfm_mode")), unload_mode)
            else:
                command_line = ("%s/hecl4cpl.pm -file %s -die %s -sbft_mode %s -sbft_state %s -num_of_caches %s -cfg %s -engine %s -bfm_mode %s %s") % (os.environ.get('HTD_SBFT_UCPL_LOCATION'), optm_cpl_file, os.environ.get('HTD_SBFT_UCPL_SEGMENT'), self.arguments.get_argument("sbft_mode"), self.arguments.get_argument("sbft_state"), str(self.arguments.get_argument("number_of_caches")), os.environ.get('HTD_SBFT_CPL_HECL_DEF_FILE_PATH'), self.arguments.get_argument("engine"), str(self.arguments.get_argument("bfm_mode")), unload_mode)

            sbftHand = subprocess.Popen(command_line, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            cpl_logger.inform("Running hecl4cpl.pm:")
            cpl_logger.inform(command_line)
            HTD_subroccesses_pid_tracker_list.append(sbftHand.pid)
            status = sbftHand.communicate()

    def run_flow_integ(self):

        if (CFG["HPL"]["execution_mode"] == "spf"):
            self.run_spf_action()
        else:
            self.run_spf2itpp()
            # else:
            #    cpl_logger.error("Don't know how to integrate load for execution_mode %s!\n"%(CFG["HPL"]["execution_mode"]))

    def run_spf2itpp(self):
        # exe spf2itpp cmd:
        if (self.sbft_mode == UCPL.SBFT_MODE_MLC):  # if mlc sbft mode
            command_line = ("%s/bin/spf --tapSpecFile %s --testSeqFile %s --itppFile %s --templateFile %s --mciSpecFile %s") % (os.environ.get('SPF_ROOT'), os.environ.get('HTD_SPF_TAP_SPEC_FILE'), self.spf_file, self.itpp_file, os.environ.get('SPF_MCI_TEMPLATE_FILE'), os.environ.get('SPF_MCI_SPEC_FILE'))
        else:  # else llc/fcs sbft mode
            command_line = ("%s/bin/spf --tapSpecFile %s --testSeqFile %s --itppFile %s --templateFile %s --mciSpecFile %s") % (os.environ.get('SPF_ROOT'), os.environ.get('HTD_SPF_TAP_SPEC_FILE'), self.spf_file, self.itpp_file, os.environ.get('SPF_MCI_TEMPLATE_FILE'), os.environ.get('SPF_MCI_SPEC_FILE'))
        cpl_logger.inform("Running spf cmd:")
        cpl_logger.inform(command_line)
        sbftHand = subprocess.Popen(command_line, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        HTD_subroccesses_pid_tracker_list.append(sbftHand.pid)
        status = sbftHand.communicate()
        # cpl_logger.inform(("%s\n%s\n")%(command_line,str(status)))
        if (re.search("error", str(status), flags=re.IGNORECASE)):
            cpl_logger.error(("spf run did not finish correctly\n%s") % (str(status)))
        cpl_logger.inform("spf run finish successfully\n")

        # psot processing section:
        if (self.arguments.get_argument("run_post_proc")):
            command_line = ("%s/tools/scripts/pp_ItppParser.py  --file %s --new_file %s --project %s --mci_mode %s --mci_freq_clk '%s'") % (os.environ.get('HTD_ROOT'), self.itpp_file, self.output_file, os.environ.get('HTD_PROJ'), self.arguments.get_argument("mci_config_ch"), self.arguments.get_argument("mci_config_freq"))
            cpl_logger.inform("Run pp_ItppParser.py:")
            cpl_logger.inform(command_line)
            sbftHand = subprocess.Popen(command_line, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            HTD_subroccesses_pid_tracker_list.append(sbftHand.pid)
            status = sbftHand.communicate()
            cpl_logger.inform(("%s\n%s\n") % (command_line, str(status)))
            if (re.search("error", str(status), flags=re.IGNORECASE)):
                cpl_logger.error(("pp_ItppParser.py run did not finish correctly\n%s") % (str(status)))
            cpl_logger.inform("pp_ItppParser.py run finish successfully\n")

    def run_spf_action(self):
        # Setup the params
        params = {}
        params["spf_file"] = self.spf_file

        # execute a spf action
        #        self.get_curr_flow().exec_action(params, "SPF", self.__class__.__name__, 0, self.get_action_name())

        # Execute happens later, just need to set the output file
        self.output_file = self.spf_file

    def get_output_file_name_mci(self, cpl_file):
        self.set_spf_file_iswat(cpl_file)

        # Check what flow integration mode this is
        if (CFG["HPL"]["execution_mode"] == "spf"):
            return self.spf_file
        else:
            self.itpp_file = re.sub(r'\.spf$', r'.itpp', self.spf_file)

            if (self.arguments.get_argument("run_post_proc")):
                return re.sub(r'\.itpp$', r'_pp.itpp', self.itpp_file)
            else:
                return self.itpp_file

    def set_spf_file_iswat(self, cpl_file):
        #  Get the base name of the test
        base_testname = re.sub(r'\.cpl', '', cpl_file)

        if (self.arguments.get_argument("sbft_mode") == "mlc"):  # if mlc sbft mode
            # DTS_32_fill_forSBFT_MLC_DAT_fc.spf - <testname>_<ISWAT_ARRAY>_<ISWAT_DUT>.spf
            self.spf_file = "%s_%s_%s.spf" % (base_testname, os.environ.get('HTD_SBFT_ISWAT_MLC_ARRAY'), os.environ.get('HTD_SBFT_ISWAT_MLC_DUT'))
        else:  # else llc/fcs sbft mode
            self.spf_file = "%s_%s_%s.spf" % (base_testname, os.environ.get('HTD_SBFT_ISWAT_LLC_ARRAY'), os.environ.get('HTD_SBFT_ISWAT_LLC_DUT'))
