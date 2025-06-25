import os
import subprocess
import pytest


TESTS = [
    "hello",
    "cat",
    "hello_user_name",
    "tail_recursion",
    "sort",
    "double_precision",
    "prob2",
]


@pytest.mark.parametrize("test_name", TESTS)
def test_golden(test_name, golden):
    base = os.path.join("lisp", test_name)
    lisp_file = os.path.join(base, f"{test_name}.lisp")
    binary_file = os.path.join(base, f"{test_name}.bin")
    input_file = os.path.join(base, "input.txt")
    output_file = os.path.join(base, "out.txt")

    subprocess.run(
        ["python", "expr_to_asm.py", lisp_file, binary_file],
        check=True,
    )

    args = ["python", "cpu_sim.py", binary_file]
    if os.path.exists(input_file):
        args.append(input_file)
    args.append(output_file)

    subprocess.run(args, check=True)

    with open(output_file, encoding="utf-8") as f:
        result = f.read()

    TESTS.assert_match(result)

