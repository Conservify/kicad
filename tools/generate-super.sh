#!/bin/bash

set -xe

FK=$HOME/fieldkit

./kicad-tool.py --bom \
                $FK/core/hardware/fk-core.sch \
                $FK/atlas/hardware/fk-atlas.sch \
                $FK/sonar/hardware/fk-sonar.sch \
                $FK/weather/hardware/module-board/fk-weather.sch \
                $FK/weather/hardware/sensor-board/fk-weather-sensors.sch \
                $FK/naturalist/hardware/sensor-board/fk-naturalist-sensors.sch
