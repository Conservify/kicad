export PATH=$PATH:/c/Python27/Scripts:/c/Python27

PROJECT_FILE=`ls *.pro`
PROJECT=`basename $PROJECT_FILE .pro`

kifield -rg -i $PROJECT.sch -x $PROJECT.csv
