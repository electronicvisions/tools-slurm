#!/usr/bin/env python3

import contextlib
import io
import unittest
from find_free_chip import main, get_chip_licenses, get_slurm_entity, \
    get_parser, CHIP_REVISION_DEFAULT


CHIP_LICENSE_REGEX = r"W[0-9]+F[0-9]+"
CHIP_SRUN_ARGS_REGEX = r"--wafer=[0-9]+\ --fpga-without-aout=[0-9]+"


class TestFindFreeChip(unittest.TestCase):

    def test_get_chip_licenses(self):
        chips = get_chip_licenses(CHIP_REVISION_DEFAULT)
        self.assertGreater(len(chips), 0)
        self.assertRegex(chips[0], CHIP_LICENSE_REGEX)

    def test_get_slurm_entity(self):
        licenses = get_slurm_entity("licenses")
        self.assertGreater(len(licenses), 0)

        self.assertIn('LicenseName', licenses[0])
        self.assertIn('Used', licenses[0])

        filtered_licenses = get_slurm_entity(
            "licenses",
            conditions=[f"LicenseName={licenses[0]['LicenseName']}"])
        self.assertEqual(len(filtered_licenses), 1)
        self.assertDictEqual(filtered_licenses[0], licenses[0])

    def test_main(self):
        parser = get_parser()

        stdout_string = io.StringIO()
        with contextlib.redirect_stdout(stdout_string):
            main(parser.parse_args(["--random"]))
        lines = stdout_string.getvalue().splitlines()
        self.assertLessEqual(len(lines), 1)
        if lines:
            self.assertRegex(lines[0], CHIP_LICENSE_REGEX)

        stdout_string = io.StringIO()
        with contextlib.redirect_stdout(stdout_string):
            main(parser.parse_args(["--srun-args"]))
        lines = stdout_string.getvalue().splitlines()
        if lines:
            self.assertRegex(lines[0], CHIP_SRUN_ARGS_REGEX)


if __name__ == "__main__":
    unittest.main()
