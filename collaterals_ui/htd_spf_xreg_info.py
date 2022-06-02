import socket
import sys
import re
import os
import subprocess
from htd_tap_info import *
from htd_utilities import *
from htd_collaterals import *
path_to_collateral_interface = ("%s/bin/API_SERVER_CLIENT") % (os.environ.get('SPF_ROOT'))
sys.path.insert(0, path_to_collateral_interface)
from collateral_interface import Client


class htd_spf_xreg_info(htd_info_server):

    def __init__(self):
        htd_info_server.__init__(self, 0 if(os.environ.get('NO_XREGSERVER_RUN') is not None or os.environ.get('NO_XREGSERVER_RUN') != "1") else 1)
        if(os.environ.get('HTD_PROJ') is None):
            htdte_logger.error('Missing obligatory unix environment ENV[HTD_PROJ] ')
        proj = os.environ.get('HTD_PROJ').upper()
        # ------------------------
    # if(os.environ.get('XREG_SPF_SERVER')==None):
    #     htdte_logger.error( 'Missing obligatory unix environment ENV[XREG_SPF_SERVER] - must point to SPF Xreg info server ')
    #htdte_logger.inform(("Using TAP server path=%s")%(os.environ.get('XREG_SPF_SERVER')))
    # if(not os.path.exists(os.environ.get('XREG_SPF_SERVER'))):
    #   htdte_logger.error(( 'The TAP server path (%s) given in ENV[XREG_SPF_SERVER] - is not exists')%(os.environ.get('XREG_SPF_SERVER')))
        # --------------------------------
        if(os.environ.get('SPF_ROOT') is None):
            htdte_logger.error('Missing SPF_ROOT env. (should it  be set in TE_cfg or in xterm ?')
        LdLibraryPath = ("%s/lib/perl5%s") % (os.environ.get('SPF_ROOT'),
                                              ("" if (os.environ.get('LD_LIBRARY_PATH') is None) else (":%s") % (os.environ.get('LD_LIBRARY_PATH'))))
        os.environ['LD_LIBRARY_PATH'] = LdLibraryPath
        htdte_logger.inform(('SPF setup done: setenv LD_LIBRARY_PATH %s') % (os.environ.get('LD_LIBRARY_PATH')))
        # --------------------------------
        if(os.environ.get('HTD_SPF_TAP_SPEC_FILE') is None):
            htdte_logger.error('Missing obligatory TE_cfg.cml parameter HTD_SPF_TAP_SPEC_FILE.')
        htdte_logger.inform(("Using HTD_SPF_TAP_SPEC_FILE file=%s") % (os.environ.get('HTD_SPF_TAP_SPEC_FILE')))
        self.spec_file = os.environ.get('HTD_SPF_TAP_SPEC_FILE')
        # ---------------------------------------
        ld_library = os.environ.get('LD_LIBRARY_PATH')
        ld_library_l = ld_library.split(":")
        if(("%s/lib") % os.environ.get('SPF_ROOT') not in ld_library_l):
            new_ld_library_path = ("%s/lib") % os.environ.get('SPF_ROOT')
            htdte_logger.inform(('Modifying LD_LIBRARY_PATH =%s') % (new_ld_library_path))
            os.environ["LD_LIBRARY_PATH"] = new_ld_library_path
            os.putenv("LD_LIBRARY_PATH", new_ld_library_path)
        # --------------------------------
        #socket_file=("%s/SpfXregInfoServerSocket%d")%(os.environ.get('PWD') if("socket_file_location" not in CFG["INFO"].keys()) else CFG["INFO"]["socket_file_location"],os.getpid())
        #server_command = ("%s -sock %s -spec %s -silent 1")%(os.environ.get('XREG_SPF_SERVER'),"%s",self.spec_file)
        # -------------------------
        #if ("server_retry_times" in CFG["INFO"].keys()): self.set_server_retry(int(CFG["INFO"]["server_retry_times"]))
        #if ("server_timeout" in CFG["INFO"].keys()):self.set_server_timeout(int(CFG["INFO"]["server_timeout"]))
        # self.StartServer("XregSpfServer",socket_file,server_command,1200,4)
        # if(self.GetServerProcessId()>0):HTD_subroccesses_pid_tracker_list.append(self.GetServerProcessId())
        # self.rtl_path_register_indexing={}
        # Connecting to creg API server from DTS
    #path_to_collateral_interface = ("%s/bin/API_SERVER_CLIENT")%(os.environ.get('SPF_ROOT'))
    #sys.path.insert(0, path_to_collateral_interface)
    #from collateral_interface import Client
        #api_client = Client('uds',os.environ.get("PWD"))

        # Usage: api_client = Client(proto=<tcp|uds>, log_file=None, workspace=<current-dir>)
        # Please do not turn on log parameter as it clutters all rundirs with SPF info log files
        # If log files are required setup debug hook for that purpose.
        api_client = Client('uds', log_file=None, workspace='/tmp')
        #crif_files = { 'tap_punit' : { 'tap_punit' : [ '/p/hdk/rtl/ip_models/shdk74/chassis/chassis-srvr10nm-0p3-latest//target/punit_nebulon_lib/nebulon/output/crif/punit_top_crif.xml',],}}
        crif_files = {}
        for collateral in list(HTD_INFO.RegAccInfo.keys()):
            if ("regclass" not in list(HTD_INFO.RegAccInfo[collateral]["RegAccInfoProperties"].keys())):
                htdte_logger.error(('Missing obligatory reg_class value on \'%s\' collateral definition') % (collateral))
            if ("regSpace" not in list(HTD_INFO.RegAccInfo[collateral]["RegAccInfoProperties"].keys())):
                htdte_logger.error(('Missing obligatory reg_space value on \'%s\' collateral definition') % (collateral))
            if ("marshall" not in list(HTD_INFO.RegAccInfo[collateral]["RegAccInfoProperties"].keys())):
                htdte_logger.error(('Missing obligatory marshall location  or target path on \'%s\' collateral definition') % (collateral))
            crif_files[HTD_INFO.RegAccInfo[collateral]["RegAccInfoProperties"]["regclass"]] = \
                {HTD_INFO.RegAccInfo[collateral]["RegAccInfoProperties"]["regSpace"]:
                 [(HTD_INFO.collaterals_list[HTD_INFO.RegAccInfo[collateral]["RegAccInfoProperties"]["collateral"]]["path"],
                   HTD_INFO.RegAccInfo[collateral]["RegAccInfoProperties"]["marshall"])]}

        #crif_files = { 'IOSF_SB' : { 'GPSB' : [ ('/nfs/sc/proj/skx/skx_rtl127/lmoraseg/lastest_pacman/htdmain/project/icxsp/htd_te_proj/private_collaterals/reduced_spm_top_crif.xml','/nfs/sc/proj/skx/skx_rtl127/lmoraseg/lastest_pacman/htdmain/project/icxsp/htd_te_proj/private_collaterals/reduced_top_crif.marshall'),],}}
        htdte_logger.inform('Created socket connetion')
        self.CRobj = api_client.get_CR(crif_files, timeout_except=60 * int(CFG["INFO"]["server_timeout"]))
        htdte_logger.inform('Created socket connetion')
        #list_files = CRobj.get_csr_regfile_by_regname('PCU_BAR', 'IOSF_SB')
        #list_files = CRobj.get_csr_address_by_regname('PCU_BAR', '.+', 'GPSB')
        #htdte_logger.inform(("Using reg files=%s")%(list_files))
        #htdte_logger.inform('Created CRobj connetion')

    # --------Automatically discovered method , called by help if exists----------------
    def html_content_help(self, file_name):
        html_file = open(file_name, 'w')
        html_file.write("<!DOCTYPE html>\n<html>\n")
        html_file.write('<a name="top"></a>\n<body>')
        html_file.write('<p><h1> XREG Content </h1></p><hr>\n')
        #print (("Alexse : %s")%(self. get_cr_regfile_list()))
        html_file.write('<hr>\n<a href="#top">Top of Page</a>\n')
        html_file.write('<br>\n</body>\n</html>\n')
        html_file.close()
# --------------------

    def extract_result(self, msg):
        m = re.match(r"(\d)|", res_str)
        if(not m):
            htdte_logger.error(
                ("Response format received from SPF XREG server: (Expected format <error_status-0|1>|<message>', received - \"%s\"") % (res_str))
        else:
            if(m.groups()[0] == "1"):
                htdte_logger.error(("Error status received from XREG SPF Server: %s") % (m.groups()[1]))
            else:
                return m.groups()[1]
    # -----------------------------------

    def set_additional_register_indexing_rtl_path(self, indexing_str, crname, regfile_filter_str=""):
        (reginfo, regfile, dict_ref) = self.get_cr_info_by_name(crname, regfile_filter_str, 1, 1)
        if(regfile not in self.rtl_path_register_indexing):
            self.rtl_path_register_indexing[regfile] = {}
        self.rtl_path_register_indexing[regfile][crname] = indexing_str
    # ----------------No API for this

    def get_cr_regfile_list(self, register, register_space):
        message = "get_cr_regfile_list:;"
        rsp_str = self.CRobj.get_csr_regfile_by_regname(register, register_space)
        return rsp_str
    # -----------------------
    # def get_cr_name_by_address(self,address,regfile_filter_str="",port_id = -1, bar_id = -1, device_id = -1, function_id = -1, noerr=0):

    def get_cr_name_by_address(self, address, regfile, register_space):
        res_str = self.CRobj.get_csr_name_by_address(address, regfile, register_space)
        return res_str

    # ------------------------------
    def get_cr_regfile_property_by_name(self, reg, name, register_space, regfile, regfile_filter_str=""):
        res_str = self.CRobj.get_csr_regfile_property(name, regfile, register_space)[regfile.strip("$")]
        return res_str

    def has_cr_regfile_property_by_name(self, reg, name, register_space, regfile, regfile_filter_str=""):
        res_str = self.CRobj.has_csr_regfile_property(name, regfile, register_space)[regfile.strip("$")]
        return res_str

    def get_matching_crs_by_name(self, name, regfile_filter_str=""):
        res_str = self.extract_result(self.send_receive_message(
            ("get_matching_crs_by_name:name=%s,regfile_filter_str=%s;") % (name, regfile_filter_str)))
        return res_str.split(",")
    # -----------------------------------------------------------------
    # Should not be used - need to review if calling failure happen

    def get_cr_info_by_name(self, name, register_space, regfile_filter_str="", get_regfile=0, get_dict=0, get_dict_name=0, noerr=0):
        res_str = self.CRobj.get_csr_regfile_by_regname(name, register_space)
        return res_str

    def get_cr_info_and_regfile_name(self, name, register_space, regfile_filter_str="", get_regfile=0, get_dict=0, get_dict_name=0, noerr=0):
        res_str = self.CRobj.get_csr_regfile_by_regname(name, register_space)
        res_reg_file = []
        for regf in res_str:
            if (re.match(regf, regfile_filter_str)):
                res_reg_file.append(regf)
        if (len(res_reg_file) > 1):
            htdte_logger.error(
                ("Error status, the regular expression for the register file matches several register files  %s for cr: %s, please provide the correct scope") % (res_str, name))
        return "NONE", "".join(res_reg_file)

    def get_cr_regfile(self, name, register_space):
        rsp_str = self.CRobj.get_csr_regfile_by_regname(name, register_space)
        return res_str
    # Should not be used - need to review if calling failure happen def get_cr_info_and_regfile_name(self,name,regfile_filter_str=""):pass
    # -----------------------------------------------------------------

    def get_cr_address_by_name(self, name, reg_space, regfile_filter_str="", noerr=0):
        reg_file = regfile_filter_str.replace("$", "")
        res_str = self.CRobj.get_csr_address_by_regname(name, reg_file, reg_space)
        if (len(res_str) > 1):
            htdte_logger.error(
                ("Error status, the regular expression for the register file matches several register files  %s for cr: %s, please provide the correct scope") % (res_str, name))
        for key in list(res_str.keys()):
            return util_get_int_value(res_str[key])[1]

    # -----------------------------------------------------------------
    def get_cr_property_by_name(self, name, property_str, reg_space, regfile_filter_str=""):
        reg_file = regfile_filter_str.replace("$", "")
        res_str = self.CRobj.get_csr_property_by_name(property_str, name, reg_file, reg_space)
        if (len(res_str) > 1):
            htdte_logger.error(
                ("Error status, the regular expression for the register file matches several register files  %s for cr: %s, please provide the correct scope") % (res_str, name))
        for key in list(res_str.keys()):
            return res_str[key]
    # -----------------------------------------------------------------

    def has_cr_property_by_name(self, name, property_str, reg_space, regfile_filter_str=""):
        res_str = self.CRobj.has_csr_property_by_name(property_str, name, regfile_filter_str, reg_space)
        if (len(res_str) > 1):
            htdte_logger.error(
                ("Error status, the regular expression for the register file matches several register files  %s for cr: %s, please provide the correct scope") % (res_str, name))
        for key in list(res_str.keys()):
            return res_str[key]

    # -----------------------------------------------------------------
    def get_cr_fields(self, name, reg_space, regfile_filter_str=""):
        res_str = self.CRobj.get_csr_fields_by_regname(name, regfile_filter_str, reg_space)
        field_list = []
        if (len(res_str) > 1):
            htdte_logger.error(
                ("Error status, the regular expression for the register file matches several register files  %s for cr: %s, please provide the correct scope") % (res_str, name))
        for key in list(res_str.keys()):
            for field in list(res_str[key].keys()):
                if (field not in field_list):
                    field_list.append(field)
        return field_list
    # -----------------------------------------------------------------

    def get_cr_field_reset_val(self, field, crname, reg_space, regfile_filter_str="", reset_type=""):
        reg_file = regfile_filter_str.replace("$", "")
        res_str = self.CRobj.get_csr_field_resetVal_by_regname_fieldname(field, crname, reg_file, reg_space)
        if (len(res_str) > 1):
            htdte_logger.error(
                ("Error status, the regular expression for the register file matches several register files  %s for cr: %s, please provide the correct scope") % (res_str, crname))
        for key in list(res_str.keys()):
            return util_get_int_value(res_str[key])[1]

    # -----------------------------------------------------------------
    def get_cr_field_boundaries(self, field, crname, reg_space, regfile_filter_str=""):
        reg_file = regfile_filter_str.replace("$", "")
        res_str = self.CRobj.get_csr_field_boundaries_by_regname_fieldname(field, crname, reg_file, reg_space)
        if (len(res_str) > 1):
            htdte_logger.error(
                ("Error status, the regular expression for the register file matches several register files  %s for cr: %s, please provide the correct scope") % (res_str, crname))
        for key in list(res_str.keys()):
            return res_str[key]

    # -----------------------------------------------------------------
    def get_missing_cr_fields_rtlnodes(self, name, reg_space, regfile_filter_str=""):
        missing_field_rtl = self.CRobj.get_csr_fields_missingRTLName_by_regname(name, regfile_filter_str, reg_space)
        if (missing_field_rtl is not None) and (len(missing_field_rtl) > 1):
            htdte_logger.error(
                ("Error status, the regular expression for the register file matches several register files  %s for cr: %s, please provide the correct scope") % (res_str, crname))
        field_list = []
        if missing_field_rtl is not None:
            for key in list(missing_field_rtl.keys()):
                for field in missing_field_rtl[key]:
                    field_list.append(field)
        return field_list
    # --------------------
        # return missing_field_rtl[regfile_filter_str]
    # ------------------------------------------
    #
    # ------------------------------------------

    def has_rtl_node_backdoor_override(self, regfield, regname, regfile):
        if("XREG_RTL_NODES_BACKDOOR" not in list(CFG.keys()) or len(list(CFG["XREG_RTL_NODES_BACKDOOR"].keys())) == 0):
            return False
        if("regfile" not in list(CFG["XREG_RTL_NODES_BACKDOOR"].keys())):
            htdte_logger.error(
                "Improper CFG[XREG_RTL_NODES_BACKDOOR] table found in TE_cfg.xml - missing \"regfile\" entry. Expected structure: <CFG category=\"XREG_RTL_NODES_BACKDOOR\">\n <regfile name=\"<regfile_name>\" ...   ")
        if(regfile not in list(CFG["XREG_RTL_NODES_BACKDOOR"]["regfile"].keys())):
            return False
        if("register" not in list(CFG["XREG_RTL_NODES_BACKDOOR"]["regfile"][regfile].keys())):
            htdte_logger.error(("Improper CFG[XREG_RTL_NODES_BACKDOOR] table found in TE_cfg.xml - missing \"register\" entry. Expected structure: <CFG category=\"XREG_RTL_NODES_BACKDOOR\">\n <regfile name=\"%s\">\n   <register name=\"<regname>\" <field_name1>=\"<field_rtl_path>\" <field_name2>=\"<field_rtl_path>\" ") % (regfile))
        if(regname not in list(CFG["XREG_RTL_NODES_BACKDOOR"]["regfile"][regfile]["register"].keys())):
            return False
        if(regfield not in list(CFG["XREG_RTL_NODES_BACKDOOR"]["regfile"][regfile]["register"][regname].keys())):
            return False
        return True
    # ------------------------------------------
    #
    # ------------------------------------------

    def get_rtl_node_backdoor_override(self, regfield, regname, regfile):
        if(not self.has_rtl_node_backdoor_override(regfield, regname, regfile)):
            htdte_logger.error(("Trying to retrieve not existent XREG RTL node backdoor override (%s:%s:%s)...   ") % (regfile, regname, regfield))
        return CFG["XREG_RTL_NODES_BACKDOOR"]["regfile"][regfile]["register"][regname][regfield]
    # ------------------------------------------
    #
    # ------------------------------------------

    def resolve_rtl_node(self, field, crname, reg_space, regfile_filter_str="", instance_num=0):
        rtl_node = self.CRobj.get_csr_field_RTLName_by_regname_fieldname(field, crname, regfile_filter_str, reg_space)
        if (len(rtl_node) > 1):
            htdte_logger.error(
                ("Error status, the regular expression for the register file matches several register files  %s for cr: %s, please provide the correct scope") % (res_str, crname))
        for key in list(rtl_node.keys()):
            return rtl_node[key]
    # ------------------------------------------
    #
    # ------------------------------------------

    def has_rtl_node(self, field, crname, reg_space, regfile_filter_str=""):
        res_str = self.CRobj.has_csr_field_RTLName_by_regname_fieldname(field, crname, regfile_filter_str, reg_space)
        if (len(res_str) > 1):
            htdte_logger.error(
                ("Error status, the regular expression for the register file matches several register files  %s for cr: %s, please provide the correct scope") % (res_str, crname))
        for key in list(res_str.keys()):
            return res_str[key]

    # ------------------------------------------
    #
    # ------------------------------------------
    def has_no_rtl_nodes(self, crname, reg_space, regfile_filter_str=""):
        res_str = self.CRobj.has_csr_no_RTLName_by_regname(crname, regfile_filter_str, reg_space)
        if (len(res_str) > 1):
            htdte_logger.error(
                ("Error status, the regular expression for the register file matches several register files  %s for cr: %s, please provide the correct scope") % (res_str, crname))
        for key in list(res_str.keys()):
            return res_str[key]

    def verify_reg_access_integrity(self, reg_access, dictionary_name, reg_file):
        for reg_type in list(reg_access.keys()):
            if ('dictionary' not in list(reg_access[reg_type].keys())):
                dictionary_found_in_regAccInfo = True
                for regf in reg_access[reg_type]["RegisterFile"]:
                    if (re.search(regf, reg_file)):
                        return "True", reg_type
            else:
                if (reg_access[reg_type]['dictionary'] == dictionary_name):
                    dictionary_found_in_regAccInfo = True
                    for regf in reg_access[reg_type]["RegisterFile"]:
                        if (re.search(regf, reg_file)):
                            return "True", reg_type
