STATE_COUNTING_NUMBER_OF_CHECKS = 0
STATE_RUNNING_CHECKS            = 1

state         = -1
checks_file   = "./checks.txt"
checks_n      = 0
current_check = 0


def run_checks(func):
    global state

    state = STATE_COUNTING_NUMBER_OF_CHECKS
    func()
    state = STATE_RUNNING_CHECKS
    while current_check < checks_n:
        func()


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

