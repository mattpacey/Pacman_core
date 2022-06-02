from htd_utilities import *
from htd_collaterals import *
from htd_hpl_not_interactive_interface import *
from itertools import count, groupby
import re

# ----------------------------
# Base xdp interface class
# ----------------------------
xdp_instr_table = []
# ------------------------------------------------------------------------------------------------------------------------------------


class hpl_xdp_interface(hpl_not_interactive_interface):
    def __init__(self, filename, uiptr, stream=None):
        self.silent_stream = open("SilentModeStream", "w", 1)
        htdte_logger.inform("Creating Silent Mode activity Stream file:SilentModeStream")
        if (stream is None):
            self.file_name = filename
            self.logStream = open(self.file_name, "w", 1)
            htdte_logger.inform(("Creating XDP file:%s") % (self.file_name))
            self.__isstream = 0

            # ---Add function
            self.logStream.write("def pcodeless():\n")

            # ---Add header
            self.print_header(
                "***********************************HEADER XDP**********************************************/n")
            for l in htdte_logger.get_header():
                self.print_header(l)
            self.print_header(
                "***************************************************************************************/n")
            if(os.environ.get("XDP_MODE") != "pythonsv"):
                self.logStream.write(" import itpii                        # load DAL\n")
                self.logStream.write(" itp = itpii.baseaccess()\n")
                #self.logStream.write(" from itpii.datatypes import *\n")
                self.logStream.write(" import sys\n")
            else:
                self.logStream.write(" \n\
 print \"pythonsv pcodeless flow: ported from HVM by alexey.chinkov@intel.com\"\n\
 from common import baseaccess\n\
 import __main__\n\
 cpu = __main__.cpu\n\
 \n\
 def refreshPySV():\n\
   print \"refreshing\"\n\
 \n\
 import itpii                        # load DAL\n\
 itp = itpii.baseaccess()\n\
 #from itpii.datatypes import *\n\
 import sys\n\
 import time\n\
 \n\
 itp.nolog()\n\
 \n\
 if (baseaccess.getaccess() == \"stub\") :\n\
   refresh = refreshPySV \n\
   DEBUG = True\n\
   TIMEOUT = 0\n\
 else:\n\
   refresh = __main__.refresh\n\
   DEBUG = False\n\
   TIMEOUT = 1\n\
   tm = time.localtime()\n\
   suffix = \"%d_%d_%d_%d_%d_%d\" %(tm.tm_year,tm.tm_mon,tm.tm_mday,tm.tm_hour,tm.tm_min,tm.tm_sec);\n\
   _SAVE_PATH = r\"C:\\temp\\pcodeless_\"\n\
   print \"Saving trace to \", _SAVE_PATH\n\
   filename = _SAVE_PATH +suffix+ \".log\";\n\
   itp.log(filename)\n\
 \n\
 \n")
                self.refresh_command = "\
 counter = 0\n\
 agent = %s\n\
 irname = \"%s\"\n\
 while(not hasattr(agent,irname)):\n\
   if (counter == 0): \n\
     refresh() ### achinkov \n\
   else: \n\
     itp.wait(1) \n\
   counter = counter + 1 \n\
   print \"waiting.. \", agent._name, counter, hasattr(agent,irname) \n\
 \n"

        else:
            self.file_name = ""
            self.logStream = stream
            self.__isstream = 1

        self.current_stream = self.logStream
        self.uiptr = uiptr
        self.interface_debug_mode = True if (
            "InterfaceDebugMode" in list(CFG["HPL"].keys()) and CFG["HPL"]["InterfaceDebugMode"] in ["1", "True",
                                                                                               "TRUE"]) else False
        self.silent_mode = 0
        self.tap_ctrl_hndlr_var_l = []
   # --------------------------------

    def tap_compression_off(self): pass  # - Tap Compression off - self.logStream.write("no_compress: start;\n")

    def tap_compression_on(self): pass  # - Tap compression on - self.logStream.write("no_compress: stop;\n")

    def tap_command_low_level_mode_enabled(self): return False
   # ------------------------------------------------------------------------------------------------------------------------------------

    def print_header(self, line):
        no_new_lines = line.split('\n')
        for l in no_new_lines:
            if (len(l)):
                self.logStream.write(("# %s\n") % (l))

   # ------------------------------------------------------------------------------------------------------------------------------------
    def insert_line(self, line):
        no_new_lines = line.split('\n')
        for l in no_new_lines:
            if (len(l)):
                self.logStream.write(("#Itpp Line insert - %s\n") % (l))

   # ------------------------------------------------------------------------------------------------------------------------------------
    def close(self):
        if (not self.__isstream):
            self.logStream.close()

    # -----Silent mode , the stream is redirected to another file-----------------------
    # ------------------------------------------------------------------------------------------------------------------------------------
    def set_silent_mode(self):
        self.logStream = self.silent_stream
        self.silent_mode = 1

   # ------------------------------------------------------------------------------------------------------------------------------------
    def unset_silent_mode(self):
        self.logStream = self.current_stream
        self.silent_mode = 0
   # ------------------------------------------------------------------------------------------------------------------------------------

    def get_model_time(self):
        return -1
   # ------------------------------------------------------------------------------------------------------------------------------------

    def send_action(self, line):
        if (not self.uiptr.silent_mode and not self.uiptr.current_action.get_curr_flow().is_verification_mode()):
            self.logStream.write(line)

   # ------------------------------------------------------------------------------------------------------------------------------------
    def add_comment(self, line):
        if (self.uiptr.silent_mode):
            return
        no_new_lines = line.split('\n')
        for l in no_new_lines:
            if (len(l)):
                self.logStream.write((" print (\"comment: %s\")\n") % (l.replace("rem:", "")))
   # ------------------------------------------------------------------------------------------------------------------------------------

    def set_pattern_info(self, message):
        if (self.uiptr.silent_mode):
            return
        no_new_lines = message.split('\n')
        for l in no_new_lines:
            self.logStream.write((" print \"PatInfo: %s\"\n") % (l))

   # ------------------------------------------------------------------------------------------------------------------------------------
    def signal_unforce(self, full_path):
        if (self.uiptr.silent_mode):
            return
        self.logStream.write((" print \"release_signal %s\"") % (full_path))
   # ------------------------------------------------------------------------------------------------------------------------------------

    def signal_peek(self, full_path, value=-1):
        if (self.uiptr.silent_mode):
            return
        if (value < 0):
            self.logStream.write((" print \"peek_signal %s \";") % (full_path))
        else:
            self.logStream.write((" print \"peek_signal %s 0x%x\";") % (full_path, value))
   # ------------------------------------------------------------------------------------------------------------------------------------

    def signal_poke(self, full_path, value):
        if (self.uiptr.silent_mode):
            return
        if(isinstance(value, int)):
            self.logStream.write((" print \"deposit_signal %s 0x%x \";") % (full_path, value))
        elif(value == "x"):
            self.logStream.write((" print \"deposit_signal %s x \";") % (full_path))
        elif(value == "z"):
            self.logStream.write((" print \"deposit_signal %s z \";") % (full_path))
        else:
            htdte_logger.error(("Illegal signal value type :%s") % (value))

   # ------------------------------------------------------------------------------------------------------------------------------------
    def check_signal(self, full_path, value):
        if (self.uiptr.silent_mode):
            return
        self.logStream.write((" print \"peek_signal  %s 0x%x\";") % (full_path, value))
   # ------------------------------------------------------------------------------------------------------------------------------------

    def check_signal_not(self, full_path, value): pass

   # ------------------------------------------------------------------------------------------------------------------------------------
    def signal_exists(self, full_path):
        return True

    # -------Need ITPP EXTENSIONS----------------------
    def signal_force(self, full_path, value):
        if (self.uiptr.silent_mode):
            return
        if(isinstance(value, int)):
            self.logStream.write((" print \"force_signal %s 0x%x \";") % (full_path, value))
        elif(value == "x"):
            self.logStream.write((" print \"force_signal %s x \";") % (full_path))
        elif(value == "z"):
            self.logStream.write((" print \"force_signal %s z \";") % (full_path))
        else:
            htdte_logger.error(("Illegal signal value type :%s") % (value))

   # ------------------------------------------------------------------------------------------------------------------------------------
    def signal_set(self, full_path, value):
        if (not isinstance(value, int) and not isinstance(value, int) and value not in ["x", "X", "z", "Z"]):
            htdte_logger.error(("Improper value type received : expected int , while got:%s") % (type(value)))
        if(isinstance(value, int)):
            self.logStream.write((" print \"deposit_signal %s 0x%x \";") % (full_path, value))  # TODO - Check with Rob if this applicable also for DP!!!
        elif(value == "x"):
            self.logStream.write((" print \"deposit_signal %s x \";") % (full_path))
        elif(value == "z"):
            self.logStream.write((" print \"deposit_signal %s z \";") % (full_path))
        else:
            htdte_logger.error(("Illegal signal value type :%s") % (value))

   # ------------------------------------------------------------------------------------------------------------------------------------
    def ext_signalset_poke(self, signal_l, signal_values_l, delay=-1):
        if("xdp_pin_table" not in list(CFG.keys())):
            htdte_logger.error("Missing \"xdp_pin_table\" - definition in TE_cfg.xml . ")
        if (not isinstance(signal_l, list)):
            htdte_logger.error("Wrong \"signal_l\" argument type: expected list of signals . ")
        if (not isinstance(signal_values_l, list)):
            htdte_logger.error("Wrong \"signal_values_l\" argument type: expected list of expected signal values . ")
        if (len(signal_l) != len(signal_values_l)):
            htdte_logger.error(("Error in  \"signal_values_l\" vs' \"signal_l\" arguments assignment , expected same list size , while len(\"signal_values_l\")=%d,len(\"signal_l\")=%d . ") % (len(signal_values_l), len(signal_l)))
        sigs_entry = ""
        for i in range(0, len(signal_l)):
            if(signal_l[i] not in list(CFG["xdp_pin_table"].keys())):
                htdte_logger.error(("Can't match XDP pin name by TE logic name -  \"%s\" in CFG[\"xdp_pin_table\"] - definition in TE_cfg.xml . ") % (signal_l[i]))
            str_val = ((" %s\n") % (CFG["xdp_pin_table"][signal_l[i]])) % (int(signal_values_l[i]))
            self.logStream.write(str_val)

   # ------------------------------------------------------------------------------------------------------------------------------------
    def signal_wait(self, full_path, value, wait_time):
        self.logStream.write(("# itp.sleep(1) #signal_wait: %s=%d (wait %d pS)") % (full_path, value, wait_time))

        # if (type(full_path) != list):
        #       self.logStream.write(
        #            (" print \"poll_signal  %s 0x%x %d %s;\"") % (full_path, value, wait_time, CFG["HTD_Clocks_Settings"]["sim_time_unit"]))
        # else:
        #    for sig in full_path:
        #            self.logStream.write(
        #                (" print \"poll_signal  %s 0x%x %d %s;\"") % (sig, value, wait_time, CFG["HTD_Clocks_Settings"]["sim_time_unit"]))
   # ------------------------------------------------------------------------------------------------------------------------------------
    def wait_clock_num(self, width, clock):
        period_orig_clock = self.uiptr.hplClockMgr.get_clock_period(clock)
        period_vec_clock = self.uiptr.hplClockMgr.get_clock_period(CFG["HPL"]["PatVecClock"])
        NumOfVecClocks = int(math.ceil(width * period_orig_clock / (period_vec_clock if(period_vec_clock > 0) else 1)))
        if(NumOfVecClocks < 0):
            NumOfVecClocks = 1
        self.logStream.write(("# itp.sleep(1) #delay: %s(%d)") % (self.uiptr.hplClockMgr.get_clock_rtl_path(CFG["HPL"]["PatVecClock"]), NumOfVecClocks))
        #self.logStream.write(("vector: xxtms(0),%d;\n") % (NumOfVecClocks))

   # ------------------------------------------------------------------------------------------------------------------------------------
    def wait_clock_edge(self, clock, edge):
        # FIXME:bring me back
        #self.logStream.write(("rem:   wait_clock_edge:   %s:%s;\n")%(clock,edge))
        return
   # ------------------------------------------------------------------------------------------------------------------------------------

    def wait_tick(self):
        # FIXME:bring me back
        #self.logStream.write(("rem:   wait_clock_edge:   %s:%s;\n")%(clock,edge))
        return
   # ------------------------------------------------------------------------------------------------------------------------------------

    def wait_clock_modulo(self, clock, modulo): pass
    # --If this clock is not modulo vector - error on DP
    # FIXME:bring me back
    #self.logStream.write(("rem:   wait_clock_edge:   %s:%d;\n")%(clock,modulo))
    #self.logStream.write(("rem: comment: MODULO TVPV TODO;\n"))

   # ------------------------------------------------------------------------------------------------------------------------------------
    def write_itpp_cmd(self, cmd):
        # if (self.uiptr.silent_mode):
        #    return
        self.logStream.write((" print \"%s\"") % (cmd))

    # --------Tap Parameters instrumental printout-------
   # ------------------------------------------------------------------------------------------------------------------------------------
    def tap_parameters_instrumetal_print(self, irname, agent, parallel_mode, assigned_fields, attributes, labels, masks,
                                         strobe, capture, tdolabels): pass
   # ------------------------------------------------------------------------------------------------------------------------------------

    def label(self, label):
        if (self.uiptr.silent_mode):
            return
        self.logStream.write((" print \"label: %s \";") % (label))
   # ------------------------------------------------------------------------------------------------------------------------------------

    def to_tap_state(self, to_state):
        # if( self.uiptr.current_action.get_curr_flow().is_verification_mode()):return
        # self.logStream.write((" itp.msgdr(msgHandle,32,None,None,None,None,%s) #?????????? Need to be modified ") % (to_state))
        #htdte_logger.error(("\"to_tap_state\"- statement not supported yet in this interface  "))
        self.logStream.write((" print \"to_tap_state: %s \";") % (to_state))
   # ------------------------------------------------------------------------------------------------------------------------------------

    def high_level_tap_bfm_transactor(self, irname, ircode, irsize, drsize, agent, dr_by_fields, dr_read_byfields, dri, dro, parallel, labels, mask, capture, read_bitmap, pscand_en, pscand_delay, pscand_pins, shadow_agents="", postfocus_delay=0):
        if("xdp_tapcontroller_handler" not in list(CFG.keys())):
            htdte_logger.error(("Missing TAP controller handler string in CFG[\"xdp_tapcontroller_handler\"]"))
        # ------------------------------
        active_agents_l = []
        parallel_tap_agents = HTD_INFO.tap_info.get_taplink_parallel_agents_by_agents(agent)
        if(len(parallel_tap_agents) == 1 and re.search("no instances for", parallel_tap_agents[0])):
            parallel_tap_agents = [agent]
        for agnt in parallel_tap_agents:
            if(agnt not in list(CFG["xdp_tapcontroller_handler"].keys())):
                htdte_logger.error(("Missing TAP controller handler string in CFG[\"xdp_tapcontroller_handler\"][\"%s\"]") % (agnt))
            curr_tap_handler = CFG["xdp_tapcontroller_handler"][agnt]
            # -----------------------------------------
            reg_handler = ("%s.%s") % (curr_tap_handler, irname)
            # ----------------------------------
            if(agent not in xdp_instr_table):
                xdp_instr_table.append(agent)
                if(os.environ.get("XDP_MODE") == "pythonsv"):
                    #import pdb; pdb.set_trace()
                    self.logStream.write((self.refresh_command) % (curr_tap_handler, dict_tapxml_info[agent]["register"][irname]["full_name"].lower()))
            # ----------------------------------

            if(os.environ.get("XDP_MODE") == "pythonsv"):
                if((agnt in list(dict_tapxml_info.keys())) and irname in list(dict_tapxml_info[agnt]["register"].keys()) and "full_name" in list(dict_tapxml_info[agnt]["register"][irname].keys())):
                    full_name = dict_tapxml_info[agnt]["register"][irname]["full_name"]
                    reg_handler = (("%s.%s") % (curr_tap_handler, full_name)).lower()
                else:
                    htdte_logger.error(("Can;t find entry : dict_tapxml_info[\"%s\"][\"register\"][\"%s\"][\"full_name\"]") % (agnt, irname))

            # import pdb; pdb.set_trace()
            if(dri < 0 and dro < 0 and (len(list(dr_read_byfields.keys())) or len(list(dr_by_fields.keys())))):
                if(not len(list(dr_read_byfields.keys()))):
                    # ---Create current reg instance
                    if("tap_set_during_strobe_mode" not in list(CFG["HPL"].keys()) or CFG["HPL"]["tap_set_during_strobe_mode"] not in [0, "False", "FALSE"]):
                        if(os.environ.get("XDP_MODE") == "pythonsv"):
                            if(full_name.lower() != "punit_tap_pcudatago"):
                                reg_handler = (("%s.getreg(\"%s\")") % (curr_tap_handler, full_name)).lower()
                                self.logStream.write((" register=%s\n") % (reg_handler))
                                # ---Per field assignment
                                for f in list(dr_by_fields.keys()):
                                    field_name = HTD_INFO.tap_info.normalize_field_name(irname, agnt, f)
                                    self.logStream.write((" register.%s.store(0x%x);\n") % (field_name.lower().replace(".", "_"), dr_by_fields[f]))
                                self.logStream.write((" register.flush();print register.name;print register.__str__();print register.read();print register.show(returnstr = True)\n"))
                            else:
                                #import pdb; pdb.set_trace()
                                if(dr_by_fields['UCDATA.CMD'] == 1):  # pcudata read
                                    self.logStream.write((" pd=itp.pcudata(0,%s)\n") % (hex(dr_by_fields['UCDATA.ADDR'])))
                                elif(dr_by_fields['UCDATA.CMD'] == 2):  # pcudata write
                                    self.logStream.write((" itp.pcudata(0,%s,%s)\n") % (hex(dr_by_fields['UCDATA.ADDR']), hex(dr_by_fields['UCDATA.DATA'])[:-1]))
                                    if(hex(dr_by_fields['UCDATA.ADDR']) == "0xf948"):
                                        self.logStream.write(" time.sleep(TIMEOUT) #achinkov: Sleep on the ucdata_done\\n")
                                else:
                                    exit("unexpected pcudata command")

                        else:
                            # --DAL mode
                            reg_handler = ("%s.%s") % (curr_tap_handler, irname)
                            self.logStream.write((" register=%s.get()\n") % (reg_handler))
                            for f in list(dr_by_fields.keys()):
                                # ---Discovering the actual case of field in dictionary
                                if((agnt in list(dict_tapxml_info.keys())) and irname in list(dict_tapxml_info[agnt]["register"].keys()) and (f.upper().replace(".", "_") in [x.upper() for x in list(dict_tapxml_info[agnt]["register"][irname]["field"].keys())])):
                                    for x in list(dict_tapxml_info[agnt]["register"][irname]["field"].keys()):
                                        if(f.upper().replace(".", "_") == x.upper()):
                                            self.logStream.write((" register.%s=%s;") % (x, hex(dr_by_fields[f])))
                                            break
                                else:
                                    htdte_logger.error(("Can;t find entry :dict_tapxml_info[\"%s\"][\"register\"][\"%s\"][\"field\"][\"%s\"]") % (agnt, irname, f))
                            self.logStream.write((" %s.put(register)\n") % (reg_handler))
                    # achinkov removed to reduce IR/DR traffic => self.logStream.write((" register_read=%s.get()\n") % (reg_handler))
                    once = False
                # ---------------------------------
                for f in list(dr_read_byfields.keys()):
                    if (dr_read_byfields[f] >= 0):
                        field_name = HTD_INFO.tap_info.normalize_field_name(irname, agent, f)
                        if(os.environ.get("XDP_MODE") != "pythonsv"):
                            reg_handler = ("%s.%s") % (curr_tap_handler, irname)
                            for x in list(dict_tapxml_info[agnt]["register"][irname]["field"].keys()):
                                if(field_name.upper().replace(".", "_") == x.upper()):
                                    if(once == False):
                                        once = True
                                        self.logStream.write((" register_read=%s.get()\n") % (reg_handler))
                                    self.logStream.write((" if(register_read.%s!=%s): sys.stderr.write('Failed to match %s->%s==%s\\n')\n") % (x, hex(dr_read_byfields[f]), agnt, field_name, hex(dr_read_byfields[f])))
                            self.logStream.write((" register_read=%s.get();\n") % (reg_handler))
                        else:
                            if(full_name.replace(".", "_").lower() != "punit_tap_pcudataread"):
                                # --Need to use a full name intead of short name
                                if((agnt in list(dict_tapxml_info.keys())) and irname in list(dict_tapxml_info[agnt]["register"].keys()) and "full_name" in list(dict_tapxml_info[agnt]["register"][irname].keys())):
                                    full_name = dict_tapxml_info[agnt]["register"][irname]["full_name"]
                                    reg_handler = (("%s.getreg(\"%s\")") % (curr_tap_handler, full_name.replace(".", "_"))).lower()
                                else:
                                    htdte_logger.error(("Can;t find entry : dict_tapxml_info[\"%s\"][\"register\"][\"%s\"][\"full_name\"]") % (agnt, irname))
                                self.logStream.write((" register_read=%s; register_read.read()\n") % (reg_handler))
                                self.logStream.write((" if(DEBUG == True): print register_read.name;print register_read;print register_read.show(returnstr = True)\n"))
                                self.logStream.write((" if(register_read.%s!=%s): sys.stderr.write('Failed to match %s->%s==%s (actual 0x%%x)\\n'%% (%s).read())\n") % (f.replace(".", "_").lower(), hex(dr_read_byfields[f]), agnt, field_name, hex(dr_read_byfields[f]), reg_handler))
                            else:
                                self.logStream.write((" if(pd!=%s): sys.stderr.write('Failed to match %s->%s==%s (actual 0x%%x)\\n' %% pd)\n") % (hex(dr_read_byfields[f]), agnt, field_name, hex(dr_read_byfields[f])))
            else:  # --else :if(rdi or dro mode)
                self.logStream.write((" %s = %s\n") % (reg_handler, hex(dri)))
                # dro ????

   # ------------------------------------------------------------------------------------------------------------------------------------
   # ------------------------------------------------------------------------------------------------------------------------------------
    def StfPacket(self, size, in_val, out_val=0, strobes={}):
        htdte_logger.error(" NOT SUPPORTED IN XDP mode")

   # ------------------------------------------------------------------------------------------------------------------------------------
    def tap_verify(self, param, tapobj):
        return 1
   # ------------------------------------------------------------------------------------------------------------------------------------

    def cycles2time(self, clk, val):
        ts = 1 if (("HTD_Clocks_Settings" not in list(CFG.keys())) or ("sim_time_scale" not in list(CFG["HTD_Clocks_Settings"].keys()))) else CFG["HTD_Clocks_Settings"]["sim_time_scale"]
        unit = "ps" if (("HTD_Clocks_Settings" not in list(CFG.keys())) or ("sim_time_unit" not in list(CFG["HTD_Clocks_Settings"].keys()))) else CFG["HTD_Clocks_Settings"]["sim_time_unit"]
        base_clk = 10000 if (("HTD_Clocks_Settings" not in list(CFG.keys())) or ("base_clk" not in list(CFG["HTD_Clocks_Settings"].keys()))) else CFG["HTD_Clocks_Settings"]["base_clk"]

        clk2baseclk = val / cfg_HTD_Clocks(clk)
        base_clk_time = clk2baseclk * base_clk
        base_clk_time_scaled = base_clk_time / int(ts) * float(CFG["HTD_Clocks_Settings"][unit])

        return base_clk_time_scaled
   # ------------------------------------------------------------------------------------------------------------------------------------

    def tap_instruction_size(self, tap_size):
        self.logStream.write((" print \"tap_instruction_size: %s\"") % (tap_size))

   # ------------------------------------------------------------------------------------------------------------------------------------
    def pscand(self, tap_size): pass
  # -------------------------------------

    def get_indices_list_str(self, data_hash):
        final_data_l = []
        for l in sorted(data_hash):
            if (data_hash[l]):
                final_data_l.append(l)

        group_list = (list(x) for _, x in groupby(final_data_l, lambda x, c=count(): next(c) - x))
        final_data_str = ",".join("-".join(map(str, (g[0], g[-1])[:len(g)])) for g in group_list)
        return final_data_str
