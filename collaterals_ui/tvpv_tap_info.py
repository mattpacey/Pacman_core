import sys
import os
from glob import glob

# import TVPV lib
if ("tvpv_collaterals_fullpath" in list(CFG["INFO"].keys())):
    dirname, filename = os.path.split(CFG["INFO"]["tvpv_collaterals_fullpath"])
    filename_noext = os.path.splitext(filename)[0]

    # append the path and import the filename
    sys.path.append(dirname)
    exec((("from %s import *") % (filename_noext)), globals())

from htd_collaterals import *


class collaterals_importer(object):

    def __init__(self, prod, step):
        self.tap_agents = []
        self.tap_link_remote_data = {}
        self.per_agent_irs = {}
        self.tap_link_commands = {}
        self.parallel_link_irs = {}
        self.parallel_link_ir_to_dr = {}
        self.interface_obj = self.get_object(prod, step)
        # TapInterface_KG0v1() #TapInterface_KG0v1()#TapInterface_CA0v1()
        self.master_tap = ""
        self.tap_link_opcodes = []
        self.tap_lengths = {}
        self.taps_to_skip = self.get_taps_to_skip(prod, step)
        self.project = (os.environ.get("PROJECT")).lower()

    def get_taps_to_skip(self, prod, step):
        taps_to_skip = []
        if (prod == "cnl" or prod == "cdk"):
            if (step == "b0" or step == "c0"):
                taps_to_skip.append("CCF_LR_SR_MBISTTAP")  # appears as master tap
                taps_to_skip.append("FIVR_CCP3_RC_REPEATER")  # wrong size for IRs (1)
                taps_to_skip.append("CCF_TOP_SR_MBISTTAP")  # appears as master tap
                taps_to_skip.append("CCF_UL_SR_MBISTTAP")  # appears as master tap
                taps_to_skip.append("CCF_UR_SR_MBISTTAP")  # appears as master tap
                taps_to_skip.append("CCF_LL_SR_MBISTTAP")  # appears as master tap
        if (prod == "cnls62" or prod == "cnls82"):
            if (step == "p0" or step == "g0"):
                taps_to_skip.append("CCF_LR_SR_MBISTTAP")  # appears as master tap
                taps_to_skip.append("CCF_TOP_SR_MBISTTAP")  # appears as master tap
                taps_to_skip.append("CCF_UL_SR_MBISTTAP")  # appears as master tap
                taps_to_skip.append("CCF_UR_SR_MBISTTAP")  # appears as master tap
                taps_to_skip.append("CCF_LL_SR_MBISTTAP")  # appears as master tap
                taps_to_skip.append("CCF_MBISTTAPPAR")  # appears as master tap
                taps_to_skip.append("CCF_MBISTTAP")  # appears as master tap
                taps_to_skip.append("SR1KPAR")  # appears as master tap
                taps_to_skip.append("SR1K")  # appears as master tap
        if (prod == "icl"):
            if (step == "a0"):
                taps_to_skip.append("FIVR_IP_CORE_IOV0")  # appears as master tap
                taps_to_skip.append("FIVR_IP_CORE_IOV1")  # appears as master tap
                taps_to_skip.append("FIVR_IP_CORE_IOV2")  # appears as master tap
                taps_to_skip.append("FIVR_IP_CORE_IOV3")  # appears as master tap
                taps_to_skip.append("FIVR_IP_CORE_STAP0")  # appears as master tap
                taps_to_skip.append("FIVR_IP_CORE_STAP1")  # appears as master tap
                taps_to_skip.append("FIVR_IP_CORE_STAP2")  # appears as master tap
                taps_to_skip.append("FIVR_IP_CORE_STAP3")  # appears as master tap
                taps_to_skip.append("FIVR_IP_GT_IOV0")  # appears as master tap
                taps_to_skip.append("FIVR_IP_GT_IOV1")  # appears as master tap
                taps_to_skip.append("FIVR_IP_GT_STAP0")  # appears as master tap
                taps_to_skip.append("FIVR_IP_GT_STAP1")  # appears as master tap
                taps_to_skip.append("FIVR_IP_TCSS_IOV")  # appears as master tap
                taps_to_skip.append("FIVR_IP_TCSS_STAP")  # appears as master tap
        if (prod == "tgl"):
            if (step == "a0"):
                taps_to_skip.append("FIVR_IP_CORE_IOV0")  # appears as master tap
                taps_to_skip.append("FIVR_IP_CORE_IOV1")  # appears as master tap
                taps_to_skip.append("FIVR_IP_CORE_IOV2")  # appears as master tap
                taps_to_skip.append("FIVR_IP_CORE_IOV3")  # appears as master tap
                taps_to_skip.append("FIVR_IP_CORE_STAP0")  # appears as master tap
                taps_to_skip.append("FIVR_IP_CORE_STAP1")  # appears as master tap
                taps_to_skip.append("FIVR_IP_CORE_STAP2")  # appears as master tap
                taps_to_skip.append("FIVR_IP_CORE_STAP3")  # appears as master tap
                taps_to_skip.append("FIVR_IP_GT_IOV0")  # appears as master tap
                taps_to_skip.append("FIVR_IP_GT_IOV1")  # appears as master tap
                taps_to_skip.append("FIVR_IP_GT_STAP0")  # appears as master tap
                taps_to_skip.append("FIVR_IP_GT_STAP1")  # appears as master tap
                taps_to_skip.append("FIVR_IP_TCSS_IOV")  # appears as master tap
                taps_to_skip.append("FIVR_IP_TCSS_STAP")  # appears as master tap
        return taps_to_skip

    def get_object(self, prod, step):
        prod_lc = prod.lower()
        step_lc = step.lower()

        if (prod == "cnl" or prod == "cdk"):
            if (step == "c0"):
                return TapInterface_CC0v1()
            elif (step == "b0"):
                return TapInterface_CB0v1()
            elif (step == "a0"):
                return TapInterface_CA0v1()
        elif (prod == "icl"):
            if (step == "a0"):
                return TapInterface_IA0v1()
        elif (prod == "tgl"):
            if (step == "a0"):
                return TapInterface_TA0v1()
        elif (prod == "kbl"):
            if (step == "a0"):
                return TapInterface_KA0v1()
            elif (step == "d0"):
                return TapInterface_KD0v1()
            elif (step == "g0"):
                return TapInterface_KG0v1()
            elif (step == "h0"):
                return TapInterface_KH0v1()
            elif (step == "j0"):
                return TapInterface_KJ0v1()
            elif (step == "y0"):
                return TapInterface_KY0v1()
            elif (step == "r0"):
                return TapInterface_KR0v1()
            elif (step == "u0"):
                return TapInterface_KU0v1()
        elif (prod == "cnls62"):
            return TapInterface_CP0v1()
        elif (prod == "cnls82"):
            return TapInterface_CG0v1()

        htdte_logger.error("Could not find the matching tap collateral interface for product %s and step %s" % (prod, step))

    ###################################################################################
    def run(self):
        self.populate_tap_agents()
        self.populate_irs_per_tap()
        self.get_serial_linked_ir_and_dr()
        self.get_parallel_linked_ir_and_dr()
        self.get_regular_commands()
        # self.print_results()
        self.dump(os.getcwd())

    ###################################################################################
    def populate_tap_agents(self):
        self.tap_agents = HTD_INFO.tap_info.get_tap_agents()

    ###################################################################################
    def populate_irs_per_tap(self):
        for tap_agent in self.tap_agents:
            if (tap_agent in self.taps_to_skip):
                htdte_logger.inform("Skipping tap %s as setup files have some issues" % (tap_agent))
                continue
            self.per_agent_irs[tap_agent] = HTD_INFO.tap_info.get_ir_commands(tap_agent)
            first_ir_opcode_string = HTD_INFO.tap_info.get_ir_opcode_string(list(self.per_agent_irs[tap_agent])[0], tap_agent)

            if (HTD_INFO.tap_info.is_taplink_remote_tap(tap_agent)):
                htdte_logger.inform("adding tap agent %s with len %d - remote type" % (tap_agent, len(first_ir_opcode_string)))
                self.interface_obj.add_tap(tap_agent, len(first_ir_opcode_string))  # IR length is 8 in remote taps
                self.tap_lengths[tap_agent] = len(first_ir_opcode_string)
                self.tap_link_remote_data[tap_agent] = 1
            else:
                htdte_logger.inform("adding tap agent %s with len %d - master type" % (tap_agent, len(first_ir_opcode_string)))
                self.interface_obj.add_tap(tap_agent, len(first_ir_opcode_string), master=True)  # IR is 9 on CLTAP
                self.tap_lengths[tap_agent] = len(first_ir_opcode_string)
                self.tap_link_remote_data[tap_agent] = 0
                self.master_tap = tap_agent

    ###################################################################################
    def get_serial_linked_ir_and_dr(self):
        for tap_agent in self.tap_agents:
            if (tap_agent not in list(self.tap_link_remote_data.keys()) or self.tap_link_remote_data[tap_agent] == 0):
                continue

            # handle serial IR
            linked_agent = tap_agent

            htdte_logger.inform(("Getting tap link IR for agent:  %s") % (tap_agent))
            (local_agent, irname, mytype) = HTD_INFO.tap_info.get_tap_link_IR(tap_agent)
            htdte_logger.inform(("Getting tap IR opcode for local agent:  %s : %s") % (local_agent, irname))

            tap_len = self.tap_lengths[self.local_tap(local_agent)]

            ir_opcode = self.check_length(HTD_INFO.tap_info.get_ir_opcode_string(irname, local_agent), tap_len)

            htdte_logger.inform("Adding new register %s on agent %s with length %d" % (irname, local_agent,
                                                                                       HTD_INFO.tap_info.get_dr_total_length(irname, local_agent)))
            self.interface_obj.add_register(self.local_tap(local_agent), irname, ir_opcode,
                                            HTD_INFO.tap_info.get_dr_total_length(irname, local_agent))
            self.tap_link_commands[irname] = local_agent
            self.tap_link_opcodes.append(ir_opcode)

            reg_fields = HTD_INFO.tap_info.get_ir_field_details(irname, local_agent)
            for reg_field in list(reg_fields.keys()):
                if (reg_field.startswith("DUMMY")):
                    self.add_field(self.local_tap(local_agent), irname, reg_field, reg_fields[reg_field])
                else:
                    self.add_field_taplink_ir(self.local_tap(local_agent), irname, reg_field, reg_fields[reg_field], linked_agent)

            linked_irs_l = []
            linked_irs_l.append(irname)

            # handle serial DR
            (local_agent, drname, mytype) = HTD_INFO.tap_info.get_tap_link_DR(tap_agent)
            ir_opcode = self.check_length(HTD_INFO.tap_info.get_ir_opcode_string(drname, local_agent), tap_len)

            self.tap_link_commands[drname] = local_agent
            self.tap_link_opcodes.append(ir_opcode)
            htdte_logger.inform("Adding new register %s on agent %s with length %d" % (drname, local_agent,
                                                                                       HTD_INFO.tap_info.get_dr_total_length(drname, local_agent)))
            self.interface_obj.add_register(self.local_tap(local_agent), drname, ir_opcode,
                                            HTD_INFO.tap_info.get_dr_total_length(drname, local_agent))

            reg_fields = HTD_INFO.tap_info.get_ir_field_details(drname, local_agent)
            for reg_field in list(reg_fields.keys()):
                if (reg_field.startswith("DUMMY")):
                    self.add_field(self.local_tap(local_agent), drname, reg_field, reg_fields[reg_field])
                else:
                    self.add_field_taplink_dr(self.local_tap(local_agent), drname, reg_field, reg_fields[reg_field], irname)

            # For CNL DT on HDK need to also handle the CFG and STATUS which exist in the GLUE
            if self.project == 'hdk':
                for (local_agent, drname, mytype) in (HTD_INFO.tap_info.get_tap_link_CFG(local_agent),
                                                      HTD_INFO.tap_info.get_tap_link_STATUS(local_agent)):
                    ir_opcode = self.check_length(HTD_INFO.tap_info.get_ir_opcode_string(drname, local_agent), tap_len)

                    self.tap_link_commands[drname] = local_agent
                    self.tap_link_opcodes.append(ir_opcode)
                    htdte_logger.inform("Adding new register %s on agent %s with length %d" % (drname, local_agent,
                                                                                               HTD_INFO.tap_info.get_dr_total_length(drname, local_agent)))
                    self.interface_obj.add_register(self.local_tap(local_agent), drname, ir_opcode,
                                                    HTD_INFO.tap_info.get_dr_total_length(drname, local_agent))

                    reg_fields = HTD_INFO.tap_info.get_ir_field_details(drname, local_agent)
                    for reg_field in list(reg_fields.keys()):
                        self.add_field(self.local_tap(local_agent), drname, reg_field, reg_fields[reg_field])

    ###################################################################################
    def get_parallel_linked_ir_and_dr(self):
        # find all parallel taps
        parallel_agents = {}
        for tap_agent in self.tap_agents:
            if (tap_agent not in list(self.tap_link_remote_data.keys()) or self.tap_link_remote_data[tap_agent] == 0):
                continue

            if (not HTD_INFO.tap_info.has_tap_link_parallel_support(tap_agent)):
                continue

            # IR
            (local_agent, irname, mytype) = HTD_INFO.tap_info.get_tap_link_PARIR(tap_agent)
            htdte_logger.inform(("Getting tap IR opcode for local agent:  %s : %s") % (local_agent, irname))

            if (irname not in list(self.parallel_link_irs.keys())):
                self.parallel_link_irs[irname] = []
            self.parallel_link_irs[irname].append(tap_agent)

            # DR
            (local_agent, drname, mytype) = HTD_INFO.tap_info.get_tap_link_PARDR(tap_agent)
            self.parallel_link_ir_to_dr[irname] = drname

            # Must remember which parallel tap the IR/DR came from for HDK
            parallel_agents[irname] = parallel_agents[drname] = local_agent if self.project == 'hdk' else self.master_tap

        for irname in list(self.parallel_link_irs.keys()):
            irname_l = []
            irname_l.append(irname)

            # add the IR
            htdte_logger.inform("Processing parellel irname: %s" % irname)
            tap_len = self.tap_lengths[self.master_tap]
            ir_opcode = self.check_length(HTD_INFO.tap_info.get_ir_opcode_string(irname, parallel_agents[irname]), tap_len)

            irlen = HTD_INFO.tap_info.get_dr_total_length(irname, parallel_agents[irname])

            self.interface_obj.add_register(self.master_tap, irname, ir_opcode, irlen)
            self.tap_link_commands[irname] = self.master_tap
            self.tap_link_opcodes.append(ir_opcode)

            reg_fields = HTD_INFO.tap_info.get_ir_field_details(irname, parallel_agents[irname])
            for reg_field in list(reg_fields.keys()):
                if (reg_field.startswith("DUMMY")):
                    self.add_field(self.local_tap(local_agent), irname, reg_field, reg_fields[reg_field])
                else:
                    parallel_tap = irname.replace("%s_" % (local_agent), "")
                    # tvpv request
                    parallel_tap = parallel_tap.replace("PARIR", "PAR")

                    self.add_field_taplink_ir(self.local_tap(local_agent), irname, reg_field, reg_fields[reg_field], parallel_tap)
                    self.add_parallel_tap(parallel_tap, self.parallel_link_irs[irname])

            # add the DR
            drname = self.parallel_link_ir_to_dr[irname]
            dr_opcode = self.check_length(HTD_INFO.tap_info.get_ir_opcode_string(drname, parallel_agents[drname]), tap_len)

            drlen = HTD_INFO.tap_info.get_dr_total_length(drname, parallel_agents[drname])

            self.interface_obj.add_register(self.master_tap, drname, dr_opcode, drlen)
            self.tap_link_commands[drname] = self.master_tap
            self.tap_link_opcodes.append(dr_opcode)
            reg_fields = HTD_INFO.tap_info.get_ir_field_details(drname, parallel_agents[drname])
            for reg_field in list(reg_fields.keys()):
                if (reg_field.startswith("DUMMY")):
                    self.add_field(self.local_tap(local_agent), drname, reg_field, reg_fields[reg_field])
                else:
                    self.add_field_taplink_dr(self.master_tap, drname, reg_field, reg_fields[reg_field], irname)

            # For CNL DT also need to add the PARCFG and PARSTATUS
            if self.project == 'hdk':
                for (local_agent, drname, mytype) in (HTD_INFO.tap_info.get_tap_link_PARCFG(parallel_agents[irname]),
                                                      HTD_INFO.tap_info.get_tap_link_PARSTATUS(parallel_agents[irname])):
                    dr_opcode = self.check_length(HTD_INFO.tap_info.get_ir_opcode_string(drname, parallel_agents[irname]), tap_len)
                    htdte_logger.inform("Adding register %s on agent %s" % (drname, self.master_tap))

                    drlen = HTD_INFO.tap_info.get_dr_total_length(drname, parallel_agents[irname])

                    self.interface_obj.add_register(self.master_tap, drname, dr_opcode, drlen)
                    self.tap_link_commands[drname] = self.master_tap
                    self.tap_link_opcodes.append(dr_opcode)
                    reg_fields = HTD_INFO.tap_info.get_ir_field_details(drname, parallel_agents[irname])
                    for reg_field in list(reg_fields.keys()):
                        self.add_field(self.local_tap(local_agent), drname, reg_field, reg_fields[reg_field])

    ###################################################################################
    def get_regular_commands(self):
        for tap_agent in self.tap_agents:

            if (tap_agent not in list(self.per_agent_irs.keys())):
                continue
            htdte_logger.inform("Getting all commands from agent: %s" % (tap_agent))
            opcode_l = []
            for irname in self.per_agent_irs[tap_agent]:
                irname = self.get_raw_command(irname)
                if (self.master_tap == tap_agent and irname in list(self.tap_link_commands.keys())):
                    htdte_logger.inform("skipping %s (agent %s) as this was added as a link command" % (irname, tap_agent))
                    continue

                ir_opcode = ""
                try:
                    ir_opcode = HTD_INFO.tap_info.get_ir_opcode_string(irname, tap_agent)
                except BaseException:
                    htdte_logger.inform("Failed to find the correct opcode for IR %s and agent %s" % (irname, tap_agent))
                    continue

                if (self.master_tap == tap_agent and ir_opcode in self.tap_link_opcodes):
                    htdte_logger.inform("skipping %s (agent %s) as its opcode %s is already inserted " % (irname, tap_agent, ir_opcode))
                    continue

                tap_len = self.tap_lengths[tap_agent]
                if (len(ir_opcode) < tap_len):
                    htdte_logger.inform("Warning: ir opcode %s is lower than tap length %s, skipping command!!!" % (len(ir_opcode), tap_len))
                    continue

                if (ir_opcode not in opcode_l):
                    self.interface_obj.add_register(tap_agent, irname, ir_opcode, HTD_INFO.tap_info.get_dr_total_length(irname, tap_agent))
                    opcode_l.append(ir_opcode)
                    reg_fields = HTD_INFO.tap_info.get_ir_field_details(irname, tap_agent)
                    try:
                        for reg_field in list(reg_fields.keys()):
                            self.add_field(tap_agent, irname, reg_field, reg_fields[reg_field])
                    except BaseException:
                        htdte_logger.inform("Issues with data on field %s ir %s agent %s" % (reg_field, irname, tap_agent))
                else:
                    htdte_logger.inform("skipping IR %s as opcode %s (agent %s) is already inserted" % (irname, ir_opcode, tap_agent))

    ###################################################################################
    def print_results(self):
        debug_str = self.interface_obj.debug_print()
        htdte_logger.inform("Tap debug info: %s" % debug_str)

    ###################################################################################
    def dump(self, pathname):
        for f in glob("%s/*.pkl" % (pathname)):
            htdte_logger.inform("deleting old pkl file %s" % (f))
            os.unlink(f)
        self.interface_obj.dump_collateral(pathname)

    ###################################################################################
    def add_field(self, tap_agent, irname, reg_field_name, reg_field_obj):
        field_lsb = int(reg_field_obj["lsb"])
        field_msb = int(reg_field_obj["msb"])
        if (field_lsb > field_msb):
            htdte_logger.inform("WARNING: reverted MSB/LSB bits, fixing it")
            temp = field_lsb
            field_lsb = field_msb
            field_msb = temp
        bit_range = field_msb - field_lsb + 1
        #htdte_logger.inform("add regular field agent %s %s lsb %d range %d" %(tap_agent, reg_field_name, field_lsb, bit_range))

        self.interface_obj.add_field(tap_agent, irname, reg_field_name, field_lsb, bit_range)

    ###################################################################################
    def add_field_taplink_ir(self, tap_agent, irname, reg_field_name, reg_field_obj, taplink_irs_data):
        field_lsb = int(reg_field_obj["lsb"])
        field_msb = int(reg_field_obj["msb"])
        #htdte_logger.inform("Adding a taplink IR: %s - %s"%(tap_agent,irname))
        if (field_lsb > field_msb):
            htdte_logger.inform("WARNING: reverted MSB/LSB bits, fixing it")
            temp = field_lsb
            field_lsb = field_msb
            field_msb = temp
        bit_range = field_msb - field_lsb + 1
        #htdte_logger.inform("add regular field agent %s %s lsb %d range %d" %(tap_agent, reg_field_name, field_lsb, bit_range))
        self.interface_obj.add_field(tap_agent, irname, reg_field_name, field_lsb, bit_range, taplink_ir=taplink_irs_data)

    ###################################################################################
    def add_parallel_tap(self, parallel_tap_name, tap_names):
        self.interface_obj.add_parallel_tap(parallel_tap_name, tap_names)

    ###################################################################################
    def add_field_taplink_dr(self, tap_agent, irname, reg_field_name, reg_field_obj, taplink_drs_data):
        field_lsb = int(reg_field_obj["lsb"])
        field_msb = int(reg_field_obj["msb"])
        if (field_lsb > field_msb):
            htdte_logger.inform("WARNING: reverted MSB/LSB bits, fixing it")
            temp = field_lsb
            field_lsb = field_msb
            field_msb = temp
        bit_range = field_msb - field_lsb + 1
        #htdte_logger.inform("add regular field agent %s %s[%d:%d] %s" %(tap_agent, reg_field_name, field_msb, field_lsb, taplink_drs_data))
        self.interface_obj.add_field(tap_agent, irname, reg_field_name, field_lsb, bit_range, taplink_dr=taplink_drs_data)

    ###################################################################################
    def get_raw_command(self, ir_command):
        ir_command_parts = ir_command.split('.')
        if (len(ir_command_parts) == 1):
            return ir_command
        return ir_command_parts[1]

    def check_length(self, ir_opcode, tap_len):
        if (len(ir_opcode) > tap_len):
            htdte_logger.inform("Warning: ir opcode %s is bigger than tap length %s" % (len(ir_opcode), tap_len))
            # truncate the string
            diff = len(ir_opcode) - tap_len
            ir_opcode = ir_opcode[diff:]

        if (len(ir_opcode) < tap_len):
            htdte_logger.inform("Warning: ir opcode %s is lower than tap length %s" % (len(ir_opcode), tap_len))
            # pad the string
            diff = tap_len - len(ir_opcode)
            ir_opcode = ir_opcode + '0' * diff

        return ir_opcode

    def local_tap(self, local_agent):
        if self.project == 'hdk':
            return self.master_tap
        else:
            return local_agent


# default values
prod_name = "cnl"
prod_step = "b0"
prd_and_step = os.environ.get("STEPPING", "")

if (prd_and_step != ""):
    prd_and_step = prd_and_step.lower()
    prd_and_step_l = prd_and_step.split('-', 2)
    prod_name = prd_and_step_l[0]
    prod_step = prd_and_step_l[1]
    print("Choosing prod %s with step %s" % (prod_name, prod_step))

local_collaterals_importer = collaterals_importer(prod_name, prod_step)
local_collaterals_importer.run()
# does not work for now - waiting for example
# interface_obj.dump_collateral("/nfs/iil/proj/mpg/egreen_wa/orubin/repo/htdmain")
