TDC Final v2 
by Toodles
Release February 2007

Contents:
 Capcom vs SNK 2 (JP)
 Marvel vs Capcom 2 (US)
 Marvel vs Capcom 2 (JP)
 Street Fighter 3: 3rd Strike (US)
 Street Fighter 3: 3rd Strike (JP)
 Super Street Fighter 2 X (NEW English Translation)
 Super Street Fighter 2 X (JP)
 Super Puzzle Fighter 2 X (NEW English Translation)
 Super Puzzle Fighter 2 X (JP)
 Ikaruga (JP)
 Capcom vs SNK 2: Fan Disk (JP)

Extras: 
 Soft reset works as expected. If you try a soft reset
(Start+A+B+X+Y) inside a game, it will go to the first
splash screen for the game. If you try a soft reset at
the splash screen for a game, it will take you to the 
game select menu. If you soft reset at the game select
menu, it will just restart the browser and take you 
right to the same game select menu. 
 VMU saves for all included games. Puzzle Fighter has 
nothing to unlock, but the save on the disk has the 
region already set to U.S.A. so you don't have to go 
into EX settings for English winquotes. 
 Soundtrack options. Any of the games except for 
Ikaruga give a menu option for which soundtrack to 
use. There are options for each of the available games
and a 'Silent' option for those who want sound effects
but no background music. That's a total of 11 
soundtrack- able games, with 7 soundtracks each.
 GameShark and Action Replay are both included and are
the hacked Echelon versions that save to a normal VMU.
Yes, you can use these to turn on codes and play one 
of the included games without leaving your sofa.
 DCLoad tool is included. Versions included are the 
serial version, an original DCLoadIP set at 0.0.0.0 
(default), as well as a 192.168.0.199 version, and a
10.0.0.199 version. If you know what this means and 
does, you can also hex edit the cd image to setup your
own custom IP, but this won't change the menu image 
for the DCLoad.
 VMUTool by Speud. This tool is VERY nice to have 
around, especially when used with DCLoad to transfer 
saves. 
 Others that maybe I forgot to list, or decided to 
leave a little secret.

Ripped:
 All ADX's were downsampled to 22kHz mono and 
normalized. All of the remixed tracks in Puzzle 
Fighter were deleted and the normal versions linked 
in. Every stage in 3rd Strike had one single ADX file
kept; the other two were deleted and linked back to 
the file that was left. VOICE.AFS files were deleted 
and their respective entries in the DP2.INI's 
commented out. The CvS2 Fandisk included the opening 
tracks to many of their games to be played when 
selecting a save game. These have been removed. Since
they were not looped, I couldn't use then as 
soundtrack material, and the FanDisk will likely be 
the least used part of the disk. The space saved is 
well worth it. 
 
Silly Questions:
Q: Will this play in Chankast?
A: As a matter of fact, yes it will. 

Q: Will this play in a PAL Dreamcast?
A: Unknown. I know at least one of the versions is 
3rd Strike should already have the RGB patch, but I 
don't know if its the JP or US version. All of the 
other games are unpatched NTSC versions. 

Q: Can you help me patch it for PAL?
A: No more than this. If you have the codes for 
hexediting the game so it is in PAL, then go ahead and
try them on the disk image. Remember, even though 
there are 8 some copies of the game on the CD, there 
is actually only 1 copy of each file in the image, so
don't freak out if the hex string your looking for is
only there once.
  
Q: Where is the save for the Japanese 3rd Strike?
A: Don't need it. The American save loads and reads 
in both versions.

Q: Why does the music skip when I use a different i
soundtrack for Super Turbo?
A: When the game gets 'tense' (someone gets hit to 
around 25% of their life), it normally plays the 
faster version of the music for that stage. Since 
there isn't a faster version of the alternate 
soundtrack music, it starts that track over at the 
beginning. Sorry, there is no way for me to change 
that. If you select the original ST soundtrack, the 
'tense' music will play properly. 
 
Q: Why does it take up 6 gigs if I copy it to my hard
drive?
A: Don't copy it to your hard drive. 

Q: How'd you fit all that in there? 
A: Using links. 
http://en.wikipedia.org/wiki/Hard_link

Q: What's different between this and the TDC_Final 
from 2004?
A: Aside from the additional games? Good question:
	Different browser used for booting. Using XDP
(Dream Passport 3) instead of Planet Web 2.6, no one 
should be plagued with the 'Select your calling area'
screen the last version had. Even you ghetto folks who
would rather have an empty hole in the side of your 
Dreamcast than leave the damn modem in. Those people 
get no sympathy; you PAL Dreamcast owners, sorry about
that. Using XDP also lets it work in Chankast.

Q: I want to take your disk, and replace the music on
it with my own/my favorite band/whatever. How do I do
that?
A: It's possible, but it's not easy. Sorry, you're on
your own. Feel free to look through the disk; some of
the scripts I used are still in there. The main thing
is to use Linux, hard link all of the files to be 
duplicated with the 'ln' command, and mkisofs will 
take care of the linking on the ISO automatically. If
you need more help than that, you're not getting it 
from me.  

Q: But will you help me do it?
A: Nope. Look around and read up where you can. 
Fileforums.com is probably your best source of 
information. 

Q: What if I want to pull out a single game and make 
a stand alone disk for it?
A: Much easier than trying to rebuild this disk. 
Unless you're planning on replacing EVERY ADX file in
the game, I would recommend you use a copy of the game
from somewhere else. The background music on this disk
has been scrunched down hard. If you still want to 
anyways, go ahead. Copy the directory holding the game
you want to your PC, find a copy of IP.BIN on the disk
and copy it to the directory you just made on your 
hard drive. Walk through all of the instructions in 
the Echelon selfboot tutorial package, and you'll be 
golden. WARNING: The 1ST_READ.BIN for Super Turbo 
cannot be BINHACK'ed or it will fail completely. If 
you want to make a stand alone Super Turbo disk, 
either use the files without BINHACKING them by 
creating your disk in the 45000 LBA DATA/DATA method 
and copying the files as is, or manually hexedit the 
LBA.   

Q: What the LBA used on this disk?
A: This disk was built using the 45000 LBA DATA/DATA 
method. This should boot far more reliably that the 
previous 11702 AUDIO/DATA used in the first TDC_Final.
All of the executables on the disk have been BINHACKED
to 45000 LBA, including the browsers included with 
most of the games. However, trying to run one of 
these browsers from the game fails miserably, so if 
you need to surf on your DC, use the XDP browser that
comes up when it first boots.

Notes and Errata:
-Super Turbo does not seem to play nice with the Bonus
Rounds on a legit DC. At the winquote of your 3rd win,
it may appear to just stay there, and never load the 
bonus round. On occasion, bonus rounds will work fine
in Chankast. You can either keep Bonus Rounds turned 
off, or have another player jump in and you can both 
play the bonus round.  This is a problem I cannot 
resolve since the original Echelon release had the 
same problem. 

-The CvS2 replays were from casual matches in the 
hotel of Evo 2k4, the room 403 party.  Used without 
permission, but they were saved to my VMU :) If I 
didn't get your name in and you're one of the ???'s, 
sorry. All of the A-are teams kinda blend together 
after a while. 

-DCLoad and VMUTool have problems accessing the disk.
They will load fine and work fine, but because they 
were booted from the browser, they cannot read cd's, 
even if you swap disks. There is nothing I can do 
about this. It's still handy to have for testing code
and copying saves from the VMU to a PC, but for any 
kind of disk access, you're going to need a dedicated
DCLoad or VMUTool disk. This limitation affects all 
homebrew code loaded by the browser. 

Counting translations, there are 11 soundtrack-able 
games, with 7 soundtracks each; there is always the 
possibility that one or more combinations won't work
properly.  There are simply too many for me to be able
to test all possible combinations, but they all SHOULD
work. 

Toodles
Feb 6th, 2007




 
