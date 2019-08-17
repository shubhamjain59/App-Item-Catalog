App Item Catalog

A Item catalog app which list all the Categories and the Items in each Category with each Items details

Prerequisites
Python
Vagrant
VirtualBox
App Setup
This project makes use of Udacity's Linux-based virtual machine (VM) configuration which includes all of the necessary software to run the application.

Download VirtualBox and install
VirtualBox is the software that actually runs the virtual machine.
You can download it from this URL - https://www.virtualbox.org/wiki/Download_Old_Builds_5_1

Download Vagrant and install
Vagrant is the software that configures the VM and lets you share files between host and the VM's filesystem.
You can downlaod it from this URL - https://www.vagrantup.com/downloads.html

Download the VM configuration
you can use Github to fork and clone this repository.
Change your directory to this repository and do cd vagrant

Start the virtual machine
From your terminal, inside the vagrant subdirectory, run the command vagrant up
This will cause Vagrant to download the Linux operating system and install it.
When vagrant up is finished running, you will get your shell prompt back.
At this point, you can run vagrant ssh to log in to your newly installed Linux VM!

How to Run this application-

Download the ZIP folder of this project & Extract It.
place the App Item Catalog folder in your Vagrant directory
Launch Vagrant
$ Vagrant up 
Login to Vagrant
$ Vagrant ssh
Change directory to /vagrant
$ Cd /vagrant
Initialize the database
$ Python db_setup.py
Populate the database with some initial data
$ Python data.py
Launch application
$ Python project.py
Open the browser and go to http://localhost:5000
JSON endpoints
Returns JSON of all category
/catalog.json
Returns JSON of specific category
/catalog/category<int:category_id>/json
Returns JSON of specific item in a category
/catalog/category<int:category_id>/item<int:item_id>/json