import socket
import sys
import re
import os
import subprocess
import json
from htd_tap_info import *
from htd_utilities import *
from htd_collaterals import *

path_to_collateral_interface = ("%s/bin/API_SERVER_CLIENT") % (os.environ.get('SPF_ROOT'))
sys.path.insert(0, path_to_collateral_interface)
from collateral_interface import Client


class htd_spf_stf_info(htd_info_server):

    def __init__(self):
        htd_info_server.__init__(self)

        # Check that ENV Variables are setup
        if(os.environ.get('HTD_PROJ') is None):
            htdte_logger.error('Missing obligatory unix environment ENV[HTD_PROJ] ')
        proj = os.environ.get('HTD_PROJ').upper()

        if(os.environ.get('SPF_ROOT') is None):
            htdte_logger.error('Missing SPF_ROOT env. (should it  be set in TE_cfg or in xterm ?')
        LdLibraryPath = ("%s/lib/perl5%s") % (os.environ.get('SPF_ROOT'),
                                              ("" if (os.environ.get('LD_LIBRARY_PATH') is None) else (":%s") % (os.environ.get('LD_LIBRARY_PATH'))))
        os.environ['LD_LIBRARY_PATH'] = LdLibraryPath
        htdte_logger.inform(('SPF setup done: setenv LD_LIBRARY_PATH %s') % (os.environ.get('LD_LIBRARY_PATH')))

        if(os.environ.get('HTD_SPF_STF_SPEC_FILE') is None):
            htdte_logger.error('Missing obligatory TE_cfg.cml parameter HTD_SPF_STF_SPEC_FILE.')
        htdte_logger.inform(("Using HTD_SPF_STF_SPEC_FILE file=%s") % (os.environ.get('HTD_SPF_STF_SPEC_FILE')))
        self.spec_file = os.environ.get('HTD_SPF_STF_SPEC_FILE')

        ld_library = os.environ.get('LD_LIBRARY_PATH')
        ld_library_l = ld_library.split(":")
        if(("%s/lib") % os.environ.get('SPF_ROOT') not in ld_library_l):
            new_ld_library_path = ("%s/lib") % os.environ.get('SPF_ROOT')
            htdte_logger.inform(('Modifying LD_LIBRARY_PATH =%s') % (new_ld_library_path))
            os.environ["LD_LIBRARY_PATH"] = new_ld_library_path
            os.putenv("LD_LIBRARY_PATH", new_ld_library_path)

        # Usage: api_client = Client(proto=<tcp|uds>, log_file=None, workspace=<current-dir>)
        # Please do not turn on log parameter as it clutters all rundirs with SPF info log files
        # If log files are required setup debug hook for that purpose.
        api_client = Client('uds', log_file=None, workspace='/tmp')
        self.stfObj = api_client.get_Stf(self.spec_file)
        self.reg_spec_hub_targets = ["group_membership", "group_responder", "tracker_enable", "tracker_delay", "mode", "response_fifo_size"]
        self.reg_spec_extra_params = {"usrop": 1, "group_membership": 1, "group_responder": 1}

    def has_stop(self, stop_name, throwError=False):
        #        htdte_logger.inform("Querying DTS STF API to see if stop %s exists"%(stop_name))
        if (self.stfObj.has_stf_network_stop(stop_name)):
            #            htdte_logger.inform("Stop %s exists in the STF network"%(stop_name))
            return True
        else:
            if (throwError):
                htdte_logger.error("Stop %s does not exist in the STF network" % (stop_name))
            else:
                htdte_logger.inform("Stop %s does not exist in the STF network" % (stop_name))
            return False

    def get_stop_by_name(self, stop_name):
        self.has_stop(stop_name, throwError=True)
        return self.stfObj.get_stf_stop_by_name(stop_name)

    def is_stop_a_hub(self, stop_name, throwError=False):
        self.has_stop(stop_name, throwError=True)
        if (self.stfObj.is_stf_stop_hub(stop_name)):
            return True
        else:
            if (throwError):
                htdte_logger.error("Stop %s is not a hub!" % (stop_name))
            else:
                htdte_logger.inform("Stop %s is not a hub!" % (stop_name))

            return False

    def is_stop_a_controller(self, stop_name, throwError=False):
        self.has_stop(stop_name, throwError=True)
        if (self.stfObj.is_stf_stop_a_controller(stop_name)):
            return True
        else:
            if (throwError):
                htdte_logger.error("Stop %s is not a controller!" % (stop_name))
            else:
                htdte_logger.inform("Stop %s is not a controller!" % (stop_name))

            return False

    def is_stop_a_repeater(self, stop_name, throwError=False):
        self.has_stop(stop_name, throwError=True)
        if (self.stfObj.is_stf_stop_a_repeater(stop_name)):
            return True
        else:
            if (throwError):
                htdte_logger.error("Stop %s is not a repeater!" % (stop_name))
            else:
                htdte_logger.inform("Stop %s is not a repeater!" % (stop_name))

            return False

    def is_stop_a_endpoint(self, stop_name, throwError=False):
        self.has_stop(stop_name, throwError=True)
        if (self.stfObj.is_stf_stop_a_endpoint(stop_name)):
            return True
        else:
            if (throwError):
                htdte_logger.error("Stop %s is not a endpoint!" % (stop_name))
            else:
                htdte_logger.inform("Stop %s is not a endpoint!" % (stop_name))

            return False

    def get_hub_by_name(self, hub_name):
        self.is_stop_a_hub(hub_name, throwError=True)
        return self.get_stop_by_name(hub_name)

    def stop_has_deskew_fifo_size_reg_spec(self, stop_name, throwError=False):
        self.has_stop(stop_name, throwError=True)

        if (self.stfObj.has_stf_stop_deskew_fifo_size_reg_spec(stop_name)):
            return True
        else:
            if (throwError):
                htdte_logger.error("Stop %s does not have a deskew register spec!" % (stop_name))
            else:
                htdte_logger.inform("Stop %s does not have a deskew register spec!" % (stop_name))
                return False

    def get_stop_deskew_fifo_size_reg_spec(self, stop_name, throwError=False):
        self.stop_has_deskew_fifo_size_reg_spec(stop_name, throwError=True)

        return self.stfObj.get_stf_stop_deskew_fifo_size_reg_spec(stop_name)

    def stop_has_register(self, stop_name, reg_name, throwError=False):
        self.has_stop(stop_name, throwError=True)

        if (self.stfObj.has_stf_stop_register(stop_name, reg_name)):
            return True
        else:
            if (throwError):
                htdte_logger.error("Register %s does not exist in Stop %s!" % (reg_name, stop_name))
            else:
                htdte_logger.inform("Register %s does not exist in Stop %s!" % (reg_name, stop_name))
            return False

    def get_register_by_name(self, stop_name, reg_name):
        self.stop_has_register(stop_name, reg_name, throwError=True)

        return self.stfObj.get_stf_register_by_name(stop_name, reg_name)

    def get_register_fields(self, stop_name, reg_name):

        self.stop_has_register(stop_name, reg_name, throwError=True)

        return self.stfObj.get_stf_register_fields(stop_name, reg_name)

    def register_has_field(self, stop_name, reg_name, field_name, throwError=False):
        self.stop_has_register(stop_name, reg_name, throwError=True)

        if (self.stfObj.has_stf_register_field(stop_name, reg_name, field_name)):
            return True
        else:
            if (throwError):
                htdte_logger.error("Field %s does not exist in Register %s!" % (field_name, reg_name))
            else:
                htdte_logger.inform("Field %s does not exist in Register %s!" % (field_name, reg_name))
            return False

    def get_register_size(self, stop_name, reg_name):
        self.stop_has_register(stop_name, reg_name, throwError=True)
        return self.stfObj.get_stf_register_size(stop_name, reg_name)

    def register_has_default(self, stop_name, reg_name, throwError=False):
        self.stop_has_register(stop_name, reg_name)

        if (self.stfObj.has_stf_register_default(stop_name, reg_name)):
            return True
        else:
            if (throwError):
                htdte_logger.error("Register %s does not have a default value!" % (reg_name))
            else:
                htdte_logger.inform("Register %s does not have a default value!" % (reg_name))
            return False

    def get_register_default(self, stop_name, reg_name):
        self.register_has_default(stop_name, reg_name, throwError=True)

        return self.stfObj.get_stf_register_default(stop_name, reg_name)

    def get_field_lsb(self, stop_name, reg_name, field_name):
        self.register_has_field(stop_name, reg_name, field_name, throwError=True)

        return self.stfObj.get_stf_field_lsb(stop_name, reg_name, field_name)

    def get_field_msb(self, stop_name, reg_name, field_name):
        self.register_has_field(stop_name, reg_name, field_name, throwError=True)

        return self.stfObj.get_stf_field_msb(stop_name, reg_name, field_name)

    def get_field_size(self, stop_name, reg_name, field_name):
        self.register_has_field(stop_name, reg_name, field_name, throwError=True)

        val = self.stfObj.get_stf_field_width(stop_name, reg_name, field_name)

        return self.stfObj.get_stf_field_width(stop_name, reg_name, field_name)

    def field_has_default(self, stop_name, reg_name, field_name, throwError=False):

        self.register_has_field(stop_name, reg_name, field_name, throwError=True)

        if (self.stfObj.has_stf_field_default(stop_name, reg_name, field_name)):
            return True
        else:
            if (throwError):
                htdte_logger.error("Field %s does not have a default value!" % (field_name))
            else:
                htdte_logger.inform("Field %s does not have a default value!" % (field_name))
            return False

    def get_field_default(self, stop_name, reg_name, field_name):

        self.field_has_default(stop_name, reg_name, field_name, throwError=True)

        return self.stfObj.get_stf_field_default(stop_name, reg_name, field_name)

    def get_register_type(self, stop_name, reg_name):
        self.stop_has_register(stop_name, reg_name, throwError=True)

        return self.stfObj.get_stf_register_type(stop_name, reg_name)

    def get_register_access_method(self, stop_name, reg_name):
        self.stop_has_register(stop_name, reg_name, throwError=True)

        return self.stfObj.get_stf_register_access(stop_name, reg_name)

    def get_register_address(self, stop_name, reg_name):
        self.stop_has_register(stop_name, reg_name, throwError=True)

        return self.stfObj.get_stf_register_address(stop_name, reg_name)

    def get_register_address_decimal(self, stop_name, reg_name):
        self.stop_has_register(stop_name, reg_name, throwError=True)

        return self.stfObj.get_stf_register_address_decimal(stop_name, reg_name)

    def get_register_description(self, stop_name, reg_name):
        self.stop_has_register(stop_name, reg_name, throwError=True)

        return self.stfObj.get_stf_register_description(stop_name, reg_name)

    def get_parent_hubs(self, stop_name):
        self.has_stop(stop_name, throwError=True)

        return self.stfObj.get_stf_parent_hubs(stop_name)

    def get_each_controller(self):
        return self.stfObj.get_stf_controllers()

    def get_hub_children(self, hub_name):
        # self.is_stop_a_hub(hub_name, throwError=True) ##Commenting out because controller is parent but not a hub

        return self.stfObj.get_stf_child_ring_stops(hub_name)

    def get_stops(self):
        return self.stfObj.get_stf_stops()

    def get_stop_names(self):
        return self.stfObj.get_stf_stop_names()

    def get_stop_pid_by_name(self, stop_name):
        self.has_stop(stop_name, throwError=True)

        return self.stfObj.get_stf_stop_pid_by_name(stop_name)

    def get_stop_name_by_pid(self, stop_pid):
        return self.stfObj.get_stf_stop_name_by_pid(stop_pid)

    def get_each_register(self, stop_name):
        self.has_stop(stop_name, throwError=True)

        return self.stfObj.get_stf_stop_registers(stop_name)

    def get_each_register_name(self, stop_name):
        self.has_stop(stop_name, throwError=True)

        return self.stfObj.get_stf_stop_register_names(stop_name)

    def get_stop_parent(self, stop_name):
        self.has_stop(stop_name, throwError=True)

        return self.stfObj.get_stf_stop_immediate_parent(stop_name)

    def get_stop_parent_hubs(self, stop_name, throwError=False):
        self.has_stop(stop_name, throwError=True)

        return self.stfObj.get_stf_parent_hubs(stop_name)

    def get_stop_parents(self, stop_name):
        self.has_stop(stop_name, throwError=True)

        return self.stfObj.get_stf_stop_parents(stop_name)

    def has_stop_attribute(self, stop_name, att_name, throwError=False):
        self.has_stop(stop_name, throwError=True)

        if (self.stfObj.has_stf_stop_attribute(stop_name, att_name)):
            return True
        else:
            if (throwError):
                htdte_logger.error("Stop %s does not have attribute %s" % (stop_name, att_name))
            else:
                htdte_logger.inform("Stop %s does not have attribute %s" % (stop_name, att_name))
            return False

    def get_stop_attribute(self, stop_name, att_name):
        self.has_stop_attribute(stop_name, att_name, throwError=True)

        return self.stfObj.get_stf_stop_attribute(stop_name, att_name)

    def has_stop_register_spec(self, stop_name, spec_name, *params):
        self.has_stop(stop_name, throwError=True)

        target = "hub" if spec_name in self.reg_spec_hub_targets else "stop"
        retVal = ""
        if spec_name in list(self.reg_spec_extra_params.keys()):
            args = []
            for i in range(0, self.reg_spec_extra_params[spec_name]):
                args.append(params[i])
            retVal = getattr(self.stfObj, "has_stf_%s_%s_reg_spec" % (target, spec_name))(stop_name, *args)
        else:
            retVal = getattr(self.stfObj, "has_stf_%s_%s_reg_spec" % (target, spec_name))(stop_name)
        if (retVal):
            return True
        else:
            return False

    def get_stop_register_spec(self, stop_name, spec_name, *params):
        if not self.has_stop_register_spec(stop_name, spec_name, *params):
            htdte_logger.error("Stop %s does not have register spec %s" % (stop_name, spec_name))

        target = "hub" if spec_name in self.reg_spec_hub_targets else "stop"
        retVal = ""
        if spec_name in list(self.reg_spec_extra_params.keys()):
            args = []
            for i in range(0, self.reg_spec_extra_params[spec_name]):
                args.append(params[i])
            retVal = getattr(self.stfObj, "get_stf_%s_%s_reg_spec" % (target, spec_name))(stop_name, *args)
        else:
            retVal = getattr(self.stfObj, "get_stf_%s_%s_reg_spec" % (target, spec_name))(stop_name)
        return retVal

    def has_child_ring_delay(self, stop_name, throwError=False):
        self.is_stop_a_hub(stop_name, throwError=True)

        if (self.stfObj.has_stf_hub_child_ring_delay(stop_name)):
            return True
        else:
            if (throwError):
                htdte_logger.error("Hub %s does not have a child ring delay!" % (stop_name))
            else:
                htdte_logger.inform("Hub %s does not have a child ring delay!" % (stop_name))
            return False

    def get_child_ring_delay_parts(self, stop_name):
        self.has_child_ring_delay(stop_name, throwError=True)

        childring_delay = self.stfObj.get_stf_hub_child_ring_delay(stop_name)
        m = re.search(r"(\d+)\(P\)", childring_delay)
        parent_delay = m.group(1)
        m = re.search(r"(\d+)\(C\)", childring_delay)
        child_delay = m.group(1)

        return {"parent": int(parent_delay), "child": int(child_delay)}

    def get_child_ring_latency(self, stop_name):
        self.is_stop_a_hub(stop_name)

        latency = 0

        for stop in self.get_hub_children(stop_name):
            latency += int(self.get_stop_attribute(stop["name"], "DELAY"))
        return latency

    def has_stop_reg_attribute(self, stop_name, reg, attribute, throwError=False):
        self.stop_has_register(stop_name, reg, throwError=True)

        if (self.stfObj.has_stf_register_attribute(stop_name, reg, attribute)):
            return True
        else:
            if (throwError):
                htdte_logger.error("Reg %s in stop %s does not have attribute %s" % (reg, stop_name, attribute))
            else:
                htdte_logger.inform("Reg %s in stop %s does not have attribute %s" % (reg, stop_name, attribute))

    def get_stop_reg_attribute(self, stop_name, reg, attribute):
        self.has_stop_reg_attribute(stop_name, reg, attribute)

        return self.stfObj.get_stf_register_attribute(stop_name, reg, attribute)
