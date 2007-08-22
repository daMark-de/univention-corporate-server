#!/bin/sh -e


# check if user is logged in using ssh

if [ -n "$SSH_CLIENT" ]
    then
    echo "WARNING: You are logged in using SSH -- this may interrupt the update and result in an inconsistent system!"
    echo "         I will wait 10 seconds until starting the update. If you are not sure press Strg+C to quit."
    echo -n "         " 
    
    for i in `seq 1 10`
      do
      echo -n "."
      sleep 1
    done
    echo ""

fi
	

eval `univention-baseconfig shell`


check_space(){
	partition=$1
	size=$2
	usersize=$3
	if [ `df $partition|tail -n1 | awk '{print $4}'` -gt "$size" ]
		then 
		echo -e "Space on $partition:\t OK"
	else
		echo "ERROR:   Not enough space in $partition, need at least $usersize."
        echo "         This may interrupt the update and result in an inconsistent system!"
    	echo "         If neccessary you can skip this check by setting the value of the"
		echo "         baseconfig variable update13_checkfilesystems to \"no\"."
		echo "         But be aware that this is not recommended!"
		echo ""
		exit 1
	fi
}


# check space on filesystems
if [ "$update13_checkfilesystems" != "no" ]
then

	check_space "/var/cache/apt/archives" "1000000" "1 GB"
	check_space "/boot" "6000" "6 MB"
    check_space "/" "1200000" "1.2 GB"

else
    echo "WARNING: skipped disk-usage-test as you requested"
fi


if [ ! -e "/etc/univention/ssl/ucsCA" -a -d "/etc/univention/ssl/udsCA" ] ; then
	mv /etc/univention/ssl/udsCA /etc/univention/ssl/ucsCA
	ln -s ucsCA /etc/univention/ssl/udsCA
fi
