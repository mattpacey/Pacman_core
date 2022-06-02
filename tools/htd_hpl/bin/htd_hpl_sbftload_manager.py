from htd_utilities import *
from htd_collaterals import *
from htd_te_shared import *
#from htd_player_top import *
from htd_basic_action import *


class hpl_SbftLoadManager(object):
    def __init__(self, interface=None, uiptr=None):
        self.interface = interface
        self.uiptr = uiptr
        # self.interactive_mode=interactive_mode
        self.handler = None

    def set_mode(self, mode):
        self.handler = eval(("hpl_SbftLoadManager_%s") % (mode))(self.interface, self.uiptr)

    def load_cache(self, injection_file):
        self.handler.load_cache(injection_file)


# ----------------------------------------------------------------
class hpl_SbftLoadManager_injection_te(hpl_SbftLoadManager):
    def __init__(self, interface=None, uiptr=None):
        hpl_SbftLoadManager.__init__(self, interface, uiptr)

    def load_cache(self, injection_file):
        htdte_logger.inform("    Using cache injection from %s injection file" % (injection_file))
        for line in open(injection_file):
            split_line = re.split(r"\s+", line)
            full_signal = HTD_INFO.signal_info.extract_full_signal_path(split_line[0], -1, -1, "")
            full_signal = re.sub(r'^\[\'(.+)\'\]$', r'\1', str(full_signal))
            full_signal = re.sub(r'\[(\d+):\d+\]', r'[\1]', full_signal)
            value = split_line[1]
            htdte_logger.inform(("       Injecting signal %s with Value %s") % (full_signal, str(split_line[1])))
            self.interface.signal_set(full_signal, int(value, 0))

# ----------------------------------------------------------------


class hpl_SbftLoadManager_injection_svtb(hpl_SbftLoadManager):
    def __init__(self, interface=None, uiptr=None):
        hpl_SbftLoadManager.__init__(self, interface, uiptr)

    def load_cache(self, injection_file):
        htdte_logger.inform(("       Injecting signal %s for trigger cache loading") % (os.environ.get('HTD_SBFT_CPL_TRIGGER_SIGNAL')))
        self.interface.signal_set(os.environ.get('HTD_SBFT_CPL_TRIGGER_SIGNAL'), 1)
        self.interface.signal_wait(os.environ.get('HTD_SBFT_CPL_TRIGGER_SIGNAL'), 0, self.interface.cycles2time("bclk", 10000))  # FIXME: once signal_wait will support all 4 inputs..

# ----------------------------------------------------------------


class hpl_SbftLoadManager_mci(hpl_SbftLoadManager):
    def __init__(self, interface=None, uiptr=None):
        hpl_SbftLoadManager.__init__(self, interface, uiptr)

    def load_cache(self, load_file):
        htdte_logger.inform("Loading the cache with file %s" % (load_file))
        self.interface.add_comment("Cache load file: %s" % (load_file))
        line_num = 0
        for line in open(load_file):
            line_num = line_num + 1
            if (CFG["HPL"]["execution_mode"] == "spf"):
                htdte_logger.inform("Copying line %d (%s) to main SPF file" % (line_num, line))
                self.interface.send_action(line)
            else:
                if ((not re.match(r'^\s*#', line)) and (re.match(r'^rem:\s*force_signal', line) or re.match(r'^rem:\s*wait', line) or re.match(r'^vector:\s*ddr', line))):
                    htdte_logger.inform(("copying line %s to main ITPP file") % (line))
                    self.interface.insert_line(("%s\n") % (line))
# ----------------------------------------------------------------


class hpl_SbftLoadManager_mci_serial(hpl_SbftLoadManager):
    def __init__(self, interface=None, uiptr=None):
        hpl_SbftLoadManager.__init__(self, interface, uiptr)

    def load_cache(self, load_file):
        for line in open(load_file):
            if (CFG["HPL"]["execution_mode"] == "spf"):
                htdte_logger.inform("Copying line %s to main SPF file" % (line))
                self.interface.send_action(line)
            else:
                if ((not re.match(r'^\s*#', line)) and (not re.match(r'^vector:\s*xxTMS', line))):
                    htdte_logger.inform(("copying line %s to main ITPP file") % (line))
                    self.interface.insert_line(("%s") % (line))


# ---------------------------------------------------------------------

class hpl_SbftLoadManager_tap(hpl_SbftLoadManager):
    def __init__(self, interface=None, uiptr=None):
        hpl_SbftLoadManager.__init__(self, interface, uiptr)

    def load_cache(self, load_file):
        #htdte_logger.inform( ("       Injecting signal %s for trigger cache loading")%(os.environ.get('HTD_SBFT_CPL_TRIGGER_SIGNAL')))
        #self.interface.print_header("rem: bla bla")
        for line in open(load_file):
            if (CFG["HPL"]["execution_mode"] == "itpp"):
                if ((not re.match(r'^\s*#', line)) and (re.match(r'^rem:\s*force_signal', line) or re.match(r'^rem:\s*wait', line))):
                    htdte_logger.inform(("copying line %s to main ITPP file") % (line))
                    self.interface.insert_line(("%s") % (line))
            elif (CFG["HPL"]["execution_mode"] == "spf"):
                htdte_logger.inform("Copying line %s to main SPF file" % (line))
                self.interface.send_action(line)

# ---------------------------------------------------------------------


class hpl_SbftLoadManager_dynamic_cache_preload(hpl_SbftLoadManager):
    def __init__(self, interface=None, uiptr=None):
        hpl_SbftLoadManager.__init__(self, interface, uiptr)

    def load_cache(self, load_file):
        #htdte_logger.inform( ("       Injecting signal %s for trigger cache loading")%(os.environ.get('HTD_SBFT_CPL_TRIGGER_SIGNAL')))
        #self.interface.print_header("rem: bla bla")
        for line in open(load_file):
            if (CFG["HPL"]["execution_mode"] == "itpp"):
                if ((not re.match(r'^\s*#', line)) and (re.match(r'^rem:\s*force_signal', line) or re.match(r'^rem:\s*wait', line))):
                    htdte_logger.inform(("copying line %s to main ITPP file") % (line))
                    self.interface.insert_line(("%s") % (line))
            elif (CFG["HPL"]["execution_mode"] == "spf"):
                htdte_logger.inform("Copying line %s to main SPF file" % (line))
                self.interface.send_action("pass itpp \"%s\"; \n" % (line))

# ----------------------------------------------------------------------
