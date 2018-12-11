#!/usr/bin/python

import argparse
import logging
import pprint
import string
import os
import kinparse
import json

logger = logging.getLogger('pintool')

class PinMap:
    def __init__(self):
        self._pins = {}
        self._boards = {}

    def add(self, board, ref, pin, name, nets):
        self._pins[pin] = self._pins.get(pin, []) + [name]

        b = self._boards[board] = self._boards.get(board, {})

        pins = b['pins'] = b.get('pins', {})
        pins[pin] = nets

    def boards(self):
        return [os.path.basename(x).upper() for x in self._boards.keys()]

    def pins(self):
        keys = self._pins.keys()
        return sorted(keys, key=lambda r: int(r))

    def pin_name(self, key):
        return self._pins[key]

    def pin_description(self, key):
        return key + " (" + ", ".join(set(self._pins[key])) + ")"

    def pin_row(self, key):
        pns = [b['pins'][key] for board_name, b in self._boards.iteritems()]
        good = len(set(pns)) == 1
        return [self.pin_description(key)] + pns + ["Good" if good else ""]

def configure_logging():
    logging.basicConfig(format='%(asctime)-15s %(levelname)s %(message)s')
    logger.setLevel(logging.DEBUG)

def main():
    configure_logging()

    footprint = "conservify:TQFP-48_7x7mm_Pitch0.5mm"

    parser = argparse.ArgumentParser(description='')
    parser.add_argument('args', nargs='*')

    args = parser.parse_args()
    working = os.getcwd()

    processed_args = []
    for arg in args.args:
        if os.path.isfile(arg):
            processed_args.append(os.path.abspath(arg))

    combined = {}
    combined[footprint] = PinMap()

    pp = pprint.PrettyPrinter(indent=4, width=1)
    for child_filename in processed_args:
        logger.info("Processing: " + child_filename)
        nl = kinparse.parse_netlist(child_filename)

        netmap = {}
        parts = {}
        for n in nl.nets:
            name = n.name[0]
            connected = len(n.nodes) > 1
            for node in n.nodes:
                ref = node.ref[0]
                pin = node.pin[0]
                refmap = netmap[ref] = netmap.get(ref, {})
                if connected:
                    refmap[pin] = refmap.get(pin, []) + [name]
                else:
                    refmap[pin] = refmap.get(pin, []) + [name + "*"]

        for lp in nl.libparts:
            lp_key = lp.lib[0] + ":" + lp.part[0]
            parts[lp_key] = lp

        for c in nl.components:
            ref = c.ref[0]
            fp = c.footprint[0]
            lp_key = c.libsource[0] + ":" + c.libsource[1]
            if fp == footprint:
                logger.info("Match: ref=%s %s" % (ref, fp))

                part = parts[lp_key]
                for pin in part.pins:
                    num = pin.num[0]
                    name = pin.name[0]
                    nets = ", ".join(netmap[ref][num]).replace("/", "")
                    combined[footprint].add(child_filename, ref, num, name, nets)
                    if False: logger.info("- %s %s %s" % (num, name, nets))

    for fp, pm in combined.iteritems():
        print("| " + (" | ".join(["Pin"] + pm.boards() + [ "Status"])) + " |")
        for pin in pm.pins():
            print("| " + (" | ".join(pm.pin_row(pin))) + " |")

if __name__ == "__main__":
    main()
