#!/usr/intel/pkgs/python3/3.6.3a/modules/r1/bin/python -B
import sys
import os
# ------
if(len(sys.argv) < 2):
    print("ERROR:Missing name of unix env to be processed...")
    sys.exit(-1)
env_name = sys.argv[1]
if(os.environ.get(env_name) is None):
    print(("ERROR:The given in cmd ENV[%s] is not exists/defined..") % (env_name))
    sys.exit(-1)
if(os.environ.get('HTD_ROOT') is None):
    print('Missing obligatory unix environment ENV[HTD_ROOT] - must point to user flow libraries location')
    sys.exit(-1)
htd_utilities_dir = ("%s/htd_info") % (os.environ.get('HTD_ROOT'))
if(not os.path.isdir(htd_utilities_dir)):
    print((('The given directory (%s)  - is not directory or not exists') % (htd_utilities_dir)))
sys.path.append(htd_utilities_dir)
from htd_utilities import *
# ------------------------------
origin_value = os.environ.get(env_name)
resolved_cmd = util_resolve_unix_env(os.environ.get(env_name))
os.environ[env_name] = resolved_cmd
os.putenv(env_name, resolved_cmd)
print(("Replace the origin ENV[%s]=\"%s\"\nNew value: ENV[%s]=\"%s\"") % (env_name, origin_value, env_name, os.environ.get(env_name)))
