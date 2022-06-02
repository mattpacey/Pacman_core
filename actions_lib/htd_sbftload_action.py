from htd_basic_action import *
from htd_utilities import *
from htd_collaterals import *
from htd_player_top import *
import re
import os
from os.path import basename
import time
# ---------------------------------------------
cpl_actions_init_tracking = {}

if ('cpl_logger' not in locals()):
    cpl_logger = Logger("htd_sbftload.log")
    #cpl_logger = htdte_logger


class SBFTLOAD(htd_base_action):
    SBFT_MODE_MLC = 0
    SBFT_MODE_SLC = 1
    SBFT_MODE_FCS = 2
    OUTPUT_FILE_NAME_L = {}

    def __init__(self, action_name, source_file, source_lineno, currentFlow, is_internal):
        htd_base_action.__init__(self, self.__class__.__name__, action_name, source_file, source_lineno, currentFlow, is_internal)
        self.arguments.set_argument("source", 1, "Specify which source for this action")
        self.arguments.declare_arg("input_file", ".obj input file's name .", "string", "", 1)
        self.arguments.declare_arg("sbft_mode", "The sbft mode: mlc|slc|fcs ", ["mlc", "slc", "fcs"], "mlc", 0)
        self.arguments.declare_arg("way_mask", "ways to be masked coded HEX", "int", 0, 0)
        self.arguments.declare_arg("pad", "padding length ", "int", 0, 0)
        self.arguments.declare_arg("pad_val", "padding value", "string", "00", 0)
        self.arguments.declare_arg("sbft_state", "mlc cache state", "string", "E", 0)
        self.arguments.declare_arg("number_of_caches", "number of cache slices (for fcs sbft)", "int", 1, 0)
        self.arguments.declare_arg("core0_only", "preload only core0", "bool", 1, 0)
        self.arguments.declare_arg("cpl2alfa_standalone", "execute cpl2alfa before iswat", "bool", 0, 0)
        self.arguments.declare_arg("spf_template", "set the spf template for iswat to print", "string", "", 0)
        self.arguments.declare_arg("fix_iswat", "execute fix_iswat script", "bool", 0, 0)
        self.arguments.declare_arg("fix_iswat_mclk04", "execute fix_iswat script", "bool", 0, 0)
        self.arguments.declare_arg("fix_iswat_bub", "fix_iswat bubble count", "int", 0, 0)
        self.arguments.declare_arg("fix_iswat_template", "fix_iswat mci mode", "string", "TWO_CHANNEL_IN", 0)
        self.arguments.declare_arg("fix_iswat_testtype", "fix_iswat testtype", "string", "", 0)
        self.arguments.declare_arg("fix_iswat_transform_only", "fix_iswat transform fix_only", [0, 1], 0, 0)
        self.arguments.declare_arg("express_mode", "preload using express mode", "bool", 0, 0)
        self.arguments.declare_arg("bfm_mode", "The bfm mode: injection_svtb|injection_te|stf|stf_serial|mci|mci_serial|tap|dynamic_cache_preload", [
                                   "injection_svtb", "injection_te", "stf", "stf_serial", "mci", "mci_serial", "tap", "dynamic_cache_preload"], "injection_svtb", 0)
        self.arguments.declare_arg("mci_config_ch", "The mci config - channels: ii (2 channels input)|io (1 channel input)", ["ii", "io"], "ii", 0)
        self.arguments.declare_arg("mci_config_freq", "The mci config - freq: 0:100|1:200|3:400 Mhz ", ["0", "1", "3"], "0", 0)
        self.arguments.declare_arg("run_post_proc", "run post processing tool - pp_ItppParser", "bool", 1, 0)
        self.arguments.declare_arg("pad_for_real_mode", "pad for real mode", "bool", 0, 0)
        self.arguments.declare_arg("dynamic_preload_en_padding", "enable padding or not", "bool", 0, 0)
        self.arguments.declare_arg("mci_serial_scan_pingroups", "scan pin groups in mci serial mode", "string", "", 0)
        self.arguments.declare_arg("cpl_method", "cpl_method param determines if use cepler or iswat", ["cepler", "iswat"], "iswat", 0)
        self.verify_flag = 0
        self.set_verify_mode = False
        self.output_file = ""
        self.sbft_modes = {"mlc": SBFTLOAD.SBFT_MODE_MLC, "slc": SBFTLOAD.SBFT_MODE_SLC, "fcs": SBFTLOAD.SBFT_MODE_FCS}
        self.template = ""

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
        if(os.environ.get('HTD_SBFT_CPL_LOCATION') is None):
            cpl_logger.error('Missing obligatory unix environment ENV[HTD_SBFT_CPL_LOCATION] - must point to to HTD CPL path')
       # if(os.environ.get('MODEL_SBFT_CPL_TABLE_LOCATION')==None):
       #     cpl_logger.error( 'Missing obligatory unix environment ENV[MODEL_SBFT_CPL_TABLE_LOCATION] - must point to to $CORE_ROOT/target/cte/core_te/gen/arraydft/l2r/mlc_cache path')
       # if(os.environ.get('HTD_SBFT_CPL_TRIGGER_SIGNAL')==None):
       #     cpl_logger.error( 'Missing obligatory unix environment ENV[HTD_SBFT_CPL_TRIGGER_SIGNAL] - sinst signal for triggering sv hvm sbft loading  ')
        if(os.environ.get('HTD_SBFT_CPL_OUTPUT_FILE_NAME') is None):
            cpl_logger.error('Missing obligatory unix environment ENV[HTD_SBFT_CPL_OUTPUT_FILE_NAME] - cpl default name ')

        input_file = re.split(r'\.', re.split(r'\/', self.arguments.get_argument("input_file"))[-1])[0] + ".obj"

        # check input file & geneate cpl collateral files name:
        # The input_file should be <TESTNAME>.obj
        # match = re.search('([a-zA-Z0-9_]+\.obj)', input_file)
        # Some tests have characters other than a-zA-Z0-9_ in their name

        file_basename = basename(input_file)

        # Make sure the file_basename is an obj file
        if (re.search(r'.+\.obj$', file_basename) is None):
            cpl_logger.error("Expecting an OBJ file (e.g. %s.obj) as input, not %s" % (os.getenv("TESTNAME"), file_basename))

        obj_file = file_basename
        cpl_file = re.sub(".obj", ".cpl", obj_file)

        # Check to see if CPL file already exists
        self.cpl_file_exists = 0
        self.check_for_cpl_file(cpl_file)

        if (not os.path.exists(input_file) and self.cpl_file_exists != 1):
            cpl_logger.error(("input file %s does not exist") % (input_file))

        output_file_name = ("%s%s") % (os.environ.get('HTD_SBFT_CPL_OUTPUT_FILE_NAME'), ("" if re.match(
            "injection", self.arguments.get_argument("bfm_mode")) else "." + CFG["HPL"]["execution_mode"]))
        temp_output_filename = ("%s%s") % (os.environ.get('HTD_SBFT_CPL_OUTPUT_FILE_NAME'), ("" if re.match(
            "injection", self.arguments.get_argument("bfm_mode")) else "." + CFG["HPL"]["execution_mode"]))

        self.verify_obligatory_arguments()
        tracking_key = ("%s_%s") % (htd_base_action.get_action_name(self), self.get_curr_flow().get_flow_num())
        cpl_logger.inform(("tracking key is:%s") % (tracking_key))
        if(tracking_key not in list(cpl_actions_init_tracking.keys())):
            cpl_actions_init_tracking[tracking_key] = 0

            # This is currently only used in the mci mode, but it is also valid for stf and maybe tap
        self.iswat_dir = "iswat_" + self.get_action_name() + "_" + self.arguments.get_argument("bfm_mode")

        if (not cpl_actions_init_tracking[tracking_key]):
            counter = 0
            while os.path.exists(temp_output_filename):
                counter = counter + 1
                temp_output_filename = output_file_name + "." + str(counter)
            SBFTLOAD.OUTPUT_FILE_NAME_L[tracking_key] = temp_output_filename
            cpl_logger.inform("SBFTLOAD.OUTPUT_FILE_NAME_L[%s]: %s" % (tracking_key, SBFTLOAD.OUTPUT_FILE_NAME_L[tracking_key]))

            # -------------------------------------INJECION-------------------------------------------------------------------
            if(self.arguments.get_argument("bfm_mode") == "injection_svtb" or self.arguments.get_argument("bfm_mode") == "injection_te"):
                self.output_file = re.sub(r'.obj', r'.txt', input_file)

                self.run_obj2image(input_file, cpl_file)
                self.run_image2inj(cpl_file)
                os.symlink(self.output_file, SBFTLOAD.OUTPUT_FILE_NAME_L[tracking_key])

                for line in open(self.output_file):
                    split_line = re.split(r"\s+", line)
                    cpl_logger.inform((" Verifying signal for cpl %s....") % (split_line[0]))
                    htdPlayer.hplSignalMgr.signal_exists(split_line[0])

                # --------------------------------------- MCI ---------------------------------------------------------------------
            elif (self.arguments.get_argument("bfm_mode") == "mci" or self.arguments.get_argument("bfm_mode") == "mci_serial"):
                self.output_file = self.get_output_file_name_mci(cpl_file)

                self.run_obj2image(input_file, cpl_file)
                cpl_logger.inform(self.arguments.get_argument("bfm_mode"))
                cpl_logger.inform(self.arguments.get_argument("cpl_method"))
                if self.arguments.get_argument("bfm_mode") == "mci":
                    cpl_logger.inform("output and cpl_file = %s" % (self.output_file))
                    cpl_logger.inform(self.arguments.get_argument("cpl_method"))
                    self.run_image2mci(cpl_file, "mci")
                else:
                    self.run_image2mci(cpl_file, "serial")
                # Flow integration
                self.run_flow_integ()
                os.symlink(self.output_file, SBFTLOAD.OUTPUT_FILE_NAME_L[tracking_key])
                SBFTLOAD.OUTPUT_FILE_NAME_L[tracking_key] = self.output_file  # mavindas

            # --------------------------------------- dynamic cache preloading ---------------------------------------------------------------------
            # --------------------------------------- TAP ---------------------------------------------------------------------
            elif (self.arguments.get_argument("bfm_mode") == "tap"):
                self.output_file = self.get_output_file_name_mci(cpl_file)

                self.run_obj2image(input_file, cpl_file)
                self.run_image2tap(cpl_file)

                # Flow integration
                self.run_flow_integ()
                os.symlink(self.output_file, SBFTLOAD.OUTPUT_FILE_NAME_L[tracking_key])
                SBFTLOAD.OUTPUT_FILE_NAME_L[tracking_key] = self.output_file  # mavindas

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
                                                                                         ("TRUE" if (self.arguments.get_argument(
                                                                                             "pad_for_real_mode") == 1) else "FALSE"),
                                                                                         self.arguments.get_argument("way_mask"),
                                                                                         ("TRUE" if (self.arguments.get_argument(
                                                                                             "core0_only") == 1) else "FALSE"),
                                                                                         self.arguments.get_argument("sbft_state"),
                                                                                         tmp_sbft_type,
                                                                                         ("TRUE" if (self.arguments.get_argument(
                                                                                             "dynamic_preload_en_padding") == 1) else "FALSE"),
                                                                                         "TRUE"))
                f.close()
                self.output_file = "dynamic_preload.txt"
                SBFTLOAD.OUTPUT_FILE_NAME_L[tracking_key] = self.output_file  # mavindas

            # ------------------------------- once more bfm_mode will be supported---------------------------------------------------------------
            else:
                cpl_logger.error(("Unsupported action bfm_mode:%s, SBFTLOAD action support only these bfm_mode: injection_svtb, injection(te) and mci") % (
                    self.arguments.get_argument("bfm_mode")))

            cpl_actions_init_tracking[tracking_key] = 1
            cpl_logger.inform("SBFTLOAD.OUTPUT_FILE_NAME_L[tracking_key]: %s" % (SBFTLOAD.OUTPUT_FILE_NAME_L[tracking_key]))
        else:
            self.output_file = SBFTLOAD.OUTPUT_FILE_NAME_L[tracking_key]

    def run(self):
        cpl_logger.inform(("      Running SBFTLOAD::run:%s:%s:%s:%d \n\n") % (htd_base_action.get_action_name(self),
                                                                              htd_base_action.get_action_type(self),
                                                                              htd_base_action.get_action_call_file(self),
                                                                              htd_base_action.get_action_call_lineno(self)))

        # napounde - this line only needs to be insertted in modes where the maintrace is a fsdb but the cache load sequence is still in an itpp file to be insertted by TVPV. For traces where the cache load is in the trace this might break vcf.  Needs to be re-visited
        #        htdPlayer.add_comment("vc2_api.insert_itpp_file(itpp_file=%s)" %(self.output_file))
        if(os.environ.get('HTD_COLLECT_RTL_SIGNALS_MODE') == "1"):
            return

        htdPlayer.hplSbftLoadMgr.set_mode(self.arguments.get_argument("bfm_mode"))

        cpl_logger.inform("Loading cache with file %s" % (self.output_file))

        htdPlayer.hpl_to_dut_interface.write_itpp_cmd("label: SBFTLoad_Start [Domain: ALL] ;")

        # scan_start and scan_stop support
        scan_mci_serial_pins = self.arguments.get_argument("mci_serial_scan_pingroups")
        scan_pins_l = scan_mci_serial_pins.split(",")

        if (self.arguments.get_argument("bfm_mode") == "mci_serial" and scan_mci_serial_pins != ""):
            htdPlayer.hpl_to_dut_interface.write_itpp_cmd("label: ChnlLnk_sbftloadstart [Domain: ALL] ;")
            htdPlayer.hpl_to_dut_interface.start_scan(scan_pins_l)

        htdPlayer.hplSbftLoadMgr.load_cache(self.output_file)

        if (self.arguments.get_argument("bfm_mode") == "mci_serial" and scan_mci_serial_pins != ""):
            htdPlayer.hpl_to_dut_interface.write_itpp_cmd("label: ChnlLnk_sbftloadstop [Domain: ALL] ;")
            htdPlayer.hpl_to_dut_interface.stop_scan(scan_pins_l)

        htdPlayer.hpl_to_dut_interface.write_itpp_cmd("label: SBFTLoad_End [Domain: ALL] ;")

    # ------------------------------- FUNCTIONS -----------------------------------------------------------------------------------------
    def run_image2inj(self, cpl_file):
        # if mlc sbft mode
        if (self.sbft_mode == SBFTLOAD.SBFT_MODE_MLC):
            command_line = ("%s/image2inj.py -f %s -p %s -d %s -o %s -s %s") % (os.environ.get('HTD_SBFT_CPL_LOCATION'), cpl_file, os.environ.get(
                'HTD_PROJ'), os.environ.get('MODEL_SBFT_CPL_MLC_TABLE_LOCATION'), self.output_file, os.environ.get('HTD_SBFT_CPL_NUM_OF_CORES'))
        else:  # else llc/fcs sbft mode
            if (os.environ.get('HTD_PROJ') == "icl"):
                command_line = ("%s/image2inj.py -f %s -p %s -d %s -o %s -s %s --llc  --override_dictionary_path /p/cdk/rtl/proj_tools/dft_sbft/latest/cpl_tools/dictionaries/ --override_dictionary_name dictionary_icl.bin -m fc") % (
                    os.environ.get('HTD_SBFT_CPL_LOCATION'), cpl_file, os.environ.get('HTD_PROJ'), os.environ.get('MODEL_SBFT_CPL_TABLE_LOCATION'), self.output_file, os.environ.get('HTD_SBFT_CPL_NUM_OF_CORES'))
            else:
                command_line = ("%s/image2inj.py -f %s -p %s -d %s -o %s -s %s -l") % (os.environ.get('HTD_SBFT_CPL_LOCATION'), cpl_file, os.environ.get(
                    'HTD_PROJ'), os.environ.get('MODEL_SBFT_CPL_TABLE_LOCATION'), self.output_file, os.environ.get('HTD_SBFT_CPL_NUM_OF_CORES'))
        sbftHand = subprocess.Popen(command_line, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        cpl_logger.inform("Running image2inj.py:")
        cpl_logger.inform(command_line)
        status = sbftHand.communicate()
        cpl_logger.inform(command_line)
        if (re.search("Error", str(status))):
            cpl_logger.error(("image2inj.py run did not finish correctly\n%s") % (status[len(status) - 1]))
        elif (re.search("ERROR", str(status)) or re.search("error", str(status))):  # this error found  in the printout
            cpl_logger.error(("image2inj.py run did not finish correctly\n%s") % (status[len(status) - 2]))
        else:
            cpl_logger.inform("image2inj.py run finish successfully\n")

    def run_image2mci(self, cpl_file, drive_mode):
        cpl_logger.inform(self.arguments.get_argument("cpl_method"))
        cpl_logger.inform("cpl_method = %s" % (self.arguments.get_argument("cpl_method")))
        command_line = ""
        if (self.arguments.get_argument("cpl_method") == "cepler"):
            return
        elif (self.arguments.get_argument("cpl_method") == "iswat"):
            # ISWAT
            # execute iswat & igo cmd
            if (self.sbft_mode == SBFTLOAD.SBFT_MODE_MLC):  # if mlc sbft mode
                if (os.environ.get('HTD_PROJ') == "icl"):
                    command_line = ("iswat -bypass_smart_rtl -array %s -sbft -xstate_xml %s -eval -run_mode offline -drive -drive_mode %s -format igo -dut %s -cpl2alfa %s -cpl_type mlc -bypass_cmd_ext -bypass_inst_sigs -gen_spf -outpath ./%s %s  -ip_name snc") % (os.environ.get('HTD_SBFT_ISWAT_MLC_ARRAY'), os.environ.get('HTD_SBFT_ISWAT_MLC_XSTATE_XML'), drive_mode, os.environ.get('HTD_SBFT_ISWAT_MLC_DUT'), cpl_file, self.iswat_dir, os.environ.get('HTD_SBFT_ISWAT_MLC_ADDITIONAL_SWITCHES'))
                    #command_line=("iswat -bypass_smart_rtl -array %s -sbft -xstate_xml %s -eval -run_mode offline -drive -drive_mode %s -format igo -dut %s -cpl2alfa %s -cpl_type mlc -bypass_cmd_ext -bypass_inst_sigs -gen_spf -outpath ./%s %s")%(os.environ.get('HTD_SBFT_ISWAT_MLC_ARRAY'), os.environ.get('HTD_SBFT_ISWAT_MLC_XSTATE_XML'), drive_mode, os.environ.get('HTD_SBFT_ISWAT_MLC_DUT') ,cpl_file, self.iswat_dir, os.environ.get('HTD_SBFT_ISWAT_MLC_ADDITIONAL_SWITCHES'))
                else:
                    command_line = ("iswat -bypass_smart_rtl -array %s -sbft -xstate_xml %s -eval -run_mode offline -drive -drive_mode %s -format igo -dut %s -cpl2alfa %s -cpl_type mlc -bypass_cmd_ext -bypass_inst_sigs -gen_spf -outpath ./%s %s") % (os.environ.get('HTD_SBFT_ISWAT_MLC_ARRAY'), os.environ.get('HTD_SBFT_ISWAT_MLC_XSTATE_XML'), drive_mode, os.environ.get('HTD_SBFT_ISWAT_MLC_DUT'), cpl_file, self.iswat_dir, os.environ.get('HTD_SBFT_ISWAT_MLC_ADDITIONAL_SWITCHES'))

                # DTS_32_fill_forSBFT_MLC_DAT_fc.spf - <testname>_<ISWAT_ARRAY>_<ISWAT_DUT>.spf
            else:  # else llc/fcs sbft mode
                command_line = ("iswat -bypass_smart_rtl -array %s -sbft -xstate_xml %s -no_compile_xstate -eval -run_mode offline -drive -drive_mode %s -format igo -dut %s -cpl2alfa %s -cpl_type llc -bypass_cmd_ext -bypass_inst_sigs -gen_spf -outpath ./%s %s") % (
                    os.environ.get('HTD_SBFT_ISWAT_LLC_ARRAY'), os.environ.get('HTD_SBFT_ISWAT_LLC_XSTATE_XML'), drive_mode, os.environ.get('HTD_SBFT_ISWAT_LLC_DUT'), cpl_file, self.iswat_dir, os.environ.get('HTD_SBFT_ISWAT_LLC_ADDITIONAL_SWITCHES'))

            self.run_iswat(cpl_file, command_line)

    def run_image2tap(self, cpl_file):
        command_line = ""
        # ISWAT
        # execute iswat & igo cmd
        if (self.sbft_mode == SBFTLOAD.SBFT_MODE_MLC):  # if mlc sbft mode
            command_line = ("iswat -array %s -sbft -xstate_xml %s -eval -run_mode offline -drive -drive_mode tap -format igo -dut %s -cpl2alfa %s -cpl_type mlc -bypass_cmd_ext -bypass_inst_sigs -gen_spf -outpath ./%s %s") % (
                os.environ.get('HTD_SBFT_ISWAT_MLC_ARRAY'), os.environ.get('HTD_SBFT_ISWAT_MLC_XSTATE_XML'), os.environ.get('HTD_SBFT_ISWAT_MLC_DUT'), cpl_file, self.iswat_dir, os.environ.get('HTD_SBFT_ISWAT_MLC_ADDITIONAL_SWITCHES'))

            # DTS_32_fill_forSBFT_MLC_DAT_fc.spf - <testname>_<ISWAT_ARRAY>_<ISWAT_DUT>.spf
        else:  # else llc/fcs sbft mode
            command_line = ("iswat -array %s -sbft -xstate_xml %s -no_compile_xstate -eval -run_mode offline -drive -drive_mode tap -format igo -dut %s -cpl2alfa %s -cpl_type llc -bypass_cmd_ext -bypass_inst_sigs -gen_spf -outpath ./%s %s") % (
                os.environ.get('HTD_SBFT_ISWAT_LLC_ARRAY'), os.environ.get('HTD_SBFT_ISWAT_LLC_XSTATE_XML'), os.environ.get('HTD_SBFT_ISWAT_LLC_DUT'), cpl_file, self.iswat_dir, os.environ.get('HTD_SBFT_ISWAT_LLC_ADDITIONAL_SWITCHES'))

        self.run_iswat(cpl_file, command_line)

    def run_iswat(self, cpl_file, command_line):

        if self.arguments.get_argument("cpl2alfa_standalone") == 1:
            cpl2alfa_type = "llc"
            if (self.sbft_mode == SBFTLOAD.SBFT_MODE_MLC):
                cpl2alfa_type = "mlc"

            iswat_path = util_toolconfig_get_tool_path("iswat")
            cpl2alfa_cmd = "%s/etc/cpl2alfa.pl -cpl %s -%s -outpath ./%s" % (iswat_path, cpl_file, cpl2alfa_type, self.iswat_dir)

            cpl_logger.inform("Running CPL2ALFA Command:")
            cpl_logger.inform(cpl2alfa_cmd)
            cpl2alfa_hand = subprocess.Popen(cpl2alfa_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            HTD_subroccesses_pid_tracker_list.append(cpl2alfa_hand.pid)
            status = cpl2alfa_hand.communicate()
            if (re.search("error", str(status)) or re.search("ERROR", str(status)) or cpl2alfa_hand.returncode != 0):
                cpl_logger.error(("cpl2alfa run did not finish correctly\n%s") % (str(status)))
            cpl_logger.inform("cpl2alfa run finish successfully\n")

        if (self.arguments.get_argument("spf_template") != ""):
            command_line = command_line + " -igo2spf_args mci_transform_name=%s" % (self.arguments.get_argument("spf_template"))

        cpl_logger.inform("Running iswat cmd:")
        cpl_logger.inform(command_line)
        sbftHand = subprocess.Popen(command_line, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=1)
        HTD_subroccesses_pid_tracker_list.append(sbftHand.pid)

        while sbftHand.poll() is None:
            iswat_line = sbftHand.stdout.readline()
            cpl_logger.inform("Iswat logging: %s" % str(iswat_line.rstrip('\n')))

        status = sbftHand.communicate()
        if (re.search("error", str(status)) or re.search("ERROR", str(status)) or sbftHand.returncode != 0):
            cpl_logger.error(("iswat run did not finish correctly\n%s") % (str(status)))
        cpl_logger.inform("iswat run finish successfully\n")

        iswat_path = "%s/%s" % (self.iswat_dir, self.spf_file)
        cpl_logger.inform("Making sbftload spf symlink: %s" % iswat_path)
        try:
            os.symlink(iswat_path, self.spf_file)
        except OSError:
            cpl_logger.error("Failed to make iswat spf symlink.")

        # call fix_iswat script.
        # $HTD_ROOT/tools/scripts/fix_iswat_spf.pl -spf htd_test_stimulus.spf -transform $template -bub $bub_cnt -sbft_type gt_llc
        if (self.arguments.get_argument("fix_iswat") != 0):
            fix_command_line = ("%s/tools/scripts/fix_iswat_spf.pl -spf %s -transform %s -bub %s -sbft_type %s -transform_only %d") % (os.environ.get('HTD_ROOT'), self.spf_file, self.arguments.get_argument(
                "fix_iswat_template"), self.arguments.get_argument("fix_iswat_bub"), self.arguments.get_argument("fix_iswat_testtype"), self.arguments.get_argument("fix_iswat_transform_only"))
            cpl_logger.inform("Running fix_iswat cmd:")
            cpl_logger.inform(fix_command_line)
            fixHand = subprocess.Popen(fix_command_line, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            HTD_subroccesses_pid_tracker_list.append(fixHand.pid)
            status = fixHand.communicate()
            if (re.search("error", str(status)) or re.search("ERROR", str(status)) or fixHand.returncode != 0 or re.search("No such file or directory", str(status))):
                cpl_logger.error(("fix_iswat run did not finish correctly\n%s") % (str(status)))
            cpl_logger.inform("fix_iswat run finish successfully\n")
        if (self.arguments.get_argument("fix_iswat_mclk04") != 0):
            #fix_command_line=("%s/tools/scripts/fix_spf_mclk04.pl -spf %s")%(os.environ.get('HTD_ROOT'),self.spf_file)
            fix_command_line = ("%s/tools/scripts/fix_spf_mclk04.pl -spf %s -transform %s -bub %s -sbft_type %s") % (os.environ.get('HTD_ROOT'), self.spf_file,
                                                                                                                     self.arguments.get_argument("fix_iswat_template"), self.arguments.get_argument("fix_iswat_bub"), self.arguments.get_argument("fix_iswat_testtype"))
            cpl_logger.inform("Running fix_iswat cmd:")
            cpl_logger.inform("Running fix_iswat cmd:")
            cpl_logger.inform(fix_command_line)
            fixHand = subprocess.Popen(fix_command_line, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            HTD_subroccesses_pid_tracker_list.append(fixHand.pid)
            status = fixHand.communicate()
            if (re.search("error", str(status)) or re.search("ERROR", str(status)) or fixHand.returncode != 0 or re.search("No such file or directory", str(status))):
                cpl_logger.error(("fix_iswat run did not finish correctly\n%s") % (str(status)))
            cpl_logger.inform("fix_iswat run finish successfully\n")

    def check_for_cpl_file(self, cpl_file):
        # if TID-specific CPL file exists, create soft link
        tid_cpl_file = re.sub(".cpl", ("_%s.cpl") % (os.environ.get('CATS_ID')), cpl_file)
        if (os.path.exists(tid_cpl_file)):
            cpl_logger.inform(("check_for_cpl_file has detected tid_cpl_file existance <%s> - creating a link to cpl_file <%s>") %
                              (tid_cpl_file, cpl_file))
            if (os.path.exists(cpl_file)):  # Seed takes priority so remove non-seed version prior to symlinking
                os.remove(cpl_file)
            os.symlink(tid_cpl_file, cpl_file)

        # if CPL file already exists, do not run force run obj2image but instead, use the existing CPL
        if (os.path.exists(cpl_file)):
            cpl_logger.inform(
                ("check_for_cpl_file has detected cpl_file existance certains checks and parts of conversion will be skipped cpl_file:  %s") % (cpl_file))
            self.cpl_file_exists = 1
            return

    def inplace_change(self, filename, old_string, new_string):
                # Safely read the input filename using 'with'
        with open(filename) as f:
            s = f.read()
            if old_string not in s:
                cpl_logger.error("old_string:%s not found in: %s" % (old_string, filename))
                return
        # Safely write the changed content, if found in the file
        with open(filename, 'w') as f:
            cpl_logger.inform("Changing Old_string: %s to new string: %s" % (old_string, new_string))
            s = s.replace(old_string, new_string)
            f.write(s)

    def run_obj2image(self, input_file, cpl_file):
        if (self.cpl_file_exists == 1):
            cpl_logger.inform("run_obj2image has detected cpl_file existance, run_obj2image will be skipped")
            return

        if(self.arguments.get_argument("sbft_mode") == "fcs" and (os.environ.get('FCS_LLC_BROADCAST_EN', None) is not None)):
                        # Harcoding slice mode for FCS broadcast mode
            command_line = ("%s/obj2image.pl -file %s -cpl -sbft_mode %s -sbft_state %s -way_mask %s -pad %s -pad_val %s -num_of_caches %s") % (os.environ.get('HTD_SBFT_CPL_LOCATION'), input_file, "slc",
                                                                                                                                                self.arguments.get_argument("sbft_state"), str(self.arguments.get_argument("way_mask")), str(self.arguments.get_argument("pad")), str(self.arguments.get_argument("pad_val")), str(self.arguments.get_argument("number_of_caches")))
        else:
            command_line = ("%s/obj2image.pl -file %s -cpl -sbft_mode %s -sbft_state %s -way_mask %s -pad %s -pad_val %s -num_of_caches %s") % (os.environ.get('HTD_SBFT_CPL_LOCATION'), input_file, self.arguments.get_argument("sbft_mode"),
                                                                                                                                                self.arguments.get_argument("sbft_state"), str(self.arguments.get_argument("way_mask")), str(self.arguments.get_argument("pad")), str(self.arguments.get_argument("pad_val")), str(self.arguments.get_argument("number_of_caches")))

        # Add extra args to obj2image if they exist
        if (not os.getenv("HTD_SBFT_CPL_EXTRA_ARGS", None) is None):
            command_line += " %s" % (os.getenv("HTD_SBFT_CPL_EXTRA_ARGS"))

        # The -new_version switch is required for more than 4 cores.
        if ((os.environ.get('HTD_PROJ') == "icl") or (self.arguments.get_argument("number_of_caches") > 4)):
            command_line += " -new_version"

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
            # quick fix for slice disable
            if ("IPs" in list(CFG.keys()) and "IA_CORES" in list(CFG['IPs'].keys()) and self.arguments.get_argument("sbft_mode") == "f"):
                if CFG['IPs']['IA_CORES'] == '2345':
                    self.inplace_change(cpl_file, "Dst_Id=0x2", "Dst_Id=0x4")
                    self.inplace_change(cpl_file, "Dst_Id=0x3", "Dst_Id=0x5")
                    self.inplace_change(cpl_file, "Dst_Id=0x0", "Dst_Id=0x2")
                    self.inplace_change(cpl_file, "Dst_Id=0x1", "Dst_Id=0x3")
                if CFG['IPs']['IA_CORES'] == '0145':
                    self.inplace_change(cpl_file, "Dst_Id=0x2", "Dst_Id=0x4")
                    self.inplace_change(cpl_file, "Dst_Id=0x3", "Dst_Id=0x5")
            cpl_logger.inform("obj2image.pl run finish successfully\n")  # FIXME: once more bfm_mode will be supported

    def run_flow_integ(self):

        if (CFG["HPL"]["execution_mode"] == "spf"):
            self.run_spf_action()
        else:
            self.run_spf2itpp()
            # else:
            #    cpl_logger.error("Don't know how to integrate load for execution_mode %s!\n"%(CFG["HPL"]["execution_mode"]))

    def run_spf2itpp(self):
        if (self.arguments.get_argument("bfm_mode") == "mci"
            and "SBFT_EXTRA_PADDING" in list(CFG["FlowGen"].keys())
                and CFG["FlowGen"]["SBFT_EXTRA_PADDING"] == 1):
            cpl_logger.inform("Padding spf sbft load\n")
            os.system('mv ' + self.spf_file + ' ' + self.spf_file + '.bak')
            os.system('cat ' + self.spf_file + '.bak ' + os.environ.get('HTD_ROOT') + '/tools/scripts/mci_nop_padding >> ' + self.spf_file)
        if(os.environ.get('HTD_CONTENT_TEMPLATE_OVRD') is None):
            self.template = os.environ.get('SPF_MCI_TEMPLATE_FILE')
        else:
            self.template = os.environ.get('HTD_CONTENT_TEMPLATE_OVRD')

        # exe spf2itpp cmd:
        if (self.sbft_mode == SBFTLOAD.SBFT_MODE_MLC):  # if mlc sbft mode
            command_line = ("%s/bin/spf --tapSpecFile %s --testSeqFile %s --itppFile %s --templateFile %s --mciSpecFile %s") % (os.environ.get('SPF_ROOT'),
                                                                                                                                os.environ.get('HTD_SPF_TAP_SPEC_FILE'), self.spf_file, self.itpp_file, self.template, os.environ.get('SPF_MCI_SPEC_FILE'))
        else:  # else llc/fcs sbft mode
            command_line = ("%s/bin/spf --tapSpecFile %s --testSeqFile %s --itppFile %s --templateFile %s --mciSpecFile %s") % (os.environ.get('SPF_ROOT'),
                                                                                                                                os.environ.get('HTD_SPF_TAP_SPEC_FILE'), self.spf_file, self.itpp_file, self.template, os.environ.get('SPF_MCI_SPEC_FILE'))
        cpl_logger.inform("Running spf cmd:")
        cpl_logger.inform(command_line)
        sbftHand = subprocess.Popen(command_line, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        HTD_subroccesses_pid_tracker_list.append(sbftHand.pid)
        status = sbftHand.communicate()
        # cpl_logger.inform(("%s\n%s\n")%(command_line,str(status)))
        if (re.search("error", str(status), flags=re.IGNORECASE)):
            cpl_logger.error(("spf run did not finish correctly\n%s") % (str(status)))
        cpl_logger.inform("spf run finish successfully\n")

        # post processing section:
        if (self.arguments.get_argument("run_post_proc")):
            command_line = ("%s/tools/scripts/pp_ItppParser.py  --file %s --new_file %s --project %s --mci_mode %s --mci_freq_clk '%s'") % (os.environ.get('HTD_ROOT'),
                                                                                                                                            self.itpp_file, self.output_file, os.environ.get('HTD_PROJ'), self.arguments.get_argument("mci_config_ch"), self.arguments.get_argument("mci_config_freq"))
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
        if (self.arguments.get_argument("cpl_method") == "cepler"):
            self.set_spf_file_cepler(cpl_file)
        elif (self.arguments.get_argument("cpl_method") == "iswat"):
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

    def set_spf_file_cepler(self, cpl_file):
        #  Get the base name of the test
        base_testname = re.sub(r'\.cpl', '', cpl_file)
        self.spf_file = "%s.spf" % (base_testname)
