#!/bin/python

import time
import os
import csv
import sys
import argparse
import pprint

from goldfish import lookup, mana_full

fields = ['Name'] + mana_full + ['Type', 'Power', 'Toughness', 'Description']


def load_existing(f='detailed.csv'):
    cards = {}
    with open(f, 'r') as fin:
        for j, line in enumerate(csv.reader(fin, quotechar='"', skipinitialspace=True)):
            if j == 0:
                continue
            if len(line) == len(fields):
                c = {}
                m = {}
                for i, field in enumerate(fields):
                    c[field] = line[i]
                cards[c['Name']] = c
    return cards


def load_unprocessed(f, cards={}):
    errors = []

    with open(f, 'r') as fin:
        lines = [line for line in csv.reader(
            fin, quotechar='"', skipinitialspace=True)]
    args = lines[0]

    # Load cards first to remove duplicates
    for line in lines[1:]:
        name = line[args.index('Card')]
        setn = line[args.index('Set Name')]
        var = None
        foil = (line[args.index('Foil')] == 'foil')
        if len(line) > args.index('Variation'):
            var = line[args.index('Variation')]
        if not (name in cards):
            try:
                time.sleep(0.5)  # try not to totally spam and get blocked
                c = lookup(name, setn, var, foil)
                cards[name] = c
                print("Got data for '%s'" % name)
            except KeyboardInterrupt as ki:
                raise "Aborted by CTRL+C"
            except BaseException as se:
                print("Error on card %s:\n%s\n\n" % (name, str(se)))
                errors.append(line)

    return cards, errors, args


def write_errors(f, errors, args):
    # Write missing
    with open(f, 'w') as ferr:
        we = csv.writer(ferr, quotechar='"', lineterminator='\n')
        we.writerow(args)
        for line in errors:
            we.writerow(line)
    pass


def write_csv(fname, cards):
    try:
        with open(fname + '_tmp', 'w') as fout:
            w = csv.writer(fout, quotechar='"', lineterminator='\n')

            # Write the header
            w.writerow(fields)

            # Write out
            for c in sorted(cards):
                card = cards[c]
                line = []
                for f in fields:
                    line.append(str(card[f]))
                w.writerow(line)

        os.rename('%s_tmp' % fname, fname)
    except BaseException as be:
        print("Failed to write csv:")
        print(str(be))


class ArgError(BaseException):
    def __init__(self, str=""):
        super().__init__(str)


def call_lookup(args):
    pp = pprint.PrettyPrinter(indent=4, sort_dicts=False)
    name = ' '.join(args.name)
    setn = ' '.join(args.setname)
    try:
        c = lookup(name, setn, args.var, args.foil)
        pp.pprint(c)
    except:
        print("Unable to find card '%s' in set '%s'" % (name, setn))


def call_scrape(args):
    cards = {}

    if (not args.gen_csv) and (not args.gen_html):
        raise ArgError("Nothing to do")

    # Get already existing cards
    if args.load_existing:
        cards = load_existing(args.output)

    # Scrape unprocessed cards
    if args.scrape:
        cards, errors, a = load_unprocessed(args.input, cards)

        # Write out errors
        if args.dump_errors:
            write_errors(args.errors, errors, a)

    if not cards:
        raise ArgError("No cards to write out")

    # Write out csv
    if args.gen_csv:
        write_csv(args.output, cards)

    print("Done!")


def main(cli_args):
    stuff = False
    parser = argparse.ArgumentParser(description="MTG Scraper Utility")
    subs = parser.add_subparsers()
    lparse = subs.add_parser('lookup', help="Search for specific card")
    lparse.set_defaults(func=call_lookup)
    lparse.add_argument('name', nargs="+", default=[],
                        help="Name of card to search for")
    lparse.add_argument('--setname', nargs="+", dest="setname",
                        default=['Modern', 'Horizons', '2'], help="Name of set card is from")
    lparse.add_argument('--var', dest="var", default=None,
                        help="Card variation")
    lparse.add_argument('-f', action="store_true",
                        dest="foil", help="Card is a foil")

    rparse = subs.add_parser('run', help="Scrape an input csv")
    rparse.set_defaults(func=call_scrape)
    rparse.add_argument('-l', dest='load_existing',
                        action="store_true", help="Load existing output csv before run")
    rparse.add_argument('-i', dest='scrape',
                        action='store_true', help="Load csv from goldfish and process")
    rparse.add_argument('-e', dest='dump_errors',
                        action='store_true', help="Write out errors")
    rparse.add_argument(
        '-c', dest="gen_csv", action="store_true", help="Write to .csv")
    rparse.add_argument('-w', dest="gen_html",
                        action="store_true", help="build webpage (Not yet implemented)")
    rparse.add_argument('--input-csv', dest="input", default="my_collection.csv",
                        help="goldfish file to process, defines file to use for -i")
    rparse.add_argument('--error-csv', dest="errors", default="missing.csv",
                        help="csv for card errors, used by -e, ignored if -i is not set")
    rparse.add_argument('--output-csv', dest="output",
                        default="detailed.csv", help="Output csv, used by -l, -c")

    args = parser.parse_args(cli_args)

    if not 'func' in args:
        parser.print_help()
        return

    try:
        args.func(args)
    except ArgError as ae:
        print(str(ae))
        parser.print_help()
        return
    except BaseException as be:
        print(str(be))


if __name__ == '__main__':
    main(sys.argv[1:])
