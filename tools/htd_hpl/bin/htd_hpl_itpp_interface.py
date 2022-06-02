from htd_utilities import *
from htd_collaterals import *
from htd_hpl_not_interactive_interface import *
from itertools import count, groupby
import re

# ----------------------------
# Base itpp interface class
# ----------------------------
# -------------------------------------------------------------------------


class hpl_itpp_interface(hpl_not_interactive_interface):

    def __init__(self, filename, uiptr, stream=None):
        self.silent_stream = open("SilentModeStream", "w", 1)
        htdte_logger.inform("Creating Silent Mode activity Stream file:SilentModeStream")
        if (stream is None):
            self.file_name = filename
            self.logStream = open(self.file_name, "w", 1)
            htdte_logger.inform(("Creating ITPP file:%s") % (self.file_name))
            self.__isstream = 0

            # ---Add header
            self.print_header(
                "***********************************HEADER**********************************************/n")
            for l in htdte_logger.get_header():
                self.print_header(l)
            self.print_header(
                "***************************************************************************************/n")
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
   # --------------------------------

    def tap_compression_off(self): self.logStream.write("no_compress: start;\n")

    def tap_compression_on(self): self.logStream.write("no_compress: stop;\n")

    def change_output_stream(self, name):
        if(self.file_name is None):
            htdte_logger.inform(("Can't switch un-named stream to named (%s)") % name)
        htdte_logger.inform(("Close the current stream : %s") % self.file_name)
        self.logStream.close()
        self.logStream = open(name, "w", 1)
        htdte_logger.inform(("Creating ITPP file:%s") % (name))
        self.__isstream = 0
        # ---Add header
        self.print_header(
            "***********************************HEADER**********************************************/n")
        for l in htdte_logger.get_header():
            self.print_header(l)
        self.print_header(
            "***************************************************************************************/n")
   # -------------------------------------------------------------------------

    def print_header(self, line):
        no_new_lines = line.split('\n')
        for l in no_new_lines:
            if (len(l)):
                self.logStream.write(("# %s\n") % (l))

   # -------------------------------------------------------------------------
    def insert_line(self, line):
        no_new_lines = line.split('\n')
        for l in no_new_lines:
            if (len(l)):
                self.logStream.write(("%s\n") % (l))

   # -------------------------------------------------------------------------
    def close(self):
        if (not self.__isstream):
            self.logStream.close()

    # -----Silent mode , the stream is redirected to another file-----------------------
   # -------------------------------------------------------------------------
    def tap_command_low_level_mode_enabled(self):
        return True
   # -------------------------------------------------------------------------

    def set_silent_mode(self):
        self.logStream = self.silent_stream
        self.silent_mode = 1

   # -------------------------------------------------------------------------
    def unset_silent_mode(self):
        self.logStream = self.current_stream
        self.silent_mode = 0
   # -------------------------------------------------------------------------

    def get_model_time(self):
        return -1
   # -------------------------------------------------------------------------

    def send_action(self, line):
        if (not self.uiptr.silent_mode and (self.uiptr.current_action is None or not self.uiptr.current_action.get_curr_flow().is_verification_mode())):
            self.logStream.write(line)

   # -------------------------------------------------------------------------
    def add_comment(self, line):
        if (self.uiptr.silent_mode):
            return
        no_new_lines = line.split('\n')
        for l in no_new_lines:
            if (len(l)):
                self.logStream.write(("rem: comment: %s ;\n") % (l.replace("rem:", "")))
   # -------------------------------------------------------------------------

    def set_pattern_info(self, message):
        if (self.uiptr.silent_mode):
            return
        no_new_lines = message.split('\n')
        for l in no_new_lines:
            self.logStream.write(("comment: %s ;\n") % (l))

   # -------------------------------------------------------------------------
    def signal_unforce(self, full_path):
        if (self.uiptr.silent_mode):
            return
        self.logStream.write(("rem: release_signal %s ;\n") % (full_path))
   # -------------------------------------------------------------------------

    def signal_peek(self, full_path, value=-1):
        if (self.uiptr.silent_mode):
            return
        if (value < 0):
            self.logStream.write(("rem: peek_signal %s ;\n") % (full_path))
        else:
            self.logStream.write(("rem: peek_signal %s 0x%x;\n") % (full_path, value))
   # -------------------------------------------------------------------------

    def signal_poke(self, full_path, value):
        if (self.uiptr.silent_mode):
            return
        if(isinstance(value, int)):
            self.logStream.write(("rem: deposit_signal %s 0x%x ;\n") % (full_path, value))
        elif(value == "x"):
            self.logStream.write(("rem: deposit_signal %s x ;\n") % (full_path))
        elif(value == "z"):
            self.logStream.write(("rem: deposit_signal %s z ;\n") % (full_path))
        else:
            htdte_logger.error(("Illegal signal value type :%s") % (value))

   # -------------------------------------------------------------------------
    def check_signal(self, full_path, value):
        if (self.uiptr.silent_mode):
            return
        if (isinstance(value, int)):
            self.logStream.write(("rem:  peek_signal  %s 0x%x;\n") % (full_path, value))
        else:
            self.logStream.write(("rem:  peek_signal  %s %s;\n") % (full_path, value))
   # -------------------------------------------------------------------------

    def check_signal_not(self, full_path, value):
        if (self.uiptr.silent_mode):
            return
        if (isinstance(value, int)):
            self.logStream.write(("rem:  inv_peek_signal  %s 0x%x;\n") % (full_path, value))
        else:
            self.logStream.write(("rem:  inv_peek_signal  %s %s;\n") % (full_path, value))

   # -------------------------------------------------------------------------
    def signal_exists(self, full_path):
        return True

    # -------Need ITPP EXTENSIONS----------------------
    def signal_force(self, full_path, value):
        if (self.uiptr.silent_mode):
            return
        if(isinstance(value, int)):
            self.logStream.write(("rem: force_signal %s 0x%x ;\n") % (full_path, value))
        elif(value == "x"):
            self.logStream.write(("rem: force_signal %s x ;\n") % (full_path))
        elif(value == "z"):
            self.logStream.write(("rem: force_signal %s z ;\n") % (full_path))
        else:
            htdte_logger.error(("Illegal signal value type :%s") % (value))

   # -------------------------------------------------------------------------
    def signal_set(self, full_path, value):
        if (not isinstance(value, int) and not isinstance(value, int) and value not in ["x", "X", "z", "Z"]):
            htdte_logger.error(
                ("Improper value type received : expected int , while got:%s") % (type(value)))
        if(type(value) in [int, int]):
            # TODO - Check with Rob if this applicable also for DP!!!
            self.logStream.write(("rem: deposit_signal %s 0x%x ;\n") % (full_path, value))
        elif(value == "x"):
            self.logStream.write(("rem: deposit_signal %s x ;\n") % (full_path))
        elif(value == "z"):
            self.logStream.write(("rem: deposit_signal %s z ;\n") % (full_path))
        else:
            htdte_logger.error(("Illegal signal value type :%s") % (value))

   # -------------------------------------------------------------------------
    def ext_signalset_poke(self, signal_l, signal_values_l, delay=-1):
        if (not isinstance(signal_l, list)):
            htdte_logger.error("Wrong \"signal_l\" argument type: expected list of signals . ")
        if (not isinstance(signal_values_l, list)):
            htdte_logger.error(
                "Wrong \"signal_values_l\" argument type: expected list of expected signal values . ")
        if (len(signal_l) != len(signal_values_l)):
            htdte_logger.error((
                               "Error in  \"signal_values_l\" vs' \"signal_l\" arguments assignment , expected same list size , while len(\"signal_values_l\")=%d,len(\"signal_l\")=%d . ") % (
                               len(signal_values_l), len(signal_l)))
        sigs_entry = ""
        for i in range(0, len(signal_l)):
            sigs_entry += (" %s(%s)") % (signal_l[i], signal_values_l[i])
        self.logStream.write(("vector: %s,%d;\n") % (sigs_entry, delay if delay >= 0 else 1))
   # -------------------------------------------------------------------------

    def signal_wait(self, full_path, value, wait_time):
        if (not isinstance(full_path, list)):
            self.logStream.write(
                ("rem: poll_signal %s 0x%x %d %s;\n") % (full_path, value, wait_time, CFG["HTD_Clocks_Settings"]["sim_time_unit"]))
        else:
            for sig in full_path:
                self.logStream.write(
                    ("rem: poll_signal %s 0x%x %d %s;\n") % (sig, value, wait_time, CFG["HTD_Clocks_Settings"]["sim_time_unit"]))
   # -------------------------------------------------------------------------

    def start_clock(self, clock):
        self.logStream.write(("start_clk: %s;\n" % (clock)))

    def stop_clock(self, clock):
        self.logStream.write(("stop_clk: %s;\n" % (clock)))

    def wait_clock_num(self, width, clock):
        period_orig_clock = self.uiptr.hplClockMgr.get_clock_period(clock)
        period_vec_clock = self.uiptr.hplClockMgr.get_clock_period(CFG["HPL"]["PatVecClock"])
        NumOfVecClocks = int(math.ceil(width * period_orig_clock /
                                       (period_vec_clock if(period_vec_clock > 0) else 1)))
        if(NumOfVecClocks < 0):
            NumOfVecClocks = 1
        if (self.uiptr.signal_wait_mode == "silicon"):
            if ("delay_statement" in list(CFG["HPL"].keys())):
                self.logStream.write((CFG["HPL"]["delay_statement"] + "\n") % (NumOfVecClocks))
            else:
                self.logStream.write(("delay: %s(%d);\n") % (
                    self.uiptr.hplClockMgr.get_clock_rtl_path(CFG["HPL"]["PatVecClock"]), NumOfVecClocks))
        else:
            width_in_orig_clocks = self.uiptr.hplClockMgr.get_clock_period(clock)
            width_in_vec_clock = self.uiptr.hplClockMgr.get_clock_period(clock)
            self.logStream.write(("delay: %s(%d);\n") % (
                self.uiptr.hplClockMgr.get_clock_rtl_path(CFG["HPL"]["PatVecClock"]), NumOfVecClocks))
#	    self.logStream.write(("vector: xxtms(0),%d;\n") % (NumOfVecClocks))

   # -------------------------------------------------------------------------
    def wait_clock_edge(self, clock, edge):
        # FIXME:bring me back
        #self.logStream.write(("rem:   wait_clock_edge:   %s:%s;\n")%(clock,edge))
        return
   # -------------------------------------------------------------------------

    def wait_tick(self):
        # FIXME:bring me back
        #self.logStream.write(("rem:   wait_clock_edge:   %s:%s;\n")%(clock,edge))
        return
   # -------------------------------------------------------------------------

    def wait_clock_modulo(self, clock, modulo):
        # --If this clock is not modulo vector - error on DP
        # FIXME:bring me back
        #self.logStream.write(("rem:   wait_clock_edge:   %s:%d;\n")%(clock,modulo))
        self.logStream.write(("rem: comment: MODULO TVPV TODO;\n"))

   # -------------------------------------------------------------------------
    def write_itpp_cmd(self, cmd):
        if (self.uiptr.silent_mode):
            return
        self.logStream.write(("%s\n") % (cmd))

    # --------Tap Parameters instrumental printout-------
   # -------------------------------------------------------------------------
    def tap_parameters_instrumetal_print(self, irname, agent, parallel_mode, assigned_fields, attributes, labels, masks,
                                         strobe, capture, tdolabels):
        if (self.uiptr.silent_mode):
            return
        if (not cfg_HPL("ItppInstrCommentsEna")):
            return
        self.logStream.write("@ TAP_PARAMS_START \n")
        for atr in list(attributes.keys()):
            self.logStream.write(("@ %s=%s \n") % (atr, attributes[atr]))
        self.logStream.write("@  TAP_FIELDS_START \n")
        # for field in tapobj.api.get_ir_fields(param.irname,param.agent,param.eptarget):
        for field in HTD_INFO.tap_info.get_ir_fields(irname, agent):
            # rtl_node=api.get_rtl_endpoint(param.irname,param.agent,field)
            rtl_node = HTD_INFO.tap_info.get_rtl_endpoint(irname, agent, field)
            # TODO - rtl_node could be a multiple strings (in parallel) , should be separated by <path>,<path> ... - Need to close with Oz
            # self.logStream.write(("@   field_start:%s lsb=%d msb=%d reset_val=%s %s\n")%(field,api.get_field_lsb(param.irname,param.agent,field),
            #                                                                                api.get_field_msb(param.irname,param.agent,field),
            #									         api.get_field_reset_value(param.irname,param.agent,field),
            #										  ("rtl=%s")%(rtl_node) if len(rtl_node) else ""))
            self.logStream.write(("@   field_start:%s lsb=%d msb=%d reset_val=%s %s\n") % (
                field, HTD_INFO.tap_info.get_field_lsb(irname, agent, field),
                HTD_INFO.tap_info.get_field_msb(irname, agent, field),
                HTD_INFO.tap_info.get_field_reset_value(irname, agent, field),
                ("rtl=%s") % (rtl_node) if len(rtl_node) else ""))
            if (field in list(attributes.keys())):
                for field_val in attributes[field]["val"]:
                    self.logStream.write(
                        ("@    access: val=%s lsb=%d msb=%d strobe_flag=%d label=%s capture=%s mask=%s\n") % (
                            field_val.value, field_val.lsb, field_val.msb, field_val.strobe,
                            field_val.label, field_val.capture, field_val.mask))

            self.logStream.write(("@   field_end:%s \n") % (field))
        self.logStream.write("@  TAP_FIELDS_END\n")
        self.logStream.write("@ TAP_PARAMS_END\n")

   # -------------------------------------------------------------------------
    def label(self, label):
        if (self.uiptr.silent_mode):
            return
        self.logStream.write(("label: %s ;\n") % (label))
   # -------------------------------------------------------------------------

    def to_tap_state(self, to_state):
        if(self.uiptr.current_action.get_curr_flow().is_verification_mode()):
            return
        if (to_state == "IDLE"):
            self.logStream.write("to_state: Run-Test/Idle ;\n")
        elif (to_state == "SELECTDR"):
            self.logStream.write("to_state: Select-DR-Scan \n")
        elif (to_state == "CAPTUREDR"):
            self.logStream.write("to_state: Capture-DR \n")
        elif (to_state == "SHIFTDR"):
            self.logStream.write("to_state: Shift-DR \n")
        elif (to_state == "EXIT1DR"):
            self.logStream.write("to_state: Exit1-DR \n")
        elif (to_state == "PAUSEDR"):
            self.logStream.write("to_state: Pause-DR \n")
        elif (to_state == "EXIT2DR"):
            self.logStream.write("to_state: Exit2-DR \n")
        elif (to_state == "UPDATEDR"):
            self.logStream.write("to_state: Update-DR \n")
        elif (to_state == "SELECTIR"):
            self.logStream.write("to_state: Select-IR-Scan \n")
        elif (to_state == "CAPTUREIR"):
            self.logStream.write("to_state: Capture-IR \n")
        elif (to_state == "SHIFTIR"):
            self.logStream.write("to_state: Shift-IR \n")
        elif (to_state == "EXIT1IR"):
            self.logStream.write("to_state: Exit1-IR \n")
        elif (to_state == "PAUSEIR"):
            self.logStream.write("to_state: Pause-IR \n")
        elif (to_state == "EXIT2IR"):
            self.logStream.write("to_state: Exit2-IR \n")
        elif (to_state == "UPDATEIR"):
            self.logStream.write("to_state: Update-IR \n")
        else:
            htdte_logger.error((
                               "Invalid tap state value - \"%s\".\nExpected: SELECTDR,CAPTUREDR,SHIFTDR,EXIT1DR,PAUSEDR,EXIT2DR,UPDATEDR,SELECTIR,CAPTUREIR,SHIFTIR,EXIT1IR,PAUSEIR,EXIT2IR,UPDATEIR") % (
                               to_state))
   # -------------------------------------------------------------------------

    def ShiftIr(self, bin, size, labels):
        if (self.uiptr.silent_mode):
            return
        if (len(list(labels.keys())) > 0):
            label_index_str = ""
            delim = ""
            for l in list(labels.keys()):
                label_index_str = ("%s%s%s@%d") % (label_index_str, delim, labels[l], l)
                delim = ","
            self.logStream.write(("label: %s ;\n") % (label_index_str))
        self.logStream.write(("scani: %s ;\n") % (util_int_to_binstr(bin, size)))

    def ShiftParallelDr(self, bin, size, labels, masks, parallel_pins, captures, strobes, offsets_list):
        self.logStream.write("pin_group: pscan_pins, %s;\n" % (",".join(parallel_pins)))
        if (self.uiptr.silent_mode):
            return
        # ----LABELS------------
        if (len(list(labels.keys())) > 0):
            label_index_str = ""
            delim = ""
            for l in list(labels.keys()):
                label_index_str = ("%s%s%s@%d") % (
                    label_index_str, delim, labels[l], l - offsets_list[0])
                delim = ","
            self.logStream.write(("label: %s ;\n") % (label_index_str))
        # ----CAPTURE--------------------------
        if (len(list(captures.keys())) > 0):
            capture_str = self.get_indices_list_str(captures, offsets_list[0])
            self.logStream.write(("capture: %s;\n") % (capture_str))
        # ----MASK--------------------------
        if (len(list(masks.keys())) > 0):
            mask_str = self.get_indices_list_str(masks, offsets_list[0])
            self.logStream.write(("mask: %s;\n") % (mask_str))

            # ---------------
        parallel_pins_shift_out_l = []
        parallel_pin_index = 0

        for parallel_pin in parallel_pins:
            shift_in_str = util_int_to_binstr(bin, size)
            shift_out_str = shift_in_str.replace("1", "X").replace("0", "X")
            shift_out_str_l = list(shift_out_str)
            for ch in range(0, len(shift_out_str)):
                bitindex = len(shift_out_str) - 1 - ch + offsets_list[parallel_pin_index]
                if (len(list(strobes.keys())) > 0 and (bitindex in list(strobes.keys())) and (strobes[bitindex] != "S")):
                    shift_out_str_l[ch] = strobes[bitindex]

            # remove the strobes if masks are set
            if ("mask_tdo_on_mask_directive" in list(CFG["TE"].keys()) and CFG["TE"]["mask_tdo_on_mask_directive"] == 1 and len(masks) > 0):
                for mask_item in masks:
                    bit_index = len(shift_out_str) - 1 - mask_item + \
                        offsets_list[parallel_pin_index]
                    shift_out_str_l[bit_index] = 'X'

            shift_out_str = "".join(shift_out_str_l)
            parallel_pins_shift_out_l.append(shift_out_str)
            parallel_pin_index = parallel_pin_index + 1

        final_shift_out_str = ", ".join(parallel_pins_shift_out_l)
        # -----------------
        self.logStream.write(("pscand: %s, %s ;\n") % (shift_in_str, final_shift_out_str))

   # -------------------------------------------------------------------------
    def ShiftDr(self, bin, size, labels, masks, captures, strobes, pad_left=0, pad_rigth=0):
        if (self.uiptr.silent_mode):
            return
        # ----LABELS------------
        if (len(list(labels.keys())) > 0):
            label_index_str = ""
            delim = ""
            for l in list(labels.keys()):
                label_index_str = ("%s%s%s@%d") % (label_index_str, delim, labels[l], l)
                delim = ","
            self.logStream.write(("label: %s ;\n") % (label_index_str))
        # ----CAPTURE--------------------------
        if (len(list(captures.keys())) > 0):
            capture_str = self.get_indices_list_str(captures)
            self.logStream.write(("capture: %s;\n") % (capture_str))
        # ----MASK--------------------------
        if (len(list(masks.keys())) > 0):
            mask_str = self.get_indices_list_str(masks)
            self.logStream.write(("mask: %s;\n") % (mask_str))

            # ---------------
        shift_in_str = util_int_to_binstr(bin, size)
        shift_out_str = shift_in_str.replace("1", "X").replace("0", "X")
        shift_out_str_l = list(shift_out_str)
        for ch in range(0, len(shift_out_str)):
            bitindex = len(shift_out_str) - 1 - ch
            if (len(list(strobes.keys())) > 0 and (bitindex in list(strobes.keys())) and (strobes[bitindex] != "S")):
                shift_out_str_l[ch] = strobes[bitindex]

        # remove the strobes if masks are set
        if ("mask_tdo_on_mask_directive" in list(CFG["TE"].keys()) and CFG["TE"]["mask_tdo_on_mask_directive"] == 1 and len(masks) > 0):
            for mask_item in masks:
                bit_index = len(shift_out_str) - 1 - mask_item
                shift_out_str_l[bit_index] = 'X'

        shift_out_str = "".join(shift_out_str_l)
        # -----------------
        self.logStream.write(("scand: %s, %s ;\n") % (shift_in_str, shift_out_str))
   # -------------------------------------------------------------------------

    def StfPacket(self, size, in_val, out_val=0, strobes={}):
        if (self.uiptr.silent_mode):
            return
        shift_in_str = util_int_to_binstr(in_val, size)
        shift_out_str = util_int_to_binstr(0, size).replace("0", "X")
        shift_out_str_l = list(shift_out_str)
        for ch in range(0, len(shift_out_str)):
            bitindex = len(shift_out_str) - 1 - ch
            if (len(list(strobes.keys())) > 0 and (bitindex in list(strobes.keys())) and (strobes[bitindex] != "S")):
                shift_out_str_l[ch] = strobes[bitindex]
        shift_out_str = "".join(shift_out_str_l)
        self.logStream.write(("vector: stf_in(%s) stf_out(%s);\n") % (shift_in_str, shift_out_str))

   # -------------------------------------------------------------------------
    def tap_verify(self, param, tapobj):
        return 1
   # -------------------------------------------------------------------------

    def cycles2time(self, clk, val):
        ts = 1 if (("HTD_Clocks_Settings" not in list(CFG.keys())) or ("sim_time_scale" not in list(CFG[
                   "HTD_Clocks_Settings"].keys()))) else CFG["HTD_Clocks_Settings"]["sim_time_scale"]
        unit = "ps" if (("HTD_Clocks_Settings" not in list(CFG.keys())) or ("sim_time_unit" not in list(CFG[
                        "HTD_Clocks_Settings"].keys()))) else CFG["HTD_Clocks_Settings"]["sim_time_unit"]
        base_clk = 10000 if (("HTD_Clocks_Settings" not in list(CFG.keys())) or ("base_clk" not in list(CFG[
                             "HTD_Clocks_Settings"].keys()))) else CFG["HTD_Clocks_Settings"]["base_clk"]

        clk2baseclk = float(val) / cfg_HTD_Clocks(clk)
        base_clk_time = clk2baseclk * base_clk
        base_clk_time_scaled = base_clk_time / int(ts) * float(CFG["HTD_Clocks_Settings"][unit])

        return base_clk_time_scaled
   # -------------------------------------------------------------------------

    def tap_instruction_size(self, tap_size):
        self.logStream.write(("tap_instruction_size: %s; \n") % (tap_size))

   # -------------------------------------------------------------------------
    def pscand(self, tap_size):
        self.logStream.write(("pscand: %s ;\n") % (tap_size))

    def get_indices_list_str(self, data_hash, offset=0):
        final_data_l = []
        for l in sorted(data_hash):
            if (data_hash[l]):
                final_data_l.append(l - offset)

        group_list = (list(x) for _, x in groupby(final_data_l, lambda x, c=count(): next(c) - x))
        final_data_str = ",".join("-".join(map(str, (g[0], g[-1])[:len(g)])) for g in group_list)
        return final_data_str

    def start_scan(self, scan_pins_list):
        if (self.uiptr.silent_mode):
            return
        scan_group_sep = ","
        scan_pins_str = scan_group_sep.join(scan_pins_list)
        self.logStream.write(("start_scan: %s;\n") % (scan_pins_str))

    def stop_scan(self, scan_pins_list):
        if (self.uiptr.silent_mode):
            return
        scan_group_sep = ","
        scan_pins_str = scan_group_sep.join(scan_pins_list)
        self.logStream.write(("stop_scan: %s;\n") % (scan_pins_str))
