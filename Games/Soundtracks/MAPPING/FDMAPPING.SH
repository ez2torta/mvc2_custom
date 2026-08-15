#!/bin/bash

echo \$1 mapping file
echo \$2 GAMEDIR being changed
echo \$3 SOURCE gamedir source of soundtrack
echo \$4 Game String to weed out of sort
echo \$5 field number of game
for BLAH in `grep -v $4 $1 | cut -f1,${5} | perl -pi -e 's/\t/\:/g'`
do
	export TARGET=`echo $BLAH | cut -d':' -f2| perl -pi -e 's/[^A-Za-z0-9\:\.\_]//g'|perl -pi -e 's/\.ADX/\.BIN/g'`
	export LINKNAME=`echo $BLAH | cut -d':' -f1| perl -pi -e 's/[^A-Za-z0-9\:\.\_]//g'`
	if [ -z $TARGET ] 
	then
		echo echo null target $TARGET
	else
		rm ${2}/${LINKNAME}  
		ln ${3}/${TARGET} ${2}/${LINKNAME}
	fi
done
