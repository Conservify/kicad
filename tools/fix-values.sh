#/bin/bash

fix() {
    ./kicad-tool.py --from-value "$1" --to-value "$2" \
         /home/jlewallen/fieldkit/core/hardware/fk-core.sch \
         /home/jlewallen/fieldkit/naturalist/hardware/main-board/fk-naturalist.sch \
         /home/jlewallen/fieldkit/atlas/hardware/fk-atlas.sch \
         /home/jlewallen/fieldkit/weather/hardware/module-board/fk-weather.sch \
         /home/jlewallen/fieldkit/weather/hardware/sensor-board/fk-weather-sensors.sch \
         /home/jlewallen/fieldkit/naturalist/hardware/sensor-board/fk-naturalist-sensors.sch \
         /home/jlewallen/fieldkit/sonar/hardware/fk-sonar.sch
}


# fix "1uF 10V X5R" "1uF"
# fix "1uF 50V X5R" "1uF"
# fix "4.7nF 25V X7R" "4.7nF"
# fix "4.7uF 10V X5R" "4.7uF"
# fix "47uF 10V X5R" "47uF"
# fix "1k" "1K"
# fix "100k" "100K"
# fix "MCP1700T-XXX2E" "MCP1700T-3302E/MB"
# fix "DIODE_DUAL_Schottky" "PMEG3020CPA"
# fix "S25FL1xxK0XM" "S25FL116K0XMFI041"
# fix "Battery_Cell" "BATTERY_CELL"
# fix "CONN-HDR-2x5" "CONN_02x05_SWD"
# fix "BKP1005TS121-T" "BLM18KG221SN1D"
# fix "Conn_01x04" "CONN_01x04"

