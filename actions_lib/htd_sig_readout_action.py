from htd_basic_action import *
from htd_utilities import *
from htd_collaterals import *
from htd_player_top import *
import os
import re

# ---------------------------------------------
# Running readout signature action
# -----------------------------------------------
#
#
#
# ------------------------------------------


class SIGREADOUT(htd_base_action):

    def __init__(self, action_name, source_file, source_lineno, currentFlow, is_internal):
        htd_base_action.__init__(self, self.__class__.__name__, action_name, source_file, source_lineno, currentFlow, is_internal)
        #---STF access by agent.register.field
        self.arguments.set_argument("source", 1, "Specify which source for this action")
        self.arguments.declare_arg("stream_map", "Cores and thread input for signature readout", "string", "", 0)
        self.arguments.declare_arg("reg_name", "Register name to read", "string", "", 1)
        self.arguments.declare_arg("reg_field", "Register fields to read", "string", "ADR_LO[31:0]", 0)
        self.arguments.declare_arg("ExpArchSig", "Read value of architectural signature", "int", 0, 1)
        self.arguments.declare_arg("ReadAllDRs", "Read all available DRs", "bool", 0, 0)
        self.arguments.declare_arg("specific_core", "Specific core to work on", "int", -1, 0)

        self.dr_specific_values = {}

    def get_action_not_declared_argument_names(self): pass

    def verify_arguments(self):
        if (self.arguments.get_argument("stream_map") == "" and os.environ.get('STREAM_MAP') is None):
            self.error("Missing 'stream_map parameter or environment variable", 1)

        if (self.arguments.get_argument("reg_name") == ""):
            self.error("Missing control register name to use", 1)

        if (self.arguments.get_argument("reg_field") == ""):
            self.error("Missing control register field to use", 1)

        # check the configurations
        configurations = self.get_configuration().split(',')
        for single_config in configurations:
            htdte_logger.inform("verifying config %s" % (single_config))
            if (not re.match(r'^C[\d+X]T[\d+X]$', single_config)):
                self.error("Illegal configuration %s was declared" % (single_config), 1)

    # populate user specific DRs. In this case the entire 64 bits will be written
    def populate_dr_user_values(self):
        if (self.arguments.get_argument("ReadAllDRs") == 1):
            self.dr_specific_values["dr0"] = {}
            self.dr_specific_values["dr1"] = {}
            self.dr_specific_values["dr2"] = {}
            self.dr_specific_values["dr3"] = {}

            if (os.environ.get('T0_DR0') is not None):
                self.dr_specific_values["dr0"][0] = os.environ.get('T0_DR0')
            else:
                self.dr_specific_values["dr0"][0] = ""

            if (os.environ.get('T1_DR0') is not None):
                self.dr_specific_values["dr0"][1] = os.environ.get('T1_DR0')
            else:
                self.dr_specific_values["dr0"][1] = ""

            if (os.environ.get('T0_DR1') is not None):
                self.dr_specific_values["dr1"][0] = os.environ.get('T0_DR1')
            else:
                self.dr_specific_values["dr1"][0] = ""

            if (os.environ.get('T1_DR1') is not None):
                self.dr_specific_values["dr1"][1] = os.environ.get('T1_DR1')
            else:
                self.dr_specific_values["dr1"][1] = ""

            if (os.environ.get('T0_DR2') is not None):
                self.dr_specific_values["dr2"][0] = os.environ.get('T0_DR2')
            else:
                self.dr_specific_values["dr2"][0] = ""

            if (os.environ.get('T1_DR2') is not None):
                self.dr_specific_values["dr2"][1] = os.environ.get('T1_DR2')
            else:
                self.dr_specific_values["dr2"][1] = ""

            if (os.environ.get('T0_DR3') is not None):
                self.dr_specific_values["dr3"][0] = os.environ.get('T0_DR3')
            else:
                self.dr_specific_values["dr3"][0] = ""

            if (os.environ.get('T1_DR3') is not None):
                self.dr_specific_values["dr3"][1] = os.environ.get('T1_DR3')
            else:
                self.dr_specific_values["dr3"][1] = ""

    def run(self):
        self.populate_dr_user_values()

        # currently supporting only sbft_mlc and sbft_slice (sbft_fc wip)
        configurations = self.get_configuration().split(',')

        # generate internal xreg commands
        flow_ptr = self.get_curr_flow()

        for single_config in configurations:
            match = re.match(r'^C([\d+X])T([\d+X])$', single_config)
            core_data = ""
            thread_data = ""
            if (match):
                core_data = match.groups()[0]
                thread_data = match.groups()[1]

            htdte_logger.inform("Reading the following readout config : %s (core %s thread %s)" % (single_config, "All" if core_data == "X" else core_data,
                                                                                                   "All" if thread_data == "X" else thread_data))

            if (self.arguments.get_argument("ReadAllDRs") == 0):
                params = {}
                params = {"reg": self.arguments.get_argument("reg_name"),
                          self.arguments.get_argument("reg_field"): {"read_value": self.arguments.get_argument("ExpArchSig"), "label": "ARCH_SIG_DR0_DR"},
                          "read_type": 1,
                          "read_modify_write": 0, \
                          # "check":self.arguments.get_argument("check"), \
                          "check": 0, \
                          "compression": "0", \
                          "pscand_en": os.getenv('HTD_SBFT_MLC_PSCAND_EN', 0)}

                # specific core
                if (core_data != "X"):
                    params["specific_core"] = int(core_data)
                    if (core_data != "0"):
                        params["tap"] = {"value": "CORE%d_CORE" % (int(core_data))}

                # specific thread
                if (thread_data != "X"):
                    params["threadid"] = {"value": int(thread_data)}
                # Force specific core for debug
                if (self.arguments.get_argument("specific_core") > -1):
                    params["specific_core"] = self.arguments.get_argument("specific_core")
                # assumption only two threads
                if (thread_data == "X"):
                    # perform action per thread
                    params["threadid"] = {"value": 0}
                    flow_ptr.exec_action(params, "XREG", self.__class__.__name__, 0, self.get_action_name())
                    params["threadid"] = {"value": 1}
                    flow_ptr.exec_action(params, "XREG", self.__class__.__name__, 0, self.get_action_name())
                else:
                    flow_ptr.exec_action(params, "XREG", self.__class__.__name__, 0, self.get_action_name())

            else:  # perform action on all DRs
                for dr in sorted(self.dr_specific_values):

                    htdte_logger.inform("Reading the following register (all 64 bits): %s" % (dr))
                    params = {}
                    params = {"reg": dr,
                              "read_type": 1,
                              "read_modify_write": 0,
                              "check": 0,
                              "compression": "0",
                              "pscand_en": os.getenv('HTD_SBFT_MLC_PSCAND_EN', 0)}

                    if (self.dr_specific_values[dr] != ""):
                        specific_value = self.dr_specific_values[dr][0]
                        if (thread_data != "X"):
                            specific_value = self.dr_specific_values[dr][int(thread_data)]

                        if (specific_value != ""):
                            htdte_logger.inform("testing for specific value as assigned by the user: %s (thread: %s)" % (specific_value, thread_data))
                            fields_l = HTD_INFO.cr_info.get_cr_fields(dr, "NONE", "")
                            for field in fields_l:
                                (f_lsb, f_msb) = HTD_INFO.cr_info.get_cr_field_boundaries(field, dr, "NONE", "")
                                params[field] = {"read_value": int(specific_value, 16) & util_calculate_range_mask(
                                    int(specific_value, 16), f_lsb, f_msb), "label": "ARCH_SIG_%s_%s" % (dr, field)}

                    # specific core
                    if (core_data != "X"):
                        params["specific_core"] = int(core_data)
                        if (core_data != "0"):
                            params["tap"] = {"value": "CORE%d_CORE" % (int(core_data))}

                    # specific thread
                    if (thread_data != "X"):
                        params["threadid"] = {"value": int(thread_data)}
                    # Force specific core for debug
                    if (self.arguments.get_argument("specific_core") > -1):
                        params["specific_core"] = self.arguments.get_argument("specific_core")
                    # assumption only two threads
                    if (thread_data == "X"):
                        # perform action per thread
                        params["threadid"] = {"value": 0}
                        flow_ptr.exec_action(params, "XREG", self.__class__.__name__, 0, self.get_action_name())
                        params["threadid"] = {"value": 1}
                        flow_ptr.exec_action(params, "XREG", self.__class__.__name__, 0, self.get_action_name())
                    else:
                        flow_ptr.exec_action(params, "XREG", self.__class__.__name__, 0, self.get_action_name())

    def get_configuration(self):

        # env. variable overrides the setting of stream_map parameter
        if (os.environ.get('STREAM_MAP') is not None):
            self.arguments.set_argument("stream_map", os.environ.get('STREAM_MAP'), "Inherited from $STREAM_MAP")

        if (os.environ.get('READ_ALL_DRS') is not None):
            self.arguments.set_argument('ReadAllDRs', os.environ.get('READ_ALL_DRS'), "Inherited from $READ_ALL_DRS")

        if (self.arguments.get_argument("ReadAllDRs")):
            self.arguments.set_argument("reg_field", "All fields", "Overwritten by setting ReadAllDRs=1")
            self.arguments.set_argument("reg_name", "dr0,dr1,dr2,dr3", "Overwrittem by setting ReadAllDRs=1")
            self.arguments.set_argument("ExpArchSig", "-1", "Overwritten by setting ReadAllDRs=1")

        stream_map_data = self.arguments.get_argument("stream_map")
        # placeholder for flow type
        flow_type = self.get_curr_flow().get_flow_type_enum()
        if (flow_type == "MLC_SBFT" or flow_type == "SLC_SBFT"):
            if (stream_map_data == "0"):
                return "CXT0"
            elif (stream_map_data == "0,1"):
                return "CXT0,CXT1"

        elif (flow_type == "FC_SBFT"):
            stream_map_data_items = stream_map_data.split(',')
            core_thread_settings = []
            for data_item in stream_map_data_items:
                if (self.arguments.get_argument("specific_core") > -1):
                    core_number = self.arguments.get_argument("specific_core") + int(data_item) // 2
                else:
                    core_number = int(data_item) // 2
                thread_number = int(data_item) % 2
                core_thread_settings.append("C%dT%d" % (core_number, thread_number))
            return ','.join(core_thread_settings)

        else:
            if (stream_map_data == "0"):
                return "CXT0"
            elif (stream_map_data == "0,1"):
                return "CXT0,CXT1"

    def debug_readback(self): pass
