#!/usr/bin/env python3

"""
Show available BSS-2 chips.
"""

import argparse
from enum import Enum
import random
import sys
from tools_slurm.helpers import get_slurm_entity, get_licenses, get_idle_chips


CHIP_REVISION_DEFAULT = 3


class ExitCode(Enum):
    NO_FREE_CHIP = 2


def get_parser():
    """
    Returns the argument parser for this script.
    """
    parser = argparse.ArgumentParser(
        description=f'Shows available BSS-2 chips. Exit code is 0 on success, '
                    f'{ExitCode.NO_FREE_CHIP.value} if no chips are available '
                    f'and 1 in fail case')
    parser.add_argument(
        '--chip-revision', type=int, default=CHIP_REVISION_DEFAULT,
        help=f'specify chip revision (defaults to {CHIP_REVISION_DEFAULT})')
    parser.add_argument('--random', action='store_true',
                        help='get a single random chip')
    parser.add_argument('--srun-args', action='store_true',
                        help='return srun arguments instead of license')
    parser.add_argument('--user', type=str,
                        help='add reservations where the provided user is '
                             'included to the search')
    return parser


def main(args):
    reservations = get_slurm_entity("reservations", ["State=ACTIVE"])
    if args.user is not None:
        reservation_licenses = []
        for reservation in reservations:
            if args.user not in reservation['Users'].split(','):
                reservation_licenses.extend(get_licenses([reservation]))
    else:
        reservation_licenses = get_licenses(reservations)
    # manually block Jenkins test setups. The can be in undefined state, but
    # we don't want to put them in a reservation so people can debug faster.
    reservation_licenses.extend(['W62F0', 'W62F3'])
    chips = filter(lambda license: license not in reservation_licenses,
                   get_idle_chips(args.chip_revision))
    chips = list(chips)
    if len(chips) == 0:
        print("There is no free chip available", file=sys.stderr)
        sys.exit(ExitCode.NO_FREE_CHIP.value)
    if args.random:
        chips = random.choices(chips, k=1)
    for chip_license in chips:
        if args.srun_args:
            print(chip_license.replace(
                "W", "--wafer=").replace(
                    "F", " --fpga-without-aout="))
        else:
            print(chip_license)


if __name__ == "__main__":
    main(get_parser().parse_args())
