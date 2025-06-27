import contextlib
import io
import logging
import os
import tempfile

import cpu_sim
import expr_to_asm
import pytest

MAX_LOGS = 150000


@pytest.mark.golden_test("tests/*.yml")
def test_translator_asm_and_machine(golden, caplog):
    caplog.set_level(logging.DEBUG)
    with tempfile.TemporaryDirectory() as tmpdirname:
        source = os.path.join(tmpdirname, "source.lisp")
        input_stream = os.path.join(tmpdirname, "input.txt")
        target = os.path.join(tmpdirname, "target.bin")
        comands = os.path.join(tmpdirname, "target.bin.hex")
        output_stream = os.path.join(tmpdirname, "output.txt")
        trace_path = os.path.join(tmpdirname, "trace.log")

        with open(source, "w", encoding="utf-8") as file:
            file.write(golden.get("in_source"))
        with open(input_stream, "w", encoding="utf-8") as file:
            file.write(golden["in_stdin"])

        with contextlib.redirect_stdout(io.StringIO()) as stdout:
            expr_to_asm.main(source, target)
            print("============================================================")
            cpu_sim.main(
                bin_path=target,
                input_path=input_stream,
                output_path=output_stream,
                log_path=trace_path
            )

        with open(target, "rb") as file:
            code = file.read()
        with open(comands, encoding="utf-8") as file:
            code_hex = file.read()
        with open(output_stream, encoding="utf-8") as file:
            output_str = file.read()
        with open(trace_path, encoding="utf-8") as file:
            trace_log = file.read()

        assert code == golden.out["out_code"]
        assert code_hex.strip() == golden.out["out_code_hex"].strip()
        assert stdout.getvalue().strip() == golden.out["out_stdout"].strip()
        assert output_str.strip() == golden.out["out_output_file"].strip()
        assert trace_log[:MAX_LOGS].strip() == golden.out["out_log"][:MAX_LOGS].strip()
