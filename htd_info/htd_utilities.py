import os
import locale
import imp
import sys
import time
import inspect
import re
import traceback
import types
import subprocess
import getpass
import pydoc
import subprocess
from copy import deepcopy
# ----------------------------
HTD_True_Statement = [1, "1", "TRUE", "true", "True", "On", "ON", "on"]
HTD_False_Statement = [0, "0", "FALSE", "false", "False", "Off", "OFF"]
HTD_Cfgs_Cmd_Override = {}
TE_Cfg_override = ""
HTD_Cfg_Up = 0
HTD_subroccesses_pid_tracker_list = []
# structure HTD_Classes_Help["class_name"]["method_name"]["description"]
# and HTD_Classes_Help["class_name"]["method_name"]["prototype"]
HTD_Classes_Help = {}

############## more functionality moved by orubin ####################


def add_class_help_description(class_name, method_name, description, prototype):
    res_str = ""
    res_str += '<tr bgcolor="00FC00" align="left"><th><td nowrap>' + prototype + \
        "</td></th><th><td nowrap>" + description + "</td></th></tr>\n"
    return res_str
# ---------------------------------------------------------------------
# Gets the list of available slices
# ---------------------------------------------------------------------


def util_get_slices_list():
    # workaround for now
    if ("emu" in os.environ.get("CLUSTER_NAME") or "emu" in os.environ.get("DUT")):
        return [0, 1]
    if ("_dc" in os.environ.get("MODEL_ROOT")):
        return [0, 1]
    else:
        return [0]

# ----------------------------------------------------------------------
# Find a maximal msb bit-1 and return a mask from [found msb bit :0]
# ----------------------------------------------------------------------


def util_calculate_range_mask(val, subrange_lsb=-1, subrange_msb=-1):
    bit_pos = 0
    calc_val = val
    while calc_val != 0:
        calc_val = calc_val >> 1
        bit_pos += 1
    if(subrange_lsb < 0):
        return pow(2, bit_pos) - 1
    if(subrange_msb < 0):
        return (pow(2, bit_pos) - 1) >> subrange_lsb
    return (util_get_int_sub_range(subrange_lsb, subrange_msb, (pow(2, bit_pos) - 1)))
# ----------------------------------------------------------------------
# gets the check sum of a file
# ----------------------------------------------------------------------


def util_get_cksum(path):
    cksum_cmd = ("/usr/bin/cksum %s") % (path)
    # array - first is status, 2nd is result
    cksum_result = subprocess.getstatusoutput(cksum_cmd)
    if (cksum_result[0] is not 0):
        htdte_logger.error(("Fail to run UNIX checksum command:%s\n%s...") % (
            cksum_cmd, cksum_result[1]))
    crc = int(cksum_result[1].split(" ")[0])
    return crc

# ----------------------------------------------------------------------
# gets a temporary directory name according to user name
# ----------------------------------------------------------------------


def util_get_temp_dir_name(self, postfix="htd_te"):
    return ("/tmp/%s_%s_%s") % (getpass.getuser(), str(os.getpid()), postfix)

# ----------------------------------------------------------------------
# Search $<ENV> token in string and rplace it by UNIOC ENV value
# ----------------------------------------------------------------------


def util_resolve_unix_env(val, message_postfix=""):
    str_val = val
    all_env_l = re.findall(r"\$(\w+)", str_val)
    for env in all_env_l:
        if (os.environ.get(env) is None):
            if (os.getenv("HTD_TE_CFG_ENV_ONLY", "0") == "0"):
                htdte_logger.error(
                    ("Wrong environment reference $%s used in token: \"%s\".%s...") % (env, str_val, message_postfix))
            else:
                htdte_logger.inform("env %s do not exist" % (env))
                return ""
        str_val = str_val.replace(("$%s") % (env), os.getenv(env, ""))
    return str_val


# ----------------------------------------------------------------------
# gets integer value
# ----------------------------------------------------------------------
# Declare these helper regex objects outside the function so they only get compiled once
# This function is called MANY times and compiling these each time was
# causing unnecessary slowness.
hex_h = re.compile(r"^\d+'?h([A-Fa-f0-9_]+)$")
hex_x = re.compile(r"^\d+'?x([A-Fa-f0-9_]+)$")
bin_b = re.compile(r"^(\d+)?'?b([0-1_]+)$")
dec = re.compile(r"^\d+$")
neg = re.compile(r"^-\s*(\d+)$")
dec_d = re.compile(r"^\d*'?d([0-9]+)")
float_p = re.compile(r"^\d*\.\d+$")

#########################################################################
# A NOTE TO ANYONE DEBUGGING AN ISSUE CAUSED BY THIS CODE...
#
# Cascade saw the following issue with this code in 17ww36
# 1. In our TE_cfg, as in a lot of products, we have a dictionary
#    definition called pcode_labels_constants which is defined as a
#    regmatch dictionary matching a label followed by a pcode address
#    (e.g. I31d3) on a different line.
#
# 2. When the htd_collaterals_parser matches a label and address in the
#    pcode lst file it sends the values through this function to
#    convert any numbers to int for easier manipulation inside Pacman.
#    Note that the value received by this function does not include
#    the leading I on the address (e.g. 31d3)
#
# 3. For a lot of addresses this is fine, but on CNL G0 pcode changed
#    slightly and the address 31d3 started being processed by this func.
#    31d3 actually matches the dec_d regex above and so this function
#    would actually strip off the 31d as being part of the dec number
#    definition and return a value of 3 as the int value.
#
# 4. Some of our tests that reference the PCODE label address values
#    now received an incorrect address and the test would fail.
#
#
# RESOLUTION:
# - A first attempt at fixing the issue was made by including the I with
#   the address that was passed into this function and adding a case
#   to this function to handle I[0-9a-f]+. This caused unforseen issues with
#   crif file parsing as all crif values are also passed into this
#   function. A field called 'IC' was being sent into this function from
#   a crif file and would match the new regex and only 'C' would be
#   returned which caused further issues.  This change was revertted!
#
# - A final solution was implemented that added a feature to regmatch
#   dictionary parsing that allows us to replace the matched value
#   with a different one. See the git log on commit 60cd97de4e for full
#   details.
#
#########################################################################


def util_get_int_value(value):
    if (type(value) in [int, int]):
        return (1, value)
    val = 0
    if (hex_h.match(value)):
        match = hex_h.match(value)
        value = match.groups()[0].replace("_", "", 1000)
        val = int("0x%s" % (value), 16)
    elif (hex_x.match(value)):
        match = hex_x.match(value)
        value = match.groups()[0].replace("_", "", 1000)
        val = int("0x%s" % (value), 16)
    elif (bin_b.match(value)):
        match = bin_b.match(value)
        value = match.groups()[1].replace("_", "", 1000)
        val = int(value, 2)
    elif (dec.match(value)):
        val = int(value)
    elif (neg.match(value)):
        match = neg.match(value)
        val = int(match.groups()[0], 10) * (-1)
    elif (dec_d.match(value)):
        match = dec_d.match(value)
        val = int(match.groups()[0], 10)
    elif (float_p.match(value)):
        val = float(value)
    else:
        return (0, 0)
    return (1, val)


# ----------------------------------------------------------------------
# merge dictionaries
# ----------------------------------------------------------------------


def util_merge_dictionaries(a, b):
    if isinstance(b, dict) and isinstance(a, dict):
        a_and_b = a.keys() & b.keys()
        every_key = a.keys() | b.keys()
        return {k: util_merge_dictionaries(a[k], b[k]) if k in a_and_b else
                deepcopy(a[k] if k in a else b[k]) for k in every_key}
    elif isinstance(b, list) and isinstance(a, list):
        return deepcopy(list(set(a + b)))
    return deepcopy(b)

# ----------------------------------------------------------------------
# gets max dictionary depth and keys number
# ----------------------------------------------------------------------


def util_get_max_dict_depth_and_keys_num(dictionary, depth=0, max_depth=0, keys_num=0):
    accamulated_keys_num = 0
    for key, value in dictionary.items():
        if isinstance(value, dict):
            (curr_depth, accamulated_keys_num) = util_get_max_dict_depth_and_keys_num(value, depth + 1, max_depth,
                                                                                      keys_num)
        else:
            curr_depth = depth + 1
            accamulated_keys_num = 0
        if (curr_depth > max_depth):
            max_depth = curr_depth
    keys_num += len(list(dictionary.keys()))
    return (max_depth, keys_num)

# ----------------------------------------------------------------------
# Print nested dictionary content in html table format
# ----------------------------------------------------------------------


def util_get_dict_depth(dictionary, depth=0, max_depth=0):
    """ Recursively prints nested dictionaries."""
    for key, value in dictionary.items():
        if isinstance(value, dict):
            curr_depth = util_get_dict_depth(value, depth + 1, max_depth)
        else:
            curr_depth = depth + 1
        if (curr_depth > max_depth):
            max_depth = curr_depth
    return max_depth

# ----------------------------------------------------------------------
# Prints dictionary HTML table
# ----------------------------------------------------------------------


def util_print_dict_html_table(dictionary, html_file, level=0, hierarchy=""):
    """ Recursively prints nested dictionaries."""
    # html_file.write('<tr>\n')
    first = True
    key_val_mode = True if (level == 0) else False
    # check if this is key->value format type
    if (level == 0):
        for key, value in dictionary.items():
            if (isinstance(value, dict)):
                key_val_mode = False
                break
    # ------Key->Value mode--------------------------
    if (key_val_mode):
        html_file.write(
            '<tr  bgcolor="blue" align="left"><th><font color="white"> Key(Key->Value format)</font></th><th><font color="white"> Value</font></th></tr>\n')
        for key, value in dictionary.items():
            # There is key->value format type
            if (type(value) in [int, int]):
                html_file.write(
                    '<tr  align="left"><th>%s</th><th>%s(0x%x)</th></tr>\n' % (key, value, value))
            else:
                html_file.write(
                    '<tr  align="left"><th>%s</th><th>%s</th></tr>\n' % (key, value))
        return
    else:
        # --Non Key->Value mode-----
        html_file.write('<ul>')
        first = True
        for key, value in dictionary.items():
            if not isinstance(value, dict):
                html_file.write('<li>%s = %s         <i><font color="gray">%s</font><i>\n' % (
                    key, value, ("%s[\"%s\"]") % (hierarchy, key)))
        for key, value in dictionary.items():
            if isinstance(value, dict):
                if (level == 0):
                    html_file.write('<a name="%s"></a>\n' % (key))
                html_file.write('<li>%s\n' % (key))
                util_print_dict_html_table(
                    value, html_file, level + 1, ("%s[\"%s\"]") % (hierarchy, key))

        html_file.write('</ul>\n')
        return

# ----------------------------------------------------------------------
# Print nested dictionary content
# ----------------------------------------------------------------------


def util_print_dict(dictionary, ident='', braces=1, stream=None):
    """ Recursively prints nested dictionaries."""
    for key, value in dictionary.items():
        if isinstance(value, dict):
            if (stream is not None):
                stream.write('%s%s%s%s\n' % (ident, braces * ' ', key, '->'))
            else:
                htdte_logger.inform('%s%s%s%s' %
                                    (ident, braces * ' ', key, '->'))
            util_print_dict(value, ident + '  ', braces + 1, stream)
        else:
            if (stream is not None):
                stream.write('%s%s%s = %s\n' %
                             (ident, braces * ' ', key, value))
            else:
                htdte_logger.inform('%s%s%s = %s' %
                                    (ident, braces * ' ', key, value))

# ----------------------------------------------------------------------
# Convert integer to binary string
# ----------------------------------------------------------------------


def util_int_to_binstr(i, size, lsb_pad=False):
    if (i < 0):
        htdte_logger.error(
            ("Can't convert negative value %d to binary string ") % (i))
    if (type(i) in [str, str]):
        i = int(i, 2)
    if i == 0:
        return ("0" * size)
    s = ''
    while i:
        if i & 1 == 1:
            s = "1" + s
        else:
            s = "0" + s
        i >>= 1
    compl_str = ""
    if (len(s) < size):
        compl_str = ("0" * (size - len(s)))

    if (lsb_pad):
        return ("%s%s") % (s, compl_str)

    return ("%s%s") % (compl_str, s)

# ----------------------------------------------------
# Resize list , filling by given item, left or right
# ------------------------------------------------------


def util_list_resize(list_src, size, item, up_direct=1, increase_only=1):
    if (len(list_src) > size and increase_only):
        return list_src
    elif (len(list_src) > size and (not increase_only)):
        return list_src[0:size]
    elif (len(list_src) == size):
        return list_src
    else:
        new_list = []
        if (up_direct):
            for i in range(0, len(list_src) - 1):
                new_list.append(list_src[i])
            for i in range(len(list_src), size - 1):
                new_list.append(item)
        else:
            for i in range(0, size - len(list_src)):
                new_list.append(item)
            for i in range(size - len(list_src) + 1, size):
                new_list.append(list_src[i - size + len(list_src) - 1])
        return new_list

# ----------------------------------------------------
# Reduce a bit range in int value
# ------------------------------------------------------


def util_get_int_sub_range(lsb, msb, orig_val):
    if (not isinstance(orig_val, int) and not isinstance(orig_val, int)):
        htdte_logger.error(
            ("Expected integer value , while got - %s.") % (type(orig_val)))
    bin_str = "{0:b}".format(orig_val)
    if(lsb > 0):
        reduced_range = bin_str[-(msb + 1):-(lsb)]
    else:
        reduced_range = bin_str[-(msb + 1):]
    return int(reduced_range, 2) if(reduced_range != "") else 0

# -----------------------------------------------
# Retrieve the class members of basic types
# ----------------------------------------------


def util_retrieve_obj_members(obj):
    res = {}
    attrs = []
    for slot in dir(obj):
        attr = getattr(obj, slot)
        if ((slot not in ['__class__', '__doc__', '__module__']) and (type(attr) in [int, str, bool])):
            res[slot] = attr
    return res

# --------------------------------------------------
# Formatting location information to file and line no
# --------------------------------------------------


def util_format_sorce_location_info(src_info):
    _path_tokens = src_info[0].split('/')
    location_file_str = _path_tokens[len(_path_tokens) - 1]
    location_file_lineno = src_info[1]
    return location_file_str, location_file_lineno

# ------------------------------
# executes all flows in module
# ------------------------------


def util_execute_all_flow_in_module(flow_obj, module_obj, module_name):
    flow_class = None
    htdte_logger.inform(
        ("---------Running %s.flow_run() ------------") % (module_name))
    for name, obj in inspect.getmembers(module_obj):
        if (obj is not None):
            getattr(module_obj, "flow_run")(flow_obj)
            return
    htdte_logger.error(
        " Can't find a flow_run method in  dynamically loaded model  ")

# ---------------------------------------------------
# this function dynamically loads an external module
# ---------------------------------------------------


def util_dynamic_load_external_module(module_path):
    path, fname = os.path.split(module_path)
    mname, ext = os.path.splitext(fname)
    no_ext = os.path.join(path, mname)
    if os.path.exists(no_ext + '.py'):
        htdte_logger.inform(
            ("Dynamic Loading external library %s...") % (module_path))
        py_mod = imp.load_source(mname, no_ext + '.py')
        return 1, mname, py_mod
    elif os.path.exists(no_ext + '.pac'):  # Vault doesn't like .py extension.
        htdte_logger.inform(
            ("Dynamic Loading external library %s...") % (module_path))
        py_mod = imp.load_source(mname, no_ext + '.pac')
        return 1, mname, py_mod
    else:
        htdte_logger.error(
            ("Attempting to load not existent module- \"%s\" ") % (module_path))
        return 1, "", __thismodule__

# ---------------------------------------------------
# get class method names
# ---------------------------------------------------


def util_get_class_method_names(obj, postfix=""):
    methods = dir(obj)
    res = []
    for m in methods:
        if (not re.match("^_", m)):
            res.append(("%s%s") % (m, postfix))
    return res

# ---------------------------------------------------
# iter subclasses names
# ---------------------------------------------------


def util_itersubclasses_names(cls, _seen=None):
    subclasses = []
    for cls in util_itersubclasses(cls):
        subclasses.append(cls.__name__)
    return subclasses


# ------------------------
HelpListStreamEnum_functions_only = 1
HelpListStreamEnum_all = 2
HelpListStreamEnum_data_only = 3


class HelpListStream:

    def __init__(self):
        self.data = []

    def write(self, s):
        self.data.append(s)

    def print_html(self, file_pt, mode=HelpListStreamEnum_functions_only):
        if (mode == HelpListStreamEnum_functions_only):
            func_help_l = '\n'.join(self.data).split("\nDATA\n")[0].split("Data descriptors defined here")[0].split(
                "\n")
        elif (mode == HelpListStreamEnum_data_only):
            func_help_l = '\n'.join(self.data).split("\nDATA\n")[1].split("Data descriptors defined here")[0].split(
                "\n")
        else:
            func_help_l = '\n'.join(self.data).split("\n")
        file_pt.write(
            '<br><details>\n <summary><h3> %s </h3></summary>\n' % (func_help_l[0]))
        for i in range(1, len(func_help_l) - 1):
            file_pt.write('<p> %s </p>' % (func_help_l[i]))
        file_pt.write('</details>')


def util_get_methods_prototypes_of_class(name_fo_class):
    sys.stdout = x = HelpListStream()
    pydoc.help(name_fo_class)
    sys.stdout = sys.__stdout__
    return x


def util_grep_file_classes(file_name):
    classes_found = []
    grep_cmd = "grep class %s" % (file_name)
    grep_process = subprocess.Popen(
        grep_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    for grep_line in iter(grep_process.stdout.readline, b''):
        grep_line = grep_line.decode().lstrip()
        if (grep_line.startswith("class")):
            grep_info = grep_line.split()
            class_name_index = grep_info[1].find("(")
            if (class_name_index > 0):
                classes_found.append(grep_info[1][:class_name_index])
    grep_process.wait()
    return classes_found

# -----------Caller extract


def util_itersubclasses(cls, _seen=None):
    """
    itersubclasses(cls)

    Generator over all subclasses of a given class, in depth first order.

    >>> list(itersubclasses(int)) == [bool]
    True
    >>> class A(object): pass
    >>> class B(A): pass
    >>> class C(A): pass
    >>> class D(B,C): pass
    >>> class E(D): pass
    >>>
    >>> for cls in itersubclasses(A):
    ...     print(cls.__name__)
    B
    D
    E
    C
    >>> # get ALL (new-style) classes currently defined
    >>> [cls.__name__ for cls in itersubclasses(object)] #doctest: +ELLIPSIS
    ['type', ...'tuple', ...]
    """

    if not isinstance(cls, type):
        raise TypeError('itersubclasses must be called with '
                        'new-style classes, not %.100r' % cls)
    if _seen is None:
        _seen = set()
    try:
        subs = cls.__subclasses__()
    except TypeError:  # fails only when cls is type
        subs = cls.__subclasses__(cls)
    for sub in subs:
        if sub not in _seen:
            _seen.add(sub)
            yield sub
            for sub in util_itersubclasses(sub, _seen):
                yield sub


# -----------Caller extract
def caller_name(skip=2):
    """Get a name of a caller in the format module.class.method

       `skip` specifies how many levels of stack to skip while getting caller
       name. skip=1 means "who calls me", skip=2 "who calls my caller" etc.

       An empty string is returned if skipped levels exceed stack height
    """
    stack = inspect.stack()
    start = 0 + skip
    if len(stack) < start + 1:
        return ''
    parentframe = stack[start][0]

    name = []
    module = inspect.getmodule(parentframe)
    # `modname` can be None when frame is executed directly in console
    # TODO(techtonik): consider using __main__
    if module:
        name.append(module.__name__)
    # detect classname
    if 'self' in parentframe.f_locals:
        # I don't know any way to detect call from the object method
        # XXX: there seems to be no way to detect static method call - it will
        #      be just a function call
        name.append(parentframe.f_locals['self'].__class__.__name__)
    codename = parentframe.f_code.co_name
    if codename != '<module>':  # top level usually
        name.append(codename)  # function or a method
    del parentframe
    return ".".join(name)


def env_group_check(site=None):
    if site is None:
        p = subprocess.Popen('groups', stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE, shell=True)
        out, err = p.communicate()
    else:
        # The round-robin DNS for rsync.<site>.intel.com sometimes returns a bad domain, so retry if it fails.
        # Based on FM, there are only ~6 domains in the round, and is advanced once per user connecting
        # So 5 back-back retries should be sufficient, if most of the round-robin pool is alive.
        for retry in range(5):
            p = subprocess.Popen('ssh rsync.' + site + '.intel.com groups', stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE, shell=True)
            out, err = p.communicate()
            if p.returncode == 0:
                break

    print("")
    htdte_logger.inform(
        "##################################################################")
    if site is None:
        htdte_logger.inform(
            "####                    USER GROUP CHECK                      ####")
    else:
        htdte_logger.inform(
            "####               REMOTE USER GROUP CHECK:" + site + "              ####")
    htdte_logger.inform(
        "##################################################################")

    groups = out.decode().strip().split(" ")
    req_groups = os.getenv("REQUIRED_GROUPS", "").split(",")
    htdte_logger.inform("User group check - REQUIRED_GROUPS: %s" %
                        (", ".join(req_groups)))
    if site is None:
        htdte_logger.inform("User group check - USER_GROUPS: %s" %
                            (", ".join(groups)))
    else:
        htdte_logger.inform("Remote site %s User group check - USER_GROUPS: %s" %
                            (site, (", ".join(groups))))

    # Netbatch adds 1 additional group so this is actually 1 less than the max
    # allowable
    max_active_groups = 15

    # Check to see if we should error or warn
    err_on_group_check = int(os.getenv("ERROR_ON_GROUP_CHECK", "0"))

    # Put the htdte_logger into the collect all errors mode
    htdte_logger.set_collect_all_errors_mode()

    # Check if the user has more than the maximum allowable groups
    if (len(groups) > max_active_groups):
        if err_on_group_check != 0:
            htdte_logger.error(
                "User group check - Cannot have more than %d groups active. You currently have %d groups active. Please use xwashmgr to manage your active groups" % (max_active_groups, len(groups)))
        else:
            htdte_logger.warn(
                "User group check - Cannot have more than %d groups active. You currently have %d groups active. Please use xwashmgr to manage your active groups" % (max_active_groups, len(groups)))

    err_groups = []
    for req_group in req_groups:
        if req_group not in groups:
            err_groups.append(req_group)

    if len(err_groups) > 0:
        if err_on_group_check != 0:
            htdte_logger.error("User group check - Groups \"%s\" are required for this project.\nGroup(s) \"%s\" are not active in your shell. Please use xwashmgr to manage your active groups!" %
                               (", ".join(req_groups), ", ".join(err_groups)))
        else:
            htdte_logger.warn("User group check - Groups \"%s\" are required for this project.\nGroup(s) \"%s\" are not active in your shell. Please use xwashmgr to manage your active groups!" %
                              (", ".join(req_groups), ", ".join(err_groups)))

    # Put the htdte_logger back into normal mode
    htdte_logger.unset_collect_all_errors_mode()
    if (htdte_logger.has_collected_errors() > 0):
        if err_on_group_check != 0:
            htdte_logger.print_collected_errors()
            htdte_logger.error("User group check - Detected errors during env group check!",
                               err_code=LOGGER_ERROR_CODES.GROUP_CHECK)
        else:
            htdte_logger.warn(
                "User group check - Detected errors during env group check!")
    else:
        htdte_logger.inform(
            "User group check - All required user groups are active!")


def env_os_check():
    print("")
    htdte_logger.inform(
        "##################################################################")
    htdte_logger.inform(
        "####                    OS VERSION CHECK                      ####")
    htdte_logger.inform(
        "##################################################################")

    # Set error_on_os_check
    error_on_os_check = int(os.getenv("ERROR_ON_OS_CHECK", "0"))

    # Get supported OS versions
    # Have to add the filter to remove '' from the list if the env var is ""
    # to begin with.
    supported_os = [a for a in os.getenv(
        "SUPPORTED_OS", "").strip().split(",") if a != '']

    # Possible OS prefixes
    os_prefixes = ["SLES"]

    # Call the appropriate os check function
    version = None
    for prefix in os_prefixes:
        # Construct function name
        function_name = "env_get_" + prefix.lower() + "_version"

        # Get handle to the function in this module
        module = sys.modules[__name__]
        function_to_call = getattr(module, function_name, None)

        # Check if the function was actually returned
        if function_to_call is None:
            htdte_logger.warn(
                "OS Version Check - Could not find function %s to check if the os version is correct! Continuing to next supported os" % (function_name))
            continue

        # Call the function
        version = function_to_call()

        # If version is -1 then it wasn't found, not this type of OS
        if version is None:
            continue
        else:
            break

    if version is None:
        if error_on_os_check:
            htdte_logger.error(
                "OS Version Check - Could not determine what OS you are running on!", err_code=LOGGER_ERROR_CODES.OS_CHECK)
        else:
            htdte_logger.warn(
                "OS Version Check - Could not determine what OS you are running on! Skipping check...")
            return 1

    htdte_logger.inform(
        "OS Version Check - SUPPORTED OS VERSIONS: %s" % (", ".join(supported_os)))
    htdte_logger.inform("OS Version Check - CURRENT OS VERSION: %s" % (version))

    if version not in supported_os:
        if len(supported_os) > 0:
            if error_on_os_check:
                htdte_logger.error("OS Version Check - OS Version %s that you are running on is not supported for this product! The supported OS Versions are: %s!" %
                                   (version, ", ".join(supported_os)), err_code=LOGGER_ERROR_CODES.OS_CHECK)
            else:
                htdte_logger.warn(
                    "OS Version Check - OS Version %s that you are running on is not supported for this product! The supported OS Versions are: %s! This may cause unknown issues." % (version, ", ".join(supported_os)))
    else:
        htdte_logger.inform("OS Version Check - OS Version supported!")


def env_get_sles_version():
    # Get SLES version
    cmd = r"cat /etc/SuSE-release | grep VERSION | sed 's/VERSION\s*=\s*//g'"
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, shell=True)
    out, err = p.communicate()
    # Popen return bytes, str() doesn't handle bytes
    out = out.decode()
    # Check to make sure out is not ""
    if out is "" or out is None:
        return None
    else:
        return "SLES" + out.strip()


def util_toolconfig_get_tool_path(tool):
    cmd = ("ToolConfig.pl get_tool_path %s") % (tool)
    # array - first is status, 2nd is value
    result = subprocess.getstatusoutput(cmd)
    status = result[0]
    ip_root = result[1]

    if(status is not 0):
        htdte_logger.error(("Fail to execute cmd {}").format(cmd))

    htdte_logger.inform("ToolConfig path for %s: %s" % (tool, ip_root))
    return ip_root


if __name__ == '__main__':
    import doctest

    doctest.testmod(verbose=1)

# -----------Logger Class--------------
from htd_logger import *
# --------------------------------------------------------
# Create the logger instance  (wraps printMessage)
htdte_logger = Logger("htd_te_manager.log")
# -------------------------
#from htd_collaterals import *
# --------------------------
if(os.environ.get('INFO_SERVICES_ONLY_MODE') is None or os.environ.get('INFO_SERVICES_ONLY_MODE') != "1"):
    from htd_arguments_container import *
# -------------------------
# --Create Dynamic config methods---
#from collateral_dynamic_members import *
# -------------------------------------------------------------------
