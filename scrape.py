#!/bin/python

import time
import os
import csv
import sys
import re
import requests

mana_names = ['X', 'White', 'Black', 'Blue', 'Green', 'Red']
mana_colorless = 'Colorless'
mana_alt = 'Special'

mana_full = [mana_colorless] + mana_names + [mana_alt]

land_names = ['island', 'mountain', 'forest', 'swamp', 'plains']

url_base = 'https://www.mtggoldfish.com/price'

# Just cuz
sublist = {
    'Commander Anthology 2018': 'Commander Anthology Volume II'
}

# url-ify names


def fixname(s):
    s = s.strip()
    s = re.sub(r"['\.,:/\\]", '', s)
    s = re.sub(r'\s+', ' ', s)
    return re.sub(' ', '+', s)


# Generic text cleanup, remove HTML elements and fix escaped characters
def cleanHTML(s):
    s = s.strip().replace('\n', ' ').replace('<br>', ' ')

    s = re.sub(r'<.*?>', '', s)
    s = re.sub(r'\s+', ' ', s)

    specials = re.findall(r'&#(\d+);', s)
    if not specials:
        return s

    reps = [chr(int(n)) for n in set(specials)]
    for i, sp in enumerate(set(specials)):
        s = s.replace('&#%s;' % sp, reps[i])

    return s


# Convert goldfish mana name to actual
def convertMana(m):
    if m == 't':
        return 'Tap'
    if m == mana_colorless.lower():
        return mana_colorless
    try:
        n = int(m)
        return n
    except:
        pass
    for test in mana_names:
        if m == test.lower():
            return test
    return mana_alt


# "2 white white" -> colorless: 2, white: 2 etc
def countMana(l, split=False):
    cost = {x: 0 for x in mana_full}

    try:
        s = l[0]
    except:
        return cost

    # Wow it's like two cards in one! -nobody
    if split:
        for i in s.split('//'):
            sc = countMana([i])
            for j in cost:
                cost[j] += sc[j]
        return cost

    s = re.sub('\s+', ' ', s)
    s = s.strip()

    for m in s.split(' '):
        mana = convertMana(m)
        if type(mana) is int:
            cost[mana_colorless] = mana
        elif mana in mana_names:
            cost[mana] += 1
        else:
            cost[mana_alt] += 1
    return cost


# Parse out the stupid svgs goldfish uses to render mana symbols
def getManaList(s):
    return re.findall(r"<span[^>]*?class='manacost'[^>]*?aria-label='mana cost:([^']*?)'>", s, re.DOTALL)


# Lookup by card name/set name
def lookup(name, setname, var=None, foil=False, dbg=False):

    n = fixname(name)
    sn = fixname(setname)

    if setname in sublist:
        print("Note: set changed from '%s' to '%s' for card '%s'" %
              (setname, sublist[setname], name))
        sn = fixname(sublist[setname])

    if var:
        n += '-%s' % var
    if foil:
        sn += ':Foil'

    # Make GET request
    url = '%s/%s/%s#paper' % (url_base, sn, n)
    if dbg:
        print('Trying url=%s' % url)

    r = requests.get(url=url)
    assert(r.status_code == 200)

    ps = {x: y for x, y in re.findall(
        r"<p class='([^']*?)'>(.*?)</p>", r.text, re.DOTALL)}

    # Name
    topline = re.findall(
        r"<h3 class='gatherer-name'>(.*?)</h3>", r.text, re.DOTALL)[0]
    if dbg:
        print("Topline: %s" % str(topline))
    nohtml = re.sub(r'<.*?>', '', topline)
    name = cleanHTML(nohtml)

    # Handle these stupid things
    if '//' in name:
        name = ' // '.join([dash.strip() for dash in name.split('//')[:2]])
        ml = getManaList(topline)
        if dbg:
            print("ml= %s" % str(ml))
        mana = countMana(ml, split=True)
    else:
        mana = countMana(getManaList(topline))

    if dbg:
        print("Mana cost: %s" % str(mana))

    # Type
    t = cleanHTML(ps['gatherer-type'])
    if dbg:
        print("Type: %s" % t)

    # P/T
    pt = re.findall(r"<div class='gatherer-power'>(.*?)</div>",
                    r.text, re.DOTALL)
    pwr = 'N/A'
    tough = 'N/A'
    if pt:
        ptfix = cleanHTML(pt[0])
        if '/' in ptfix:
            pwr, tough = ptfix.split('/')
        else:
            pwr = ptfix

    # Description
    nows = ps['gatherer-oracle'].replace('\n', ' ')
    nospan = re.sub(r"<span.*?>.*?</span>", "[REPLACE]", nows)
    if dbg:
        print("nospan='%s'" % nospan)
    ml = getManaList(nows)
    if dbg:
        print("ml='%s'" % str(ml))
    desc = nospan
    if ml:
        ins = nospan.split('[REPLACE]')
        s = ""
        for i, sect in enumerate(ins):
            s += sect + ' '
            if i < len(ml):
                s += str(convertMana(ml[i].strip()))
        desc = s
    desc = cleanHTML(desc)
    if dbg:
        print("Description: %s" % desc)

    info = mana
    info['Name'] = name.strip()
    info['Type'] = t.strip()
    info['Description'] = desc.strip()
    info['Power'] = pwr.strip()
    info['Toughness'] = tough.strip()
    return info


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
            if name.lower() in land_names:
                print('Skipping basic land "%s" from "%s"' % (name, setn))
            elif not (name in cards):
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


if __name__ == '__main__':
    if len(sys.argv) > 1:
        run(sys.argv[1])
    else:
        print("Need input file")
