#!/usr/intel/pkgs/python3/3.6.3a/modules/r1/bin/python  -B
import os
from htd_unix_socket import *

os.environ["INFO_SERVICES_ONLY_MODE"] = "1"
os.putenv("INFO_SERVICES_ONLY_MODE", "1")
from htd_utilities import *
import inspect
# --------------------------------
# os.environ["HTD_ROOT"]=os.path.realpath(__file__).replace("htd_info/info_service.py","")
# os.putenv("HTD_ROOT",os.path.realpath(__file__).replace("htd_info/info_service.py",""))
# os.environ["STEP"]="A0"
# os.putenv("STEP","A0")

# ----------------------------------
if ("-tecfg" in sys.argv):
    if (len(sys.argv) < sys.argv.index("-tecfg") + 2):
        sys.stderr.write("Missing argument value in command line for: -tecfg ....\n")
        exit(-1)
    os.environ["HTD_TE_CFG"] = sys.argv[sys.argv.index("-tecfg") + 1]
    os.putenv("HTD_TE_CFG", sys.argv[sys.argv.index("-tecfg") + 1])

if (os.environ.get("HTD_TE_CFG") is None):
    sys.stderr.write("Missing ENV[HTD_TE_CFG] ....\n")
    exit(-1)
from htd_collaterals import *
# -------------------------------


class htd_info_service_server(htd_unix_socket_server):
    def __init__(self, server_name, socket_name, debug_mode=0):
        os.environ["HTD_SOCKET_FILE"] = socket_name
        os.putenv("HTD_SOCKET_FILE", socket_name)
        htd_unix_socket_server.__init__(self, server_name, 1, debug_mode)

    # -----------------------------
    def error(self, message):
        sys.stderr.write(("ERROR: %s") % message)
        exit(-1)

    def request_handler(self, data):
        #print ("Server:Got a request data:%s")%(data)

        tokens = data.split(",")
        (key, func_name) = tokens[0].split("=")
        if (key != "NAME"):
            self.error(("illegal message received (Exapected NAME=<function_name>... format): received %s \n") % (data))
        (key, ui) = tokens[1].split("=")
        if (key != "ui"):
            self.error((
                       "illegal message received (Exapected NAME=<function_name>:ui:<api_name>... format): received %s \n") % (
                       data))
        func_args = {}
        for i in range(2, len(tokens)):
            (key, val) = tokens[i].split("=")
            func_args[key] = val
        # --------------------------
        ui_list = [x for x in list(CFG["INFO"].keys()) if (
            isinstance(CFG["INFO"][x], dict) and "module" in list(CFG["INFO"][x].keys()) and "class" in list(CFG["INFO"][x].keys()))]
        if (ui not in ui_list):
            sys.stderr.write((
                             "Illegal INFO UI name referenced by info_service: \"%s\",message: %s.Available UI names are: %s  \n") % (
                             ui, data, str(ui_list)))
        ui_funcs = eval(("[x for x in dir(HTD_INFO.%s) if (not re.search(\"^__\",x))]") % (ui))
        if (func_name not in ui_funcs):
            self.error(
                ("Illegal INFO %s:%s referencied by info_service,message: %s.Available function names are: %s  \n") % (
                    ui, func_name, data, ui_funcs))

        # -------------------------
        arg_spec = inspect.getargspec(eval(("HTD_INFO.%s.%s") % (ui, func_name)))
        def_func_args = arg_spec[0]
        for i in range(1, len(def_func_args) - len(arg_spec[3])):
            if (def_func_args[i] not in list(func_args.keys())):
                self.error(
                    ("Missing (not given)  argument (%s) referenced by info_service INFO.%s:%s,message: %s.  \n") % (
                        def_func_args[i], ui, func_name, data))
        # -----------------
        for arg in list(func_args.keys()):
            if (arg not in def_func_args):
                self.error((
                           "The given  argument name (%s) referenced by info_service INFO.%s:%s is not legal:,message: %s.Available argument names are: %s  \n") % (
                           arg, ui, func_name, data, def_func_args))
                # -------------------------
        func_cmd = ("HTD_INFO.%s.%s(") % (ui, func_name)
        for i in range(1, len(def_func_args)):
            if (def_func_args[i] in list(func_args.keys())):
                argval = func_args[def_func_args[i]]
            elif (i > len(def_func_args) - len(arg_spec[3])):
                argval = arg_spec[3][len(arg_spec[3]) - len(def_func_args) + i]

            func_cmd += (("\"%s\"") % argval) if i == 1 else ((",\"%s\"") % argval)
        func_cmd += ")"
        self.send(str(eval(func_cmd)))


# ---------------------------------------
if (("-socket" not in sys.argv) or (len(sys.argv) < sys.argv.index("-socket") + 2)):
    sys.stderr.write("Missing socket file name argument: -socket <socket_file_name>\n")
serv = htd_info_service_server("INFO_SERVICES", sys.argv[sys.argv.index("-socket") + 1])
