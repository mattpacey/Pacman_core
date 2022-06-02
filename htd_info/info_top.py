#!/usr/intel/pkgs/python3/3.6.3a/modules/r1/bin/python  -B
import os
from htd_unix_socket import *
from htd_utilities import *
import inspect
# --------------------------------
os.environ["HTD_ROOT"] = os.path.realpath(__file__).replace("htd_info/info_service.py", "")
os.putenv("HTD_ROOT", os.path.realpath(__file__).replace("htd_info/info_service.py", ""))
os.environ["STEP"] = "A0"
os.putenv("STEP", "A0")

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
