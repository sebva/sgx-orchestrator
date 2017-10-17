#!/usr/bin/env python3
import sys
from dateutil import parser
from fileinput import input

for line in input():
    try:
        split = line.split(",")
        start = parser.parse(split[7])
        end = parser.parse(split[8])
        print((end - start).seconds)
    except:
        print("Line ignored", file=sys.stderr)
