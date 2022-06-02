#!/usr/intel/pkgs/python3/3.6.3a/modules/r1/bin/python -u

import os
import sys
import shutil
import time
from os.path import join, dirname, exists, basename, realpath, getsize

if os.getenv("PACMAN_ROOT") is None:
    raise Exception("Please source HTD Simode Root!")


elif ('/p/hdk/rtl/proj_tools/pacman/') in os.getenv("PACMAN_ROOT"):
    raise Exception("You are currently using the release area PACMAN_ROOT environment [%s]."
                    "\nPlease set the PACMAN_ROOT into your own sandbox environment!!!"
                    "\nExample: setenv PACMAN_ROOT <sandbox>" % os.getenv("PACMAN_ROOT"))

from utils.veplog import log

from utils.utils import Elapsed, iif, count_iter
from utils.dictmore import DictDot
from utils.shell import BgCmd, USERNAME
from utils.files import File, TempDir
from utils.disk import mkdirs, allfiles
from utils.strmore import regex, group
from veplib.prod.errors import check
from utils.helperclass import OPT, TagOnce


class RunAllTest(object):

    def get_files(self, tpath=None):
        """
        Iterator: Returns (file, name and mod (module name))
        of all library vep files with test_*.py file and product test_* file

        file is the <path>/test/test_<file>.py
        name is just a name for bgcmd
        mod is a python file being tested. mod does not contain path

        Example:
        ('/somepath/library/veplib/test/test_releases.py', 'releases', 'releases.py')
        """

        tpath = os.getenv("PACMAN_ROOT")
        file_iter = self.get_tests_py(tpath)

        for ff in file_iter:
            if regex(r'pre_commit_home/', ff):
                continue
            if regex(r'test_(\w+)\.', ff):
                name = group(1)
                mod = name + ".py"
            else:
                raise Exception("get_files(): Regex Error to get module name: [{}]".format(ff))

            yield ff, name, mod

    def runtests(self, test_files):
        """
        Main routine to run all tests
        """
        self.logdir = self.setpath()
        allmod = set()
        alltests = list(test_files)
        stat = DictDot()
        stat.totline, stat.totassert, stat.tottest, stat.totlinet = 0, 0, 0, 0
        fails = []
        sw = Elapsed()

        bg = BgCmd(startid=1000, ncpu=1)
        for ff, name, mod in alltests:

            cmd = "{exe} {ff} -v -b".format(exe=sys.executable,
                                            ff=ff)
            bg.send(cmd, name=mod)

        self.finish_jobs(bg, fails, stat)
        bg.close()

# Execute the parallel jobs =============================================
#        bg = BgCmd(startid=1000, timeout=60*90)     # 90 mins (1.5 hrs).
#        # send them in queue first
#        for ff, name, mod in alltests:
#            allmod.add(mod)
#            cmd = "{exe} {ff} -v -b".format(exe=sys.executable,
#                                                     ff=ff)
#            bg.send(cmd, name=mod)
#
#        self.finish_jobs(bg, fails, stat)
#
#        bg.close()

        # Summary ==================================================
        log.info("{tot:<25} {l:>5} lines, {tl:>5} test-lines, {tas:>4} asserts, {time}, {tott:>4} tests"
                 .format(tot="TOTAL", l=stat.totline, tl=stat.totlinet, tas=stat.totassert,
                         time=sw(), tott=stat.tottest), True)

        if len(fails) > 0:
            log.info("Logdir: {}".format(self.logdir))
            log.info("")

        # Display all fails
        for f in fails:
            log.info("FAIL: {}".format(f), True)

        if len(fails) > 0:
            return 1
        # pass
        return 0

    def get_tests_py(self, vdir):
        """
        Iterator: Return all test_* files given vdir
        """
        log.info("Processing dir: {}".format(vdir))
        for fullpath in allfiles(vdir, skipsvn=True, rx=regex.compile(r'/test/test_\w+\.py$')):
            yield fullpath

    def setpath(self):
        """
        Prepare the log path
        """
        logdir = os.getenv("PACMAN_ROOT")
        check.is_dir(logdir, message="Required dir does not exist: [{dir}]. Pls create this dir with 775 permission")
        logdir = join(logdir, 'ut_logs')
        mkdirs(logdir, mode="02775")
        # delete all contents
        for f in os.listdir(logdir):
            os.unlink(join(logdir, f))

        return logdir

    def finish_jobs(self, bg, fails, stat):
        """Execute the bg jobs"""
        # Start of BgCmd block ===========================================================
        # Run the jobs
        while bg.run():
            for job in bg.queue(done=True):   # these are completed jobs
                self.process(job, fails, stat)
                bg.purge(job.name)
            time.sleep(0.05)

        # Wait for all jobs to complete
        for job in bg.queue(wip=True):
            log.info("Waiting for {nam}, pid={p}".format(nam=job.name, p=job.pr.pid))

        once = TagOnce()
        while bg.count() > 0:
            for job in bg.queue(done=True):
                if once(job.name):
                    log.info("{} is done".format(job.name))
            time.sleep(0.5)

        # Process the rest of completed jobs
        for job in bg.queue(done=True):
            self.process(job, fails, stat)
            bg.purge(job.name)
        # END of BgCmd block ============================================================

    def process(self, job, fails, stat):
        """
        Process the completed jobs
        """
        ff = job.cmd[1]
        mod = job.name

        lines, asserts, linet = self.get_lines_asserts(ff, mod)

        stderr = open(job.serr).read().rstrip()

        if regex(r'Ran (\d+) test', stderr):
            tests = int(group(1))
        else:
            tests = 0

        for res in stderr.split('\n'):
            pass   # get the last line

        # Cannot use exitcode for 1) unittest has exit(0) inside; 2) ChkTmp cannot set exit status code at destructor.

        # Add the ff if fail
        if not res.startswith("OK"):
            res += " [{}]".format(realpath(ff))
            fails.append(realpath(ff))
            self.noempty(job.serr)
            shutil.copy(job.serr, self.logdir)
            # TODO: self.get_fail_detail(basename(ff), job.serr)   # stores fail to self.faildetail[key]   # key is basename(ff)

        log.info("{m:<25} {l:5} lines, {tl:5} test-lines, {ass:4} asserts, {el:5.2f}, {t:4} tests: {r}"
                 .format(m=mod, l=lines, tl=linet, ass=asserts, el=job.elapsed, t=tests, r=res))

        stat.totline += lines
        stat.totassert += asserts
        stat.tottest += tests
        stat.totlinet += linet

    def get_lines_asserts(self, test, mod):
        """
        Get the number of lines and asserts
        """
        targ = join(dirname(test), "..", mod)
        if exists(targ):
            totline = count_iter(File(targ).fh())  # self.code_lines(targ)
        else:
            totline = 0
        totassert = sum(1 for x in open(test) if 'self.a' in x)
        return totline, totassert, count_iter(File(test).fh())

    def noempty(self, ff):
        """If ff is size zero, then put a text"""
        if getsize(ff) == 0:
            open(ff, 'w').write('Unittest was not executed successfully\n'
                                'Pls execute the unittest in unix with -v to show details.\n')


def main():
    if (os.getenv("LD_LIBRARY_PATH")) is not None:
        os.environ["LD_LIBRARY_PATH"] = str(os.getenv("SPF_ROOT")) + "/lib:" + os.environ["LD_LIBRARY_PATH"] + \
            str(os.getenv("SPF_ROOT")) + "/lib:" + str(os.getenv("SPF_ROOT")) + "/lib/SPF_API_LIB:" + \
            str(os.getenv("SPF_ROOT")) + "/lib/CMTS_libs:" + \
            str(os.getenv("SPF_ROOT")) + "/lib/SPF_API_LIB/python:" + \
            str(os.getenv("SPF_ROOT")) + "/lib/xml_lib:" + \
            str(os.getenv("SPF_ROOT")) + "/lib/boost_lib:" + \
            str(os.getenv("SPF_ROOT")) + "/lib/tar_lib:" + os.environ["LD_LIBRARY_PATH"]
    else:
        os.environ["LD_LIBRARY_PATH"] = str(os.getenv("SPF_ROOT")) + "/lib" + \
            str(os.getenv("SPF_ROOT")) + "/lib:" + str(os.getenv("SPF_ROOT")) + "/lib/SPF_API_LIB:" + \
            str(os.getenv("SPF_ROOT")) + "/lib/CMTS_libs:" + \
            str(os.getenv("SPF_ROOT")) + "/lib/SPF_API_LIB/python:" + \
            str(os.getenv("SPF_ROOT")) + "/lib/xml_lib:" + \
            str(os.getenv("SPF_ROOT")) + "/lib/boost_lib:" + \
            str(os.getenv("SPF_ROOT")) + "/lib/tar_lib"

    with TempDir(chdir=True):     # so that cwd() is not written
        run = RunAllTest()
        res = run.runtests(run.get_files())
        if res != 0:
            exit(1)
        return res


if __name__ == '__main__':  # pragma: no cover
    main()
