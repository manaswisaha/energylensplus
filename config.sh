#Commands to run when deploying


# Install server requirements 
# Run only once TODO: Add a check

# Apache
sudo apt-get install apache2 apache2-prefork-dev

# mod_wsgi 
sudo apt-get install mod_wsgi

# MySQL Server
sudo apt-get install mysql-server

# Install python libraries with Django web framework
pip install -r requirements.txt

database_name = $1

# Create database
mysql -u root -p -e "create database ".$database_name;

# Create tables
python manage.py sql energylenserver
python manage.py syncdb
