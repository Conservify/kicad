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
    'value': 'value',
    'price1': 'price1',
    'price100': 'price100',
    'price1000': 'price1000',
    'price5000': 'price5000'
}

class FieldsTablePart:
    def __init__(self, data):
        self.data = data
        self.key = " ".join([data[v] for v in key_fields])

    def first_value(self, keys):
        for key in keys:
            value = self.data.get(pretty_field_names[key], None)
            if value:
                return value
        return ''

    def value(self, key):
        return self.data.get(pretty_field_names[key], '')

    def with_footprint(self, footprint):
        new_data = self.data.copy()
        new_data['footprint'] = footprint
        return FieldsTablePart(new_data)

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

    def with_footprint(self, fp):
        new_data = self.data.copy()
        new_data['footprint'] = fp
        return SchematicPart(self.ref, new_data)

    def footprint(self):
        return self.data['footprint']

    def change(self, key, value):
        self.data[key] = value

    def first_value(self, keys):
        for key in keys:
            value = self.data.get(pretty_field_names[key], None)
            if value:
                return value
        return ''

    def value(self, key):
        return self.data.get(pretty_field_names[key], '')

    def remove_fields(self):
        for name in self.data:
            if name not in preserved_fields:
                self.data[name] = ""
        return True

    def to_fields_part(self):
        new_data = self.data.copy()
        new_data['source'] = 'ANY'
        return FieldsTablePart(new_data)

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
        uniq = set([x for x in values if len(x) > 0])
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

    def merge(self, table, multiplier):
        self.all += table.all
        for key, parts in table.keyed.iteritems():
            self.keyed[key] = self.keyed.get(key, []) + (parts * multiplier)

    def grouped(self):
        rows = []
        for key, parts in self.keyed.iteritems():
            rows.append(PartGroup(key, parts))
        rows.sort(key=lambda pg: pg.key)
        return rows

def update_part_fields(source_part, schematic_part):
    for name in fields:
        schematic_name = pretty_field_names[name]
        if source_part.data.get(name):
            schematic_part.data[schematic_name] = source_part.data[name]
        else:
            schematic_part.data[schematic_name] = " "
    return True

def update_schematic_fields(working, filename, source, unauthorized):
    table = SchematicTable(kifield.extract_part_fields_from_sch(filename, recurse=True))

    errors = False
    modified = False
    for key, schematic_parts in table.keyed.iteritems():
        for schematic_part in schematic_parts:
            source_part = source.keyed.get(schematic_part.key)
            if source_part is None:
                logger.log(logging.ERROR, "No authority: %s: %s" % (os.path.basename(filename), schematic_part))
                unauthorized.add(schematic_part)
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

class UnauthorizedParts:
    def __init__(self):
        self.parts = []

    def add(self, part):
        self.parts.append(part)

    def alternative_keys(self, part):
        fp = part.footprint()
        fp_parts = fp.split(":")
        possible = part.with_footprint('RocketScreamKicadLibrary:' + fp_parts[1])
        return [ possible.key ]

    def resolve(self, source):
        new_rows = []
        for part in self.parts:
            keys = self.alternative_keys(part)
            missing = True
            for key in keys:
                source_part = source.keyed.get(key)
                if source_part is not None:
                    new_rows.append(source_part.with_footprint(part.footprint()))
                    logger.log(logging.INFO, "Found: %s" % (key))
                    missing = False
            if missing:
                new_rows.append(part.to_fields_part())
        for new_part in new_rows:
            source.keyed[new_part.key] = new_part
        return new_rows

class BomGenerator:
    def __init__(self, schematic, source_fields):
        self.schematic = schematic
        self.source_fields = source_fields

    def generate(self, path):
        wb = pyxl.Workbook()
        self.individual(wb.active)
        self.grouped(wb.create_sheet("grouped"))
        wb.save(path)

    def individual(self, ws):
        ws.title = "bom"

        headings = [ 'ref', 'footprint', 'value', 'mfn', 'mfp', 'source', 'critical', 'price1', 'price100', 'price1000', 'price5000' ]
        for c, name in enumerate(headings):
            ws.cell(row=1, column=c + 1).value = name

        for row, part in enumerate(self.schematic.sorted()):
            source = self.source_fields.keyed[part.key]
            ws.cell(row=row + 2, column=1).value = part.ref
            ws.cell(row=row + 2, column=2).value = part.value('footprint')
            ws.cell(row=row + 2, column=3).value = part.value('value')
            ws.cell(row=row + 2, column=4).value = part.value('mfn')
            ws.cell(row=row + 2, column=5).value = part.value('mfp')
            ws.cell(row=row + 2, column=6).value = part.value('source')
            ws.cell(row=row + 2, column=7).value = part.value('critical')
            ws.cell(row=row + 2, column=8).value = source.first_value([ 'price1' ])
            ws.cell(row=row + 2, column=9).value = source.first_value([ 'price100', 'price1' ])
            ws.cell(row=row + 2, column=10).value = source.first_value([ 'price1000', 'price100', 'price1' ])
            ws.cell(row=row + 2, column=11).value = source.first_value([ 'price5000', 'price1000', 'price100', 'price1' ])

    def grouped(self, ws):
        ws.title = "grouped"

        headings = [ 'refs', 'footprint', 'value', 'mfn', 'mfp', 'source', 'critical', 'quantity', 'price1', 'price100', 'price1000', 'price5000' ]
        for c, name in enumerate(headings):
            ws.cell(row=1, column=c + 1).value = name

        for row, group in enumerate(self.schematic.grouped()):
            source = self.source_fields.keyed[group.key]
            ws.cell(row=row + 2, column=1).value = group.refs()
            ws.cell(row=row + 2, column=2).value = group.values('footprint')
            ws.cell(row=row + 2, column=3).value = group.values('value')
            ws.cell(row=row + 2, column=4).value = group.values('mfn')
            ws.cell(row=row + 2, column=5).value = group.values('mfp')
            ws.cell(row=row + 2, column=6).value = group.values('source')
            ws.cell(row=row + 2, column=7).value = group.values('critical')
            ws.cell(row=row + 2, column=8).value = group.size()
            ws.cell(row=row + 2, column=9).value = source.first_value([ 'price1' ])
            ws.cell(row=row + 2, column=10).value = source.first_value([ 'price100', 'price1' ])
            ws.cell(row=row + 2, column=11).value = source.first_value([ 'price1000', 'price100', 'price1' ])
            ws.cell(row=row + 2, column=12).value = source.first_value([ 'price5000', 'price1000', 'price100', 'price1' ])

def create_schematic_bom(working, filename, source_fields, combined, multiplier):
    name = os.path.basename(filename)
    schematic = SchematicTable(kifield.extract_part_fields_from_sch(filename, recurse=True))
    combined.merge(schematic, multiplier)

    generator = BomGenerator(schematic, source_fields)
    generator.generate(os.path.join(working, name + ".xlsx"))

    return True

def change_value(working, filename, from_value, to_value):
    table = SchematicTable(kifield.extract_part_fields_from_sch(filename, recurse=True))

    errors = False
    modified = False
    for key, schematic_parts in table.keyed.iteritems():
        for schematic_part in schematic_parts:
            if schematic_part.value('value') == from_value:
                logger.log(logging.INFO, "Changing: %s: %s" % (os.path.basename(filename), schematic_part))
                schematic_part.change('value', to_value)
                modified = True

    if errors:
        return False

    if modified:
        kifield.insert_part_fields_into_sch(table.original, filename, True, False)

    return True

def read_csv(filename):
    rows = []
    with open(filename) as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            rows.append(row)
    return rows

class ExcelFile:
    def read(self, filename):
        wb = pyxl.load_workbook(filename)
        ws = wb.active
        rows = []
        header = None
        for number, row in enumerate(ws.rows):
            row = [cell.value for cell in row]
            if header is None:
                header = row
                continue

            keyed = {}
            for i, value in enumerate(row):
                if header[i] is not None:
                    keyed[header[i]] = value

            rows.append(keyed)

        self.rows = rows
        self.header = header

        return rows

def update_xlsx_fields(filename, source):
    wb = pyxl.load_workbook(filename)
    ws = wb.active
    header = None
    seen = []
    for number, row in enumerate(ws.rows):
        row = [cell.value for cell in row]
        if header is None:
            header = row
            continue
        keyed = {}
        for i, value in enumerate(row):
            if header[i] is not None:
                keyed[header[i]] = value

        key = " ".join([keyed[v] for v in key_fields])
        f = source.keyed.get(key)
        if f:
            for name in [ 'mfn', 'mfp' ]:
                column = header.index(name)
                ws.cell(row=number + 1, column = column + 1).value = f.data[name]
            seen.append(key)
        else:
            logger.log(logging.ERROR, "Missing %s", key)

    bottom = ws.max_row

    for part in source.keyed.values():
        if part.key not in seen:
            pprint.pprint([ 'Adding to XLSX: ', bottom, part.key ])
            for index, name in enumerate(header):
                value = ""
                if name in part.data:
                    value = part.data[name]
                ws.cell(row = bottom, column = index + 1).value = value
            bottom += 1

    updated_fn = os.path.join(os.path.dirname(filename), "updated-" + os.path.basename(filename))
    wb.save(updated_fn)

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
    parser.add_argument('--from-value', help='', action="store")
    parser.add_argument('--to-value', help='', action="store")
    parser.add_argument('args', nargs='*')

    args = parser.parse_args()
    working = os.getcwd()

    processed_args = []
    for arg in args.args:
        if os.path.isfile(arg):
            processed_args.append(os.path.abspath(arg))
        else:
            processed_args.append(arg)

    errors = False

    logger.log(logging.INFO, "Opening %s" % ("authority.xlsx"))

    authority = ExcelFile()
    authority_fn = os.path.abspath("authority.xlsx")
    source_fields = FieldsTable(authority.read(authority_fn))
    unauthorized = UnauthorizedParts()

    if args.remove:
        for child_filename in processed_args:
            if os.path.isfile(child_filename):
                os.chdir(os.path.dirname(child_filename))

                logger.log(logging.INFO, "Removing fields %s" % (child_filename))
                errors = not remove_schematic_fields(working, child_filename) or errors

        if errors:
            return

    if args.update:
        for child_filename in processed_args:
            if os.path.isfile(child_filename):
                os.chdir(os.path.dirname(child_filename))

                logger.log(logging.INFO, "Updating fields %s" % (child_filename))
                errors = not update_schematic_fields(working, child_filename, source_fields, unauthorized) or errors

        rows = unauthorized.resolve(source_fields)
        update_xlsx_fields(authority_fn, source_fields)

        if errors:
            return

    if args.from_value and args.to_value:
        logger.log(logging.INFO, "Changing value '%s' to '%s'" % (args.from_value, args.to_value))
        for child_filename in processed_args:
            logger.log(logging.INFO, "Processing %s" % (child_filename))
            os.chdir(os.path.dirname(child_filename))

            errors = not change_value(working, child_filename, args.from_value, args.to_value) or errors

    if args.bom:
        combined = SchematicTable({ })
        multiplier = 1
        for arg in processed_args:
            if os.path.isfile(arg):
                child_filename = arg
                os.chdir(os.path.dirname(child_filename))

                if not args.update:
                    logger.log(logging.INFO, "Updating fields %s" % (child_filename))
                    errors = not update_schematic_fields(working, child_filename, source_fields, unauthorized) or errors

                logger.log(logging.INFO, "Export BOM %s (%d)" % (child_filename, multiplier))
                errors = not create_schematic_bom(working, child_filename, source_fields, combined, multiplier) or errors
                multiplier = 1
            else:
                multiplier = int(arg)

        if errors:
            return

        generator = BomGenerator(combined, source_fields)
        generator.generate(os.path.join(working, "combined.xlsx"))

if __name__ == "__main__":
    main()
