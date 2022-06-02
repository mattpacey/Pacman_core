from htd_utilities import *
import pickle
import datetime
import fileinput
import pydoc
from htd_collaterals_parser import *
import resource
import os

######################################### Class that builds the HTML help ############################################


class htd_html_builder(object):

    def __init__(self):
        self.main_html_file = None
        self.htd_html_help_dir = None

    def __open_file(self, htd_help_dir):
        self.htd_html_help_dir = htd_help_dir
        try:
            os.stat(self.htd_html_help_dir)
        except BaseException:
            os.mkdir(self.htd_html_help_dir)
        self.main_html_file = open(("%s/htd_te_collaterals_help.html") % (self.htd_html_help_dir), 'w')

    def __close_file(self):
        self.main_html_file.close()

    def __build_header(self):
        self.main_html_file.write("<!DOCTYPE html>\n<html>\n")
        self.main_html_file.write('<a name="top"></a>\n<body>')
        self.main_html_file.write('<p><h1> Test Environment Collaterals Content </h1></p><hr>\n')

    def __print_dictionaries(self, htd_info):
        for dictionary in list(htd_info.dictionaries_list.keys()):
            self.main_html_file.write(('<a href="%s_dictionary_help.html#dict_%s">dict_%s</a><br>\n') % (dictionary, dictionary, dictionary))
        self.main_html_file.write('<hr>\n')

    def __print_cfg(self, htd_info):
        self.main_html_file.write('<p><h3> HTD_INFO CFG data: </h3></p>\n')
        for cfg in list(htd_info.CFG.keys()):
            if (len(list(htd_info.CFG[cfg].keys())) > 0):
                self.main_html_file.write(('<a href="%s_CFG_help.html#CFG_%s">CFG[\"%s\"]</a><br>\n') % (cfg, cfg, cfg))
        self.main_html_file.write('<hr>\n')

    def __print_ui_collaterals(self, htd_ui_collaterals):
        for ui in list(htd_ui_collaterals.keys()):
            if ("html_content_help" in dir(htd_ui_collaterals[ui][1])):
                ui_html_help_file = (
                    ("%s/%s_content_help") % (self.htd_html_help_dir, htd_ui_collaterals[ui][1].__class__.__name__))
                htd_ui_collaterals[ui][1].html_content_help(("%s.html") % ui_html_help_file)
                self.main_html_file.write('<p><h3> HTD_INFO Content help file: </h3></p>\n')
                self.main_html_file.write(('<a href="%s.html">%s</a><br>\n') % (ui_html_help_file, htd_ui_collaterals[ui][1].__class__.__name__))

        self.main_html_file.write('<hr>\n')
        self.main_html_file.write('<p><h3> HTD_INFO User Interface API: </h3></p>\n')
        for ui in list(htd_ui_collaterals.keys()):
            self.main_html_file.write(('<a href="#%s">%s</a><br>\n') % (htd_ui_collaterals[ui][1].__class__.__name__,
                                                                        htd_ui_collaterals[ui][1].__class__.__name__))
        self.main_html_file.write('<hr>\n')
        for ui in list(htd_ui_collaterals.keys()):
            self.main_html_file.write(('<a name="%s"></a>\n') % (htd_ui_collaterals[ui][1].__class__.__name__))
            util_get_methods_prototypes_of_class(ui).print_html(self.main_html_file)
            self.main_html_file.write('<a href="#top">Top of Page</a><br><hr><br>\n')
        self.main_html_file.write('<hr>\n<a href="#top">Top of Page</a>\n')
        self.main_html_file.write('<br>\n</body>\n</html>\n')

    def __build_dictionary_html_table(self, dictionary_name, dictionary_object):
        html_file = open(("%s/%s_dictionary_help.html") % (self.htd_html_help_dir, dictionary_name), 'w')
        html_file.write("<!DOCTYPE html>\n<html>\n")
        html_file.write('<a name="top"></a>\n<body>')
        html_file.write(('<p><h1> Dictionary dict_%s Content </h1></p><hr>\n') % (dictionary_name))
        html_file.write('<table border="1">\n')
        util_print_dict_html_table(dictionary_object, html_file, 0,
                                   ("dict_%s") % (dictionary_name))
        html_file.write('</table>\n')
        html_file.write('<a href="#top">Top of Page</a>\n')
        html_file.write('<a href="htd_te_collaterals_help.html#top">Back to Main</a>\n')
        html_file.write('<hr>\n</body>\n</html>\n')
        html_file.close()

    def __generate_dictionary_html(self, dictionary, dictionary_object):
        if (util_get_dict_depth(dictionary_object) <= 4):
            self.__build_dictionary_html_table(dictionary, dictionary_object)
        else:
            # ---Splitting multihierarchical files by first key-------------------
            html_file = open(("%s/%s_dictionary_help.html") % (self.htd_html_help_dir, dictionary), 'w')
            html_file.write("<!DOCTYPE html>\n<html>\n")
            html_file.write('<a name="top"></a>\n<body>')
            html_file.write(('<p><h1> Dictionary dict_%s Content </h1></p>\n') % (dictionary))

            for h in list(dictionary_object.keys()):
                subfile_name = ("%s__%s__dictionary_help.html") % (dictionary, h.replace("/", "_"))
                html_file.write("<hr>\n")
                # ---Separate a single 2-nd level key : iterating a 3rd level
                if (len(list(dictionary_object[h].keys())) == 1):
                    html_file.write('<p><h2> %s</h2></p>' % (h.replace("/", "_")))
                    for sh in list(dictionary_object[h][list(dictionary_object[h].keys())[0]].keys()):
                        html_file.write(
                            ('<a href="%s#%s">%s</a><br>\n') % (subfile_name, sh, sh))
                else:
                    html_file.write('<p><h2>%s</h2></p>' % (h.replace("/", "_")))
                    for sh in list(dictionary_object[h].keys()):
                        html_file.write(
                            ('<a href="%s#%s">%s</a><br>\n') % (subfile_name, sh, sh))
                        # -----------------
                sub_html_file = open(("%s/%s") % (self.htd_html_help_dir, subfile_name), 'w')
                sub_html_file.write("<!DOCTYPE html>\n<html>\n")
                sub_html_file.write('<a name="top"></a>\n<body>')
                sub_html_file.write(
                    ('<p><h1> Dictionary dict_%s[%s] Content </h1></p><hr>\n') % (dictionary, h))
                sub_html_file.write('<table border="1">\n')
                if (len(list(dictionary_object[h].keys())) == 1):
                    util_print_dict_html_table(dictionary_object[h][list(dictionary_object[h].keys())[0]],
                                               sub_html_file, 0, ("dict_%s") % (dictionary))
                else:
                    util_print_dict_html_table(dictionary_object[h], sub_html_file, 0,
                                               ("dict_%s") % (dictionary))
                sub_html_file.write('</table>\n')
                sub_html_file.write('<a href="#top">Top of Page</a>\n')
                sub_html_file.write('<a href="htd_te_collaterals_help.html#top">Back to Main</a>\n')
                sub_html_file.write('<hr>\n</body>\n</html>\n')
                sub_html_file.close()

            html_file.write('<a href="#top">Top of Page</a>\n')
            html_file.write('<a href="htd_te_collaterals_help.html#top">Back to Main</a>\n')
            html_file.write('<hr>\n</body>\n</html>\n')
            html_file.close()

    def __generate_cfg_html(self, cfg_name, cfg_object):

        # create new cfg file
        html_file = open(("%s/%s_CFG_help.html") % (self.htd_html_help_dir, cfg_name), 'w')
        html_file.write("<!DOCTYPE html>\n<html>\n")
        html_file.write('<a name="top"></a>\n<body>')
        html_file.write(('<p><h1> Configuration %s Content </h1></p><hr>\n') % (cfg_name))

        html_file.write('<table border="1">\n')
        html_file.write('<tr bgcolor="blue" align="left"><th><font color="white"> Key</font></th><th><font color="white"> Value</font></th></tr>\n')
        for config_key in list(cfg_object.keys()):
            if (type(cfg_object[config_key]) in [int, int]):
                html_file.write('<tr  align="left"><th>%s</th><th>%s(0x%x)</th></tr>\n' %
                                (config_key, cfg_object[config_key], cfg_object[config_key]))
            else:
                html_file.write('<tr  align="left"><th>%s</th><th>%s</th></tr>\n' % (config_key, cfg_object[config_key]))

        html_file.write('</table>\n')
        html_file.close()

    def build_htd_html(self, htd_info, htd_ui_collaterals, html_help_dir):

        self.__open_file(html_help_dir)
        self.__build_header()
        self.__print_dictionaries(htd_info)
        self.__print_ui_collaterals(htd_ui_collaterals)
        self.__print_cfg(htd_info)
        self.__close_file()

        for dictionary in list(htd_info.dictionaries_list.keys()):
            self.__generate_dictionary_html(dictionary, htd_info.dictionaries_list[dictionary])

        for cfg in list(htd_info.CFG.keys()):
            if (len(list(htd_info.CFG[cfg].keys())) > 0):
                self.__generate_cfg_html(cfg, htd_info.CFG[cfg])
####################################End of Class that builds the HTML help ############################################
###################################Class template for regaccess########################################################


class htd_base_regaccess(object):

    def __init__(self):
        self.assigned_field_labales = []
        self.patmod_bits = dict()

    def read(self, action_ptr, flow_ptr, reg_name, reg_space, reg_file, data_by_fields, arguments_container, regaccess_category, reg_acc, express=0):
        htdte_logger.error(("Missing register read() handler in %s class..") % (self.__class__.__name__))

    def write(self, action_ptr, flow_ptr, reg_name, reg_space, reg_file, data_by_fields, arguments_container, regaccess_category, reg_acc, express=0):
        htdte_logger.error(("Missing register write() handler in %s class..") % (self.__class__.__name__))

    def rtl_specification_set(self, reg_name, reg_space, filter_str): pass

    def add_equiv_patmod_for_field(self, reg_space, reg_name, reg_field, equiv_network, equiv_agent, equiv_reg,
                                   equiv_field, reg_msb, reg_lsb, equiv_msb, equiv_lsb, parent_container):
        equiv_bits = "%s:%s" % (equiv_msb, equiv_lsb)

        key = "%s::%s::%s" % (reg_space, reg_name, reg_field)

        if key not in self.patmod_bits:
            self.patmod_bits[key] = dict()

        if reg_lsb not in self.patmod_bits[key]: # fix on jitbit20858
            self.patmod_bits[key][reg_lsb] = dict()

        # Save info for further usage
        self.patmod_bits[key][reg_lsb]["reg_lsb"] = reg_lsb
        self.patmod_bits[key][reg_lsb]["reg_msb"] = reg_msb
        self.patmod_bits[key][reg_lsb]["equiv_msb"] = equiv_msb
        self.patmod_bits[key][reg_lsb]["equiv_lsb"] = equiv_lsb

        rel_usage = HTD_INFO.patmods.add_related_usage_for_network_usage_match("xreg", reg_space, reg_name, reg_field,
                                                                               equiv_network, equiv_agent, equiv_reg,
                                                                               equiv_field, equiv_bits,
                                                                               "internal_" + parent_container.get_action_name())

        if rel_usage:
            bit_str = ""
            # Organize all of the bits
            for r_lsb in sorted(self.patmod_bits[key], reverse=True):
                r_msb = self.patmod_bits[key][r_lsb]["reg_msb"]
                e_msb = self.patmod_bits[key][r_lsb]["equiv_msb"]
                e_lsb = self.patmod_bits[key][r_lsb]["equiv_lsb"]

                # Set new bits on rel_usage
                if bit_str != "":
                    bit_str += ","
                bit_str += "%d:%d" % (e_msb, e_lsb)

            rel_usage.bits = bit_str

    def get_actual_assignment_boundaries(self, field, reg_name, reg_space, reg_file, parent_container, value, return_patmod_info=False):
        res = []
        if(not parent_container.arguments.is_argument_assigned(field)):
            (lsb, msb) = HTD_INFO.cr_info.get_cr_field_boundaries(field, reg_name, reg_space, reg_file)
            if not return_patmod_info:
                return [(lsb, msb, value, 0, 0)]
            else:
                return [(lsb, msb, value, 0, 0, 1, "")]
        else:
            for val in parent_container.arguments.get_argument(field):
                if(val.lsb >= 0):
                    #mask_hi = pow(2, val.msb) - 1
                    #mask_lo = pow(2, val.lsb) - 1
                    #mask = mask_hi ^ mask_lo
                    #value= (value & mask) >> val.lsb
                    (flsb, fmsb) = HTD_INFO.cr_info.get_cr_field_boundaries(field, reg_name, reg_space, reg_file)
                    if not return_patmod_info:
                        res.append((flsb + val.lsb, flsb + val.msb, 0 if(val.capture > 1) else val.value,
                                    1 if(val.capture > 0) else 0, 1 if(val.mask > 0) else 0))
                    else:
                        res.append((flsb + val.lsb, flsb + val.msb, 0 if(val.capture > 1) else val.value,
                                    1 if(val.capture > 0) else 0, 1 if(val.mask > 0) else 0, val.patmod_en, val.patmod_var))
                else:
                    (lsb, msb) = HTD_INFO.cr_info.get_cr_field_boundaries(field, reg_name, reg_space, reg_file)
                    if not return_patmod_info:
                        res.append((lsb, msb, 0 if(val.capture > 0) else val.value, 1 if(val.capture > 0) else 0, 1 if(val.mask > 0) else 0))
                    else:
                        res.append((lsb, msb, 0 if(val.capture > 0) else val.value, 1 if(val.capture > 0) else 0, 1 if(val.mask > 0) else 0,
                                    val.patmod_en, val.patmod_var))
        return res
    # -------------------

    def get_direct_label_assignment(self, parent_container, current_field, current_lsb):
        read_mode = False
        if(current_field in parent_container.arguments.arg_l):
            for val in parent_container.arguments.get_argument(current_field):
                if ((val.lsb >= 0 and current_lsb == val.lsb and val.label != "" and val.label != -1)
                        or (val.lsb < 0 and val.label != "" and val.label != -1)):
                    if CFG["HPL"].get("NEW_LABEL_SPEC"):
                        return val.label + "_strobe"
                    else:
                        return val.label
                if val.read_value > -1:
                    read_mode = True

        if CFG["HPL"].get("NEW_LABEL_SPEC"):
            if read_mode:
                return "%s_%s_strobe" % (parent_container.arguments.get_argument("label_prefix"), current_field)
            else:
                return ""
        else:
            return current_field


###################################End Class template for regaccess####################################################

class htd_ip_iter:

    def __init__(self, ip_name):
        self.ip_name = ip_name

    def all_si_list(self, formatter=None):
        """
        Provides an iterator for the all the instances of this IP available on RTL
        :param str formatter: Instead of returning a list of Ints, return a list of formatted strings "prefix_%i"
        :returns: list of int or list of string
        """
        dut = "si"
        itr = CFG["dut_die_ip_itr"]["ip"][self.ip_name]["dut"][dut]["valid"].split(',')
        return self.__format_itr(itr, formatter)

    def all_dut_list(self, formatter=None):
        """
        Provides an iterator for the all the instances of this IP available on this DUT
        :param str formatter: Instead of returning a list of Ints, return a list of formatted strings "prefix_%i"
        :returns: list of int or list of string
        """
        dut = CFG["dut_die_ip_itr"]["common"]["active_die"]
        itr = CFG["dut_die_ip_itr"]["ip"][self.ip_name]["dut"][dut]["valid"].split(',')
        return self.__format_itr(itr, formatter)

    def all_enabled_list(self, formatter=None):
        """
        Provides an iterator for the all the instances of this IP currently enabled
        i.e. on client products cores can be fuse-disabled
        :param str formatter: Instead of returning a list of Ints, return a list of formatted strings "prefix_%i"
        :returns: list of int or list of string
        """
        if 'enabled_ips' in CFG["dut_die_ip_itr"]["ip"][self.ip_name]:
            enabled_ips = CFG["dut_die_ip_itr"]["ip"][self.ip_name]['enabled_ips'].split(',')
            itr = [dut for dut in self.all_dut_list() if dut in enabled_ips]
        elif 'disabled_ips' in CFG["dut_die_ip_itr"]["ip"][self.ip_name]:
            disabled_ips = CFG["dut_die_ip_itr"]["ip"][self.ip_name]['disabled_ips'].split(',')
            itr = [dut for dut in self.all_dut_list() if dut not in disabled_ips]
        else:
            itr = []
            htdte_logger.error("Need to set either enabled_ips or disabled_ips in CFG:dut_die_ip_itr:ip:%s" % self.ip_name)

        return self.__format_itr(itr, formatter)

    @staticmethod
    def __format_itr(itr, formatter):
        if formatter:
            return [formatter % i for i in itr]
        else:
            return itr


#htdPlayer = None
# --------------------------------------
#
# -------------------------------------
HTML_Help_dir = ("%s/html_help/") % (os.environ.get('PWD'))
HTD_INFO = htd_collaterals_engine()
HTD_HTML_BUILDER = htd_html_builder()

if (os.environ.get('HTD_TE_CFG') is None and TE_Cfg_override == ""):
    htdte_logger.error(
        'Missing obligatory unix environment ENV[HTD_TE_CFG] or command line "-tecfg <path to cfg xml>" -  ( PROJECT dependent TE CFG XML file path) ')
te_cfg = os.environ.get('HTD_TE_CFG')
if (TE_Cfg_override != ""):
    te_cfg = TE_Cfg_override
if (not os.path.isfile(te_cfg)):
    htdte_logger.error(('The TE CFG file (%s) , given in %s - is not file or not exists') % (
        te_cfg, "ENV[HTD_TE_CFG]" if (TE_Cfg_override == "") else "CMD argument \"-tecfg <path to cfg>\""))
htdte_logger.inform("Adding USER LIBRARY path=", te_cfg)
if (os.environ.get('HTD_TE_CFG_ONLY') == "1"):
    xmldoc = minidom.parse(te_cfg)
    HTD_INFO.read_cfg(xmldoc, "CFG", te_cfg)
    CFG = HTD_INFO.CFG
elif (os.getenv("HTD_TE_CFG_ENV_ONLY", "0") == "1"):
    HTD_INFO.read_te_cfg(te_cfg)
else:
    HTD_INFO.read_te_cfg(te_cfg)
    # ------------------------------------
    if ("CMD" not in list(HTD_INFO.CFG.keys())):
        HTD_INFO.CFG["CMD"] = {}
    CFG = HTD_INFO.CFG
    # --Create Dynamic config methods---
    dynamic_methods_module = "collateral_dynamic_members.py"
    file_name = HTD_INFO.create_dynamic_methods_module(dynamic_methods_module)
    print(("Loading %s ....") % (dynamic_methods_module))
    status, mname, py_mod = util_dynamic_load_external_module(dynamic_methods_module)
    if (not status):
        htdte_logger.error((
                           " Not existent \"%s\" module -generated by RES.create_dynamic_methods_module() \"<segment>:post_module\" ") % (
                           dynamic_methods_module))

    from htd_clocks import *

    clock_info = htd_clocks(CFG, htdte_logger)
    setattr(HTD_INFO, "clock_info", clock_info)
    # --Create Dynamic config methods---
    from collateral_dynamic_members import *
    # ---Create dynamic signal access method

    def SIGMAP(sig_name): return HTD_INFO.CFG['FlowSignals'][sig_name] if (
        sig_name in list(HTD_INFO.CFG['FlowSignals'].keys())) else htdte_logger.error(
        ("Can't find signal alias -\"%s\" at %s or TE_cfg.xml:CFG['FlowSignals'] ") % (
            sig_name, os.environ.get('HTD_SIGNALS_MAP')))
    # -------------------------------------------------------------
    if (os.environ.get('HTD_TE_COLLATERALS_COMPILE_MODE') != "1"):
        # --------Adding UI info---------------------------
        htd_collaterals_ui_modules = {}

        #---------------------------------------
        #------------Register Access processing--------------
        if (os.environ.get('HTD_TE_INFO_UI_HELP') == None and os.environ.get('HTD_TE_CMD_HELP_MODE') == None):
            xml_docs_l = HTD_INFO.get_xml_docs_multiple_files(HTD_INFO.te_xfg_docs_xml_list, HTD_INFO.path_to_tecfg)
            HTD_INFO.read_RegAccInfo(xml_docs_l, HTD_INFO.path_to_tecfg)
            HTD_INFO.read_patmod_info(xml_docs_l, HTD_INFO.path_to_tecfg)

        # ----------------------------------
        if (os.environ.get('HTD_TE_CMD_HELP_MODE') is None):
            if ("INFO" not in list(CFG.keys())):
                htdte_logger.inform(" !!!WARNING: No HTD_INFO API initilized under \"INFO\" configuration . ")
            if (os.environ.get('HTD_TE_INFO_UI_HELP') is not None and (
                    os.environ.get('HTD_TE_INFO_UI_HELP') not in list(CFG["INFO"].keys()))):
                htdte_logger.error(("Can't find INFO API %s name :given by -info_ui_help  . ") % (
                    os.environ.get('HTD_TE_INFO_UI_HELP')))
            # ---------------------------------
            if ("INFO" in list(CFG.keys())):
                for var in list(CFG["INFO"].keys()):
                    if (isinstance(CFG["INFO"][var], dict) and ("class" in list(CFG["INFO"][var].keys())) and (
                            os.environ.get('HTD_TE_INFO_UI_HELP') is None or var == os.environ.get(
                            'HTD_TE_INFO_UI_HELP'))):
                        if ("module" not in list(CFG["INFO"][var].keys())):
                            htdte_logger.error((
                                               " Missing mopdule name in <CFG category=\"INFO\"> -><Var key=\"%s\" module=<PY_MODULE_NAME_DEFINE_UI_CLASS_NAME>] configuration in TE_cfg - specify the module name for accessing collateral-%s . ") % (
                                               var, var))
                        if ("path" not in list(CFG["INFO"][var].keys())):
                            htdte_logger.error((
                                               " Missing <CFG category=\"INFO\"> -><Var key=\"%s\" path=<PATH_TO_PY_MODULE_DEFINE_UI_CLASS>] configuration in TE_cfg - specify the class object for accessing collateral-%s   . ") % (
                                               var, var))
                        module_path = ("%s/%s") % (CFG["INFO"][var]["path"], CFG["INFO"][var]["module"] + ".py")
                        matchEnv = re.match(r"\$([A-z0-9_]+)", module_path)
                        if matchEnv:
                            for match in matchEnv.groups():
                                if (os.environ.get(match) is None):
                                    htdte_logger.error((
                                                       "Can't resolve UNIX env \"%s\" atribute in <Var key=\"%s\" path=<PATH_TO_PY_MODULE_DEFINE_UI_CLASS>...") % (
                                                       match))
                                module_path = module_path.replace(("$%s") % (match), os.environ.get(match))
                        # --Adding the module location to sys.path to resolve a possible internal import there
                        module_path_l = module_path.split("/")
                        sys.path.append(module_path.replace(module_path_l[len(module_path_l) - 1], ""))
                        # ---Actual loading the module
                        if (not os.path.exists(module_path)):
                            htdte_logger.error((
                                               " The requested HTD_INFO UI Python module path not exists or not accessable: %s   . ") % (
                                               module_path))
                        status, mname, py_mod = util_dynamic_load_external_module(module_path)
                        if (not status):
                            htdte_logger.error((" Can't load HTD_INFO UI module - %s ") % (module_path))
                        exec((("from %s import *") % (mname)), globals())
                        htdte_logger.inform(("Successfully loaded HTD_INFO UI module=%s") % (module_path))
                        curr_obj = eval(CFG["INFO"][var]["class"])()
                        setattr(HTD_INFO, var, curr_obj)
                        htd_collaterals_ui_modules[CFG["INFO"][var]["module"]] = (module_path, curr_obj)

                        # support external collaterals generation
                        if (os.environ.get('HTD_GENERATE_EXTERNAL_COLLATERALS')):
                            for single_key in list(CFG["INFO"][var].keys()):
                                if (single_key not in ["class", "module", "path"]):
                                    execution_file = "%s/%s" % (os.environ.get("HTD_COLLATERALS_UI_LOCATION"), CFG["INFO"][var][single_key])
                                    htdte_logger.inform("Executing collaterals file %s" % (execution_file))
                                    exec(compile(open(execution_file).read(), execution_file, 'exec'))

        if (os.environ.get('HTD_TE_COLLATERALS_HACK') is not None and os.environ.get('HTD_TE_INFO_UI_HELP') is None):
            misc_info_module = os.environ.get('HTD_TE_COLLATERALS_HACK')
            status, mname, py_mod = util_dynamic_load_external_module(misc_info_module)
            if (not status):
                htdte_logger.error(
                    (" Not existent MISC INFO module - %s given in command line : \"-misc_info_module\" ") % (
                        misc_info_module))
            try:
                command_module = __import__(mname, globals()['__name__'])
                keys = command_module.__all__
            except AttributeError:
                keys = dir(command_module)
                # execute all methods within current module
                # for key in keys:
                # if(getattr(command_module, key).__module__==mname):
                methods = [x for x in keys if (
                    'func_code' in dir(getattr(command_module, x)) and getattr(command_module, x).__module__ == mname)]
                for m in methods:
                    htdte_logger.inform((" Calling INFO Misc module method: \"%s.%s()\" ") % (mname, m))
                    getattr(py_mod, m)()
            except ImportError:
                htdte_logger.error(
                    (" Fail to load  MISC INFO module - %s given in command line : \"-misc_info_module \" ") % (
                        misc_info_module))

        # -------------------------------------------------------------
        #     Generating dynamic HTML help
        # -----------------------------------------
            # ------------------------------------------
        if (os.environ.get('HTD_TE_INFO_UI_HELP') is not None):
            try:
                os.stat(HTML_Help_dir)
            except BaseException:
                os.mkdir(HTML_Help_dir)
            found_ui = False
            for ui in list(htd_collaterals_ui_modules.keys()):
                if (ui == CFG["INFO"][os.environ.get('HTD_TE_INFO_UI_HELP')]["module"]):
                    found_ui = True
                    if ("html_content_help" in dir(htd_collaterals_ui_modules[ui][1])):
                        ui_html_help_file = (
                            ("%s/%s_content_help") % (HTML_Help_dir, htd_collaterals_ui_modules[ui][1].__class__.__name__))
                        htd_collaterals_ui_modules[ui][1].html_content_help(("%s.html") % ui_html_help_file)
                        htdte_logger.inform(
                            ("\n\n\n***HTD_INFO UI %s HELP FILE CREATED:%s/%s_content_help.html\n\n\n\n") % (
                                os.environ.get("HTD_TE_INFO_UI_HELP"), HTML_Help_dir, ui_html_help_file))
                else:
                    htdte_logger.error((" The INFO UI \"%s\" have not defined html_content_help() method  ") % (ui))
            if (not found_ui):
                htdte_logger.error((
                                   " The INFO UI name - \"%s\" is not defined in TE_cfg: CFG[\"INFO\"], available modules are: %s  ") % (
                                   os.environ.get('HTD_TE_INFO_UI_HELP'),
                                   str([x for x in list(CFG["INFO"].keys()) if
                                        (isinstance(CFG["INFO"][x], dict) and "module" in list(CFG["INFO"][x].keys()))])))
        # ----------------------------------------
        if (os.environ.get('HTD_TE_COLLATERALS_HELP_MODE') not in [None, 0] or os.environ.get(
                'HTD_TE_HELP_MODE') is not None):
            HTD_HTML_BUILDER.build_htd_html(HTD_INFO, htd_collaterals_ui_modules, HTML_Help_dir)
            htdte_logger.inform(("***HTD_INFO HELP FILE CREATED:%s/htd_te_collaterals_help.html") % (HTML_Help_dir))

    # Add a data structure for IPs which can have varying numbers of instances, based on model, as well as support for dynamic chops.
    HTD_IP_ITR = {}
    for ip in CFG.get("dut_die_ip_itr", {}).get("ip", {}):
        HTD_IP_ITR[ip] = htd_ip_iter(ip)
