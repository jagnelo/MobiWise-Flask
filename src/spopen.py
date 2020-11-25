import subprocess


# SPopen (Startable Popen) is a simple alternative to the subprocess.Popen class which, rather than
# spawn a subprocess upon calling the constructor (i.e., __init()__), simply stores the arguments
# that should be passed to a Popen instance
# Upon calling the start() method, a proper subprocess.Popen object is constructed using the stored
# arguments, and returned
class SPopen:
    def __init__(self, args, bufsize=-1, executable=None, stdin=None, stdout=None, stderr=None, preexec_fn=None,
                 close_fds=True, shell=False, cwd=None, env=None, universal_newlines=None, startupinfo=None,
                 creationflags=0, restore_signals=True, start_new_session=False, pass_fds=(), *, encoding=None,
                 errors=None, text=None):
        self.args = args
        self.bufsize = bufsize
        self.executable = executable
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr
        self.preexec_fn = preexec_fn
        self.close_fds = close_fds
        self.shell = shell
        self.cwd = cwd
        self.env = env
        self.universal_newlines = universal_newlines
        self.startupinfo = startupinfo
        self.creationflags = creationflags
        self.restore_signals = restore_signals
        self.start_new_session = start_new_session
        self.pass_fds = pass_fds
        self.encoding = encoding
        self.errors = errors
        self.text = text

    def start(self) -> subprocess.Popen:
        return subprocess.Popen(args=self.args, bufsize=self.bufsize, executable=self.executable, stdin=self.stdin,
                                stdout=self.stdout, stderr=self.stderr, preexec_fn=self.preexec_fn,
                                close_fds=self.close_fds, shell=self.shell, cwd=self.cwd, env=self.env,
                                universal_newlines=self.universal_newlines, startupinfo=self.startupinfo,
                                creationflags=self.creationflags, restore_signals=self.restore_signals,
                                start_new_session=self.start_new_session, pass_fds=self.pass_fds,
                                encoding=self.encoding, errors=self.errors, text=self.text)
