# -*- coding: utf-8 -*-
from xml.dom import minidom
from htd_utilities import *
from htd_patmod_manager import *
import pickle
import json
import datetime
import fileinput
import getpass
import multiprocessing
import subprocess
import cProfile
import pstats
import io
import os
import xml.etree.ElementTree as et
import calendar
import struct
import binascii
import subprocess
import gzip
import shutil
import bz2
import sys
import zlib
import filelock
import pprint
import re
import copy
from xml.sax.saxutils import escape


HTD_Cfg_Up = 1
HTD_XML_parallel_processing_file_size_criteria = 2 * (1024 * 1024)  # 2M
HTD_XML_parallel_processing_proc_num = 8
HTD_XML_second_level_file_size_split_criteria = 10 * (1024 * 1024)  # 10M
HTD_XML_parallel_processing_text_file_lines_criteria = 100000  # 2M

# tag names
HTD_XML_SPLIT_TAG_NAME = "SPLIT"
HTD_XML_IMPORT_TAG_NAME = "IMPORT"
HTD_XML_FUNCTOR_TAG_NAME = "functor"
HTD_XML_SETENV_TAG_NAME = "setenv"
HTD_XML_COLLATERAL_TAG_NAME = "COLLATERAL"
HTD_XML_DICTIONARY_TAG_NAME = "dictionary"
HTD_XML_REGACCESS_TAG_NAME = "RegAccess"
HTD_XML_PATMOD_TAG_NAME = "PATMOD"

# Track the collateral compressor type
COLLATERAL_COMPRESSOR = "pickle"


# --------------------------------------------------
# Partially XML's processing - used as a thread_handler
# -------------------------------------------------


def process_handler_proceed_xml_part(te_cfg_col, file_name, dictionary, key, dic_entry, disable_duplicated_xml_node_error):
    xml_ptr = minidom.parse(file_name)
    res = {}
    col_eng = htd_collaterals_engine()
    col_eng.te_cfg_col = te_cfg_col
    col_eng.disable_duplicated_xml_node_error = disable_duplicated_xml_node_error
    col_eng.apply_current_dictionary_on_current_xml_collateral(dictionary, key, dic_entry, xml_ptr, res)
    os.remove(file_name)
    htd_compress.dump(res, open(("%s.%s") % (file_name, COLLATERAL_COMPRESSOR), "w"))


# --------------------------------------------------
# Partially csv files processing - used as a thread_handler
# -------------------------------------------------


def process_handler_proceed_csv_part(collaterals_list, te_cfg_col, file_name, dictionary, coll_name, dic_entry):
    fptr = open(file_name, 'r')
    res = {}
    line_num = 0
    col_eng = htd_collaterals_engine()
    col_eng.te_cfg_col = te_cfg_col
    line = fptr.readline()
    while line:
        line_num = line_num + 1
        if (("comment" in list(collaterals_list[coll_name].keys())) and (
                len(collaterals_list[coll_name]["comment"]) > 0) and (
                re.match(("^\s+%s") % (collaterals_list[coll_name]["comment"]), line))):
            line = fptr.readline()
            continue
        if (re.match("^-", line) or re.match(r"^\s*#", line)):
            line = fptr.readline()
            continue
        if (re.match(r"^\s*CSV_FORMAT", line) or re.match(r"^\s*\n", line)):
            line = fptr.readline()
            continue
        csv_entries = re.split(",", line.replace("\n", ""))
        col_eng.apply_current_dictionary_on_current_tab_collateral(dictionary, dic_entry, csv_entries, coll_name,
                                                                   line_num, res)
        line = fptr.readline()
    fptr.close()
    # --------------
    os.remove(file_name)
    htd_compress.dump(res, open(("%s.%s") % (file_name, COLLATERAL_COMPRESSOR), "w"))


# --------------------------------------------------
# Partially tab files processing - used as a thread_handler
# -------------------------------------------------


def process_handler_proceed_tab_part(collaterals_list, te_cfg_col, file_name, dictionary, coll_name, dic_entry,
                                     debug=0):
    fptr = open(file_name, 'r')
    res = {}
    line_num = 0
    col_eng = htd_collaterals_engine()
    col_eng.te_cfg_col = te_cfg_col
    line = fptr.readline()
    while line:
        line_num = line_num + 1
        if (("comment" in list(collaterals_list[coll_name].keys())) and (
                len(collaterals_list[coll_name]["comment"]) > 0) and (
                re.match(("^\s+%s") % (collaterals_list[coll_name]["comment"]), line))):
            line = fptr.readline()
            continue
        tabed_entries = re.split(" +", line)
        if (debug):
            htdte_logger.inform(("Adding : %s %d") % (str(tabed_entries), line_num))
        col_eng.apply_current_dictionary_on_current_tab_collateral(dictionary, dic_entry, tabed_entries, coll_name,
                                                                   line_num, res)
        line = fptr.readline()
    fptr.close()
    # --------------
    os.remove(file_name)
    htd_compress.dump(res, open(("%s.%s") % (file_name, COLLATERAL_COMPRESSOR), "w"))


# ---------------------------------------------------------
# this class handles all htd collaterals
# ---------------------------------------------------------


class htd_collaterals_engine(object):

    def __init__(self):
        self.collaterals_list = {}
        self.te_cfg_col = {}
        self.te_cfg_col_order = []
        self.CFG = {}
        self.patmods = HtdPatmodManager()
        self.te_cfg_functors_l = {}
        self.RegAccInfo = {}
        self.te_env = {}
        self.__defined_dynamicaly_methods = []
        self.__col_defined_dynamicaly_methods = []
        self.dictionaries_list = {}
        self.dictionary_entry_reserved_keys = ["node", "filter", "key", "collateral", "islist", "key_value_format"]
        self.config_entry_reserved_keys = ["key", "value", "filter_env", "filter_no_env", "filter_exp"]
        self.te_xfg_doc_xml = None
        self.te_xfg_docs_xml_list = None
        self.path_to_tecfg = ""
        self.curr_pid = os.getpid()
        self.disable_duplicated_xml_node_error = False
        self.te_cfg_env_output = "te_cfg_env.sourceme"
        self.te_cfg_env_f = None
        self.__cfg_allow_dynamic_assignment = []

    # ---------------------------------------------------------
    # filtering options - used for filter evaluation on different XML blocks
    # ---------------------------------------------------------

    def get_xml_attribute_value(self, value, xml_indentifier_str="", expectedIntType=False):
        str_val = util_resolve_unix_env(value, (xml_indentifier_str))
        str_val = self.resolve_functor_call(str_val, xml_indentifier_str)
        (isInt, eval_status) = util_get_int_value(str_val)
        if (expectedIntType):
            if (not isInt):
                htdte_logger.error((
                                   "Improper returned value type by XML portion:  %s: expected digital value , "
                                   "while returned - \"%s\"") %
                                   (xml_indentifier_str, str_val))
            else:
                return eval_status
        else:
            if (isInt):
                return eval_status
            else:
                return str_val.lstrip().rstrip()

    # ---------------------------------------------------------
    # filtering options - used for filter evaluation on different XML blocks
    # ---------------------------------------------------------

    def evaluate_filter(self, node, xml_indentifier_str):
        if ("filter_env" in list(node.attributes.keys())):
            filter_envs_str = node.attributes["filter_env"].value
            filter_envs_str = filter_envs_str.replace("^$", "")
            filter_envs_str = filter_envs_str.replace(r"\s+", "")
            filter_envs = re.split(",", filter_envs_str)

            htdte_logger.inform("evaluate_filter : filter_env %s" % (filter_envs_str))
            for filter_env in filter_envs:
                if (len(filter_envs) > 1 and ("filter_exp" in list(node.attributes.keys()))):
                    htdte_logger.error("filter_exp defined while filter_env includes multiple setenvs {}  {}".format(filter_envs, xml_indentifier_str))

                if (len(filter_envs) == 1 and ("filter_exp" in list(node.attributes.keys())) and os.environ.get(filter_env) is None):
                    htdte_logger.error((
                        "Unknown XML filtering environment name: Filtering on unix environment-\"%s\" "
                        "while the env. is not initilized ....\n%s") % (
                            filter_env, xml_indentifier_str))
                if (("filter_exp" in list(node.attributes.keys())) and (not re.match(node.attributes["filter_exp"].value, os.environ.get(filter_env))) and
                        (node.attributes["filter_exp"].value not in os.environ.get(filter_env))):
                    htdte_logger.inform(("Filtered out %s  ....") % (xml_indentifier_str))
                    return False
        if ("filter_no_env" in list(node.attributes.keys())):
            filter_no_envs_str = node.attributes["filter_no_env"].value
            filter_no_envs_str = filter_no_envs_str.replace("^$", "")
            filter_no_envs_str = filter_no_envs_str.replace(r"\s+", "")
            filter_no_envs = re.split(",", filter_no_envs_str)
            for filter_no_env in filter_no_envs:
                htdte_logger.inform("evaluate_filter : filter_no_env %s" % (filter_no_env))
                if (os.environ.get(filter_no_env) is not None):
                    htdte_logger.inform("evaluate_filter : filter out because %s exists " % (filter_no_env))
                    return False
        if ("filter_functor" in list(node.attributes.keys())):
            str_val = self.resolve_functor_call(node.attributes["filter_functor"].value,
                                                (xml_indentifier_str), 1)
            (isInt, eval_status) = util_get_int_value(str_val)
            if (not isInt):
                htdte_logger.error(
                    ("Improper returned value type by functor %s: expected digital value , while returned - \"%s\"") %
                    (node.attributes["filter_functor"], str_val))
            else:
                if (eval_status != 0):
                    htdte_logger.inform(
                        ("Filtered out %s  filter_functor=\"%s\"-->Evaluated to %s   ....") % (xml_indentifier_str,
                                                                                               node.attributes[
                                                                                                   "filter_functor"].value,

                                                                                               str_val))
                    return False
        return True

    # ---------------------------------------------------------
    # gets collateral file information
    # ---------------------------------------------------------

    def get_collateral_file_info(self, col_name, errpostfix=""):
        if (col_name not in list(self.collaterals_list.keys())):
            htdte_logger.error(("Can't find a collateral name - \"%s\" %s  ....") % (col_name, errpostfix))
        # --Assign the collateral file properties

        # file might be gzipped. In this case gunzip it to a new location
        file_name = self.collaterals_list[col_name]["path"]
        if (not os.path.isfile(file_name)):
            file_name = "%s.gz" % (file_name)
            if (not os.path.isfile(file_name)):
                htdte_logger.error(
                    ("Can't find a file - \"%s\" %s  (regular or copmpressed)....") % (
                        self.collaterals_list[col_name]["path"], errpostfix))
            else:
                # do the unzip
                self.collaterals_list[col_name]["path"] = self.get_collateral_from_zip(col_name, file_name)
                self.collaterals_list[col_name]["gzip"] = 1

        finfo = os.stat(self.collaterals_list[col_name]["path"])
        time_str_l = re.split(r"\s+", str(time.ctime(finfo.st_mtime)))
        time_str = str(list(calendar.month_abbr).index(time_str_l[1])) + "-" + time_str_l[2] + "-" + time_str_l[3]
        return ("%s:%s:%s") % (col_name, time_str, str(finfo.st_size))

    # ------------------------------------------------------------
    # handle zipped file collaterals
    # ------------------------------------------------------------
    def get_collateral_from_zip(self, col_name, file_name):
        # do the unzip
        base_file = os.path.basename(file_name)
        bare_file = os.path.splitext(base_file)[0]

        # add a timestamp
        time_stamp = time.strftime("%Y_%m_%d_%H_%M_%S", time.gmtime())
        user_name = os.getenv('USER', 'unknown')
        base_file = "%s_%s_%s_%s" % (user_name, time_stamp, os.getpid(), base_file)

        shutil.copy(file_name, "/tmp/%s" % (base_file))

        bare_file = os.path.splitext(base_file)[0]
        htdte_logger.inform("unzipping collaterals file /tmp/%s" % (base_file))
        subprocess.call("gunzip -f /tmp/%s" % (base_file), shell=True)
        return "/tmp/%s" % (bare_file)

    def import_collateral_compressor(self):
        # Determine which compressor we want to use
        if "collateral_compressor" not in self.CFG["INFO"] or self.CFG["INFO"]["collateral_compressor"].lower() not in [
                "pickle", "json"]:
            htdte_logger.inform(
                "CFG[INFO][collateral_compressor] is not set, or is set to an invalid value, using json")
            self.CFG["INFO"]["collateral_compressor"] = "json"
        else:
            htdte_logger.inform("Using %s as the collateral_compressor!" % (self.CFG["INFO"]["collateral_compressor"]))

        # Ensure we are using lowercase to pick the module
        self.CFG["INFO"]["collateral_compressor"] = self.CFG["INFO"]["collateral_compressor"].lower()

        # Re-import the compressor module as htd_compress
        sys.modules["htd_compress"] = sys.modules[self.CFG["INFO"]["collateral_compressor"]]
        import htd_compress
        # Need to make htd_compress available in global scope now
        globals()["htd_compress"] = htd_compress

        global COLLATERAL_COMPRESSOR
        COLLATERAL_COMPRESSOR = self.CFG["INFO"]["collateral_compressor"]

    # ------------------------------------------------------------
    # gets collateral pickle name
    # ------------------------------------------------------------
    def get_col_pickle_name(self, col_names, dictionary_name, info=0, base_crc=0):

        if (isinstance(col_names, str)):
            return ("%s/%s_%s.%s") % (
                os.environ.get('HTD_COLLATERALS_SAVED_IMAGE'), dictionary_name,
                self.collaterals_list[col_names]["file_info"],
                (self.CFG["INFO"]["collateral_compressor"] if (not info) else "info"))
        else:
            col_info_str = ""
            delimiter = ""
            crc_path_list = ""
            crc = base_crc
            model = ""
            cuenv = ""
            htdte_logger.inform("Base CRC: %d" % crc)

            col_sep = "" if os.getenv("HTD_DICT_COL_SEP") is None else os.getenv("HTD_DICT_COL_SEP")
            for col in sorted(set(col_names)):
                col_info_str = ("%s%s%s") % (col_info_str, col_sep, col)
                crc = util_get_cksum(self.collaterals_list[col]["path"]) ^ crc
                crc_path_list += (self.collaterals_list[col]["path"] + ",")
            if (len(col_info_str) > 180):
                col_info_str = col_info_str[0:180]
            htdte_logger.inform("Calculated CRC: %d Paths Used: %s" % (crc, crc_path_list))

            if (os.getenv("JSON_LEG_SWITCH") == "0"):

                # RegEx special characters to split from MODEL_ROOT. Only want the workweek part. (e.g. 17ww45)
                com = re.compile(r'[`\-=~!@#$%^&*()_+\[\]{};\'\\:"|<,./<>?]')

                ww = [b for b in com.split(str(os.getenv('MODEL_ROOT'))) if 'ww' in b.lower()]
                if (os.getenv("PICKLE_NAME_OVERRIDE", "") == ""):  # Need to specify a default if the param doesn't exist.
                    model = ('_').join([os.getenv("SOURCE_MODE"), (ww if ww else ['ww'])[0]])
                else:    
                    #ICXSP Merge request
                    model = ('_').join([os.getenv("PICKLE_NAME_OVERRIDE"), (ww if ww else ['ww'])[0]])

                prod = str(os.getenv('HTD_PROJ'))
                step = str(os.getenv('HTD_STEP'))

                model = ('_').join([prod, step, model])

                return ("%s/%s_%s_%d.%s") % (
                    os.environ.get('HTD_COLLATERALS_SAVED_IMAGE'), dictionary_name, model, crc,
                    (self.CFG["INFO"]["collateral_compressor"] if (not info) else "info"))

            else:
                return ("%s/%s_%s_%d.%s") % (
                    os.environ.get('HTD_COLLATERALS_SAVED_IMAGE'), dictionary_name, col_info_str, crc,
                    (self.CFG["INFO"]["collateral_compressor"] if (not info) else "info"))

    # -----------------------------------------------------------
    # Determine dict definition crc
    # -----------------------------------------------------------
    def get_dict_definition_crc(self, dictionary_name):
        # Strip HTD_ROOT from dictionary before hashing to let us move/copy a root.
        # Strip MODEL_ROOT since GK moves symlinks around during release
        # Actual effects of changing to a new MODEL_ROOT are covered later when the source file
        # checksum is calculated.
        dict_pre_hash = json.dumps(self.te_cfg_col[dictionary_name])
        dict_pre_hash = re.sub(os.environ.get('HTD_ROOT'), '', dict_pre_hash)
        dict_pre_hash = re.sub(os.environ.get('MODEL_ROOT'), '', dict_pre_hash)
        dict_definition_crc = zlib.crc32(dict_pre_hash.encode()) & 0xffffffff if os.getenv("HTD_BASE_CRC") is None else int(
            os.getenv("HTD_BASE_CRC"))
        return dict_definition_crc

    # ------------------------------------------------------------
    # Write collateral pickle info
    # ------------------------------------------------------------
    def write_col_pickle_info(self, col_names, dictionary_name, dictionary):
        dict_definition_crc = self.get_dict_definition_crc(dictionary_name)
        dicionary_file_name = self.get_col_pickle_name(col_names, dictionary_name, 1, base_crc=dict_definition_crc)
        if(not os.path.isfile(dicionary_file_name)):
            Stream = open(dicionary_file_name, "w", 1)
            if (isinstance(col_names, str)):
                Stream.write(("Collateral Name  : %s\n") % (col_names))
                Stream.write(("Dictionary Name  : %s\n") % (dictionary_name))
                Stream.write(("Path             : %s\n") % (self.collaterals_list[col_names]["path"]))
                finfo = os.stat(self.collaterals_list[col_names]["path"])
                Stream.write(("Modification Time: %s\n") % (str(finfo.st_mtime)))
                Stream.write(("File Size        : %s\n") % (str(finfo.st_size)))
                Stream.write(("File CRC         : %s\n") % (str(util_get_cksum(self.collaterals_list[col_names]["path"]))))
                Stream.write("------------------------------------------------------------------------\n")
            else:
                for col in col_names:
                    Stream.write(("Name             : %s\n") % (col))
                    Stream.write(("Dictionary Name  : %s\n") % (dictionary_name))
                    Stream.write(("Path             : %s\n") % (self.collaterals_list[col]["path"]))
                    finfo = os.stat(self.collaterals_list[col]["path"])
                    Stream.write(("Modification Time: %s\n") % (str(time.ctime(finfo.st_mtime))))
                    Stream.write(("File Size        : %s\n") % (str(finfo.st_size)))
                    Stream.write(("Created by       : %s\n") % (getpass.getuser()))
                    Stream.write(("File CRC         : %s\n") % (str(util_get_cksum(self.collaterals_list[col]["path"]))))
                    Stream.write("------------------------------------------------------------------------\n")
            Stream.close()

    # ------------------------------------------------------------
    # gets saved pickle information
    # ------------------------------------------------------------
    def get_saved_pickle_info(self, dictionary="", pickle_name=""):
        info_str = ""
        save_image_dir_content = os.listdir(os.environ.get('HTD_COLLATERALS_SAVED_IMAGE'))
        for f in save_image_dir_content:
            if (re.search(self.CFG["INFO"]["collateral_compressor"], f) and (re.search(dictionary, f)) and (
                    re.search("info$", f))):
                fh = open(f, 'r')
                line = fh.readline()
                while line:
                    info_str += fh.readline()
                fh.close()
        return info_str

    # ------------------------------------------------------------
    # cfg command line override - override the default CFG through command line
    # ------------------------------------------------------------
    def cfg_command_line_override(self):
        # -----------------------
        # ---Apply cfg override from cmd after everything is loaded--------
        for category in list(HTD_Cfgs_Cmd_Override.keys()):
            for key in list(HTD_Cfgs_Cmd_Override[category].keys()):
                if (category not in list(self.CFG.keys())):
                    htdte_logger.error(
                        ("Trying to override not existent CFG category - (CFG[\"%s\"])  -  by command line") % (
                            category))

                final_value = HTD_Cfgs_Cmd_Override[category][key]
                b_category = self.CFG[category]
                # Create nested dict sctructure for all keys but final
                for k in key.split(':')[0:-1]:
                    if k not in b_category:
                        b_category[k] = {}
                    b_category = b_category.get(k)
                final_key = key.split(':')[-1]

                if (final_key in b_category):
                    # Final key already exists

                    if (isinstance(b_category[final_key], int)):
                        # If current value is in, commandine value must be int
                        final_int = util_get_int_value(final_value)
                        if (not final_int[0]):
                            htdte_logger.error(("Trying to convert not numeric value to int ... CFG[%s][%s]=(%s) ") % (
                                category, key, final_value))
                        b_category[final_key] = final_int[1]
                    else:
                        b_category[final_key] = final_value

                elif (category not in self.__cfg_allow_dynamic_assignment):
                    htdte_logger.error((
                        "Trying to override not existent CFG entry - (CFG[\"%s\"][\"%s\"])  -  by command line.\n"
                        "For enabling dynamic CMD initilization, pls add "
                        "<CFG category=\"%s\" allow_dynamic_assignment=\"1\" attribute.. ") % (category, key, category))
                else:
                    if (re.match(r"^\d+$", final_value)):
                        b_category[final_key] = int(final_value)
                    else:
                        b_category[final_key] = final_value

    # ------------------------------------------------------------
    # get string value from CFG
    # ------------------------------------------------------------

    def cfg_getstr(self, var_category, var_name, obligatory=1, location_str=""):
        info = inspect.getframeinfo(inspect.currentframe().f_back)[0:3]
        self._oblig_varcfg_info[var_name] = ("%s:%d") % (info[0], info[1])
        loc_str = location_str if location_str != "" else ("%s:%d") % (info[0], info[1])
        if (var_category not in list(self.CFG.keys())):
            if (obligatory):
                htdte_logger.error(("Missing obligatory CFG category:%s - requested by %s") % (var_category, loc_str))
            else:
                return ""
        elif (var_name not in list(self.CFG[var_category].keys())):
            if (obligatory):
                htdte_logger.error(
                    ("Missing obligatory CFG[\"%s\"][\"%s\"] - requested by %s") % (var_category, var_name, loc_str))
            else:
                return ""
        else:
            return self.CFG[var_category][var_name]  # ???????????????Make a dynamic method here checking existence!!!!

    # -------------------------------------------------
    # get integer value
    # ------------------------------------------------
    def cfg_getint(self, var_category, var_name, obligatory=1):
        info = inspect.getframeinfo(inspect.currentframe().f_back)[0:3]
        self._oblig_varcfg_info[var_name] = ("%s:%d") % (info[0], info[1])
        str_val = self.cfg_getstr(var_category, var_name, obligatory, ("%s:%d") % (info[0], info[1]))
        return int(str_val if str_val != "" else 0)

    # -----------------------------------------------------------------------
    # Traverse TE CFG XML sub tree
    # -----------------------------------------------------------------------
    def traverse_cfg_xml_node(self, rootNode, cfg_hash, dict_name, path_to_cfg, col_type):
        xml_indentifier = ("<dictionary name=\"%s\"> -> <%s > definition in TE_cfg file -\"%s\"") % (dict_name,
                                                                                                     rootNode.nodeName,
                                                                                                     path_to_cfg)
        if ("node" not in list(rootNode.attributes.keys()) and col_type == "xml"):
            htdte_logger.error(
                ("Wrong %s: Missing \"node\"=<parsed  entry subnode path in XML tree> atribute  ....") % (
                    xml_indentifier))
        for attr in list(rootNode.attributes.keys()):
            cfg_hash[attr] = self.get_xml_attribute_value(rootNode.attributes[attr].value,
                                                                                    xml_indentifier)
        # ----------Browsing all child nodes-----------------
        for childNode in rootNode.childNodes:
            childNodeName = childNode.nodeName
            if (childNode.nodeType == childNode.ELEMENT_NODE):
                # ---supported atributes are [node] or [node,key,value]---
                cfg_hash[childNodeName] = {}
                if ("key" not in list(childNode.attributes.keys())):
                    htdte_logger.error((
                        "Wrong <dictionary name=\"%s\"> -> <%s > definition in TE_cfg file "
                        "-\"%s\": Missing \"key\"=<parsed  entry subnode path in XML tree> "
                        "atribute in dictionary sub tree  ....") % (
                        dict_name, childNodeName, path_to_cfg))
                self.traverse_cfg_xml_node(childNode, cfg_hash[childNodeName], dict_name, path_to_cfg, col_type)
            elif (childNode.nodeType == childNode.TEXT_NODE):
                if (childNode.nodeValue.replace(" ", "") != "\n" and (len(
                        childNode.nodeValue.replace(" ", "").replace("\n", "").replace("\t",
                                                                                                                 "")) >
                        1)):
                    htdte_logger.error((
                        "Wrong text node - \"%s\" defined in <dictionary name=\"%s\"> -> <%s=%s > "
                        "definition in TE_cfg file -\"%s\": Nor expected node type - \"%d\" found  "
                        " ....") % (
                        rootNode.nodeName, dict_name, childNode.nodeName,
                        childNode.nodeValue.replace(" ", ""), path_to_cfg,
                        childNode.nodeType))
            elif (childNode.nodeName != "#comment"):
                htdte_logger.error((
                    "Wrong node - \"%s\" defined in <dictionary name=\"%s\"> -> <%s > definition "
                    "in TE_cfg file -\"%s\": Nor expected node type - \"%d\" found   ....") % (
                    rootNode.nodeName, dict_name, childNodeName, path_to_cfg, childNode.nodeType))

    # -----------------------------------------------------------------------
    # Read cfg file
    # -----------------------------------------------------------------------
    def read_cfg_file(self, cfg_path):
        htdte_logger.inform((" Opening external CFG XML file - %s ....") % (cfg_path))
        xmldoc = minidom.parse(cfg_path)

        xml_docs_l = []
        xml_docs_l.append(xmldoc)
        self.read_cfg(xml_docs_l, "CFG", cfg_path)
        self.read_RegAccInfo(xml_docs_l, cfg_path)
        self.read_patmod_info(xml_docs_l, cfg_path)

    # -----------------------------------------------------------------------
    # Extract CFG entries from XML cfg file
    # -----------------------------------------------------------------------
    def read_RegAccInfo(self, xml_docs_l, path_to_cfg):
        reg_acc_cfgs = self.read_tag_multiple_files(xml_docs_l, HTD_XML_REGACCESS_TAG_NAME)
        found_regfiles = {}
        for cfg in reg_acc_cfgs:
            # ---filtering option
            if (not self.evaluate_filter(cfg, ("<RegAccess category=\"%s\">") % (
                    cfg.attributes["category"].value))):
                continue
            if ("category" not in list(cfg.attributes.keys())):
                htdte_logger.error(
                    (
                        "Wrong <RegAccess> definition in TE_cfg file -\"%s\": Missing \"category\"=<register access type "
                        "config name> atribute  ....") % (
                        path_to_cfg))
            category = cfg.attributes["category"].value
            if (category in list(self.RegAccInfo.keys())):
                htdte_logger.error((
                                   "Wrong <RegAccess> definition in TE_cfg file -\"%s\": Duplicated RegAccInfo "
                                   "category - %s found.(Defined in %s and %s)  ....") %
                                   (path_to_cfg, category, self.RegAccInfo[category]["path"], list(self.RegAccInfo.keys())))
            # --------------------
            self.RegAccInfo[category] = {}
            self.RegAccInfo[category]["path"] = path_to_cfg
            self.RegAccInfo[category]["RegisterFile"] = []
            # -----------------
            if ("module" not in list(cfg.attributes.keys())):
                htdte_logger.error((
                    "Wrong <RegAccess> definition in TE_cfg file -\"%s\": Missing "
                    "\"module\"=<dynamic python API module name> atribute  ....") % (
                    path_to_cfg))
            # ------------------
            if ("dictionary" not in list(cfg.attributes.keys())):
                htdte_logger.error((
                    "Wrong <RegAccess> definition in TE_cfg file -\"%s\": Missing "
                    "\"dictionary\"=<register definition dictionary linkage> atribute  ....") % (
                    path_to_cfg))
            # ------Verify dictionary name----------------
            if (self.get_xml_attribute_value(cfg.attributes["dictionary"].value) != "NONE"):
                if (self.get_xml_attribute_value(
                        cfg.attributes["dictionary"].value) not in list(self.dictionaries_list.keys())):
                    htdte_logger.error((
                        "Wrong <RegAccess dictionary=\"%s\"> definition in TE_cfg file - "
                        "dictionary name is not recognized,Available dictionaries are : %s ....") % (
                        self.get_xml_attribute_value(cfg.attributes["dictionary"]),
                        str(list(self.dictionaries_list.keys()))))
            self.RegAccInfo[category]["dictionary"] = self.get_xml_attribute_value(cfg.attributes["dictionary"].value)
            # ------Verify dictionary name----------------
            current_module = self.get_xml_attribute_value(cfg.attributes["module"].value)
            if (current_module not in list(sys.modules.keys())):
                if ("path" not in list(cfg.attributes.keys())):
                    htdte_logger.error((
                        "Wrong <RegAccess dictionary=\"%s\"> definition in TE_cfg file - missing "
                        "the \"path\" attribute - dynamic module %s location ....") % (
                        self.get_xml_attribute_value(cfg.attributes["category"].value),
                        current_module))
                module_path = util_resolve_unix_env(
                    ("%s/%s.py") % (self.get_xml_attribute_value(cfg.attributes["path"].value), current_module))
                if (os.path.exists(module_path)):
                    status, mname, py_mod = util_dynamic_load_external_module(module_path)
                    if (not status):
                        htdte_logger.error((" Can't load register type transpose  module - %s ") % (module_path))
                    exec ((("from %s import *") % (mname)), globals())
                else:
                    htdte_logger.error((" Can't find register type transpose module - %s ") % (module_path))
            # ------Adding aditional XML configurartion options-----------------
            if ("RegAccInfoProperties" not in list(self.RegAccInfo[category].keys())):
                self.RegAccInfo[category]["RegAccInfoProperties"] = {}
            for attr in list(cfg.attributes.keys()):
                if (attr not in ["category", "dictionary", "module", "path", "filter_env", "filter_exp",
                                 "filter_functor"]):
                    self.RegAccInfo[category]["RegAccInfoProperties"][attr] = util_resolve_unix_env(
                        self.get_xml_attribute_value(cfg.attributes[attr].value))
            # ---Read all reg entries, expecting RegisterFile - list , tap...
            for ch in cfg.childNodes:
                if (ch.localName == "RegisterFile"):
                    if ("name" not in list(ch.attributes.keys())):
                        htdte_logger.error((
                            "Wrong <RegAccess category=\"%s\"> ->  <RegisterFile "
                            "name=\"<name>\"../> definition in TE_cfg file ,missing Register File "
                            "\"name\" attribute  ....") % (
                            category))
                    regfile = self.get_xml_attribute_value(ch.attributes["name"].value)
                    # if(regfile in found_regfiles.keys() and (found_regfiles[regfile]!=category) and cfg.attributes[
                    # "dictionary"]????):
                    #  htdte_logger.error( ("Duplicated <RegisterFile name=\"<%s>\"../> definition in TE_cfg
                    # file:<RegAccType name=\"%s\" ,previously defined in <RegAccType name=\"%s\"  ....")%(regfile,
                    # category,found_regfiles[regfile]))
                    self.RegAccInfo[category]["RegisterFile"].append(regfile)
                    found_regfiles[self.get_xml_attribute_value(ch.attributes["name"].value)] = category
                    # ????TODO - check if register file names are valid in crif
                elif (ch.localName == "table"):
                    if ("name" not in list(ch.attributes.keys())):
                        htdte_logger.error((
                            "Wrong <RegAccess category=\"%s\"> ->  <table name=\"<name>\"../> "
                            "definition in TE_cfg file ,missing table \"name\" attribute  ....") % (
                            category))
                    if ("table" not in list(self.RegAccInfo[category].keys())):
                        self.RegAccInfo[category]["table"] = {}
                    table_name = self.get_xml_attribute_value(ch.attributes["name"].value)
                    if (table_name not in list(self.RegAccInfo[category]["table"].keys())):
                        self.RegAccInfo[category]["table"][table_name] = {}
                    for attr in list(ch.attributes.keys()):
                        if (attr not in ["name"]):
                            self.RegAccInfo[category]["table"][table_name][attr] = self.get_xml_attribute_value(
                                ch.attributes[attr].value, ("<RegAccess category=\"%s\">") % (category))
                # ---------------------
                elif (ch.nodeType == ch.ELEMENT_NODE):
                    if ("class" not in list(ch.attributes.keys())):
                        htdte_logger.error((
                            "Wrong <RegAccess category=\"%s\"> ->  <tap class=\"<name>\"../> "
                            "definition in TE_cfg file ,missing register class name in attribute  "
                            "....") % (
                            category))
                    class_name = self.get_xml_attribute_value(ch.attributes["class"].value)
                    # -----------------------------
                    self.RegAccInfo[category][ch.localName] = {}
                    handler_obj = eval(("%s") % (self.get_xml_attribute_value(ch.attributes["class"].value)))()
                    self.RegAccInfo[category][ch.localName]["obj"] = handler_obj
                    self.RegAccInfo[category][ch.localName]["params"] = []
                    # class_attr_l=inspect.getmembers(self.RegAccInfo[category][ch.localName], lambda a:not(
                    # inspect.isroutine(a)))
                    # class_variables=[a[0] for a in class_attr_l if not(a[0].startswith('__') and a[0].endswith('__'))]
                    self.RegAccInfo[category][ch.localName]["paramValues"] = {}
                    for attr in list(ch.attributes.keys()):
                        if (attr not in ["class"]):
                            self.RegAccInfo[category][ch.localName]["params"].append(attr)
                            val = self.get_xml_attribute_value(ch.attributes[attr].value,
                                                               ((
                                                                "<RegAccess category=\"%s\"\n   <%s \"%s\"=\"%s\" "
                                                                "...") % (
                                                                category, ch.localName, attr,
                                                                ch.attributes[attr].value)))
                            setattr(handler_obj, attr, val)
                            self.RegAccInfo[category][ch.localName]["paramValues"][attr] = val

    def read_patmod_info(self, xml_docs_l, path_to_cfg):
        patmod_cfgs = self.read_tag_multiple_files(xml_docs_l, HTD_XML_PATMOD_TAG_NAME)

        en = None
        for cfg in patmod_cfgs:
            # Check to see if PATMODS are actually enabled.
            if "enabled" in list(cfg.attributes.keys()):
                en_tmp = int(self.get_xml_attribute_value(cfg.attributes["enabled"].value))

                if en is not None and en_tmp != en:
                    htdte_logger.error("Found multiple PATMOD config sections with conflicting values for enabled! "
                                       "Please ensure there is only 1 enabled attribute in all <PATMOD> configs.")
                en = en_tmp
                self.patmods.enabled = en

            for var in cfg.childNodes:
                if var.localName == "var":
                    if "name" not in list(var.attributes.keys()):
                        htdte_logger.error("Attribute 'name' must be provided on PATMOD var entry")
                    if "description" not in list(var.attributes.keys()):
                        htdte_logger.error("Attribute 'description' must be provided on PATMOD var entry")
                    var_name = self.get_xml_attribute_value(var.attributes["name"].value)
                    var_desc = self.get_xml_attribute_value(var.attributes["description"].value)

                    new_patmod = HtdPatmod(var_name, var_desc)
                    for var_node in var.childNodes:
                        if var_node.localName == "values":
                            for val_node in var_node.childNodes:
                                if val_node.localName not in ["value", "value_range"]:
                                    continue
                                if "name" not in list(val_node.attributes.keys()):
                                    htdte_logger.error("Attribute 'name' must be provided on PATMOD value entry")

                                value_name = self.get_xml_attribute_value(val_node.attributes["name"].value)

                                if val_node.localName == "value":
                                    str_val = val_node.firstChild.nodeValue
                                    if re.match("^[Xx]", str_val):
                                        # Special handling for "X"
                                        new_patmod.add_value(value_name, "X")
                                    else:

                                        int_val = util_get_int_value(str_val)

                                        if int_val[0] == 1:
                                            new_patmod.add_value(value_name, str(int_val[1]))
                                        else:
                                            val = val_node.firstChild.nodeValue
                                            new_patmod.add_value(value_name, val)
                                elif val_node.localName == "value_range":
                                    range_val = val_node.firstChild.nodeValue
                                    range_vals = range_val.split(",")

                                    err_str = "Expecting 2 or 3 comma separated int values <start>,<end> or " \
                                              "<start>,<end>,<step_size>. Step size defaults to 1 if not specified"
                                    if len(range_vals) not in [2, 3]:
                                        htdte_logger.error(err_str)

                                    # Value ranges should have a start_val and stop_val
                                    (start_val_is_int, start_val) = util_get_int_value(range_vals[0].strip())
                                    (end_val_is_int, end_val) = util_get_int_value(range_vals[1].strip())
                                    step_size = 1
                                    step_size_is_int = 1

                                    # Convert step_size if it was specified
                                    if len(range_vals) == 3:
                                        (step_size_is_int, step_size) = util_get_int_value(range_vals[2].strip())

                                    # Do final error checking
                                    if start_val_is_int == 0 or end_val_is_int == 0 or step_size_is_int == 0:
                                        htdte_logger.error(err_str)

                                    # Reverse values if start value is bigger than end value
                                    if start_val > end_val:
                                        tmp = end_val
                                        end_val = start_val
                                        start_val = tmp

                                    if "lambda_x" in list(val_node.attributes.keys()):
                                        lambda_x = self.get_xml_attribute_value(val_node.attributes["lambda_x"].value)
                                    else:
                                        lambda_x = None

                                    # Add a value for every value in the range
                                    for i in range(start_val, end_val + 1, step_size):

                                        if lambda_x:
                                            name = eval('lambda x: {}'.format(lambda_x))(i)
                                        else:
                                            name = "%s%d" % (value_name, i)

                                        new_patmod.add_value(name, str(i))

                        if var_node.localName == "usages":
                            for usage_node in var_node.childNodes:
                                if usage_node.localName != "usage":
                                    continue
                                usage = HtdPatmodUsage()

                                required_atts = ["network"]
                                for att in required_atts:
                                    if att not in list(usage_node.attributes.keys()):
                                        htdte_logger.error("Usage node in PATMOD must contain the '%s' attribute" % (att))

                                    usage.__setattr__(att, self.get_xml_attribute_value(usage_node.attributes[att].value))

                                optional_atts = ["agent", "register", "field", "bits", "label_ext"]
                                multi_fields = []
                                for att in optional_atts:
                                    # usage[att] = None
                                    if att in list(usage_node.attributes.keys()):
                                        if att == "field":
                                            multi_fields = self.get_xml_attribute_value(usage_node.attributes[att].value).split(",")
                                        else:
                                            usage.__setattr__(att, self.get_xml_attribute_value(usage_node.attributes[att].value))

                                if usage.network != "xreg" and usage.agent is None:
                                    htdte_logger.error("Usage node in PATMOD must contain the 'agent' attribute unless "
                                                       "the network type is xreg")

                                if usage.network != "fuse" and usage.register is None:
                                    htdte_logger.error("Usage node in PATMOD must contain the 'register' attribute unless "
                                                       "the network type is fuse")

                                if len(multi_fields) > 0:
                                    for field in multi_fields:
                                        usage_copy = copy.deepcopy(usage)
                                        usage_copy.__setattr__("field", field)
                                        new_patmod.add_usage(usage_copy)
                                else:
                                    new_patmod.add_usage(usage)
                                self.patmods.add_patmod(new_patmod)

                    # Print out this patmod
                    new_patmod.print_patmod_info()
                elif var.localName == "group":
                    try:
                        group_name = self.get_xml_attribute_value(var.attributes["name"].value)
                    except KeyError:
                        htdte_logger.error("Attribute 'name' must be provided on PATMOD group entry")
                    try:
                        group_mode = self.get_xml_attribute_value(var.attributes["mode"].value)
                    except KeyError:
                        htdte_logger.error("Attribute 'mode' must be provided on PATMOD group entry")
                    new_group = HtdPatmodGroup(group_name, group_mode)
                    for var_node in var.childNodes:
                        if var_node.localName == "member":
                            try:
                                member_name = self.get_xml_attribute_value(var_node.attributes["name"].value)
                            except KeyError:
                                htdte_logger.error("Attribute 'name' must be provided on PATMOD group member entry")
                            new_group.add_member(member_name)
                    self.patmods.add_patmodgroup(new_group)

        base_ref = None
        for group in self.patmods.get_patmodgroups():
            base_ref = None
            for member in group.get_members():
                for patmod in self.patmods.get_patmods():
                    if member == patmod.name:
                        if base_ref is None:
                            base_ref = list(patmod.values.keys())
                        elif base_ref != list(patmod.values.keys()):
                            htdte_logger.error("All members of group {g_name} must have the same value keys. {p_name} is different".format(g_name=group.name, p_name=patmod.name))

    # -----------------------------------------------------------------------
    # Extract CFG entries from XML cfg file
    # -----------------------------------------------------------------------

    def read_cfg(self, xmldocs_l, node, path_to_cfg):
        cfgs_to_setenv = []
        if (os.getenv("HTD_CFG_TO_SETENV", "") != ""):
            cfgs_to_setenv = os.getenv("HTD_CFG_TO_SETENV", "").split()
        cfgs = self.read_tag_multiple_files(xmldocs_l, node)
        for cfg in cfgs:
            current_category = ""
            allowed_attributes = ["category", "filter_env", "filter_exp", "filter_functor", "error_assert",
                                  "disable_duplicated_xml_nodes_error", "description", "allow_dynamic_assignment"]
            # ----------------------
            if ("category" not in list(cfg.attributes.keys())):
                htdte_logger.error(
                    (
                        "Wrong <CFG> definition in TE_cfg file -\"%s\": Missing \"category\"=<category config name> "
                        "atribute  ....") % (
                        path_to_cfg))
            for atr in list(cfg.attributes.keys()):
                if (atr not in allowed_attributes):
                    htdte_logger.error((
                        "Wrong <CFG category=\"%s\"> definition in TE_cfg file -\"%s\": Unknown "
                        "attribute -\"%s\" : supported attributes are : %s  ....") % (
                        cfg.attributes["category"].value, path_to_cfg,
                        atr, allowed_attributes))
            # -----filtering option------
            if (not self.evaluate_filter(cfg, ("<CFG category=\"%s\"> definition in TE_cfg file -\"%s\">") % (
                    cfg.attributes["category"].value, path_to_cfg))):
                continue
            # ---------------------------
            error_assert = 0
            if (("error_assert" in list(cfg.attributes.keys())) and (
                    cfg.attributes["error_assert"].value in HTD_True_Statement)):
                error_assert = 1
            current_category = self.get_xml_attribute_value(cfg.attributes["category"].value)
            # ------------------------------------
            if ("allow_dynamic_assignment" in list(cfg.attributes.keys()) and cfg.attributes[
                    "allow_dynamic_assignment"].value in ["1", "True", "TRUE"]):
                self.__cfg_allow_dynamic_assignment.append(cfg.attributes["category"].value)
            # ------------------------------------

            vars_l = cfg.getElementsByTagName("Var")

            if (len(vars_l) > 0 and len(vars_l) < self.get_entries_for_cfg(cfg)):
                htdte_logger.error(
                    "category \"%s\" has an illegal mixture of Vars and other attributes, check your TE_cfg.xml file"
                    % (
                        current_category))

            if (current_category not in list(self.CFG.keys())):
                self.CFG[current_category] = {}
            for var in vars_l:
                if ("key" not in list(var.attributes.keys())):
                    htdte_logger.error((
                        "Wrong <Var> definition in TE_cfg file -\"%s\": Missing \"key\"=<config "
                        "definition key> atribute  ....") % (
                        path_to_cfg))
                # -Adding filter evaluation on entry ver -> key level
                if (not self.evaluate_filter(var, ("<Var key=\"%s\" > definition in TE_cfg file -\"%s\">") % (
                        var.attributes["key"].value, path_to_cfg))):
                    continue
                # --------------------
                attributes = [x for x in list(var.attributes.keys())]
                if (len([x for x in attributes if (x not in self.config_entry_reserved_keys)]) > 0):
                    # --There is a dictionary type of config
                    for attr in [x for x in attributes if (x != "key" and (x not in self.config_entry_reserved_keys))]:
                        if (self.get_xml_attribute_value(var.attributes["key"].value) not in list(self.CFG[
                                current_category].keys())):
                            self.CFG[current_category][self.get_xml_attribute_value(var.attributes["key"].value)] = {}

                        # resolve env. variable dependency
                        final_value = self.resolve_cfg_value(var.attributes[attr].value,
                                                             current_category,
                                                             var.attributes["key"].value)
                        sub_category = self.resolve_functor_call(var.attributes["key"].value, ("CFG[%s]") % (current_category))
                        attr_category = self.resolve_functor_call(attr, ("CFG[%s][%s]") % (
                            current_category, var.attributes["key"].value))
                        self.CFG[current_category][sub_category][attr_category] = final_value
                        if (current_category in cfgs_to_setenv):
                            self.write_to_te_cfg_env_sourceme(
                                "HTD_CFG__%s__%s__%s" % (current_category, sub_category, attr_category), final_value)
                else:
                    if ("value" not in list(var.attributes.keys())):
                        htdte_logger.error((
                            "Wrong <Var> definition in TE_cfg file -\"%s\": Missing "
                            "\"value\"=<config definition key> atribute  ....") % (
                            path_to_cfg))
                    final_value = self.resolve_cfg_value(var.attributes["value"].value,
                                                         current_category,
                                                         var.attributes["key"].value)
                    sub_category = self.resolve_functor_call(var.attributes["key"].value,
                                                             ("CFG[%s]") % (current_category))
                    self.CFG[current_category][sub_category] = final_value
                    if (current_category in cfgs_to_setenv):
                        self.write_to_te_cfg_env_sourceme("HTD_CFG__%s__%s" % (current_category, sub_category),
                                                          final_value)
            # --Non Vars entries--
            if (len(vars_l) < 1):
                self.CFG[current_category] = util_merge_dictionaries(self.CFG[current_category],
                                                                     self.traverse_cfg_entries(cfg))
            # ----Dynamically create access method
            if (current_category != ""):
                setattr(self, current_category, self.CFG[current_category])

    # ------------------------------------------
    #
    # ----------------------------------------

    def traverse_cfg_entries(self, rootNode):
        res = {}
        if (rootNode.nodeType == rootNode.TEXT_NODE or rootNode.nodeType == rootNode.COMMENT_NODE or rootNode.nodeName
                 == "Var"):
            return {}
        # -------------------------------------------
        if (rootNode.attributes is not None):
            for atr in list(rootNode.attributes.keys()):
                if (atr not in self.config_entry_reserved_keys and atr != "category"):
                    if ("name" in list(rootNode.attributes.keys()) or "key" in list(rootNode.attributes.keys())):
                        entry_key = self.resolve_functor_call(
                            rootNode.attributes["name"].value if (
                                "name" in list(rootNode.attributes.keys())) else rootNode.attributes["key"].value)
                        if (entry_key not in list(res.keys())):
                            res[entry_key] = {}
                        res[entry_key][atr] = self.resolve_functor_call(
                            rootNode.attributes[atr].value)
                        if ((re.search("NodeList",
                                       str(type(rootNode))) or rootNode.nodeType == rootNode.ELEMENT_NODE) and len(
                                rootNode.childNodes) > 0):
                            for childNode in rootNode.childNodes:
                                if (childNode.nodeType == childNode.ELEMENT_NODE):
                                    child_NodeName = childNode.tagName
                                    sub_res = self.traverse_cfg_entries(childNode)
                                    if (child_NodeName not in list(res[entry_key].keys())):
                                        res[entry_key][child_NodeName] = {}
                                    res[entry_key][child_NodeName] = util_merge_dictionaries(
                                        res[entry_key][child_NodeName], sub_res)
                    else:
                        res[atr] = self.resolve_functor_call(rootNode.attributes[atr].value)
                        if ((re.search("NodeList",
                                       str(type(rootNode))) or rootNode.nodeType == rootNode.ELEMENT_NODE) and len(
                                rootNode.childNodes) > 0):
                            for childNode in rootNode.childNodes:
                                if (childNode.nodeType == childNode.ELEMENT_NODE):
                                    child_NodeName = childNode.tagName
                                    if (child_NodeName not in list(res.keys())):
                                        res[child_NodeName] = {}
                                    sub_res = self.traverse_cfg_entries(childNode)
                                    res[child_NodeName] = util_merge_dictionaries(res[child_NodeName], sub_res)
        return res

    # ----------------------------------------------------------------------
    # get number of entries for CFG
    # ----------------------------------------------------------------------

    def get_entries_for_cfg(self, cfg):
        entries_num = 0
        if (cfg.childNodes):
            for node in cfg.childNodes:
                if (node.attributes is not None):
                    entries_num = entries_num + 1
        return entries_num

    # ----------------------------------------------------------------------
    # resolves cfg value by applying env. resolve and then functor resolve
    # ----------------------------------------------------------------------
    def resolve_cfg_value(self, cfg_value, current_category, current_key):
        return self.get_xml_attribute_value(cfg_value, ("<CFG category=\"%s\"\n   <Var key=\"%s\" ...") % (
            current_category, current_key))

    # ----------------------------------------------------------------------
    # Search $<ENV> token in string and rplace it by UNIOC ENV value
    # ----------------------------------------------------------------------

    def resolve_functor_call(self, val, idmsg="", has_functor_constrain=0):
        str_val = val
        functor_found = False
        for func in list(self.te_cfg_functors_l.keys()):
            if (not re.search((r"%s\(([A-z\-0-9 ,_:\.\/'\$]*)\)") % (func), str_val)):
                continue
            functor_found = True
            if (not self.te_cfg_functors_l[func]["loaded"]):
                module_path = ("%s.py") % (self.te_cfg_functors_l[func]["path"]) if (
                    not re.search("\.py$", self.te_cfg_functors_l[func]["path"])) else self.te_cfg_functors_l[func][
                    "path"]
                module_path = util_resolve_unix_env(module_path,
                                                    (("<functor name=\"%s\"> definition in TE_cfg file ") % (func)))
                if (os.path.exists(module_path)):
                    htdte_logger.inform(("Loading functor module - %s ") % (module_path))
                    status, mname, py_mod = util_dynamic_load_external_module(module_path)
                    if (not status):
                        htdte_logger.error(
                            (" Can't load global functor module - %s %s") % (module_path, ("(used in %s)") % (idmsg)))
                    exec((("from %s import *") % (mname)), globals())
                    self.te_cfg_functors_l[func]["loaded"] = 1
                else:
                    htdte_logger.error((" Can't find a functor python module %s") % (module_path))

            # ----------Expected arguments format argname:<val2>,arg2:<val3>... format-----------------------
            all_func_calls_l = re.findall((r"%s\(([A-z\-0-9 ,_:\.\/'\$]*)\)") % (func), str_val)
            for fc in all_func_calls_l:
                arg_str = ""
                if (fc != ""):
                    fc_args_pairs_l = re.split(",", fc.replace(" ", ""))
                    for arg_pair in fc_args_pairs_l:
                        if (not re.search(":", arg_pair)):
                            htdte_logger.error((
                                " Wrong functor module arguments usage - %s(%s) %s, "
                                "expected <argname>:<argvalue>[,<argname2>:<argvalue2>...] "
                                "format") % (
                                ("(used in %s)") % (idmsg), func, fc))
                        (arg_name, arg_value) = re.split(":", arg_pair)
                        arg_str += ("%s\"%s\":\"%s\"") % ("" if arg_str == "" else ",", arg_name, arg_value)
                        # ----------------------
                arg_str = ("{%s}") % (arg_str) if arg_str != "" else arg_str
                call_result = eval(("%s(%s)") % (func, arg_str))
                str_val = str_val.replace(("%s(%s)") % (func, fc), str(call_result))
        # --------------------
        if (not functor_found and has_functor_constrain):
            htdte_logger.error(("Can't match expected functor call in  %s ") % (idmsg))
        return str_val

    # -----------------------------------------------------------------------
    # Parses a given XML file. return xmlDoc object
    # ------------------------------------------------------------------------
    def parse_xml_file(self, xmlPath):
        try:
            xmldoc = minidom.parse(xmlPath)
        except BaseException:
            traceback.print_exc()
            htdte_logger.error(("Malformed XML format found in parsing file:%s...\n\t\t\t\t%s ...\n") % (
                xmlPath, str(sys.exc_info()[1])))
        return xmldoc

    # -----------------------------------------------------------------------
    # Open new TE CFG XML file with predefined XML structure
    # This file define a XML files structures aplicable under current TE CFG
    # ------------------------------------------------------------------------
    def read_te_cfg(self, path_to_cfg):

        # ---------------------
        htdte_logger.inform((" Opening Project dependent TE CFG XML collateral - %s ....") % (path_to_cfg))
        xmldoc = self.parse_xml_file(path_to_cfg)
        self.te_xfg_doc_xml = xmldoc
        self.path_to_tecfg = path_to_cfg
        allowed_attributes = ["name", "path", "filter_exp", "filter_env", "filter_exp", "filter_functor", "type",
                              "comment", "savesrc", "disable_duplicated_xml_nodes_error"]

        htdte_logger.inform("ENV HTD_TE_CFG_ENV_ONLY: %s" % (os.getenv("HTD_TE_CFG_ENV_ONLY", "0")))
        if (os.getenv("HTD_TE_CFG_ENV_ONLY", 0) == "1"):
            htdte_logger.inform("Opening TE CFG ENV sourceme (%s) file for writing" % (self.te_cfg_env_output))
            self.te_cfg_env_f = open(self.te_cfg_env_output, 'w')

        # create the list of XML docs to be used
        xml_docs_l = []
        xml_docs_l.append(xmldoc)
        # Append all <SPLIT> tag xmldocs list
        xml_docs_l.extend(self.get_split_xml_docs(xmldoc))
        self.te_xfg_docs_xml_list = xml_docs_l

        # get the list of imported files, it is important to have this after the envvars in the xml are resolved in
        # handle_te_cfg_xml_env_setup
        # to avoid issues in a L0 regression setup.
        xml_docs_l = self.get_xml_docs_multiple_files(xml_docs_l, path_to_cfg) # Get all the <IMPORT> tags for all xmldoc in xml_docs_l including split xml

        # ---Parsing and save all collaterals definitions
        collaterals_l = self.read_tag_multiple_files(xml_docs_l, HTD_XML_COLLATERAL_TAG_NAME)
        self.handle_te_cfg_xml_collaterals(collaterals_l, allowed_attributes, path_to_cfg)

        # get all dictionaries and populate
        dictionary_l = self.read_tag_multiple_files(xml_docs_l, HTD_XML_DICTIONARY_TAG_NAME)
        self.handle_te_cfg_xml_dictionaries(dictionary_l, path_to_cfg)

        # read free configuration entries - flat node
        self.read_cfg(xml_docs_l, "CFG", path_to_cfg)

        if (os.getenv("HTD_TE_CFG_ENV_ONLY", 0) == "1"):
            htdte_logger.inform("Closing TE CFG ENV sourceme (%s) file" % (self.te_cfg_env_output))
            self.te_cfg_env_f.close()
            return 0

        # ----------------
        if (os.environ.get('HTD_COLLATERALS_SAVED_IMAGE') is None):
            htdte_logger.error(
                'Missing obligatory unix environment ENV[HTD_COLLATERALS_SAVED_IMAGE] - must point to save/restore '
                'binary compiled collaterals content')
        if (not os.path.isdir(os.environ.get('HTD_COLLATERALS_SAVED_IMAGE'))):
            htdte_logger.error(
                ('The given directory (%s) in ENV[HTD_COLLATERALS_SAVED_IMAGE] - is not directory or not exists') % (
                    os.environ.get('HTD_COLLATERALS_SAVED_IMAGE')))
        # ----------------------------------
        self.cfg_command_line_override()

        # Re-import either json or pickle as htd_compress
        self.import_collateral_compressor()

        if ((os.environ.get('HTD_TE_CMD_HELP_MODE') != "1" or os.environ.get(
                'HTD_ENFORCE_COLLATERALS_ACCESS') == "1" or os.environ.get(
                'HTD_TE_COLLATERALS_COMPILE_MODE') == "1") and (os.environ.get('HTD_TE_INFO_UI_HELP') is None)):
            exclude_list = []
            if (os.environ.get('HTD_TE_COLLATERALS_COMPILE_EXCLUDE') is not None):
                exclude_list = os.environ.get('HTD_TE_COLLATERALS_COMPILE_EXCLUDE').split(",")
            self.parse_all_collaterals(exclude_list)

        # ----Open sig file if defined--------------------
        self.handle_signal_file()

    # ------------------------------------------------------------------------------------
    # Writes output to te_cfg_env.sourceme file
    # ------------------------------------------------------------------------------------
    def write_to_te_cfg_env_sourceme(self, env_var, val, conditions=None):
        if (self.te_cfg_env_f is None):
            return 0

        if (env_var == "filter_env" or env_var == "filter_exp"):
            return 0

        # Don't print the value if it is None. Functor calls return with None as a string.
        if (val is None or val == "None" or val == ""):
            return 0

        if (conditions is None):
            conditions = []

        indent = 0
        spacer = "  "
        for condition in conditions:
            spaces = spacer * indent
            self.te_cfg_env_f.write(spaces + "if %s then\n" % (condition))
            indent = indent + 1

        spaces = spacer * indent
        self.te_cfg_env_f.write(spaces + "echo setenv %s \"%s\"\n" % (env_var, val))
        self.te_cfg_env_f.write(spaces + "setenv %s \"%s\"\n" % (env_var, val))
        htdte_logger.inform("Writing env_var %s with value %s" % (env_var, val))

        for i in range(len(conditions)):
            indent = indent - 1
            spaces = spacer * indent
            self.te_cfg_env_f.write(spaces + "endif\n")

    # ------------------------------------------------------------------------------------
    # handles the functors retrieved from XML files
    # ------------------------------------------------------------------------------------
    def handle_te_cfg_xml_functors(self, func_cfg_l, allowed_attributes, path_to_cfg):
        for f in func_cfg_l:
            illegal_attributes = self.get_illegal_attributes(f, allowed_attributes)
            if (len(illegal_attributes) > 0):
                htdte_logger.error((
                    "Illegal (not supported attribute/s (%s) found in <functor .../> definition , "
                    "TE_cfg file -\"%s\"...") % (
                    str(illegal_attributes), path_to_cfg))
            if ("name" not in list(f.attributes.keys())):
                htdte_logger.error(
                    ("Missing \"name\" attribute in <functor .../> definition , TE_cfg file -\"%s\"...") % (
                        path_to_cfg))
            if ("path" not in list(f.attributes.keys())):
                htdte_logger.error(
                    ("Missing \"path\" attribute in <functor name=\"%s\" .../> definition , TE_cfg file -\"%s\"...") % (
                        path_to_cfg, f.attributes["name"].value))
            if (f.attributes["name"].value in list(self.te_cfg_functors_l.keys()) and \
                self.te_cfg_functors_l[f.attributes["name"].value]["path"] != f.attributes["path"].value):
                htdte_logger.error(
                    ("Duplicated functor definition <functor name=\"%s\" .../> found in  TE_cfg file -\"%s\"...") % (
                        path_to_cfg, f.attributes["name"].value))

            self.te_cfg_functors_l[f.attributes["name"].value] = {}
            self.te_cfg_functors_l[f.attributes["name"].value]["path"] = f.attributes["path"].value
            self.te_cfg_functors_l[f.attributes["name"].value]["loaded"] = 0

    # ------------------------------------------------------------------------------------
    # handles the environment setup retrieved from XML files
    # ------------------------------------------------------------------------------------
    def handle_te_cfg_xml_env_setup(self, env_setup_l, path_to_cfg):
        overriten_by_cmd_list = [] if os.environ.get('HTD_CMD_OVERRITEN_ENV_LIST') is None else [x for x in os.environ.get('HTD_CMD_OVERRITEN_ENV_LIST').split(",")]

        for envset in env_setup_l:
            no_sourceme = 0
            if ("no_sourceme" in list(envset.attributes.keys())):
                no_sourceme = envset.attributes["no_sourceme"].value
                envset.removeAttribute("no_sourceme")

            for env in list(envset.attributes.keys()):
                if (env not in overriten_by_cmd_list):
                    # evaluate filters ------
                    if (not self.evaluate_filter(envset, ("<setenv \"%s\">") % (envset.attributes[env].value))):
                        continue

                    # ------------------------
                    env_val = util_resolve_unix_env(envset.attributes[env].value, (
                        ("<setenv %s=\"%s\"> definition in TE_cfg file - %s") % (
                            env, envset.attributes[env], path_to_cfg)))
                    env_val = self.resolve_functor_call(env_val, (
                        ("<setenv %s=\"%s\"> definition in TE_cfg file - %s") % (
                            env, envset.attributes[env], path_to_cfg)))
                    os.putenv(env, env_val)
                    os.environ[env] = env_val
                if no_sourceme != "1":
                    self.write_to_te_cfg_env_sourceme(env, os.environ.get(env))
                htdte_logger.inform(("TE_CFG: SETTING ENV[%s]=%s") % (env, os.environ.get(env)))
                htdte_logger.add_header(("TE_CFG: SETTING ENV[%s]=%s") % (env, os.environ.get(env)))

    # ------------------------------------------------------------------------------------
    # handles the environment setup retrieved from XML files
    # ------------------------------------------------------------------------------------
    def handle_te_cfg_xml_collaterals(self, collaterals_l, allowed_attributes, path_to_cfg):
        for collateral in collaterals_l:

            illegal_attributes = self.get_illegal_attributes(collateral, allowed_attributes)
            if (len(illegal_attributes) > 0):
                htdte_logger.error(
                    ("Illegal (not supported attribute/s (%s) found in <COLLATERAL>, TE_cfg file -\"%s\"...") % (
                        str(illegal_attributes), path_to_cfg))
            if ("name" not in list(collateral.attributes.keys())):
                htdte_logger.error(
                    ("Wrong <COLLATERAL> definition in TE_cfg file -\"%s\": Missing \"name\" atribute...(") % (
                        path_to_cfg))
            if ("path" not in list(collateral.attributes.keys())):
                htdte_logger.error((
                    "Wrong <COLLATERAL> definition in TE_cfg file -\"%s\": Missing "
                    "\"path\"=<path_to_xmlfile> atribute  ....") % (
                    path_to_cfg))
            # ----
            if (not self.evaluate_filter(collateral, ("<COLLATERAL name=\"%s\">") % (
                    collateral.attributes["name"].value))):
                continue
            # ----------
            coll_name = collateral.attributes["name"].value
            self.collaterals_list[coll_name] = {}
            final_path = self.get_xml_attribute_value(collateral.attributes["path"].value,
                                                      (
                                                      "<COLLATERAL name=\"%s\" path=\"%s\"> definition in TE_cfg file "
                                                      "- %s>") % (
                                                      coll_name,
                                                      collateral.attributes["path"].value,
                                                      path_to_cfg))
            self.collaterals_list[coll_name]["path"] = final_path

            # ---Extract a type of collateral
            if ("type" in list(collateral.attributes.keys())):
                self.collaterals_list[coll_name]["type"] = collateral.attributes["type"].value
            else:
                fileName, fileExtension = os.path.splitext(final_path)
                if (fileExtension == ".xml"):
                    self.collaterals_list[coll_name]["type"] = "xml"
                else:
                    htdte_logger.error((
                        "Wrong <COLLATERAL name=\"%s\" path=\"%s\"> definition in TE_cfg file - "
                        "%s: Missing collateral format type=\"<xml|tab>\"...") % (
                        coll_name, collateral.attributes["path"].value,
                        path_to_cfg))
            # ----------------------
            if ("comment" in list(collateral.attributes.keys())):
                self.collaterals_list[coll_name]["comment"] = collateral.attributes["comment"].value
            if ("savesrc" in list(collateral.attributes.keys())):
                htdte_logger.inform((" Saving origin collateral source -%s:%s to dir:%s ....") % (
                    coll_name, self.collaterals_list[coll_name]["path"], os.environ.get('HTD_COLLATERALS_SAVED_IMAGE')))
                cmd = ("/usr/intel/bin/gcp -a %s %s" % (
                    self.collaterals_list[coll_name]["path"], os.environ.get('HTD_COLLATERALS_SAVED_IMAGE')))
                status = subprocess.call(cmd, shell=True)
                if (status):
                    htdte_logger.error(("Fail to copy source collateral file: %s") % cmd)
            if ("disable_duplicated_xml_nodes_error" in list(collateral.attributes.keys()) and collateral.attributes[
                    "disable_duplicated_xml_nodes_error"].value in ["1", "True", "TRUE"]):
                htdte_logger.inform((" Disable duplicated XML nodes error found in collateral -%s:%s  ....") % (
                    coll_name, self.collaterals_list[coll_name]["path"]))
                self.collaterals_list[coll_name]["disable_duplicated_xml_nodes_error"] = 1
            # ------------------------------
            for attr in list(collateral.attributes.keys()):
                if (attr not in allowed_attributes):
                    htdte_logger.error((
                        "Illegal attribute - \"%s\" found in <COLLATERAL name=\"%s\" .../> "
                        "definition , TE_cfg file -\"%s\"...") % (
                        attr, coll_name, path_to_cfg))

    # ------------------------------------------------------------------------------------
    # handles the environment setup retrieved from XML files
    # ------------------------------------------------------------------------------------
    def handle_te_cfg_xml_dictionaries(self, dictionary_l, path_to_cfg):
        for dictionary in dictionary_l:
            dict_collaterals = []
            if ("name" not in list(dictionary.attributes.keys())):
                htdte_logger.error(
                    ("Wrong <dictionary> definition in TE_cfg file -\"%s\": Missing \"name\" atribute...(") % (
                        path_to_cfg))
            dict_name = dictionary.attributes["name"].value
            # ---Filter evaluation
            if (not self.evaluate_filter(dictionary, ("<dictionary name=\"%s\">") % (dict_name))):
                continue
            # --Parsing collaterals reference
            colls = dictionary.getElementsByTagName("collateral")

            for coll in colls:
                if ("name" not in list(coll.attributes.keys())):
                    htdte_logger.error((
                        "Wrong <dictionary name=\"%s\"> <collateral../> <dictionary/> definition "
                        "in TE_cfg file -\"%s\": Missing <collateral name=\"reference to "
                        "collateral name previously defined in xml\"> atribute  ....") % (
                        dict_name, path_to_cfg))
                curr_coll = coll.attributes["name"].value
                # --Filter apply
                if (not self.evaluate_filter(coll, ("<collateral name=\"%s\">") % (curr_coll))):
                    continue
                    # -------------------------------
                if (curr_coll not in self.collaterals_list):
                    htdte_logger.error((
                        "Wrong <dictionary name=\"%s\"> <collateral name=\"%s\" > definition in "
                        "TE_cfg file -\"%s\": Referenced collateral name - \"%s\" should be "
                        "defined previously by <COLLATERAL> xml node  ....") % (
                        dict_name, curr_coll, path_to_cfg, curr_coll))
                if (len(dict_collaterals)
                        and self.collaterals_list[dict_collaterals[len(dict_collaterals) - 1]]["type"]
                        != self.collaterals_list[curr_coll]["type"]):
                    htdte_logger.error((
                        "Wrong <dictionary name=\"%s\"> <collateral name=\"%s\" > definition in "
                        "TE_cfg file -\"%s\": Mixing different collateral types (%s and %s) in "
                        "same dictionary  ....") % (
                        dict_name,
                        coll.attributes["name"].value, path_to_cfg,
                        self.collaterals_list[dict_collaterals[len(dict_collaterals) - 1]]["type"],
                        self.collaterals_list[curr_coll]["type"]))

                dict_collaterals.append(curr_coll)

            # --Collateral reference in dictionary attribute----------------
            if ("collateral" not in list(dictionary.attributes.keys()) and len(dict_collaterals) == 0):
                htdte_logger.error((
                    "Wrong <dictionary name=\"%s\"> definition in TE_cfg file -\"%s\": Missing "
                    "\"collateral\" reference in atribute or as a list of nodes in current "
                    "dictionary  ....") % (
                    dict_name, path_to_cfg))
            if ("collateral" in list(dictionary.attributes.keys())):
                curr_coll = dictionary.attributes["collateral"].value
                if (curr_coll not in self.collaterals_list):
                    htdte_logger.error((
                        "Wrong <dictionary collateral=\"%s\" > definition in TE_cfg file -\"%s\": "
                        "Referenced collateral name - \"%s\" should be defined previously by "
                        "<COLLATERAL> xml node  ....") % (
                        dict_name, path_to_cfg, curr_coll))

                if (len(dict_collaterals)
                        and self.collaterals_list[dict_collaterals[len(dict_collaterals) - 1]]["type"]
                        != self.collaterals_list[curr_coll]["type"]):
                    htdte_logger.error((
                        "Wrong <dictionary name=\"%s\"> <collateral name=\"%s\" > definition in "
                        "TE_cfg file -\"%s\": Mixing different collateral types (%s and %s) in "
                        "same dictionary  ....") % (
                        dict_name,
                        coll.attributes["name"].value, path_to_cfg,
                        self.collaterals_list[dict_collaterals[len(dict_collaterals) - 1]]["type"],
                        self.collaterals_list[curr_coll]["type"]))
                dict_collaterals.append(curr_coll)

            # -----------------------------
            new_dic_entry = {}
            new_dic_entry["collateral"] = dict_collaterals
            # --------------------------
            for dict_property in list(dictionary.attributes.keys()):
                if (dict_property != "collateral"):
                    new_dic_entry[dict_property] = self.get_xml_attribute_value(
                        dictionary.attributes[dict_property].value)
            # ----------------------------
            entries = dictionary.getElementsByTagName("entry")
            if (len(entries) < 1):
                htdte_logger.error((
                    "Wrong <dictionary name=\"%s\"> definition in TE_cfg file -\"%s\": Missing "
                    "<entry ..../> - dictionary definition subtree") % (
                    dict_name, path_to_cfg))
            new_dic_entry["entries"] = []
            for entry in entries:
                if ("key" not in list(entry.attributes.keys())):
                    htdte_logger.error((
                        "Wrong <dictionary name=\"%s\"> definition in TE_cfg file -\"%s\": Missing "
                        "\"key\"=<result dictionary key pointer mapped to parsed XML tree> "
                        "atribute  ....") % (
                        dict_name, path_to_cfg))
                res = {}
                self.traverse_cfg_xml_node(entry, res, dict_name, path_to_cfg,
                                           self.collaterals_list[dict_collaterals[len(dict_collaterals) - 1]]["type"])
                new_dic_entry["entries"].append(res)
            # -----------
            functions_l = dictionary.getElementsByTagName("func")

            for f in functions_l:
                if ("func" not in list(new_dic_entry.keys())):
                    new_dic_entry["func"] = []
                new_func_entry = {}
                func_attributes = ["func", "path", "module", "method"]
                for attr in list(f.attributes.keys()):
                    if (attr not in func_attributes):
                        htdte_logger.error((
                            "Wrong func definition attribute name (%s) in : <dictionary "
                            "name=\"%s\"> <func ...%s=\"%s\"> </dictionary>.Supported attributes "
                            "are : %s  ....") % (
                            attr, dict_name, attr, f.attributes[attr], str(func_attributes)))
                for attr in func_attributes:
                    if (attr not in list(f.attributes.keys())):
                        htdte_logger.error((
                            "Missing func  attribute name (%s) in : <dictionary name=\"%s\"> <func "
                            "...%s=\"%s\"> </dictionary>.Supported attributes are : %s  ....") % (
                            attr, dict_name, attr, f.attributes[attr], str(func_attributes)))
                    attr_value = f.attributes[attr].value.replace(" ", "")
                    new_func_entry[attr] = util_resolve_unix_env(attr_value)
                new_dic_entry["func"].append(new_func_entry)
            # -----------
            if (dict_name not in list(self.te_cfg_col.keys())):
                self.te_cfg_col[dict_name] = []
                self.te_cfg_col_order.append(dict_name)
            self.te_cfg_col[dict_name].append(new_dic_entry)

    # ------------------------------------------------------------------------------------
    # Handles signal file parsing
    # ------------------------------------------------------------------------------------
    def handle_signal_file(self):
        signal_files_list = []

        if (os.environ.get('HTD_SIGNALS_MAP') is not None):
            if (os.environ.get('SBFT_SIGNALS_MAP') is not None):
                signal_files_list = [os.environ.get('HTD_SIGNALS_MAP'), os.environ.get('SBFT_SIGNALS_MAP')]
            else:
                signal_files_list = [os.environ.get('HTD_SIGNALS_MAP')]
        elif (os.environ.get('SBFT_SIGNALS_MAP') is not None):
            signal_files_list = [os.environ.get('SBFT_SIGNALS_MAP')]

        for signal_file in signal_files_list:
            fptr = open(signal_file, 'rb')
            line_num = 0
            line = fptr.readline()
            while line:
                line = line.decode("ascii", "ignore")
                line_num = line_num + 1
                line = re.sub("#.+", "", line)
                line = re.sub(r"\/\/.+", "", line)
                line = re.sub(" +$", "", line)
                line = re.sub("\t", "", line)
                if (re.match("^ *$", line)):
                    line = fptr.readline()
                    continue
                tabbed_entries = re.split(" +", line)
                if ('FlowSignals' not in list(self.CFG.keys())):
                    self.CFG['FlowSignals'] = {}
                if (len(tabbed_entries) >= 2):
                    if tabbed_entries[0] not in list(self.CFG['FlowSignals'].keys()):
                        self.CFG['FlowSignals'][tabbed_entries[0]] = tabbed_entries[1].replace("\n", "").strip()
                else:
                    htdte_logger.error((
                        "Unexpected format found at %s:%d: Expected tabular format "
                        "<SignalNickName> <relative rtl path> ") % (
                        signal_file, line_num))
                line = fptr.readline()
            fptr.close()

    # ------------------------------------------------------------------------------------
    # Checks the if illegal attributes appear in the list of attributes
    # ------------------------------------------------------------------------------------
    def get_illegal_attributes(self, xmlNode, allowed_attributes):
        illegal_attributes = [x for x in list(xmlNode.attributes.keys()) if
                              (x not in allowed_attributes)]
        return illegal_attributes

    # ------------------------------------------------------------------------------------
    # gets the list of available xml_docs - both main XML and import XMLs
    # ------------------------------------------------------------------------------------
    def get_xml_docs(self, xmldoc_top, path_to_cfg):
        xml_docs_l = []
        xml_docs_l.append(xmldoc_top)

        for xmldoc in xml_docs_l:
            # Straighten out env vars and functors first
            # get all functors and populate
            func_cfg_l = self.read_tag(xmldoc, HTD_XML_FUNCTOR_TAG_NAME)
            self.handle_te_cfg_xml_functors(func_cfg_l, ["name", "path"], path_to_cfg)

            # parse all setenv nodes and populate
            set_env_l = self.read_tag(xmldoc, HTD_XML_SETENV_TAG_NAME)
            self.handle_te_cfg_xml_env_setup(set_env_l, path_to_cfg)

            # get the list of imported files
            imports_l = self.read_tag(xmldoc, HTD_XML_IMPORT_TAG_NAME)

            # parse XML docs to ensure all imports are ok
            for i in imports_l:
                xmldoc = None
                if 'optional' in list(i.attributes.keys()):
                    if i.attributes["optional"].value == "1":
                        if i.attributes["file"].value.replace("$", "") in os.environ:
                            htdte_logger.inform(("Found optional CFG IMPORT: %s with existing location: %s") %
                                                (i, i.attributes["file"].value))
                            xmldoc = minidom.parse(util_resolve_unix_env(i.attributes["file"].value))
                    else:
                        xmldoc = minidom.parse(util_resolve_unix_env(i.attributes["file"].value))
                else:
                    import_name = util_resolve_unix_env(i.attributes["file"].value)
                    xmldoc = minidom.parse(import_name)

                if xmldoc is not None:
                    htdte_logger.inform("Loading CFG IMPORT via xml append for: %s" % i)
                    xml_docs_l.append(xmldoc)
                else:
                    htdte_logger.inform("Not Loading CFG IMPORT via xml append for %s" % i)

        return xml_docs_l

    # ------------------------------------------------------------------------------------
    # gets the list of available xml_docs - both main XML (+ SPLIT XMLs) and import XMLs in xml_docs_l
    # ------------------------------------------------------------------------------------
    def get_xml_docs_multiple_files(self, xml_docs_l, path_to_cfg):
        xml_docs_list = []

        for xmldoc in xml_docs_l:
            xml_docs_list.extend(self.get_xml_docs(xmldoc,path_to_cfg))

        return xml_docs_list

    # ------------------------------------------------------------------------------------
    # gets the list of splitted xml_docs - both main XML and SPLIT XMLs
    # ------------------------------------------------------------------------------------
    def get_split_xml_docs(self, xmldocMain):
        xml_docs_split_l = []

        # get the list of imported files
        splits_l = self.read_tag(xmldocMain, HTD_XML_SPLIT_TAG_NAME)

        # parse XML docs to ensure all splitted xml are appended
        import_name = ""
        for i in splits_l:
            xmldoc = None
            import_name = util_resolve_unix_env(i.attributes["file"].value)
            xmldoc = minidom.parse(import_name)

            if xmldoc is not None:
                htdte_logger.inform("Loading CFG <SPLIT> via xml append for: %s" % import_name)
                xml_docs_split_l.append(xmldoc)
            else:
                htdte_logger.error("Failed to load CFG <SPLIT> via xml append for: %s" % import_name)

        return xml_docs_split_l

    # ------------------------------------------------------------------------------------
    # reads a specific tag from xml doc. return the list of applicable nodes
    # ------------------------------------------------------------------------------------
    def read_tag(self, xmldoc, tagName):
        tags_l = xmldoc.getElementsByTagName(tagName)
        return tags_l

    # ------------------------------------------------------------------------------------
    # generates a list of applicable tags from multiple files
    # ------------------------------------------------------------------------------------
    def read_tag_multiple_files(self, xml_docs_l, tagName):
        tag_list = []
        for single_xml_doc in xml_docs_l:
            tag_list_single_file = self.read_tag(single_xml_doc, tagName)
            tag_list.extend(tag_list_single_file)
        return tag_list

    # -------------------------------------------------------------------------------------
    # read combined XML value in format xmlnode1/xmlnode2/.../xmlnodeN[.attrNode][=value]
    # -------------------------------------------------------------------------------------
    def read_combined_xml_cfg_value(self, value):
        xml_val = "none"
        xml_node = []
        xml_node_hierarchy = value.replace(" ", "")
        xml_append_l = xml_node_hierarchy.split("+", xml_node_hierarchy.count("+"))
        chars = []
        if (len(xml_append_l) > 1):
            xml_node = []
            for append_node in xml_append_l:
                if (append_node[0] != "'" and append_node[len(append_node) - 1] != "'"):
                    xml_app_node = append_node.split("/", append_node.count("/"))
                    if (xml_app_node[len(xml_app_node) - 1] == ""):
                        xml_app_node.pop(len(xml_node) - 1)
                    xml_node.append(xml_app_node)
                else:
                    xml_node.append(append_node)
            # ----------------
            chars = set(xml_node[len(xml_node) - 1][len(xml_node[len(xml_node) - 1]) - 1])
            #if ("=" in chars and "(" not in chars):  # EitanPinhas for ADL: added "(" check as it split the filter we added
            if ("=" in chars):
                xml_node[len(xml_node) - 1][len(xml_node[len(xml_node) - 1]) - 1], xml_val = \
                    xml_node[len(xml_node) - 1][len(xml_node[len(xml_node) - 1]) - 1].split("=", 1)
            return xml_node, xml_val
        else:
            xml_node = xml_node_hierarchy.split("/", xml_node_hierarchy.count("/"))
            if (xml_node[len(xml_node) - 1] == ""):
                xml_node.pop(len(xml_node) - 1)
            chars = set(xml_node[len(xml_node) - 1])
            if ("=" in chars and "(" not in chars): #ticket_28847
                xml_node[len(xml_node) - 1], xml_val = xml_node[len(xml_node) - 1].split("=", 1)
            return xml_node, xml_val

    # -----------------------------------------------------
    # Traverse the nodes path in XML tree starting from rootNode
    #  Return Node or NodeList
    # -------------------------------------------------------
    def traverse_nodes_by_path(self, rootNode, path_l, depth, strict_path=1, conditional_existence=0):
        res = []
        if (depth >= len(path_l)):
            htdte_logger.error((" traverse_node_path() depth-%d exceed path array size - %d (%s)....") % (
                depth, len(path_l), str(path_l)))
        # -------------
        curr_node = rootNode
        if (depth < len(path_l) - 1 and len(path_l) > 0):
            for i in range(depth, len(path_l) - 1):
                if (path_l[i] == ".."):
                    if (re.match("<class\s+'xml.dom.minicompat.NodeList'>", str(type(curr_node))) or re.match(
                            "<class 'list'>", str(type(curr_node)))):
                        nextNode = curr_node[0].parentNode
                    else:
                        nextNode = curr_node.parentNode
                    curr_node = nextNode
                else:
                    if (curr_node.nodeName == path_l[i]):
                        curr_node = curr_node  # ???Check if legal - matching current rootNode
                    else:
                        if (strict_path):
                            for next_node in self.findChildNodesByName(curr_node, path_l[i]):
                                res.extend(self.traverse_nodes_by_path(next_node, path_l, i + 1, strict_path,
                                                                       conditional_existence))
                            return res
                        else:
                            nextNodeLevel = curr_node.getElementsByTagName(path_l[i])
                            if (len(nextNodeLevel) < 1):
                                htdte_logger.error(
                                    (" traverse_node_path() No element -\"%s\" found from node -\"%s\"....") % (
                                        path_l[i], curr_node.nodeName))
                            for node in nextNodeLevel:
                                res.extend(self.traverse_nodes_by_path(node, path_l, i + 1, strict_path,
                                                                       conditional_existence))
                            return res
        # ----------------
        return self.destination_xml_node_processing(path_l[len(path_l) - 1], curr_node, strict_path,
                                                    conditional_existence)

    # -----------------------------------------
    # Final XML path node Processing
    #  destination_xml_node_processing(path_l[depth]
    # ----------------------------------------

    def destination_xml_node_processing(self, node_str, rootNode, strict_path, conditional_existence):
        # else:
        res = []
        # ----Final node
        # ---Node could be represented by <Node:Attribute>
        node_cmb_str = node_str.split(".")
        if (len(node_cmb_str) > 2):
            htdte_logger.error((
                " traverse_node_path() More then one attribute reference found in node string "
                "\"%s\" - expected format <nodePath>.<attributeName>....") % (
                node_str))
        if (len(node_cmb_str) > 1):
            node_str = node_cmb_str[0]
        if (rootNode.nodeName == node_str or node_str == ""):
            if (strict_path):
                return [rootNode]
        # -----------
        if (strict_path):
            return self.findChildNodesByName(rootNode, node_str, 0 if conditional_existence > 0 else 1)
        else:
            res.extend(rootNode.getElementsByTagName(node_str))
            return res

    # -----------------------------------------------------
    # Traverse the single node path in XML tree starting from rootNode
    #  Return Node or NodeList, if multiple nodes are matched , returned error
    # -------------------------------------------------------
    def traverse_single_node_by_path(self, rootNode, path_l, conditional_existence=0):
        # Eitan Pinhas for ADL
        # example: reset="?RESET(type=reset)">
        match_filters = [re.search(r"([A-z0-9]+)\(([A-z0-9\.=']+)\)", x) for x in path_l]  # [None,obbj,None,None]
        match_filters = [x for x in match_filters if(x)]
        nodes = []
        if(len(match_filters) == 0):
            nodes = self.traverse_nodes_by_path(rootNode, path_l, 0, 1, conditional_existence)
        else:
            new_path_l = [x.groups()[0] for x in match_filters]
            if(len(new_path_l) > 1):
                htdte_logger.error("Unsupported multiple matching value filtering.")
            nodes_t = self.traverse_nodes_by_path(rootNode, new_path_l, 0, 1, conditional_existence)
            filter_val_exp = match_filters[0].groups()[1]  # type='reset'
            if(len(filter_val_exp.split("=")) == 0):
                htdte_logger.error("Wrong value filter expression format: Expected <attribute_name>='expected_value',\
                                       Found: %s" % filter_val_exp)
            (filter_val_attr_name, filter_val_attr_val) = filter_val_exp.split("=")
            for n in nodes_t:
                if(filter_val_attr_name in list(n.attributes.keys())
                        and n.attributes[filter_val_attr_name].value == filter_val_attr_val):
                    nodes = [n]
                    break
        # -------------------
        if (isinstance(nodes, list) and len(nodes) > 1):
            if (not self.disable_duplicated_xml_node_error):
                htdte_logger.error(
                    (" traverse_single_node_by_path() matching multiple nodes (root node- \"%s\" path-\"%s\")....") % (
                        rootNode.nodeName, str(path_l)))
        if (((isinstance(nodes, list) and len(nodes) < 1) or nodes is None)):
            if (conditional_existence):
                return None
            else:
                htdte_logger.error(
                    (" traverse_single_node_by_path() doesn't match any node (root node- \"%s\" path-\"%s\")....") % (
                        rootNode.nodeName, str(path_l)))
        return nodes[0] if isinstance(nodes, list) else nodes

    # -------------------------------------------------
    # Read Collateral XML node value by combined path
    # ------------------------------------------------
    def get_xml_value_by_combined_path(self, rootNode, path_l, conditional_existence=0):
        if (len(path_l) == 0):
            return "none"
        if (re.match(r"<class\s+'list'>", str(type(path_l[0])))):
            # ---The path_l has a list of nodes to be appended---
            ret_val_str = ""
            ret_val_int = 0
            for app_node in path_l:
                if (app_node[0] == "'" and app_node[len(app_node) - 1] == "'"):
                    val = app_node[1:len(app_node) - 2]
                else:
                    val = self.get_xml_value_by_combined_path(rootNode, app_node, conditional_existence)
                if (re.match(r"<class\s+'str'>", str(type(val)))):
                    ret_val_str = ("%s%s") % (ret_val_str, val)
                else:
                    ret_val_int = ret_val_int + val
            # ----------------
            if (ret_val_str != ""):
                return ret_val_str
            else:
                return ret_val_int
        else:
            node = self.traverse_single_node_by_path(rootNode, path_l, conditional_existence)
            if ((node is None or node == [None]) and conditional_existence):
                return "none"
            if (re.match(r"<class\s+'xml.dom.minicompat.NodeList'>", str(type(node)))):
                htdte_logger.error((
                    " Trying to extract text node from NodeList node type,root Node - %s,"
                    "path- %s te_cfg_col[\"%s\"][\"%s\"]  ....") % (
                    rootNode, str(path_l), col_tag, col_type))
            node_attr_l = str(path_l[len(path_l) - 1]).split(".")
            if (len(node_attr_l) > 2):
                htdte_logger.error((
                    " get_xml_value_by_combined_path() More then one attribute reference found in "
                    "node "
                    "string \"%s\" - expected format ....") % (
                    str(path_l)))
            # ----------------------------
            if (len(node_attr_l) > 1):
                node_str = node_attr_l[0]
                attr_str = node_attr_l[1]
                if (conditional_existence and attr_str not in list(node.attributes.keys())):
                    return "none"
                else:
                    return self.get_xml_attribute_value(node.attributes[attr_str].value)

            else:
                if ((not conditional_existence) or node is not None):
                    if (node is None):
                        htdte_logger.error((" Can't resolve a path - %s,from root node - %s : \n%s ....") % (
                            str(path_l), rootNode.nodeName, self.get_xml_tree_str(rootNode)))
                    for chnode in node.childNodes:
                        if (chnode.nodeType == chnode.TEXT_NODE):
                            return self.get_xml_attribute_value(chnode.data)
                else:
                    return "none"
                #       htdte_logger.error( (" The node \"%s\" is not of TEXT_TYPE and could not be used to get a
                # value....")%(node.nodeName.encode('ascii','ignore')))

    # -------------------------------------------------------------
    # Verify single node structure
    # -------------------------------------------------------------
    def is_single_node_hierarchy(self, rootNode, path_l, conditional_existence=0):
        if (len(path_l) == 0):
            return 1
        nodes = self.traverse_nodes_by_path(rootNode, path_l, 0, 1, conditional_existence)
        if (isinstance(nodes, list) and len(nodes) > 1):
            return 0
        else:
            return 1

    # ------------------------------------------------------------
    # Retrieve a list of nodes used in dictionary as a reference
    # ------------------------------------------------------------
    def browse_dict_nodes(self, entity, result):
        for entry_key in list(entity.keys()):
            if (not isinstance(entity[entry_key], dict)):
                result.append(entity[entry_key])
            else:
                self.browse_dict_nodes(entity[entry_key], result)
        return

    # ------------------------------------------------------------------------------------------------------
    #
    # ------------------------------------------------------------------------------------------------------
    def get_all_used_xml_node_names(self, dict_entry):
        all_entries = []
        result = []
        for ent in dict_entry:
            self.browse_dict_nodes(ent, all_entries)
        # ---Cleanup "?" and "../" , splitting up xml hierarchy : "<lt>hier>/hier2>/hier3>....."----
        all_entries = [x.replace("../", "") for x in all_entries]
        all_entries = [x.replace("?", "") for x in all_entries]
        for ent in all_entries:
            _l = ent.split("/")
            result.extend(_l)
        # --Remove duplications----
        result = list(set(result))
        result = [x for x in result if len(x) > 0]
        return result

    # ----------------------------------------------------------------------------------------
    # Conditional adding string value to dictionary depend on type of node:list or  just value
    #  separating between int value and string upon insertion
    # ----------------------------------------------------------------------------------------
    def add_normilized_string_value_to_dictionary(self, res, str_value, islist=0):
        # ----------------------------------------
        isInt, val = util_get_int_value(str_value)
        # ----------------------------------------
        if (islist):
            if (not isinstance(res, list)):
                # if the entry already exists and not a list , create a list and inserting it back
                tmp = res
                res = []
                res.append(tmp)
            if (isInt):
                if (val not in res):
                    res.append(val)
            else:
                if (str_value not in res):
                    res.append(str_value)
        else:
            if (isInt):
                res = val
            else:
                res = str_value
        return res

    # ----------------------------------------------------------------------------------------
    # Apply current dictionary on current tab collateral and create dynamically the dictiory-hash
    # ----------------------------------------------------------------------------------------
    def apply_current_dictionary_on_current_user_collateral(self, dict_name, dictionary, matched_entries, coll_name,
                                                            line_num, res):
        if (isinstance(dictionary["key"], int) or (
                type(dictionary["key"]) in [str, str] and re.search("^\d+$", dictionary["key"]))):
            keyIndex = int(dictionary["key"])
            if (keyIndex >= len(matched_entries)):
                htdte_logger.error((
                    " The  key index (%d) in \"user text\" in dictionary  \"%s\" exceed the "
                    "matched number of elements -%d  at collateral:%s:line:%d ") % (
                    int(dictionary["key"]), dict_name, len(matched_entries), coll_name, line_num))
            keyValue = matched_entries[int(dictionary["key"])]
        else:
            keyValue = dictionary["key"]
        # ----------------------------
        for entry in list(dictionary.keys()):
            if (entry not in self.dictionary_entry_reserved_keys):
                if (isinstance(dictionary[entry], dict)):
                    if ("key" not in list(dictionary[entry].keys())):
                        htdte_logger.error((
                            " The dictionary  \"%s\" has not assigned key-attribute at sub level "
                            "definition - \"%s\"....") % (
                            dict_name, entry))
                    if (keyValue not in list(res.keys())):
                        res[keyValue] = {}
                    if (entry not in list(res[keyValue].keys())):
                        res[keyValue][entry] = {}
                    self.apply_current_dictionary_on_current_user_collateral(dict_name, dictionary[entry],
                                                                             matched_entries, coll_name, line_num,
                                                                             res[keyValue][entry])
                else:
                    islist = ("islist" in list(dictionary.keys())) and (dictionary["islist"] in HTD_True_Statement)
                    key_value_format = ("key_value_format" in list(dictionary.keys())) and (
                        dictionary["key_value_format"] in HTD_True_Statement)
                    if (key_value_format and (
                            len([x for x in list(dictionary.keys()) if (x not in self.dictionary_entry_reserved_keys)]) > 1)):
                        htdte_logger.error((
                            " The dictionary  \"%s\" has multiple attributes while the simgle "
                            "mapping \"key_value_format\" is selected   ....") % (
                            dict_name))
                    final_value = ""
                    if (isinstance(dictionary[entry], int) or (
                            type(dictionary[entry]) in [str, str] and re.search("^\d+$", dictionary[entry]))):
                        entryIndex = int(dictionary[entry])
                        if (entryIndex >= len(matched_entries)):
                            htdte_logger.error((
                                " The  %s index (%d) in \"user text\" in dictionary  \"%s\" exceed "
                                "the matched number of elements -%d at collateral:%s:line:%d ") % (
                                entry, entryIndex, dict_name, len(matched_entries), coll_name,
                                line_num))
                        final_value = matched_entries[entryIndex]
                    elif (isinstance(dictionary[entry], int) or (
                            type(dictionary[entry]) in [str, str] and re.search("%(\d+)", dictionary[entry]))):
                        final_value = dictionary[entry]
                        m = re.search(r"%(\d+)", final_value)
                        while (m):
                            entryIndex = int(m.groups()[0])
                            if (entryIndex >= len(matched_entries)):
                                htdte_logger.error((
                                    " The  %s index (%d) in \"user text\" in dictionary  \"%s\" "
                                    "exceed the matched number of elements -%d at "
                                    "collateral:%s:line:%d ") % (
                                    entry, entryIndex, dict_name, len(matched_entries), coll_name,
                                    line_num))
                            final_value = final_value.replace(("%s%d") % ("%", entryIndex), matched_entries[entryIndex])
                            m = re.search(r"%(\d+)", final_value)
                    else:
                        final_value = dictionary[entry]
                    # ------------------
                    res_ptr = None
                    # if(keyValue not in res.keys()):
                    if (key_value_format):
                        if (keyValue not in list(res.keys())):
                            if (islist):
                                res[keyValue] = []
                            else:
                                res[keyValue] = -1
                        res[keyValue] = self.add_normilized_string_value_to_dictionary(res[keyValue], final_value,
                                                                                       islist)
                    else:
                        if (keyValue not in list(res.keys())):
                            res[keyValue] = {}
                        if (islist):
                            res[keyValue][entry] = []
                        if (entry not in list(res[keyValue].keys())):
                            res[keyValue][entry] = ""
                        res[keyValue][entry] = self.add_normilized_string_value_to_dictionary(res[keyValue][entry],
                                                                                              final_value, islist)
                        # -----------------

    # ----------------------------------------------------------------------------------------
    # Apply current dictionary on current tab collateral and create dynamically the dictiory-hash
    # ----------------------------------------------------------------------------------------
    def apply_current_dictionary_on_current_tab_collateral(self, dict_name, dictionary, tabed_entries, coll_name,
                                                           line_num, res):
        keyIndex = int(dictionary["key"])
        if (keyIndex >= len(tabed_entries)):
            htdte_logger.error((
                " The  key index (%d) in \"tab text\" in dictionary  \"%s\" exceed the line tabs "
                "number at collateral:%s:line:%d - %s") % (
                int(dictionary["key"]), dict_name, coll_name, line_num, str(tabed_entries)))
        keyValue = tabed_entries[int(dictionary["key"])]
        # ----------------------------
        for entry in list(dictionary.keys()):
            if (entry not in self.dictionary_entry_reserved_keys):
                if (isinstance(dictionary[entry], dict)):
                    if ("key" not in list(dictionary[entry].keys())):
                        htdte_logger.error((
                            " The dictionary  \"%s\" has not assigned key-attribute at sub level "
                            "definition - \"%s\"....") % (
                            dict_name, entry))
                    if (keyValue not in list(res.keys())):
                        res[keyValue] = {}
                    self.apply_current_dictionary_on_current_tab_collateral(dict_name, dictionary[entry], tabed_entries,
                                                                            coll_name, line_num, res[keyValue])
                else:
                    islist = ("islist" in list(dictionary.keys())) and (dictionary["islist"] in HTD_True_Statement)
                    key_value_format = ("key_value_format" in list(dictionary.keys())) and (
                        dictionary["key_value_format"] in HTD_True_Statement)
                    if (key_value_format and (
                            len([x for x in list(dictionary.keys()) if (x not in self.dictionary_entry_reserved_keys)]) > 1)):
                        htdte_logger.error((
                            " The dictionary  \"%s\" has multiple attributes while the simgle "
                            "mapping "
                            "\"key_value_format\" is selected   ....") % (
                            dict_name))
                    # -----------------
                    entryIndex = int(dictionary[entry])
                    if (entryIndex >= len(tabed_entries)):
                        htdte_logger.error((
                            " The  %s index (%d) in \"tab text\" in dictionary  \"%s\" exceed the "
                            "line tabs number at collateral:%s:line:%d ,line:%s") % (
                            entry, entryIndex, dict_name, coll_name, line_num, str(tabed_entries)))
                    if (keyValue not in list(res.keys())):
                        if (key_value_format):
                            if (islist):
                                res[keyValue] = []
                        else:
                            res[keyValue] = {}
                            res[keyValue][entry] = [] if islist else {}
                    # --------------------------------
                    if (key_value_format):
                        if (islist):
                            self.add_normilized_string_value_to_dictionary(res[keyValue], tabed_entries[entryIndex],
                                                                           islist)
                        else:
                            res[keyValue] = self.add_normilized_string_value_to_dictionary(res[keyValue],
                                                                                           tabed_entries[entryIndex],
                                                                                           islist)
                    else:
                        if (islist):
                            if (entry not in list(res[keyValue].keys())):
                                res[keyValue][entry] = []
                            self.add_normilized_string_value_to_dictionary(res[keyValue][entry],
                                                                           tabed_entries[entryIndex], islist)
                        else:
                            if (entry not in list(res[keyValue].keys())):
                                res[keyValue][entry] = {}
                            res[keyValue][entry] = util_merge_dictionaries(res[keyValue][entry],
                                                                           self.add_normilized_string_value_to_dictionary(
                                                                               res[keyValue][entry],
                                                                               tabed_entries[entryIndex], islist))

    # ----------------------------------------------------------------------------------------
    # Apply current dictionary on current xml collateral and create dynamically the dictiory-hash
    # ----------------------------------------------------------------------------------------
    def apply_current_dictionary_on_current_xml_collateral(self, dict_name, keyNodePath, dictionary, rootNode, res,
                                                           level=0):
        # -----First level entry should have a key entry ---
        if ("node" not in list(dictionary.keys())):
            htdte_logger.error(
                (" The dictionary  \"%s\" has not assigned node-attribute at first level definition....") % (dict_name))
        # -----Filtering nodes (if filter property exists in dictionary def--------
        filtered_nodes = []
        node_l, val = self.read_combined_xml_cfg_value(dictionary["node"])
        target_nodes = self.traverse_nodes_by_path(rootNode, node_l, 0, (0 if level == 0 else 1))
        # ---Filtering all nodes by "filter" attribute, if exists
        if ("filter" in list(dictionary.keys())):
            for node in target_nodes:
                fnode_l, fval = self.read_combined_xml_cfg_value(dictionary["filter"])
                filter_evaluated_value = self.get_xml_value_by_combined_path(node, fnode_l)
                if (re.search(fval, filter_evaluated_value)):
                    filtered_nodes.append(node)
        else:
            filtered_nodes = target_nodes
        # --------------------------
        for nodeIter in filtered_nodes:
            keyNodeStr = dictionary["key"]
            matchCond = re.match(r"^\?([A-z0-9\.\./]+)", keyNodeStr)
            conditionalKeyNode = 0
            if (matchCond):
                keyNodeStr = matchCond.groups()[0]
                conditionalKeyNode = 1
            key_node_l, dummy = self.read_combined_xml_cfg_value(keyNodeStr)
            # ------Check node to key consistency - no multiple key nodes in same root node ------------------
            if (not self.is_single_node_hierarchy(nodeIter, key_node_l,
                                                  conditionalKeyNode) and not self.disable_duplicated_xml_node_error):
                htdte_logger.error((
                    " The dictionary  \"%s\" has multiple key-attribute mapping in repect to "
                    "rootnode=\"%s\" : Each root node appearence should have a single mapping to "
                    "key node only....") % (
                    dict_name, dictionary["key"]))
            keyValue = self.get_xml_value_by_combined_path(nodeIter, key_node_l, conditionalKeyNode)
            if ((not conditionalKeyNode) or keyValue != "none"):
                islist = ("islist" in list(dictionary.keys())) and (dictionary["islist"] in HTD_True_Statement)
                key_value_format = ("key_value_format" in list(dictionary.keys())) and (
                    dictionary["key_value_format"] in HTD_True_Statement)

                res[keyValue] = {}
                if (islist):
                    if (key_value_format):
                        res[keyValue] = []
                    else:
                        res[keyValue][entry] = []

                # -----------------------
                for entry in list(dictionary.keys()):
                    if (entry not in self.dictionary_entry_reserved_keys):
                        if (isinstance(dictionary[entry], dict)):
                            if ("key" not in list(dictionary[entry].keys())):
                                htdte_logger.error((
                                    " The dictionary  \"%s\" has not assigned key-attribute at sub "
                                    "level definition - \"%s\"....") % (
                                    dict_name, entry))
                            # --------
                            res[keyValue][entry] = {}
                            self.apply_current_dictionary_on_current_xml_collateral(dict_name, dictionary[entry]["key"],
                                                                                    dictionary[entry], nodeIter,
                                                                                    res[keyValue][entry], level + 1)
                        else:
                            entryNode = dictionary[entry]
                            # --Entry node format :
                            matchCond = re.match(r"^\?([A-z0-9\.\./='\(\)]+)", entryNode)  # Eitan Pinhas for ADL
                            # ---If the node value starts by ? - may exist or not on input XML
                            optionalNode = 0
                            if (matchCond):
                                entryNode = matchCond.groups()[0]
                                optionalNode = 1
                            # --------------------
                            entry_node_l, dummy = self.read_combined_xml_cfg_value(entryNode)
                            xmlvalue = self.get_xml_value_by_combined_path(nodeIter, entry_node_l, optionalNode)
                            if ((not optionalNode) or xmlvalue != "none"):
                                if (islist):
                                    if (key_value_format):
                                        res[keyValue].append(xmlvalue)
                                    else:
                                        res[keyValue][entry].append(xmlvalue)
                                else:
                                    if (key_value_format):
                                        res[keyValue] = xmlvalue
                                    else:
                                        res[keyValue][entry] = xmlvalue
                                        # --------------------

    # ----------------------------------------------------------------------------------------
    # Multiprocessing Processing XML collaterals by splitting them to
    # ----------------------------------------------------------------------------------------
    def partial_xml_parse_dictionary(self, part_file_name, dictionary, key, dic_entry):
        xml_ptr = minidom.parse(part_file_name)
        res = {}
        self.apply_current_dictionary_on_current_xml_collateral(dictionary, key, dic_entry, xml_ptr, res)
        os.remove(part_file_name)
        htd_compress.dump(res, open(("%s.%s") % (part_file_name, self.CFG["INFO"]["collateral_compressor"]), "w"))

    # ----------------------------------------------------------------------------------------
    # Second level Splitting large XML files to partial xml files while keeping same structure- two levels: key1, key2
    # ----------------------------------------------------------------------------------------
    def second_level_split_xml_large_file(self, temp_dir, file_name, root_nodes, relevant_nodes, num_of_parts_limit):
        total_num_of_blocks = 0
        for n in root_nodes:
            total_num_of_blocks += int(os.popen(("grep -c \"<%s\" %s") % (n, file_name)).read().replace("\n", ""))
        # -----------------------------------------
        partial_files_tracker = {}
        xml_ptr = et.iterparse(file_name, events=("start", "end"))
        # event, root = xml_ptr.next()
        header_inprocess = True
        content_inprogress = False
        current_content_count = 0
        current_file_index = 1
        prev_event = ""
        stop_processing = True
        header = []  # array of {'s'}=<start tag>,{'a'}=<attribute>,{'v'}=<value>,{'e'}=<tag end>
        for event, elem in xml_ptr:
            # ---Recording the header (1st) level until actual (2nd level) block reached
            if (event == 'start' and header_inprocess and elem.tag in root_nodes):
                header_inprocess = False
                current_content_count += 1
                stop_processing = False
            if (event == 'start' and header_inprocess and elem.tag in relevant_nodes):
                header.append({'s': elem.tag, "a": ""})
            if (event == 'end' and header_inprocess and elem.tag in relevant_nodes):
                header[-1]['e'] = elem.tag
                header[-1]['v'] = elem.text
                header[-1]['a'] = ""
                for att in list(elem.attrib.keys()):
                    header[-1]['a'] += att + "=\"" + elem.attrib[att] + "\" "
            # -----------------------------------
            if (event == 'start' and not header_inprocess and elem.tag in root_nodes):
                stop_processing = False
            if (event == 'start' and not header_inprocess and elem.tag in relevant_nodes):
                if (current_content_count == 1):
                    # ------------------
                    current_file_index += 1
                    fwptr = open(file_name + ("_%d") % (current_file_index), 'w')
                    # -------Write header
                    for h in header:
                        if ("s" in list(h.keys()) and "e" not in list(h.keys())):
                            fwptr.write("\n<" + h["s"] + h["a"] + ">")
                        elif (h["v"] is None and h["a"] == ""):
                            pass
                        else:
                            escaped_str0 = escape(h["v"] if (h["v"] != None) else "")
                            if escaped_str0 == "":
                                escaped_str0 = "  "  # Put two spaces for backward compatibility
                            fwptr.write(
                                "\n<" + h["s"] + h["a"] + ">" + escaped_str0 + "</" + h["e"] + ">")
                # ---end of write header
                current_content_count += 1
                attr_str = ""
                for att in list(elem.attrib.keys()):
                    attr_str += " " + att + "=\"" + elem.attrib[att] + "\" "
                fwptr.write("<" + elem.tag + attr_str + ">")
            # ---------------
            if (event == 'end' and (not header_inprocess) and (elem.tag in relevant_nodes) and (not stop_processing)):
                escaped_str = escape(elem.text if (elem.text != None) else "")
                if escaped_str == "":
                    escaped_str = " "  # To fix description = null
                fwptr.write(escaped_str + "</" + elem.tag + ">\n")
                elem.clear()
            if (event == 'end' and not header_inprocess and elem.tag in root_nodes):
                stop_processing = True
                if (current_content_count > total_num_of_blocks // num_of_parts_limit):
                    current_content_count = 1
                    # ---Write close xml
                    for h in header:
                        if ("s" in list(h.keys()) and "e" not in list(h.keys())):
                            fwptr.write("</" + h["s"] + ">\n")
                    fwptr.close()
                    # ---Save file infor in tracker
                    finfo = os.stat(file_name + ("_%d") % (current_file_index))
                    if (finfo.st_size not in list(partial_files_tracker.keys())):
                        partial_files_tracker[finfo.st_size] = []
                    partial_files_tracker[finfo.st_size].append(file_name + ("_%d") % (current_file_index))
                # ---------------------------------
                elem.clear()
            prev_event = event
        # -----------
        return partial_files_tracker
        htdte_logger.inform("STAM")

    # ----------------------------------------------------------------------------------------
    # Splitting large XML files to partial xml files while keeping same structure- two levels: key1, key2
    # ----------------------------------------------------------------------------------------
    def split_xml_large_file(self, col_name, temp_dir, file_name, root_node_name, cfg_entry, relevant_nodes):
        # ---------Prepare second level key splitting criteria----------------------
        second_level_key_nodes = []
        for k in list(cfg_entry.keys()):
            if (isinstance(cfg_entry[k], dict) and ("key" in list(cfg_entry[k].keys()))):
                second_level_key_nodes.append(k)
        # -------------------------------
        indx = 0
        fptr = open(self.collaterals_list[col_name]["path"], 'rb')
        partial_files_tracker = {}
        fwptr = None
        file_name = re.sub("[A-z0-9_]+/", "", self.collaterals_list[col_name]["path"]).replace("/", "")
        part_file_name = ("%s/%s_%d") % (temp_dir, file_name, indx)
        for line in fptr:
            line = line.decode("ascii","ignore")
            if ("<" + root_node_name in line):
                part_file_name = ("%s/%s_%d") % (temp_dir, file_name, indx)
                fwptr = open(part_file_name, 'w')
            elif ("</" + root_node_name + ">" in line):
                fwptr.write(line)
                fwptr.close()
                fwptr = None
                # -------Start multi threading for processing all sub files------
                finfo = os.stat(part_file_name)
                if (finfo.st_size > HTD_XML_second_level_file_size_split_criteria and len(second_level_key_nodes) > 0):
                    partial_files_tracker = util_merge_dictionaries(partial_files_tracker,
                                                                    self.second_level_split_xml_large_file(temp_dir,
                                                                                                           part_file_name,
                                                                                                           second_level_key_nodes,
                                                                                                           relevant_nodes,
                                                                                                           finfo.st_size // HTD_XML_second_level_file_size_split_criteria))
                    os.remove(part_file_name)
                else:
                    if (finfo.st_size not in list(partial_files_tracker.keys())):
                        partial_files_tracker[finfo.st_size] = []
                    partial_files_tracker[finfo.st_size].append(part_file_name)
                indx += 1
            if (fwptr is not None):
                fwptr.write(line)
        fptr.close()
        # --------------
        return partial_files_tracker

    # ----------------------------------------------------------------------------------------
    # Processing XML collaterals, there are 2 different parsing modes: big and regular file
    # ----------------------------------------------------------------------------------------
    def parse_xml_dictionary(self, col_name, dictionary, dict_entity, result):
        start = time.clock()
        if ("disable_duplicated_xml_nodes_error" in list(self.collaterals_list[col_name].keys())
                and self.collaterals_list[col_name]["disable_duplicated_xml_nodes_error"] > 0):
            self.disable_duplicated_xml_node_error = True
        else:
            self.disable_duplicated_xml_node_error = False
        # ---------------------------
        if (("largefile" in list(dict_entity.keys())) and (
                dict_entity["largefile"] in HTD_True_Statement)):  # the collateral is more then 10Mbyte
            htdte_logger.inform("Processing XML in  \"large file\" mode...")
            # ---Prepare temp sirectory-------------------------
            temp_dir = util_get_temp_dir_name("htd_info")
            htdte_logger.inform(("Splitting XML file %s and processing on temp area :  %s...") % (
                self.collaterals_list[col_name]["path"], temp_dir))
            if (not os.access(temp_dir, os.W_OK)):
                os.mkdir(temp_dir)
            # --------------------------------------------------
            # splitting file by key Tag for multiple files and execute multiple processes to parse it
            relevant_nodes = self.get_all_used_xml_node_names(
                dict_entity["entries"])  # get only relevant nodes used in dictionary
            for entry in dict_entity["entries"]:
                # -----First level entry should have a key entry ---
                if ("key" not in list(entry.keys())):
                    htdte_logger.error((
                        " The dictionary:collateral  \"%s:%s\" has not assigned key-attribute at "
                        "first level definition....") % (
                        dictionary, coll_name))
                # -------Splitting file to multiple files----------------------
                node_l, val = self.read_combined_xml_cfg_value(entry["node"])
                part_file_name_prefix = re.sub("[A-z0-9_]+/", "", self.collaterals_list[col_name]["path"]).replace("/",
                                                                                                                   "")
                partial_files_tracker = self.split_xml_large_file(col_name, temp_dir, part_file_name_prefix, node_l[0],
                                                                  entry, relevant_nodes)
                # ---------------------------------------------------------------
                # 1 we are interesting to submit in multiprocessing only "heavy-weight" files >1M for example...
                #  need to orbitrate between process wakup time and XML processing consuming time
                #  The heavy processes to be executed first , the "light" files to be executed serially
                active_processes = {}
                active_processes_obj = []
                reversed_sorted_key_l = reversed(sorted(partial_files_tracker.keys()))
                for size in reversed_sorted_key_l:
                    for part_file_name in partial_files_tracker[size]:
                        num_of_active_processes = len([x for x in active_processes_obj if (x.is_alive())])
                        if ((
                                size > HTD_XML_parallel_processing_file_size_criteria and num_of_active_processes
                                < HTD_XML_parallel_processing_proc_num) or num_of_active_processes < 4):
                            # --Execute multiple process
                            print("Submitting " + part_file_name + "\n")
                            p = multiprocessing.Process(target=process_handler_proceed_xml_part, args=(
                                self.te_cfg_col, part_file_name, dictionary, entry["key"], entry, self.disable_duplicated_xml_node_error))
                            p.start()
                            active_processes[part_file_name] = p
                            active_processes_obj.append(p)
                        else:
                            # serial processing
                            self.partial_xml_parse_dictionary(part_file_name, dictionary, entry["key"], entry)
                # ---------------------------------------------------------------
                # Start merging the results and waiting until all processes done
                # ---------------------------------------------------------------
                htdte_logger.inform(" Merging partial files..")
                for size in sorted(partial_files_tracker.keys()):  # start merging from small size toward large size
                    for part_name in partial_files_tracker[size]:
                        if ((part_name in list(active_processes.keys())) and (active_processes[part_name].is_alive())):
                            sys.stdout.write((' Waiting until %s processing done \n') % (part_name))
                            active_processes[part_name].join()

                        res = htd_compress.load(
                            open(("%s.%s") % (part_name, self.CFG["INFO"]["collateral_compressor"]), "rb"))
                        for key in list(res.keys()):
                            if (key in list(result.keys())):
                                result[key] = util_merge_dictionaries(result[key], res[key])
                            else:
                                result[key] = res[key]
                        os.remove(("%s.%s") % (part_name, self.CFG["INFO"]["collateral_compressor"]))
                # --------------------------------
                for fptr in list(active_processes.keys()):
                    if (active_processes[fptr].is_alive()):
                        htdte_logger.error((" The collateral partition \"%s\" was not merged properly ....") % (fptr))
                        # ------------------------
        else:
            # --The XML collateral is less then 10Mbyte size---
            if ("ptr" not in list(self.collaterals_list[col_name].keys())):
                htdte_logger.inform(
                    (" Opening XML collateral[\"%s\" - %s ....") % (col_name, self.collaterals_list[col_name]["path"]))
                self.collaterals_list[col_name]["ptr"] = minidom.parse(self.collaterals_list[col_name]["path"])
            # --------------------------------------------------
            xml_ptr = self.collaterals_list[col_name]["ptr"]
            # ---------------
            for entry in dict_entity["entries"]:
                # -----First level entry should have a key entry ---
                if ("key" not in list(entry.keys())):
                    htdte_logger.error((
                        " The dictionary:collateral  \"%s:%s\" has not assigned key-attribute at "
                        "first level definition....") % (
                        dictionary, col_name))
                # -----------------------
                self.apply_current_dictionary_on_current_xml_collateral(dictionary, entry["key"], entry, xml_ptr,
                                                                        result)
        htdte_logger.inform(("Processing time : %d(ms)") % ((time.clock() - start) * 1000))

    # -----------------------------------------------------------
    # Processing user regexp collateral
    # -----------------------------------------------------------
    def processing_user_regexp_collateral(self, dictionary, coll_name, dict_entity):
        start = time.clock()
        res = {}
        line_queue = []
        if ("regmatch" not in list(dict_entity.keys())):
            htdte_logger.error((
                " The dictionary:collateral  \"%s:%s\" has not assigned regular expression string "
                "(to be used for paring/matching)....") % (
                dictionary, coll_name))
        regexp = dict_entity["regmatch"]

        replacements = dict()
        if ("regreplace" in list(dict_entity.keys())):
            for replacement in dict_entity["regreplace"].split(","):
                idx, replace = replacement.split(":")
                idx = int(idx)
                replacements[idx] = replace
                htdte_logger.inform("Regreplace for index %d: %s" % (idx, replace))
        else:
            htdte_logger.inform("No regreplace found for %s" % (coll_name))

        for entry in dict_entity["entries"]:
            # -----First level entry should have a key entry ---
            if ("key" not in list(entry.keys())):
                htdte_logger.error((
                    " The dictionary:collateral  \"%s:%s\" has not assigned key-attribute at first "
                    "level definition....") % (
                    dictionary, coll_name))
            # -----------------------
            htdte_logger.inform(
                (" Opening USER collateral[\"%s\" - %s ....") % (coll_name, self.collaterals_list[coll_name]["path"]))
            fptr = open(self.collaterals_list[coll_name]["path"], 'r')
            line_num = 0
            # --Calculating number of user lines matching, pre-reading the number of regexp lines to queue -
            regexp_l = regexp.split("\\n")
            while True:
                line = fptr.readline()
                if not line:
                    break
                line_num = line_num + 1
                # ---if queue is empty refill it -----------------
                if (len(line_queue) == 0):
                    while (len(line_queue) <= len(regexp_l) - 1):
                        if (("comment" not in list(self.collaterals_list[coll_name].keys())) or (
                                not re.match(("^\s*%s") % (self.collaterals_list[coll_name]["comment"]), line)) or (
                                not re.match("^\s*$", line))):
                            line_queue.append(line)
                        line = fptr.readline()
                        line_num = line_num + 1
                # -------Matching Comment-------------
                if (("comment" in list(self.collaterals_list[coll_name].keys())) and (
                        re.match(("^\s*%s") % (self.collaterals_list[coll_name]["comment"]), line) or re.match("^\s*$",
                                                                                                               line))):
                    continue
                line_queue.append(line)
                # ------Matching-------------
                final_match = True
                result_matches = []

                for i in range(0, len(regexp_l)):
                    match = re.search(regexp_l[i], line_queue[i])
                    if (match):
                        match_groups = match.groups()

                        # Check if there is a replacement for this regex group
                        if (i in replacements):
                            temp_match = match_groups[0]
                            match_groups = (re.sub(r"\|%d\|" % (i), temp_match, replacements[i]),)
                            htdte_logger.inform("Updating match %s to %s due to regreplace (%s) match" % (
                                temp_match, match_groups[0], replacements[i]))

                        result_matches.extend(match_groups)
                        if (("debug" in list(dict_entity.keys())) and (dict_entity["debug"] in HTD_True_Statement)):
                            htdte_logger.inform(("Matched:%d: %s") % (line_num, line_queue[i]))
                        else:
                            if (("debug" in list(dict_entity.keys())) and (dict_entity["debug"] in HTD_True_Statement)):
                                htdte_logger.inform(("Not Matched:%d: %s") % (line_num, line_queue[i]))
                    else:
                        final_match = False
                        break
                # -----------------------------------
                if (final_match):
                    if (("debug" in list(dict_entity.keys())) and (dict_entity["debug"] in HTD_True_Statement)):
                        htdte_logger.inform(("Final Match:%d: %s") % (line_num, str(result_matches)))
                    self.apply_current_dictionary_on_current_user_collateral(dictionary, entry, result_matches,
                                                                             coll_name, line_num, res)
                # ------Remove last line from pipe---------------
                line_queue.pop(0)
            fptr.close()
        htdte_logger.inform(("Processing time : %d(ms)") % ((time.clock() - start) * 1000))
        return res

    # ----------------------------------------------------------------------------------------
    # Splitting large Text files to partial  files while by number of lines limit
    # ----------------------------------------------------------------------------------------
    def split_text_large_file(self, col_name, temp_dir, file_name):
        sufix_length = 5
        if ("INFO" in list(self.CFG.keys()) and "split_file_name_sufix_length" in list(self.CFG["INFO"].keys())):
            sufix_length = int(self.CFG["INFO"]["split_file_name_sufix_length"])
        part_file_prefix = ("%s/%s") % (temp_dir, file_name)
        cmd = ("/usr/bin/split -l %d -d -a %d --verbose %s %s") % (
            HTD_XML_parallel_processing_text_file_lines_criteria, sufix_length, self.collaterals_list[col_name]["path"],
            part_file_prefix)
        result = subprocess.getstatusoutput(
            cmd)  # array - first is status, 2nd is valuesplit_args=['/usr/bin/split','-l %d'%
        # HTD_XML_parallel_processing_text_file_lines_criteria, "-d -a 4 --verbose",self.collaterals_list[col_name][
        # "path"]]
        if (result[0] is not 0):
            htdte_logger.error(("Fail to run UNIX split command:%s\n%s...") % (cmd, result[1]))
        partial_files_tracker = result[1].replace("creating file ", "").replace("`", "").replace("'", "").split("\n")
        return partial_files_tracker

    # -----------------------------------------------------------
    # Processing large
    # -----------------------------------------------------------
    # -----------------------------------------------------------
    # Processing csv text collateral
    # -----------------------------------------------------------
    def processing_csv_collateral(self, dictionary, coll_name, dict_entity):
        result = {}
        res = {}
        for entry in dict_entity["entries"]:
            # -----First level entry should have a key entry ---
            if ("key" not in list(entry.keys())):
                htdte_logger.error((
                    " The dictionary:collateral  \"%s:%s\" has not assigned key-attribute at first "
                    "level definition....") % (
                    dictionary, coll_name))
            htdte_logger.inform(
                (" Opening CSV collateral[\"%s\" - %s ....") % (coll_name, self.collaterals_list[coll_name]["path"]))
            if (("largefile" in list(dict_entity.keys())) and (
                    dict_entity["largefile"] in HTD_False_Statement)):
                # --Regular non large mode-------------
                fptr = open(self.collaterals_list[coll_name]["path"], 'r')
                line_num = 0
                StartCSV_Content = True
                line = fptr.readline()
                while line:
                    line_num = line_num + 1
                    if (("comment" in list(self.collaterals_list[coll_name].keys())) and (
                            re.match(("^\s+%s") % (self.collaterals_list[coll_name]["comment"]), line))):
                        line = fptr.readline()
                        continue
                    if (re.match("^-", line) or re.match(r"^\s*#", line)):
                        line = fptr.readline()
                        continue
                    if (re.match(r"^\s*CSV_FORMAT", line)):
                        line = fptr.readline()
                        StartCSV_Content = False
                        continue
                    if (not StartCSV_Content):
                        line = fptr.readline()
                        StartCSV_Content = True
                        continue
                    csv_entries = re.split(",", line.replace("\n", ""))
                    if (("debug" in list(dict_entity.keys())) and (dict_entity["debug"] in HTD_True_Statement)):
                        htdte_logger.inform(("Adding : %s %d") % (str(csv_entries), line_num))
                    self.apply_current_dictionary_on_current_tab_collateral(dictionary, entry, csv_entries, coll_name,
                                                                            line_num, res)
                    line = fptr.readline()
                fptr.close()
            else:  # the collateral is more then 10Mbyte
                htdte_logger.inform("Processing CSV in  \"large file\" mode...")
                # ---Prepare temp sirectory-------------------------
                temp_dir = util_get_temp_dir_name("htd_info")
                htdte_logger.inform(("Splitting CSV file %s and processing on temp area :  %s...") % (
                    self.collaterals_list[coll_name]["path"], temp_dir))
                if (not os.access(temp_dir, os.W_OK)):
                    os.mkdir(temp_dir)
                part_file_name_prefix = re.sub("[A-z0-9_]+/", "", self.collaterals_list[coll_name]["path"]).replace("/",
                                                                                                                    "")
                partial_files_tracker = self.split_text_large_file(coll_name, temp_dir, part_file_name_prefix)
                active_processes = {}
                active_processes_obj = []
                for part_file_name in partial_files_tracker:
                    print("Submitting " + part_file_name + "\n")
                    p = multiprocessing.Process(target=process_handler_proceed_csv_part, args=(
                        self.collaterals_list, self.te_cfg_col, part_file_name, dictionary, coll_name, entry))
                    p.start()
                    active_processes[part_file_name] = p
                    active_processes_obj.append(p)
                # ---------------------------------------------------------------
                # Start merging the results and waiting until all processes done
                # ---------------------------------------------------------------
                htdte_logger.inform(" Merging partial files..")
                for part_name in partial_files_tracker:
                    if ((part_name in list(active_processes.keys())) and (active_processes[part_name].is_alive())):
                        sys.stdout.write((' Waiting until %s processing done \n') % (part_name))
                        active_processes[part_name].join()
                    res = htd_compress.load(
                        open(("%s.%s") % (part_name, self.CFG["INFO"]["collateral_compressor"]), "rb"))
                    for key in list(res.keys()):
                        if (key in list(result.keys())):
                            result[key] = util_merge_dictionaries(result[key], res[key])
                        else:
                            result[key] = res[key]
                    os.remove(("%s.%s") % (part_name, self.CFG["INFO"]["collateral_compressor"]))
                # --------------------------------
                for fptr in list(active_processes.keys()):
                    if (active_processes[fptr].is_alive()):
                        htdte_logger.error((" The collateral partition \"%s\" was not merged properly ....") % (fptr))
        return res

    # -----------------------------------------------------------
    # Processing tabular text collateral
    # -----------------------------------------------------------
    def processing_tabular_text_collateral(self, dictionary, coll_name, dict_entity):
        res = {}
        for entry in dict_entity["entries"]:
            # -----First level entry should have a key entry ---
            if ("key" not in list(entry.keys())):
                htdte_logger.error((
                    " The dictionary:collateral  \"%s:%s\" has not assigned key-attribute at first "
                    "level definition....") % (
                    dictionary, coll_name))
            htdte_logger.inform(
                (" Opening TAB collateral[\"%s\" - %s ....") % (coll_name, self.collaterals_list[coll_name]["path"]))
            # ----------------------------------
            if (("largefile" in list(dict_entity.keys())) and (
                    dict_entity["largefile"] in HTD_False_Statement)):
                fptr = open(self.collaterals_list[coll_name]["path"], 'r')
                line_num = 0
                line = fptr.readline()
                while line:
                    line_num = line_num + 1
                    if (("comment" in list(self.collaterals_list[coll_name].keys())) and (
                            re.match(("^\s+%s") % (self.collaterals_list[coll_name]["comment"]), line))):
                        line = fptr.readline()
                        continue
                    # line.split() is the same thing as re.split(" +", line) but string split is faster than re.split
                    tabed_entries = line.split()
                    if (("debug" in list(dict_entity.keys())) and (dict_entity["debug"] in HTD_True_Statement)):
                        htdte_logger.inform(("Adding : %s %d") % (str(tabed_entries), line_num))
                    self.apply_current_dictionary_on_current_tab_collateral(dictionary, entry, tabed_entries, coll_name,
                                                                            line_num, res)
                    line = fptr.readline()
                fptr.close()
            else:  # the collateral is more then 10Mbyte
                htdte_logger.inform("Processing TAB files in  \"large file\" mode...")
                # ---Prepare temp sirectory-------------------------
                temp_dir = util_get_temp_dir_name("htd_info")
                htdte_logger.inform(("Splitting TAB file %s and processing on temp area :  %s...") % (
                    self.collaterals_list[coll_name]["path"], temp_dir))
                if (not os.access(temp_dir, os.W_OK)):
                    os.mkdir(temp_dir)
                # --------------------------------------------------
                part_file_name_prefix = re.sub("[A-z0-9_]+/", "", self.collaterals_list[coll_name]["path"]).replace("/",
                                                                                                                    "")
                partial_files_tracker = self.split_text_large_file(coll_name, temp_dir, part_file_name_prefix)
                active_processes = {}
                active_processes_obj = []
                for part_file_name in partial_files_tracker:
                    print("Submitting " + part_file_name + "\n")
                    p = multiprocessing.Process(target=process_handler_proceed_tab_part, args=(
                        self.collaterals_list, self.te_cfg_col, part_file_name, dictionary, coll_name, entry,
                        ("debug" in list(dict_entity.keys())) and (dict_entity["debug"] in HTD_True_Statement)))
                    p.start()
                    active_processes[part_file_name] = p
                    active_processes_obj.append(p)
                # ---------------------------------------------------------------
                # Start merging the results and waiting until all processes done
                # ---------------------------------------------------------------
                htdte_logger.inform(" Merging partial files..")
                for part_name in partial_files_tracker:
                    if ((part_name in list(active_processes.keys())) and (active_processes[part_name].is_alive())):
                        sys.stdout.write((' Waiting until %s processing done \n') % (part_name))
                        active_processes[part_name].join()
                    res_tmp = htd_compress.load(
                        open(("%s.%s") % (part_name, self.CFG["INFO"]["collateral_compressor"]), "rb"))
                    for key in list(res_tmp.keys()):
                        if (key in list(res.keys())):
                            res[key] = util_merge_dictionaries(res[key], res_tmp[key])
                        else:
                            res[key] = res_tmp[key]
                    os.remove(("%s.%s") % (part_name, self.CFG["INFO"]["collateral_compressor"]))
                # --------------------------------
                for fptr in list(active_processes.keys()):
                    if (active_processes[fptr].is_alive()):
                        htdte_logger.error((" The collateral partition \"%s\" was not merged properly ....") % (fptr))
                        # ----------------------------------
        return res

    # -------------------------------------------------------------
    # Execute post processing functor on dictionaries
    # -------------------------------------------------------------
    def post_processing_functors(self, dictionary, dict_entity, dict_ptr, debug):
        # -----If dictionary postprocessing function define , run it ----
        if ("func" in list(dict_entity.keys())):
            for f in dict_entity["func"]:
                module_path = ("%s/%s.py") % (f["path"], f["module"])
                htdte_logger.inform(("Running dictionary (%s) postprocessing functor: %s, from module: %s") % (
                    dictionary, f["func"], module_path))
                if (os.path.exists(module_path)):
                    status, mname, py_mod = util_dynamic_load_external_module(module_path)
                    if (not status):
                        htdte_logger.error((" Can't load collateral post-processing module - %s ") % (module_path))
                    exec((("from %s import *") % (mname)), globals())
                    exec (("%s(\"%s\",dict_ptr,self.dictionaries_list,self.CFG,%d)") % (f["method"], dictionary, debug))
                else:
                    htdte_logger.error(
                        (" Can't resolve a path to collateral post-processing module - %s ") % (module_path))

    # -------------------------------------------------------------
    # Parsing all collaterals XML based on TE_CFG dictionary
    # ------------------------------------------------------------

    def parse_all_collaterals(self, exclude_list):
        # ---Processing all dictionary to inedtify if collaterals previously parsed and saved, load dictionaries from
        #  binary if saved or processing collaterals if not
        not_saved_dictionaries = []
        gzipped_file_l = []
        lock_obj = dict()
        try:
            collateral_timeout_in_minutes = self.CFG["INFO"]["collateral_generation_wait_timeout"]
        except KeyError:
            collateral_timeout_in_minutes = 60  # default value
        htdte_logger.inform(("Timeout for waiting on collateral files = %s minutes") % (collateral_timeout_in_minutes))
        try:
            # ---Verify exclude list
            for excl in exclude_list:
                if (excl not in self.te_cfg_col_order):
                    htdte_logger.error((
                        "Illegal collateral dictionary name (%s) found in exclude "
                        "list:%s.\nAvailable dictionaries are : %s  ") % (
                        excl, str(exclude_list), str(self.te_cfg_col_order)))
            # ----------------------
            for dictionary in self.te_cfg_col_order:
                col_names = []
                if (dictionary in exclude_list):
                    continue
                for dict_entity in self.te_cfg_col[dictionary]:
                    for coll in dict_entity["collateral"]:
                        current_col_name = coll
                        col_names.append(current_col_name)
                        self.collaterals_list[current_col_name]["file_info"] = self.get_collateral_file_info(
                            current_col_name, (" required by dictionary -\"%s\"") % (dictionary))
                # ---------------------
                # --Check if this dictionary saved in binary mode and verify integrity of image---
                dict_definition_crc = self.get_dict_definition_crc(dictionary)
                picklefile = self.get_col_pickle_name(col_names, dictionary, base_crc=dict_definition_crc)

                lock_obj[picklefile] = filelock.FileLock(picklefile + ".lock")
                htdte_logger.inform(("[%s] Requesting lock on %s") % (time.ctime(), os.path.basename(picklefile)))
                try:
                    lock_obj[picklefile].acquire(timeout=collateral_timeout_in_minutes * 60,
                                                 poll_intervall=5)  # timeout in seconds, poll every 5 seconds
                    htdte_logger.inform(("[%s] Got lock on %s") % (time.ctime(), os.path.basename(picklefile)))
                except OSError:  # Most likely due to not having write permissions to private collaterals dir,
                    # carry on and let the directory write test below fail
                    htdte_logger.inform(("[%s] Did not get lock on %s") % (time.ctime(), os.path.basename(picklefile)))
                    pass
                if (os.path.exists(picklefile)):
                    lock_obj[picklefile].release()
                    htdte_logger.inform(("[%s] Released lock on %s") % (time.ctime(), os.path.basename(picklefile)))
                    htdte_logger.inform(("Loading compiled image for dictionary - \"%s\"  ....\n%s") % (
                        picklefile, self.get_saved_pickle_info(picklefile)))
                    self.dictionaries_list[dictionary] = htd_compress.load(open(picklefile, "rb"))
                elif (os.path.isfile(picklefile + ".bz2")):
                    lock_obj[picklefile].release()
                    htdte_logger.inform(("[%s] Released lock on %s") % (time.ctime(), os.path.basename(picklefile)))
                    htdte_logger.inform(("Loading compiled image for dictionary - \"%s\"  ....\n%s") % (
                        picklefile + ".bz2", self.get_saved_pickle_info(picklefile)))
                    self.dictionaries_list[dictionary] = htd_compress.load(bz2.BZ2File(picklefile + ".bz2", "rb"))
                else:
                    not_saved_dictionaries.append(dictionary)
                    for dict_entity in self.te_cfg_col[dictionary]:
                        if (("compile" in list(dict_entity.keys())) and (dict_entity["compile"] in HTD_True_Statement)):
                            htdte_logger.inform(
                                ("Can't find compiled dictionary - \"%s\"..Compiling it now...") % (picklefile))
                            if (("INFO" in list(self.CFG.keys())) and (
                                    self.CFG["INFO"]["compile_collaterals"] in HTD_False_Statement)):
                                pickles_info = self.get_saved_pickle_info(dictionary)
                                htdte_logger.error((
                                    "Missing compiled dictionary - \"%s\" (signed in TE_cfg as "
                                    "compiled)...\nIn order to enable dictionary generation, "
                                    "pls. supply in command line \"-CFG:INFO:compile_collaterals "
                                    "1\" or change this configuration in TE_cfg.xml.\nAvailable "
                                    "collaterals are:%s") % (
                                    dictionary, pickles_info))
                            else:
                                # verify write access to collateral save directory
                                if (not os.access(os.environ.get('HTD_COLLATERALS_SAVED_IMAGE'), os.W_OK)):
                                    htdte_logger.error((
                                        "Trying to compile dictionary - \"%s\" (signed in TE_cfg "
                                        "as compiled) in not-writable directory: %s") % (
                                        dictionary, os.environ.get('HTD_COLLATERALS_SAVED_IMAGE')))
                        else:
                            # This collateral doesn't need to be compiled to disk, so release the lock
                            lock_obj[picklefile].release()
                            htdte_logger.inform(("[%s] Released lock, no need to compile %s") % (
                                time.ctime(), os.path.basename(picklefile)))
                # collect the list of gzipped file that need to be removed
                if ("gzip" in list(self.collaterals_list[current_col_name].keys())
                        and self.collaterals_list[current_col_name]["gzip"] == 1):
                    gzipped_file_l.append(self.collaterals_list[current_col_name]["path"])

            # ------------------------
            for dictionary in self.te_cfg_col_order:
                if (dictionary in exclude_list):
                    continue
                if (dictionary in not_saved_dictionaries):
                    res = {}
                    col_names = []

                    # ---Processing each dictionary
                    for dict_entity in self.te_cfg_col[dictionary]:
                        for coll in dict_entity["collateral"]:
                            coll_name = coll
                            col_names.append(coll_name)
                            # -----------------------
                            htdte_logger.inform(
                                ("Processing  dictionary -\"%s\" collateral-\"%s\" ....") % (dictionary, coll_name))

                            # --------------
                            start_time = datetime.datetime.now()
                            if (self.collaterals_list[coll_name]["type"] == "xml"):
                                self.parse_xml_dictionary(coll_name, dictionary, dict_entity, res)
                            elif (self.collaterals_list[coll_name]["type"] == "csv"):
                                res = util_merge_dictionaries(res, util_merge_dictionaries(res,
                                                                                           self.processing_csv_collateral(
                                                                                               dictionary, coll_name,
                                                                                               dict_entity)))
                            elif (self.collaterals_list[coll_name]["type"] == "tab"):
                                res = util_merge_dictionaries(res, util_merge_dictionaries(res,
                                                                                           self.processing_tabular_text_collateral(
                                                                                               dictionary, coll_name,
                                                                                               dict_entity)))
                            elif (self.collaterals_list[coll_name]["type"] == "user"):
                                res1 = self.processing_user_regexp_collateral(dictionary, coll_name, dict_entity)
                                res = util_merge_dictionaries(res, res1)
                            else:
                                htdte_logger.error(
                                    (
                                        "Not supported collateral type - \"%s\" required by collateraldef -\"%s\"  ....")
                                    % (
                                        self.collaterals_list[coll_name]["type"], coll_name))
                            htdte_logger.inform(("Processing  dictionary -\"%s\" collateral -\"%s\" time: %s ....") % (
                                dictionary, coll_name, str(datetime.datetime.now() - start_time)))
                    # ---end for dict_entity in  self.te_cfg_col[dictionary]----------
                    self.dictionaries_list[dictionary] = res
                    # ----------Executing post processing functors---
                    debug_mode = ("debug" in dict_entity and (dict_entity["debug"] in HTD_True_Statement))
                    self.post_processing_functors(dictionary, dict_entity, self.dictionaries_list[dictionary],
                                                  debug_mode)

                    htdte_logger.inform(("Total dictionary -\"%s\" processing time: %s ....") % (
                        dictionary, str(datetime.datetime.now() - start_time)))
                    # -----end of for dictionary in self.te_cfg_col_order:
                    if (debug_mode):
                        util_print_dict(res)
                    if dict_entity.get("compile") in HTD_True_Statement:
                        dict_definition_crc = self.get_dict_definition_crc(dictionary)
                        picklefile = self.get_col_pickle_name(col_names, dictionary, base_crc=dict_definition_crc)
                        if self.CFG.get("INFO", {}).get("compress_collaterals") in HTD_True_Statement:
                            with bz2.open(picklefile + ".bz2", 'wt', encoding="ascii") as zipfile:
                                htd_compress.dump(self.dictionaries_list[dictionary], zipfile)
                        else:
                            htd_compress.dump(self.dictionaries_list[dictionary], open(picklefile, "w"))
                        self.write_col_pickle_info(col_names, dictionary, self.dictionaries_list[dictionary])

                        lock_obj[picklefile].release()
                        htdte_logger.inform(
                            ("[%s] Released lock, done generating %s") % (time.ctime(), os.path.basename(picklefile)))
        finally:
            for lock in lock_obj.values():
                if lock.is_locked:
                    lock.release(force=True)
                    htdte_logger.warn(
                        ("[%s] WARNING: forcing release of lock of %s!") % (time.ctime(), os.path.basename(picklefile)))

        # remove temp files
        for gzip_file in gzipped_file_l:
            htdte_logger.inform("Deleting temporary collaterals file %s" % (gzip_file))
            os.remove(gzip_file)

    # ---------------------------
    #
    # --------------------------
    def traverse_single_xml_node(self, parent_node, key, xmlcfg, xml_hash, col_tag, col_type):
        node_l, val = self.read_combined_xml_cfg_value(xmlcfg["attributes"][key])
        nextKeyNode = self.traverse_node_path(parent_node, node_l, 0)
        if (nextKeyNode.childNodes[0].nodeType != nextKeyNode.childNodes[0].TEXT_NODE):
            htdte_logger.error((
                " Expected Tesxt Node type while received type- %d for node-\"%s\" te_cfg_col["
                "\"%s\"][\"%s\"]  ....") % (
                nextKeyNode.nodeType, parent_node, col_tag, col_type))
        nodeKeyVal = nextKeyNode.childNodes[0].data.replace(" ", "")
        if (nodeKeyVal in list(xml_hash.keys())):
            htdte_logger.error(
                (" Duplicated Key node value- %s found for Node - %s  te_cfg_col[\"%s\"][\"%s\"]  ....") % (
                    nodeKeyVal, nextKeyNode.nodeType, parent_node, col_tag, col_type))
        if (key not in xml_hash):
            xml_hash[key] = {}
        xml_hash[key][nodeKeyVal] = {}
        self.traverse_xml_entry(parent_node, col_tag, col_type, xmlcfg, xml_hash[key][nodeKeyVal])

    # ---------------------------
    #
    # --------------------------
    def traverse_xml_entry(self, parent_node, col_tag, col_type, xmlcfg, xml_hash):
        for entry in list(xmlcfg.keys()):
            if (isinstance(xmlcfg[entry], dict)):
                # --More then one entry is expected--
                if ("node" not in list(xmlcfg[entry].keys())):
                    htdte_logger.error(
                        (" Missing \"node\" attribute in node-\"%s\" -  te_cfg_col[\"%s\"][\"%s\"]  ....") % (
                            entry, col_tag, col_type))
                node_l, val = self.read_combined_xml_cfg_value(xmlcfg[entry]["node"])
                # --The multiple XML subtries are indexed by attribute properties
                if ("attributes" not in list(xmlcfg[entry].keys())):
                    htdte_logger.error(
                        (" Missing \"attribute\" attribute for node-\"%s\" te_cfg_col[\"%s\"][\"%s\"]  ....") % (
                            entry, col_tag, col_type))
                nodes_ptr = self.traverse_node_path(parent_node, node_l, 0)
                if (not re.match(r"<class\s+'xml.dom.minicompat.NodeList'>", str(type(nodes_ptr)))):
                    for key in list(xmlcfg[entry]["attributes"].keys()):
                        if (key not in ["node", "filter"]):
                            self.traverse_single_xml_node(nodes_ptr, key, xmlcfg[entry], xml_hash, col_tag, col_type)
                else:
                    for key in list(xmlcfg[entry]["attributes"].keys()):
                        if (key not in ["node", "FilterIn", "FilterOut"]):
                            for node in nodes_ptr:
                                self.traverse_single_xml_node(node, key, xmlcfg[entry], xml_hash, col_tag, col_type)
                                # -----------------
            else:
                if (entry not in ["node", "FilterIn", "FilterOut"]):
                    node_l, val = self.read_combined_xml_cfg_value(xmlcfg[entry])
                    xml_hash[entry] = self.get_combined_xml_value(parent_node, node_l)

    # ---------------------
    def findChildNodesByName(self, parent, name, err=1):
        res = [x for x in parent.childNodes if (x.nodeType == x.ELEMENT_NODE and x.localName == name)]
        if (len(res) < 1 and err and not name[0] == '?'):
            htdte_logger.error((" Can't find child node \"%s\" from parent \"%s\" node : \n%s....") % (
                name, parent.localName, self.get_xml_tree_str(parent)))
        return res

    # ------------------------
    def findChildNodeByName(self, parent, name, err=1):
        for node in parent.childNodes:
            if node.nodeType == node.ELEMENT_NODE and node.localName == name:
                return node
        if (err):
            htdte_logger.error((" Can't find child node \"%s\" from parent \"%s\" node : %s....") % (
                name, parent.localName, self.get_xml_tree_str(parent)))
        return None

    # --------------
    def getChildNodeValByName(self, parent, name, err=1):
        rc = []
        node = self.findChildNodeByName(parent, name, err)
        for node in node.childNodes:
            if node.nodeType == node.TEXT_NODE:
                rc.append(node.data)
        return ''.join(rc)

    # --------------------------------------------------
    # Get XML tree from a node
    # --------------------------------------------------
    def get_xml_tree_str(self, node, indentationLevel=0):
        res = indentationLevel * ' ' + (node.tagName if hasattr(node, ("tagName")) else "")
        # print node.firstChild.data
        for child in node.childNodes:
            if child.nodeType == child.TEXT_NODE:
                res = res + "->" + child.data
            if child.nodeType == child.ELEMENT_NODE:
                res = res + self.get_xml_tree_str(child, indentationLevel + 4)

        res = (res[:200] + '..') if len(res) > 75 else res
        return res

    # ----------------------------------------------------------------------------
    # This method used to create a string - dynamic methods to access CFG portion and
    #     dynamic methods to access dictionary portion
    # ----------------------------------------------------------------------------
    def create_dynamic_methods_module(self, file_name):
        fh = open(file_name, 'w')
        frame, filename, line_number, function_name, lines, index = inspect.stack()[1]
        obj_prefix = ""
        match = re.match(r".+[\(\) =]([A-z0-9_]+)\.create_dynamic_methods_module", lines[index])
        if (match):
            obj_prefix = ("%s.") % (match.groups()[0])
            fh.write(("from htd_collaterals import %s\n") % (match.groups()[0]))

        res = "from htd_utilities import * \n"
        # --------------------------------------
        for cat in list(self.CFG.keys()):
            if (cat not in self.__defined_dynamicaly_methods):
                self.__defined_dynamicaly_methods.append(cat)
                res = ("%s\ndef cfg_%s(var,err=1):") % (res, cat)
                res = ("%s\n if(var not in %sCFG[\"%s\"].keys()):") % (res, obj_prefix, cat)
                res = ("%s\n  if(err):") % (res)
                res = (
                    "%s\n   htdte_logger.error((\"Trying to access not existent CFG[\\\"%s\\\"] variable - %s .\\n\\tPls. define it by TE_cfg.xml , external cfg file by command line: -load_cfg <path to cfg xml file, or direct comman line assignment -CFG:<category>:<variable> <value>  .\\n\\tAvailable variables in this category are : %s\")%s(var,%sCFG[\"%s\"].keys()))") % (
                    res, cat, "\\\"%s\\\"", "\\\"%s\\\"", "%", obj_prefix, cat)
                res = ("%s\n  else:") % (res)
                res = ("%s\n   return \"-1\"") % (res)
                res = ("%s\n if(type(%sCFG[\"%s\"][var])==dict):") % (res, obj_prefix, cat)
                res = ("%s\n   if(len(%sCFG[\"%s\"][var].keys())==1):") % (res, obj_prefix, cat)
                res = ("%s\n     return %sCFG[\"%s\"][var][%sCFG[\"%s\"][var].keys()[0]]") % (
                    res, obj_prefix, cat, obj_prefix, cat)
                res = ("%s\n   else:") % (res)
                res = ("%s\n     return %sCFG[\"%s\"][var]\n") % (res, obj_prefix, cat)
                res = ("%s\n else:") % (res)
                res = ("%s\n   return %sCFG[\"%s\"][var]\n") % (res, obj_prefix, cat)
        for col in list(self.dictionaries_list.keys()):
            if (col not in self.__col_defined_dynamicaly_methods):
                self.__col_defined_dynamicaly_methods.append(col)
                setattr(self, ("dict_%s") % (col), self.dictionaries_list[col])
                res = ("%s\ndict_%s=%sdictionaries_list[\"%s\"]") % (res, col, obj_prefix, col)
        fh.write(res)
        fh.close()

    # ----------------------------------------------------------------------------
    # This method used to make verification of expected ui
    #
    # ----------------------------------------------------------------------------
    def verify_info_ui_existence(self, expected_ui):
        if (not isinstance(expected_ui, list)):
            htdte_logger.error("The - expecte_ui argument is not a list type - while expected a list of ui names.")
        for ui in expected_ui:
            try:
                l = eval(("self.%s") % (ui))
            except NameError:
                htdte_logger.error((
                    "Missing \"%s\" - user interface object , should be defined in  TE_cfg.xml and used by accessing to collaterals by actions. "))
