#!/usr/bin/env python

# Inspired by https://allanderek.github.io/posts/flask-%2B-coverage-analysis/
# - Start the dev server under coverage.py
# - Do any setup required
# - Run tests
# - Generate coverage report

import contextlib
import os
import signal
import subprocess
import sys

env = os.environ.copy()
env["TEST_MODE"] = "yes"


def main():
    with start_server():
        setup()
        run_tests()

    generate_coverage()


@contextlib.contextmanager
def start_server():
    server_command = ["coverage", "run", "-p", "-m", "flask", "run", "--host=0.0.0.0", "--port=5000"]

    print("Starting test server...")
    sys.stdout.flush()

    # TODO: Need to write the server output to a file or something to make it easier to debug playwright test issues
    server = subprocess.Popen(server_command, stderr=subprocess.PIPE, env=env)
    for line in server.stderr:  # type: ignore
        if line.startswith(b" * Running on"):
            break

    yield

    server.send_signal(signal.SIGINT)
    server.wait(timeout=30)


def setup():
    # Run migrations
    print("Running migrations...")
    sys.stdout.flush()

    # Seed test data
    print("Seeding test database...")
    sys.stdout.flush()

    seed_command = ["flask", "data", "seed-test-db"]
    seed = subprocess.Popen(seed_command, env=env)
    seed.wait(timeout=30)


def run_tests():
    print("Running tests...")
    sys.stdout.flush()

    do_e2e = False  # TODO: Change this to True once we add e2e tests
    do_unit = True

    specific_tests = sys.argv[1:]
    if specific_tests:
        if not any("/e2e/" in test for test in specific_tests):
            do_e2e = False

        if not any("/unit/" in test for test in specific_tests):
            do_unit = False

    wait_for = []

    # Run e2e tests
    if do_e2e:
        e2e_test_command = [
            "pytest",
            "tests/e2e",
            "--video",
            "retain-on-failure",
            "--tracing",
            "retain-on-failure",
            "--output",
            "debug/tests",
            *sys.argv[1:],
        ]
        e2e_test_process = subprocess.Popen(e2e_test_command, env=env)
        wait_for.append(e2e_test_process)

    # Run unit tests
    if do_unit:
        unit_test_command = ["coverage", "run", "-p", "-m", "pytest", "tests/unit", *sys.argv[1:]]
        unit_test_process = subprocess.Popen(unit_test_command, env=env)
        wait_for.append(unit_test_process)

    for to_await in wait_for:
        to_await.wait(timeout=120)


def generate_coverage():
    os.system("coverage combine")
    os.system("coverage report -m")


if __name__ == "__main__":
    main()
