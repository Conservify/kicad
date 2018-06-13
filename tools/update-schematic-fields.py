#!/usr/bin/python

import csv
import argparse
import csv
import copy
import logging
import sys
import shutil
import os
import pprint
import string
import openpyxl as pyxl

from kifield import sch
from kifield import kifield

logger = logging.getLogger('bomtool')
key_fields = [ 'footprint', 'value' ]
fields = [ 'spn1', 'supplier1', 'mfn', 'mfp', 'source', 'notes', 'subsystem', 'critical', 'package' ]
preserved_fields = [ 'footprint', 'value', 'datasheet' ]
pretty_field_names = {
    'spn1': 'SPN1',
    'supplier1': 'Supplier1',
    'mfn': 'MFN',
    'mfp': 'MFP',
    'source': 'Source',
    'notes': 'Notes',
    'subsystem': 'Subsystem',
    'critical': 'Critical',
    'package': 'Package',
    'footprint': 'footprint',
    'value': 'value'
}

class FieldsTablePart:
    def __init__(self, data):
        self.data = data
        self.key = " ".join([data[v] for v in key_fields])

class FieldsTable:
    def __init__(self, original):
        self.keyed = {}
        self.original = original
        for row in original:
            pi = FieldsTablePart(row)
            self.keyed[pi.key] = pi

class SchematicPart:
    def __init__(self, ref, data):
        self.ref = ref
        self.data = data
        self.key = " ".join([data[v] for v in key_fields])

    def __str__(self):
        return "SchematicPart<%s>" % (self.key,)

    def value(self, key):
        return self.data.get(pretty_field_names[key], '')

    def remove_fields(self):
        for name in self.data:
            if name not in preserved_fields:
                self.data[name] = ""
        return True

class PartGroup:
    def __init__(self, key, parts):
        self.key = key
        self.parts = parts

    def size(self):
        return len(self.parts)

    def refs(self):
        values = [part.ref for part in self.parts]
        return ", ".join(values)

    def values(self, key):
        values = [part.value(key) for part in self.parts]
        uniq = set(values)
        return ", ".join(uniq)

class SchematicTable:
    def __init__(self, original):
        self.original = original
        self.all = []
        self.keyed = {}
        for ref, data in original.iteritems():
            part = SchematicPart(ref, data)
            self.keyed[part.key] = self.keyed.get(part.key, []) + [ part ]
            self.all.append(part)

    def sorted(self):
        values = self.all
        values.sort(key=lambda p: p.key)
        return values

    def grouped(self):
        rows = []
        for key, parts in self.keyed.iteritems():
            rows.append(PartGroup(key, parts))
        rows.sort(key=lambda pg: pg.key)
        return rows

    def update_fields(self, source):
        pass

def update_part_fields(source_part, schematic_part):
    for name in fields:
        schematic_name = pretty_field_names[name]
        if source_part.data.get(name):
            schematic_part.data[schematic_name] = source_part.data[name]
        else:
            schematic_part.data[schematic_name] = " "
    return True

def update_schematic_fields(working, filename, source):
    table = SchematicTable(kifield.extract_part_fields_from_sch(filename, recurse=True))

    errors = False
    modified = False
    for key, schematic_parts in table.keyed.iteritems():
        for schematic_part in schematic_parts:
            source_part = source.keyed.get(schematic_part.key)
            if source_part is None:
                logger.log(logging.ERROR, "Missing %s: %s" % (filename, schematic_part))
                errors = True
                continue
            modified = update_part_fields(source_part, schematic_part) or modified

    if errors:
        return False

    if modified:
        kifield.insert_part_fields_into_sch(table.original, filename, True, False)

    return True

def remove_schematic_fields(working, filename):
    table = SchematicTable(kifield.extract_part_fields_from_sch(filename, recurse=True))

    errors = False
    modified = False
    for key, schematic_parts in table.keyed.iteritems():
        for schematic_part in schematic_parts:
            modified = schematic_part.remove_fields() or modified

    if errors:
        return False

    if modified:
        kifield.insert_part_fields_into_sch(table.original, filename, True, False)

    return True

class BomGenerator:
    def __init__(self, schematic):
        self.schematic = schematic

    def generate(self, path):
        wb = pyxl.Workbook()
        self.individual(wb.active)
        self.grouped(wb.create_sheet("grouped"))
        wb.save(path)

    def individual(self, ws):
        ws.title = "bom"

        headings = [ 'ref', 'footprint', 'value', 'mfn', 'mfp', 'source', 'critical' ]
        for c, name in enumerate(headings):
            ws.cell(row=1, column=c + 1).value = name

        for row, part in enumerate(self.schematic.sorted()):
            ws.cell(row=row + 2, column=1).value = part.ref
            ws.cell(row=row + 2, column=2).value = part.value('footprint')
            ws.cell(row=row + 2, column=3).value = part.value('value')
            ws.cell(row=row + 2, column=4).value = part.value('mfn')
            ws.cell(row=row + 2, column=5).value = part.value('mfp')
            ws.cell(row=row + 2, column=6).value = part.value('source')
            ws.cell(row=row + 2, column=7).value = part.value('critical')

    def grouped(self, ws):
        ws.title = "grouped"

        headings = [ 'refs', 'footprint', 'value', 'mfn', 'mfp', 'source', 'critical', 'quantity' ]
        for c, name in enumerate(headings):
            ws.cell(row=1, column=c + 1).value = name

        for row, group in enumerate(self.schematic.grouped()):
            ws.cell(row=row + 2, column=1).value = group.refs()
            ws.cell(row=row + 2, column=2).value = group.values('footprint')
            ws.cell(row=row + 2, column=3).value = group.values('value')
            ws.cell(row=row + 2, column=4).value = group.values('mfn')
            ws.cell(row=row + 2, column=5).value = group.values('mfp')
            ws.cell(row=row + 2, column=6).value = group.values('source')
            ws.cell(row=row + 2, column=7).value = group.values('critical')
            ws.cell(row=row + 2, column=8).value = group.size()

def create_schematic_bom(working, filename):
    name = os.path.basename(filename)
    schematic = SchematicTable(kifield.extract_part_fields_from_sch(filename, recurse=True))

    generator = BomGenerator(schematic)
    generator.generate(os.path.join(working, name + ".xlsx"))

    return True

def read_csv(filename):
    rows = []
    with open(filename) as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            rows.append(row)
    return rows

def read_xlsx(filename):
    wb = pyxl.load_workbook(filename)
    ws = wb.active
    for number, row in enumerate(ws.rows):
        width = len(row) - [c.value for c in row].count(None)
        header = [cell for cell in row]

    return []

def configure_logging():
    logging.basicConfig(format='%(asctime)-15s %(levelname)s %(message)s')
    if False: logging.getLogger('kifield').setLevel(logging.DEBUG - 0) 
    logger.setLevel(logging.DEBUG)

def main():
    configure_logging()

    parser = argparse.ArgumentParser(description='')
    parser.add_argument('--remove', help='', action="store_true")
    parser.add_argument('--update', help='', action="store_true")
    parser.add_argument('--bom', help='', action="store_true")
    parser.add_argument('files', nargs='*')

    args = parser.parse_args()
    working = os.getcwd()

    errors = False

    source_fields = FieldsTable(read_csv("test.csv"))

    if args.remove:
        for child_filename in args.files:
            os.chdir(os.path.dirname(child_filename))

            logger.log(logging.INFO, "Removing fields %s" % (child_filename))
            errors = not remove_schematic_fields(working, child_filename) or errors

        if errors:
            return

    if args.update:
        for child_filename in args.files:
            os.chdir(os.path.dirname(child_filename))

            logger.log(logging.INFO, "Updating fields %s" % (child_filename))
            errors = not update_schematic_fields(working, child_filename, source_fields) or errors

        if errors:
            return

    if args.bom:
        for child_filename in args.files:
            os.chdir(os.path.dirname(child_filename))

            logger.log(logging.INFO, "Export BOM %s" % (child_filename))
            errors = not create_schematic_bom(working, child_filename) or errors

        if errors:
            return

if __name__ == "__main__":
    main()
