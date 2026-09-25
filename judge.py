"""
judge.py — runs a student's submitted Python code against stdin/stdout
test cases and reports pass/fail.

SECURITY NOTE — read before deploying anywhere but your own machine:
This runs submitted code via a plain subprocess with a wall-clock timeout.
That is NOT a real sandbox: submitted code still has full filesystem and
network access as the user running the Flask process. It is fine for a
single student practicing locally, but it must NOT be exposed on a
shared server or the public internet without real isolation — a
container per run (Docker), a restricted user account, seccomp/gVisor,
or a hosted judge API (e.g. Judge0). Do not skip that step before
putting this anywhere multi-user.
"""

import subprocess
import tempfile
import os
import sys

TIME_LIMIT_SECONDS = 5


def _run_subprocess(code: str, stdin_data: str):
    """Writes `code` to a temp .py file and runs it with `stdin_data` on stdin."""
    fd, path = tempfile.mkstemp(suffix=".py")
    try:
        with os.fdopen(fd, "w") as f:
            f.write(code)

        try:
            proc = subprocess.run(
                [sys.executable, path],
                input=stdin_data,
                capture_output=True,
                text=True,
                timeout=TIME_LIMIT_SECONDS,
            )
            return {
                "stdout": proc.stdout,
                "stderr": proc.stderr,
                "timed_out": False,
                "returncode": proc.returncode,
            }
        except subprocess.TimeoutExpired:
            return {
                "stdout": "",
                "stderr": f"Time limit exceeded ({TIME_LIMIT_SECONDS}s).",
                "timed_out": True,
                "returncode": None,
            }
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass


def run_code(code: str, stdin_data: str = ""):
    """Runs code once with the given stdin, no pass/fail comparison. Used by 'Run'."""
    return _run_subprocess(code, stdin_data)


def _normalize(text: str) -> str:
    # Compare output ignoring trailing whitespace per line and trailing blank lines.
    lines = [line.rstrip() for line in text.strip().splitlines()]
    return "\n".join(lines)


def judge_submission(code: str, test_cases):
    """
    Runs `code` against a list of test cases:
        [{"input": "...", "expected_output": "...", "is_sample": bool}, ...]

    Returns:
        {
          "status": "Accepted" | "Wrong Answer" | "Runtime Error" | "Time Limit Exceeded",
          "passed": int, "total": int,
          "results": [ {input, expected, actual, passed, stderr}, ... ]
        }
    """
    results = []
    passed = 0
    overall_status = "Accepted"

    for tc in test_cases:
        result = _run_subprocess(code, tc["input"])

        if result["timed_out"]:
            case_status = "Time Limit Exceeded"
        elif result["returncode"] not in (0, None) or result["stderr"].strip():
            case_status = "Runtime Error"
        elif _normalize(result["stdout"]) == _normalize(tc["expected_output"]):
            case_status = "Passed"
        else:
            case_status = "Wrong Answer"

        if case_status == "Passed":
            passed += 1
        elif overall_status == "Accepted":
            # first failure sets the overall status, but keep running remaining
            # cases so the student can see how many pass overall
            overall_status = case_status

        results.append({
            "input": tc["input"],
            "expected": tc["expected_output"],
            "actual": result["stdout"],
            "stderr": result["stderr"],
            "passed": case_status == "Passed",
            "is_sample": tc.get("is_sample", False),
        })

    if passed == len(test_cases) and test_cases:
        overall_status = "Accepted"

    return {
        "status": overall_status,
        "passed": passed,
        "total": len(test_cases),
        "results": results,
    }
