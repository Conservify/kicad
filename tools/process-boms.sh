#!/bin/bash

python ./sync-bom.py \
       --authority authority.xlsx \
       ../../../fieldkit/core/hardware/fk-core.sch \
       ../../../fieldkit/weather/hardware/fk-weather.sch \
       ../../../fieldkit/sonar/hardware/fk-sonar.sch \
       ../../../fieldkit/atlas/hardware/fk-atlas.sch
