from htd_sbftload_action import *


class SBFTLOAD_KBL(SBFTLOAD):
    def __init__(self, action_name, source_file, source_lineno, currentFlow, is_internal):
        SBFTLOAD.__init__(self, action_name, source_file, source_lineno, currentFlow, is_internal)
        self.arguments.declare_arg("sbft_mode", "The sbft mode: m|l|f", ["m", "l", "f"], "m", 0)
        self.sbft_modes = {"m": SBFTLOAD.SBFT_MODE_MLC, "l": SBFTLOAD.SBFT_MODE_SLC, "f": SBFTLOAD.SBFT_MODE_FCS}

    def run_image2inj(self, cpl_file):
        if (self.arguments.get_argument("sbft_mode") == "m"):  # if mlc sbft mode
            command_line = ("%s/image2inj_llc.py -f %s -d %s -o %s -s %s") % (os.environ.get('HTD_SBFT_CPL_LOCATION'), cpl_file, os.environ.get('HTD_SBFT_CPL_LOCATION'), self.output_file, os.environ.get('HTD_SBFT_CPL_NUM_OF_CORES'))
        else:  # else llc/fcs sbft mode
            command_line = ("%s/image2inj_llc.py -f %s -d %s -o %s -s %s -l") % (os.environ.get('HTD_SBFT_CPL_LOCATION'), cpl_file, os.environ.get('HTD_SBFT_CPL_LOCATION'), self.output_file, os.environ.get('HTD_SBFT_CPL_NUM_OF_CORES'))
        sbftHand = subprocess.Popen(command_line, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        status = sbftHand.communicate()
        htdte_logger.inform(command_line)
        if (re.search("Error", str(status))):
            htdte_logger.error(("image2inj.py run did not finish correctly\n%s") % (status[len(status) - 1]))
        elif (re.search("ERROR", str(status)) or re.search("error", str(status))):  # this error found  in the printout
            htdte_logger.error(("image2inj.py run did not finish correctly\n%s") % (status[len(status) - 2]))
        else:
            htdte_logger.inform("image2inj.py run finish successfully\n")

    def run_iswat(self, cpl_file, command_line):
        if (self.arguments.get_argument("sbft_mode") == "f"):
            new_path = "%s/iswat_chopper.py " % (os.environ.get('HTD_SBFT_CPL_LOCATION'))
            if ("HTD_SBFT_ISWAT_CHOPPER" in list(CFG["HPL"].keys()) and CFG["HPL"]["HTD_SBFT_ISWAT_CHOPPER"] == "FALSE"):
                htdte_logger.inform("Not using iswat chopper\n")
            else:
                htdte_logger.inform("Using iswat chopper\n")
                command_line = re.sub("^iswat ", new_path, command_line)
        SBFTLOAD.run_iswat(self, cpl_file, command_line)

    def set_spf_file_iswat(self, cpl_file):
        #  Get the base name of the test
        base_testname = re.sub(r'\.cpl', '', cpl_file)

        if (self.arguments.get_argument("sbft_mode") == "m"):  # if mlc sbft mode
            # DTS_32_fill_forSBFT_MLC_DAT_fc.spf - <testname>_<ISWAT_ARRAY>_<ISWAT_DUT>.spf
            self.spf_file = "%s_%s_%s.spf" % (base_testname, os.environ.get('HTD_SBFT_ISWAT_MLC_ARRAY'), os.environ.get('HTD_SBFT_ISWAT_MLC_DUT'))
        else:  # else llc/fcs sbft mode
            self.spf_file = "%s_%s_%s.spf" % (base_testname, os.environ.get('HTD_SBFT_ISWAT_LLC_ARRAY'), os.environ.get('HTD_SBFT_ISWAT_LLC_DUT'))
