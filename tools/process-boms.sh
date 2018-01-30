#!/bin/bash

ROOT="/Users/jlewallen/fieldkit"

python ./sync-bom.py \
       --authority authority.csv \
       $ROOT/core/hardware/fk-core.sch \
       $ROOT/naturalist/hardware/fk-naturalist.sch \
       $ROOT/weather/hardware/sensor-board/fk-weather-sensors.sch \
       $ROOT/weather/hardware/module-board/fk-weather.sch \
       $ROOT/sonar/hardware/fk-sonar.sch \
       $ROOT/atlas/hardware/fk-atlas.sch
