"""Controlled subprocess execution for student code.

Every run happens in its own temporary directory, with a stripped environment,
a wall-clock timeout, capped output, and (where the OS supports it) CPU, memory,
file-size and process limits. Network access is disabled when the OS allows it
(Linux user namespaces). Capabilities that are unavailable are reported by
`sandbox_capabilities()` instead of being silently assumed.

This is suitable for a local college demonstration. For public deployment, run
the whole backend inside a container or VM with its own isolation as well.
"""
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
from contextlib import contextmanager
from pathlib import Path

try:
    import resource  # POSIX only
except ImportError:  # Windows
    resource = None

IS_WINDOWS = os.name == "nt"
MAX_OUTPUT_BYTES = 64 * 1024
MAX_CONCURRENT_RUNS = int(os.environ.get("PEES_MAX_CONCURRENT_RUNS", "4"))
_run_slots = threading.BoundedSemaphore(MAX_CONCURRENT_RUNS)
_network_prefix = None


class RunResult:
    def __init__(self, returncode, stdout, stderr, timed_out, truncated, duration):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
        self.timed_out = timed_out
        self.truncated = truncated
        self.duration = duration


@contextmanager
def workspace():
    """A fresh temporary directory that is always cleaned up."""
    directory = tempfile.mkdtemp(prefix="pees_")
    try:
        yield Path(directory)
    finally:
        shutil.rmtree(directory, ignore_errors=True)


def network_isolation_prefix():
    """Command prefix that removes network access, or [] if unsupported."""
    global _network_prefix
    if _network_prefix is None:
        _network_prefix = []
        if sys.platform.startswith("linux") and shutil.which("unshare"):
            for flags in (["-n"], ["-rn"]):
                try:
                    probe = subprocess.run(
                        ["unshare", *flags, "true"],
                        capture_output=True, timeout=5
                    )
                    if probe.returncode == 0:
                        _network_prefix = ["unshare", *flags]
                        break
                except Exception:
                    pass
    return _network_prefix


def sandbox_capabilities():
    return {
        "platform": sys.platform,
        "time_limit": True,
        "output_limit": True,
        "temporary_directory": True,
        "resource_limits": resource is not None,
        "network_disabled": bool(network_isolation_prefix()),
        "concurrent_run_limit": MAX_CONCURRENT_RUNS,
    }


def safe_env(extra=None):
    env = {"LC_ALL": "C", "LANG": "C", "PYTHONDONTWRITEBYTECODE": "1",
           "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"}
    for key in ("PATH", "SYSTEMROOT", "SystemRoot", "WINDIR", "TEMP", "TMP",
                "COMSPEC", "PATHEXT"):
        if key in os.environ:
            env[key] = os.environ[key]
    if extra:
        env.update(extra)
    return env


def _limit_setter(timeout, memory_mb, restrict_processes, max_file_mb):
    def apply():
        if resource is None:
            return

        def put(kind, value):
            try:
                resource.setrlimit(kind, (value, value))
            except (ValueError, OSError):
                pass

        put(resource.RLIMIT_CPU, int(timeout) + 2)
        put(resource.RLIMIT_CORE, 0)
        put(resource.RLIMIT_FSIZE, max_file_mb * 1024 * 1024)
        if memory_mb:
            put(resource.RLIMIT_AS, memory_mb * 1024 * 1024)
        if restrict_processes and hasattr(resource, "RLIMIT_NPROC"):
            put(resource.RLIMIT_NPROC, 64)
    return apply


def _kill_tree(process):
    try:
        if IS_WINDOWS:
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(process.pid)],
                capture_output=True, timeout=5
            )
        else:
            os.killpg(process.pid, signal.SIGKILL)
    except Exception:
        try:
            process.kill()
        except Exception:
            pass


def run_limited(
    cmd, cwd, timeout=5.0, stdin_text="", memory_mb=None,
    restrict_processes=True, isolate_network=True, max_file_mb=16, env_extra=None
):
    """Run `cmd` with limits and return a RunResult. Never raises on timeout."""
    full_cmd = list(cmd)
    if isolate_network:
        full_cmd = network_isolation_prefix() + full_cmd

    kwargs = {}
    if IS_WINDOWS:
        kwargs["creationflags"] = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
    else:
        kwargs["start_new_session"] = True
        kwargs["preexec_fn"] = _limit_setter(
            timeout, memory_mb, restrict_processes, max_file_mb
        )

    with _run_slots:
        started = time.monotonic()
        with tempfile.TemporaryFile() as out_file, tempfile.TemporaryFile() as err_file:
            process = subprocess.Popen(
                full_cmd, cwd=str(cwd), stdin=subprocess.PIPE,
                stdout=out_file, stderr=err_file, env=safe_env(env_extra), **kwargs
            )
            timed_out = False
            try:
                process.communicate(
                    input=(stdin_text or "").encode("utf-8", "replace"),
                    timeout=timeout
                )
            except subprocess.TimeoutExpired:
                timed_out = True
                _kill_tree(process)
                try:
                    process.communicate(timeout=5)
                except Exception:
                    pass
            duration = time.monotonic() - started

            def read(handle):
                handle.seek(0)
                data = handle.read(MAX_OUTPUT_BYTES + 1)
                return data[:MAX_OUTPUT_BYTES].decode("utf-8", "replace"), len(data) > MAX_OUTPUT_BYTES

            stdout, out_cut = read(out_file)
            stderr, err_cut = read(err_file)

    return RunResult(process.returncode, stdout, stderr, timed_out,
                     out_cut or err_cut, duration)


def find_tool(names, extra_dirs=()):
    for name in names:
        found = shutil.which(name)
        if found:
            return found
    for directory in extra_dirs:
        for name in names:
            for suffix in ("", ".exe"):
                candidate = Path(directory) / (name + suffix)
                if candidate.exists():
                    return str(candidate)
    return None
