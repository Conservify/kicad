#!/usr/bin/python

import argparse
import os
import sys
import logging
import shutil
import schlib
import sch

logger = logging.getLogger('test')
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

paths = [
    "/home/jlewallen/conservify/kicad/conservify.lib",
    "/home/jlewallen/fieldkit/core/hardware/fk-core-cache.lib",
]

found = {}

merged = schlib.SchLib("conservify-new.lib", True)

for path in paths:
    lib = schlib.SchLib(path)
    logger.info(path)
    for c in lib.components:
        clean = c.name.replace("~", "")
        if clean not in found:
            found[clean] = c
            merged.components.append(c)

merged.save()

fps = {}
paths = [
    "/home/jlewallen/fieldkit/core/hardware/fk-core.sch"
]

for path in paths:
    logger.info(path)
    sch = sch.Schematic(path)
    for comp in sch.components:
        name = comp.labels['name']
        fp = comp.fields[2]['ref']
        if fp != '""':
            fps[fp] = True
        if name not in found:
            logger.info("Missing: " + name)

destination_library = "/home/jlewallen/conservify/kicad/conservify.pretty"
search = [
    "/home/jlewallen/oss/RocketScreamKicadLibrary",
    "/home/jlewallen/conservify/kicad",
    "/usr/share/kicad/modules"
]
for key, value in fps.iteritems():
    relative_path = key.replace('"', "").replace(":", ".pretty/") + ".kicad_mod"
    original_path = None
    for s in search:
        path = os.path.join(s, relative_path)
        if os.path.isfile(path):
            original_path = path
    if not original_path:
        logger.info("Missing: " + relative_path)
    else:
        name = os.path.basename(original_path)
        destination_path = os.path.join(destination_library, name)
        if original_path != destination_path:
            if not os.path.exists(destination_path):
                logger.info("Copying %s to %s" % (original_path, destination_path))
                shutil.copy(original_path, destination_path)
            else:
                logger.info("File exists: %s" %(destination_path,))
