from htd_utilities import *
import math
from copy import deepcopy
import cProfile
import pstats
import io
# --------------------------


def convert_key_value_table_hexstring_to_dec(dict_name, dictionary, all_dict_list, CFG, debug=0):
    for entry in list(dictionary.keys()):
        if(isinstance(dictionary[entry], dict)):
            htdte_logger.error((" More then one level dictionary depth is not supported yet.(dictionary:%s)  ") % (dict_name))
        if(type(dictionary[entry]) in [str, str]):
            if(not re.search("^0x", dictionary[entry])):
                dictionary[entry] = ("0x%s") % (dictionary[entry])
            dictionary[entry] = int(dictionary[entry], 16)
        elif(type(dictionary[entry]) in [int, int, float]):
            dictionary[entry] = ("0x%s") % dictionary[entry]
        else:
            htdte_logger.error((" Unknown value type - %s found in dictionary:%s  ") % (str(type(dictionary[entry])), dict_name))
# -------Used for processing top.hier dictionary - duplicate a keys by last hier name (if not exists)---------


def duplicate_keys_by_last_hier_level(dict_name, dictionary, all_dict_list, CFG, debug=0):
    new_dictionary = {}
    for entry in list(dictionary.keys()):
        for path in dictionary[entry]:
            module = re.sub(r"[A-z0-9_]+\.", "", path)
            if(module not in list(new_dictionary.keys())):
                new_dictionary[module] = []
            if(path not in new_dictionary[module]):
                new_dictionary[module].append(path)
    del(dictionary)
    all_dict_list[dict_name] = new_dictionary
# -------------------------


def extract_last_module_hierarhy_name(dict_name, dictionary, all_dict_list, CFG, debug=0):
    #  pr = cProfile.Profile()
    #  pr.enable()
    new_dictionary = {}
    keys_tracker = set()
    for entry in list(dictionary.keys()):
        for p in dictionary[entry]:
            hier_l = p.rsplit(".", 1)
            if(len(hier_l) == 2):
                if(hier_l[1] not in keys_tracker):
                    keys_tracker.add(hier_l[1])
                    new_dictionary[hier_l[1]] = []
                new_dictionary[hier_l[1]].append(p)
            else:
                if(hier_l[0] not in keys_tracker):
                    keys_tracker.add(hier_l[0])
                    new_dictionary[hier_l[0]] = []
                new_dictionary[hier_l[0]].append(p)
        del(p)
    del(dictionary)
    all_dict_list[dict_name] = new_dictionary
#  pr.disable()
#  s = StringIO.StringIO()
#  sortby = 'cumulative'
#  ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
#  ps.print_stats()
#  print s.getvalue()
    htdte_logger.inform((" extract_last_module_hierarhy_name done - %d") % (len(list(new_dictionary.keys()))))
