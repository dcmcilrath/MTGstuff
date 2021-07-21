#!/bin/python

import time
import os
import csv
import sys
import argparse
import pprint

from goldfish import lookup, mana_full

def run(input_csv, output_csv='detailed.csv', missing_csv='missing.csv'):
    """
    Run through input csv, write to output csv
    """

    cards = {}
    errors = []

    fields = ['Name'] + mana_full + \
        ['Type', 'Power', 'Toughness', 'Description']

    # Get already existing cards:
    try:
        with open(output_csv, 'r') as fin:
            for j, line in enumerate(csv.reader(fin, quotechar='"', skipinitialspace=True)):
                if j == 0:
                    continue
                if len(line) == len(fields):
                    c = {}
                    m = {}
                    for i, field in enumerate(fields):
                        c[field] = line[i]
                    cards[c['Name']] = c
    except:
        cards = {}

    # Re-open, and now prepare to write back out
    with open(output_csv + '_tmp', 'w') as fout:
        w = csv.writer(fout, quotechar='"', lineterminator='\n')
        # Write the header
        w.writerow(fields)
        lines = []

        # Read in input
        with open(input_csv, 'r') as fin:
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

        # Write missing
        with open(missing_csv, 'w') as ferr:
            we = csv.writer(ferr, quotechar='"', lineterminator='\n')
            we.writerow(args)
            for line in errors:
                we.writerow(line)

        # Write out
        for c in sorted(cards):
            card = cards[c]
            line = []
            for f in fields:
                line.append(str(card[f]))
            w.writerow(line)

    os.rename('%s_tmp' % output_csv, output_csv)
    print("all done!\n")


def main():
    pp = pprint.PrettyPrinter(indent=4, sort_dicts=False)
    stuff = False
    parser = argparse.ArgumentParser(description="MTG Scraper")
    parser.add_argument('--run', dest='input', help="Run the scraper against a goldfish csv")
    parser.add_argument('--lookup', dest='name', nargs="*", help="Search for specific card")
    parser.add_argument('--set-name', dest='setname', nargs="*", help="Set name to use for lookup", default="Modern Horizons 2".split(' '))
    parser.add_argument('--variation', dest='var', default=None, help="Variation field")
    parser.add_argument('--foil', action="store_const", dest='foil', const=True, default=False, help="is a foil?")
    args = parser.parse_args(sys.argv[1:])

    if args.input:
        stuff=True
        run(args.input)

    if args.name:
        stuff = True
        c = lookup(' '.join(args.name), ' '.join(args.setname), args.var, args.foil)
        pp.pprint(c)

    if not stuff:
        parser.print_help()

if __name__ == '__main__':
    main()