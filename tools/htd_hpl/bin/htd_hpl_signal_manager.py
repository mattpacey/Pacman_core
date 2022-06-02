from htd_utilities import *
from htd_collaterals import *
from htd_te_shared import *
"""
  class hpl_SignalManager - base class for all Signal operations under HPL -unified interface encapsulation
        interface - handler to external world interface (could be itpp, xml or any other object "speaking" with model or TVPV env
"""


class hpl_SignalManager(object):
    def __init__(self, interactive_mode, interface=None, uiptr=None):
        self.interface = interface
        self.uiptr = uiptr
        self.interactive_mode = interactive_mode
        # ---Open a signal access log for emu signal collection-----
        self.captured_signals = {}
        # ----------------------------
        try:
            sig_file = ("%s.sig") % (HTD_INFO.signal_info.get_module_file_name())
        except BaseException:
            sig_file = ("htd_captured_rtl_signals.sig")

        self.signal_file = open(sig_file, 'w')
        htdte_logger.inform(("Logging RT signals to file:  %s. ") % sig_file)
        if("PatVecClock" not in list(CFG["HPL"].keys())):
            htdte_logger.error(
                "Missing \"PatVecClock\" configuration entry in  CFG[HPL] structure - define the default vector resolution clock name . ")

    # -------------------------------------------------------------------------------------------------------------
    def get_full_path(self, sig, lsb, msb, selector):
        if(HTD_INFO.signal_info.dut_pin_defined(sig)):
            sig = HTD_INFO.signal_info.get_signal_by_dut_pin(sig)
        sigs_l = HTD_INFO.signal_info.extract_full_signal_path(sig, lsb, msb, selector)
        temp_sigs_l = list(sigs_l)
        if(isinstance(sigs_l, list)):
            for s in sigs_l:
                if (self.is_sig_disabled(s)):
                    temp_sigs_l.remove(s)
                else:
                    self.collect_signal_access(s)
            sigs_l = temp_sigs_l
            return sigs_l
        else:
            return [sigs_l]
    # -------------------------------------------------------------------------------------------------------------

    def is_sig_disabled(self, sig):
        if ("DisableSigs" in CFG):
            if "allow_dynamic_assignment" in CFG["DisableSigs"]:
                del CFG["DisableSigs"]["allow_dynamic_assignment"]
            if "description" in CFG["DisableSigs"]:
                del CFG["DisableSigs"]["description"]
            for s in CFG["DisableSigs"]:
                if CFG["DisableSigs"][s] == 1 and re.match(r'%s' % (s), sig):
                    return 1
        return 0
    # -------------------------------------------------------------------------------------------------------------

    def get_full_external_pin_name(self, signal, lsb, msb):
        if(lsb < 0 or msb < 0):
            return signal
        else:
            return ("%s[%d:%d]") % (signal, msb, lsb)
    # -------------------------------------------------------------------------------------------------------------

    def is_interactive_mode(self):
        return self.interactive_mode
    # -------------------------------------------------------------------------------------------------------------

    def signal_exists(self, search_signal):
        htdte_logger.error("This method is a pure virtual and should be overloading by inheritance tree . ")
    # -------------------------------------------------------------------------------------------------------------

    def signal_peek(self, signal_path, lsb, msb, selector=""):
        htdte_logger.error("This method is a pure virtual and should be overloading by inheritance tree . ")
    # -------------------------------------------------------------------------------------------------------------

    def signal_check(self, signal_path, lsb, msb, value, selector):
        htdte_logger.error("This method is a pure virtual and should be overloading by inheritance tree . ")

    def signal_check_not(self, signal_path, lsb, msb, value, selector):
        htdte_logger.error("This method is a pure virtual and should be overloading by inheritance tree . ")
   # -----------------------------------
    # -------------------------------------------------------------------------------------------------------------

    def external_signal_set(self, sig_l, sig_values_l, delay=1):
        value_binary_map = []
        signals_l = []
        for i in range(0, len(sig_l)):
            # This isn't always an int, so we need to check before comparing
            # Also, it can be 'x', so int() won't work either.
            if(not isinstance(sig_values_l[i] , int) or sig_values_l[i] > 1):
                m = re.search(r"\[(\d+):(\d+)\]$", sig_l[i])
                if(not m):
                    if(not HTD_INFO.signal_info.dut_pin_defined(sig_l[i])):
                        if("dut_pin_map_file" not in list(CFG["HPL"].keys())):
                            htdte_logger.error(
                                "Trying to set external DUT signal not  dut_pin_map  (TVPV to RTL pin name conversion) file is not set in CFG[\"HPL\"][\"dut_pin_map_file\"].\nPls. define the TE_cfg.xml entry to specify the file location. ")
                        else:
                            htdte_logger.error(("Trying to set external DUT signal-(%s) while not defined in dut_pin_map (TVPV to RTL pin name conversion) file -(%s) . ") % (
                                sig_l[i], CFG["HPL"]["dut_pin_map_file"]))
                    else:
                        m = re.search(r"\[(\d+):(\d+)\]$", HTD_INFO.signal_info.get_signal_by_dut_pin(sig_l[i]))
                        if(not m):
                            # assuming the missing indexes are (lsb,msb)=(0:0-)
                            msb = 0
                            lsb = 0
                            #htdte_logger.error(("Trying to set external DUT signal by non one bit value (%s)..Pls. add a signal range %s[<msb>:<lsb>] or modify assigned value . ")%(sig_values_l[i],sig_l[i]))
                        else:
                            msb = int(m.groups()[0])
                            lsb = int(m.groups()[1])
                else:
                    msb = int(m.groups()[0])
                    lsb = int(m.groups()[1])
                if(not isinstance(sig_values_l[i], str) and sig_values_l[i] > (pow(2, msb - lsb + 1) - 1)):
                    htdte_logger.error(
                        ("Trying to assign external DUT pin -%s of range[%d:%d] by out of range value - 0x%x  . ") % (sig_l[i], msb, lsb, sig_values_l[i]))
                if(not isinstance(sig_values_l[i], str)):
                    value_binary_map.append(util_int_to_binstr(sig_values_l[i], msb - lsb + 1))
                else:
                    final_nonint_value = sig_values_l[i]
                    if (msb > -1 and lsb > -1):
                        final_nonint_value = sig_values_l[i] * (msb - lsb + 1)
                    value_binary_map.append(final_nonint_value.upper())
            else:
                value_binary_map.append(str(sig_values_l[i]))
            # if(sig_l[i] not in self.dut_pin_map.keys()):
            signals_l.append(sig_l[i])
            # else:
            #    signals_l.append(self.dut_pin_map[sig_l[i]])
        self.interface.ext_signalset_poke(signals_l, value_binary_map, delay)
        # -----------------------------------
    # -------------------------------------------------------------------------------------------------------------

    def resize_list(l, newsize, filling=None):
        if newsize > len(l):
            l.extend([filling for x in range(len(l), newsize)])
        else:
            del l[newsize:]
    # -------------------------------------------------------------------------------------------------------------

    def collect_signal_access(self, sig):
        normalized_sig = re.sub(r"(\[\d+:\d+\])$", "", sig)
        current_action = self.uiptr.get_current_action().get_action_name() if(self.uiptr.get_current_action() is not None) else "None"
        if(normalized_sig not in list(self.captured_signals.keys())):
            self.captured_signals[normalized_sig] = [current_action]
            current_file = self.uiptr.get_current_action().get_action_call_file() if(self.uiptr.get_current_action() is not None) else "None"
            current_line = self.uiptr.get_current_action().get_action_call_lineno() if(self.uiptr.get_current_action() is not None) else 0
            self.signal_file.write(("%s  #%s(%d):%s\n") % (normalized_sig, current_file, current_line, current_action))
        else:
            if(current_action not in self.captured_signals[normalized_sig]):
                self.captured_signals[normalized_sig].append(current_action)
    # -------------------------------------------------------------------------------------------------------------

    def verify_all_signals(self):
        htdte_logger.error("This method is a pure virtual and should be overloading by inheritance tree . ")
    # -------------------------------------------------------------------------------------------------------------

    def __del__(self):
        self.signal_file.close()
    # -------------------------------------------------------------------------------------------------------------

    def clock_wait(self, clock, clock_frequency, waitcycles, maxtimeout, refclock, selector=""):
        self.interface.wait_clock_num(waitcycles, refclock)
        self.interface.clock_wait(self.get_full_path(clock, -1, -1, selector), clock_frequency, maxtimeout)

    def clock_check_average(self, clock, clock_frequency, waitcycles, refclock, average=1, selector=""):
        self.interface.wait_clock_num(waitcycles, refclock)
        for clock in self.get_full_path(clock, -1, -1, selector):
            self.interface.clock_check_average(clock, clock_frequency, average)

    def cycles2time(self, clk, val):
        ts = 1 if (("Temp" not in list(CFG.keys())) or ("sim_time_scale" not in list(CFG["Temp"].keys()))) else cfg_Temp("sim_time_scale")
        unit = "ps" if (("Temp" not in list(CFG.keys())) or ("sim_time_unit" not in list(CFG["Temp"].keys()))) else cfg_Temp("sim_time_unit")
        base_clk = 10000 if (("Temp" not in list(CFG.keys())) or ("base_clk" not in list(CFG["Temp"].keys()))) else cfg_Temp("base_clk")

        clk2baseclk = val / cfg_HTD_Clocks(clk)
        base_clk_time = clk2baseclk * base_clk
        base_clk_time_scaled = base_clk_time / int(ts) * float(cfg_Temp(unit))

        return base_clk_time_scaled
    # -------------------------------------------------------------------------------------------------------------

    def signalset_pack(self, sig_l, val_l):
        sigs_l = {}
        for i in range(0, len(sig_l)):
            if(sig_l[i] not in list(sigs_l.keys())):
                sigs_l[sig_l[i]] = {}
                sigs_l[sig_l[i]][-1] = {}
                sigs_l[sig_l[i]][-1][-1] = val_l[i]
        return sigs_l

    # -------------------------------------------------------------------------------------------------------------

    def signalset_wait(self, sigs_l, waitcycles, maxtimeout, refclock, silicon_wait_enabled=1, selector="", override_sigs_l=[], peeksignal_disable=0):
        if(not isinstance(sigs_l, dict)):
            htdte_logger.error(
                ("Wrong  \"sigs_l\" - arguments type, expected dictionary sigs_l[<sig_path_name>][lsb_or-1][msb_or_-1]=<value> , received - %s . ") % (str(type(sigs_l))))
        wait_tick_time = self.uiptr.hplClockMgr.train_tick_time()
        maxtimeout_rt = (maxtimeout * wait_tick_time * self.uiptr.hplClockMgr.get_clock_period(refclock))
        waitcycles_rt = (waitcycles * wait_tick_time * self.uiptr.hplClockMgr.get_clock_period(refclock))

        # Temp workaround for negative poll values seen on KBL. Will find more robust solution later.
        if (maxtimeout > waitcycles_rt):
            timeout_time_rt = maxtimeout_rt - waitcycles_rt
        else:
            timeout_time_rt = waitcycles_rt
        if(maxtimeout_rt > waitcycles_rt):
            DefaultTimeOutTime = maxtimeout_rt
        else:
            (CFG["HPL"]["DefaultTimeOutTime"])
        if("DefaultTimeOutTime" in list(CFG["HPL"].keys())):
            DefaultTimeOutTime = CFG["HPL"]["DefaultTimeOutTime"]
        else:
            (CFG["HPL"]["DefaultTimeOutTime"] == "1000")
        # ----------------------------------------
        if(self.uiptr.signal_wait_mode == "silicon"):
            # WidthInVecClocks=self.uiptr.hplClockMgr.clock_transpose(refclock,waitcycles,CFG["HPL"]["PatVecClock"])
            # -wait_clock_num:vector + not fatal peek +fatal pool
            if (silicon_wait_enabled == 1):
                self.interface.wait_clock_num(waitcycles, refclock)

            # --
            for sig in list(sigs_l.keys()):
                for lsb in list(sigs_l[sig].keys()):
                    for msb in list(sigs_l[sig][lsb].keys()):
                        if (sig in override_sigs_l):
                            if(lsb >= 0 and msb >= 0):
                                sig = "%s[%d:%d]" % (sig, msb, lsb)
                            if not peeksignal_disable:
                                self.interface.signal_peek(sig, sigs_l[sig][lsb][msb])
                        else:
                            for s in self.get_full_path(sig, lsb, msb, selector):
                                if not peeksignal_disable:
                                    self.interface.signal_peek(s, sigs_l[sig][lsb][msb])

            # --
            for sig in list(sigs_l.keys()):
                for lsb in list(sigs_l[sig].keys()):
                    for msb in list(sigs_l[sig][lsb].keys()):
                        if (sig in override_sigs_l):
                            if(lsb >= 0 and msb >= 0):
                                sig = "%s[%d:%d]" % (sig, msb, lsb)
                            self.interface.signal_wait(sig, sigs_l[sig][lsb][msb], timeout_time_rt)
                        else:
                            for s in self.get_full_path(sig, lsb, msb, selector):
                                self.interface.signal_wait(s, sigs_l[sig][lsb][msb], timeout_time_rt)
        else:
            # --Simulation mode : Sim time optimization
            for sig in list(sigs_l.keys()):
                for lsb in list(sigs_l[sig].keys()):
                    for msb in list(sigs_l[sig][lsb].keys()):
                        if (sig in override_sigs_l):
                            if(lsb >= 0 and msb >= 0):
                                sig = "%s[%d:%d]" % (sig, msb, lsb)
                            self.interface.signal_wait(sig, sigs_l[sig][lsb][msb], waitcycles_rt)
                        else:
                            for s in self.get_full_path(sig, lsb, msb, selector):
                                self.interface.signal_wait(s, sigs_l[sig][lsb][msb], waitcycles_rt)
    #-------------------------------------------------------------------------------------------------------------

    def signal_wait(self, signal_path, lsb, msb, value, waitLimit, time_out=-1, refclk="none", selector=""):
        sigs = {}
        if(not isinstance(signal_path, list)):
            sigs[signal_path] = {}
            sigs[signal_path][lsb] = {}
            sigs[signal_path][lsb][msb] = value
            self.signalset_wait(sigs, waitLimit, time_out, refclk, 1, selector)
        else:
            for sig in signal_path:
                sigs[sig] = {}
                sigs[sig][lsb] = {}
                sigs[sig][lsb][msb] = value
            self.signalset_wait(sigs, waitLimit, time_out, refclk, 1, selector)
    # -------------------------------------------------------------------------------------------------------------

    def signalset_serial_set(sigs_l, width, refclock, selector):
        if(not isinstance(sigs_l, dict)):
            htdte_logger.error(
                ("Wrong  \"sigs_l\" - arguments type, expected dictionary sigs_l[<sig_path_name>][lsb_or-1][msb_or_-1]=<value> , received - %s . ") % (str(type(sigs_l))))
        ext_mode = -1
        signal_map = []
        for sig in list(sigs_l.keys()):
            if(sig.find('.') < 0 and sig.find("/") < 0):
                if(ext_mode == 0):
                    htdte_logger.error(("Mixed external DUT pin set and enternal signals list not allowed (%s) . ") % (sig))
                ext_mode = 1
            else:
                if(ext_mode == 1):
                    htdte_logger.error(("Mixed external DUT pin set and enternal signals list not allowed (%s) . ") % (sig))
                ext_mode = 0
        # -----------------
        WidthInVecClocks = uiptr.hplClockMgr.clock_transpose(refclock, 1, CFG["HPL"]["PatVecClock"])
        pin_mapping_sig = []
        pin_mapping_val = []
        for sig in list(sigs_l.keys()):
            for lsb in list(sigs_l[sig].keys()):
                for msb in list(sigs_l[sig][lsb].keys()):
                    if(ext_mode):
                        pin_mapping_sig.append(self.get_full_external_pin_name(sig, lsb, msb))
                        val_l = [int(x) for x in list("".join(reversed(util_int_to_binstr(sigs_l[sig][lsb][msb], width))))]
                        pin_mapping_val.append(val_l)
                    else:
                        for s in self.get_full_path(sig, lsb, msb, selector):
                            pin_mapping_sig.append(s)
                            val_l = [int(x) for x in list("".join(reversed(util_int_to_binstr(sigs_l[sig][lsb][msb], width))))]
                            pin_mapping_val.append(val_l)
        # -------------------------------------------
        for n in range(0, width):
            if(ext_mode):
                one_cycle_values_l = []
                for s in range(0, len(pin_mapping_sig)):
                    one_cycle_values_l.append(ext_pin_mapping_val[s][n])
                self.external_signal_set(pin_mapping_sig, one_cycle_values_l, 1)
                # for ext signals wait is happen on vector
            else:
                for s in range(0, len(pin_mapping_sig)):
                    self.interface.signal_set(pin_mapping_sig[s], pin_mapping_val[s][n])
                    # --wait_clock_num
                    self.interface.wait_clock_num(1, CFG["HPL"]["PatVecClock"])
    # -------------------------------------------------------------------------------------------------------------

    def signalset_modular_set(self, op, sigs_l, selector=""):
        if(not isinstance(sigs_l, dict)):
            htdte_logger.error(
                ("Wrong  \"sigs_l\" - arguments type, expected dictionary sigs_l[<sig_path_name>][lsb_or-1][msb_or_-1]=<value> , received - %s . ") % (str(type(sigs_l))))
        ext_mode = -1
        signal_map = []
        for sig in list(sigs_l.keys()):
            if(sig.find('.') < 0 and sig.find("/") < 0):
                if(ext_mode == 0):
                    htdte_logger.error(("Mixed external DUT pin set and internal signals list not allowed (%s) . ") % (sig))
                ext_mode = 1
            else:
                if(ext_mode == 1):
                    htdte_logger.error(("Mixed external DUT pin set and internal signals list not allowed (%s) . ") % (sig))
                ext_mode = 0
        # -----------------
        if(ext_mode):
            dut_signals_l = []
            dut_signal_values = []
            for sig in list(sigs_l.keys()):
                for lsb in list(sigs_l[sig].keys()):
                    for msb in list(sigs_l[sig][lsb].keys()):
                        dut_signals_l.append(self.get_full_external_pin_name(sig, lsb, msb))
                        dut_signal_values.append(sigs_l[sig][lsb][msb])
            self.external_signal_set(dut_signals_l, dut_signal_values, 1)
        else:
            for sig in list(sigs_l.keys()):
                for lsb in list(sigs_l[sig].keys()):
                    for msb in list(sigs_l[sig][lsb].keys()):
                        for s in self.get_full_path(sig, lsb, msb, selector):
                            if(op == "set"):
                                self.interface.signal_set(s, sigs_l[sig][lsb][msb])
                            elif(op == "force"):
                                self.interface.signal_force(s, sigs_l[sig][lsb][msb])
                            elif(op == "unforce"):
                                self.interface.signal_unforce(s)
                            else:
                                htdte_logger.error(("Unknown op: %s, supported [force,unforce,set] . ") % (op))
    # -------------------------------------------------------------------------------------------------------------

    def signalset_force(self, sigs_l, selector=""): self.signalset_modular_set("force", sigs_l, selector)
    # -------------------------------------------------------------------------------------------------------------

    def signalset_unforce(self, sigs_l, selector=""): self.signalset_modular_set("unforce", sigs_l, selector)
    # -------------------------------------------------------------------------------------------------------------

    def signalset_set(self, sigs_l, selector=""): self.signalset_modular_set("set", sigs_l, selector)
    # -------------------------------------------------------------------------------------------------------------

    def signal_modular_set(self, op, signal_path, lsb, msb, value, selector="", signal_path_override=0):
        if(signal_path.find('.') < 0 and signal_path.find("/") < 0):
            self.external_signal_set([self.get_full_external_pin_name(signal_path, lsb, msb)], [value], 1)
        else:
            if (signal_path_override):
                full_path_list = [signal_path]
            else:
                full_path_list = self.get_full_path(signal_path, lsb, msb, selector)
            for s in full_path_list:
                if(op == "force"):
                    self.interface.signal_force(s, value)
                elif(op == "unforce"):
                    self.interface.signal_unforce(s, value)
                elif(op == "set"):
                    self.interface.signal_set(s, value)
                else:
                    htdte_logger.error(("Unknown op: %s, supported [force,unforce,set] . ") % (op))
    # -------------------------------------------------------------------------------------------------------------

    def signal_force(self, signal_path, lsb, msb, value, selector=""): self.signal_modular_set("force", signal_path, lsb, msb, value, selector="")
    # -------------------------------------------------------------------------------------------------------------

    def signal_unforce(self, signal_path, lsb, msb, value, selector=""): self.signal_modular_set("unforce", signal_path, lsb, msb, value, selector="")
    # -------------------------------------------------------------------------------------------------------------

    def signal_set(self, signal_path, lsb, msb, value, selector="", signal_path_override=0): self.signal_modular_set("set", signal_path, lsb, msb, value, selector="", signal_path_override=signal_path_override)

    # -------------------------------------------------------------------------------------------------------------
    def signal_pulse(self, signal_path, lsb, msb, active_value, width, clock, selector):
        if(active_value > 1):
            htdte_logger.error(("Pulse active values are 0 or 1 , while getting - %d ") % (active_value))
        if(signal_path.find('.') < 0 and signal_path.find("/") < 0):
            # external pins mode
            period_orig_clock = self.uiptr.hplClockMgr.get_clock_period(clock)
            period_vec_clock = self.uiptr.hplClockMgr.get_clock_period(CFG["HPL"]["PatVecClock"])
            NumOfVecClocks = int(math.ceil(width * period_orig_clock / (period_vec_clock if(period_vec_clock > 0) else 1)))
            inverted_value = (1 ^ active_value)
            self.external_signal_set([self.get_full_external_pin_name(signal_path, lsb, msb)], [inverted_value], 1)
            self.external_signal_set([self.get_full_external_pin_name(signal_path, lsb, msb)], [active_value], NumOfVecClocks)
            self.external_signal_set([self.get_full_external_pin_name(signal_path, lsb, msb)], [inverted_value], 1)
        else:
            for s in self.get_full_path(signal_path, lsb, msb, selector):
                self.interface.signal_set(s, active_value)
            self.interface.wait_clock_num(WidthInVecClocks, CFG["HPL"]["PatVecClock"])
            for s in self.get_full_path(signal_path, lsb, msb, selector):
                self.interface.signal_set(s, (1 ^ active_value))
    # -------------------------------------------------------------------------------------------------------------

    def signalset_pulse(self, sigs_l, width, refclock, selector):
        if(not isinstance(sigs_l, dict)):
            htdte_logger.error(
                ("Wrong  \"sigs_l\" - arguments type, expected dictionary sigs_l[<sig_path_name>][lsb_or-1][msb_or_-1]=<value> , received - %s . ") % (str(type(sigs_l))))
        ext_mode = -1
        signal_map = []
        for sig in list(sigs_l.keys()):
            if(sig.find('.') < 0 and sig.find("/") < 0):
                if(ext_mode == 0):
                    htdte_logger.error(("Mixed external DUT pin set and enternal signals list not allowed (%s) . ") % (sig))
                ext_mode = 1
            else:
                if(ext_mode == 1):
                    htdte_logger.error(("Mixed external DUT pin set and enternal signals list not allowed (%s) . ") % (sig))
                ext_mode = 0
        # -----------------
        period_orig_clock = self.uiptr.hplClockMgr.get_clock_period(refclock)
        period_vec_clock = self.uiptr.hplClockMgr.get_clock_period(CFG["HPL"]["PatVecClock"])
        WidthInVecClocks = int(math.ceil(width * period_orig_clock / (period_vec_clock if(period_vec_clock > 0) else 1)))
        pin_mapping_sig = []
        pin_mapping_val = []
        pin_mapping_inv_val = []
        for sig in list(sigs_l.keys()):
            for lsb in list(sigs_l[sig].keys()):
                for msb in list(sigs_l[sig][lsb].keys()):
                    if(ext_mode):
                        pin_mapping_sig.append(self.get_full_external_pin_name(sig, lsb, msb))
                        pin_mapping_val.append(sigs_l[sig][lsb][msb])
                        pin_mapping_inv_val.append(1 ^ sigs_l[sig][lsb][msb])
                    else:
                        for s in self.get_full_path(sig, lsb, msb, selector):
                            pin_mapping_sig.append(s)
                            pin_mapping_val.append(sigs_l[sig][lsb][msb])
                            pin_mapping_inv_val.append(1 ^ sigs_l[sig][lsb][msb])
        # -------------------------------------------
        if(ext_mode):
            self.external_signal_set(pin_mapping_sig, pin_mapping_inv_val, 1)
            # for vector already have a delay : self.interface.wait_clock_num(1,CFG["HPL"]["PatVecClock"])
            self.external_signal_set(pin_mapping_sig, pin_mapping_val, WidthInVecClocks)
            # for vector already have a delay :self.interface.wait_clock_num(WidthInVecClocks,CFG["HPL"]["PatVecClock"])
            self.external_signal_set(pin_mapping_sig, pin_mapping_inv_val, 1)
        else:
            for s in range(0, len(pin_mapping_sig)):
                self.interface.signal_force(pin_mapping_sig[s], pin_mapping_val[s])
            self.interface.wait_clock_num(width, CFG["HPL"]["PatVecClock"])
            for s in range(0, len(pin_mapping_sig)):
                self.interface.signal_force(pin_mapping_sig[s], pin_mapping_inv_val[s])


"""
  class hpl_SignalManager_interactive - encapsulate overloading operations used for interactive (real time TCM model simulation)?????????????????????????????????
"""


class hpl_SignalManager_interactive(hpl_SignalManager):
    def __init__(self, interface, uiptr=None):
        hpl_SignalManager.__init__(self, 0, interface, uiptr)
        if(interface is None):
            htdte_logger.error("Missing interface object pointer - received None . ")
    # ---This Method will not really peek the signal on non interactive mode and return 0
    # -------------------------------------------------------------------------------------------------------------

    def signal_peek(self, signal_path, lsb=-1, msb=-1, selector=""):
        final_val = ""
        prev_signal = ""
        for s in self.get_full_path(signal_path, lsb, msb, selector):
            val = self.interface.signal_peek(s)
            prev_signal = s
            if(final_val != "" and final_val != val):
                htdte_logger.error(("Multiple signal peek with different value found.(pls. use selector to specify each signal separately:%s=%s,%s=%s ") % (
                    prev_signal, final_val, s, val))
        return final_val
    # --This could not be really be verified on offline , just making directive to make such verification on stimulus execution
    # -------------------------------------------------------------------------------------------------------------

    def signal_exists(self, signal_path, lsb=-1, msb=-1, selector=""):
        for s in self.get_full_path(signal_path, lsb, msb, selector):
            if(not self.interface.signal_exists(s)):
                return False
            else:
                return True
    # -------------------------------------------------------------------------------------------------------------

    def verify_all_collected_signals(self):
        # in interactive mode the verification done by signal_exists()
        return
    # --This could not be really be verified on offline , just making directive to make such verification on stimulus execution
    # -------------------------------------------------------------------------------------------------------------

    def signal_check(self, signal_path, lsb, msb, value, selector):
            # no signal check should be done on interactive mode as no siganls are stimulated yet
        if (self.uiptr.get_current_action().get_curr_flow().is_verification_mode()):
            htdte_logger.inform("No signal check in verify() mode")
            return True
        for s in self.get_full_path(signal_path, lsb, msb, selector):
            if(not self.interface.check_signal(s, value)):
                return False
        return True
    # -------------------------------------------------------------------------------------------------------------

    def signal_check_not(self, signal_path, lsb, msb, value, selector):
        for s in self.get_full_path(signal_path, lsb, msb, selector):
            if(not self.interface.check_signal_not(s, value)):
                return False
        return True


"""
  class hpl_SignalManager_non_interactive - encapsulate overloading operations used for non interactive (model simulation driven by stimulus data)
"""


class hpl_SignalManager_non_interactive(hpl_SignalManager):
    # -------------------------------------------------------------------------------------------------------------
    def __init__(self, interface, uiptr=None):
        hpl_SignalManager.__init__(self, 0, interface, uiptr)
        if(interface is None):
            htdte_logger.error("Missing interface object pointer - received None . ")
    # -------------------------------------------------------------------------------------------------------------

    def signal_exists(self, search_signal):
        for s in self.get_full_path(search_signal, -1, -1, ""):
            pass
        return 1  # always return existence
    # ---This Method will not really peek the signal on non interactive mode and return 0
    # -------------------------------------------------------------------------------------------------------------

    def signal_peek(self, signal_path, lsb, msb, selector="none"):
        for s in self.get_full_path(signal_path, lsb, msb, selector):
            self.interface.signal_peek(signal_path)
        return 0
    # --This could not be really be verified on offline , just making directive to make such verification on stimulus execution

    def signal_check(self, signal_path, lsb, msb, value, selector):
        for s in self.get_full_path(signal_path, lsb, msb, selector):
            self.interface.check_signal(s, value)
        return 1
    # --This could not be really be verified on offline , just making directive to make such verification on stimulus execution

    def signal_check_not(self, signal_path, lsb, msb, value, selector):
        for s in self.get_full_path(signal_path, lsb, msb, selector):
            self.interface.check_signal_not(s, value)
        return 1
    # -------------------------------------------------------------------------------------------------------------

    def verify_all_collected_signals(self):
        if("disable_signal_verification" in list(CFG["HPL"].keys()) and CFG["HPL"]["disable_signal_verification"]):
            return
        normalized_by_action = {}
        processed_signal = []
        for sig in list(self.captured_signals.keys()):
            for act in self.captured_signals[sig]:
                if(sig not in processed_signal):  # MlcInvalidate
                    if(act not in list(normalized_by_action.keys())):
                        normalized_by_action[act] = []
                    normalized_by_action[act].append(sig)
                    processed_signal.append(sig)
        # --------------------------------
        for act in sorted(normalized_by_action.keys()):
            self.interface.print_header(("Signal Verification for action: %s") % (act))
            for sig in sorted(normalized_by_action[act]):
                self.interface.signal_peek(sig)


# -------------------------------------
"""
  class hpl_SignalManager_itpp - inherits from hpl_SignalManager_non_interactive class and define overloads for itpp format only
"""


class hpl_SignalManager_itpp(hpl_SignalManager_non_interactive):
    # -------------------------------------------------------------------------------------------------------------
    def __init__(self, interface=None, uiptr=None):
        hpl_SignalManager_non_interactive.__init__(self, interface, uiptr)


"""
  class hpl_SignalManager_interactive_socket - inherits from hpl_SignalManager_interactive class and define overloads interactive simulation over sockets
"""


class hpl_SignalManager_interactive_socket(hpl_SignalManager_interactive):
    # -------------------------------------------------------------------------------------------------------------
    def __init__(self, interface=None, uiptr=None):
        hpl_SignalManager_interactive.__init__(self, interface, uiptr)


"""
  class hpl_SignalManager_spf - inherits from hpl_SignalManager_non_interactive class and define overloads for itpp format only
"""


class hpl_SignalManager_spf(hpl_SignalManager_non_interactive):
    # -------------------------------------------------------------------------------------------------------------
    def __init__(self, interface=None, uiptr=None):
        hpl_SignalManager_non_interactive.__init__(self, interface, uiptr)
