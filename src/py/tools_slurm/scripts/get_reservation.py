#!/usr/bin/env python3

"""
Get the applicable reservation given a hardware license.
"""


import argparse
import sys
from tools_slurm.helpers import get_slurm_entity, get_licenses


def get_parser():
    """
    Returns the argument parser for this script.
    """
    parser = argparse.ArgumentParser(
        description='Returns the applicable reservation given a hardware '
                    'license.')
    req_args = parser.add_argument_group('required arguments')
    req_args.add_argument('--license', type=str, required=True,
                          help='slurm hardware license (e.g. W60F0)')
    parser.add_argument('--user', type=str,
                        help='Optional: checks if given user is included '
                             'in the resulting reservation '
                             '(exit code 1 if check fails).')
    parser.add_argument('--srun-args', action='store_true',
                        help='Optional: Adds a \'--reservation \' flag '
                             'prefix if a reservation is found.')
    return parser


def main(args):
    reservations = get_slurm_entity("reservations", ["State=ACTIVE"])

    prefix = "--reservation " if args.srun_args else ""

    for reservation in reservations:
        licenses = get_licenses([reservation])
        if args.license in licenses:
            print(prefix + reservation['ReservationName'])
            if args.user is not None:
                if args.user not in reservation['Users'].split(','):
                    sys.exit(1)
            break


if __name__ == "__main__":
    main(get_parser().parse_args())
