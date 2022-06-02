#!/usr/intel/pkgs/python3/3.6.3a/modules/r1/bin/python
import sys
import subprocess
import re
import tempfile
import os
import json
import argparse
import glob
import inspect

"""
Author: Chris Flanagan

Wrapper script for htd_te_manager to help with integration into IDEs like Intellij

This script handles:
 1) Sourcing the correct environment
 2) Generating a feedlist
 3) Extracting the te_manager command from the feedlist
 4) Running said te_manger command

 This lets you put a simple call like
    htd_te_debug_helper.py -p htdval -s a0 -li htdval_longreset_type1
 into your IDE's debugger window and gain access to the full debugger capabilities

 Known issues:
 * You must start Intellij in a shell that already has SPF sourced.
    * This is because $LD_LIBRARY_PATH can't be set from within python.
"""


def run_sourceme(path, prod, step, mode=None, save_env_vars=""):
    """
    Source the common sourcme, and import all it's env into the current process

    :param string path: The HTD ROOT path
    :param string prod: Product to source
    :param string step: Stepping to source
    :param string mode: Source -mode option
    :return: None
    """

    env_dump = tempfile.NamedTemporaryFile(delete=False)

    for k in list(os.environ.keys()):  # Actually need .keys() here since deleting items, don't remove it!
        dont_delete = ["SHELL", "HOME", "TERM", "DISPLAY", "PATH"]
        dont_delete = dont_delete + save_env_vars.split(",")
        if k not in dont_delete and not re.match("EC_", k):
            del os.environ[k]
    os.environ["HTD_ROOT_DIRNAME"] = path

    sourceme = "source %s/sourceme -p %s -s %s" % (path, prod, step)
    if mode:
        sourceme += " -mode %s" % mode

    print("File: %s" % env_dump.name)
    cmds = [sourceme,
            "/usr/intel/bin/python2.7 -c \"import os;import json;json.dump(dict(os.environ),open(\'%s\',\'wb\'))\"" % env_dump.name,
            ]

    try:
        subprocess.check_call(["tcsh", "-cf", " && ".join(cmds)])
    except subprocess.CalledProcessError:
        print("-e- Error in sourcme")
        exit(1)

    # Replace the current env with what we got from sourcme
    os.environ.update(json.load(env_dump))
    # FYI: Don't do it this way: os.environ = json.load(env_dump)

    # Update path with PYTHONPATH from sourceme
    # This normally happens at python exec time, but we ran sourcme inside of our script.
    sys.path = os.environ["PYTHONPATH"].split(":") + sys.path


def replace_pacman_root():
    # Replace PACMAN_ROOT with the local version where this script is executing from, so you can debug pacman_core
    # without having to manually update your project
    orig_pacman_root = os.getenv("PACMAN_ROOT")
    pacman_root = os.path.abspath(os.path.dirname(os.path.realpath(inspect.stack()[0][1])) + "/../../..")

    return pacman_root


def generate_feedlist(product, stepping, lineitem, linus_overrides):
    """
    Generate a testlist

    :param string product: The product code
    :param string stepping: Which stepping
    :param string lineitem: Lineitem name to load
    :param string linus_overrides: Testlist gen overrides to pass via -linus_overrides
    :return string: The path to the new testlist
    """
    # Get a temp dir. This is always used for feedlist gen, to ensure uniqueness, but te_manager rundir can be overriden
    temp_dir = tempfile.mkdtemp(prefix="intellij_run_")

    os.environ["WARD"] = temp_dir
    print("Running testlistgen")
    try:

        tlg_command = [
            "testlistgen",
            "-header_only",
            "-output_dir", temp_dir,
            "-product", product,
            "-stepping", stepping,
            "-line_item", lineitem]
        if linus_overrides:
            tlg_command += ["-linus_overrides", linus_overrides]

        subprocess.check_call(tlg_command)
    except subprocess.CalledProcessError:
        print("-e- Error in testlistgen")
        exit(1)

    names = glob.glob("%s/tlgen/*.list" % temp_dir)
    if len(names) > 1:
        print("-e- Multiple feedlists found in %s" % temp_dir)
        exit(1)
    return names[0]


def parse_commandline():
    """
    Parse the command line

    :return: command line args object
    """
    # Command line parsing
    parser = argparse.ArgumentParser(description="A tool to aid in running htd_te_manager from IDEs such as Intellij."
                                     " This will let you use the full featured debugger capabilities without having to"
                                     " manually copy and paste htd_te_manager commandlines."
                                     " The tool does the following steps for you:"
                                     " 1) Source your env from common sourceme"
                                     " 2) Install the specified testlist"
                                     " 3) Extract the te_manager command (with all args) from the feedlist"
                                     " 4) Run te_manager and automatcially connect it to your IDE debugger")

    parser.add_argument('-product', '-p', help="What product to run", required=True)
    parser.add_argument('-stepping', '-s', help="What stepping to run", required=True)
    parser.add_argument('-htd_root', '-r', help="The HTD_ROOT to use", required=True)
    parser.add_argument('-flow', '-f', help="What flow to run. Cannot be used with -lineitem", required=False)
    parser.add_argument('-lineitem', '-line_item', '-li', help="Line item name, cannot be used with -flow", required=False)
    parser.add_argument('-no_source', help="Skip running sourcme", action='store_const', const=True, default=False)
    parser.add_argument('-feedlist', help="Previously generated feedlist to extract te_manager command from")
    parser.add_argument('-linus_overrides', help="Linus overrides to pass to testlistgen")
    parser.add_argument('-source_mode', help="Value to pass to -mode of sourceme i.e [cu_emu, cug_emu]")
    parser.add_argument('-save_env_vars', help="A comma separated list of env vars to copy into the run env", default="")

    return parser.parse_args()


def extract_te_commandline(feedlist_name):
    """
    Read teh testlist and extract out the te_manager command line.  Assumes it is in -mid -mid-, per standard
    :param string feedlist_name: The path to the feedlist to parse
    :return string: The resulting commandline, cleaned of all feedlist wrappings
    """
    print("Extracting te_manager command")
    try:
        out = subprocess.check_output('grep htd_te_manager %s' % feedlist_name, shell=True)
        # Expand ENV Vars in te_manager command
        out = os.path.expandvars(out)
        # Remove feedlist wrappers
        out = out.rstrip('\n')
        out = re.sub(r'.*-mid\s+', '', out)
        out = re.sub(r'\s*-mid-.*', '', out)

        # pacman_root = replace_pacman_root()

        # if pacman_root != os.getenv("PACMAN_ROOT"):
        #     out += " -ENV:PACMAN_ROOT {}".format(pacman_root)

        return out.encode("ascii")
    except subprocess.CalledProcessError:
        print("-e- Error in htd_te_manager command extraction")
        exit(1)


def main():
    args = parse_commandline()

    if not args.no_source:
        # Sourcing sourcme
        print("Sourcing sourcme")
        run_sourceme(args.htd_root, args.product, args.stepping, args.source_mode, args.save_env_vars)

    te_command = ""
    if args.flow:
        flow = args.flow
        te_command = "$PACMAN_ROOT/tools/htd_te/bin/htd_te_manager.py -flow1 -flow_name {} -flow1-".format(flow)
    else:
        if args.feedlist:
            feedlist_name = args.feedlist
        else:
            feedlist_name = generate_feedlist(args.product, args.stepping, args.lineitem, args.linus_overrides)

        te_command = extract_te_commandline(feedlist_name)

    print("Running htd_te_manager")
    # Doing it this way, so that IDE debuggers work
    # System calls will break the debugger
    sys.argv = te_command.split(' ')
    import htd_te_manager


if __name__ == '__main__':
    main()
