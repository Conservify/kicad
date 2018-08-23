#!/bin/bash

./update-schematic-fields.py --bom \
    12 ~/fieldkit/core/hardware/fk-core.sch \
    4 ~/fieldkit/atlas/hardware/fk-atlas.sch \
    4 ~/fieldkit/weather/hardware/module-board/fk-weather.sch \
    4 ~/fieldkit/weather/hardware/sensor-board/fk-weather-sensors.sch \
    4 ~/fieldkit/sonar/hardware/fk-sonar.sch
