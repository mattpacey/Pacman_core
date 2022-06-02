import re
from htd_utilities import *
from htd_te_shared import *
import datetime
#########################################################################################
# History manager - store and share actions history assignment ,
#  Manage save restore state and different output interfaces of save state (TPV/SPF...)
#  Manage blacklist - restrictions on action override
#
#########################################################################################


class htd_history_manager(object):
    # ----------------------
    def __init__(self):
        self.container = {}
        self.container["blacklist"] = {}
        self.container["tap_history"] = {}
        self.container["stf_history"] = {}
        self.container["general_param_history"] = {}

        self.special_keys = ["filesrc", "fileslineno"]
        self.HistoryManagerSaveFile = "HtdHistoryChkpt.pickle" if("chkptfile" not in CFG["TE"]) else CFG["TE"]["chkptfile"]
        self.Chkpt_file_info = ""
    # --------------------

    def get_chkpt_file_name(self): return self.HistoryManagerSaveFile

    def restore(self):
        htdte_logger.inform(("Loading the History Manager info to file: %s ...") % (self.HistoryManagerSaveFile))
        if(os.path.isfile(self.HistoryManagerSaveFile) and os.access(self.HistoryManagerSaveFile, os.R_OK)):
            self.container = pickle.load(open(self.HistoryManagerSaveFile, "rb"))
    # --------------------------------
    #
    # --------------------------------

    def load_history(self, filename):
        htdte_logger.inform(("Reloading the History Manager info to file: %s ...") % (filename))
        if(not os.path.isfile(filename) or not os.access(filename, os.R_OK)):
            htdte_logger.eror(("Can't access history checkpoint  file: %s ...") % (filename))
        self = pickle.load(open(filename, "rb"))

    def clean_history(self):
        self.container["blacklist"] = {}
        self.container["tap_history"] = {}
        self.container["stf_history"] = {}
        self.container["general_param_history"] = {}
    # --------------------------------
    # capture history/blacklist buffer
    # --------------------------------

    def __capture(self, arguments_container, indx, curr_buffer, keys_list, data_by_field=0, location_file_str="none", location_line_no=0, save_non_arg_data=0):
        if(indx >= len(keys_list)):

            if save_non_arg_data == 1:
                if (isinstance(data_by_field, dict)):
                    for key, val in data_by_field.items():
                        curr_buffer[key] = val
            else:

                for p in arguments_container.not_declared_keys():
                    if(not isinstance(data_by_field, dict) or (p not in data_by_field)):
                        val_l = arguments_container.get_argument(p)
                        curr_buffer[p] = val_l[len(val_l) - 1].value
                    else:
                        curr_buffer[p] = data_by_field[p]
            curr_buffer["filesrc"] = location_file_str
            curr_buffer["fileslineno"] = location_line_no
            return
        else:
            if(keys_list[indx] not in curr_buffer):
                curr_buffer[keys_list[indx]] = {}
            self.__capture(arguments_container, indx + 1, curr_buffer[keys_list[indx]],
                           keys_list, data_by_field, location_file_str, location_line_no, save_non_arg_data)
    # ----------------------------
    # capture history buffer
    # ----------------------------

    def history_capture(self, action_ptr, keys_list, data_by_field={}, location_file_str="none", location_file_lineno=0, container_type="tap_history", save_non_arg_data=0):
        # -------------------------------
        if (location_file_str == "none"):
            info = inspect.getframeinfo(inspect.currentframe().f_back)[0:3]
            location_file_lineno = info[1]
            _path_tokens = info[0].split('/')
            location_file_str = _path_tokens[len(_path_tokens) - 1]
        # -------------------------------------------------
        if(action_ptr.get_action_type() not in self.container[container_type]):
            self.container[container_type][action_ptr.get_action_type()] = {}
        # -------------------------------------------------
        self.__capture(action_ptr.arguments, 0, self.container[container_type][action_ptr.get_action_type(
        )], keys_list, data_by_field, location_file_str, location_file_lineno, save_non_arg_data)
    # ----------------------------
    # capture blacklist buffer
    # ----------------------------

    def blacklist_capture(self, action_ptr, keys_list, data_by_field={}, location_file_str="none", location_file_lineno=0):
        # -------------------------------
        if (location_file_str == "none"):
            info = inspect.getframeinfo(inspect.currentframe().f_back)[0:3]
            location_file_lineno = info[1]
            _path_tokens = info[0].split('/')
            location_file_str = _path_tokens[len(_path_tokens) - 1]
        # -------------------------------
        if(action_ptr.get_action_type() not in self.container["blacklist"]):
            self.container["blacklist"][action_ptr.get_action_type()] = {}
        # -------------------------------------------------
        self.__capture(action_ptr.arguments, 0, self.container["blacklist"][action_ptr.get_action_type(
        )], keys_list, data_by_field, location_file_str, location_file_lineno)
    # ----------------------------
    # capture parametric buffer
    # ----------------------------

    def __parametric_capture(self, indx, param_keys, param_value, curr_buffer, location_file_str, location_file_lineno):
        if(indx >= len(param_keys)):
            curr_buffer["val"] = param_value
            curr_buffer["filesrc"] = location_file_str
            curr_buffer["fileslineno"] = location_file_lineno
            return
        else:
            if(param_keys[indx] not in curr_buffer):
                curr_buffer[param_keys[indx]] = {}
            self.__parametric_capture(indx + 1, param_keys, param_value, curr_buffer[param_keys[indx]], location_file_str, location_file_lineno)

    def parametric_capture(self, param_type, param_keys, param_value, location_file_str="none", location_file_lineno=0):
        if (location_file_str == "none"):
            info = inspect.getframeinfo(inspect.currentframe().f_back)[0:3]
            location_file_lineno = info[1]
            _path_tokens = info[0].split('/')
            location_file_str = _path_tokens[len(_path_tokens) - 1]
        # ------------------------
        if(not isinstance(param_keys, list)):
            htdte_logger.error(
                ("Improper keys argument type - %s , (expected list of strings representing parametric table keys path) .") % (str(type(param_keys))))
        # -------------------------------
        if(param_type not in self.container["general_param_history"]):
            self.container["general_param_history"][param_type] = {}
        # ----------------------------------------------
        self.__parametric_capture(0, param_keys, param_value,
                                  self.container["general_param_history"][param_type], location_file_str, location_file_lineno)
    # --------------------------

    def _normalize_parametric_table(self, curr_buffer, location_file_str, location_file_lineno):
        for param_key in curr_buffer:
            if(not isinstance(curr_buffer[param_key], dict)):
                tmp = curr_buffer[param_key]
                curr_buffer[param_key] = {}
                curr_buffer[param_key]["val"] = tmp
                curr_buffer[param_key]["filesrc"] = location_file_str
                curr_buffer[param_key]["fileslineno"] = location_file_lineno
                return
            else:
                self._normalize_parametric_table(curr_buffer[param_key], location_file_str, location_file_lineno)

    def _unnormalize_parametric_table(self, curr_buffer):
        if(not isinstance(curr_buffer, dict)):
            return
        for param_key in curr_buffer:
            if(isinstance(curr_buffer[param_key], dict) and "filesrc" in curr_buffer[param_key] and "fileslineno" in curr_buffer[param_key]):
                tmp = curr_buffer[param_key]["val"]
                curr_buffer[param_key] = tmp
            else:
                self._unnormalize_parametric_table(curr_buffer[param_key])
    # -------------------------

    def parametric_table_capture(self, param_type, parametric_hash_table, location_file_str="none", location_file_lineno=0):
        if (location_file_str == "none"):
            info = inspect.getframeinfo(inspect.currentframe().f_back)[0:3]
            location_file_lineno = info[1]
            _path_tokens = info[0].split('/')
            location_file_str = _path_tokens[len(_path_tokens) - 1]
        # -------------------------------
        if(param_type not in self.container["general_param_history"]):
            self.container["general_param_history"][param_type] = {}
        self.container["general_param_history"][param_type]["val"] = deepcopy(parametric_hash_table)
        self.container["general_param_history"][param_type]["filesrc"] = location_file_str
        self.container["general_param_history"][param_type]["fileslineno"] = location_file_lineno
        # self._normalize_parametric_table(self.container["general_param_history"][param_type],location_file_str,location_file_lineno)
    # --------------------
    #
    # ---------------------

    def print_history(self):
        print("Blacklist:", str(self.container["blacklist"]), "\n")
        print("TAP History:", str(self.container["tap_history"]), "\n")
        print("STF History:", str(self.container["stf_history"]), "\n")
        print("Global:", str(self.container["general_param_history"]), "\n")
    # ----------------------
    # buffer evaluation
    # ----------------------

    def __recursive_has(self, indx, keys_list, param, buffer_ptr):
        if(indx >= len(keys_list)):
            if(param != ""):
                if(param in buffer_ptr):
                    return True
                else:
                    return False
            else:
                return True
        else:
            if(keys_list[indx] not in buffer_ptr):
                return False
            return self.__recursive_has(indx + 1, keys_list, param, buffer_ptr[keys_list[indx]])
    # -----------------------

    def history_has(self, action_ptr, keys_list, param="", container_type="tap_history"):
        if(action_ptr.get_action_type() not in self.container[container_type]):
            return False
        return self.__recursive_has(0, keys_list, param, self.container[container_type][action_ptr.get_action_type()])

    def blacklist_has_type(self, action_type):
        if(action_type not in self.container["blacklist"]):
            return False
        else:
            return True

    def blacklist_has(self, action_ptr, keys_list, param=""):
        if(action_ptr.get_action_type() not in self.container["blacklist"]):
            return False
        return self.__recursive_has(0, keys_list, param, self.container["blacklist"][action_ptr.get_action_type()])
    # -----------------------------------

    def parametric_has(self, param_type, param_keys):
        if(param_type not in self.container["general_param_history"]):
            return False
        return self.__recursive_has(0, param_keys, "", self.container["general_param_history"][param_type])
    # -----------------------------------------

    def parametric_has_table(self, param_type):
        if(param_type not in self.container["general_param_history"]):
            return False
        else:
            return True
    # ----------------------
    # buffer get
    # ----------------------

    def __recursive_get(self, indx, keys_list, param, buffer_ptr):
        if(indx >= len(keys_list)):
            if(param != ""):
                if(param in buffer_ptr):
                    return buffer_ptr[param]
                else:
                    htdte_logger.error(("Trying to access not existent history entity:%s%s .") % (str(keys_list).replace(",", "->"), param))
            else:
                return buffer_ptr
        else:
            return self.__recursive_get(indx + 1, keys_list, param, buffer_ptr[keys_list[indx]])
    # -----------------------------

    def history_get(self, action_ptr, keys_list, param="", container_type="tap_history"):
        if(not self.history_has(action_ptr, keys_list, param, container_type)):
            htdte_logger.error(("Trying to access not existent history entity:%s:%s%s .") %
                               (action_ptr.get_action_type(), str(keys_list).replace(",", "->"), param))
        return self.__recursive_get(0, keys_list, param, self.container[container_type][action_ptr.get_action_type()])

    def blacklist_get(self, action_ptr, keys_list, param=""):
        if(not self.blacklist_has(action_ptr, keys_list, param)):
            htdte_logger.error(("Trying to access not existent blacklist entity-%s:%s%s .") %
                               (action_ptr.get_action_type(), str(keys_list).replace(",", "->"), param))
        return self.__recursive_get(0, keys_list, param, self.container["blacklist"][action_ptr.get_action_type()])

    def parametric_get(self, param_type, param_keys):
        if(param_type not in self.container["general_param_history"]):
            htdte_logger.error(("Trying to access not existent parametric table entry-%s .") % (param_type))
        return self.__recursive_get(0, param_keys, "", self.container["general_param_history"][param_type])["val"]
    # ----------------------------------------------

    def parametric_table_get(self, param_type):
        if(param_type not in self.container["general_param_history"]):
            htdte_logger.error(("Trying to access not existent parametric table entry-%s .") % (param_type))
        return deepcopy(self.container["general_param_history"][param_type]["val"])
    # -------------------------

    def save_history(self, info):
        htdte_logger.inform(("Saving the History Manager info to file: %s ...") % (self.HistoryManagerSaveFile))
        self.Chkpt_file_info = info
        try:
            pickle.dump(self.container, open(self.HistoryManagerSaveFile, "wb"))
        except TypeError as e:
            htdte_logger.error(("Failed to save (dump) a history: %s . Try to zero the action class member ...") % (e))


#####################################################################################################
htd_history_mgr = htd_history_manager()
