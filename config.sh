#!/bin/bash
# Script to configure the system

bash_file="$HOME/.bashrc"

# 1. Confirm the user that he is in the repo directory
echo -e "Are you in EnergyLensPlus's installation directory (y/n)?"
read isInstallDirectory
if [ $isInstallDirectory = 'n' ] || [ $isInstallDirectory = 'N' ]; then
	echo "Please go to the directory and run this file again"
	exit 1

# 2. If yes, then add an repo directory's (ELENSERVER) entry to ~/.bashrc file
# and enable the changes
elif [ $isInstallDirectory = 'y' ] || [ $isInstallDirectory = 'Y' ]; then
	ELENSHOME=`pwd`
	echo "Installation Directory: $ELENSHOME"
	if [ -z `grep 'ELENSERVER=' $bash_file` ]; then
		echo ``ELENSERVER=$ELENSHOME`` >> $bash_file
		echo ``export ELENSERVER`` >> $bash_file
	else
		echo "Entry already made in the bashrc file"
	fi
	. $bash_file
else
	echo "Incorrect input. Please enter either y or n"
	exit 1
fi

celery_config_file="${ELENSHOME}/config/celery-config"

# 3. Copy ELENSERVER variable to the appropriate location in the celery-config file
sed -i "s#\(CELERYD_CHDIR=\).*#\1$ELENSHOME/#g" $celery_config_file
sed -i "s#\(CELERYBEAT_CHDIR=\).*#\1$ELENSHOME/#g" $celery_config_file

sed -i "s#\(CELERYD_LOG_FILE=\).*#\1$ELENSHOME/logs/%N.log#g" $celery_config_file
sed -i "s#\(CELERYD_PID_FILE=\).*#\1$ELENSHOME/logs/%N.pid#g" $celery_config_file

sed -i "s#\(CELERYBEAT_LOG_FILE=\).*#\1$ELENSHOME/logs/beat.log#g" $celery_config_file
sed -i "s#\(CELERYBEAT_PID_FILE=\).*#\1$ELENSHOME/logs/beat.pid#g" $celery_config_file

# Assign the default user
user=`whoami`
sed -i "s#\(DEFAULT_USER=\).*#\1\"$user\"#g" "${ELENSHOME}/config/celery-init-script"
sed -i "s#\(DEFAULT_USER=\).*#\1\"$user\"#g" "${ELENSHOME}/config/celerybeat-init-script"


# 4. Copy the three files from config directory to the appropriate locations
	# celery-config --> /etc/default/celeryd
	# celery-init-script --> /etc/init.d/celeryd
	# celerybeat-init-script --> /etc/init.d/celerybeat
sudo cp "${ELENSHOME}/config/celery-config" /etc/default/celeryd
sudo cp "${ELENSHOME}/config/celery-init-script" /etc/init.d/celeryd
sudo cp "${ELENSHOME}/config/celerybeat-init-script" /etc/init.d/celerybeat

# 5. Give the init scripts execute privileges for all users
sudo chmod 755 /etc/init.d/celeryd /etc/init.d/celeryd

echo "Celery configured"

# 6. Create the energylens command symbolic link
if [ ! -f "/usr/bin/energylens" ];then
	sudo ln -s "$ELENSHOME/energylenserver/management/energylens" /usr/bin/energylens
	sudo chmod 755 /usr/bin/energylens
	echo "'energylens' command created"
fi

echo "EnergyLensPlus system configuration complete! Use 'energylens' cmd to manage the server"
echo "Usage: energylens {start|stop|status}"