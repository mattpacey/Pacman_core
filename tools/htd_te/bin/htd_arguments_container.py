import inspect
import re
import traceback
import types
import copy
from htd_logger import *
from htd_utilities import *

HTD_VALUE_DEFAULT_ACCESS = 0
HTD_VALUE_READ_ACCESS = 1
HTD_VALUE_WRITE_ACCESS = 2
HTD_VALUE_RW_ACCESS = 3
# ------------------------------------
# Class container for argument storage
# ------------------------------------
htd_action_argument_hidden_entries = ["lsb", "msb", "src"]


class htd_action_argument_entry(object):
    def __init__(self, argvalue=-1, src="", lsb=-1, msb=-1, strobe=-1, label=-1, capture=-1, mask=-1, read_val=-1, zmode=-1, xmode=-1, access_type=HTD_VALUE_DEFAULT_ACCESS, verify_arg=1, patmod_en=1, patmod_var=None):
        self.value = -1
        self.read_value = -1
        self.write_value = -1
        self.lsb = lsb
        self.msb = msb
        self.src = src
        self.patmod_en = patmod_en
        self.patmod_var = patmod_var

        self.strobe = strobe
        self.label = label
        self.capture = capture
        self.mask = mask
        self.access_type = access_type
        self.zmode = zmode
        self.xmode = xmode
        self.verify_arg = verify_arg

    def verify(self, prefix=""):
        if(self.read_value is not -1 and self.strobe is not -1):
            htdte_logger.error(("Illegal combination in mutual argument properties : read_value=%x and strobe=%d. %s ") %
                               (self.read_value, self.strobe, prefix))

    def merge(self, other_entry):
        # py2 allows comparing "None", it is considered less than any interger, even negative ones
        # py3 did not allow comparing "None", raising TypeError
        y = []
        for x in list(self.__dict__.keys()):
            if x not in htd_action_argument_hidden_entries and re.match(r"<class\s+'int'>", str(type(eval("other_entry.%s" % x)))):
                if eval(("other_entry.%s") % (x)) >= 0:
                    y.append(x)

        for k in y:
            if(eval(("self.%s") % (k)) < 0):
                exec(("self.%s=other_entry.%s") % (k, k))

    def get_properties_string(self, masked_properties=[]):
        res = ""
        delim = ""
        for k in [x for x in list(self.__dict__.keys()) if(x not in htd_action_argument_hidden_entries and x not in masked_properties)]:
            delim = ","
            val = eval('self.%s' % k)
            res += ("%s%s:%s") % (delim, k, val) if(type(val) in [str, str]) else \
                (("%s%s:%d") % (delim, k, val) if(val != -1 and isinstance(val, int)) else "")
        return res


# ------------------------------------
# Class container for general argument
# ------------------------------------
HTD_ARGUMENTS_DECLARED_ONLY = 1
HTD_ARGUMENTS_NOT_DECLARED_ONLY = 2


class htd_argument_containter(object):
    def __init__(self, declared_arguments_only_mode=0):
        self.arg_l = {}
        # self.action_src = 0
        self._declared_arguments_only_mode = declared_arguments_only_mode
        self._dual_read_write_mode = False
    # -----------------

    def enable_dual_read_write_mode(self):
        self._dual_read_write_mode = True

    def is_enabled_dual_read_write_mode(self):
        return self._dual_read_write_mode
    # ---------------------------

    def get_field_ctrl_assignment(self, argname, lsb=-1, msb=-1):
        if(argname not in self.arg_l):
            #htdte_logger.error(("(get_field_ctrl_assignment)Requested argument-%s was never defined previously by self.define().Available arguments are: %s.")%(argname,self.arg_l.keys()))
            return {}
        if(self.arg_l[argname]["declared"]):
            htdte_logger.error(("(get_field_ctrl_assignment)Trying to extract register field (%s) control info from declared argument.") % (argname))
        # -----------
        val_l = self.arg_l[argname]["val"]
        result_dict = {}
        for entry in val_l:
            if(entry.lsb < 0):
                result_dict = {"strobe": entry.strobe, "capture": entry.capture, "label": entry.label, "mask": entry.mask}
            else:
                result_dict = {}
                #htdte_logger.error(("(get_field_ctrl_assignment)Register field (%s) control is not supported for field subrange.")%(argname))
        return result_dict
    # ---------------------------

    def normalize_indexes(self, first, second):
        lsb = int(first)
        msb = int(second)
        tmp = lsb
        if(lsb > msb):
            lsb = msb
            msb = tmp
        return lsb, msb
    # --------All General arguments should be defined prior accessing------------------------------

    def declare_arg(self, argname, description, typeval, default_value="---", obligatory=0):
        known_types = ["dict", "string", "bool", "int", "none", "string_or_int", "string_or_list", "int_or_list", "string_or_int_or_list"]
        # ---Accepting as type list of strings or
        if(re.match(r"<class\s+'list'>", str(type(typeval)))):
            if(not re.match(r"<class\s+'str'>", str(type(typeval[0])))):
                #htdte_logger.error(("The argument(%s) type(%s) has an illegal value - expected types are - %s or list of strings.Called in %s")%(argname,typeval,str(known_types),loc_string))
                htdte_logger.inform("The argument %s is of type list of string" % (argname))
        else:
            if(typeval not in known_types):
                info = inspect.getframeinfo(inspect.currentframe().f_back)[0:3]
                loc_string = ("%s:%d") % (info[0], info[1])
                htdte_logger.error(("The argument(%s) type(%s) has an illegal value - expected types are - %s.Called in %s") %
                                   (argname, typeval, str(known_types), loc_string))
        # ----------------------
        self.arg_l[argname] = {"description": description, "type": typeval, "obligatory": obligatory, "assigned": 0}
        if(default_value != "---"):
            self.arg_l[argname]["default"] = default_value
        # ---Signing the argument as a declared------------------
        self.arg_l[argname]["declared"] = 1
        if "source" in list(self.arg_l.keys()):
            self.arg_l[argname]["source"] = self.arg_l["source"]['assigned']
        self.arg_l[argname]["declared"] = 1
    #----------------------

    def set_obligatory(self, argname):
        if(argname not in self.arg_l):
            info = inspect.getframeinfo(inspect.currentframe().f_back)[0:3]
            loc_string = ("%s:%d") % (info[0], info[1])
            htdte_logger.error(
                ("Trying to set undefined argument(%s) as obligatory (should be defined first as a declared).Called in %s") % (argname, loc_string))
        self.arg_l[argname]["obligatory"] = 1
    # -----------------------

    def print_html_help(self, html_file, title, add_top_of_page=True):
        ignore_column_names = ["declared", "assigned", "source"]
        full_col_list = []
        for arg in self.arg_l:
            if(self.arg_l[arg]["declared"]):
                for col in self.arg_l[arg]:
                    if(col not in ignore_column_names):
                        if(col not in full_col_list):
                            full_col_list.append(col)

        # -----------------------
        html_file.write(('<a name="%s"></a>\n') % (title.replace(" ", "_")))
        html_file.write(('<br><hr><h3> %s </h3>\n') % (title))
        html_file.write('<table border="1">\n')
        html_file.write('<tr bgcolor="blue">\n')
        html_file.write('<th><font color="white"> argument_name </font></th>\n')
        for col in full_col_list:
            html_file.write('<th><font color="white">' + col + '</font></th>\n')
        html_file.write('</tr>\n')
        #-------------------------

        final_arg_list = self.arg_l

        if "_action" in title:
            obligatory_list = []
            source_list = []
            other_list = []
            for arg in self.arg_l:
                if arg == "source":
                    continue
                if (self.arg_l[arg]["obligatory"]):
                    if (self.arg_l[arg]["source"]):
                        # Argument is obligatory and from action class
                        obligatory_list.insert(0,arg)
                    else:
                        # Argument is obligatory and from base class
                        obligatory_list.append(arg)
                elif (self.arg_l[arg]["source"]):
                    # Argument is non-obligatory and from action class
                    source_list.insert(0,arg)
                elif ("src" in self.arg_l[arg]):
                    # Argument being set in action class
                    source_list.append(arg)
                else:
                    # Other than above
                    other_list.append(arg)

            for list in source_list:
                obligatory_list.append(list)
            for list in other_list:
                obligatory_list.append(list)

            final_arg_list = obligatory_list

        for arg in final_arg_list:
            html_file.write('<tr>')
            html_file.write('<td>' + arg + '</td>\n')
            if(self.arg_l[arg]["declared"]):
                for col in full_col_list:
                    if(col != "argument"):
                        col_str = (str(self.arg_l[arg][col]) if(col in self.arg_l[arg]) else "")
                        html_file.write('<td>' + col_str + '</td>\n')
            html_file.write('<tr>\n')
        html_file.write('<table>\n')
        if (add_top_of_page):
            html_file.write('<a href="#top">Top of Page</a>\n')
 
    # -----------------------
    def print_help(self):
        htdte_logger.inform("-" * 70)
        for arg in self.arg_l:
            if(self.arg_l[arg]["declared"]):
                htdte_logger.inform(("\t%s\t-\t%s") % (arg, self.arg_l[arg]["description"]))
        htdte_logger.inform("-" * 70)
    # ------------------------

    def print_help_table(self):
        # ---Create a table of arguments---
        # 1-- Collect length of each table column
        column_width = {}
        ignore_column_names = ["declared", "assigned"]
        full_col_list = []
        for arg in self.arg_l:
            column_width["argument"] = (len(arg) if(len("argument") < len(arg)) else len("argument")) if(
                "argument" not in column_width) else (len(arg) if(len(arg) > column_width["argument"]) else column_width["argument"])
            if(self.arg_l[arg]["declared"]):
                for col in list(self.arg_l[arg].keys()):
                    if(col not in ignore_column_names):
                        if(col not in full_col_list):
                            full_col_list.append(col)
                        if(col not in column_width):
                            column_width[col] = len(col) if(len(col) >= len(str(self.arg_l[arg][col]))) else len(str(self.arg_l[arg][col]))
                        else:
                            column_width[col] = len(str(self.arg_l[arg][col])) if(
                                len(str(self.arg_l[arg][col])) > column_width[col]) else column_width[col]
        # ----------------
        table_width = 4 + column_width["argument"]  # The chars '| |'+ ' |'
        for col in column_width:
            if(col not in ignore_column_names):
                if(col != "argument"):
                    table_width = table_width + column_width[col] + 3
        # --------Print Header----------------
        htdte_logger.inform("-" * table_width)
        row_str = "| " + "argument" + (" " * (column_width["argument"] - len("argument"))) + " |"
        for col in full_col_list:
            if(col != "argument"):
                col_str = " " + col + (" " * (column_width[col] - len(col)))
                row_str = row_str + col_str + " |"
        htdte_logger.inform(row_str)
        htdte_logger.inform("-" * table_width)
        # -------Entries----------------------
        for arg in self.arg_l:
            if(self.arg_l[arg]["declared"]):
                row_str = "| " + arg + (" " * (column_width["argument"] - len(arg))) + " |"
                for col in full_col_list:
                    if(col != "argument" and (col not in ignore_column_names)):
                        col_str = (str(self.arg_l[arg][col]) if(col in list(self.arg_l[arg].keys())) else "")
                        col_str = " " + col_str + (" " * (column_width[col] - len(col_str)))
                        row_str = row_str + col_str + " |"
                htdte_logger.inform(row_str)
                htdte_logger.inform("-" * table_width)
    # ---------------------------------------------

    def keys(self):
        return list(self.arg_l.keys())

    def declared_keys(self):
        res = []
        for arg in self.arg_l:
            if(self.arg_l[arg]["declared"]):
                res.append(arg)
        return res

    def not_declared_keys(self):
        res = []
        for arg in self.arg_l:
            if(not self.arg_l[arg]["declared"]):
                res.append(arg)
        return res
    # -----------------------------------------------------------------------
    # Access tracker used to tracking dowsn if the argument was ever accessed
    # Used to verify that all command line arguments to be consumed
    # -----------------------------------------------------------------------

    def ever_accessed(self, argname):
        return self.arg_l[argname]["ever_accessed"]

    def set_accessed(self, argname):
        self.arg_l[argname]["ever_accessed"] = 1

    def argument_is_assigned(self, arg_name):
        if("assigned" in self.arg_l[arg_name]):
            return self.arg_l[arg_name]["assigned"]
        return 0
    # ------------------------------------
    # Convert string value to int based on formats:
    #   \dx<hex>,\db<bin> else decimal
    # -------------------------------------

    def get_int_from_string_val(self, val):
        if(re.search(r"^\d+x[A-Fa-f0-9]+$", val)):
            return int(val, 16)
        elif(re.search(r"^\d+b[0-1]+$", val)):
            return int(val, 2)
        elif(re.search(r"^\d+d([0-9]+)$", val)):
            m = re.search(r"^\d+d([0-9]+)$", val)
            return int(m.groups[0])
        elif(val == "STROBE"):
            return val
        else:
            return int(val)
    # ------------------------------------
    # Parse indixation in parameter
    # -----------------------------------

    def parse_argument_name_indexation(self, arg_name):
        lsb = -1
        msb = -1
        final_arg_name = re.sub(r"\s*\[[0-9:]+\]\s*$", "", arg_name)
        matchIndexes = re.match(r".+\[(\d+):(\d+)\]$", str(arg_name))
        if(matchIndexes):
            lsb, msb = self.normalize_indexes(matchIndexes.groups()[0], matchIndexes.groups()[1])
        matchIndexes = re.match(r".+\[(\d+)\]$", str(arg_name))
        if(matchIndexes):
            lsb, msb = self.normalize_indexes(matchIndexes.groups()[0], matchIndexes.groups()[0])
        return (final_arg_name, lsb, msb)
    # -------------------------
    # Matching arg_value on STROBE|CAPT|MASK|<Label>---
    # The format are : field=<int>,field="<drive_int>",field="<drive_int>|<read_int>",field="<drive_int>|<read_int>|STROBE|MASK|CAPT|<SomeLabel>"
    # --------------------------

    def parse_not_declared_argument_tokens(self, arg_name, arg_value, lsb=-1, msb=-1, read_type_argument=False, access_type=HTD_VALUE_DEFAULT_ACCESS):
        # --------------------
        # --The argname could have an argument name and idexing like ARGUMENT[2:3]---
        if(arg_name not in self.arg_l):
            self.arg_l[arg_name] = {}
        # -----------------------
        entry_obj = htd_action_argument_entry(1, "")
        # (arg_name,lsb,msb)=self.parse_argument_name_indexation(arg_name)
        entry_obj.lsb = lsb
        entry_obj.msb = msb
        entry_obj.access_type = access_type
        # ------------------------
        if (type(arg_value) in [int, int]):
            if(read_type_argument):
                exec(("entry_obj.read_value=%d") % (arg_value))
            else:
                exec(("entry_obj.value=%d") % (arg_value))
        elif(isinstance(arg_value, dict)):
            # ------------------------------
            for k in list(arg_value.keys()):
                if(k not in list(entry_obj.__dict__.keys()) or k in htd_action_argument_hidden_entries):
                    htdte_logger.error(("Trying to assign  argument-%s by illegal hash key value - {..\"%s\":\"%s\"..}.Available keys are: %s") % (
                        arg_name, k, arg_value[k], str([x for x in list(entry_obj.__dict__.keys()) if(x not in htd_action_argument_hidden_entries)])))
            # -----------------------
            for param in arg_value:
                # label attribute can't never be an integer
                if(type(arg_value[param]) in [int, int]):
                    exec(("entry_obj.%s=%d") % (param, arg_value[param]))
                elif(param != "label" and re.match("^([0-9]?)([xbd]?)[a-f0-9A-F]+$", arg_value[param])):
                    exec(("entry_obj.%s=%d") % (param, self.get_int_from_string_val(arg_value[param])))
                elif(type(arg_value[param]) in [str, str]):
                    exec(("entry_obj.%s=\"%s\"") % (param, arg_value[param]))
                else:
                    htdte_logger.error(("Trying to assign  argument-%s by illegal hash value type - {..\"%s\":\"%s\"..}.Expected (int,long,string) , received:%s") % (
                        arg_name, k, arg_value[param], type(arg_value[param])))
        # ----------------------
        elif(type(arg_value) in [str, str]):
            if(read_type_argument):
                if(re.match("^([0-9]+)b[xX]$", arg_value)):
                    exec("entry_obj.xmode=1")
                elif(re.match("^([0-9]+)b[zZ]$", arg_value)):
                    exec("entry_obj.zmode=1")
                elif(re.match("^([0-9]?)([xbd]?)[a-f0-9A-F]+$", arg_value)):
                    exec(("entry_obj.read_value=%d") % (self.get_int_from_string_val(arg_value)))
                elif(re.match("^(?=.*?[0-1])(?=.*?[X])((?![xbd]).)*$", arg_value)):
                    exec(("entry_obj.read_value=\'%s\'") % (arg_value))
                elif(arg_value in ["true", "True", "TRUE"]):
                    exec("entry_obj.read_value=1")
                elif(arg_value in ["false", "False", "FALSE"]):
                    exec("entry_obj.read_value=0")
                else:
                    htdte_logger.error(("Trying to assign  argument-%s by illegal string value - %s=\"%s\".Expected (int,long,bool)") %
                                       (arg_name, arg_name, arg_value))
            else:
                if(re.match("^([0-9]+)b[xX]$", arg_value)):
                    exec("entry_obj.xmode=1")
                elif(re.match("^([0-9]+)b[zZ]$", arg_value)):
                    exec("entry_obj.zmode=1")
                elif(re.match("^([0-9]?)([xbd]?)[a-f0-9A-F]+$", arg_value)):
                    exec(("entry_obj.value=%d") % (self.get_int_from_string_val(arg_value)))
                # DELETE THIS ELIF, only available for read mode
                elif(re.match("^(?=.*?[0-1])(?=.*?[X])((?![xbd]).)*$", arg_value)):
                    exec(("entry_obj.value=\'%s\'") % (arg_value))
                elif(arg_value in ["true", "True", "TRUE"]):
                    exec("entry_obj.value=1")
                elif(arg_value in ["false", "False", "FALSE"]):
                    exec("entry_obj.value=0")
                else:
                    htdte_logger.error(
                        ("Trying to assign  argument-%s by illegal string value - %s=\"%s\".Expected (int,long,bool,([0-9]+)bz,([0-9]+)bZ,([0-9]+)bx,([0-9]+)bX)") % (arg_name, arg_name, arg_value))
            # ------------
        else:
            htdte_logger.error(
                ("Trying to assign  argument-%s by illegal value type - %s.Found more then one non VALUE|MASK|CAPT token - assumed as a label.(Only one permitted)") % (arg_name, arg_value))

        return entry_obj

    # --------------------------------------
    # Merging the new entry om existent
    # --------------------------------------
    def insert_not_declared_argument_value(self, arg_name, src, arg_value, lsb, msb, read_type_argument=False, access_type=HTD_VALUE_DEFAULT_ACCESS):
        arg_entry = self.parse_not_declared_argument_tokens(arg_name, arg_value, lsb, msb, read_type_argument, access_type)
        arg_entry.verify()
        arg_entry.src = src
        # ------------------------
        if(arg_name not in self.arg_l):
            self.arg_l[arg_name] = {}
        if("val" not in list(self.arg_l[arg_name].keys())):
            self.arg_l[arg_name]["val"] = []
        if(type(self.arg_l[arg_name]["val"]) in [int, int]):
            self.arg_l[arg_name]["val"] = [self.arg_l[arg_name]["val"]]
        # ---Merge the new entry based on lsb-msb range
        delete_list = []
        if(len(self.arg_l[arg_name]["val"]) > 0):
            for curr in self.arg_l[arg_name]["val"]:
                # ---New value is covering the old existent
                if(arg_entry.msb < curr.lsb):  # overlaping range
                    # ---New value range is below of existent in container: just adding it
                    self.arg_l[arg_name]["val"].append(arg_entry)
                    break
                elif(arg_entry.lsb > curr.msb):  # overlaping high
                    # ---New value range is above of existent in container: just adding it
                    self.arg_l[arg_name]["val"].append(arg_entry)
                    break
                elif(arg_entry.lsb <= curr.lsb and arg_entry.msb >= curr.msb):  # equal range
                    # ---Same range: just replacing it
                    arg_entry.merge(curr)
                    delete_list.append(curr)
                    self.arg_l[arg_name]["val"].append(arg_entry)
                    break
                elif(arg_entry.lsb <= curr.lsb and arg_entry.msb <= curr.msb):  # overlaping in low part
                    #--Insert [arg_entry.lsb:curr.lsb-1], override [curr.lsb:arg_entry.msb]
                    # 1. Adding low instance
                    low_arg_entry = deepcopy(arg_entry)
                    low_arg_entry.value = util_get_int_sub_range(arg_entry.value, arg_entry.lsb, curr.lsb) if arg_entry.value >= 0 else -1
                    low_arg_entry.read_value = util_get_int_sub_range(
                        arg_entry.read_value, arg_entry.lsb, curr.lsb) if arg_entry.read_value >= 0 else -1
                    ovrlp_arg_entry = deepcopy(arg_entry)
                    ovrlp_arg_entry.merge(curr)
                    ovrlp_arg_entry.value = util_get_int_sub_range(arg_entry.value, curr.lsb + 1, arg_entry.msb) if arg_entry.value >= 0 else -1
                    ovrlp_arg_entry.read_value = util_get_int_sub_range(
                        arg_entry.read_value, curr.lsb + 1, arg_entry.msb) if arg_entry.read_value >= 0 else -1
                    high_arg_entry = deepcopy(curr)
                    if(arg_entry.msb < curr.msb):
                        high_arg_entry.value = util_get_int_sub_range(curr.value, arg_entry.msb + 1, curr.msb) if curr.value >= 0 else -1
                        high_arg_entry.read_value = util_get_int_sub_range(
                            curr.read_value, arg_entry.msb + 1, curr.msb) if curr.read_value >= 0 else -1
                    delete_list.append(curr)
                    self.arg_l[arg_name]["val"].append(low_arg_entry)
                    self.arg_l[arg_name]["val"].append(ovrlp_arg_entry)
                    if(arg_entry.msb < curr.msb):
                        self.arg_l[arg_name]["val"].append(high_arg_entry)
                    break
                elif(arg_entry.lsb > curr.lsb and arg_entry.msb >= curr.msb):  # overlaping in high part
                    low_arg_entry = deepcopy(curr)
                    low_arg_entry.value = util_get_int_sub_range(curr.value, curr.lsb, arg_entry.lsb - 1) if arg_entry.value >= 0 else -1
                    low_arg_entry.read_value = util_get_int_sub_range(
                        curr.read_value, curr.lsb, arg_entry.lsb - 1) if arg_entry.read_value >= 0 else -1
                    ovrlp_arg_entry = deepcopy(arg_entry).merge(curr)
                    ovrlp_arg_entry.value = util_get_int_sub_range(arg_entry.value, curr.lsb, curr.msb) if arg_entry.value >= 0 else -1
                    ovrlp_arg_entry.read_value = util_get_int_sub_range(arg_entry.read_value, curr.lsb, curr.msb) if arg_entry.read_value >= 0 else -1
                    high_arg_entry = deepcopy(arg_entry)
                    if(arg_entry.msb > curr.msb):
                        high_arg_entry.value = util_get_int_sub_range(arg_entry, arg_entry.msb + 1, curr.msb) if curr.value >= 0 else -1
                        high_arg_entry.read_value = util_get_int_sub_range(
                            arg_entry.read_value, arg_entry.msb + 1, curr.msb) if curr.read_value >= 0 else -1
                    delete_list.append(curr)
                    self.arg_l[arg_name]["val"].append(low_arg_entry)
                    self.arg_l[arg_name]["val"].append(ovrlp_arg_entry)
                    if(arg_entry.msb > curr.msb):
                        self.arg_l[arg_name]["val"].append(high_arg_entry)
                    break
            # end of for curr ----------------------------
            for d in delete_list:
                self.arg_l[arg_name]["val"].remove(d)
            # --end of update existent container
        else:
            self.arg_l[arg_name]["val"].append(arg_entry)
        # ------------------
        return arg_name
    # ----------------------------
    #
    # -----------------------------

    def delete_argument(self, arg_name, src="??"):
        orig_arg_name = arg_name
        is_declared_argument_reference = False
        if(re.match(r"^declared:([A-z0-9_.\[\]:]+)", arg_name)):
            is_declared_argument_reference = True
            m = re.match(r"^declared:([A-z0-9_.\[\]:]+)", arg_name)
            arg_name = m.groups()[0]
        is_not_declared_argument_reference = False
        if(re.match(r"^not_declared:([A-z0-9_.\[\]:]+)", arg_name)):
            is_not_declared_argument_reference = True
            is_declared_argument_reference = False
            m = re.match(r"^not_declared:([A-z0-9_.\[\]:]+)", arg_name)
            arg_name = m.groups()[0]
        # -------------------------------
        (arg_name, lsb, msb) = self.parse_argument_name_indexation(arg_name)
        if(arg_name not in list(self.arg_l.keys())):
            htdte_logger.warn(("Trying to delete not existent (not assigned) argument-\"%s\" (Called by %s).") % (arg_name, src))
            return
        if(lsb < 0 or msb < 0):
            del(self.arg_l[arg_name])
        else:
            htdte_logger.error(("(%s)Trying to delete argument subrange %s[%d:%d] is not supported yet (Called by %s).") % (arg_name, lsb, msb, src))
    # ----------------------------
    #
    # -----------------------------

    def change_argument_name(self, arg_name, arg_name_new, src="??"):
        orig_arg_name = arg_name
        is_declared_argument_reference = False
        if(re.match(r"^declared:([A-z0-9_.\[\]:]+)", arg_name)):
            is_declared_argument_reference = True
            m = re.match(r"^declared:([A-z0-9_.\[\]:]+)", arg_name)
            arg_name = m.groups()[0]
        is_not_declared_argument_reference = False
        if(re.match(r"^not_declared:([A-z0-9_.\[\]:]+)", arg_name)):
            is_not_declared_argument_reference = True
            is_declared_argument_reference = False
            m = re.match(r"^not_declared:([A-z0-9_.\[\]:]+)", arg_name)
            arg_name = m.groups()[0]
        # -------------------------------
        (arg_name, lsb, msb) = self.parse_argument_name_indexation(arg_name)
        if(arg_name not in list(self.arg_l.keys())):
            htdte_logger.error(("Trying to rename non-existing (not assigned) argument-\"%s\"  to %s (Called by %s).") %
                               (orig_arg_name, arg_name_new, src))
        else:
            self.arg_l[arg_name_new] = self.arg_l[arg_name]
            del(self.arg_l[arg_name])

    # ----------------------------
    #
    # -----------------------------
    def set_argument(self, arg_name, arg_value, src="", read_type_arg=False, access_type=HTD_VALUE_DEFAULT_ACCESS):
        src = re.sub(r"[A-z0-9_]*/", "", src)
        info = inspect.getframeinfo(inspect.currentframe().f_back)[0:3]
        loc_string = ("%s:%d") % (info[0], info[1])
        orig_arg_name = arg_name
        is_declared_argument_reference = False
        if(re.match(r"^declared:([A-z0-9_.\[\]:]+)", arg_name)):
            is_declared_argument_reference = True
            m = re.match(r"^declared:([A-z0-9_.\[\]:]+)", arg_name)
            arg_name = m.groups()[0]
        # -------------------------------
        is_not_declared_argument_reference = False
        if(re.match(r"^not_declared:([A-z0-9_.\[\]:]+)", arg_name)):
            is_not_declared_argument_reference = True
            is_declared_argument_reference = False
            m = re.match(r"^not_declared:([A-z0-9_.\[\]:]+)", arg_name)
            arg_name = m.groups()[0]
        # -------------------------------
        (arg_name, lsb, msb) = self.parse_argument_name_indexation(arg_name)
        if((arg_name not in list(self.arg_l.keys()) or (("declared" in list(self.arg_l[arg_name].keys())) and (not self.arg_l[arg_name]["declared"])) or is_not_declared_argument_reference) and (not is_declared_argument_reference)):
            if(self._declared_arguments_only_mode):
                htdte_logger.error(
                    ("(%s)Trying to assign undeclared argument-\"%s\" .This container allow only declared arguments usage.") % (loc_string, arg_name))
            # -------------------------------------
            self.insert_not_declared_argument_value(arg_name, src, arg_value, lsb, msb, read_type_arg, access_type)
            self.arg_l[arg_name]["declared"] = 0
            self.arg_l[arg_name]["ever_accessed"] = 0
        else:
            if(re.match(r"<class\s+'unicode'>", str(type(arg_value)))):
                arg_value = str(arg_value)
            # ---------This is declared manager/flow/action/segment  parameter - should registrated prior accessing
            self.arg_l[arg_name]["declared"] = 1
            self.arg_l[arg_name]["ever_accessed"] = 0
            self.arg_l[arg_name]["src"] = src
            # -----------------------------
            if(re.match(r"<class\s+'list'>", str(type(self.arg_l[arg_name]["type"])))):
                if(lsb > 0 or msb > 0):
                    htdte_logger.error(
                        ("(%s)Wrong argument  indexation assigned for argument-%s ,  (Could not be used for declared argument of type \"list\" - only \"int\" type is allowed for indixation in CMD)") % (loc_string, orig_arg_name))
                if(arg_value not in self.arg_l[arg_name]["type"]):
                    htdte_logger.error(("(%s)Trying to assign enumerated argument-%s by illegal value - %s.Acceptable enumerated values are: %s") %
                                       (loc_string, arg_name, arg_value, str(self.arg_l[arg_name]["type"])))
                self.arg_l[arg_name]["val"] = arg_value
            # ----------BOOL------------------
            elif(self.arg_l[arg_name]["type"] == "bool"):
                if(lsb > 0 or msb > 0):
                    htdte_logger.error(
                        ("(%s)Wrong argument  indexation assigned for argument-%s ,  (Could not be used for declared argument of type \"bool\" - only \"int\" type is allowed for indixation in CMD)") % (loc_string, orig_arg_name))
                if(re.match(r"<class\s+'int'>", str(type(arg_value)))):
                    self.arg_l[arg_name]["val"] = 1 if(arg_value > 0) else 0
                elif(re.match(r"<class\s+'bool'>", str(type(arg_value)))):
                    self.arg_l[arg_name]["val"] = 1 if(arg_value) else 0
                elif(re.match(r"<class\s+'str'>", str(type(arg_value)))):
                    arg_value = arg_value.replace(" ", "")
                    if(arg_value == "TRUE" or arg_value == "1" or arg_value == "true"):
                        self.arg_l[arg_name]["val"] = 1
                    elif(arg_value == "FALSE" or arg_value == "0" or arg_value == "false"):
                        self.arg_l[arg_name]["val"] = 0
                    else:
                        htdte_logger.error(
                            ("(%s)Wrong value -\"%s\" assigned for argument-%s , expected type is \"bool\"-[TRUE|true|0|1|false|FALSE] (Could it be missing separator \",\" in CMD)") % (loc_string, arg_value, arg_name))
                else:
                    htdte_logger.error(
                        ("(%s)Wrong value -\"%s\" assigned for argument-%s , expected type is \"bool\"-[TRUE|true|0|1|false|FALSE] (Could it be missing separator \",\"  in CMD)") % (loc_string, arg_value, arg_name))
            # ------------DICT-----------------------
            elif(self.arg_l[arg_name]["type"] == "dict"):
                if(lsb > 0 or msb > 0):
                    htdte_logger.error(
                        ("(%s)Wrong argument  indexation assigned for argument-%s ,  (Could not be used for declared argument of type \"dict\" - only \"int\" type is allowed for indixation in CMD)") % (loc_string, orig_arg_name))
                if(isinstance(arg_value, dict)):
                    self.arg_l[arg_name]["val"] = arg_value
                else:
                    htdte_logger.error(("(%s)Wrong value -\"%s\" assigned for argument-%s , expected type is \"dict\" (Could it be missing separator \",\"  in CMD)") % (
                        loc_string, str(arg_value), arg_name))
            # ------------STRING---------------------
            elif(self.arg_l[arg_name]["type"] == "string"):
                if(lsb > 0 or msb > 0):
                    htdte_logger.error(
                        ("(%s)Wrong argument  indexation assigned for argument-%s ,  (Could not be used for declared argument of type \"string\" - only \"int\" type is allowed for indixation in CMD)") % (loc_string, orig_arg_name))
                if(re.match(r"<class\s+'str'>", str(type(arg_value)))):
                    self.arg_l[arg_name]["val"] = arg_value
                    self.arg_l[arg_name]["val"] = self.arg_l[arg_name]["val"].rstrip()
                else:
                    htdte_logger.error(("(%s)Wrong value -\"%s\" assigned for argument-%s , expected type is \"string\" (Could it be missing separator \",\"  in CMD)") % (
                        loc_string, str(arg_value), arg_name))
            # -----------------------------------------
            elif(self.arg_l[arg_name]["type"] == "int"):
                # ------------------
                if(type(arg_value) in [str, str]):
                    arg_value = arg_value.replace(" ", "")
                    try:
                        arg_value = int(arg_value, 16 if re.match("^0x[A-Fa-f0-9]+", arg_value) else 2 if re.match("^0b[0-1]+", arg_value) else 10)
                    except ValueError:
                        htdte_logger.error(
                            ("(%s)Wrong value -\"%s\" assigned for argument-%s , expected type is \"integer\"-[\d+|0x[a-f0-9]]|0b[0-1]] (Could it be missing separator \",\"  in CMD)") % (loc_string, arg_value, arg_name))
                # --------------------------------------------
                if(lsb >= 0):
                    arg_value = (arg_value << lsb)
                if(self.arg_l[arg_name]["assigned"] and lsb >= 0 and msb >= 0):
                    prev_val = self.arg_l[arg_name]["val"]
                    prev_src = self.arg_l[arg_name]["src"]
                    prev_lsb = self.arg_l[arg_name]["lsb"]
                    prev_msb = self.arg_l[arg_name]["msb"]
                    # different sub range given
                    self.arg_l[arg_name]["val"] = prev_val | arg_value
                    self.arg_l[arg_name]["lsb"] = prev_lsb
                    self.arg_l[arg_name]["msb"] = msb if ("msb" not in list(self.arg_l[arg_name].keys())) else (
                        msb if(msb > self.arg_l[arg_name]["msb"]) else (self.arg_l[arg_name]["msb"]))
                else:
                    self.arg_l[arg_name]["lsb"] = lsb
                    self.arg_l[arg_name]["val"] = arg_value
                    self.arg_l[arg_name]["msb"] = msb
                if(msb > self.arg_l[arg_name]["msb"]):
                    self.arg_l[arg_name]["msb"]
            # -----------STRING_OR_INT_TYPE - adaptive type--------
            elif(self.arg_l[arg_name]["type"] == "string_or_int"):
                if(lsb > 0 or msb > 0):
                    htdte_logger.error(
                        ("(%s)Wrong argument  indexation assigned for argument-%s ,  (Could not be used for declared argument of type \"string_or_int\" - only \"int\" type is allowed for indixation in CMD)") % (loc_string, orig_arg_name))
                if(re.match(r"<class\s+'str'>", str(type(arg_value)))):
                    arg_value = arg_value.replace(" ", "")
                    try:
                        self.arg_l[arg_name]["val"] = int(arg_value)
                    except ValueError:
                        self.arg_l[arg_name]["val"] = arg_value
                elif(re.match(r"<class\s+'int'>", str(type(arg_value)))):
                    self.arg_l[arg_name]["val"] = int(arg_value)
                elif(re.match(r"<class\s+'bool'>", str(type(arg_value)))):
                    self.arg_l[arg_name]["val"] = 1 if(arg_value) else 0
                else:
                    htdte_logger.error(("(%s)Unknown argument type -\"%s\" assigned for argument-%s , expected type is \"string_or_int\"-[\d+|0x[a-f0-9]]|0b[0-1]] (Could it be missing separator \",\"  in CMD)") % (
                        loc_string, str(type(arg_value)), arg_name))
            elif(self.arg_l[arg_name]["type"] == "string_or_list"):
                if(lsb > 0 or msb > 0):
                    htdte_logger.error(
                        ("(%s)Wrong argument  indexation assigned for argument-%s ,  (Could not be used for declared argument of type \"string_or_int\" - only \"int\" type is allowed for indixation in CMD)") % (loc_string, orig_arg_name))
                if(re.match(r"<class\s+'str'>", str(type(arg_value)))):
                    arg_value = arg_value.replace(" ", "")
                    self.arg_l[arg_name]["val"] = arg_value
                elif(re.match(r"<class\s+'list'>", str(type(arg_value)))):
                    self.arg_l[arg_name]["val"] = arg_value
                else:
                    htdte_logger.error(("(%s)Unknown argument type -\"%s\" assigned for argument-%s , expected type is \"string_or_list\" (Could it be missing separator \",\"  in CMD)") % (
                        loc_string, str(type(arg_value)), arg_name))
            elif(self.arg_l[arg_name]["type"] == "int_or_list"):
                if(lsb > 0 or msb > 0):
                    htdte_logger.error(
                        ("(%s)Wrong argument  indexation assigned for argument-%s ,  (Could not be used for declared argument of type \"int_or_list\" - only \"int\" type is allowed for indixation in CMD)") % (loc_string, orig_arg_name))
                if(re.match(r"<class\s+'int'>", str(type(arg_value)))):
                    self.arg_l[arg_name]["val"] = int(arg_value)
                elif(re.match(r"<class\s+'bool'>", str(type(arg_value)))):
                    self.arg_l[arg_name]["val"] = 1 if(arg_value) else 0
                elif(re.match(r"<class\s+'list'>", str(type(arg_value)))):
                    self.arg_l[arg_name]["val"] = arg_value
                else:
                    htdte_logger.error(("(%s)Unknown argument type -\"%s\" assigned for argument-%s , expected type is \"string_or_int\"-[\d+|0x[a-f0-9]]|0b[0-1]] (Could it be missing separator \",\"  in CMD)") % (
                        loc_string, str(type(arg_value)), arg_name))
            elif(self.arg_l[arg_name]["type"] == "string_or_int_or_list"):
                if(lsb > 0 or msb > 0):
                    htdte_logger.error(
                        ("(%s)Wrong argument  indexation assigned for argument-%s ,  (Could not be used for declared argument of type \"string_or_int\" - only \"int\" type is allowed for indixation in CMD)") % (loc_string, orig_arg_name))
                if(re.match(r"<class\s+'str'>", str(type(arg_value)))):
                    arg_value = arg_value.replace(" ", "")
                    try:
                        self.arg_l[arg_name]["val"] = int(arg_value)
                    except ValueError:
                        self.arg_l[arg_name]["val"] = arg_value
                    self.arg_l[arg_name]["val"] = arg_value
                elif(re.match(r"<class\s+'int'>", str(type(arg_value)))):
                    self.arg_l[arg_name]["val"] = int(arg_value)
                elif(re.match(r"<class\s+'list'>", str(type(arg_value)))):
                    self.arg_l[arg_name]["val"] = arg_value
                else:
                    htdte_logger.error(("(%s)Unknown argument type -\"%s\" assigned for argument-%s , expected type is \"string_or_list\" (Could it be missing separator \",\"  in CMD)") % (
                        loc_string, str(type(arg_value)), arg_name))
            else:
                htdte_logger.error(("(%s)Trying to assign argument-%s - not defined type - %s.") %
                                   (loc_string, arg_name, self.arg_l[arg_name]["type"]))
        # -----------
        self.arg_l[arg_name]["assigned"] = 1
        if(is_not_declared_argument_reference or is_declared_argument_reference):
            self.arg_l[arg_name]["declaration_specified"] = 1
    # -------------------------
    # Override single argument
    # ------------------------

    def is_argument_assigned(self, arg_name):
        if(arg_name not in list(self.arg_l.keys())):
            return False
        return (self.arg_l[arg_name]["assigned"] == 1)

    # -------------------------
    # Override single argument
    # ------------------------
    def overrideSingleArgument(self, argName, value, location="", lsb=-1, msb=-1):
        info = inspect.getframeinfo(inspect.currentframe().f_back)[0:3]
        loc_string = ("%s:%d") % (info[0], info[1]) if(location == "") else location
        # ------For declared parameters it is just override , for rest is mixing ranges of list (lsb/msb)-------------------
        if(argName not in list(self.arg_l.keys())):
            htdte_logger.error(("(%s)Trying to override not existent argument-%s .") % (loc_string, arg_name))
        # --Insert new value
        self.set_argument(argName, value, location)
    # ----------------------------------------------------------

    def is_declared_argument(self, argname):
        if(argname not in list(self.arg_l.keys())):
            return 0
        return self.arg_l[argname]["declared"]
    # ----------------------------------------------------------

    def get_not_declared_arguments(self):
        res = {}
        for arg in self.arg_l:
            if(not self.arg_l[arg]["declared"]):
                res[arg] = self.arg_l[arg]
        return res
    # ----------------------------------------------------------

    def get_argument_src(self, argname, location=""):
        if(argname not in self.arg_l):
            info = inspect.getframeinfo(inspect.currentframe().f_back)[0:3]
            loc_string = ("%s:%d") % (info[0], info[1]) if(location == "") else location
            htdte_logger.error(("(%s:get_argument_src)Requested argument-%s was never defined previously by self.define().Available arguments are: %s.") %
                               (loc_string, argname, self.arg_l))
        # -----declared arguments-------
        if(self.arg_l[argname]["declared"]):
            if("val" in self.arg_l[argname]):
                return self.arg_l[argname]["src"]
            else:
                return "default assignment"
        else:
            # --This is register values - list of bit range bitmap values: type "int" or list of bitmaps
            return self.arg_l[argname]["val"][0].src
    # ----------------------------------------------------------

    def get_argument_type(self, argname, noerr=0, location=""):
        if (argname not in self.arg_l):
            if(not noerr):
                info = inspect.getframeinfo(inspect.currentframe().f_back)[0:3]
                loc_string = ("%s:%d") % (info[0], info[1]) if(location == "") else location
                htdte_logger.error(("(%s:get_argument_type)Requested argument-%s was never defined previously by self.define().Available arguments are: %s.") %
                                   (loc_string, argname, self.arg_l))
            else:
                return "N/A"
        
        if ("type" in self.arg_l[argname]):
            return self.arg_l[argname]["type"]
        else:
            if(not noerr):
                info = inspect.getframeinfo(inspect.currentframe().f_back)[0:3]
                loc_string = ("%s:%d") % (info[0], info[1]) if(location == "") else location
                htdte_logger.error(("(%s)Requested argument-%s was never assigned and has no type value .") % (loc_string, argname))
            else:
                return "N/A"

#-------------------------------------------------------------------------------------------------------------------------

    def get_argument_lsb_msb(self, argname, err=1, location=""):
        info = inspect.getframeinfo(inspect.currentframe().f_back)[0:3]
        loc_string = ("%s:%d") % (info[0], info[1]) if(location == "") else location
        if(argname not in self.arg_l):
            if(err):
                htdte_logger.error(("(%s:get_argument_src)Requested argument-%s was never defined previously by self.define().Available arguments are: %s.") %
                                   (loc_string, argname, self.arg_l))
            else:
                return (-1, -1)
        # -----declared arguments-------
        if(self.arg_l[argname]["declared"]):
            if(("lsb" in list(self.arg_l[argname].keys())) and ("msb" in self.arg_l[argname])):
                return (self.arg_l[argname]["lsb"], self.arg_l[argname]["msb"])
            else:
                return (-1, -1)
        else:
            return (-1, -1)
    # ----------------------------------------------------------

    def argument_assigned(self, arg):
        return self.arg_l[arg]["assigned"]
    # -------------------------------------

    def exists_not_declared_argument(self, argname):
        if(argname not in list(self.arg_l.keys())):
            return 0
        return self.arg_l[argname]["declared"]
    # ------------------------------------

    def get_argument(self, argname, noerr=0, location=""):
        if(argname not in self.arg_l):
            if(not noerr):
                info = inspect.getframeinfo(inspect.currentframe().f_back)[0:3]
                loc_string = ("%s:%d") % (info[0], info[1]) if(location == "") else location
                htdte_logger.error(("(%s:get_argument)Requested argument-%s was never defined previously by self.define().Available arguments are: %s.") %
                                   (loc_string, argname, self.arg_l))
            else:
                return "N/A"
        # -----declared arguments-------
        if(self.arg_l[argname]["declared"]):
            if("val" in self.arg_l[argname]):
                return self.arg_l[argname]["val"]
            elif("default" in self.arg_l[argname]):
                return self.arg_l[argname]["default"]
            else:
                if(not noerr):
                    info = inspect.getframeinfo(inspect.currentframe().f_back)[0:3]
                    loc_string = ("%s:%d") % (info[0], info[1]) if(location == "") else location
                    htdte_logger.error(("(%s)Requested argument-%s was never assigned and has no default value .") % (loc_string, argname))
                else:
                    return "N/A"
        else:
            # --This is register values - list of bit range bitmap values: type "int" or list of bitmaps
            return self.arg_l[argname]["val"]
    # ----------------------------------------

    def get_declared_argument_indexes(self, argname, noerr=0, location=""):
        info = inspect.getframeinfo(inspect.currentframe().f_back)[0:3]
        loc_string = ("%s:%d") % (info[0], info[1]) if(location == "") else location
        if(argname not in self.arg_l):
            htdte_logger.error(("(%s:get_argument)Requested argument-%s was never defined previously by self.define().Available arguments are: %s.") %
                               (loc_string, argname, self.arg_l))
        # -----declared arguments-------
        if(self.arg_l[argname]["declared"]):
            if("val" in self.arg_l[argname]):
                return (self.arg_l[argname]["lsb"], self.arg_l[argname]["msb"])
            elif("default" in self.arg_l[argname]):
                return (self.arg_l[argname]["lsb"], self.arg_l[argname]["msb"])
            else:
                if(not noerr):
                    htdte_logger.error(("(%s)Requested argument-%s was never assigned and has no default value .") % (loc_string, argname))
                else:
                    return "N/A"
        else:
            # --This is register values - list of bit range bitmap values: type "int" or list of bitmaps
            htdte_logger.error("This method is to be used for declared arguments only")
            return (-1, -1)

    # -----------------------------------------
    def is_obligatory_argument(self, argname):
        if(argname not in self.arg_l):
            info = inspect.getframeinfo(inspect.currentframe().f_back)[0:3]
            loc_string = ("%s:%d") % (info[0], info[1])
            htdte_logger.error(("(%s:is_obligatory_argument)Requested argument-%s was never defined previously by self.define().Available arguments are: %s.") %
                               (loc_string, argname, self.arg_l))
        if("obligatory" not in self.arg_l[argname]):
            return 0
        else:
            return self.arg_l[argname]["obligatory"]
    # --------------------------------------------

    def verify_obligatory_arguments(self, header, location=""):
        for arg in self.declared_keys():
            if(self.is_obligatory_argument(arg) and (not self.arg_l[arg]["assigned"])):
                info = inspect.getframeinfo(inspect.currentframe().f_back)[0:3]
                loc_string = ("%s:%d") % (info[0], info[1]) if(location == "") else location
                htdte_logger.error(("(%s)Missing obligatory argument \"%s\" in accessing %s.\n\t\t\tDescription:%s") %
                                   (loc_string, arg, header, self.arg_l[arg]["description"]))
    # --------------------------------------------

    def print_arguments(self, header=""):
        if(header == ""):
            header = "***************************************"
        htdte_logger.inform(("**********************%30s*********************************") % (header))
        for arg in sorted(self.arg_l):
            if(self.arg_l[arg]["declared"]):
                htdte_logger.inform(("     %20s       = %20s, SRC:%s") % (arg, self.get_argument(arg, 1), self.get_argument_src(arg)))
        htdte_logger.inform(("--------------------------------------------------------------------------------------------------------"))
        for arg in sorted(self.arg_l):
            if(not self.arg_l[arg]["declared"]):
                for argument_value in self.arg_l[arg]["val"]:

                    if(argument_value.lsb >= 0):
                        htdte_logger.inform(("     %80s[%d:%d] = %20s%s %s, SRC:%s") % (arg, argument_value.lsb, argument_value.msb, (("0x%x") % argument_value.value if (
                            type(argument_value.value) in [int, int] and argument_value.value != -1) else (("\'b%s") % argument_value.value if (
                                argument_value.value != -1 and isinstance(argument_value.value, str)) else "")),
                            (("read:0x%x") % argument_value.read_value if (
                                type(argument_value.read_value) in [int, int] and argument_value.read_value != -1) else (("read:\'b%s") % argument_value.read_value if (
                                    argument_value.read_value != -1 and isinstance(argument_value.read_value, str)) else "")),
                            (argument_value.get_properties_string(["value", "read_value", "msb", "lsb"])), argument_value.src))
                    else:
                        htdte_logger.inform(("     %80s       = %20s%s %s, SRC:%s") % (arg, (("0x%x") % argument_value.value if (
                            type(argument_value.value) in [int, int] and argument_value.value != -1) else (("\'b%s") % argument_value.value if (
                                argument_value.value != -1 and isinstance(argument_value.value, str)) else "")),
                            (("read:0x%x") % argument_value.read_value if (
                                type(argument_value.read_value) in [int, int] and argument_value.read_value != -1) else (("read:\'b%s") % argument_value.read_value if (
                                    argument_value.read_value != -1 and isinstance(argument_value.read_value, str)) else "")),
                            (argument_value.get_properties_string(
                                ["value", "read_value", "msb", "lsb"])),
                            argument_value.src))

        htdte_logger.inform(("********************************************************************************************************"))
    # --------------------------------------------

    def get_arguments_table(self):
        result_dict = {}
        for arg in self.arg_l:
            if(self.arg_l[arg]["declared"]):
                if(self.get_argument_src(arg) != "default assignment"):
                    result_dict[arg] = str(self.get_argument(arg, 1))
            else:
                for argument_value in self.arg_l[arg]["val"]:
                    arg_name = arg if(argument_value.lsb < 0) else ("%s[%d:%d]") % (arg, argument_value.msb, argument_value.lsb)
                    result_dict[arg_name] = ("%s%s") % ((("read:0x%x ") % argument_value.read_value if (argument_value.read_value != -1) else ""),
                                                        (("write:0x%x") % argument_value.value if (argument_value.value != -1) else ""))

        # -------------
        return result_dict
