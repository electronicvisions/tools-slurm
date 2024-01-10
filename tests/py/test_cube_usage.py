#!/usr/bin/env python3

import unittest
import tempfile
import os
import datetime
from cube_usage import main, generate_output, get_jobs, generate_figure


class TestCubeUsage(unittest.TestCase):

    def test_generate_output(self):
        start = datetime.datetime(2021, 1, 19, 18, 21, 17)
        end = datetime.datetime(2021, 1, 21, 16, 43, 4)
        n_hours = 48
        binwidth = 1
        jobs = {'w33f6': [(start, end, 'hd383')]}
        lines = generate_output(jobs, n_hours, start, binwidth)
        self.assertEqual(len(lines), 1)

    def test_get_jobs(self):
        start = datetime.datetime.now() - datetime.timedelta(hours=1)
        self.assertIsNotNone(get_jobs(start))

    def test_generate_figure(self):
        start = datetime.datetime(2021, 1, 19, 18, 21, 17)
        end = datetime.datetime(2021, 1, 21, 16, 43, 4)
        jobs = {'w33f6': [(start, end, 'hd383')]}
        with tempfile.TemporaryDirectory() as tmpdirname:
            path = os.path.join(tmpdirname, "cube_usage.pdf")
            self.assertIsNone(generate_figure(jobs, start, path))
            self.assertTrue(os.path.isfile(path))

    def test_main(self):
        n_hours = 48
        binwidth = 2
        figure = False
        self.assertIsNone(main(n_hours, binwidth, figure))


if __name__ == "__main__":
    unittest.main()
