from htd_basic_action import *
from htd_utilities import *
from htd_collaterals import *
from htd_player_top import *
import os
import re
# ------------------------------------------


class FIVR_FUSE(htd_base_action):
    def __init__(self,action_name,source_file,source_lineno,currentFlow,is_internal):
        htd_base_action.__init__(self,self.__class__.__name__,action_name,source_file,source_lineno,currentFlow,is_internal)
        self.arguments.set_argument("source", 1, "Specify which source for this action")
        self.arguments.declare_arg("cfg_file"             ,"The path to file define a test sequence in SPF format","string"      ,"none"  ,1 )
        #self.arguments.declare_arg("parallel_mode", "Used to dis/ena taplink parallel/specific taplink endpoint access  ", "bool", 1, 0) 
    #------------------------
    def verify_arguments(self):pass  #Req'd func don't delete
    def get_action_not_declared_argument_names(self): pass #Req'd func, don't delete
    def run(self):
        # Parse XML to d_dict
        xml_doc = minidom.parse(self.arguments.get_argument("cfg_file"))
        d_dict = {}
        found = {}
        # TODO Add loop on destination (mesh, core, etc)
        # Want to wait for final format though.
        for tap in xml_doc.getElementsByTagName("tap"):
            for reg in tap.getElementsByTagName("register"):
                for fld in reg.getElementsByTagName("name"):
                    #htdte_logger.inform("reg:%s fld:%s"%(reg.attributes['reg'].value,fld.attributes['field'].value))
                    data = int(fld.getElementsByTagName("data")[0].childNodes[0].data, 2)  # Assumes data only exists once per field
                    fld_name = "REG_%s_FLD_%s" % (reg.attributes['reg'].value, fld.attributes['field'].value)
                    d_dict[(tap.attributes['fivr_stap'].value, fld_name.upper())] = data
                    found[(tap.attributes['fivr_stap'].value, fld_name.upper())] = 0

        # Search TAP for matching regs & fields
        params = {}
        for agent in HTD_INFO.tap_info.get_tap_agents():
            for ir in HTD_INFO.tap_info.get_ir_commands(agent):
                params = {}
                for field in HTD_INFO.tap_info.get_ir_fields(ir, agent):
                    if (agent, field.upper()) in d_dict:
                        #htdte_logger.inform("agent:%s, field:%s"%(agent,field.upper()))
                        params["agent"] = agent
                        params["ir"] = ir
                        params["check"] = self.arguments.get_argument("check")
                        params["parallel_mode"] = 0  # TODO Move up to action control, and be smart about redundency. FIVR tap parallel mode seems to be unsuppored in CNL-P0 tapspec for example
                        params[field] = d_dict[agent, field.upper()]  # Output case matches what's in TAP, regardless of XML case
                        found[(agent, field.upper())] = 1
                if params:
                    self.get_curr_flow().exec_action(params, "TAP", self.__class__.__name__, 0, self.get_action_name())
        for key in found:
            if found[key] == 0:
                htdte_logger.error("Can't find FIVR FUSE field %s in any tap.  Please check your input XML for correctness" % key[1])


class FIVR_FUSE_10NMSRVR(htd_base_action):

    def __init__(self, action_name, source_file, source_lineno, currentFlow, is_internal):
        htd_base_action.__init__(self, self.__class__.__name__, action_name, source_file, source_lineno, currentFlow, is_internal)
        self.arguments.declare_arg("cfg_file", "The path to file define a test sequence in SPF format", "string", "none", 1)
        #self.arguments.declare_arg("parallel_mode", "Used to dis/ena taplink parallel/specific taplink endpoint access  ", "bool", 1, 0)
    # ------------------------

        self.d_dict = {}
        self.a_dict = {}
        self.f_dict = {}
        self.found = {}
        self.agents = []

    def verify_arguments(self):  # Req'd func don't delete
        # Parse XML to d_dict
        xml_doc = minidom.parse(self.arguments.get_argument("cfg_file"))
        # TODO Add loop on destination (mesh, core, etc)
        # Want to wait for final format though.
        # for reg in xml_doc.getElementsByTagName("register"):
        #    for fld in reg.getElementsByTagName("name"):
        #       	data= int(fld.getElementsByTagName("data")[0].childNodes[0].data,2)  #Assumes data only exists once per field
        #        fld_name = "REG_%s_FLD_%s"%(reg.attributes['reg'].value,fld.attributes['field'].value)
        #dom_name = fld.getElementsByTagName("dom")[0].childNodes[0].data
        #	self.d_dict[fld_name.upper()] = data
        #	print "MVLEIVAR data %s reg %s fld_name %s " %(data, fld_name, fld)
        #        self.found[fld_name.upper()] = 0

        for dom in xml_doc.getElementsByTagName("domain"):
            dom1 = dom.attributes['dom'].value
            TAP_d = CFG["FIVR_TAP_DEF"][dom1]
            #print"MVLEIVAR TAP %s" %TAP_d
            self.agents.append(TAP_d)
            for reg in dom.getElementsByTagName("register"):
                for fld in reg.getElementsByTagName("name"):
                    data = int(fld.getElementsByTagName("data")[0].childNodes[0].data, 2)  # Assumes data only exists once per field
                    fld_name = "DOM_%s_REG_%s_FLD_%s" % (TAP_d, reg.attributes['reg'].value, fld.attributes['field'].value)
                    fld1 = fld.attributes['field'].value
                    #dom_name = fld.getElementsByTagName("dom")[0].childNodes[0].data
                    self.d_dict[fld_name.upper()] = data
                    self.f_dict[fld_name.upper()] = "REG_%s_FLD_%s" % (reg.attributes['reg'].value, fld.attributes['field'].value)
                    self.a_dict[fld_name.upper()] = dom1
                    #print "MVLEIVAR data %s reg %s fld_name %s domain %s " %(self.d_dict[fld_name.upper()],self.f_dict[fld_name.upper()] , fld_name, self.a_dict[fld_name.upper()])
                    self.found[fld_name.upper()] = 0

    def get_action_not_declared_argument_names(self): pass  # Req'd func, don't delete

    def run(self):

        # Search TAP for matching regs & fields
        params = {}
        # for agent in HTD_INFO.tap_info.get_tap_agents():
        for agent in self.agents:
            #print "MVLEIVAR AGENT %s" %agent
            for ir in HTD_INFO.tap_info.get_ir_commands(agent):
                params = {}
                #print "MVLEIVAR IR %s" %ir
                for field in HTD_INFO.tap_info.get_ir_fields(ir, agent):
                    #print "MVLEIVAR field %s" %field
                    field2 = "DOM_" + agent + "_" + field
                    #print "MVLEIVAR el field2 %s" %field2
                    if field2.upper() in self.d_dict:
                        # if agent is self.a_dict[field2.upper()]:
                        #print "MVLEIVAR HERE HERE"
                        params["agent"] = agent
                        params["ir"] = ir
                        params["check"] = self.arguments.get_argument("check")
                        params["parallel_mode"] = 0  # TODO Move up to action control, and be smart about redundency. FIVR tap parallel mode seems to be unsuppored in CNL-P0 tapspec for example
                        params[field] = self.d_dict[field2.upper()]  # Output case matches what's in TAP, regardless of XML case
                        self.found[field2.upper()] = 1
                        print("MVLEIVAR agent %s ir %s value %s field %s TAP " % (params["agent"], params["ir"], params[field], field))

                if params:
                    print("MVLEIVAR sending %s " % (params))
                    self.get_curr_flow().exec_action(params, "TAP", self.__class__.__name__, 0, self.get_action_name())
        for fld, fnd in self.found.items():
            if fnd == 0:
                htdte_logger.error("Can't find FIVR FUSE field %s in any tap.  Please check your input XML for correctness" % fld)

# Action that writes TAP2CRI commands based on parameters from the XML file containing the fuse override recipe from the FIVR team.


class FIVR_FUSE_TAP2CRI(htd_base_action):
    # Based on the dictionary definition in the TE_cfg, the expected FIVR recipe XML file should have 5 layers: mode, domain, scope, register, and field.
    # The fuse data can be accessed with a similar dictionary reference as follows:
    # HTD_INFO.dict_fivr_recipe['VDAC']['domain']['boot']['scope']['cnxsp_top/fivrhip_sfr_fivrnorth']['register']['VRCIVRWP0']['field']['Target_Voltage']['data']

    def __init__(self, action_name, source_file, source_lineno, currentFlow, is_internal):
        htd_base_action.__init__(self, self.__class__.__name__, action_name, source_file, source_lineno, currentFlow, is_internal)
        self.arguments.declare_arg("fivr_mode", "Selects the desired FIVR mode from the fuse recipe. VDAC[default], VTARGET, Burnin, Sort, HVQK", "string", "none", 1)
        self.arguments.declare_arg("domain", "FIVR mode (boot,ddr,mesh,core", "string", 0, 1)
        #import pdb; pdb.set_trace()

# ------------------------

    def verify_arguments(self):  # Req'd func don't delete
        self.inform(("       Verifying %s::%s:%s:%d ....") % (htd_base_action.get_action_type(self),
                                                              htd_base_action.get_action_name(self),
                                                              htd_base_action.get_action_call_file(self),
                                                              htd_base_action.get_action_call_lineno(self)))

        valid_fivr_modes = ["VDAC", "VTARGET", "BURNIN", "SORT", "HVQK"]
        if (self.arguments.get_argument("fivr_mode").upper() in valid_fivr_modes):
            htdte_logger.inform(("Chosen FIVR mode: %s") % (self.arguments.get_argument("fivr_mode")))
        else:
            htdte_logger.error(("Illegal value %s used for fivr_mode. Please choose VDAC, VTARGET, Burnin, Sort, or HVQK") % (self.arguments.get_argument("fivr_mode")))

    def get_action_not_declared_argument_names(self): pass  # Req'd func, don't delete

    def run(self):
        fivr_mode = self.arguments.get_argument("fivr_mode").upper()
        requested_dom = self.arguments.get_argument("domain").lower()
        domains = ["boot", "ddr", "mesh", "core"]
        prev_max = 0

        for domain in domains:
            # HTD_INFO.dict_fivr_recipe['VDAC']['domain']['boot']['row']['1']['register']['VRCIVRWP0']['field']['Target_Voltage']['data']
            for index in range(1 + prev_max, len(HTD_INFO.dict_fivr_recipe[fivr_mode]['domain'][domain]['row']) + 1 + prev_max):

                #print ("HTD_INFO.dict_fivr_recipe['%s']['domain']['%s']['row']['%s']\n")%(fivr_mode,domain,str(index))
                for register in HTD_INFO.dict_fivr_recipe[fivr_mode]['domain'][domain]['row'][str(index)]['register']:
                    for field in HTD_INFO.dict_fivr_recipe[fivr_mode]['domain'][domain]['row'][str(index)]['register'][register]['field']:
                        params = {}
                        if (domain == requested_dom):
                            if (register == "Label"):
                                #import pdb; pdb.set_trace()

                                actionName = "Label" + HTD_INFO.dict_fivr_recipe[fivr_mode]['domain'][domain]['row'][str(index)]['register'][register]['field'][field]['size']
                                params = {"op": "PLABEL",
                                          "strvalue": HTD_INFO.dict_fivr_recipe[fivr_mode]['domain'][domain]['row'][str(index)]['register'][register]['field'][field]['size']
                                          }
                                self.get_curr_flow().exec_action(params, "GEN", self.__class__.__name__, 0, actionName)
                            elif (register == "Delay"):
                                actionName = "Delay" + field
                                params = {"op": "WAIT",
                                          "waitcycles": HTD_INFO.dict_fivr_recipe[fivr_mode]['domain'][domain]['row'][str(index)]['register'][register]['field'][field]['size'],
                                          "refclock": "tclk",
                                          "label": field,
                                          "description": field
                                          }
                                self.get_curr_flow().exec_action(params, "GEN", self.__class__.__name__, 0, actionName)
                            else:
                                actionName = register + "_" + field
                                params = {"scope": HTD_INFO.dict_fivr_recipe[fivr_mode]['domain'][domain]['row'][str(index)]['register'][register]['scope'],
                                          "reg": register,
                                          # "bfm_mode": "tap2cri",
                                          "read_type": 0,
                                          "check": 0,
                                          "read_modify_write": 0,
                                          field: HTD_INFO.dict_fivr_recipe[fivr_mode]['domain'][domain]['row'][str(index)]['register'][register]['field'][field]['data']
                                          }
                                #import pdb; pdb.set_trace()

                                if (domain == "core"):
                                    params["bfm_mode"] = "coretap2cri"
                                else:
                                    params["bfm_mode"] = "tap2cri"

                                self.get_curr_flow().exec_action(params, "XREG", self.__class__.__name__, 0, actionName)

            prev_max = index
