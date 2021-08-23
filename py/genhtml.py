from goldfish import mana_full, mana_x, mana_names, mana_colorless, mana_alt

conv_mana = 'Converted Mana'
mech_fields = ['Type', 'Power', 'Toughness', 'Description']
html_fields = ['Name'] + mana_full + [conv_mana] + mech_fields


def makeRow(elements, header=False):
    d = "th" if header else "td"
    sr = "<tr>"
    for e in elements:
        sr += "<%s>%s</%s>" % (d, e, d)
    sr += "</tr>"
    return sr


def computeConverted(card):
    mset = set(mana_full) - set(mana_x)
    count = 0
    for m in mset:
        v = 0
        try:
            v = int(card[m])
        except:
            pass
        count += v
    return count


def makePills(clr, text, n=1):
    return ''.join(['<span class="badge rounded-pill bg-%s">%s</span>' % (clr, text) for x in range(n)])


def fancyMana(m, v):
    vv = 1
    try:
        vv = int(v)
    except:
        return v

    if m == 'White':
        return makePills('white text-dark', 'W', n=vv)
    elif m == 'Black':
        return makePills('black', 'B', n=vv)
    elif m == 'Green':
        return makePills('success', 'G', n=vv)
    elif m == 'Blue':
        return makePills('primary', 'U', n=vv)
    elif m == 'Red':
        return makePills('danger', 'R', n=vv)
    elif m == 'X':
        return makePills('light text-dark', 'X', n=vv)
    else:
        return v


def genCardRow(card):
    ls = []
    for h in html_fields:
        v = 0
        try:
            v = int(card[h])
        except:
            pass

        if h == conv_mana:
            ls.append(computeConverted(card))
        elif h == mana_colorless:
            if v == 0:
                ls.append('')
            else:
                ls.append(makePills('light text-dark', card[h]))
        elif h == mana_alt:
            if v == 0:
                ls.append('')
            else:
                ls.append(card[h])
        elif h in mana_names:
            ls.append(fancyMana(h, card[h]))
        elif 'N/A' in card[h]:
            ls.append('')
        else:
            ls.append(card[h])

    return makeRow(ls)


def genCardTable(cards):
    body = ""
    for c in cards:
        body += genCardRow(cards[c])
    tbl = "<thead>%s</thead><tbody>%s</tbody>" % (
        makeRow(html_fields, header=True), body)
    return tbl


def getTypeList(cards):
    full_list = set()
    exclude = set(['--', '-', '', '//', '—'])
    for c in cards:
        sp = cards[c]['Type'].split(' ')
        full_list |= set(sp)
    return list(full_list - exclude)


def makeCheckBoxes(tlist):
    return ['<input class="form-check-input" type="checkbox" id="type-%s"> %s' % (t, t) for t in tlist]


def genTypeTable(cards):
    types = getTypeList(cards)
    types.sort()
    n = 0
    tbl = ""
    while n < len(types):
        m = min(12, len(types)-n)
        tbl += makeRow(makeCheckBoxes(types[n:n+m]))
        n += m
    return tbl


def getTableBreakpoints(lines, ids):
    blist = []
    ll = ""
    for n, line in enumerate(lines):
        if '</table>' in line:
            for i in ids:
                s = 'table id="%s"' % i
                if s in ll:
                    blist.append((n, i))
        ll = line
    return blist


def genHTML(cards, output='cards.html', template='../web/template.html'):
    lines = []
    with open(template, 'r') as fhtml:
        lines = [line for line in fhtml]

    card_tbl = genCardTable(cards)
    type_tbl = genTypeTable(cards)

    bps = getTableBreakpoints(lines, ['all-cards', 'types'])
    i = 0
    with open(output, 'w') as fout:
        for n, t in bps:
            fout.write(''.join(lines[i:n]))
            i = n
            if t == 'all-cards':
                fout.write(card_tbl)
            elif t == 'types':
                fout.write(type_tbl)
        fout.write(''.join(lines[n:]))
