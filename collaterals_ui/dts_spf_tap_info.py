#!/usr/intel/pkgs/python3/3.6.3a/modules/r1/bin/python
# -*- coding: utf-8 -*-
import socket
import sys
import re
import os
import subprocess
import os.path
from htd_tap_info import *
from htd_utilities import *
from htd_collaterals import *

path_to_collateral_interface = '%s/bin/API_SERVER_CLIENT' % os.environ.get('SPF_ROOT')
sys.path.insert(0, path_to_collateral_interface)
from collateral_interface import Client


class dts_spf_tap_info(htd_tap_info):

    def __init__(self):
        htd_tap_info.__init__(self)
        if os.environ.get('HTD_PROJ') is None:
            htdte_logger.error('Missing obligatory unix environment ENV[HTD_PROJ] ')
        proj = os.environ.get('HTD_PROJ').upper()
        if os.environ.get('SPF_ROOT') is None:
            htdte_logger.error('Missing SPF_ROOT env. (should it  be set in TE_cfg or in xterm ?')
        LdLibraryPath = '%s/lib/perl5%s' % (os.environ.get('SPF_ROOT'), ('' if os.environ.get('LD_LIBRARY_PATH')
                                                                         == None else ':%s' % os.environ.get('LD_LIBRARY_PATH')))
        os.environ['LD_LIBRARY_PATH'] = LdLibraryPath
        htdte_logger.inform('SPF setup done: setenv LD_LIBRARY_PATH %s' % os.environ.get('LD_LIBRARY_PATH'))
        # Setup local dictionaries to reduce unneeded spf server calls, and speedup pacman
        self.normalize_fast_dict = {}
        self.rtl_node_exists_fast_dict = {}

    # --------------------------------

        if os.environ.get('HTD_SPF_TAP_SPEC_FILE') is None:
            htdte_logger.error('Missing obligatory TE_cfg.cml parameter HTD_SPF_TAP_SPEC_FILE.')
        htdte_logger.inform('Using HTD_SPF_TAP_SPEC_FILE file=%s' % os.environ.get('HTD_SPF_TAP_SPEC_FILE'))
        self.spec_file = os.environ.get('HTD_SPF_TAP_SPEC_FILE')

    # ---------------------------------------

        ld_library = os.environ.get('LD_LIBRARY_PATH')
        ld_library_l = ld_library.split(':')
        if '%s/lib' % os.environ.get('SPF_ROOT') not in ld_library_l:
            new_ld_library_path = '%s/lib' % os.environ.get('SPF_ROOT')
            htdte_logger.inform('Modifying LD_LIBRARY_PATH =%s' % new_ld_library_path)
            os.environ['LD_LIBRARY_PATH'] = new_ld_library_path
            os.putenv('LD_LIBRARY_PATH', new_ld_library_path)

    # --------------------------------

        api_client = Client('uds', log_file=None, workspace='/tmp')
        if not os.environ.get('MARSHALLED_FILE') is None:
            self.tapObj = None
            if os.path.isfile(os.environ.get('MARSHALLED_FILE')):
                htdte_logger.inform('Calling the get tap with the Marshalled file =%s'
                                    % os.environ.get('MARSHALLED_FILE'))
                self.tapObj = api_client.get_Tap(self.spec_file, os.environ.get('MARSHALLED_FILE'))

            if self.tapObj is None:
                try:
                    htdte_logger.inform('Trying to generate the marshalled file =%s' % os.environ.get('MARSHALLED_FILE'))

                    if os.access(os.environ.get('MARSHALLED_FILE'), os.W_OK):
                        os.system('touch %s' % os.environ.get('MARSHALLED_FILE'))
                        os.system('rm -f %s' % os.environ.get('MARSHALLED_FILE'))
                    self.tapObj = api_client.get_Tap(self.spec_file, os.environ.get('MARSHALLED_FILE'))
                except BaseException:
                    htdte_logger.inform('Fail to generate a new marshalled file going normal')
                    self.tapObj = api_client.get_Tap(self.spec_file)

            # At this point if tapObj is still none then error out because all attempts have been made to find it or regen it.
            if self.tapObj is None:
                htdte_logger.error('DTS get_Tap returned None. This likely means SPF Spec is corrupted, or it it no longer matches the marshalled version. Delete %s and try again'
                                   % os.environ.get('MARSHALLED_FILE'))
        else:
            self.tapObj = api_client.get_Tap(self.spec_file)

        # Place for saving an entire IR dict for faster lookup on back to back queries
        self.dr_field_dict = {}

  # ---------------------------------

    def normalize_field_name(self, IR, agent, field):
        # Upper case incoming field once, outside of loops
        uppercase_field = field.upper()

        # Check if requested field exists in local dict, and return it if so
        if (IR, agent, uppercase_field) in self.normalize_fast_dict:
            return self.normalize_fast_dict[IR, agent, uppercase_field]

        # This must be a new IR,
        # so update local dict with all normalized field names
        # Doing it all at once saves time later
        for f in self.get_ir_field_details(IR, agent):
            self.normalize_fast_dict.setdefault((IR, agent, f.upper()), f)

        # Check one last time, since above loop should have found it
        if (IR, agent, uppercase_field) in self.normalize_fast_dict:
            return self.normalize_fast_dict[IR, agent, uppercase_field]

        htdte_logger.error(' Can\'t match field name - "%s" by %s->%s , Available fields are : %s' % (field, agent, IR,
                                                                                                      list(self.get_ir_field_details(IR, agent).keys())))

   # ----------------------------------------------------

    def verify_tap_cmd(self, agnt, cmd):
        self.get_ir_opcode_int(cmd, agnt)

   # ---------------------------------

    def verify_tap_register_field(
        self,
        agnt,
        cmd,
        field,
    ):
        if field not in self.get_ir_fields(cmd, agnt):
            htdte_logger.error('Illegal field - %s aplied on TAP agent - %s, CMD:%s' % (field, agent, IR))

   # ------------------

    def get_ir_commands(self, agent):
        irs_str = self.tapObj.get_tap_irs(agent)
        if not irs_str:
            htdte_logger.error(" <server_get_tap_irs> error ::%s'" % irs_str)
        return (irs_str if irs_str is not None else [])

  # ---------------------------------------------

    def get_ir_field_details(self, IR, agent):
        agent = self.get_real_agent(agent, IR)
        if self.tap_reg_backdoor_exists(IR, agent):
            return self.tap_reg_backdoor_get_field_details(IR, agent)

        self.dr_field_dict_info(agent, IR)
        fields_l = self.dr_field_dict[agent][IR]

        if fields_l is None:
            htdte_logger.error("<get_ir_field_details> Can't find an ir by   agent:%s cmd:%s." % (agent, IR))

        res = {}
        for field in fields_l:
            field_name = field
            field_msb = fields_l[field]['msb']
            field_lsb = fields_l[field]['lsb']
            res[field_name] = {'msb': field_msb, 'lsb': field_lsb}

        # Need to manually create the fields for TAP link IR and DR for padding purposes
        pre = None
        post = None
        if (self.tapObj.get_tap_SERIR(agent) == IR
                or (False if self.tapObj.get_tap_PARIR(agent) is None else (IR in self.tapObj.get_tap_PARIR(agent)))):
            pre = self.tapObj.get_taplinkEP_pre_dr_delay(agent)
            irsize = self.tapObj.get_tap_ir_size(agent.replace("GLUE_", "", 1))
            res['IR'] = {'msb': irsize - 1, 'lsb': 0}
            if pre is not None:
                res['DUMMY_HI'] = {'msb': pre + irsize, 'lsb': irsize}
        elif (self.tapObj.get_tap_SERDR(agent) == IR
                or (False if self.tapObj.get_tap_PARDR(agent) is None else (IR in self.tapObj.get_tap_PARDR(agent)))):
            pre = self.tapObj.get_taplinkEP_pre_dr_delay(agent)
            post = self.tapObj.get_taplinkEP_post_dr_delay(agent)
            res['DR'] = {'msb': post, 'lsb': post}
            if post is not None:
                res['DUMMY_LO'] = {'msb': post - 1, 'lsb': 0}
            if not (pre is None or post is None):
                res['DUMMY_HI'] = {'msb': pre + post, 'lsb': post + 1}

        return res

    # -----------------------------------

    def get_tap_field_comments(
        self,
        IR,
        agent,
        field,
    ):
        return 'NA_yet'

   # ------------------------

    def get_tap_agents(self):
        message = '<server_get_tap_types>\n'
        agents_str = self.tapObj.get_tap_all()
        if agents_str is None:
            htdte_logger.error(" <server_get_tap_types> error :%s'" % agents_err)

       # fchan4 Comment>agents = sorted(set(agents_str.split("\n"))) #unique values

        agents = sorted(agents_str)  # unique values
        return agents

   # --------Automatically discovered method , called by help if exists----------------

    def html_content_help(self, file_name):
        html_file = open(file_name, 'w')
        html_file.write('''<!DOCTYPE html>
<html>
''')
        html_file.write('<a name="top"></a>\n<body>')
        html_file.write('<p><h1> DFX Tap Link UI Content </h1></p><hr>\n')
        agents = self.get_tap_agents()
        agents = sorted(set(agents))  # unique values
        for agent in agents:
            html_file.write('<a href="#%s">%s</a><br>\n' % (agent, agent))
        html_file.write('<br><hr>\n')
        ignore_agents_or_cmds = []
        if 'TapInfoHelpIgnore' in CFG['HPL']:
            ignore_agents_or_cmds = CFG['HPL']['TapInfoHelpIgnore'].replace(' ', '').split(',')
        for agent in agents:
            if agent in ignore_agents_or_cmds:
                htdte_logger.inform('Ignoring TAP info for controller: %s (ignored by CFG["HPL"]["TapInfoHelpAgntIgnore"])'
                                    % agent)
                continue
            htdte_logger.inform('Extracting TAP info for controller: %s' % agent)
            try:
                irs_str = self.tapObj.get_tap_irs(agent)
            except BaseException:
                html_file.write('<p><h3> TAP Controller: %s is not accessable by DFT TAP Link server</h3></p><hr>\n'
                                % agent)
                continue

         # ------------------

            html_file.write('<a name="%s"></a>\n' % agent)
            html_file.write('<p><h3> TAP Controller: %s </h3></p><hr>\n' % agent)
            html_file.write('<table border="1">\n')
            html_file.write('<tr bgcolor="blue"><th><font color="white">CMD</font>\
	 		     </th><th><font color="white">OPCODE</font></th>\
	 		     <th><font color="white">FIELD</font></th>\
	 		     <th><font color="white">LSB:MSB</font></th>\
	 		     <th><font color="white">RESET</font></th>\
	 		     <th><font color="white">RTL Node</font></th>\
	 		     <th><font color="white">Comments</font></th></tr>'
                            )

     # for ir in irs_str.split("\n"):

            for ir in irs_str:
                ir = ir.replace('%s.' % agent, '')
                if ir in ignore_agents_or_cmds:
                    htdte_logger.inform('Ignoring TAP CMD info : %s (ignored by CFG["HPL"]["TapInfoHelpIgnore"])' % ir)
                    continue
                html_file.write('<tr align="left" bgcolor="yellow"><th>%s</th><th>%s</th> <th></th><th></th><th></th><th></th><th></th></tr>'
                                % (ir, util_int_to_binstr(self.get_ir_opcode_int(ir, agent), self.get_ir_size(agent))))

       # ----------Fields

                for field in self.get_ir_fields(ir, agent):
                    html_file.write('<tr align="left"><th></th><th></th> <th>%s</th><th>%d:%d</th><th>0x%x</th><th>%s</th><th>%s</th></tr>'
                                    % (
                                        field,
                                        self.get_field_lsb(ir, agent, field),
                                        self.get_field_msb(ir, agent, field),
                                        self.get_field_reset_value(ir, agent, field),
                                        (self.get_rtl_endpoint(ir, agent, field) if self.rtl_node_exists(ir, agent, field) else ''),
                                        self.get_tap_field_comments(ir, agent, field),
                                    ))

            html_file.write('</table>\n')
        html_file.write('''<hr>
<a href="#top">Top of Page</a>
''')
        html_file.write('''<br>
</body>
</html>
''')
        html_file.close()

   # ------------------------
   # def __del__(self):
   # htd_tap_info.__del__(self)
   # ------------------------

    def get_field_msb(self, IR, agent, field):
        """

        :param str IR:  The IR to check against
        :param str agent: The tap name to check against
        :param str field: The register field to check against
        :return: The msb of the specified field
        :rtype: int
        """
        agent = self.get_real_agent(agent, IR)
        if self.tap_reg_backdoor_exists(IR, agent):
            return self.tap_reg_backdoor_get_field_msb(IR, agent, field)
        normalize_field_name = self.normalize_field_name(IR, agent, field)

        self.dr_field_dict_info(agent, IR)
        msb = self.dr_field_dict[agent][IR][normalize_field_name]["msb"]

        if msb is None:
            htdte_logger.error('Failed to determine msb for Agent: (%s) IR: (%s) Field: (%s): \n %s' % (agent, IR, field, msb))
            sys.exit(1)
        if agent in self.ir_field_size_override and IR in self.ir_field_size_override[agent] and field \
                in self.ir_field_size_override[agent][IR]:
            lsb = self.get_field_lsb(IR, agent, field)
            return int(lsb) + self.ir_field_size_override[agent][IR][field] - 1
        else:
            return int(msb)

   # ------------------------------

    def get_field_lsb(self, IR, agent, field):
        agent = self.get_real_agent(agent, IR)
        if self.tap_reg_backdoor_exists(IR, agent):
            return self.tap_reg_backdoor_get_field_lsb(IR, agent, field)

        normalize_field_name = self.normalize_field_name(IR, agent, field)

        self.dr_field_dict_info(agent, IR)
        lsb = self.dr_field_dict[agent][IR][normalize_field_name]["lsb"]

        return int(lsb)

   # --------------------

    def get_field_reset_value(self, IR, agent, field, err_suppress=0):
        agent = self.get_real_agent(agent, IR)
        if(self.tap_reg_backdoor_exists(IR, agent)):
            return self.tap_reg_backdoor_get_field_reset_value(IR, agent, field)

        reset_value = self.tapObj.get_tap_field_default(agent, IR, field)

        if reset_value is None:
            if err_suppress:
                return 0
            htdte_logger.error('Failed to determine reset value for Agent: (%s) IR: (%s) Field: (%s)' % (agent, IR,
                                                                                                         field))
            sys.exit(1)

        if '\'b' in reset_value:
            reset_value = re.sub('\'b', '', reset_value)
            reset_int = int(reset_value, 2)
        if '\'h' in reset_value:
            reset_value = re.sub('\'h', '', reset_value)
            reset_int = int(reset_value, 16)

        return reset_int

   # ----------------------------------------------------

    def get_ir_opcode_string(
        self,
        IR,
        agent,
        err_suppress=0,
    ):
        if err_suppress:
            return 0

        agent = self.get_real_agent(agent, IR)
        opcode = self.tapObj.get_tap_ir_opcode(agent, IR)

        if opcode is None:
            if err_suppress:
                htdte_logger.inform("Agent: %s, IR: %s, opcode: %s" % (agent, IR, opcode))
            else:
                htdte_logger.error('Failed to get the opcode for Agent: (%s) IR: (%s) Field: (%s)' % (agent, IR, opcode))
        if '\'b' in opcode:
            opcode = re.sub('\'b', '', opcode)
        if '\'h' in opcode:
            opcode = re.sub('\'h', '', opcode)

        return opcode

   # ----------------------------------------------------

    def get_ir_opcode_int(
        self,
        IR,
        agent,
        err_suppress=0,
    ):
        str_val = self.get_ir_opcode_string(IR, agent, err_suppress)
        if str_val == 0 and err_suppress > 0:
            if err_suppress:
                return 0
            else:
                return 0
        if re.match('<server_error>.+', str_val) or str_val == 0:
            if err_suppress:
                return 0
            else:
                htdte_logger.error(" Can't find a tap instruction :%s.%s" % (agent, IR))
        return int(self.get_ir_opcode_string(IR, agent, err_suppress), 2)

   # ---------------------------------------------

    def get_ir_fields(self, IR, agent):
        agent = self.get_real_agent(agent, IR)
        if self.tap_reg_backdoor_exists(IR, agent):
            return list(self.tap_reg_backdoor_get_field_details(IR, agent).keys())

        self.dr_field_dict_info(agent, IR)
        fields_l = self.dr_field_dict[agent][IR]

        if not fields_l:
            htdte_logger.error('Failed to determine fields for Agent: (%s) IR: (%s)' % (agent, IR))
            sys.exit(1)

        return fields_l

   # ---------------------------------------------

    def get_is_tap_dr_dynamic(self, agent, IR):
        tap_dr_dynamic = self.tapObj.is_tap_dr_dynamic(agent, IR)
        if tap_dr_dynamic == 1:
            return 1
        elif tap_dr_dynamic == 0:
            return 0
        else:
            htdte_logger.error('Failed to determine dr is dynamic for Agent: (%s) IR: (%s)' % (agent, IR))

        return tap_dr_dynamic

   # --------------------------

    def get_dr_total_length(self, IR, agent):
        agent = self.get_real_agent(agent, IR)
        if self.tap_reg_backdoor_exists(IR, agent):
            return self.get_tap_reg_backdoor_size(IR, agent)

        #dr_length = self.tapObj.get_tap_dr_size(agent, IR)
        # if dr_length == None:
        #    dr_length = 0

        is_dynamic = self.get_is_tap_dr_dynamic(agent, IR)

        if is_dynamic == 0:
            fields = self.get_ir_fields(IR, agent)
            msb = 0

            for field in fields:
                msb_temp = self.get_field_msb(IR, agent, field)
                #lsb = self.get_field_lsb(IR, agent, field)

                if msb <= msb_temp:
                    msb = msb_temp
                    dr_length = msb + 1

        if dr_length == 0:
            if IR == self.tapObj.get_tap_SERIR(agent) or (False if self.tapObj.get_tap_PARIR(agent) is None else IR in self.tapObj.get_tap_PARIR(agent)):
                dr_length = self.tapObj.get_tap_ir_size(agent.replace("GLUE_", "", 1)) + (0 if self.tapObj.get_taplinkEP_pre_ir_delay(agent) is None
                                                                                          else self.tapObj.get_taplinkEP_pre_ir_delay(agent))
                htdte_logger.inform("Tap Link IR dr length found for %s as size: %d" % (agent, dr_length))
            elif IR == self.tapObj.get_tap_SERDR(agent) or (False if self.tapObj.get_tap_PARDR(agent) is None else IR in self.tapObj.get_tap_PARDR(agent)):
                dr_length = 1 + (0 if self.tapObj.get_taplinkEP_pre_dr_delay(agent) is None else self.tapObj.get_taplinkEP_pre_dr_delay(agent)) + \
                    (0 if self.tapObj.get_taplinkEP_post_dr_delay(agent) is None else self.tapObj.get_taplinkEP_post_dr_delay(agent))
                htdte_logger.inform("Tap Link DR dr length found for %s as size: %d" % (agent, dr_length))

        return dr_length

   # --------------------------

    def rtl_node_exists(self, IR, agent, field):
        # Check if we already have this field in our local dict
        # else look it up then store it before returning it
        magic_key = "%s__%s__%s" % (IR, agent, field)
        if magic_key in self.rtl_node_exists_fast_dict:
            return self.rtl_node_exists_fast_dict[magic_key]
        agent = self.get_real_agent(agent, IR)

        # message = "<server_get_rtl_struct> " + agent + "." + IR + "." + field + "\n"?????????????
        # --In future SPF should manage signals , meanwile checking in dictionary if exists

        try:

            # --Trying getting the rtl node information from processed dictionary

            if agent in dict_tap_rtl_info:
                if 'cmd' not in dict_tap_rtl_info[agent]:
                    htdte_logger.error('tap_rtl_info["%s"]["cmd"]' % agent)
                ircode = self.get_ir_opcode_int(IR, agent)
                if ircode in dict_tap_rtl_info[agent]['cmd']:
                    if 'field' not in dict_tap_rtl_info[agent]['cmd'][ircode]:
                        htdte_logger.error('tap_rtl_info["%s"]["cmd"][0x%x]["field"]' % (agent, ircode))
                    if field in dict_tap_rtl_info[agent]['cmd'][ircode]['field']:
                        if 'rtlPath' in dict_tap_rtl_info[agent]['cmd'][ircode]['field'][field]:
                            self.rtl_node_exists_fast_dict[magic_key] = 1
                            return self.rtl_node_exists_fast_dict[magic_key]
                    elif field.replace('.', '_') in dict_tap_rtl_info[agent]['cmd'][ircode]['field']:
                        if 'rtlPath' in dict_tap_rtl_info[agent]['cmd'][ircode]['field'][field.replace('.', '_')]:
                            self.rtl_node_exists_fast_dict[magic_key] = 1
                            return self.rtl_node_exists_fast_dict[magic_key]
            self.rtl_node_exists_fast_dict[magic_key] = self.rtl_node_backdoor_exists(agent, IR, field)
            return self.rtl_node_exists_fast_dict[magic_key]
        except NameError:

            # --trying getting rtl node from spf

            if os.environ.get('HTD_TE_INFO_UI_HELP') is not None:
                self.rtl_node_exists_fast_dict[magic_key] = 0
                return self.rtl_node_exists_fast_dict[magic_key]

            # fchan4 rtl_endpoint_str = self.send_receive_message("<server_get_rtl_node> " + agent + "." + IR + "." + field + "\n")

            normalize_field_name = self.normalize_field_name(IR, agent, field)

            self.dr_field_dict_info(agent, IR)
            try:
                rtl_endpoint_str = self.dr_field_dict[agent][IR][normalize_field_name]["SHADOW_SIGNAL"]
            except BaseException:
                rtl_endpoint_str = 0

            # fchan4 if(re.search("error",rtl_endpoint_str) or not rtl_endpoint_str):

            if not rtl_endpoint_str:
                self.rtl_node_exists_fast_dict[magic_key] = self.rtl_node_backdoor_exists(agent, IR, field)
                return self.rtl_node_exists_fast_dict[magic_key]
            fub_path_str_l = rtl_endpoint_str.replace('.', '/').split('/')
            if len(fub_path_str_l) > 0 and not HTD_INFO.signal_info.signal_module_exists('%s' % fub_path_str_l[0]):
                self.rtl_node_exists_fast_dict[magic_key] = self.rtl_node_backdoor_exists(agent, IR, field)
                return self.rtl_node_exists_fast_dict[magic_key]
            else:
                self.rtl_node_exists_fast_dict[magic_key] = 1
                return self.rtl_node_exists_fast_dict[magic_key]

       # rtl_endpoint_str = self.send_receive_message(message)
       # TODO should be closed with OZ (fub,node)=rtl_endpoint_str.split(":")
       # only for taplink ????
   # --------------------------------------------

    def is_taplink_remote_tap(self, agent):

        resp = self.tapObj.is_taplink_remote_tap(agent)
        if resp:
            return 1
        else:
            return 0

    def has_tap_link_parallel_support(self, TAP):

        resp = self.tapObj.has_tap_link_parallel_support(TAP)

        if not resp:
            return 0
        elif resp:
            return 1
        else:
            htdte_logger.error("Failed to determine if Tap: %s has tap link parallel support." % (TAP))

    def get_tap_link_PARIR(self, TAP):

        irname = self.tapObj.get_tap_PARIR(TAP)

        if isinstance(irname, list):
            irname = ",".join(str(x) for x in irname)
            htdte_logger.inform("Parallel IR list joined : %s" % (irname))

        if not irname:
            htdte_logger.error(" Can't find a %s.IR - field" % TAP)
        else:
            htdte_logger.inform(" Found par taplink %s.IR - field" % TAP)

        agent = self.get_real_agent(TAP, irname)
        irname = irname
        return (agent, irname, 'IR')

    def get_tap_link_PARDR(self, TAP):

        irname = self.tapObj.get_tap_PARDR(TAP)

        if isinstance(irname, list):
            irname = ",".join(str(x) for x in irname)
            htdte_logger.inform("Parallel DR list joined : %s" % (irname))

        if not irname:
            htdte_logger.error(" Can't find a %s.DR - field" % TAP)
        else:
            htdte_logger.inform(" Found par taplink %s.DR - field" % TAP)

        agent = self.get_real_agent(TAP, irname)
        irname = irname
        return (agent, irname, 'DR')

    def get_tap_link_IR(self, TAP):

        irname = self.tapObj.get_tap_SERIR(TAP)

        if not irname:
            htdte_logger.error(" Can't find a %s.IR - field: (%s)" % (TAP, irname))
        else:
            htdte_logger.inform(" Found taplink %s.IR - field: (%s)" % (TAP, irname))

        agent = self.get_real_agent(TAP, irname)
        irname = irname
        return (agent, irname, 'IR')

    def get_tap_link_DR(self, TAP):

        irname = self.tapObj.get_tap_SERDR(TAP)

        if not irname:
            htdte_logger.error(" Can't find a %s.DR - field" % TAP)
        else:
            htdte_logger.inform(" Found taplink %s.DR - field: (%s)" % (TAP, irname))

        agent = self.get_real_agent(TAP, irname)
        irname = irname
        return (agent, irname, 'DR')

    def get_tap_link_CFG(self, TAP):

        irname = self.tapObj.get_taplinkEP_SERCFG(TAP)

        if not irname:
            htdte_logger.error(" Can't find a %s.CFG - field: (%s)" % (TAP, irname))
        else:
            htdte_logger.inform(" Found taplink %s.CFG - field: (%s)" % (TAP, irname))

        agent = self.get_real_agent(TAP, irname)
        irname = irname
        return (agent, irname, 'CFG')

    def get_tap_link_STATUS(self, TAP):

        irname = self.tapObj.get_taplinkEP_SERSTATUS(TAP)

        if not irname:
            htdte_logger.error(" Can't find a %s.STATUS - field" % TAP)
        else:
            htdte_logger.inform(" Found taplink %s.STATUS - field: (%s)" % (TAP, irname))

        agent = self.get_real_agent(TAP, irname)
        irname = irname
        return (agent, irname, 'STATUS')

    def get_tap_link_PARCFG(self, TAP):

        irname = self.tapObj.get_taplinkEP_PARCFG(TAP)

        if isinstance(irname, list):
            irname = ",".join(str(x) for x in irname)
            htdte_logger.inform("Parallel CFG list joined : %s" % (irname))

        if not irname:
            htdte_logger.error(" Can't find a %s.PARCFG - field: (%s)" % (TAP, irname))
        else:
            htdte_logger.inform(" Found taplink %s.PARCFG - field: (%s)" % (TAP, irname))

        agent = self.get_real_agent(TAP, irname)
        irname = irname
        return (agent, irname, 'CFG')

    def get_tap_link_PARSTATUS(self, TAP):

        irname = self.tapObj.get_taplinkEP_PARSTATUS(TAP)

        if isinstance(irname, list):
            irname = ",".join(str(x) for x in irname)
            htdte_logger.inform("Parallel STATUS list joined : %s" % (irname))

        if not irname:
            htdte_logger.error(" Can't find a %s.PARSTATUS - field" % TAP)
        else:
            htdte_logger.inform(" Found taplink %s.PARSTATUS - field: (%s)" % (TAP, irname))

        agent = self.get_real_agent(TAP, irname)
        irname = irname
        return (agent, irname, 'STATUS')

    def get_tap_link(self, TAP, mytype):

        if mytype == "SERIR":
            irname = self.tapObj.get_tap_SERIR(TAP)
        elif mytype == "SERDR":
            irname = self.tapObj.get_tap_SERDR(TAP)
        elif mytype == "PARIR":
            irname = self.tapObj.get_tap_PARIR(TAP)
        elif mytype == "PARDR":
            irname = self.tapObj.get_tap_PARDR(TAP)
        elif mytype == "SERCFG":
            irname = self.tapObj.get_taplinkEP_SERCFG(TAP)
        elif mytype == "SERSTATUS":
            irname = self.tapObj.get_taplinkEP_SERCFG(TAP)
        elif mytype == "PARCFG":
            irname = self.tapObj.get_taplinkEP_PARCFG(TAP)
        elif mytype == "PARSTATUS":
            irname = self.tapObj.get_taplinkEP_PARSTATUS(TAP)
        else:
            htdte_logger.error("Unsupported type %s used in get tap link function." % (mytype))

        if mytype.find("PAR") > -1:
            if isinstance(irname, list):
                irname = ",".join(str(x) for x in irname)
                htdte_logger.inform("Parallel STATUS list joined : %s" % (irname))

        if not irname:
            htdte_logger.error(" Can't find a %s.%s - field" % (TAP, mytype))
        else:
            htdte_logger.inform(" Found taplink %s.%s - field: (%s)" % (TAP, mytype, irname))

        agent = self.get_real_agent(TAP, irname)
        irname = irname
        return (agent, irname, mytype)

   # --------------------------

    def change_ir_field_size(
        self,
        IR,
        agent,
        field,
        new_size,
    ):
        if agent not in self.ir_field_size_override:
            self.ir_field_size_override[agent] = {}
        if IR not in self.ir_field_size_override[agent]:
            self.ir_field_size_override[agent][IR] = {}
        self.ir_field_size_override[agent][IR][field] = new_size

   # ---------------------------------------....

    def get_rtl_endpoint(
        self,
        IR,
        agent,
        field,
    ):

       # --In future SPF should manage signals , meanwile checking in dictionary if exists
        # message = "<server_get_rtl_struct> " + agent + "." + IR + "." + field + "\n"
     # rtl_endpoint_str = self.send_receive_message(message)
     # TODO should be closed with OZ (fub,node)=rtl_endpoint_str.split(":")
     # return ("soc_tb.soc.TODO_Oz_NOT_SUPPORTING_YET__%s__%s__%s")%(agent,IR,field.replace(".","_"))

        try:

           # --Trying getting the rtl node information from processed dictionary

            if agent in dict_tap_rtl_info:
                if 'cmd' not in dict_tap_rtl_info[agent]:
                    htdte_logger.error('tap_rtl_info["%s"]["cmd"]' % agent)
                ircode = self.get_ir_opcode_int(IR, agent)
                if ircode in dict_tap_rtl_info[agent]['cmd']:
                    if 'field' not in dict_tap_rtl_info[agent]['cmd'][ircode]:
                        htdte_logger.error('tap_rtl_info["%s"]["cmd"][0x%x]["field"]' % (agent, ircode))
                    if field in dict_tap_rtl_info[agent]['cmd'][ircode]['field']:
                        fab = ('' if 'rtlFub' not in dict_tap_rtl_info[agent]['cmd'][ircode]['field'
                                                                                             ][field] else '%s/' % dict_tap_rtl_info[agent]['cmd'][ircode]['field'
                                                                                                                                                           ][field]['rtlFub'])
                        if 'rtlPath' in dict_tap_rtl_info[agent]['cmd'][ircode]['field'][field]:
                            return '%s%s' % (fab, dict_tap_rtl_info[agent]['cmd'][ircode]['field'][field]['rtlPath'])
                    elif field.replace('.', '_') in dict_tap_rtl_info[agent]['cmd'][ircode]['field']:
                        fab = ('' if 'rtlFub' not in dict_tap_rtl_info[agent]['cmd'][ircode]['field'][field.replace('.', '_')] else '%s/' % dict_tap_rtl_info[agent]['cmd'][ircode]['field'
                                                                                                                                                                                    ][field.replace('.', '_')]['rtlFub'])
                        if 'rtlPath' in dict_tap_rtl_info[agent]['cmd'][ircode]['field'][field.replace('.', '_'
                                                                                                       )]:
                            return '%s%s' % (fab, dict_tap_rtl_info[agent]['cmd'][ircode]['field'][field.replace('.',
                                                                                                                 '_')]['rtlPath'])
        except NameError:

            normalize_field_name = self.normalize_field_name(IR, agent, field)
            if self.rtl_node_backdoor_exists(agent, IR, field):
                return self.get_rtl_node_backdoor(agent, IR, field)
            else:
                if not self.tapObj.has_tap_dr_field_rtl_shadow_signal(agent, IR, normalize_field_name):
                    htdte_logger.error(' <server_get_rtl_node> Cant find rtl node by agent:%s cmd:%s field:%s.\n'
                                       % (agent, IR, field))

         # ---------------

            if self.rtl_node_backdoor_exists(agent, IR, field):
                return self.get_rtl_node_backdoor(agent, IR, field)
            else:

              # fub_path_str_l = rtl_endpoint_str.replace(".","/").split("/")
              # if(len(fub_path_str_l)>0 and not HTD_INFO.signal_info.signal_module_exists(("%s")%(fub_path_str_l[0]))):
               #  htdte_logger.error( (" <server_get_rtl_node> Cant find IP tap rtl module: \"%s\"")%(fub_path_str_l[0]))
               # return rtl_endpoint_str

                return self.tapObj.get_tap_dr_field_rtl_shadow_signal(agent, IR, normalize_field_name)

   # --------------------------

    def get_full_dr(
        self,
        IR,
        agent,
        field,
        field_dr,
    ):
        htdte_logger.error('get_full_dr not supported yet')

  # Ask Alex about this -> does it come from DFX API
    # ir_fields = get_ir_fields(s,IR)
    # splitted_list = ir_fields.rsplit('\n')
    # list_len = len(splitted_list)
    # DR = ''
    # for index in range(0,list_len-1):
    # m = re.search(r'\]\s*(\S+)', splitted_list[index])
    # if m:
    # ....field_name = m.group(1)
    # ....if (field_name == field):
    # ........get_ir_opcodeDR = field_dr + DR
    # ....else:
    # ........DR = get_field_reset_value(s,IR,field_name) + DR
    # return DR
    # --------------------------

    def get_tap_PARIR(self, agent):
        htdte_logger.error('get_tap_PARIR not supported for TAP Network')

    # --------------------------

    def get_tap_PARDR(self, TAP):
        htdte_logger.error('get_tap_PARDR not supported for TAP Network')

    # --------------------------

    def get_tap_SERIR(self, agent, slice_num):

      # message = "<server_get_tap_link_cmd_name> " + agent + ".PARIR\n"
     # PARIR = self.send_receive_message(message)

        return -1

    # --------------------------

    def get_tap_SERDR(self, TAP, slice_num):

     # message = "<server_get_tap_link_cmd_name> " + agent + ".PARDR\n"
     # PARDR = self.send_receive_message(message)

        return -1

   # ---------------------------------------

    def get_ir_name(
        self,
        ircode,
        agent,
        errsuppress=0,
    ):

        irname = self.tapObj.get_tap_ir_name(agent, ircode)

        if not irname:
            if errsuppress:
                return ''
            htdte_logger.error(" Can't find IR name for  ir code - 0x%x" % ircode)
            sys.exit(1)
        return irname

   # -----------------------------

    def get_ir_size(self, agent):
        ir_size = self.tapObj.get_tap_ir_size(agent)
        if not ir_size:
            htdte_logger.error('Failed to determine ir_size for Agent: (%s)' % agent)
            sys.exit(1)
        return int(ir_size)

   # -------------------------------------

    def get_ir_access(self, IR, agent):
        return self.tapObj.get_tap_dr_access(IR, agent)

    def get_field_access(
        self,
        IR,
        agent,
        field,
    ):
        if self.tapObj.has_tap_field_access(agent, IR, field):
            ir_access = self.tapObj.get_tap_field_access(agent, IR, field)
            if ir_access is None:
                htdte_logger.error('Failed to determine ir_access for Agent: (%s) IR: (%s) Field: (%s)' % (agent, IR,
                                                                                                           field))
                sys.exit(1)
            return ir_access
        else:
            htdte_logger.error('No field ir_access for Agent: (%s) IR: (%s) Field: (%s)' % (agent, IR, field))
            sys.exit(1)

    def get_agent_pre_delay(self, agent):
        agent = agent + "_EP"
        pre_delay = self.tapObj.get_taplinkEP_pre_dr_delay_pads(agent)

        if pre_delay is None:
            pre_delay = 0
        else:
            pre_delay = pre_delay.split("b")

            pre_delay = len(pre_delay[1])

        return pre_delay

    def get_agent_post_delay(self, agent):
        agent = agent + "_EP"
        post_delay = self.tapObj.get_taplinkEP_post_dr_delay_pads(agent)
        if post_delay is None:
            post_delay = 0
        return post_delay

   # ----------------------------

    def get_taplink_parallel_agents_by_agents(self, agent):
        agents = self.tapObj.get_tap_parallel_taplink_agents(agent)

        return agents

    # workaround for agent name as some command PARDR/PARIR/LINKIR/LINKDR/TAPSTATUS/CFG
    # belong to glue tap when referring to CLTAP
    # need to be enhanced to support all types
    def get_real_agent(self, agent, IR):

        if agent.startswith("GLUE_"):
            return agent
        elif((IR.endswith(('PARSTATUS', 'PARDR', 'PARIR', 'PARCFG'))) and IR.startswith("CLTAP_")):
            agent = "GLUE_" + agent 
            return agent
			
        if not (IR.startswith("CLTAP_") and (self.tapObj.get_tap_SERIR(agent) == IR or self.tapObj.get_tap_SERDR(agent) == IR
                                             or self.tapObj.get_taplinkEP_SERCFG(agent) == IR or self.tapObj.get_taplinkEP_SERSTATUS(agent) == IR
                                             or (False if self.tapObj.get_tap_PARIR(agent) is None else (IR in self.tapObj.get_tap_PARIR(agent) or IR in self.tapObj.get_tap_PARDR(agent)
                                                                                                      or IR in self.tapObj.get_taplinkEP_PARCFG(agent) or IR in self.tapObj.get_taplinkEP_PARSTATUS(agent))) or
                                             agent == "CLTAP")):
            return agent

        #htdte_logger.inform("Begin searching for real agent for %s - %s"%(agent,IR))

        if(IR.endswith(('PARSTATUS', 'PARDR', 'PARIR', 'PARCFG'))):
            agent = "GLUE_" + agent
            #htdte_logger.inform("Agent was changed to %s" %(agent))
            return agent
        elif (IR.endswith(('_TAPSTATUS', '_TAPDR', '_TAPIR', '_TAPCFG', 'IR', 'STATUS', 'DR', 'CFG'))):
            for repl in (('_TAPSTATUS', '_TAPDR', '_TAPIR', '_TAPCFG', 'STATUS', 'CFG', 'DR', 'IR')):
                tapreplace_index = IR.rfind(repl, len(IR) - len(repl) - 1, len(IR))
                if tapreplace_index > -1:
                    break
            estr = ""
            if repl.rfind('_TAP') > -1:
                estr = "_TAP"
            agent = IR[0: tapreplace_index]
            agent = "GLUE_%s%s" % (agent, estr)
            agent = agent.replace("CLTAP_", "")
            #htdte_logger.inform("Agent was changed to %s" % (agent))
            return agent
        else:
            htdte_logger.error(('Failed to get_real_agent tap replacement for Agent: (%s) IR: (%s)') % (agent, IR))

    def dr_field_dict_info(self, agent, IR):
        if agent not in self.dr_field_dict:
            self.dr_field_dict[agent] = {}
        if IR in self.dr_field_dict[agent]:
            return
        if(IR == self.tapObj.get_tap_SERIR(agent) or IR == self.tapObj.get_tap_SERDR(agent)):
            self.dr_field_dict[agent][IR] = self.tapObj.get_tap_dr_fields(agent, IR)
        else:
            if IR not in self.dr_field_dict[agent]:
                self.dr_field_dict[agent][IR] = self.tapObj.get_tap_dr_fields(agent, IR)

        # Need to manually create the fields for TAP link IR and DR for padding purposes
        pre = None
        post = None

        if (self.tapObj.get_tap_SERIR(agent) == IR
                or (False if self.tapObj.get_tap_PARIR(agent) is None else (IR in self.tapObj.get_tap_PARIR(agent)))):
            pre = self.tapObj.get_taplinkEP_pre_dr_delay(agent)
            irsize = self.tapObj.get_tap_ir_size(agent.replace("GLUE_", "", 1))
            self.dr_field_dict[agent][IR]['IR'] = {'msb': irsize - 1, 'lsb': 0}
            if pre is not None:
                self.dr_field_dict[agent][IR]['DUMMY_HI'] = {'msb': pre + irsize, 'lsb': irsize}
        elif (self.tapObj.get_tap_SERDR(agent) == IR
                or (False if self.tapObj.get_tap_PARDR(agent) is None else (IR in self.tapObj.get_tap_PARDR(agent)))):
            pre = self.tapObj.get_taplinkEP_pre_dr_delay(agent)
            post = self.tapObj.get_taplinkEP_post_dr_delay(agent)
            self.dr_field_dict[agent][IR]['DR'] = {'msb': post, 'lsb': post}
            if post is not None:
                self.dr_field_dict[agent][IR]['DUMMY_LO'] = {'msb': post - 1, 'lsb': 0}
            if not (pre is None or post is None):
                self.dr_field_dict[agent][IR]['DUMMY_HI'] = {'msb': pre + post, 'lsb': post + 1}

    def get_taplink_network_regs(self, agent):

        taplink_nw = self.tapObj.get_tap_taplink_network_regs(agent)
        #taplink_nw = [re.sub('[\[].*?[\]]', '', taplink) for taplink in taplink_nw]

        return taplink_nw
