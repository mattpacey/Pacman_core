from htd_basic_action import *
from htd_utilities import *
from htd_collaterals import *
from htd_player_top import *
import os
import re
# ---------------------------------------------
# Running spf sequence file
# -----------------------------------------------
#
#
#
# ------------------------------------------


class SPF(htd_base_action):
    def __init__(self,action_name,source_file,source_lineno,currentFlow,is_internal):
        self.direct_packet={}
        self.direct_packet_mode=False
        #----------------
        htd_base_action.__init__(self,self.__class__.__name__,action_name,source_file,source_lineno,currentFlow,is_internal)
        #---STF access by agent.register.field
        self.arguments.set_argument("source", 1, "Specify which source for this action")
        self.arguments.declare_arg("spf_file"             ,"The path to file define a test sequence in SPF format","string"      ,"none"  ,1 )
        #------------------------
        if (CFG["HPL"]["execution_mode"] == "itpp"):
            self.template = ""
            self.spec = ""
            self.itpp_file = ""
    # ----------------------

    def get_action_not_declared_argument_names(self): pass
    # ------------------------
    #
    # ------------------------

    def verify_arguments(self):
        if os.path.splitext(self.arguments.get_argument("spf_file"))[1] == ".espf":
            if(not os.path.exists(self.arguments.get_argument("spf_file"))):
                htdte_logger.error(('The given espf sequence file- %s is not accessible..') % (self.arguments.get_argument("spf_file")))

            try:
                command_line = ("%s/tools/scripts/spf_convert.py -f %s --espf_only") % (os.environ.get('HTD_ROOT'), self.arguments.get_argument("spf_file"))
                status = subprocess.check_output(command_line, shell=True, stderr=subprocess.STDOUT)

            except subprocess.CalledProcessError as e:
                htdte_logger.error("eSPF run didnt finish correctly\n%s" % e.output)
            else:
                htdte_logger.inform('Done Running eSPF, generated SPF')
                self.arguments.set_argument("spf_file", re.sub('.espf', '.spf', os.path.basename(self.arguments.get_argument("spf_file"))))

        if (CFG["HPL"]["execution_mode"] == "itpp"):
            self.inform(("       Verifying %s::%s:%s:%d ....") % (htd_base_action.get_action_type(self),
                                                                  htd_base_action.get_action_name(self),
                                                                  htd_base_action.get_action_call_file(self),
                                                                  htd_base_action.get_action_call_lineno(self)))

            if(os.environ.get('HTD_COLLECT_RTL_SIGNALS_MODE') == "1"):
                return
            # -----------------
            if(os.environ.get('SPF_ROOT') is None):
                htdte_logger.inform("Missing ENV[SPF_ROOT], be sure to provide the path to SPF install dir in shell env. by TE_cfg.xml or command line -ENV:SPF_ROOT <path_to_dir>")
            if(not os.path.exists(os.environ.get('SPF_ROOT'))):
                htdte_logger.error(('The  SPF ROOT directory (%s) given in ENV[SPF_ROOT] is not accessable..') % (os.path.exists(os.environ.get('SPF_ROOT'))))

            # ------------------
            ld_library = os.environ.get('LD_LIBRARY_PATH')
            if(not re.search(("%s/lib") % os.environ.get('SPF_ROOT'), ld_library)):
                new_ld_library_path = ("%s/lib") % os.environ.get('SPF_ROOT')
                htdte_logger.inform(('Modifying LD_LIBRARY_PATH =%s') % (new_ld_library_path))
                os.environ["LD_LIBRARY_PATH"] = new_ld_library_path
                os.putenv("LD_LIBRARY_PATH", new_ld_library_path)
            # ------------------------
            if(os.environ.get('SPF_PERL_LIB') is None):
                htdte_logger.inform("Missing ENV[SPF_PERL_LIB], be sure to provide the path to SPF perl lib. by TE_cfg.xml or command line -ENV:SPF_PERL_LIB <path_to_dir>")
            if(not os.path.exists(os.environ.get('SPF_PERL_LIB'))):
                htdte_logger.error(('The  SPF ROOT directory (%s) given in ENV[SPF_PERL_LIB] is not accessable..') % (os.path.exists(os.environ.get('SPF_PERL_LIB'))))
            # --------------------
            if(os.environ.get('HTD_CONTENT_TEMPLATE_OVRD') is None):
                if(os.environ.get('SPF_TEMPLATE_FILE') is None):
                    htdte_logger.inform("Missing ENV[SPF_TEMPLATE_FILE], be sure to provide the path to SPF install dir in shell env. by TE_cfg.xml or command line -ENV:SPF_TEMPLATE_FILE <path_to_file>")
                if(not os.path.exists(os.environ.get('SPF_TEMPLATE_FILE'))):
                    htdte_logger.error(('The  SPF TEMPLATE directory (%s) given in ENV[SPF_TEMPLATE_FILE] is not accessable..') % (os.environ.get('SPF_TEMPLATE_FILE')))
                else:
                    self.template = os.environ.get('SPF_TEMPLATE_FILE')
            else:
                if(not os.path.exists(os.environ.get('HTD_CONTENT_TEMPLATE_OVRD'))):
                    htdte_logger.error(('The  SPF TEMPLATE directory (%s) given in ENV[HTD_CONTENT_TEMPLATE_OVRD] is not accessable..') % (os.environ.get('HTD_CONTENT_TEMPLATE_OVRD')))
                else:
                    self.template = os.environ.get('HTD_CONTENT_TEMPLATE_OVRD')
            # ---------------------------
            if(os.environ.get('SPF_SPEC_FILE') is None):
                htdte_logger.inform("Missing ENV[SPF_SPEC_FILE], be sure to provide the path to SPF install dir in shell env. by TE_cfg.xml or command line -ENV:SPF_SPEC_FILE <path_to_file>")
            if(not os.path.exists(os.environ.get('SPF_SPEC_FILE'))):
                htdte_logger.error(('The  SPF SPEC directory (%s) given in ENV[SPF_SPEC_FILE] is not accessable..') % (os.path.exists(os.environ.get('SPF_SPEC_FILE'))))
            else:
                self.spec = os.environ.get('SPF_SPEC_FILE')
            # ------------------------------
            if(not os.path.exists(self.arguments.get_argument("spf_file"))):
                htdte_logger.error(('The given spf sequence file- %s is not accessible..') % (self.arguments.get_argument("spf_file")))
            # -------Running SPF to get ITPP----------------
            # orig_spf_seq=("%s.itpp")%(self.arguments.get_argument("spf_file"))
            self.itpp_file = re.sub('.spf', '.itpp', os.path.basename(self.arguments.get_argument("spf_file")))
            # spf_seq_l=orig_spf_seq.split("/")
            # self.itpp_file=spf_seq_l[len(spf_seq_l)-1]
            stf_spec_file = os.environ.get('HTD_SPF_STF_SPEC_FILE', "")

            command_line = ("%s/bin/spf --tapSpecFile %s --testSeqFile %s --itppFile %s --templateFile %s --mciSpecFile %s") % (os.environ.get('SPF_ROOT'),
                                                                                                                                self.spec,
                                                                                                                                self.arguments.get_argument("spf_file"),
                                                                                                                                self.itpp_file,
                                                                                                                                self.template,
                                                                                                                                os.environ.get('SPF_MCI_SPEC_FILE'))
            if (stf_spec_file != ""):
                command_line = " %s --stfSpecFile %s" % (command_line, stf_spec_file)
            htdte_logger.inform(('Running:%s') % (command_line))
            itppHand = subprocess.Popen(command_line, shell=True, stdout=subprocess.PIPE)
            HTD_subroccesses_pid_tracker_list.append(itppHand.pid)
            status = itppHand.communicate()
            if (status[len(status) - 1] is None and (not re.search("Error while parsing Test Sequence", str(status)))
                and (not re.search("ERROR TESTSEQPARSEERR", str(status)))
                                            and (not re.search("Test Sequence error message", str(status)))
                                            and (not re.search("ERROR TESTERR", str(status)))):
                spf_status_file = ("%s.pacman_log") % (self.itpp_file.replace(".itpp", ""))
                logStream = open(spf_status_file, "w", 1)
                for l in status:
                    logStream.write(("%s\n") % (l))
                logStream.close()
                htdte_logger.inform('Done Running SPF, generated ITPP')
            else:
                htdte_logger.error(("SPF run didnt finish correctly\n%s") % (status[len(status) - 2]))
           # ------------------------------------------
           #
           # -------------------------------

    def run(self):
        if (CFG["HPL"]["execution_mode"] == "itpp"):
            # FIXME - add actual action execution
            os.environ["CONVERTED_ITPP_TEST"] = ""
            self.inform(("         Running %s::%s:%s:%d \n\n") % (
                htd_base_action.get_action_type(self),
                htd_base_action.get_action_name(self),
                htd_base_action.get_action_call_file(self),
                htd_base_action.get_action_call_lineno(self)))

            if(os.environ.get('HTD_COLLECT_RTL_SIGNALS_MODE') == "1"):
                return
            line_num = 0
            # while line:
            instrumental_comment_line = ""  # tobe save in transactor for final itpp
            with open(self.itpp_file) as itppfile:
                output = itppfile.readlines()
                for line in output:
                    htdPlayer.hpl_to_dut_interface.send_action(line)
#            for line in open(self.itpp_file, 'r').readlines():
#                # ----------------------
#                line_num = line_num + 1
#                # Commenting this so that the final itpp file is not cumbersome
#                #htdPlayer.hpl_to_dut_interface.send_action(("rem: comment: Executing %s:%d\n")%(self.itpp_file,line_num))
#                htdPlayer.hpl_to_dut_interface.send_action(line)
#                #htdte_logger.inform(( 'Line %s')%(line))
            htdte_logger.inform('Done Reading ITPP')
            os.environ["CONVERTED_ITPP_TEST"] = self.arguments.get_argument("spf_file")
            path_l = self.arguments.get_argument("spf_file").split("/")
            open(("%s.converted") % path_l[len(path_l) - 1], 'w').close()
            # ----------------------------
        elif (CFG["HPL"]["execution_mode"] == "spf"):
            self.inform(("         Running SPF_SEQUENCE spf_file=%s \n\n") % (self.arguments.get_argument("spf_file")))
            line_num = 0
            try:
                with open(self.arguments.get_argument("spf_file")) as spffile:
                    # ----------------------
                    output = spffile.readlines()
                    for line in output:
                        htdPlayer.hpl_to_dut_interface.send_action(line)
            except IOError:
                htdte_logger.error("Can't open file %s" % (self.arguments.get_argument("spf_file")))
            htdte_logger.inform('Done Reading SPF')

    def debug_readback(self): pass
