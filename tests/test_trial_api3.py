"""trial-api3: the system under test and its answer key must agree.

Starts evals/trial-api3/server.js on a free port, runs evals/keys/grade_api3.py
against it and stops the server again. Skipped when `node` is not on PATH.

Run: python -m unittest tests.test_trial_api3 -v
"""
import os
from pathlib import Path
import re
import shutil
import socket
import subprocess
import sys
import time
import unittest
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
SERVER = ROOT / 'evals/trial-api3/server.js'
VERIFIER = ROOT / 'evals/keys/grade_api3.py'
LAST_LINE = re.compile(r'^(\d+)/(\d+) checks behaved as designed\.$')


def free_port():
    with socket.socket() as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]


class RunningServer:
    """Fresh server process on a free port; state lives in memory, so every instance starts from the seed."""

    def __init__(self, planted=True):
        self.port = free_port()
        self.base = 'http://127.0.0.1:%d' % self.port
        env = dict(os.environ, PORT=str(self.port))
        env.pop('API3_PLANTED', None)
        if not planted:
            env['API3_PLANTED'] = 'off'
        self.proc = subprocess.Popen(['node', str(SERVER)], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def __enter__(self):
        deadline = time.time() + 15
        while time.time() < deadline:
            if self.proc.poll() is not None:
                break
            try:
                with urllib.request.urlopen(self.base + '/health', timeout=1) as resp:
                    if resp.status == 200:
                        return self
            except OSError:
                time.sleep(0.1)
        self.__exit__(None, None, None)
        raise RuntimeError('trial-api3 server did not start on port %d' % self.port)

    def __exit__(self, *exc):
        if self.proc.poll() is None:
            self.proc.kill()
        self.proc.wait(timeout=10)
        return False


def run_verifier(base, *flags):
    env = dict(os.environ, PYTHONIOENCODING='utf-8')
    done = subprocess.run([sys.executable, str(VERIFIER), base, *flags], capture_output=True, env=env, timeout=120)
    return done.returncode, done.stdout.decode('utf-8', 'replace')


@unittest.skipUnless(shutil.which('node'), 'Node.js is required to run the trial-api3 server')
class TrialApi3Tests(unittest.TestCase):
    def assert_all_passed(self, code, out):
        lines = out.strip().splitlines()
        failed = [ln for ln in lines if ln.startswith('[FAIL]')]
        self.assertEqual(failed, [], out)
        match = LAST_LINE.match(lines[-1])
        self.assertIsNotNone(match, lines[-1])
        self.assertEqual(match.group(1), match.group(2), lines[-1])
        self.assertEqual(code, 0, lines[-1])

    def test_key_matches_server_and_restart_gives_the_same_result(self):
        outputs = []
        for _ in range(2):
            with RunningServer() as server:
                code, out = run_verifier(server.base)
            self.assert_all_passed(code, out)
            outputs.append(out)
        self.assertEqual(outputs[0], outputs[1], 'two fresh servers must behave identically')
        for k in range(1, 17):
            self.assertIn('[PASS] K%d ' % k, outputs[0], 'planted defect K%d has no check' % k)

    def test_reference_server_follows_the_contract_in_every_k_scenario(self):
        with RunningServer(planted=False) as server:
            code, out = run_verifier(server.base, '--reference')
        self.assert_all_passed(code, out)

    def test_verifier_refuses_a_server_that_is_not_in_seed_state(self):
        with RunningServer() as server:
            run_verifier(server.base)
            code, out = run_verifier(server.base)
        self.assertEqual(code, 1)
        self.assertIn('[FAIL] P2 ', out)

    def test_parallel_copies_are_independent(self):
        with RunningServer() as one, RunningServer() as two:
            code, out = run_verifier(one.base)
            self.assert_all_passed(code, out)
            code, out = run_verifier(two.base)
            self.assert_all_passed(code, out)


if __name__ == '__main__':
    unittest.main()
