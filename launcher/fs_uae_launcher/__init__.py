from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from __future__ import unicode_literals

import os
import sys
import logging
import codecs
import platform
import threading

# using this lock to serialize logging from different threads
lock = threading.Lock()

class NullOutput(object):

    def flush(self):
        pass

    def isatty(self):
        return False

    def write(self, msg):
        pass

class MultiOutput:

    def __init__(self, *files):
        self.files = files

    def flush(self):
        with lock:
            for f in self.files:
                try:
                    f.flush()
                except Exception:
                    pass

    def isatty(self):
        return False

    def write(self, msg):
        with lock:
            for f in self.files:
                try:
                    f.write(msg)
                except Exception:
                    pass

class FileOutput(object):

    def __init__(self, file_obj):
        self.file = file_obj

    def flush(self):
        return self.file.flush()

    def isatty(self):
        return False

    def write(self, msg):
        if isinstance(msg, unicode):
            if "database_password" in msg:
                return
            self.file.write(msg.encode("UTF-8"))
        else:
            if b"database_password" in msg:
                return
            self.file.write(msg)

class SafeOutput(object):

    def __init__(self, file_obj, in_charset, out_charset):
        try:
            self.writer = codecs.getwriter(out_charset)
        except LookupError:
            self.writer = codecs.getwriter('ASCII')
        self.in_charset = in_charset
        self.outfile = self.writer(file_obj, errors='replace')
        self.thread_local = threading.local()

    def flush(self):
        if hasattr(self.thread_local, 'write_func'):
            return
        try:
            if hasattr(self.outfile, 'flush'):
                self.outfile.flush()
        except Exception:
            pass

    def isatty(self):
        if hasattr(self.thread_local, 'write_func'):
            return False
        return self.outfile.isatty()

    def redirect_thread_output(self, write_func):
        if write_func is None:
            del self.thread_local.write_func
        else:
            self.thread_local.write_func = write_func

    def write(self, msg):
        if hasattr(self.thread_local, 'write_func'):
            if isinstance(msg, unicode):
                self.thread_local.write_func(msg)
                return
            msg = unicode(str(msg), self.in_charset, 'replace')
            self.thread_local.write_func(msg)
            return
        try:
            if isinstance(msg, unicode):
                self.outfile.write(msg)
            else:
                msg = unicode(str(msg), self.in_charset, 'replace')
                self.outfile.write(msg)
        except Exception:
            try:
                self.outfile.write(repr(msg))
            except Exception, e:
                self.outfile.write("EXCEPTION IN SAFEOUTPUT: %s\n" % repr(e))

def fix_output():
    sys._replaced_stdout = sys.stdout
    sys._replaced_stderr = sys.stderr
    if sys.platform == 'win32' and not os.environ.has_key('FS_FORCE_STDOUT'):
        if hasattr(sys, 'frozen'):
            sys.stdout = NullOutput()
            sys.stderr = NullOutput()
            return
        import win32console
        if win32console.GetConsoleWindow() == 0:
            # not running under console
            sys.stdout = NullOutput()
            sys.stderr = NullOutput()
            return
    try:
        if sys.platform == 'win32':
            sys.stdout = SafeOutput(sys.stdout, 'mbcs', 'cp437')
        else:
            sys.stdout = SafeOutput(sys.stdout, 'ISO-8859-1',
                    locale.getpreferredencoding())
    except Exception:
        sys.stdout = SafeOutput(sys.stdout, 'ISO-8859-1', 'ASCII')
    try:
        if sys.platform == 'win32':
            sys.stderr = SafeOutput(sys.stderr, 'mbcs', 'cp437')
        else:
            sys.stderr = SafeOutput(sys.stderr, 'ISO-8859-1',
                    locale.getpreferredencoding())
    except Exception:
        sys.stderr = SafeOutput(sys.stderr, 'ISO-8859-1', 'ASCII')

def setup_logging():
    from .Settings import Settings
    logs_dir = Settings.get_logs_dir()
    log_file = os.path.join(logs_dir, "Launcher.log.txt")
    try:
        f = open(log_file, "wb")
    except Exception:
        print("could not open log file")
        # use MultiOutput here too, for the mutex handling
        sys.stdout = MultiOutput(sys.stdout)
        sys.stderr = MultiOutput(sys.stderr)
    else:
        sys.stdout = MultiOutput(FileOutput(f), sys.stdout)
        sys.stderr = MultiOutput(FileOutput(f), sys.stderr)

    logging.basicConfig(stream=sys.stdout, level=logging.NOTSET)

def setup_portable_launcher():
    from .Settings import Settings
    path = os.path.dirname(os.path.abspath(sys.executable))
    last = ""
    while last != path:
        portable_ini_path = os.path.join(path, "Portable.ini")
        print("checking", portable_ini_path)
        if os.path.exists(portable_ini_path):
            print("detected portable dir", path)
            Settings.base_dir = path
            return
        last = path
        path = os.path.dirname(path)
    print("no Portable.ini found in search path")

def main():
    fix_output()
    if "--joystick-config" in sys.argv:
        print("importing pygame")
        import pygame
        print("initializing pygame")
        pygame.init()
        pygame.joystick.init()
        from fs_uae_launcher.JoystickConfigDialog import joystick_config_main
        return joystick_config_main()

    if "--server" in sys.argv:
        from fs_uae_launcher.server.game import run_server
        return run_server()

    from .Version import Version
    print("FS-UAE Launcher {0}".format(Version.VERSION))
    print("System: {0}".format(repr(platform.uname())))
    print(sys.argv)

    from .Settings import Settings
    for arg in sys.argv:
        if arg.startswith("--"):
            if "=" in arg:
                key, value = arg[2:].split("=", 1)
                key = key.replace("-", "_")
                if key == "base_dir":
                    value = os.path.abspath(value)
                    print("setting base_dir")
                    Settings.base_dir = value
    if Settings.base_dir:
        print("base_dir was specified so we will not check for portable dir")
    else:
        setup_portable_launcher()
    if not Settings.base_dir:
        print("base_dir not decided yet, checking FS_UAE_BASE_DIR")
        if "FS_UAE_BASE_DIR" in os.environ and os.environ["FS_UAE_BASE_DIR"]:
            print("base dir specified by FS_UAE_BASE_DIR")
            Settings.base_dir = os.environ["FS_UAE_BASE_DIR"]
    if not Settings.base_dir:
        print("using default base_dir")

    setup_logging()

    from .ConfigChecker import ConfigChecker
    config_checker = ConfigChecker()

    from .FSUAELauncher import FSUAELauncher
    application = FSUAELauncher()
    application.run()
    application.save_settings()
