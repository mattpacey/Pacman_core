from htd_utilities import *


class HtdPatmod(object):
    """
    HtdPatmod class - basic instantiation of a Patmod
    """

    def __init__(self, name, desc=None):
        """
        """
        self.name = name
        self.desc = desc
        self.usages = list()
        self.values = dict()

    def __eq__(self, other):
        if self is other:
            return True
        elif not isinstance(self, type(other)):
            return False
        else:
            for usage in other.usages:
                if not self.check_usage_exists(usage):
                    return False

            for value in other.values:
                if value not in self.values or other.values[value] != self.values[value]:
                    return False

            if self.name != other.name or self.desc != other.desc:
                return False

    def get_num_usages(self):
        """
        Returns the number of usages associated with this patmod
        :return: The number of the usages
        :rtype: int
        """
        return len(self.usages)

    def get_usages(self):
        """
        Get all of the usages for this patmod
        :return: The usages for this patmod
        :rtype: list(HtdPatmodUsage)
        """
        return self.usages

    def add_usage(self, patmod_usage):
        """
        Function to add a patmod usage

        :param HtdPatmodUsage usage: The usage object to add
        """

        # Check to make sure this usage doesn't already exist
        if not self.check_usage_exists(patmod_usage):
            # Add the new patmod usage to usages of this patmod
            self.usages.append(patmod_usage)

    def add_usage_by_parts(self, network, agent, register=None, field=None, bits=None):
        """
        Function to add a patmod usage

        :param network: The network for this patmod (e.g. tap, fuse, xreg, etc)
        :param agent: The agent (e.g. endpoint or fusename)
        :param register: The register the patmod applies to
        :param field: The field the patmod applies to
        :param bits: The bits the patmod applies to
        """
        # create a usage object
        patmod_usage = HtdPatmodUsage(network, agent, register, field, bits)
        self.add_usage(patmod_usage)

    def check_usage_exists(self, test_usage):
        """
        A function to check if a particular usage already exists for this patmod
        :param test_usage:
        :return: Whether the usage already exists for this patmod
        :rtype: bool
        """
        for usage in self.usages:
            if usage == test_usage:
                return True

        return False

    def add_value(self, value_name, value):
        """
        Function to add a new value to this patmod
        :param str value_name:
        :param str value:
        :rtype: None
        """
        if value_name not in self.values:
            self.values[value_name] = value
        else:
            htdte_logger.error("Value name %s already exists in patmod %s" % (value_name, self.name))

    def get_values(self):
        return self.values

    def print_patmod_info(self):
        """
        Prints out all of the info about this patmod
        Patmod Name:
            Usages -
                - TAP: Agent=>Register->Field[msb:lsb]
                - XREG: Register->Field[msb:lsb]
                - FUSE: Agent

            Values -
                   Name   |   Value
                ----------+-----------
                  value0  |     0
                  value1  |     1
                  ...     |    ...
                  valueN  |     N

        :return: None
        """
        # Print this patmod name
        htdte_logger.inform("PATMOD: " + self.name)
        htdte_logger.inform("    Usages -")

        # Print the usages
        for usage in self.usages:
            str = "        - "
            str += "%s: " % usage.network.upper()
            printed_agent = False
            printed_reg = False
            printed_field = False

            if usage.agent is not None and usage.agent != "":
                str += usage.agent
                printed_agent = True

            if usage.register is not None and usage.register != "":
                if printed_agent:
                    str += "=>"

                str += usage.register
                printed_reg = True

            if usage.field is not None and usage.field != "":
                if printed_reg:
                    str += "->"

                str += usage.field
                printed_field = True

            if usage.bits is not None and usage.bits != "":
                str += "[%s]" % usage.bits

            htdte_logger.inform(str)

        # Print Values
        htdte_logger.inform("")
        htdte_logger.inform("    Values -")
        min_name_len = 8
        min_value_len = 9
        max_name_len = len(max(list(self.values.keys()), key=len)) + 4
        max_value_len = len(max(list(self.values.values()), key=len)) + 4

        if min_name_len > max_name_len:
            max_name_len = min_name_len

        if min_value_len > max_value_len:
            max_value_len = min_value_len

        htdte_logger.inform("        {:{}}|{:{}}".format("  Name", max_name_len, "  Value", max_value_len))
        htdte_logger.inform("        {:^{}}+{:^{}}".format("-" * max_name_len, max_name_len, "-" * max_value_len, max_value_len))
        for name, value in sorted(iter(self.values.items()), key=lambda k_v: (k_v[1], k_v[0])):
            # if value != "X":
            #     value = int(value)
            htdte_logger.inform("        {:{}}|{:{}}".format("  " + name, max_name_len, "  " + value, max_value_len))

        htdte_logger.inform("")
        htdte_logger.inform("")


class HtdPatmodGroup(object):
    """
    HtdPatmodGroup class - basic instantiation of a PatmodGroup
    """

    def __init__(self, name, mode):
        """

        :param name: Name of the group
        :param mode: group_only or group_split
        """
        self.name = name
        self.mode = mode
        self.members = list()

    def add_member(self, member_name):
        if member_name not in self.members:
            self.members.append(member_name)
        else:
            htdte_logger.error("Member name %s already exists in patmod  group %s" % (member_name, self.name))

    def get_members(self):
        """

        :return: List of patmods in group
        :rtype: list
        """
        return self.members


class HtdPatmodUsage(object):
    """
    HtdPatmodUsage class - basic instantiation of a patmod usage
    """

    def __init__(self, network=None, agent=None, register=None, field=None, bits=None, action_name=None, label_ext=None):
        """
        :param string network: The network for this patmod (e.g. tap, fuse, xreg, etc)
        :param string agent: The agent (e.g. endpoint or fusename)
        :param string register: The register the patmod applies to
        :param string field: The field the patmod applies to
        :param string bits: The bits the patmod applies to
        :param string action_name: The action this specific usage is valid for
        :param string label_ext: An extension to the auto_generated label to create a unique label for each usage
        """
        self.network = network
        self.agent = agent
        self.register = register
        self.field = field
        self.bit_chunks = list()
        self.bits = bits
        self.label_ext = label_ext

        self.action_name = action_name

        self.related_usages = list()

    def __setattr__(self, key, value):
        """
        Overrides the super __setattr__ handler. Gives additional flexibility when self.bits is set to split bits
        out into msb and lsb and supports non-contiguous bits
        :param str key: The instance variable to set.
        :param value:
        :return:
        """
        if key == "bits":
            # Make sure bits is stored as a string. If it is a number in the XML Pacman will convert it to an int and
            # the split below will fail
            super(HtdPatmodUsage, self).__setattr__(key, str(value) if value is not None else None)
            self.split_bits()
            pass
        else:
            super(HtdPatmodUsage, self).__setattr__(key, value)

    def __eq__(self, other):
        if self is other:
            return True
        elif not isinstance(self, type(other)):
            return False
        else:
            if self.field is None and self.network == other.network and self.agent == other.agent and \
                    self.register == other.register and self.field == other.field and \
                    self.action_name == other.action_name:
                return True
            elif self.network == other.network and self.agent == other.agent and self.register == other.register and \
                    self.field == other.field and self.bits == other.bits and self.action_name == other.action_name:
                return True
            else:
                return False

    def split_bits(self):
        self.bit_chunks = list()
        if self.bits is not None:
            # Handle non-consecutive bits
            for bit_chunk in self.bits.split(","):

                # Split bits to msb and lsb
                split_vals = bit_chunk.split(":")
                num_vals = len(split_vals)

                # Split this entry into msb and lsb
                lsb = 0
                msb = 0
                if num_vals == 1:
                    msb = int(split_vals[0])
                    lsb = int(split_vals[0])
                elif num_vals == 2:
                    msb = int(split_vals[0])
                    lsb = int(split_vals[1])
                else:
                    htdte_logger.error("Expecting 1 or 2 values for msb:lsb format, received %d" % num_vals)

                # Make sure that lsb is less than msb
                if lsb > msb:
                    # Reverse msb and lsb
                    tmp = lsb
                    lsb = msb
                    msb = tmp

                if len(self.bit_chunks) > 0 and msb == self.bit_chunks[-1]["lsb"] - 1:
                    self.bit_chunks[-1]["lsb"] = lsb
                else:
                    self.bit_chunks.append({"msb": msb, "lsb": lsb})

            # Update bits with merged ranges if they exist
            super(HtdPatmodUsage, self).__setattr__("bits", ",".join("%d:%d" % (d["msb"], d["lsb"]) for d in self.bit_chunks))

    def check_self_usages_matching_register_field(self, network, agent, register, field, action_name, msb=None, lsb=None):
        if self.check_usage_matching_register_field(network, agent, register, field, action_name, msb, lsb):
            return self

        return None

    def check_self_and_related_usages_matching_register_field(self, network, agent, register, field, action_name, msb=None, lsb=None):
        if self.check_usage_matching_register_field(network, agent, register, field, action_name, msb, lsb):
            return self
        else:
            for usage in self.related_usages:
                if usage.check_usage_matching_register_field(network, agent, register, field, action_name, msb, lsb):
                    return usage

        return None

    def check_usage_matching_register_field(self, network, agent, register, field, action_name, msb=None, lsb=None):
        action_check = False
        if self.action_name is None or action_name is None:
            action_check = True
        elif self.action_name.lower() == action_name.lower():
            action_check = True

        agent_check = False
        if self.agent is None or agent is None:
            agent_check = True
        elif self.agent.lower() == agent.lower():
            agent_check = True

        field_check = False
        if self.field is None or field is None:
            field_check = True
        elif self.field.lower() == field.lower():
            field_check = True

        if action_check and agent_check and field_check and \
                self.network.lower() == network.lower() and self.register.lower() == register.lower():
            if msb is None and lsb is None:
                return True
            else:
                if msb is None:
                    msb = lsb
                elif lsb is None:
                    lsb = msb

                for bit_chunk in self.bit_chunks:
                    if bit_chunk["msb"] >= msb and bit_chunk["lsb"] <= lsb:
                        return True
        return False

    def check_self_and_related_usages_matching_register(self, network, agent, register, action_name):
        if self.check_usage_matching_register(network, agent, register, action_name):
            return [self]
        else:
            ret_usages = list()
            for usage in self.related_usages:
                if usage.check_usage_matching_register(network, agent, register, action_name):
                    ret_usages.append(usage)
            return ret_usages

        return None

    def check_usage_matching_register(self, network, agent, register, action_name):
        if (self.action_name is None or self.action_name.lower() == action_name.lower()) and \
                self.network.lower() == network.lower() and self.agent.lower() == agent.lower() and \
                self.register.lower() == register.lower():
            return True
        return False

    def add_related_usage(self, network, agent, register=None, field=None, bits=None, action_name=None, label_ext=None):
        """
        Function to add a related patmod usage

        :param string network: The network for this patmod (e.g. tap, fuse, xreg, etc)
        :param string agent: The agent (e.g. endpoint or fusename)
        :param string register: The register the patmod applies to
        :param string field: The field the patmod applies to
        :param string bits: The bits the patmod applies to
        :param string action_name: The action this usage is valid for
        """
        # create a usage object
        patmod_usage = HtdPatmodUsage(network, agent, register, field, bits, action_name, label_ext)
        rel_usage = self.check_if_related_usage_exists(patmod_usage)

        # Check to make sure this usage doesn't already exist
        if not rel_usage:
            # Add the new patmod usage to usages of this patmod
            self.related_usages.append(patmod_usage)
            return patmod_usage

        elif field is None:
            # Return usage
            return rel_usage

    def check_if_related_usage_exists(self, test_usage):
        """
        A function to check if a particular related usage already exists for this usage
        :param test_usage: The new usage to check against
        :return: Whether the usage already exists for this usage
        :rtype: bool
        """
        for usage in self.related_usages:
            if usage == test_usage:
                return usage

        return False


class HtdPatmodManager(object):
    """
    Class for managing all Patmods
    """

    def __init__(self):
        self.patmods = list()
        self.patmodgroups = list()
        self.temp_patmods = list()
        self.enabled = 1

    def __iter__(self):
        return iter(self.patmods)

    def global_patmods_enabled(self):
        if self.get_num_patmods() > 0 and self.enabled == 1:
            return True

        return False

    def get_num_patmods(self):
        """
        Returns the number of patmods in the tracker
        :return: number of patmods in the tracker
        :rtype: int
        """
        return len(self.patmods)

    def get_patmods(self):
        """
        Function to get all patmods
        :return: All patmods
        :rtype: list
        """
        return self.patmods

    def get_patmodgroups(self):
        """
        Function to get all patmodgroupss
        :return: All patmodgroups
        :rtype: [HtdPatmodGroup]
        """
        return self.patmodgroups

    def add_patmod(self, patmod):
        """
        Function to add a patmod to the patmod manager
        :param HtdPatmod patmod: The patmod to add
        """
        # Check if this patmod already exists in the patmod manager
        if not self.check_patmod_exists(patmod):
            self.patmods.append(patmod)

    def check_patmod_exists(self, patmod):
        for test_patmod in self:
            if test_patmod == patmod:
                return True

        return False

    def add_patmodgroup(self, patmodgroup):
        """
        Function to add a patmod to the patmod manager
        :param HtdPatmodGroup patmodgroup: The patmod to add
        """
        # Check if this patmod already exists in the patmod manager
        if not self.check_patmod_exists(patmodgroup):
            self.patmodgroups.append(patmodgroup)

    def check_patmodgroup_exists(self, patmodgroup):
        for test_patmodgroup in self:
            if test_patmodgroup == patmodgroup:
                return True

        return False

    def add_related_usage_for_network_agent_match(self, network, agent, rel_network, rel_agent, register,
                                                  field=None, bits=None, action_name=None, label_ext=None):
        """
        Add a related usage for a particular action. These patmods are only valid for that action
        :param string actionName:
        :param string network: The network to check against
        :param string agent: The agent name to check against
        :param rel_network: The network for this patmod (e.g. tap, fuse, xreg, etc)
        :param rel_agent: The agent (e.g. endpoint or fusename)
        :param register: The register the patmod applies to
        :param field: The field the patmod applies to
        :param bits: The bits the patmod applies to
        """
        for patmod in self:
            for usage in patmod.get_usages():
                if usage.network.lower() == network.lower():
                    if (usage.agent.lower() == agent.lower() and network.lower() != "fuse") or (usage.agent.lower().replace('.', '_') == agent.lower() and network.lower() == "fuse"):
                        # Add this to the patmod info
                        # name, network, agent, reg, field, bits=None
                        usage.add_related_usage(rel_network, rel_agent, register, field, bits, action_name, label_ext)

    def add_related_usage_for_network_usage_match(self, network, agent, register, field, rel_network, rel_agent,
                                                  rel_register, rel_field=None, bits=None, action_name=None):
        """
        Add a related usage for a particular action. These patmods are only valid for that action
        :param string actionName:
        :param string network: The network to check against
        :param string agent: The agent name to check against
        :param string register: The register name to check against
        :param rel_network: The network for this patmod (e.g. tap, fuse, xreg, etc)
        :param rel_agent: The agent (e.g. endpoint or fusename)
        :param rel_register: The register the patmod applies to
        :param rel_field: The field the patmod applies to
        :param bits: The bits the patmod applies to
        """
        for patmod in self:
            for usage in patmod.get_usages():
                tmp_agent = usage.agent
                # Do some data manipulation if on xreg network
                if network.lower() == "xreg":
                    if agent is None or usage.agent is None:
                        agent = None
                        tmp_agent = None
                if usage.network.lower() == network.lower():
                    if tmp_agent is None or tmp_agent.lower() == agent.lower():
                        if usage.register.lower() == register.lower():
                            if usage.field.lower() == field.lower():
                                # Add this to the patmod info
                                # name, network, agent, reg, field, bits=None
                                return usage.add_related_usage(rel_network, rel_agent, rel_register, rel_field, bits, action_name)

    def check_patmod_vars(self, patmod_vars):
        """
        Do some checking on patmod_vars
        :param patmod_vars:
        :return:
        """
        # Do some checking on patmod_vars
        temp_patmod_vars = list(patmod_vars)
        patmod_vars = list()
        for patmod_var in temp_patmod_vars:
            if patmod_var is not None and patmod_var.strip() != "":
                patmod_vars.append(patmod_var.strip())

        return patmod_vars

    def get_patmods_for_register_field(self, network, agent, register, field, patmod_in, patmod_out,
                                       action_name, patmod_vars=None, msb=None, lsb=None):
        '''
        Determine if this register has patmods for it


        :param string network: Name of the network this register is on (tap, stf), etc)
        :param string agent: The agent to look at
        :param string register: Name of the register to look at
        :param string field: Name of the field to look at
        :param boolean patmod_in: This patmod is for in
        :param boolean patmod_out: This patmod is for out
        :param list of str patmod_vars: The names of a specific patmod variable to get
        :return: A list of patmods matching the given network, agent, register, and field
        :rtype: list of dict
        '''
        network = network.lower()
        register = register.lower()
        field = field.lower()
        patmods = list()

        # Do some checking on patmod_vars
        patmod_vars = self.check_patmod_vars(patmod_vars)

        # Loop over HTD_INFO.patmods
        for patmod in self.patmods:
            if len(patmod_vars) > 0 and patmod.name not in patmod_vars:
                continue
            for usage in patmod.usages:
                final_patmod = dict()
                matching_usage = usage.check_self_and_related_usages_matching_register_field(network, agent, register,
                                                                                             field, action_name, msb, lsb)
                if matching_usage is not None:
                    final_patmod["name"] = patmod.name
                    # Returning two entries for field. Some action code overrides field to other values, but we want
                    # to be able to track the original register field as well
                    final_patmod["reg_field"] = matching_usage.field
                    final_patmod["field"] = matching_usage.field
                    final_patmod["bits"] = matching_usage.bits
                    final_patmod["value"] = list(patmod.values.keys())[0]
                    final_patmod["type"] = ""
                    in_out_label = ""
                    if patmod_in == 1 and patmod_out == 1:
                        in_out_label = "in_out"
                    elif patmod_in == 1:
                        in_out_label = "in"
                    elif patmod_out == 1:
                        in_out_label = "out"

                    final_patmod["type"] = in_out_label

                    final_patmod["label"] = "%s__patmod_%s__%s" % (action_name, in_out_label, patmod.name)

                    if matching_usage.label_ext is not None:
                        final_patmod["label"] += "_%s" % matching_usage.label_ext

                    patmods.append(final_patmod)

        return patmods

    def get_all_overlapping_patmods_for_register_field(self, network, agent, register, field, patmod_in, patmod_out,
                                                       action_name, msb, lsb, patmod_vars=None):
        '''
        Determine if this register has patmods for it


        :param string network: Name of the network this register is on (tap, stf), etc)
        :param string agent: The agent to look at
        :param string register: Name of the register to look at
        :param string field: Name of the field to look at
        :param boolean patmod_in: This patmod is for in
        :param boolean patmod_out: This patmod is for out
        :param list of str patmod_vars: The names of a specific patmod variable to get
        :return: A list of patmods matching the given network, agent, register, and field
        :rtype: list of dict
        '''
        network = network.lower()
        register = register.lower()
        field = field.lower()
        patmods = list()

        # Do some checking on patmod_vars
        patmod_vars = self.check_patmod_vars(patmod_vars)

        # Loop over HTD_INFO.patmods
        for patmod in self.patmods:
            if len(patmod_vars) > 0 and patmod.name not in patmod_vars:
                continue
            for usage in patmod.usages:
                final_patmod = dict()
                matching_usage = usage.check_self_usages_matching_register_field(network, agent, register,
                                                                                 field, action_name, msb=None, lsb=None)
                if matching_usage is not None:
                    # Check if the bits from this usage overlap with the msb/lsb passed in
                    if matching_usage.bits is not None:
                        overlapping = False
                        for bit_chunk in matching_usage.bit_chunks:
                            overlapping = False
                            tmp_msb = bit_chunk["msb"]
                            tmp_lsb = bit_chunk["lsb"]

                            ol_lsb = -1
                            ol_msb = -1
                            if lsb is None or msb is None:
                                continue
                            if tmp_lsb >= lsb and tmp_lsb <= msb:
                                ol_lsb = tmp_lsb
                                overlapping = True
                            elif tmp_lsb < lsb and tmp_msb >= lsb:
                                ol_lsb = lsb
                                overlapping = True

                            if tmp_msb <= msb and tmp_msb >= lsb:
                                ol_msb = tmp_msb
                                overlapping = True
                            elif tmp_msb > msb and tmp_lsb <= msb:
                                ol_msb = msb
                                overlapping = True

                            if overlapping:
                                break

                        # If this usage doesn't overlap at all, go to the next usage
                        if not overlapping:
                            continue

                    # If there are no bits specified in the matching_usage then it matches by default
                    final_patmod["name"] = patmod.name
                    # Returning two entries for field. Some action code overrides field to other values, but we want
                    # to be able to track the original register field as well
                    final_patmod["reg_field"] = matching_usage.field
                    final_patmod["field"] = matching_usage.field
                    final_patmod["bits"] = matching_usage.bits
                    final_patmod["value"] = list(patmod.values.keys())[0]
                    final_patmod["type"] = ""
                    in_out_label = ""
                    if patmod_in == 1 and patmod_out == 1:
                        in_out_label = "in_out"
                    elif patmod_in == 1:
                        in_out_label = "in"
                    elif patmod_out == 1:
                        in_out_label = "out"

                    final_patmod["type"] = in_out_label

                    final_patmod["label"] = "%s__patmod_%s__%s" % (action_name, in_out_label, patmod.name)

                    if matching_usage.label_ext is not None:
                        final_patmod["label"] += "_%s" % matching_usage.label_ext

                    patmods.append(final_patmod)

        return patmods

    def get_patmods_for_register(self, network, agent, register, patmod_in, patmod_out, action_name, patmod_vars=None):
        '''
        Determine if this register has patmods for it

        :param string network: Name of the network this register is on (tap, stf), etc)
        :param string agent: The agent to look at
        :param string register: Name of the register to look at
        :param boolean patmod_in: This patmod is for in
        :param boolean patmod_out: This patmod is for out
        :param str action_name: The name of the action for this patmod
        :param list of str patmod_vars: A list of patmod var names to look for
        :return: A list of patmods matching the given network, agent, register, and field
        :rtype: list of dict
        '''
        network = network.lower()
        register = register.lower()
        patmods = list()

        # Do some checking on patmod_vars
        patmod_vars = self.check_patmod_vars(patmod_vars)

        # Loop over HTD_INFO.patmods
        for patmod in self.patmods:
            if len(patmod_vars) > 0 and patmod.name not in patmod_vars:
                continue

            for usage in patmod.usages:
                matching_usages = list()
                matching_usages = usage.check_self_and_related_usages_matching_register(network, agent, register,
                                                                                        action_name)
                if matching_usages is not None and len(matching_usages) > 0:
                    for matching_usage in matching_usages:
                        final_patmod = dict()
                        final_patmod["name"] = patmod.name
                        # Returning two entries for field. Some action code overrides field to other values, but we want
                        # to be able to track the original register field as well
                        final_patmod["reg_field"] = matching_usage.field
                        final_patmod["field"] = matching_usage.field
                        final_patmod["bits"] = matching_usage.bits
                        final_patmod["value"] = list(patmod.values.keys())[0]
                        final_patmod["type"] = ""
                        in_out_label = ""
                        if patmod_in == 1 and patmod_out == 1:
                            in_out_label = "in_out"
                        elif patmod_in == 1:
                            in_out_label = "in"
                        elif patmod_out == 1:
                            in_out_label = "out"

                        final_patmod["type"] = in_out_label

                        final_patmod["label"] = "%s__patmod_%s__%s" % (action_name, in_out_label, patmod.name)

                        if matching_usage.label_ext is not None:
                            final_patmod["label"] += "_%s" % matching_usage.label_ext

                        patmods.append(final_patmod)

        return patmods
