timestamps {
    node () {
        stage ('git') {
            checkout([$class: 'GitSCM', branches: [[name: '*/master']], userRemoteConfigs: [[url: 'https://github.com/Conservify/kicad.git']]])
        }

        def schematics = []

        stage ("schematics") {
            sh "rm -f *.sch"

            sh "wget https://github.com/fieldkit/core/raw/master/hardware/fk-core.sch"

            sh "wget https://github.com/fieldkit/sonar/raw/master/hardware/fk-sonar.sch"

            sh "wget https://github.com/fieldkit/weather/raw/master/hardware/sensor-board/fk-weather-sensors.sch"
            sh "wget https://github.com/fieldkit/weather/raw/master/hardware/module-board/fk-weather.sch"

            sh "wget https://github.com/fieldkit/naturalist/raw/master/hardware/sensor-board/fk-naturalist-sensors.sch"
            sh "wget https://github.com/fieldkit/naturalist/raw/master/hardware/main-board/fk-naturalist.sch"

            // NOTE: The isolated_atlas?.sch files are included from fk-atlas.sch and so we skip listing them below to avoid processing them twice.
            sh "wget https://github.com/fieldkit/atlas/raw/master/hardware/fk-atlas.sch"
            sh "wget https://github.com/fieldkit/atlas/raw/master/hardware/isolated_atlas0.sch"
            sh "wget https://github.com/fieldkit/atlas/raw/master/hardware/isolated_atlas1.sch"
            sh "wget https://github.com/fieldkit/atlas/raw/master/hardware/isolated_atlas2.sch"
            sh "wget https://github.com/fieldkit/atlas/raw/master/hardware/isolated_atlas3.sch"
            sh "wget https://github.com/fieldkit/atlas/raw/master/hardware/isolated_atlas4.sch"
        }

        stage ('boms') {
            dir ("tools") {
                withPythonEnv('python') {
                    sh "rm -rf kifield-0.1.8 && tar xf kifield*.tar.gz && (cd kifield-0.1.8 && python setup.py install)"

                    sh "python kicad-tool.py --bom ../fk-core.sch ../fk-naturalist.sch ../fk-naturalist-sensors.sch ../fk-sonar.sch ../fk-atlas.sch ../fk-weather.sch ../fk-weather-sensors.sch"

                    sh "ls -alh"
                }
            }
        }

        stage ("archive") {
            dir ("tools") {
                archiveArtifacts "super.xlsx, authority.xlsx"
            }
        }
    }
}
