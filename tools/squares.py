#!/usr/bin/python

import argparse
import csv
import copy
import logging
import sys
import pcbnew
from sch import Schematic
from schlib import SchLib
from dcm import Dcm, Component

logger = logging.getLogger('test')

class Vertex:
    def __init__(self, v):
        self.x = v[0]
        self.y = v[1]

    def __repr__(self):
        return "V(%s, %s)" % (self.x, self.y)


class Square:
    def __init__(self, corners):
        self.corners = corners
        self.components = []
        self.refs = []

    def add(self, comp):
        self.components.append(comp)
        self.refs.append(comp.labels['ref'])

    def extents(self):
        x1 = y1 = sys.maxint
        x2 = y2 = 0

        for c in self.corners:
            if c[0] > x2: x2 = c[0]
            if c[1] > y2: y2 = c[1]
            if c[0] < x1: x1 = c[0]
            if c[1] < y1: y1 = c[1]

        return (Vertex((x1, y1)), Vertex((x2, y2)))

    def contains(self, p):
        tl, br = self.extents()
        return p[0] > tl.x and p[0] < br.x and p[1] > tl.y and p[1] < br.y

    def __repr__(self):
        tl, br = self.extents()
        return "Square(%s, %s)" % (tl, br)

class SquareFinder:
    def __init__(self):
        self.connected = {}

    def add(self, ends):
        end0 = ( ends[0], ends[1] )
        end1 = ( ends[2], ends[3] )
        if not self.connected.has_key(end0):
            self.connected[end0] = set()
        if not self.connected.has_key(end1):
            self.connected[end1] = set()
        self.connected[end0].update([ end1 ])
        self.connected[end0].update(self.connected[end1])
        self.connected[end1].update([ end0 ])
        self.connected[end1].update(self.connected[end0])

    def squares(self):
        found = False
        squares = set()
        for key in self.connected:
            if len(self.connected[key]) == 4:
                corners = tuple(sorted(self.connected[key], key=lambda tup: tup))
                squares.update([corners])

        return map(Square, squares)

class SchematicGroups:
    def find(self, filename):
        sch = Schematic(filename)
        squaresFinder = SquareFinder()
        for wire in sch.wires:
            desc = wire['desc'].strip().split(" ")
            if desc[1] == 'Notes':
                data = filter(None, wire['data'].strip().split(" "))
                ends = map(int, data)
                squaresFinder.add(ends)

        squares = squaresFinder.squares()

        for comp in sch.components:
            pos = tuple(map(int, [comp.position['posx'], comp.position['posy']]))
            under = []
            for square in squares:
                if square.contains(pos):
                    square.add(comp)
                    under.append(square)
            if len(under) == 0:
                print "No square found:", comp.labels
            elif len(under) > 2:
                print pos
                print "More than one square found", comp.labels
                print under

        return squares

def main():
    add_missing = True

    topX = pcbnew.FromMM(20)
    topY = pcbnew.FromMM(20)
    moduleDeltaX = pcbnew.FromMM(100)
    refDeltaX = pcbnew.FromMM(10)

    parser = argparse.ArgumentParser(description='Synchronize BOM parts and fields across schematics.')
    parser.add_argument('--schematic', action='store', required=True)
    parser.add_argument('--pcb', action='store', required=True)

    args = parser.parse_args()

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)

    logger.log(logging.INFO, "Processing %s..." % (args.schematic))
    sg = SchematicGroups()
    squares = sg.find(args.schematic)

    board = pcbnew.LoadBoard(args.pcb)
    x = topX
    for square in squares:
        print square, square.refs
        maxWidth = 0
        y = topY

        for ref in square.refs:
            if ref[0] == '#':
                continue
            module = board.FindModuleByReference(ref)
            if module is None:
                print "Unable to find %s on the PCB" % ref
            else:
                bounding = module.GetBoundingBox()
                if y > 0:
                    y += bounding.GetHeight() / 2
                vect = pcbnew.wxPoint(x, y)
                module.SetPosition(vect)
                module.Reference().SetVisible(False)
                y += bounding.GetHeight() / 2
                if bounding.GetWidth() > maxWidth:
                    maxWidth = bounding.GetWidth()
        x += maxWidth * 2


    board.Save(args.pcb)

if __name__ == "__main__":
    main()
 
