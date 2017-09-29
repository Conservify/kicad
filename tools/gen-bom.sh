export PATH=$PATH:/c/Python27/Scripts:/c/Python27

PROJECT_FILE=`ls *.pro`
PROJECT=`basename $PROJECT_FILE .pro`
CSV_ALL=$PROJECT-all.csv
rm -f $CSV_ALL
for a in *.sch; do
    echo $a
    FN=`basename $a .sch`
    kifield -x $a -i $FN.csv
    tail -n +2 $FN.csv >> $CSV_ALL
    rm $FN.csv
done

kifield -rg -x $PROJECT.sch -i $PROJECT.csv
