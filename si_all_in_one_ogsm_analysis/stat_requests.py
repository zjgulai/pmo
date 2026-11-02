#!/usr/bin/python3
import json, collections, sys

path = sys.argv[1]
fields = sys.argv[2:]
rows = [json.loads(l) for l in open(path) if l.strip()]
print(f'=== {path}: {len(rows)} records ===')

def vals(field):
    c = collections.Counter()
    for r in rows:
        v = r.get(field)
        if v is None:
            c['<null>'] += 1
        elif isinstance(v, list):
            if not v:
                c['<empty>'] += 1
            for x in v:
                c[str(x)] += 1
        else:
            c[str(v)] += 1
    return c

for f in fields:
    c = vals(f)
    print(f'\n== {f} ({len(c)} distinct) ==')
    for k, n in c.most_common(25):
        print(f'  {n:4d}  {k}')
