from htd_utilities import *
from htd_collaterals import *
from htd_hpl_not_interactive_interface import *
from htd_patmod_manager import HtdPatmod, HtdPatmodUsage
import re

# ----------------------------
#
# -------------------------------


class hpl_spf_interface(hpl_not_interactive_interface):

    def __init__(self, filename, uiptr):
        self.silent_stream = open("SilentModeStream", "w", 1)
        htdte_logger.inform("Creating Silent Mode activity Stream file:SilentModeStream")
        self.file_name = filename
        self.logStream = open(self.file_name, "w", 1)
        htdte_logger.inform(("Creating SPF file:%s") % (self.file_name))
        self.__isstream = 0
        self.current_stream = self.logStream
        self.uiptr = uiptr
        self.interface_debug_mode = True if ("InterfaceDebugMode" in list(CFG["HPL"].keys()) and CFG["HPL"][
                                             "InterfaceDebugMode"] in ["1", "True", "TRUE"]) else False
        self.sync_started = 0
        # ---Add header
        for l in htdte_logger.get_header():
            self.print_header(l)
        self.logStream.write("@set tap_elaborate_label on;\n")

    # --------------------------------
    def tap_compression_off(self): self.logStream.write("pass itpp \"no_compress: start;\";\n")

    def tap_compression_on(self): self.logStream.write("pass itpp \"no_compress: stop;\";\n")

    def change_output_stream(self, name):
        htdte_logger.inform(("Close the current stream : %s") % self.file_name)
        self.logStream.close()
        self.logStream = open(name, "w", 1)
        htdte_logger.inform(("Creating ITPP file:%s") % (name))
        self.__isstream = 0
        # ---Add header
        for l in htdte_logger.get_header():
            self.print_header(l)
        self.logStream.write("@set tap_elaborate_label on;\n")
    # ----------------------------

    def tap_command_low_level_mode_enabled(self): return False

    # -----------------------------
    def close(self):
        if(not self.__isstream):
            htdte_logger.inform("Closing SPF File")
            self.print_spf_template_patmods()
            self.logStream.close()

    def print_spf_template_patmods(self):

        if not HTD_INFO.patmods.global_patmods_enabled():
            return None

        spf_template = open("spf.patmods.template", "w")
        spf_template.write("hvm_rule_spec {\n")
        spf_template.write("    patmod_spec {\n")
        for patmod in HTD_INFO.patmods:
            assert isinstance(patmod, HtdPatmod)    # asserting type for the variable patmod for intellij

            # Print the patmod header
            spf_template.write("        %s {\n" % (patmod.name))
            spf_template.write("            desc: \"%s\";\n" % (patmod.desc))

            # Print usages if there are any
            print_usages = False
            usages_str = ""
            if patmod.get_num_usages() > 0:
                usages_str += "            usage {\n"
                for main_usage in patmod.get_usages():
                    # asserting type for the variable usage for intellij
                    assert isinstance(main_usage, HtdPatmodUsage)

                    usages_to_print = list()

                    if main_usage.network == "tap":
                        usages_to_print.append(main_usage)

                    if len(main_usage.related_usages) > 0:
                        for rel_usage in main_usage.related_usages:
                            # asserting type for the variable usage for intellij
                            assert isinstance(rel_usage, HtdPatmodUsage)
                            if rel_usage.network == "tap":
                                usages_to_print.append(rel_usage)

                    for usage in usages_to_print:
                        print_usages = True
                        # asserting type for the variable usage for intellij
                        assert isinstance(usage, HtdPatmodUsage)

                        # write the agent and register
                        usages_str += "                %s=>%s" % (usage.agent, usage.register)

                        # Write the field if it is present
                        if usage.field is not None and usage.field != "":
                            usages_str += "->%s" % (usage.field)

                        # Write the bits if they are present
                        if usage.bits is not None and usage.bits != "":
                            usages_str += "[%s]" % (usage.bits)
                        usages_str += ";\n"

                usages_str += "            }\n"

                # Only print the usages string if we actually found usages to print. Otherwise SPF complains.
                if print_usages:
                    spf_template.write(usages_str)

            spf_template.write("            values {\n")

            # Print Values
            for value_name in patmod.values:
                value = patmod.values[value_name]
                if value != "X":
                    value = int(value)
                else:
                    value = "'bX"
                spf_template.write("                %s = %s;\n" % (value_name, value))
            spf_template.write("            }\n")   # End values

            spf_template.write("        }\n")   # End patmod_name
        spf_template.write("    }\n")   # End patmod_spec
        spf_template.write("}\n")   # End hvm_rule_spec

    # -----Silent mode , the stream is refirected to another file-----------------------
    def set_silent_mode(self):
        self.logStream = self.silent_stream

    # ------------------------
    def unset_silent_mode(self):
        self.logStream = self.current_stream

    # --------------------
    def get_model_time(self): return -1

    # ---------------------------
    def send_action(self, line):
        if(not self.uiptr.silent_mode and not self.uiptr.current_action.get_curr_flow().is_verification_mode()):
            self.logStream.write(line)

    # -------------------------------------
    def add_log(self, line):
        no_new_lines = line.split('\n')
        for l in no_new_lines:
            if(len(l)):
                self.logStream.write(("pass itpp \"print_log: %s ;\";\n") % (l.replace("rem:", "")))

    # --------------------------------------
    def print_header(self, line):
        no_new_lines = line.split('\n')
        line_limit = 250
        if("comment_length_limit" in list(CFG["HPL"].keys())):
            line_limit = CFG["HPL"]["comment_length_limit"]
        for l in no_new_lines:
            if(len(l)):
                self.logStream.write(("comment \"%s\";\n") %
                                     (l[:line_limit].replace('"', "").replace('"', "")))

    # --------------------------------------
    def add_comment(self, line):
        no_new_lines = line.split('\n')
        for l in no_new_lines:
            if(len(l)):
                #self.logStream.write(("pass itpp \"rem: comment: %s \";\n")%(l.replace("rem:","")))
                if(re.search(r"Start\s+Action", l) or re.search(r"Start\s+Flow", l) or re.search(r"Start\s+Segment", l)):
                    self.logStream.write(("pass itpp \"rem: comment: %s ;\";\n\n") %
                                         (l.replace("rem:", "").replace('"', "")))
                else:
                    self.logStream.write(("pass itpp \"rem: comment: %s ;\";\n") %
                                         (l.replace("rem:", "").replace('"', "")))

    # -----------------------------
    def set_pattern_info(self, message):
        no_new_lines = message.split('\n')
        for l in no_new_lines:
            self.logStream.write(("pass itpp \"comment: %s ;\";\n") % (l.replace('"', "")))

    # -----------------------------------
    def signal_force(self, full_path, value):
        if (isinstance(value, int)):
            self.logStream.write(("pass itpp \"rem: force_signal %s 0x%x ;\";\n") %
                                 (full_path, value))
        elif (value == "x"):
            self.logStream.write(("pass itpp \"rem: force_signal %s x ;\";\n") % (full_path))
        elif (value == "z"):
            self.logStream.write(("pass itpp \"rem: force_signal %s z ;\";\n") % (full_path))
        else:
            htdte_logger.error(("Illegal signal value type :%s") % (value))

    def signal_unforce(self, full_path):
        self.logStream.write(("pass itpp \"rem: release_signal %s ;\";\n") % (full_path))

    def signal_peek(self, full_path, value=-1):
        if(value < 0):
            if(not isinstance(full_path, list)):
                self.logStream.write(("pass itpp \"rem: peek_signal %s ;\";\n") % (full_path))
            else:
                for sig in full_path:
                    self.logStream.write(("pass itpp \"rem: peek_signal %s ;\";\n") % (sig))
        else:
            if(not isinstance(full_path, list)):
                self.logStream.write(
                    ("pass itpp \"rem: peek_signal %s 0x%x;\";\n") % (full_path, value))
            else:
                for sig in full_path:
                    self.logStream.write(
                        ("pass itpp \"rem: peek_signal %s  0x%x;\";\n") % (sig, value))

    # ---------------------------------
    def signal_poke(self, full_path, value):
        self.logStream.write(("pass itpp \"rem: deposit_signal %s 0x%x ;\";\n") %
                             (full_path, value))

    def check_signal(self, full_path, value):
        self.logStream.write(("pass itpp \"rem:   peek_signal  %s 0x%x ;\";\n") %
                             (full_path, value))  # Fatal

    def check_signal_not(self, full_path, value):
        self.logStream.write(("pass itpp \"rem:   inv_peek_signal  %s 0x%x ;\";\n") %
                             (full_path, value))  # Fatal

    def signal_exists(self, full_path): return True

    # -------Need ITPP EXTENSIONS----------------------
    def signal_set(self, full_path, value):
        if(not isinstance(value, int) and not isinstance(value, int)):
            htdte_logger.error(
                ("Improper value type received : expected int , while got:%s") % (type(value)))
        self.logStream.write(("pass itpp \"rem: deposit_signal %s 0x%x ;\";\n") % (
            full_path, value))  # TODO - Check with Rob if this aplicable also for DP!!!

    # -------------------------------------------------
    def ext_signalset_poke(self, signal_l, signal_values_l, delay=-1):
        if(not isinstance(signal_l, list)):
            htdte_logger.error("Wrong \"signal_l\" argument type: expected list of signals . ")
        if(not isinstance(signal_values_l, list)):
            htdte_logger.error(
                "Wrong \"signal_values_l\" argument type: expected list of expected signal values . ")
        if(len(signal_l) != len(signal_values_l)):
            htdte_logger.error(("Error in  \"signal_values_l\" vs' \"signal_l\" arguments assignment , expected same list size , while len(\"signal_values_l\")=%d,len(\"signal_l\")=%d . ") % (
                len(signal_values_l), len(signal_l)))
        sigs_entry = ""
        for i in range(0, len(signal_l)):
            sigs_entry += (" %s(%s)") % (signal_l[i], signal_values_l[i])
        self.logStream.write(("pass itpp \"vector: %s, %d;\";\n") %
                             (sigs_entry, delay if delay >= 0 else 1))

    # -------------------------------------------------------------------------
    def signal_wait(self, full_path, value, wait_time):
        if(not isinstance(full_path, list)):
            if("Temp" in list(CFG.keys())):
                self.logStream.write(("pass itpp \"rem: poll_signal  %s 0x%x %d%s;\";\n") % (
                    full_path, value, wait_time, CFG["HTD_Clocks_Settings"]["sim_time_unit"]))
            else:
                self.logStream.write(
                    ("pass itpp \"rem: poll_signal  %s 0x%x ;\";\n") % (full_path, value))
        else:
            for sig in full_path:
                if("Temp" in list(CFG.keys())):
                    self.logStream.write(("pass itpp \"rem: poll_signal  %s 0x%x %d%s;\";\n") % (
                        sig, value, wait_time, CFG["HTD_Clocks_Settings"]["sim_time_unit"]))
                else:
                    self.logStream.write(
                        ("pass itpp \"rem: poll_signal  %s 0x%x ;\";\n") % (sig, value))

    # -------------------------------------------------------------------------
    def clock_wait(self, full_path, clock_frequency, timeout):
        self.logStream.write(("pass itpp \"rem: poll_clock  %s %s ;\";\n") % (full_path, clock_frequency))

    def clock_check_average(self, full_path, clock_frequency, average):
        self.logStream.write(("pass itpp \"rem: check_clock  %s %s %s ;\";\n") % (full_path, clock_frequency, average))

    # -------------------------------------------------------------------------
    def start_clock(self, clock):
        self.logStream.write(("pass itpp \"start_clk: %s;\";\n" % (clock)))

    def stop_clock(self, clock):
        self.logStream.write(("pass itpp \"stop_clk: %s;\";\n" % (clock)))

    def wait_clock_num(self, width, clock):

        period_orig_clock = self.uiptr.hplClockMgr.get_clock_period(clock)
        period_vec_clock = self.uiptr.hplClockMgr.get_clock_period(CFG["HPL"]["PatVecClock"])
        NumOfVecClocks = int(math.ceil(width * period_orig_clock
                                       / (period_vec_clock if(period_vec_clock > 0) else 1)))
        if(NumOfVecClocks < 0):
            NumOfVecClocks = 1

        if (self.uiptr.signal_wait_mode == "silicon"):
            if ("delay_statement" in list(CFG["HPL"].keys())):
                self.logStream.write(("pass itpp \"%s\";\n") %
                                     ((CFG["HPL"]["delay_statement"]) % (NumOfVecClocks)))
            else:
                self.logStream.write(("pass itpp \"delay: %s(%d);\";\n") % (
                    self.uiptr.hplClockMgr.get_clock_rtl_path(CFG["HPL"]["PatVecClock"]), NumOfVecClocks))
        else:
            width_in_orig_clocks = self.uiptr.hplClockMgr.get_clock_period(clock)
            width_in_vec_clock = self.uiptr.hplClockMgr.get_clock_period(clock)
            self.logStream.write(("pass itpp \"delay: %s(%d);\";\n") % (
                self.uiptr.hplClockMgr.get_clock_rtl_path(CFG["HPL"]["PatVecClock"]), NumOfVecClocks))
            #self.logStream.write(("vector: xxtms(0),%d;\n") % (NumOfVecClocks))

    # -------------------------------------------------------------
    # -------------------------------------------------------------------------
    def wait_clock_edge(self, clock, edge):
        return

    # ---------------------------------------------------------------
    # -------------------------------------------------------------------------
    def wait_clock_modulo(self, clock, modulo):
        if (self.uiptr.sync_enabled):
            period_orig_clock = self.uiptr.hplClockMgr.get_clock_period(clock)
            period_vec_clock = self.uiptr.hplClockMgr.get_clock_period(CFG["HPL"]["PatVecClock"])
            NumOfVecClocks = int(math.ceil(modulo * period_orig_clock
                                           / (period_vec_clock if(period_vec_clock > 0) else 1)))
            if(NumOfVecClocks < 0):
                NumOfVecClocks = 1

            if("PostAlign" in list(CFG["HPL"].keys())):
                self.post_align = CFG["HPL"]["PostAlign"]
            else:
                self.post_align = 1

            # Need to check for silent/verification modes here, since otherwise this
            # runonce flag gets tripped early.
            if (self.sync_started != 1 and not self.uiptr.silent_mode and not self.uiptr.current_action.get_curr_flow().is_verification_mode() and self.post_align):
                self.write_itpp_cmd(("start_sync: yclk, %s, %d;") % (
                    self.uiptr.hplClockMgr.get_clock_rtl_path(CFG["HPL"]["PatVecClock"]), NumOfVecClocks))
                self.sync_started = 1
            # Need to check for silent/verification modes here, since otherwise this
            # runonce flag gets tripped early.
            if (self.post_align):
                self.write_itpp_cmd("align_sync: yclk;")
        else:
            self.write_itpp_cmd("rem: comment: SYNC DISABLED;")

    # ----------------------------------------------------------
    # -------------------------------------------------------------------------
    def write_itpp_cmd(self, cmd):
        self.logStream.write(("pass itpp \"%s\";\n") % (cmd.strip('\n\r')))

    def write_spf_cmd(self, cmd):
        self.logStream.write(("%s\n") % (cmd.strip('\n\r')))

    def execute_signal(self, cmd):
        self.logStream.write(("execute %s;\nflush;\n") % (cmd.strip('\n\r')))

    # --------Tap Parameters instrumental printout-------
    # -------------------------------------------------------------------------
    def tap_parameters_instrumetal_print(
        self, irname, agent, parallel_mode, assigned_fields, attributes, labels, masks, strobe, capture, tdolabels): pass

    # -------------------------------------------------------------------------
    def label(self, label, label_domain=None):
        # Clean up the label to ensure there are no "." in it
        # spf does not allow labels with spaces - replacing with _
        label = re.sub(r'\.', r'_', label)
        label = re.sub(r'\s', r'_', label)
        if CFG["HPL"].get("NEW_LABEL_SPEC") == 1 and CFG["HPL"].get("LabelsInAllDomains") == 1:
            self.logStream.write(("pass itpp \"label: %s [Domain: ALL];\"; \n") % (label))
        elif label_domain is not None:
            if (label_domain not in list(CFG["HPL"].keys()) or CFG["HPL"].get(label_domain) == ""):
                htdte_logger.error('Missing obligatory key -> %s in TE cfg HPL category. Please specify the domain to print action label. Example: <Var key=\"%s\"        value=\"<comma separated domain names>\" />' % (label_domain, label_domain))
            else:
                self.logStream.write(("label \"%s\" [Domain: %s]; \n") % (label, CFG["HPL"][label_domain]))
        else:
            self.logStream.write(("label \"%s\"; \n") % (label))

    # -------------------------------------------------------------------------
    def to_tap_state(self, to_state):
        if(self.uiptr.current_action.get_curr_flow().is_verification_mode()):
            return
        if(to_state == "IDLE"):
            self.logStream.write("pass itpp \"to_state: Run-Test/Idle ;\";\n")
        elif(to_state == "SELECTDR"):
            self.logStream.write("pass itpp \"to_state: Select-DR-Scan ;\";\n")
        elif(to_state == "CAPTUREDR"):
            self.logStream.write("pass itpp \"to_state: Capture-DR ;\";\n")
        elif(to_state == "SHIFTDR"):
            self.logStream.write("pass itpp \"to_state: Shift-DR ;\";\n")
        elif(to_state == "EXIT1DR"):
            self.logStream.write("pass itpp \"to_state: Exit1-DR ;\";\n")
        elif(to_state == "PAUSEDR"):
            self.logStream.write("pass itpp \"to_state: Pause-DR ;\";\n")
        elif(to_state == "EXIT2DR"):
            self.logStream.write("pass itpp \"to_state: Exit2-DR ;\";\n")
        elif(to_state == "UPDATEDR"):
            self.logStream.write("pass itpp \"to_state: Update-DR ;\";\n")
        elif(to_state == "SELECTIR"):
            self.logStream.write("pass itpp \"to_state: Select-IR-Scan ;\";\n")
        elif(to_state == "CAPTUREIR"):
            self.logStream.write("pass itpp \"to_state: Capture-IR ;\";\n")
        elif(to_state == "SHIFTIR"):
            self.logStream.write("pass itpp \"to_state: Shift-IR ;\";\n")
        elif(to_state == "EXIT1IR"):
            self.logStream.write("pass itpp \"to_state: Exit1-IR ;\";\n")
        elif(to_state == "PAUSEIR"):
            self.logStream.write("pass itpp \"to_state: Pause-IR ;\";\n")
        elif(to_state == "EXIT2IR"):
            self.logStream.write("pass itpp \"to_state: Exit2-IR ;\";\n")
        elif(to_state == "UPDATEIR"):
            self.logStream.write("pass itpp \"to_state: Update-IR ;\";\n")
        else:
            htdte_logger.error(
                ("Invalid tap state value - \"%s\".\nExpected: SELECTDR,CAPTUREDR,SHIFTDR,EXIT1DR,PAUSEDR,EXIT2DR,UPDATEDR,SELECTIR,CAPTUREIR,SHIFTIR,EXIT1IR,PAUSEIR,EXIT2IR,UPDATEIR") % (to_state))
    # ------------------------------
    # -------------------------------------------------------------------------

    def high_level_tap_bfm_transactor(self, irname, ircode, irsize, drsize, agent, dr_by_fields, dr_read_byfields, dri,
                                      dro, parallel, labels, mask, capture, read_bitmap, pscand_en, pscand_delay, pscand_pins,
                                      patmods, patmodgroups, ir_tdi_align_label, field_labels_per_action, label_domain, action_name, shadow_agents="", postfocus_delay=0, dronly=0,
                                      overshift_en=0, overshift_marker_value=None, dba_mode=0):

        # some ir's are tricky if using spf output. Make sure we are using the correct agent
        # SPF expects the GLUE Tap instead of CLTAP when accessing TAPSTATUS and TAPCFG
        agent = HTD_INFO.tap_info.get_real_agent(agent, irname)

        # determines label behavior on align with tdi vector
        tdi_align = (CFG["HPL"].get("tdi_align_label") == 1)

        label_prefix = ""
        if CFG["HPL"].get("action_name_label_prefix") == 1:
            label_prefix = action_name + "__"

        if label_domain is not None:
            if (label_domain not in list(CFG["HPL"].keys()) or CFG["HPL"].get(label_domain) == ""):
                htdte_logger.error('Missing obligatory key -> %s in TE cfg HPL category. Please specify the domain to print field labels for action. Example: <Var key=\"%s\"        value=\"<comma separated domain names>\" />' % (label_domain, label_domain))
            else:
                label_domain = CFG["HPL"][label_domain]

        if (pscand_en == 1):
            self.logStream.write("construct itpp pscan_pin_group %s;\n" % (",".join(pscand_pins)))
            pscand_delay_str = "@set tap_pscan_delay "

            # Construct the pscan_delay string
            for i in range(0, len(pscand_pins)):
                if i > 0:
                    pscand_delay_str = pscand_delay_str + ", "

                pscand_delay_str = pscand_delay_str + pscand_pins[i] + " = " + str(pscand_delay[i])
            pscand_delay_str = pscand_delay_str + ";\n"
            self.logStream.write(pscand_delay_str)
            self.logStream.write("@set tap_pscan_mode on;\n")

        if (overshift_en == 1):
            self.logStream.write("@set tap_overshift_mode on;\n")
            if (overshift_marker_value is not None):
                self.logStream.write(("@set tap_overshift_marker "
                                      + "\"%s\"" + ";\n") % (overshift_marker_value))

        # orubin/nfar
        # it seems like parallel mode does not work properly and we are not sure how the SPF decides which agents are parallel
        # so parallel mode should apply only for CORE/CBO
        if (parallel and "parallel_cbo_core_only" in list(CFG["HPL"].keys()) and CFG["HPL"]["parallel_cbo_core_only"] == 1):
            if (not agent.startswith("CORE") and not agent.startswith("CBO") and not agent.startswith("ICEBO_HIP")):
                parallel = 0

        # ---FIXME - parallel mode need to be configured by DTS help
        # PARALLEL??????????
        # Labels,masks,ctvs
        # label : labelShift_DUNIT_DDRIO_TARGET_REG_DR@1;
        # used mainly for TapNetwork for adding shadow agents in format : , =<agent
        shadow_agents_str = ""
        shadow_agents_l = []
        if(shadow_agents != ""):
            shadow_agents_l = shadow_agents.split(",")
        for agnt in shadow_agents_l:
            shadow_agents_str += (", =%s") % (agnt)

        # dynamic base address, jitbit29067
        dba = ""
        if dba_mode:
            dba = " (DBA)"

        # -----------------------------------
        parallel_tap_agents = HTD_INFO.tap_info.get_taplink_parallel_agents_by_agents(agent)
        if(parallel and parallel_tap_agents is not None and len(parallel_tap_agents) > 1 and parallel_tap_agents[0] != ('no instances for TAP %s') % (agent)):
            focus_agents = ""
            for a in parallel_tap_agents:
                focus_agents += (" %s") % (HTD_INFO.tap_info.get_real_agent(a,irname))

            self.logStream.write(("focus_tap %s%s%s;\n") % (focus_agents, shadow_agents_str, dba))
        else:
            self.logStream.write(("focus_tap %s%s%s;\n") % (agent, shadow_agents_str, dba))

        # -----------------------------------

        # Add patmod code
        organized_patmods = dict()      # Place to store patmod prints by var name
        for patmod in patmods:
            var_name = patmod["name"]

            # Make sure organized_patmods has a key of var_name
            if var_name not in organized_patmods:
                organized_patmods[var_name] = list()

            field = patmod["field"]
            bits = "[%s]" % patmod["bits"] if patmod["bits"] is not None and patmod["bits"] != "" else ""
            patmod_type = patmod["type"]
            label = patmod["label"]

            # For tap raw shift the field should only be DR, for normal tap writes it should be Register->field
            if field != "DR":
                if field is None:
                    field = irname
                else:
                    field = "%s->%s" % (irname, field)

            # Store info for all patmods using this var
            organized_patmods[var_name].append("%s%s = \"%s\"(%s)" % (field, bits, label, patmod_type))

        # Print the actual patmods
        for key, value in list(organized_patmods.items()):
            self.logStream.write("patmod %s = {%s};\n" % (key, ", ".join(value)))

        for group in patmodgroups:
            self.write_itpp_cmd("patmod_group: {name}, {mode}, {params};".format(name=group.name, mode=group.mode, params=", ".join(group.get_members())))

        # -----------------------------------
        if(postfocus_delay > 0):
            self.logStream.write(("pass itpp \"vector: TMS(0), %d;\";\n") % (postfocus_delay))

        # -----------------------------------
        if(dri < 0 and dro < 0 and (len(list(dr_read_byfields.keys())) or len(list(dr_by_fields.keys())))):
            label_statement = ""
            label_assigned = False
            startdr_label_assigned = False
            enddr_label_assigned = False
            if CFG["HPL"].get("NEW_LABEL_SPEC") is 1:

                for bit in list(labels.keys()):
                    if labels[bit] == "":
                        continue
                    label_statement = ("%s%s%s[%d]=\"%s\"") % (label_statement, "" if(label_statement == "")
                                                               else ",", irname, bit, self.uiptr.get_indexed_label(labels[bit]))
                    label_assigned = True
                if(label_assigned):
                    self.logStream.write(("label \"%s\", select_dr={%s}%s;\n") % ("", label_statement, " [Domain: %s]" % label_domain if(label_domain is not None) else ""))
            else:
                for bit in list(labels.keys()):
                    # Clean up .'s from the label as spf doesn't like them
                    labels[bit] = re.sub(r'\.', r'_', labels[bit])
                    # for the case of starting bit, add StartDr keyword in label
                    if(bit == 0 and CFG["HPL"].get("automatic_labels_ena") == 1):
                        label_statement = ("%s%s%s[%d]=\"%sStartDr__%s\" %s") % (label_statement, "" if(
                            label_statement == "") else ",", irname, bit, label_prefix, labels[bit], "(in)" if tdi_align else "")
                        startdr_label_assigned = True
                    # for the case of ending bit, add EndDr keyword in label
                    elif(bit == (drsize - 1) and bit != 0 and CFG["HPL"].get("automatic_labels_ena") == 1):
                        label_statement = ("%s%s%s[%d]=\"%sEndDr__%s\" %s") % (label_statement, "" if(
                            label_statement == "") else ",", irname, bit, label_prefix, labels[bit], "(in)" if tdi_align else "")
                        enddr_label_assigned = True
                    # everything else in middle, label without any additional prefix/suffix
                    else:
                        label_statement = ("%s%s%s[%d]=\"%s%s\" %s") % (label_statement, "" if(label_statement == "")
                                            else ",", irname, bit, label_prefix, self.uiptr.get_indexed_label(labels[bit]), "(in)" if tdi_align else "")
                        if(bit == 0):
                            startdr_label_assigned = True
                        elif(bit == (drsize - 1)):
                            enddr_label_assigned = True
                    label_assigned = True

                # for the case if starting bit is not being labeled from the above for loop
                if((CFG["HPL"].get("automatic_labels_ena") == 1 and not startdr_label_assigned) or (field_labels_per_action and not startdr_label_assigned)):
                    label_statement = ("%s%s%s[%d]=\"%s%s\" %s") % (label_statement, "" if(label_statement == "") else ",",
                                        irname, 0, label_prefix, self.uiptr.get_indexed_label(("StartDr_%s_%s") % (agent, irname)), "(in)" if tdi_align else "")
                    label_assigned = True

                # for the case if ending bit is not being labeled from the above for loop
                if((CFG["HPL"].get("automatic_labels_ena") == 1 and not enddr_label_assigned and drsize > 1) or (field_labels_per_action and not enddr_label_assigned and drsize > 1)):
                    label_statement = ("%s%s%s[%d]=\"%s%s\" %s") % (label_statement, "" if(label_statement == "") else ",",
                                        irname, drsize - 1, label_prefix, self.uiptr.get_indexed_label(("EndDr_%s_%s") % (agent, irname)), "(in)" if tdi_align else "")
                    label_assigned = True

                # actual printing
                if(label_assigned):
                    if(ir_tdi_align_label):
                        self.logStream.write(("label \"%s\", select_ir={%s=\"%s\" %s}, select_dr={%s}%s;\n") % (
                            self.uiptr.get_indexed_label("LABEL_TEMPLATE", "%s_%s" % (agent, irname)), agent, "%s_%s_IR" % (agent, irname), "(in)", label_statement, " [Domain: %s]" % label_domain if(label_domain is not None) else ""))
                    else:
                        self.logStream.write(("label \"%s\", select_dr={%s}%s;\n") % (
                            self.uiptr.get_indexed_label("LABEL_TEMPLATE", "%s_%s" % (agent, irname)), label_statement, " [Domain: %s]" % label_domain if(label_domain is not None) else ""))

        # ------Register setting
            if(dronly):
                self.logStream.write("@set tap_skip_ir on;\n")

            if("tap_set_during_strobe_mode" not in list(CFG["HPL"].keys()) or CFG["HPL"]["tap_set_during_strobe_mode"] not in [0, "False", "FALSE"]):
                for f in list(dr_by_fields.keys()):
                    field_name = HTD_INFO.tap_info.normalize_field_name(irname, agent, f)
                    lsb = HTD_INFO.tap_info.get_field_lsb(irname, agent, field_name)
                    msb = HTD_INFO.tap_info.get_field_msb(irname, agent, field_name)
                    self.logStream.write(("set %s->%s = 'b%s;\n") % (irname, field_name,
                                                                     util_int_to_binstr(dr_by_fields[f], msb - lsb + 1)))
            for f in list(dr_read_byfields.keys()):
                if(dr_read_byfields[f] >= 0):
                    field_name = HTD_INFO.tap_info.normalize_field_name(irname, agent, f)
                    lsb = HTD_INFO.tap_info.get_field_lsb(irname, agent, field_name)
                    msb = HTD_INFO.tap_info.get_field_msb(irname, agent, field_name)
                    tdo_str = list(util_int_to_binstr(dr_read_byfields[f], msb - lsb + 1))

                    for i in range(len(tdo_str) - 1, -1, -1):
                        if((i + lsb) not in read_bitmap):
                            tdo_str[len(tdo_str) - 1 - i] = 'X'

                    self.logStream.write(("compare %s->%s = 'b%s;\n") %
                                         (irname, field_name, ''.join(tdo_str)))

            for f in mask:
                #ticket_26285
                match = re.search(r"\[\d{1,2}:\d{1,2}]", f)
                if (match != None):
                    field = f[0:match.start()].upper()
                else:
                    field = f
                field_name = HTD_INFO.tap_info.normalize_field_name(irname, agent, field)
                if (field_name in f):
                    self.logStream.write(("mask %s->%s;\n") % (irname, f))
                #field_name = HTD_INFO.tap_info.normalize_field_name(irname, agent, f)
                #self.logStream.write(("mask %s->%s;\n") % (irname, field_name))
            for f in capture:
                field_name = HTD_INFO.tap_info.normalize_field_name(irname, agent, f)
                self.logStream.write(("capture %s->%s;\n") % (irname, field_name))
        else:
           # if(len(capture.keys())>0 or len(mask.keys())>0 ):
           #     htdte_logger.error( ("The mask/capture assignment restricted by per field tap access only ."))

            ir_tdi = util_int_to_binstr(ircode, irsize)
            dr_tdi_str = util_int_to_binstr(dri if(dri >= 0) else 0, drsize)
            #ir_tdo_str=util_int_to_binstr(dri if (dri>=0)else 0, drsize)
            #dr_tdo_str=util_int_to_binstr(dro,drsize) if (dro>0) else 'X'*drsize

            x = 1
            b = 0
            ir_tdo_str = ""
            ir_tdo_str_l = ""

            # ----------------------------|RESET:GSD|-----------------------------------------------
            dr_tdo_str = util_int_to_binstr(dro, drsize) if (dro >= 0) else 'X' * drsize
            # Add Mask to Dro input
            if(isinstance(mask, str)):
                mask = mask[::-1]
                mask = mask.replace("0b", "")
                new_str = ""
                for i in range(len(str(mask))):
                    if(mask[i] == "0"):
                        new_str += "X"
                    else:
                        new_str += dr_tdo_str[i]
                dr_tdo_str = new_str
            dr_tdo_str_l = [dr_tdo_str[i:i + 32] for i in range(0, len(dr_tdo_str), 32)]
            # ---------------------------------------------------------------------------------------
            dr_tdi_str_l = [dr_tdi_str[i:i + 32] for i in range(0, len(dr_tdi_str), 32)]

            # -------------------------------------
            dr_tdi = ("\n ,dr_tdi='b%s") % dr_tdi_str_l[0] if len(dr_tdi_str_l) else ""
            for i in range(1, len(dr_tdi_str_l)):
                dr_tdi += ("\n         'b%s") % (dr_tdi_str_l[i])

            # -------------------------------------

            dr_tdo = ("\n,dr_tdo= 'b%s") % dr_tdo_str_l[0] if len(dr_tdo_str_l) else ""
            for i in range(1, len(dr_tdo_str_l)):
                dr_tdo += ("\n         'b%s") % (dr_tdo_str_l[i])

            ir_tdo = ("\n,ir_tdo= 'b%s") % ir_tdo_str_l[0] if len(ir_tdo_str_l) else ""
            for i in range(1, len(ir_tdo_str_l)):
                ir_tdo += ("\n         'b%s") % (ir_tdo_str_l[i])

            label_assigned = False
            startdr_label_assigned = False
            enddr_label_assigned = False
            label_statement = ""
            if CFG["HPL"].get("NEW_LABEL_SPEC") is 1:

                for bit in list(labels.keys()):
                    if labels[bit] == "":
                        continue
                    label_statement = ("%s%s%s[%d]=\"%s\"") % (label_statement, "" if(label_statement == "")
                                                               else ",", "DR", bit, self.uiptr.get_indexed_label(labels[bit]))
                    label_assigned = True
                if(label_assigned):
                    self.logStream.write(("label \"%s\", select_dr={%s}%s;\n") % ("", label_statement, " [Domain: %s]" % label_domain if(label_domain is not None) else ""))

            else:
                for bit in list(labels.keys()):
                    # Clean up .'s from the label as spf doesn't like them
                    labels[bit] = re.sub(r'\.', r'_', labels[bit])
                    if(bit == 0 and CFG["HPL"].get("automatic_labels_ena") == 1):
                        #temp_label = self.uiptr.get_indexed_label("StartDr__%s__%s__%s" % (agent, irname, drsize))
                        #temp_label += "__%s" % (labels[bit])
                        temp_label = "%sStartDr__%s" % (label_prefix, labels[bit])
                        label_statement = ("%s%s%s[%d]=\"%s\" %s") % (label_statement,
                                                                      "" if(label_statement == "") else ",", irname, bit, temp_label, "(in)" if tdi_align else "")
                        startdr_label_assigned = True
                    elif(bit == (drsize - 1) and bit != 0 and CFG["HPL"].get("automatic_labels_ena") == 1):
                        #temp_label = self.uiptr.get_indexed_label("EndDr__%s__%s" % (agent, irname))
                        temp_label = "%sEndDr__%s" % (label_prefix, labels[bit])
                        label_statement = ("%s%s%s[%d]=\"%s\" %s") % (label_statement,
                                                                      "" if(label_statement == "") else ",", irname, bit, temp_label, "(in)" if tdi_align else "")
                        enddr_label_assigned = True
                    else:
                        label_statement = ("%s%s%s[%d]=\"%s%s\" %s") % (label_statement, "" if(label_statement == "")
                                            else ",", "DR", bit, label_prefix, self.uiptr.get_indexed_label(labels[bit]), "(in)" if tdi_align else "")
                    label_assigned = True

                if not enddr_label_assigned and drsize > 1:
                    temp_label = self.uiptr.get_indexed_label("%sEndDr__%s__%s" % (label_prefix, agent, irname))
                    label_statement = ("%s%s%s[%d]=\"%s\" %s") % (label_statement,
                                                                  "" if(label_statement == "") else ",", irname, drsize - 1, temp_label, "(in)" if tdi_align else "")
                    enddr_label_assigned = True

                if (label_assigned):
                    if (dri >= 0 or dro >= 0):
                        label_statement = label_statement.replace("%s[" % (irname), "DR[")
                    if(ir_tdi_align_label):
                        self.logStream.write(("label \"%s\", select_ir={%s=\"%s\" %s}, select_dr={%s}%s;\n") % (
                            self.uiptr.get_indexed_label("LABEL_TEMPLATE", "%s_%s" % (agent, irname)), agent, "%s_%s_IR" % (agent, irname), "(in)", label_statement, " [Domain: %s]" % label_domain if(label_domain is not None) else ""))
                    else:
                        self.logStream.write(("label \"%s\", select_dr={%s}%s;\n") % (
                            self.uiptr.get_indexed_label("LABEL_TEMPLATE", "%s_%s" % (agent, irname)), label_statement, " [Domain: %s]" % label_domain if(label_domain is not None) else ""))

            if(dri == 0b11):
                self.logStream.write(("tap_raw_shift : ir_tdi = 'b%s %s;\n") % (ir_tdi, ir_tdo))
            else:
                self.logStream.write(("tap_raw_shift : ir_tdi = 'b%s %s %s;\n") %
                                     (ir_tdi, dr_tdi, dr_tdo))
        self.logStream.write("flush;\n")

        if(dronly):
            self.logStream.write("@set tap_skip_ir off;\n")

        if (pscand_en == 1):
            self.logStream.write("@set tap_pscan_mode off;\n")

        if (overshift_en == 1):
            self.logStream.write("@set tap_overshift_mode off;\n")

    ##########################################################################
    # MCI Interface Functions
    ##########################################################################
    def MciPackets(self, mci_in, mci_out, transform):
        self.logStream.write("@set_transform %s;\n" % (transform))
        self.logStream.write("focus_mci;\n")
        for p in mci_in:
            binstr = util_int_to_binstr(p, 21)
            self.logStream.write("set_mci_packet mci_in = 21'b" + binstr + ";\n")

        for p in mci_out:
            binstr = util_int_to_binstr(p, 21)
            self.logStream.write("set_mci_packet mci_out = 21'b" + binstr + ";\n")

        self.logStream.write("unfocus_mci;\n")

    ##########################################################################
    # STF Interface Functions
    ##########################################################################

    # Interface function for direct_packet_mode
    def StfITPPPacket(self, size, in_val, out_val=0, strobes={}):

        shift_in_str = util_int_to_binstr(in_val, size)
        shift_out_str = util_int_to_binstr(0, size).replace("0", "X")
        shift_out_str_l = list(shift_out_str)

        for ch in range(0, len(shift_out_str)):
            bitindex = len(shift_out_str) - 1 - ch
            if(len(list(strobes.keys())) > 0 and (bitindex in list(strobes.keys())) and (strobes[bitindex] != "S")):
                shift_out_str_l[ch] = strobes[bitindex]

        shift_out_str = "".join(shift_out_str_l)
        self.logStream.write(("pass itpp \"vector: stf_in(%s) stf_out(%s);\";\n") %
                             (shift_in_str, shift_out_str))

    def stf_print_comment(self, comment):
        if comment == "" or comment is None:
            return

        lines = comment.split("\n")
        for line in lines:
            if line == "":
                continue
            self.logStream.write("comment \"%s\";\n" % (line))

    # Function to handle SELECT STF operations
    def stf_select(self, gid, gid_bank, serial_mode, print_group_cmd, select_mode, agent, gid_usage_tracking, comment=""):
        # Should output
        # set_stf_packet input SELECT <gid> <agent(name)> <gid_bank>;

        if (select_mode == "RESET_STF_NETWORK"):
            self.logStream.write("stf_program_network grouping = {};\n")
            return

        self.stf_print_comment(comment)
        if ("STF_packet" in list(CFG.keys())) and ("stf_network" in list(CFG["STF_packet"].keys())) and CFG["STF_packet"]["stf_network"]:
            agents = ''
            temp_list = []
            # if no valid ep will show up in the grouping cmd, then the cmd won't be printed in spf file
            noEPFlag = True

            grouping_cmd = "stf_program_network grouping = { "
            # for gid_bank_key in gid_usage_tracking.keys():

            for group_id in list(gid_usage_tracking.keys()):
                for mode in gid_usage_tracking[group_id]:
                    curt_agents = ""
                    for bank in [0, 1]:
                        curt_list = gid_usage_tracking[group_id][mode].get(bank, [])

                        if len(curt_list) == 0:
                            continue

                        curt_temp = []
                        for endpoint in gid_usage_tracking[group_id][mode].get(bank):
                            if endpoint not in curt_temp:
                                if bank == 1:
                                    curt_agents = curt_agents + endpoint + ' (BANK = 1),'
                                else:
                                    curt_agents = curt_agents + endpoint + ','
                                curt_temp.append(endpoint)
                                noEPFlag = False

                    if len(curt_agents) != 0:
                        grouping_cmd = grouping_cmd + " %d : %s = { %s  }," %(group_id, mode, curt_agents[0:len(curt_agents)-1])


                # old cmd with only current gid_bank comination, comment out as reference
                # grouping_cmd = "stf_program_network grouping = {  %d  = { %s  (BANK = %d)}}; \n" %(gid, agents[0:len(agents)-1], curtGIDBank)
                # print grouping_cmd + "@@@"

            # complete grouping cmd
            if serial_mode == "on":
                grouping_cmd = grouping_cmd[0:len(grouping_cmd)-1] + "}, serial_mode = on; \n"
            else:
                grouping_cmd = grouping_cmd[0:len(grouping_cmd)-1] + "};\n"

            if print_group_cmd == "off":
                pass
            elif noEPFlag:
                if CFG["STF_packet"].get("set_listen_only") == 1:
                    self.logStream.write("stf_program_network grouping = {  0 : LISTEN_ONLY = { %s  }};\n" % agent)
                else:
                    self.logStream.write("stf_program_network grouping = {};\n")
            else:
                self.logStream.write(grouping_cmd)
        else:
            self.logStream.write("set_stf_packet input SELECT %d %s %d;\n\n" % (gid, agent, gid_bank))
 
    # Function to handle SELECT_MASK STF operations
    def stf_select_mask(self, pid_mask):
        pass
        # Should output
        # set_stf_packet input SELECT_MASK 0 <pid_mask>;

    # Function to handle NOP/NULL Packets
    def stf_nop(self, gid, rpt):
        # should output
        # set_stf_packet input NOP <gid> 'h0 (repeat = <rpt>);
        self.logStream.write("set_stf_packet input NOP %d 'h0 (repeat = %d);\n" % (gid, rpt))

    def adjust_input_with_strobe(self, input_data, length):
        adjusted_input = ""
        if (isinstance(input_data, str) and re.match(r'^[X]+$', input_data) is not None and len(input_data) == length):
            # already formatted, nothing to do here
            return input_data

        # check if input is defined and is a valid number
        try:
            # convert input to binary
            # add the [2:] to trim off the "0b" that the bin function adds
            adjusted_input = bin(input_data)[2:]
        except BaseException:
            # do nothing
            pass
        # stobe 'X' over each undefined bit
        return adjusted_input.rjust(length, 'X')

    # Function to handle REPLACE Packets
    def stf_replace(self, mode, gid, gid2, data2, rpt, iv, ov):
        # convert int data2 to binary, remove leading '0b' added from bin()
        # add X's after MSB to 32bit stf packet length
        if (mode == "input"):
            data_strobed = self.adjust_input_with_strobe(data2,32)
        else:
            # ticket 4008: per bit strobe on replace op
            data_strobed = data2
        #iv = self.adjust_input_with_strobe(iv,1)
        #ov = self.adjust_input_with_strobe(ov,1)
        if (iv is not ""):
            iv = ", output.IV = %s" % iv
        if (ov is not ""):
            ov = ", output.OV = %s" % ov
        #gid2 = self.adjust_input_with_strobe(gid2,4)
        #ov_strobed = data_strobed.rjust(1,'X')
        htdte_logger.inform("REPLACE Data: %s" % (data_strobed))
        # set_stf_packet input NOP <gid> 'h0 (repeat = <rpt>);
        if (mode == "input"):
            self.logStream.write("set_stf_packet input REPLACE %d 'h0 (repeat = %d);\n" % (gid, rpt))
        elif (mode == "inout"):
            self.logStream.write("set_stf_packet inout REPLACE %d 'h0 %s 'b%s (repeat = %d%s%s);\n" % (
                gid, gid2, data_strobed, rpt, iv, ov))
        else:
            htdte_logger.error(
                ("Invalid mode %s for REPLACE packet. Valid replace_mode values are: input|inout.") % (mode))

        # set_stf_packet input REPLACE <GID> <data> [ (repeat = <num> ) ];
        # set_stf_packet inout REPLACE <input GID> <input data> <output GID>
        # <output data> [(repeat = <num>, output.IV = 1|0, output.OV = 1|0)];

    # Function to handle map_usrop packets
    def stf_map_usrop(self, agents, gids, usrops_to_program):
        # should output
        # focus_stf <agent>;
        # map_usrop USROP<usrop> = <reg>-><address_field>;  e.g. RegA->@ADDRESS, RegB->@ADDRESS1, etc;
        # flush;
        focus_string = self.generate_focus_stf_string(agents, gids)
        self.logStream.write("focus_stf %s;\n" % (focus_string))

        for usrop in list(usrops_to_program.keys()):
            address_str = usrops_to_program[usrop]
            self.logStream.write("map_usrop USROP%d = %s;\n" % (usrop, address_str))
            self.logStream.write("flush;\n")

        self.logStream.write("\n")

    # Function to handle standard STF writes and read
    # Future Support Items:
    #   capture - have a placeholder here already
    #   mask - have a placeholder here already
    def stf_write_read(self, agent, gid, reg, write_by_field, read_by_field, usrop_seq=[], data_seq=[], capture="", mask="", comment=""):
        self.stf_print_comment(comment)

        focus_string = self.generate_focus_stf_string(agent, gid)
        self.logStream.write("focus_stf %s;\n" % (focus_string))

        # Everything is written/read by field. The action changes reg[msb:lsb]
        # into their corresponding field values
        if write_by_field is not None:

            if ("whole_reg" in list(write_by_field.keys()) and write_by_field["whole_reg"] == 1):
                self.logStream.write("set %s = 'h%X; \n" % (reg, write_by_field[reg]))
            else:
                for field, value in list(write_by_field.items()):
                    self.logStream.write("set %s->%s = 'h%X;\n" % (reg, field, value))

        # Everything is written/read by field. The action changes reg[msb:lsb]
        # into their corresponding field values
        if read_by_field is not None:
            if ("whole_reg" in list(read_by_field.keys()) and read_by_field["whole_reg"] == 1):
                self.logStream.write("compare %s = 'h%X; \n" % (reg, read_by_field[reg]))
            else:
                for field, value in list(read_by_field.items()):
                    # Hexa format
                    if (type(value) in [int, int]):
                        self.logStream.write("compare %s->%s = 'h%X;\n" % (reg, field, value))
                    # Binary format
                    elif (isinstance(value, str)):
                        self.logStream.write("compare %s->%s = 'b%s;\n" % (reg, field, value))
        # Read with no compare
        if (write_by_field is None or len(list(write_by_field.keys())) == 0) and (read_by_field is None or len(list(read_by_field.keys())) == 0):
            self.logStream.write("compare %s = 'bX;\n" % (reg))

        self.logStream.write("flush;\n\n")

    def generate_focus_stf_string(self, agent, gid):
        focus_string = ""
        for (i, cur_agent) in enumerate(agent):
            if focus_string != "":
                focus_string += ", "
            focus_string += "%s (%d)" % (cur_agent, gid[i])

        return focus_string

    # -------------------------------------------------------------------------
    def tap_verify(self, param, tapobj):
        return 1

    # --this function should be replaced by one from the clocks module that converts
    # --the clock cycles into time scale period.
    def cycles2baseClock(self, clk, val):
        if("default" not in list(CFG["HTD_Clocks"].keys())):
            htdte_logger.error(
                "Missing CFG[HTD_Clocks][\"default\"] in TE_cfg.xml - default clock name selection. ")

        if(CFG["HTD_Clocks"]["default"] not in list(CFG["HTD_Clocks"].keys())):
            htdte_logger.error(("Missing default clock - \"%s\" ratio definition in CFG[HTD_Clocks][\"%s\"]") % (
                CFG["HTD_Clocks"]["default"], CFG["HTD_Clocks"]["default"]))

        if(clk not in list(CFG["HTD_Clocks"].keys())):
            htdte_logger.error(
                ("Trying to reference by clock  - \"%s\" , while missing ratio definition in CFG[HTD_Clocks][\"%s\"]") % (clk, clk))

        return val * CFG["HTD_Clocks"][clk] // CFG["HTD_Clocks"][CFG["HTD_Clocks"]["default"]]

    # -------------------------------------------------------------------------
    def cycles2time(self, clk, val):
        ts = 1 if (("HTD_Clocks_Settings" not in list(CFG.keys())) or ("sim_time_scale" not in list(CFG[
                   "HTD_Clocks_Settings"].keys()))) else CFG["HTD_Clocks_Settings"]["sim_time_scale"]
        unit = "ps" if (("HTD_Clocks_Settings" not in list(CFG.keys())) or ("sim_time_unit" not in list(CFG[
                        "HTD_Clocks_Settings"].keys()))) else CFG["HTD_Clocks_Settings"]["sim_time_unit"]
        base_clk = 10000 if (("HTD_Clocks_Settings" not in list(CFG.keys())) or ("base_clk" not in list(CFG[
                             "HTD_Clocks_Settings"].keys()))) else CFG["HTD_Clocks_Settings"]["base_clk"]

        clk2baseclk = val / cfg_HTD_Clocks(clk)
        base_clk_time = clk2baseclk * base_clk
        base_clk_time_scaled = int(base_clk_time / (int(ts) * float(cfg_Temp(unit))))

        return base_clk_time_scaled

    # -------------------------------------------------------------------------
    def wait_tick(self):
        # FIXME:bring me back
        #self.logStream.write(("rem:   wait_clock_edge:   %s:%s;\n")%(clock,edge))
        return

    def start_scan(self, scan_pins_list): pass

    def stop_scan(self, scan_pins_list): pass
