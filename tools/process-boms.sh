#!/bin/bash

python ./sync-bom.py \
       --authority authority.xlsx \
       ../../fk-core/hardware/fk-core.sch \
       ../../fk-weather/hardware/fk-weather.sch \
       ../../fk-atlas/hardware/fk-atlas.sch
