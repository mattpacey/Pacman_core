#!/usr/intel/pkgs/python/2.7.5/bin/python

import os
import re
import sys
import subprocess
from utils.files import File
from utils.disk import Allfiles

def checkfile():
    arr = [] #TVPVConfigDict()
    dir = sys.argv[1]
    for files in Allfiles(dir, skipsvn=True, rx="\.py$", skiplink=True):
        print "Current file", files
        output = ""
        for line in File(files):
            if line.startswith("#!/usr/"):
                match = re.search("(#!\S+)" , line)
                sheline = match.groups(1)
                print "Found: ", line
                newline = re.sub("#!\S+", "#!/usr/intel/pkgs/python3/3.6.3a/modules/r1/bin/python", line)
                print "Replaced: ", newline
                output += newline
            else:
                output += line
        with File(files, mode="w") as fh:
            fh.write(output)

checkfile()
