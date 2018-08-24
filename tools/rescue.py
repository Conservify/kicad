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

lib = schlib.SchLib("/home/jlewallen/conservify/kicad/conservify.lib")
for c in lib.components:
    clean = c.name.replace("~", "")
    print clean

map = {
    'fk-naturalist-rescue:R' : 'conservify:R',
    'fk-naturalist-rescue:CAPACITOR-CERAMIC' : 'conservify:CAPACITOR_CERAMIC',
    'fk-naturalist-rescue:C' : 'conservify:CAPACITOR_CERAMIC',
    'fk-naturalist-rescue:LED-SINGLE': 'conservify:LED_SINGLE',
    'fk-naturalist-rescue:MICRO-USB': 'conservify:MICRO_USB',
    'fk-naturalist-rescue:+3V3': 'conservify:3V3',
    'fk-naturalist-rescue:Conn_01x06': 'conservify:CONN_01x06',
    'fk-naturalist-rescue:Conn_01x05': 'conservify:CONN_01x05',
    'fk-naturalist-rescue:Conn_01x02': 'conservify:CONN_01x02',
    'fk-naturalist-rescue:Conn_01x04': 'conservify:CONN_01x04',
    'fk-naturalist-rescue:CONN_01X02': 'conservify:CONN_01x02',
    'fk-naturalist-rescue:TACT-SWITCH_2Pins': 'conservify:SWITCH_CONN_02',
    'fk-naturalist-rescue:CONN-HDR-2x5': 'conservify:CONN_02x05_SWD',
    'fk-naturalist-rescue:ATSAMD21G18A-AU': 'conservify:ATSAMD21G18A_AU',
    'fk-naturalist-rescue:MOSFET-N': 'conservify:MOSFET_N',
    'fk-naturalist-rescue:DIODE_DUAL_Schottky': 'conservify:DIODE_DUAL_SCHOTTKY',
    'fk-naturalist-rescue:adm3260': 'conservify:ADM3260',
    'fk-naturalist-rescue:VCC': 'conservify:VCC',
    'fk-naturalist-rescue:WATER_PROBE': 'conservify:NATURALIST_WATER_PROBE',
    'fk-naturalist-rescue:S2B-PH-SM4-TB': 'conservify:S2B_PH_SM4_TB',
    'fk-naturalist-rescue:RF-SMA-EDGE': 'conservify:RF_SMA_EDGE',
    'fk-naturalist-rescue:MICROSD': 'conservify:MICRO_SD',
    'fk-naturalist-rescue:ATWINC1500-MR210PA': 'conservify:ATWINC1500_MR210PA',
    'fk-naturalist-rescue:Battery_Cell': 'conservify:BATTERY_CELL',
    'fk-naturalist-rescue:Conn_01x01': 'conservify:CONN_01x01',
    "fk-naturalist-rescue:BNO055-RESCUE-fk-naturalist": "conservify:BNO055_JACOB",
    "fk-naturalist-rescue:PRTR5V0U2X-RESCUE-fk-naturalist": "conservify:PRTR5V0U2X",
    "fk-naturalist-rescue:ISL8541x": "conservify:ISL8541X",
    "fk-naturalist-rescue:INDUCTOR-RESCUE-fk-naturalist": "conservify:INDUCTOR",
    "fk-naturalist-rescue:Conn_01x03": "conservify:CONN_01x03",
    "fk-naturalist-rescue:Conn_01x09": "conservify:CONN_01x09",
    "fk-naturalist-rescue:Conn_01x07": "conservify:CONN_01x07",

    "RocketScreamKicadLibrary:CAPACITOR-CERAMIC": "conservify:CAPACITOR_CERAMIC",
    "RocketScreamKicadLibrary:MICRO-USB": "conservify:MICRO_USB",
    "RocketScreamKicadLibrary:S2B-PH-SM4-TB": "conservify:S2B_PH_SM4_TB",
    "RocketScreamKicadLibrary:TACT-SWITCH_2Pins": "conservify:SWITCH_CONN_02",
    "RocketScreamKicadLibrary:MOSFET-N": "conservify:MOSFET_N",
    "RocketScreamKicadLibrary:CONN-HDR-2x5": "conservify:CONN_02x05_SWD",
    "RocketScreamKicadLibrary:LED-SINGLE": "conservify:LED_SINGLE",
    "RocketScreamKicadLibrary:RF-SMA-EDGE": "conservify:RF_SMA_EDGE",
}

paths = [
    "/home/jlewallen/fieldkit/naturalist/hardware/main-board/fk-naturalist.sch",
]

for path in paths:
    logger.info(path)
    fixing = sch.Schematic(path)
    for comp in fixing.components:
        ref = comp.fields[0]['ref']
        name = comp.labels['name']
        fp = comp.fields[2]['ref']
        if not 'conservify:' in name:
            if name in map:
                logger.info("Fixed %s -> %s" % (name, map[name]))
                comp.labels['name'] = map[name]
            else:
                logger.info("Missing! %s" % (name))
    fixing.save()

