from htd_basic_action import *
from htd_utilities import *
from htd_collaterals import *
from htd_player_top import *
import os
import re
# ------------------------------------------


class SCRATCHPAD(htd_base_action):

    def __init__(self,action_name,source_file,source_lineno,currentFlow,is_internal):
        htd_base_action.__init__(self,self.__class__.__name__,action_name,source_file,source_lineno,currentFlow,is_internal)
        self.arguments.set_argument("source", 1, "Specify which source for this action")
        self.arguments.declare_arg("bypass","Enables pcodeio transaction of the IO_RESET_STALL register","bool",0,1 )
        self.arguments.declare_arg("stall","Enables pcodeio transaction of the IO_RESET_STALL register","bool",0,1 )

# Initialize io_register_bypass fields to 0
        for index in range(0, 95):
            index_hex = "0x" + format(index, '02x')
            # Add existance check to avoid failures on other produts
            if 'bypass_defs' in HTD_INFO.dictionaries_list:
                HTD_INFO.dict_bypass_defs['bypass_defs']['field'][index_hex]['value'] = 0
# ------------------------

    def verify_arguments(self):  # Req'd func don't delete
        self.inform(("       Verifying %s::%s:%s:%d ....") % (htd_base_action.get_action_type(self),
                                                              htd_base_action.get_action_name(self),
                                                              htd_base_action.get_action_call_file(self),
                                                              htd_base_action.get_action_call_lineno(self)))

        # Check for non-declared arguments, including the io_reset_bypass/stall fields
        not_declared_args = self.arguments.get_not_declared_arguments()

        if (self.arguments.get_argument("bypass") == self.arguments.get_argument("stall")):
            htdte_logger.error(("bypass and stall fields cannot be enabled at the same time"))

        for field in list(not_declared_args.keys()):
            for index in range(0, 95):
                index_hex = "0x" + format(index, '02x')
                if (field in HTD_INFO.dict_bypass_defs['bypass_defs']['field'][index_hex]['field_name']):
                    #print ("FCHAN4: field=%s")%(field)
                    reg_val = self.arguments.get_argument(field)
                    #print ("FCHAN4: value=%s")%(reg_val)
                    #import pdb; pdb.set_trace()
                    for arg in reg_val:
                        if arg.value <= 1:
                            #import pdb; pdb.set_trace()
                            if (self.arguments.get_argument("read_type") == 1):
                                HTD_INFO.dict_bypass_defs['bypass_defs']['field'][index_hex]['value'] = arg.read_value
                            elif (self.arguments.get_argument("read_type") == 0):
                                HTD_INFO.dict_bypass_defs['bypass_defs']['field'][index_hex]['value'] = arg.value
                            #print ("FCHAN4: arg=%s")%(HTD_INFO.dict_bypass_defs['bypass_defs']['field'][index_hex]['value'])
                        else:
                            htdte_logger.error(("Illegal value %s used for io_reset_bypass field %s. Only 0 or 1 is allowed") % (arg.value, field))

    def get_action_not_declared_argument_names(self): pass  # Req'd func, don't delete

    def run(self):
        reg_name = ""
        if (self.arguments.get_argument("bypass") == 1):
            reg_name = "reset_bypasses"
        elif (self.arguments.get_argument("stall") == 1):
            reg_name = "reset_stalls"

# Constructing the binary value for each bypass register
        val = ""
        bypass_val = ["", "", ""]
        for index in range(0, 95):
            index_hex = "0x" + format(index, '02x')
            val = str(HTD_INFO.dict_bypass_defs['bypass_defs']['field'][index_hex]['value'])
            #print ("%s\t\t\t%s")%(HTD_INFO.dict_bypass_defs['bypass_defs']['field'][index_hex]['field_name'],val)
            if ((index >= 0) and
                    (index <= 31)):
                bypass_val[0] = val + bypass_val[0]
                #print ("%s\t\t\t%s\t%s")%(HTD_INFO.dict_bypass_defs['bypass_defs']['field'][index_hex]['field_name'],val,bypass_val[0])
            if ((index >= 32) and
                    (index <= 63)):
                bypass_val[1] = val + bypass_val[1]
                #print ("%s\t\t\t%s\t%s")%(HTD_INFO.dict_bypass_defs['bypass_defs']['field'][index_hex]['field_name'],val,bypass_val[1])
            if ((index >= 64) and
                    (index <= 95)):
                bypass_val[2] = val + bypass_val[2]
                #print ("%s\t\t\t%s\t%s")%(HTD_INFO.dict_bypass_defs['bypass_defs']['field'][index_hex]['field_name'],val,bypass_val[2])

        #print ("FCHAN4:\nbypass0=%s\nbypass1=%s\nbypass2=%s")%(bypass_val[0],bypass_val[1],bypass_val[2])
        bypass_val[0] = int(bypass_val[0], base=2)
        bypass_val[1] = int(bypass_val[1], base=2)
        bypass_val[2] = int(bypass_val[2], base=2)

        #print ("FCHAN4:\nbypass0=%s\nbypass1=%s\nbypass2=%s")%(bypass_val[0],bypass_val[1],bypass_val[2])

# Construct parameters:
        params = {"read_type": self.arguments.get_argument("read_type"),
                  "check": self.arguments.get_argument("check"),
                  "read_modify_write": 0
                  }

# Call pcu_io_tap XREG action for each bypass register
        for index in range(0, 3):
            register = reg_name
            params[register.upper()] = bypass_val[index]
            register = register + "[" + str(index) + "]"
            params["reg"] = "IO_" + register.upper()

            actionName = self.get_action_name() + "_" + register
            #print ("%s\n%s")%(actionName, params)

            self.get_curr_flow().exec_action(params, "XREG", self.__class__.__name__, 0, actionName)
