import math
import random
import time

STATE_COUNTING_NUMBER_OF_CHECKS = 0
STATE_RUNNING_CHECKS            = 1
SUBCHECK_TYPE_REQUEST_URL = "request_url"
STATUS_SUCCEEDED = "succeeded"
STATUS_FAILED    = "failed"
INDENT = "\t"

state              = -1
checks_file_path   = "./checks.txt"
checks_file_handle = None
checks_n           = 0
current_check      = 0


def run_checks(func):
    global state, checks_file_handle

    state = STATE_COUNTING_NUMBER_OF_CHECKS
    func()
    state = STATE_RUNNING_CHECKS
    with open(checks_file_path, "a") as checks_file_handle:
        while current_check < checks_n:
            timestamp = math.floor(time.time())
            if checks_file_handle == None: raise Exception
            checks_file_handle.write(f"check_begin_at_timestamp {timestamp}\n")
            func()
            checks_file_handle.write(f"check_end\n")


def next_check():
    if state == STATE_COUNTING_NUMBER_OF_CHECKS:
        global checks_n
        checks_n += 1
        return False
    if state == STATE_RUNNING_CHECKS:
        global current_check
        print(f"Running check {current_check}.")
        current_check += 1
        return True
    raise Exception


def request_url(url):
    print(f"Making request to '{url}'.")
    print("Not implemented!")
    response_time = random.randrange(1000)/1000
    if checks_file_handle == None: raise Exception
    checks_file_handle.write(f"{INDENT}subcheck_begin {SUBCHECK_TYPE_REQUEST_URL}\n")
    checks_file_handle.write(f"{INDENT}{INDENT}status {STATUS_SUCCEEDED}\n")
    checks_file_handle.write(f"{INDENT}{INDENT}url {url}\n")
    checks_file_handle.write(f"{INDENT}{INDENT}response_time_in_secs {response_time}\n")
    checks_file_handle.write(f"{INDENT}subcheck_end\n")

