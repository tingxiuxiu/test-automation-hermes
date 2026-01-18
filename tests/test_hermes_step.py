import time

import hermes


@hermes.step("Step 1: Init")
def step_1():
    time.sleep(0.1)


def test_hermes_steps():
    step_1()

    with hermes.step("Step 2: Action"):
        time.sleep(0.1)
        with hermes.step("Step 2.1: Nested Action"):
            time.sleep(0.1)

    try:
        with hermes.step("Step 3: Fail"):
            raise ValueError("Something went wrong")
    except ValueError:
        pass
