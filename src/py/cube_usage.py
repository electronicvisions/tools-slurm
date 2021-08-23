#!/usr/bin/env python3

"""
Show usage of cube setups over given time period.
"""

import argparse
import os
import subprocess
import datetime as dt


def get_jobs(start: dt.datetime) -> dict:
    """ query slurm database for jobs since start """
    datefmt = "%Y-%m-%dT%H:%M:%S"
    cmd = ("sacct -a -r cube --start {:%Y-%m-%dT%H:%M:%S} "
           "--format=start,end,state,alloctres%100,user --parsable2 "
           "| grep license")

    # pylint: disable=subprocess-run-check
    test = subprocess.run('which sacct', shell=True,
                          capture_output=True, text=True)
    if test.returncode != 0:
        raise RuntimeError("sacct command not found, first load "
                           "slurm-singularity module")

    result = subprocess.run(cmd.format(start), shell=True, check=True,
                            capture_output=True, text=True)

    licenses = {}
    for line in result.stdout.splitlines():
        line = line.split("|")
        cube_license = line[3].split(",")[2][8:-2]
        state = line[2]
        if state == "PENDING":
            continue
        user = line[4]
        start = dt.datetime.strptime(line[0], datefmt)
        try:
            end = dt.datetime.strptime(line[1], datefmt)
        except ValueError:
            end = dt.datetime.now()

        job = (start, end, user)
        if cube_license not in licenses.keys():
            licenses[cube_license] = [job]
        else:
            licenses[cube_license].append(job)
    return licenses


def generate_bars(data, n_hours, begin, binwidth):
    """ draw bars for how long cube was used in each hour """
    barchars = " ▁▂▃▄▅▆▇█"
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
    bars = [barchars[int(7 * t)] for t in activity]
    return "│" + "".join(bars) + "│"


def generate_output(licenses, n_hours, start, binwidth):
    """ generate str line with stats for each cube in licenses """
    lines = []
    for cube_license, data in licenses.items():
        durations = [stop - start for start, stop, _ in data]
        if len(durations) > 0:
            mean_duration = sum(durations, dt.timedelta(0)) / len(durations)
            # job may have started before n_hours ago
            usage = min(1, sum(durations, dt.timedelta(0))
                        / dt.timedelta(hours=n_hours))
            mean_duration = str(mean_duration).split(".")[0]
        else:
            mean_duration = "-"
            usage = 0
        act = generate_bars(data, n_hours, start, binwidth)
        lines.append(f"{cube_license:>5}  "
                     f"{len(data):4d} "
                     f"{mean_duration:>16}   "
                     f"{usage:>4.0%}  "
                     f"{act}")
    lines.sort(key=lambda x: int(x.split()[0][1:-2]), reverse=True)
    return lines


def generate_figure(licenses, begin, path):
    """ save figure to :path: that shows jobs in :licenses: since :begin: """
    # pylint: disable=import-outside-toplevel
    import matplotlib.pyplot as plt

    cubes = list(licenses.keys())
    cubes.sort(key=lambda x: int(x[1:-2]))
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


def main(n_hours, binwidth, figure):
    start = dt.datetime.now() - dt.timedelta(hours=n_hours)
    licenses = get_jobs(start)
    lines = generate_output(licenses, n_hours, start, binwidth)
    print(f"Overview for last {n_hours} hours")
    print(f"SETUP  JOBS    MEAN DURATION  USAGE  {start:%d. %Hh}"
          f"{' ':{abs(n_hours // binwidth - 12)}}"
          f"{dt.datetime.now():%d. %Hh}")
    print("\n".join(lines))

    if figure:
        generate_figure(licenses, start, figure)


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
