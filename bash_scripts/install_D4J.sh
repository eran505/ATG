#!/bin/bash


sudo apt-get install subversion -y
cd
DIRECTORY='/home/ise/programs'
if [ ! -d "$DIRECTORY" ]; then
	# Control will enter here if $DIRECTORY doesn't exist.
	mkdir ${DIRECTORY} 	

cd ${DIRECTORY}
git clone https://github.com/rjust/defects4j
cd defects4j
bash ./init.sh
sudo apt-get install libdbi-perl
sudo cpan Bundle::CSV DBD::CSV DBI
exit
