#!/usr/bin/python

import sys
import csv
from collections import defaultdict

by_part = defaultdict(list)

for row in csv.reader(iter(sys.stdin.readline, '')):
    part = row[3]
    if len(part) > 0:
        by_part[part].append(row)

for key, row in by_part.items():
    references = [x[0] for x in row]
    print(",".join([" ".join(references), str(len(references)), row[0][2], row[0][3], row[0][4], row[0][5], row[0][6], row[0][7]]))
