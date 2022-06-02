#!/usr/intel/pkgs/python3/3.6.3a/modules/r1/bin/python -B
import os
from os.path import join, dirname
import unittest
import sys
import subprocess
import pwd
import glob
import shutil
sys.path.append(join(dirname(sys.argv[0]), ".."))
sys.path.append(os.getenv('PACMAN_ROOT'))
sys.path.append(join(os.getenv('PACMAN_ROOT'), 'tools/htd_te/bin'))
sys.path.append(join(os.getenv('PACMAN_ROOT'), 'htd_info'))


from htd_spf_action import SPF
import htd_basic_action
import htd_collaterals_parser
import htd_arguments_container
import htd_logger

from utils.files import TempDir, File
from utils.mock import patch, Mock, MagicMock
#from utils.ut import TestCase, unittest
from utils.helperclass import CaptureStdoutLog


class TestHtdSpfAction(unittest.TestCase):

    def setUp(self):
        self.spf = SPF('action_name', 'source_file', 100, 'currentFlow', 'is_internal')

    def tearDown(self):
        idsid = pwd.getpwuid(os.getuid()).pw_name
        tmp = '/tmp/*' + idsid + '*'
        tmp_dir = glob.glob(tmp)

        for items in tmp_dir:
            if ('run_all_tests') in items:
                pass

            else:
                if os.path.isdir(items):
                    shutil.rmtree(items)
                elif os.path.exists(items):
                    os.remove(items)

    @patch('htd_basic_action.htd_base_action.__init__')
    @patch('htd_arguments_container.htd_argument_containter.declare_arg')
    def test_init(self, mock_declare, mock_action):
        with patch.dict('htd_collaterals_parser.CFG', {"HPL": {"execution_mode": "itpp"}}):
            self.spf.__init__('action_name', 'source_file', 100, 'currentFlow', 'is_internal')
            self.assertEqual(self.spf.direct_packet, {})
            self.assertFalse(self.spf.direct_packet_mode)
            mock_action.assert_called_once()
            mock_declare.assert_called_once_with("spf_file", "The path to file define a test sequence in SPF format", "string", "none", 1)
            self.assertEqual(self.spf.template, "")
            self.assertEqual(self.spf.spec, "")
            self.assertEqual(self.spf.itpp_file, "")

    def test_get_action_not_declared_argument_names(self):
        self.spf.get_action_not_declared_argument_names()

    @patch('htd_arguments_container.htd_argument_containter.set_argument')
    @patch('htd_arguments_container.htd_argument_containter.get_argument')
    def test_verify_arguments_espf(self, mock_get, mock_set):
        with TempDir(name=True, chdir=True) as temp_dir:
            fullpath = join(temp_dir, "file.espf")
            mock_get.return_value = fullpath
            with patch('subprocess.check_output') as mock_subprocess:
                with self.assertRaises(SystemExit) as cm:
                    with CaptureStdoutLog() as log:
                        self.spf.verify_arguments()
                self.assertIn(("The given espf sequence file- %s is not accessible..") % (fullpath), log.getvalue())
                File(fullpath).touch()
                expected_cmd = ("%s/tools/scripts/spf_convert.py -f %s --espf_only") % (os.environ.get('HTD_ROOT'), fullpath)
                self.spf.verify_arguments()
                mock_subprocess.assert_called_with(expected_cmd, shell=True, stderr=subprocess.STDOUT)
                mock_set.assert_any_call("spf_file", "file.spf")
            with self.assertRaises(SystemExit) as cm:
                with CaptureStdoutLog() as log:
                    self.spf.verify_arguments()
            self.assertIn("eSPF run didnt finish correctly\n", log.getvalue())

    def test_verify_arguments_itpp(self):
        with patch.dict('htd_collaterals_parser.CFG', {"HPL": {"execution_mode": "itpp"}}):

            # check HTD_COLLECT_RTL_SIGNALS_MODE = 1
            with patch.dict('os.environ', {'HTD_COLLECT_RTL_SIGNALS_MODE': '1'}):
                self.assertIsNone(self.spf.verify_arguments())

            # check SPF_ROOT = not exists, skip None because redundant if else condition
            with TempDir(name=True, chdir=True) as temp_dir:
                fullpath = join(temp_dir, "spf_root")
                with patch.dict('os.environ', {"SPF_ROOT": fullpath}):
                    with self.assertRaises(SystemExit) as cm:
                        with CaptureStdoutLog() as log:
                            self.spf.verify_arguments()
                    self.assertIn("The  SPF ROOT directory (%s) given in ENV[SPF_ROOT] is not accessable.." % (os.path.exists(os.environ.get('SPF_ROOT'))), log.getvalue())

                    # check ld_library
                    File(fullpath).touch()
                    expected_ld_library_path = ("%s/lib") % os.environ.get('SPF_ROOT')
                    with self.assertRaises(SystemExit) as cm:
                        with CaptureStdoutLog() as log:
                            self.spf.verify_arguments()
                    self.assertEqual(expected_ld_library_path, os.environ.get('LD_LIBRARY_PATH'))

                # check SPF_PERL_LIB not exists, skip None because redundant if else condition
                with patch.dict('os.environ', {"SPF_PERL_LIB": "/dummy/spf_perl_lib"}):
                    with self.assertRaises(SystemExit) as cm:
                        with CaptureStdoutLog() as log:
                            self.spf.verify_arguments()
                    self.assertIn(('The  SPF ROOT directory (%s) given in ENV[SPF_PERL_LIB] is not accessable..') % (os.path.exists(os.environ.get('SPF_PERL_LIB'))), log.getvalue())

                # HTD_CONTENT_TEMPLATE_OVRD default = None
                # check SPF_TEMPLATE_FILE not exists, skip None because redundant if else condition
                with patch.dict('os.environ', {"SPF_TEMPLATE_FILE": "dummy/spf_template_file"}):
                    with self.assertRaises(SystemExit) as cm:
                        with CaptureStdoutLog() as log:
                            self.spf.verify_arguments()
                    self.assertIn(('The  SPF TEMPLATE directory (%s) given in ENV[SPF_TEMPLATE_FILE] is not accessable..') % (os.environ.get('SPF_TEMPLATE_FILE')), log.getvalue())
                with self.assertRaises(SystemExit) as cm:
                    with CaptureStdoutLog() as log:
                        self.spf.verify_arguments()
                self.assertEqual(self.spf.template, os.environ.get('SPF_TEMPLATE_FILE'))

                # check HTD_CONTENT_TEMPLATE_OVRD not exists
                with TempDir(name=True, chdir=True) as temp_dir:
                    fullpath = join(temp_dir, "htd_content_template_ovrd")
                    with patch.dict('os.environ', {"HTD_CONTENT_TEMPLATE_OVRD": fullpath}):
                        with self.assertRaises(SystemExit) as cm:
                            with CaptureStdoutLog() as log:
                                self.spf.verify_arguments()
                        self.assertIn(('The  SPF TEMPLATE directory (%s) given in ENV[HTD_CONTENT_TEMPLATE_OVRD] is not accessable..') % (os.environ.get('HTD_CONTENT_TEMPLATE_OVRD')), log.getvalue())

                        # check HTD_CONTENT_TEMPLATE_OVRD exists
                        File(fullpath).touch()
                        with self.assertRaises(SystemExit) as cm:
                            with CaptureStdoutLog() as log:
                                self.spf.verify_arguments()
                        self.assertEqual(self.spf.template, os.environ.get('HTD_CONTENT_TEMPLATE_OVRD'))

                # check SPF_SPEC_FILE not exists, skip None because redundant if else condition
                with patch.dict('os.environ', {"SPF_SPEC_FILE": "dummy/spf_spec_file"}):
                    with self.assertRaises(SystemExit) as cm:
                        with CaptureStdoutLog() as log:
                            self.spf.verify_arguments()
                    self.assertIn(('The  SPF SPEC directory (%s) given in ENV[SPF_SPEC_FILE] is not accessable..') % (os.path.exists(os.environ.get('SPF_SPEC_FILE'))), log.getvalue())
                self.assertEqual(self.spf.spec, os.environ.get('SPF_SPEC_FILE'))

                # check spf_file not exists
                with self.assertRaises(SystemExit) as cm:
                    with CaptureStdoutLog() as log:
                        self.spf.verify_arguments()
                self.assertIn('The given spf sequence file- none is not accessible..', log.getvalue())

                with patch('htd_arguments_container.htd_argument_containter.get_argument') as mock_get:
                    # check self.itpp_file
                    with TempDir(name=True, chdir=True) as temp_dir:
                        fullpath = join(temp_dir, "file.spf")
                        mock_get.return_value = fullpath
                        File(fullpath).touch()
                        self.spf.verify_arguments()
                        self.assertEqual(self.spf.itpp_file, "file.itpp")

                        # check command line
                        with patch('htd_logger.Logger.inform') as mock_inform:
                            command_line = ("%s/bin/spf --tapSpecFile %s --testSeqFile %s --itppFile %s --templateFile %s --mciSpecFile %s") % (os.environ.get('SPF_ROOT'),
                                                                                                                                                os.environ.get('SPF_SPEC_FILE'),
                                                                                                                                                fullpath,
                                                                                                                                                self.spf.itpp_file,
                                                                                                                                                self.spf.template,
                                                                                                                                                os.environ.get('SPF_MCI_SPEC_FILE'))
                            self.spf.verify_arguments()
                            mock_inform.assert_any_call("Running: %s --stfSpecFile %s" % (command_line, os.environ.get('HTD_SPF_STF_SPEC_FILE')))

                            # check subprocess
                            with patch('subprocess.Popen') as mock_sub:
                                with self.assertRaises(SystemExit) as cm:
                                    with CaptureStdoutLog() as log:
                                        self.spf.verify_arguments()
                                mock_sub.assertIn(command_line, shell=True, stdout=subprocess.PIPE)

                        # check .pacman_log is created
                        with patch('builtins.open') as mock_open:
                            self.spf.verify_arguments()
                            mock_open.assertIn("file.pacman_log", "w", 1)

                        # # check subprocess
                        # with patch('subprocess.Popen.communicate') as mock_sub:
                        #     mock_sub.return_value = [True, True]
                        #     with self.assertRaises(SystemExit) as cm:
                        #         with CaptureStdoutLog() as log:
                        #             self.spf.verify_arguments()
                        #     self.assertIn("SPF run didnt finish correctly\nTrue", log.getvalue())

                        # check HTD_SPF_STF_SPEC_FILE is an empty string
                        with patch.dict('os.environ', {"HTD_SPF_STF_SPEC_FILE": ""}):
                            self.spf.verify_arguments()
    
    @patch('htd_arguments_container.htd_argument_containter.get_argument')
    @patch('htd_hpl_spf_interface.hpl_spf_interface.send_action')
    def test_run(self, mock_send_action, mock_get):
        with patch.dict('htd_collaterals_parser.CFG', {"HPL": {"execution_mode": "itpp"}}):
            with TempDir(name=True, chdir=True) as temp_dir:
                fullpath = join(temp_dir, "file.itpp")
                File(fullpath).touch("111")
                self.spf.itpp_file = fullpath
                mock_get.return_value = "dummy/abc.spf"
                self.spf.run()
                mock_send_action.assert_called_with("111")
                self.assertEqual('dummy/abc.spf', os.environ.get("CONVERTED_ITPP_TEST"))

                with patch('builtins.open') as mock_open:
                    self.spf.run()
                    mock_open.assertIn(("abc.spf.converted"), 'w')

            with patch.dict('os.environ', {"HTD_COLLECT_RTL_SIGNALS_MODE": "1"}):
                self.assertIsNone(self.spf.run())

        with patch.dict('htd_collaterals_parser.CFG', {"HPL": {"execution_mode": "spf"}}):
            with TempDir(name=True, chdir=True) as temp_dir:
                fullpath = join(temp_dir, "file.spf")
                mock_get.return_value = fullpath
                with self.assertRaises(SystemExit) as cm:
                    with CaptureStdoutLog() as log:
                        self.spf.run()
                self.assertIn("Can't open file %s" % fullpath, log.getvalue())
                File(fullpath).touch("111")
                self.spf.run()
                mock_send_action.assert_called_with("111")

        with patch.dict('htd_collaterals_parser.CFG', {"HPL": {"execution_mode": "xml"}}):
            self.spf.run()

    def test_debug_readback(self):
        self.spf.debug_readback()


if __name__ == '__main__':
    unittest.main()
