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


def genHeader():
    return makeRow(html_fields, header=True)


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
        return makePills('light text-dark', 'W', n=vv)
    elif m == 'Black':
        return makePills('dark', 'B', n=vv)
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
        else:
            ls.append(card[h])
    return makeRow(ls)


def genTable(cards):
    body = ""
    for c in cards:
        body += genCardRow(cards[c])
    tbl = "<thead>%s</thead><tbody>%s</tbody>" % (genHeader(), body)
    return tbl


def genHTML(cards, output='cards.html', template='../web/template.html'):
    i = 0
    lines = []
    with open(template, 'r') as fhtml:
        for n, line in enumerate(fhtml):
            lines.append(line)
            if '</table>' in line:
                i = n
    tbl = genTable(cards)
    with open(output, 'w') as fout:
        fout.write(''.join(lines[:i]))
        fout.write(tbl)
        fout.write(''.join(lines[i:]))
