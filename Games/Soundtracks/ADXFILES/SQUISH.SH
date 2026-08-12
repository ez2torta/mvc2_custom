#!/usr/bin/bash

adx2wav.exe $1
mv "$1" "$1.bak"
export ORGNAME=`echo $1 | cut -d'.' -f1`
export WAVNAME=$ORGNAME.wav
normalize $WAVNAME
export TARGNAME=$ORGNAME.adx
export LOOPSTART=`grep $1 looplist.txt | cut -d':' -f2`
export LOOPEND=`grep $1 looplist.txt | cut -d':' -f3`
echo original Loopend is $LOOPEND
export OPTIONS=""
if [ "$2" = "mono" ]
then
        OPTIONS="$OPTIONS -ch3"
fi
if [ "$2" = "bitrate" ]
then
        OPTIONS="$OPTIONS -sf22050"
fi

if [ "$2" = "both" ]
then
	OPTIONS="$OPTIONS -ch3 -sf22050"
fi

if [ "$LOOPSTART" != "NO" ]
then #number of samples will change. Let's dry run it to see the number
	export LOOPNUM=`adxencd "$WAVNAME" 2>&1 | grep output | cut -f2 -d':' | cut -d' ' -f2`
#	let "LOOPSTART /=2"
	echo Calculated loopend is $LOOPNUM
	if [ "$LOOPNUM" -lt "$LOOPEND" ] 
	then
		export LOOPEND=$LOOPNUM
	fi
	echo Using Loopend: $LOOPEND
	rm $TARGNAME
fi
if [ "$LOOPSTART" != "NO" ]
then
	OPTIONS="$OPTIONS -lps$LOOPSTART -lpe$LOOPEND"
fi

echo OPTIONS set :$OPTIONS
adxencd "$WAVNAME" $OPTIONS
rm "$WAVNAME"

mv "$ORGNAME.adx" "$ORGNAME.TMP"
mv "$ORGNAME.TMP" "$1"
