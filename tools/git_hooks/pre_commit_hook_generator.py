#!/usr/intel/pkgs/python3/3.6.3a/modules/r1/bin/python
import os
import sys
from subprocess import call, STDOUT
import stat
global_htd_python_lib = "/p/pde/htd/Site/Infra/GlobalTools/lib/python3.6/site-packages"
sys.path.append(global_htd_python_lib)
import logging
from pre_commit.runner import Runner
from pre_commit.commands.install_uninstall import install
from pre_commit.commands.autoupdate import autoupdate
from pre_commit.store import Store
from pre_commit.util import cmd_output
import argparse
import tempfile
import re

logging.basicConfig()


def print_info(msg):
    print("-I- " + msg)


def print_error(msg):
    print("-E- " + msg)
    exit(1)


def get_pc_config(root):
    return root + "/.pre-commit-config.yaml"


def create_runner_and_store(root):
    config = get_pc_config(root)
    runner = Runner.create(config)
    store = Store()
    return runner, store


def update_rev_to_master(root):
    config = get_pc_config(root)
    pc_cfg = open(config, "r")
    cfg_data = pc_cfg.read().split("\n")
    pc_cfg.close()
    pc_cfg = open(config, "w")

    found_repo = False
    for i, line in enumerate(cfg_data):
        if re.match(r"\s*-\s+repo:\s+ssh://git-amr-7.devtools.intel.com:29418/mdo_cgf-pre-commit-hooks", line):
            found_repo = True
        elif found_repo:
            m = re.match(r"(\s*rev:\s+)\w+", line)
            if m:
                line = m.group(1) + "master"
                found_repo = False
        elif re.match(r"\s*-\s+repo:\s+", line):
            found_repo = False

        if i < len(cfg_data) - 1:
            pc_cfg.write(line + "\n")
        else:
            pc_cfg.write(line)
    pc_cfg.close()


def get_pre_commit_hook_file():
    return ".git/hooks/pre-commit"


def disable_pre_commit():
    pc_file = get_pre_commit_hook_file()
    pc_dis = pc_file + ".disabled"
    if os.path.exists(pc_file):
        if os.path.exists(pc_dis):
            cmd_output("rm", pc_dis)
        cmd_output("mv", pc_file, pc_dis)


def enable_pre_commit():
    pc_file = get_pre_commit_hook_file()
    pc_dis = pc_file + ".disabled"
    if os.path.exists(pc_dis):
        if os.path.exists(pc_file):
            cmd_output("rm", pc_file)
        cmd_output("mv", pc_dis, pc_file)


def update_pre_commit(runner, store, skip_config_commit=False):
    autoupdate(runner.config_file, store, 0)

    # Check if config file needs to be committed
    retcode, stdout, stderr = cmd_output("git", "status", "--porcelain", runner.config_file_path)

    if stdout == "":
        # No differences
        return

    if stdout.split()[0] == "M":
        # Commit the .pre-commit-config.yaml file
        disable_pre_commit()
        try:
            retcode, stdout, stderr = cmd_output("git", "commit", "-m",
                                                 "[Auto generated commit] Updating .pre-commit-config.yaml file after "
                                                 "pre-commit autoupdate ran",
                                                 "--", runner.config_file)
        except CalledProcessError:
            enable_pre_commit()

        enable_pre_commit()


def install_pre_commit(pc_path, runner, store, dest_path=None):
    update_pre_commit(runner, store)
    install(runner.config_file, store, overwrite=False, hooks=True, hook_types=["pre-commit"])
    os.chmod(pc_path, stat.S_IRWXU + stat.S_IRGRP + stat.S_IXGRP)

    if dest_path is not None:
        if os.path.isfile(dest_path):
            # The pre_commit file already exists, delete it and replace it with the generated file
            print_info("pre-commit.pre_commit already exists, deleting it and replacing with a newly generated version")
            os.remove(dest_path)

        os.rename(pc_path, dest_path)


def get_htd_pre_commit_header():
    """
    Function to get the htd generated pre-commit header
    :return: The HTD Generated header
    :rtype: str
    """
    return "# HTD GLOBAL PRE-COMMIT HOOK"


def get_htd_pre_commit_file_contents():
    """
    Function to generate the contents of the pre-commit file
    :return: The contents of the pre-commit file
    :rtype: str
    """
    htd_global_pre_commit = "tools/git_hooks/htd_pre_commit"

    data = "#!/usr/intel/bin/tcsh\n"
    data += "{}\n".format(get_htd_pre_commit_header())
    data += "# This is an auto-generated file! DO NOT MODIFY!\n"
    data += "# If you would like to install personal pre-commit hooks, put them in .git/hooks/pre-commit.user\n"
    data += "# This script will call pre-commit.user\n\n"

    # Make sure the correct env vars are in place to where pre-commit will run
    data += "# Make sure the correct env vars are in place to where pre-commit will run\n"
    data += "modpath -q -f /p/pde/htd/Site/Infra/GlobalTools/bin\n"
    data += "modpath -q -f -v PYTHONPATH {}\n\n".format(global_htd_python_lib)

    # Make sure user has PRE_COMMIT_HOME set
    data += "# Make sure user has PRE_COMMIT_HOME set\n"
    data += "if (! $?PRE_COMMIT_HOME) then\n"
    data += "    echo You must set env var PRE_COMMIT_HOME prior to using pre-commit. BKM is to create a pre-commit " \
            "dir in your eng sandbox and set PRE_COMMIT_HOME to this path in your cshrc or aliases file.\n"
    data += "    exit 1\n"
    data += "endif\n\n"

    # Execute pre-commit.user if it exists
    data += "# Execute pre-commit.user if it exists\n"
    data += "if (-x .git/hooks/pre-commit.user) then\n"
    data += "    .git/hooks/pre-commit.user\n"
    data += check_exit_code(indent=1)
    data += "endif\n\n"

    # Execute htd_global_pre_commit file
    data += "# Execute htd_global_pre_commit file\n"
    data += "{}\n".format(htd_global_pre_commit)
    data += check_exit_code()
    data += "\n"

    # Execute the pre-commit tool code
    data += "# Execute the pre-commit tool code\n"
    data += "echo pre-commit tool:\n"
    data += "echo     Ensuring pre-commit repo is up to date:\n"
    data += "tools/git_hooks/pre_commit_hook_generator.py -root `realpath .` -update_pre_commit\n"
    data += "echo     Running pre-commit tool:\n"
    data += ".git/hooks/pre-commit.pre_commit\n"
    data += check_exit_code()
    data += "echo ''\n\n"

    # Remove the env vars for global drv python libs as they sometimes conflict with other tools
    data += "# Make sure the correct env vars are in place to where pre-commit will run\n"
    data += "modpath -q -f -d /p/pde/htd/Site/Infra/GlobalTools/bin\n"
    data += "modpath -q -f -d -v PYTHONPATH {}\n\n".format(global_htd_python_lib)

    return data


def check_exit_code(indent=0):
    data = ""
    data += "    " * indent + "set exit_code = $?\n"
    data += "    " * indent + "if ($exit_code != 0) then\n"
    data += "    " * indent + "    modpath -q -f -d /p/pde/htd/Site/Infra/GlobalTools/bin\n"
    data += "    " * indent + "    modpath -q -f -d -v PYTHONPATH {}\n\n".format(global_htd_python_lib)
    data += "    " * indent + "    exit $exit_code\n"
    data += "    " * indent + "endif\n"
    return data


def create_htd_hooks(hook_path):
    # Write the new local .git/hooks/pre-commit file
    pc = open(hook_path, "w")
    pc.write(get_htd_pre_commit_file_contents())
    pc.close()
    os.chmod(hook_path, stat.S_IRWXU + stat.S_IRGRP + stat.S_IXGRP)


if __name__ == "__main__":
    # Setup command line args
    parser = argparse.ArgumentParser(description="Generate combined git pre-commit hook")
    parser.add_argument('-root', help="Path to the top level of the HTD_ROOT", required=True)
    parser.add_argument('-update_pre_commit', help="Only update pre-commit", action="store_true", required=False)
    args = parser.parse_args()

    # Change dir into root
    os.chdir(args.root)

    # Create a runner and store object for this run
    runner, store = create_runner_and_store(args.root)

    if args.update_pre_commit:
        update_pre_commit(runner, store)
    else:
        print_info("Beginning pre-commit hook checking")
        # Check if this dir is a git repo
        if call(["git", "branch"], stderr=STDOUT, stdout=open(os.devnull, 'w')) != 0:
            # This is not a git repo, we don't need to do anything
            print_info("This root {} is not a git repo, skipping pre-commit installation\n".format(args.root))
            exit(0)
        else:
            print_info("This root {} is a git repo, starting pre-commit installation".format(args.root))

        # Create a temp_dir for temporary storage
        tmp_dir = tempfile.mkdtemp(suffix="htd_global_pre_commit")

        # Generate the path to the git hooks directory
        git_hook_rel_path = ".git/hooks"
        git_hook_path = args.root + "/" + git_hook_rel_path

        # Check that the .git/hooks directory is writable
        if not os.access(git_hook_path, os.W_OK):
            print_info("User {} does not have access to the .git/hooks directory".format(os.getenv("USER")))
            exit(0)

        # Check if pre-commit file exists
        pre_commit_path = git_hook_path + "/pre-commit"
        pre_commit_user_path = pre_commit_path + ".user"
        pre_commit_install_path = pre_commit_path + ".pre_commit"
        if os.path.isfile(pre_commit_path):
            # Check if this is the HTD Generated pre-commit file
            htd_file = False
            with open(pre_commit_path, "r") as f:
                for line in f:
                    line = line.rstrip()
                    if line == get_htd_pre_commit_header():
                        htd_file = True
                        break

            # Check if pre-commit.user exists
            if not htd_file and os.path.isfile(pre_commit_user_path):
                # The pre-commit file exists and doesn't appear to be the htd global version
                # A pre-commit.user file already exists as well
                # Error out and have the user cleanup their pre-commit files
                print_error("Both pre-commit and pre-commit.user exist and appear to be user owned files. Please move "
                            "all pre-commit code into pre-commit.user, remove the pre-commit file and re-run.")
            elif not htd_file:
                # The pre-commit file already exists but it appears to be a user generated file.
                # Move it to pre-commit.user
                print_info("Moving pre-commit file to pre-commit.user file")
                os.rename(pre_commit_path, pre_commit_user_path)
                os.chmod(pre_commit_user_path, stat.S_IRWXU + stat.S_IRGRP + stat.S_IXGRP)
            else:
                # The pre-commit file already exists but it is the htd generated version
                # Delete the file and re-generate it
                print_info("Removing HTD generated pre-commit file and will re-generate it")
                os.remove(pre_commit_path)

        # Install pre-commit
        install_pre_commit(pre_commit_path, runner, store, dest_path=pre_commit_install_path)

        # Create HTD Global pre-commit and user pre-commit files
        create_htd_hooks(pre_commit_path)

        print_info("Done installing pre-commit hooks\n")
