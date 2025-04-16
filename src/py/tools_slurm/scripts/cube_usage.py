#!/usr/bin/env python3

"""
Show usage of cube setups over given time period.
"""

from typing import Dict, List, Tuple
import argparse
import os
import re
import subprocess
import datetime as dt
import math


def get_jobs(start: dt.datetime
             ) -> Dict[str, List[Tuple[dt.datetime, dt.datetime, str]]]:
    """
    Query slurm database for jobs since start time.

    :param start: Start time for which to query.
    :return: Dictionary with extracted jobs. Each key represents a license.
        The values are lists with the extracted jobs. For each job the start
        time, end time and the user are given.
    """
    # pylint: disable=too-many-locals
    datefmt = "%Y-%m-%dT%H:%M:%S"
    cmd = ("sacct -a --start {:%Y-%m-%dT%H:%M:%S} "
           "--format=start,end,state,alloctres%100,user,jobid --parsable2 "
           "| grep license")

    # pylint: disable=subprocess-run-check
    test = subprocess.run('which sacct', shell=True,
                          capture_output=True, text=True)
    if test.returncode != 0:
        raise RuntimeError("sacct command not found, first load "
                           "slurm-singularity module")

    # get ids of currently running jobs (to later filter out runaway jobs)
    # Note: we miss classify jobs which started between the call to squeue
    # and sacct. Since these jobs only ran for a few millisecond, they are
    # negligible.
    res_squeue = subprocess.run("squeue --format=%A -h", shell=True,
                                check=True, capture_output=True, text=True)
    active_jobs = res_squeue.stdout.splitlines()

    result = subprocess.run(cmd.format(start), shell=True, check=True,
                            capture_output=True, text=True)

    license_re = re.compile(r"license\/(w(?:6\d|7[0-5])f[0,3])=1")
    jobs = {}
    for line in result.stdout.splitlines():
        line = line.split("|")
        user = line[4]
        state = line[2]
        if state == "PENDING":
            continue
        start = dt.datetime.strptime(line[0], datefmt)
        try:
            end = dt.datetime.strptime(line[1], datefmt)
        except ValueError:
            # check if job is runaway job
            jobid = line[5]
            if jobid not in active_jobs:
                continue
            # running job -> end time is now
            end = dt.datetime.now()
        maybe_hwlicenses = [license_re.match(x) for x in line[3].split(",")]
        for license_match in maybe_hwlicenses:
            if license_match is None:
                continue
            hwlicense = license_match.group(1)
            job = (start, end, user)
            if hwlicense not in jobs:
                jobs[hwlicense] = [job]
            else:
                jobs[hwlicense].append(job)
    return jobs


def generate_bars(data, n_hours, begin, binwidth):
    """
    Draw bars for how long resource was used in each bin.

    :param data: Jobs run on this resource.
    :param n_hours: Number of hours to look back in time.
    :param binwidth: Width of a time bin in hours.
    :param figure: Generate and save figure.
    """
    barchars = " ▁▂▃▄▅▆▇"
    activity = [dt.timedelta(0)] * (n_hours + 1)
    for start, stop, _ in data:
        while True:
            if start < begin:
                when = 0
            else:
                when = int(
                    (start.replace(microsecond=0, second=0, minute=0)
                     - begin.replace(microsecond=0, second=0, minute=0))
                    / dt.timedelta(hours=1)
                )
            if start.hour == stop.hour and\
                    (stop - start) < dt.timedelta(hours=1):
                activity[when] += stop - start
                break
            endhour = start.replace(microsecond=0, second=0, minute=0)\
                + dt.timedelta(hours=1)
            activity[when] += endhour - start
            start = endhour

    activity = [x / dt.timedelta(hours=1) for x in activity[1:]]
    activity = [sum(activity[i: i + binwidth]) / binwidth
                for i in range(0, len(activity), binwidth)]
    bars = [barchars[math.ceil((len(barchars) - 1) * t)] for t in activity]
    return "│" + "".join(bars) + "│"


def generate_output(jobs,
                    n_hours: int,
                    start: dt.datetime,
                    binwidth: int):
    """
    Generate str line with stats for each resource.

    :param jobs: Dictionary with extracted jobs. Each key represents a
        resource. The values are lists with the extracted jobs. For
        each job the start time, end time and the user are given.
    :param start: Start time from which time to generate the plot.
    :param n_hours: Number of hours to look back in time.
    :param binwidth: Width of a time bin in hours.
    """
    lines = []
    for cube_license, data in jobs.items():
        durations = [stop - start for start, stop, _ in data]
        if len(durations) > 0:
            mean_duration = sum(durations, dt.timedelta(0)) / len(durations)
            # job may have started before n_hours ago
            usage = min(1, sum(durations, dt.timedelta(0))
                        / dt.timedelta(hours=n_hours))
            mean_duration = str(mean_duration).split('.', maxsplit=1)[0]
        else:
            mean_duration = "-"
            usage = 0
        act = generate_bars(data, n_hours, start, binwidth)
        lines.append(f"{cube_license:>7}  "
                     f"{len(data):4d} "
                     f"{mean_duration:>16}   "
                     f"{usage:>4.0%}  "
                     f"{act}")
    lines.sort(key=lambda x: int(''.join(filter(str.isdigit, x.split()[0]))),
               reverse=True)
    return lines


def generate_figure(licenses, begin, path):
    """ save figure to :path: that shows jobs in :licenses: since :begin: """
    # pylint: disable=import-outside-toplevel
    import matplotlib.pyplot as plt

    cubes = list(licenses.keys())
    cubes.sort(key=lambda x: int(''.join(filter(str.isdigit, x.split()[0]))))
    fig, ax = plt.subplots()

    for cube_license, data in licenses.items():
        idx = cubes.index(cube_license)
        for start, stop, user in data:
            color = "#aaaaaa" if user == "vis_jenkins" else "black"
            ax.plot([start, stop], [idx, idx], color=color, linewidth=2)

    # TODO grey out night, hx_healthckeck, v1 chips, testing setups
    # ax.axvspan(from, to, facecolor, alpha)

    ax.set_xlim(begin, dt.datetime.now())
    ax.set_yticks(range(len(cubes)))
    ax.set_yticklabels(cubes)
    ax.grid(axis="y", linewidth=0.5, color="#dddddd")
    fig.autofmt_xdate()
    fig.tight_layout()
    plt.savefig(path)


def main(n_hours: int, binwidth: int, figure: bool = False):
    """
    Generate activity plot.

    Plot actvity for each setup over time in a bar plot.
    Result is printed to the console.

    :param n_hours: Number of hours to look back in time.
    :param binwidth: Width of a time bin in hours.
    :param figure: Generate and save figure.
    """
    start = dt.datetime.now() - dt.timedelta(hours=n_hours)
    jobs = get_jobs(start)
    lines = generate_output(jobs, n_hours, start, binwidth)
    print(f"Overview for last {n_hours} hours")
    print(f"  SETUP  JOBS    MEAN DURATION  USAGE  {start:%d. %Hh}"
          f"{' ':{abs(n_hours // binwidth - 12)}}"
          f"{dt.datetime.now():%d. %Hh}")
    print("\n".join(lines))

    if figure:
        generate_figure(jobs, start, figure)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=__doc__)
    parser.add_argument("-n", "--n_hours", type=int, default=24,
                        help="Number of hours to look back.")
    parser.add_argument("-b", "--binwidth", type=int, default=1,
                        help="Width of bars in hours.")
    parser.add_argument("-f", "--figure", default=False, nargs='?', type=str,
                        const="cube_usage.pdf", action='store',
                        help=("Save an overview figure in current directory. "
                              "Optional filename including file type "
                              "[default: cube_usage.pdf]. "
                              "Needs matplotlib, run: "
                              "`module load slurm-singularity/current` "
                              "and then execute script in container."))
    args = parser.parse_args()

    if args.figure:
        args.figure = os.path.join(os.getcwd(), args.figure)

    main(args.n_hours, args.binwidth, args.figure)
