#!/usr/bin/env python2.7
# Title:    Python 3 QAS Install
# Author:   Matthew Williams
# Date:     2/22/2017
# Latest Update:   4/12/2017
#
# Description: Python Code to Install/Upgrade
# Quest Authentication Services Smart Card Configuration
#
# Use: QAS installation, smartcard enforcement, smartcard dependency installation, configuration compliance
#
# pyvassc is designed to install QAS 4.1.0 or to upgrade from another version to the labwide current version.
# pyvassc will also manipulate pam configuration files and display manager configuration files to allow for 
# smartcard enforcement in order to comply with the HSPD-12 Directive and DOE regulation.
# pyvassc will install dependencies per OS and QAS requirements to allow for PKCS11 and vassc compatibility
# pyvassc will join the domain via a prompt for information from the user who initializes the script
# pyvassc requires su level privleges.
# SEE man page for vas for additional information on the functionality of vas and the vastool
import re
import fileinput
import os
import sys
import platform
import shutil
import subprocess
import logging
import time
#
# VARIABLE DEFINITION
#
file_to_test = 'nothing'# set the global variable to be edited later. This will be a path.
line_to_test = 'auth\s*\[success=ok default=die\]\s*pam_localuser.so' # Regex for smartcard enforcement line
dist_name = platform.linux_distribution()[0] # For Linux Distro's store the distribution name
dist_version = platform.linux_distribution()[1] # For Linux Distro's store the version number
smartcard_line = 'auth\s*requisite\s*pam_vas_smartcard\.so\s*echo_return' # regex line for detecting where to insert enforcement
mdm_line = '\AIncludeAll=true.*' # variable to detect MDM's include all = true
mdm_pam_line = '\Aauth\s*sufficient\s*pam_succeed_if.so\s*user\s*ingroup\s*nopasswdlogin' #REgex for MDM 
smartcard_auth_pam_line = '\Aauth\s*required\s*pam_env.so' #REgex for smartcard-auth 
script_path = os.path.abspath(os.path.dirname(sys.argv[0])) # Location script is ran from.
current_time = time.strftime("%H:%M:%S") # time variable
current_date = time.strftime("%d-%m-%Y") # date variable
log_file_path = 'QASscript_' + dist_name + dist_version + '_' + current_date + '_' + current_time + '.log' # Where the log is being saved
debug_flag = False # variable to call when you need to debug
intro_text = """
##################################################################
#Title:    Python QAS Install
# Author:   Matthew Williams
# Date:     2/22/2017
# Latest Update:   3/14/2017
#
# Description: Script to Install/Upgrade
# Quest Authentication Services Smart Card Configuration 
#
# This script is to be used on the following OS's:
# CentOS 7+
# Ubuntu 16.04+
# OpenSuse Leap 42.2+
# Mint 18.3+
# RHEL 7.3+
# Oracle 7.3
#
# If you are utilizing this script on any other OS you
# accept all risks and responsibilities for any data lost
# or misconfiguration that may occur.
"""
outro_text = """
# The script has completed!
#
# No major errors were discovered during the configuration.
##################################################################
"""
install_missing = """
*** The install.sh file was not found ***
This is likely due to this script not being ran from its
original location. 
Please locate the install.sh file and run this script from
that location or download the QAS files again and run the 
script from there.
***
"""
#
# END OF VARIABLE DEFINITION
#

#
# LOGGING DEFINITION
#
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# create file handler and set level to debug
file_handler = logging.FileHandler(log_file_path)
file_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
file_handler.setFormatter(formatter)

# create stream handler and set level to info then print that stream to console
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)
formatterstream = logging.Formatter("%(levelname)s - %(message)s")
stream_handler.setFormatter(formatterstream)

# add Handlers to logger
logger.addHandler(stream_handler)
logger.addHandler(file_handler)
#
# END OF LOGGING DEFINITION
#

#
# FUNCTIONS DEFINITION
#
def check_exists(local_file_to_test, local_line_to_test): #Checks to see if auth    [success=ok default=die]    pam_localuser.so already exists in the file before making any changes.
    line_matched_check = False
    test_file = open(local_file_to_test, "r")
    for line in test_file:
        if line_matched_check is False :
            if re.match(local_line_to_test, line):
                logger.debug(local_line_to_test + ' Line exists already in: ' + local_file_to_test)
                line_matched_check = True
                return True

def check_os(): # Function to determine OS and whether or not to continue
    from sys import platform
    if platform == "linux" or platform == "linux2": # Linux...
        print (intro_text)
        print ("Your OS:"),
        print (dist_name),
        print (dist_version)
        logger.debug(dist_name + ' ' + dist_version)
        return()
            # End Linux...
    elif platform == "darwin": #OS X...
        logger.error("Your OS is MAC")
        logger.error("This script is for Linux Machines only...")
        exit_script(0)
            # End OS X...
    elif platform == "win32": # Windows...
        logger.error("Your OS is Windows")
        logger.error("This script is for Linux Machines only...")
        exit_script(0)
            # End Windows...
    else:
        logger.error("I cannot determine your Operating System type...") # tell user that the OS cannot be determined and quit
        exit_script(0)

def exit_script(exit_code): # Function to exit script, will build exception handling in the future
    logger.info("Exiting script.")
    sys.exit(exit_code)

def manipulate_pam_files(local_file_to_test, local_line_to_test):
    line_matched = False
    file_exists = False
    if os.path.exists(local_file_to_test):    #Testing to see if /etc/pam.d/test exists.
        file_exists = True
        test_file = open(local_file_to_test, "r")
        for line in test_file:
            if line_matched is False:
                if re.match(smartcard_line, line):   # Testing to ensure file is setup for smartcard auth before enforcing it.
                    line_matched = True
                    if check_exists(local_file_to_test, local_line_to_test): #Testing to see if pam_localuser.so already exists.
                        logger.debug(local_file_to_test + " is already configured! Not making any changes...") # If it does exist make no changes.
                    else:
                        for line in fileinput.input(local_file_to_test, inplace=1):
                            print (line),
                            if re.match(smartcard_line, line):
                                print ('auth    [success=ok default=die]    pam_localuser.so') # Enforce via pam_local.so module
                        logger.debug('Configuring' + local_file_to_test) # Configure Message. Inform user of which files are being configured
    if file_exists is True:
        if line_matched is False: # Debug to see if file is smartcard configured
            logger.error(local_file_to_test + " check failed")
            logger.error("This means the files exists but is not configured for smartcard use.")
            logger.error("Please configure " + local_file_to_test + " for smartcards.")
            logger.error("Then restart this script.")
            exit_script(0)

def file_copy(src_path, dst_path, file):
    #if the destination path doesn't exist, create it
    file_dstpath = dst_path + "/" + file
    file_srcpath = src_path + "/" + file
    if not os.path.exists(dst_path):
        os.mkdir(dst_path)
        logger.debug('Directory made: ' + dst_path)
    try:
        shutil.copy2(file_srcpath, file_dstpath)
        logger.debug('File copied to: ' + file_dstpath)
    except shutil.Error as e:
        logger.error(file_dstpath + ' not copied. Error: %s' % e)
    except OSError as e:
        logger.exception(file_dstpath + ' not copied. Error: %s' % e)

def check_displaymanagers (): # Check for display managers.
    yes = set(['yes','y', 'ye', ''])
    no = set(['no','n'])
    line_matched = False
    os.system("sudo /opt/quest/bin/vastool smartcard configure pam login") # All OS's need this file configured
    if os.path.exists('/etc/pam.d/common-auth'):
        logger.debug('Configuring /etc/pam.d/common-auth')
        os.system("sudo /opt/quest/bin/vastool smartcard configure pam common-auth") # common-auth
    if os.path.exists('/etc/pam.d/common-auth-pc'):
        os.system("sudo /opt/quest/bin/vastool smartcard configure pam common-auth-pc")
    if os.path.exists('/etc/pam.d/common-auth-smartcard'):
        os.system("sudo /opt/quest/bin/vastool smartcard configure pam common-auth-smartcard")
    if os.path.exists('/etc/pam.d/password-auth'):
        logger.debug('Configuring /etc/pam.d/password-auth')
        os.system("sudo /opt/quest/bin/vastool smartcard configure pam password-auth") # password-auth
    if os.path.exists('/etc/pam.d/password-auth-ac'):
        logger.debug('Configuring /etc/pam.d/password-auth-ac in case password-auth is inaccessible...')
        os.system("sudo /opt/quest/bin/vastool smartcard configure pam password-auth-ac") # password-auth-ac
    if os.path.exists('/etc/pam.d/smartcard-auth-ac'):
        logger.debug('Configuring /etc/pam.d/smartcard-auth-ac in case smartcard-auth is inaccessible...')
        os.system("sudo /opt/quest/bin/vastool smartcard configure pam smartcard-auth-ac") # smartcard-auth-ac
    if os.path.exists('/etc/pam.d/smartcard-auth'):
        logger.debug('Configuring /etc/pam.d/smartcard-auth')
        os.system("sudo /opt/quest/bin/vastool smartcard configure pam smartcard-auth")        # smartcard-auth
        test_file = open('/etc/pam.d/smartcard-auth', "r") # Testing smartcard-auth for the smartcard line, primarily because it fails often.
        for line in test_file:
            if re.match(smartcard_line, line):
                line_matched = True
                logger.debug('Line in /etc/pam.d/smartcard-auth FOUND no extra configuration needed...') # return message in debug if line already exists
        if line_matched is False: # If line does not exist we need to search for the correct location to place the file.
            for line in fileinput.input('/etc/pam.d/smartcard-auth', inplace=1):
                print (line),
                if re.match(smartcard_auth_pam_line, line):
                    print ('auth	sufficient	pam_vas_smartcard.so')
                    print ('auth	requisite	pam_vas_smartcard.so echo_return')
            logger.debug('Line in /etc/pam.d/smartcard-auth NOT found configuration needed...') # return message in debug if line does not exist
    if os.path.exists('/etc/pam.d/mdm'): # MDM
        logger.debug('MDM was detected, configuring...')
        os.system("sudo /opt/quest/bin/vastool smartcard configure pam mdm")
        test_file = open('/etc/pam.d/mdm', "r") # Testing MDM for the smartcard line, primarily because it fails often.
        for line in test_file:
            if re.match(smartcard_line, line):
                line_matched = True
        if line_matched is False:
            for line in fileinput.input('/etc/pam.d/mdm', inplace=1):
                print (line),
                if re.match(mdm_pam_line, line):
                    print ('auth	sufficient	pam_vas_smartcard.so')
                    print ('auth	requisite	pam_vas_smartcard.so echo_return')
        if os.path.exists('/usr/share/mdm/defaults.conf'):
            os.system("sudo sed -i 's/IncludeAll=true/IncludeAll=false/g' '/usr/share/mdm/defaults.conf'")# change the MDM Defaults to not show all users on login screen.
            if debug_flag is True:
                logger.debug('MDM /usr/share/mdm/defaults.conf has been configured')
            logger.info('You will need to restart the mdm service after this script in order to function properly.') # Let user know they need to restart mdm after running this.
        else:
            logger.error('***/usr/share/mdm/defaults.conf was not detected. MDM was not configured correctly.***')
    if os.path.exists('/etc/pam.d/lightdm'): #LightDM
        logger.debug('LightDM was detected, configuring...')
        os.system("sudo /opt/quest/bin/vastool smartcard configure pam lightdm")
        os.system("sudo /opt/quest/bin/vastool smartcard configure pam lightdm-greeter")
        test_file = open('/etc/pam.d/lightdm', "r") # Testing LightDM for the smartcard line, primarily because it fails often.
        for line in test_file:
            if re.match(smartcard_line, line):
                line_matched = True
        if line_matched is False:
            for line in fileinput.input('/etc/pam.d/lightdm', inplace=1):
                print (line),
                if re.match(mdm_pam_line, line):
                    print ('auth	sufficient	pam_vas_smartcard.so')
                    print ('auth	requisite	pam_vas_smartcard.so echo_return')
        if os.path.exists(script_path + '/10-ubuntu.conf'):
            file_copy(script_path, '/etc/lightdm/lightdm.conf.d', '10-ubuntu.conf')
        else:
            logger.error('***Script was not ran from original location. LightDM has not been completely configured.***')
    if os.path.exists('/etc/pam.d/gdm'): #GDM
        logger.debug('GDM was detected, configuring...')
        os.system("sudo /opt/quest/bin/vastool smartcard configure pam gdm")
    if os.path.exists('/etc/pam.d/gdm-smartcard-ac'):
        logger.debug('GDM was detected, configuring /etc/pam.d/gdm-smartcard...')
        os.system("sudo /opt/quest/bin/vastool smartcard configure pam gdm-smartcard-ac")
    if os.path.exists('/etc/pam.d/sddm'): #SDDM - We don't currently have it configured but we would like to find a solution.
        logger.error('SDDM was detected, however, we have no current configuration for SDDM.')
        logger.error('Please use GDM or LightDM for your primary display manager.')
        os.system("sudo /opt/quest/bin/vastool smartcard configure pam sddm")
    if os.path.exists('/etc/selinux/config'):
        print("SELinux has been detected and must be disabled")
        print("Would you like to disable SELinux now?")
        choice = raw_input.lower()
        if choice in yes:
            os.system("sudo sed -i 's/SELINUX=enforcing/SELINUX=disabled/g' '/etc/selinux/config'")
            logger.info('SELINUX has been disabled or is already disabled')
            logger.info('You will need to restart your machine after this script in order to function properly.')
            return()
        elif choice in no:
            logger.info("SELinux was not disabled, smartcard enforcement cannot be ensured...")
            return()
        else:
            logger.info("Yes or no was not selected, defaulting to yes...")
            os.system("sudo sed -i 's/SELINUX=enforcing/SELINUX=disabled/g' '/etc/selinux/config'")
            logger.info('SELINUX has been disabled')
            logger.info('You will need to restart your machine after this script in order to function properly.')#defualt to yes if a bad choice is chosen.
            return()
        
def vasd_config (): # Configure vasd with the vastool
    os.system("sudo /opt/quest/bin/vastool configure vas vasd username-attr-name samAccountName") # Configure vasd to allow samAccountName as the primary human-readable identifier
    logger.debug("username-attr-name samAccountName set")
    os.system("sudo /opt/quest/bin/vastool configure vas vasd allow-upn-login True") # Configure vasd to allow UPN login for smartcards
    logger.debug("allow-upn-login True set")
    
def pkcs11_config (): # check for pkcs11 library and select the one based on which files exist
    if os.path.exists('/usr/lib64/opensc-pkcs11.so'):
        logger.debug('/usr/lib64/opensc-pkcs11.so detected configuring...')
        os.system("sudo /opt/quest/bin/vastool smartcard configure pkcs11 lib /usr/lib64/opensc-pkcs11.so") # prefer opensc pkcs11 library
        return()
    elif os.path.exists('/usr/lib/x86_64-linux-gnu/pkcs11/opensc-pkcs11.so'):
        logger.debug('/usr/lib/x86_64-linux-gnu/pkcs11/opensc-pkcs11.so detected configuring...')
        os.system("sudo /opt/quest/bin/vastool smartcard configure pkcs11 lib /usr/lib/x86_64-linux-gnu/pkcs11/opensc-pkcs11.so") # check for alt opensc pkcs11 library
        return()
    elif os.path.exists('/usr/lib64/pkcs11/libcoolkeypk11.so'):
        logger.debug('/usr/lib64/pkcs11/libcoolkeypk11.so detected configuring...')
        os.system("sudo /opt/quest/bin/vastool smartcard configure pkcs11 lib /usr/lib64/pkcs11/libcoolkeypk11.so") # check for coolkey pkcs11 library
        return()
    else:
        logger.error('No PKCS11 Library detected, something went wrong...')
        logger.error('Please verify OpenSC has been installed correctly and is not missing dependencies')
        os.system("sudo updatedb") #update the locate db if no pkcs11 library can be found
        logger.debug(subprocess.check_output("sudo locate pkcs11.so", shell=True)) # use locate library to send the locate search to logs
        exit_script(0)

def package_install (): # run package managers for each OS
    if 'CentOS' in dist_name:
        logger.info("CENTOS MATCHED!")
        os.system("sudo yum install -y coolkey opensc esc pam_pkcs11 pcsc-lite ccid opencryptoki libc.so.6 libresolv.so.2 librt.so.1 libpam.so.0")
        os.system("sudo rpm -i ./add-ons/smartcard/linux-x86_64/vassc-4.1.0-21853.x86_64.rpm") # VASSC rpm package install.
        os.system("sudo systemctl restart pcscd")
        logger.debug("pcscd restarted")
        return()
    elif 'Ubuntu' in dist_name:
        logger.info("Ubuntu MATCHED!")
        os.system("sudo apt-get install -y libpcsclite1 pcscd pcsc-tools pkg-config opensc coolkey libccid libacsccid1")
        os.system("sudo dpkg -iE ./add-ons/smartcard/linux-x86_64/vassc_4.1.0-21854_amd64.deb") # VASSC deb package install, will not install if already installed.
        os.system("sudo systemctl restart pcscd")
        logger.debug("pcscd restarted")
        return()
    elif 'SUSE' in dist_name:
        logger.info("SUSE MATCHED!")
        os.system("sudo zypper install -y opensc pam_pkcs11 pcsc-lite pcsc-ccid openCryptoki libc.so.6 libresolv.so.2 librt.so.1 libpam.so.0") #Zypper dependencies package installs
        os.system("sudo rpm -i ./add-ons/smartcard/linux-x86_64/vassc-4.1.0-21853.x86_64.rpm") # VASSC rpm package install.
        os.system("sudo systemctl restart pcscd")
        logger.debug("pcscd restarted")
        return()
    elif 'Mint' in dist_name:
        logger.info("Mint MATCHED!")
        os.system("sudo apt-get install -y libpcsclite1 pcscd pcsc-tools pkg-config opensc coolkey libccid libacsccid1 ")
        os.system("sudo dpkg -iE ./add-ons/smartcard/linux-x86_64/vassc_4.1.0-21854_amd64.deb") # VASSC deb package install, will not install if already installed.
        os.system("sudo systemctl restart pcscd")
        logger.debug("pcscd restarted")
        return()
    elif 'Red' in dist_name:
        logger.info("Red MATCHED!")
        os.system("sudo yum install -y coolkey esc pam_pkcs11 pcsc-lite ccid opencryptoki libc.so.6 libresolv.so.2 librt.so.1 libpam.so.0")
        os.system("sudo rpm -i ./add-ons/smartcard/linux-x86_64/vassc-4.1.0-21853.x86_64.rpm") # VASSC rpm package install.
        os.system("sudo systemctl restart pcscd")
        logger.debug("pcscd restarted")
        return()
    elif 'Oracle' in dist_name:
        logger.info("Oracle MATCHED!")
        os.system("sudo yum install -y coolkey pam_pkcs11 pcsc-lite ccid opencryptoki libc.so.6 libresolv.so.2 librt.so.1 libpam.so.0")
        os.system("sudo rpm -i ./add-ons/smartcard/linux-x86_64/vassc-4.1.0-21853.x86_64.rpm") # VASSC rpm package install.
        os.system("sudo systemctl restart pcscd")
        logger.debug("pcscd restarted")
        return()
        
def check_vastool (): # ensure VAS/QAS is installed before allowing script to run.
    if os.path.exists('/opt/quest/bin/vastool'):
        return()
    else:
        logger.critical("VAS/QAS has not been installed. Please reinstall QAS and run the script again.")
        exit_script(0)
        
def ask_continue (): # Verify if user wants to configure QAS and has the option to enable debugging mode
    yes = set(['yes','y', 'ye', ''])
    no = set(['no','n'])
    debug = set(['debug','d'])
    global debug_flag
    print("Would you like to configure QAS now?")
    choice = raw_input.lower()
    if choice in yes:
        debug_flag is False
        return True
    elif choice in debug: 
        debug_flag = True
        if debug_flag is True:
            logger.info("***DEBUGGING ENABLED***")
    elif choice in no:
        exit_script(0)
    else:
        logger.info("Please respond with 'yes' or 'no'")
        ask_continue ()# Just ask if the user wishes to continue

def remove (): # This function is called only when debugging is enabled to ask if the user wants to unconfigure QAS files that are not unconfigured normally when removing QAS.
    global debug_flag
    if debug_flag is True:
        logger.debug("Debug Flag was successful")
        yes = set(['yes','y', 'ye', ''])
        no = set(['no','n'])
        logger.info("***Would you like to remove QAS? (yes/no)***")
        choice = raw_input.lower()
        if choice in yes:
            unconfigure('/etc/pam.d/login')
            unconfigure('/etc/pam.d/lightdm')
            unconfigure('/etc/pam.d/lightdm-greeter')
            unconfigure('/etc/pam.d/gdm-password')
            unconfigure('/etc/pam.d/mdm')
            unconfigure('/etc/pam.d/password-auth')
            unconfigure('/etc/pam.d/common-auth')
            if os.path.exists('./install.sh'):
                os.system("sudo ./install.sh remove")
                logger.info("***QAS has been removed and unconfigured***")
                exit_script(0)
            else:
                logger.error("***QAS has been unconfigured but not removed***")
                print(install_missing)
                exit_script(0)
        elif choice in no:
            return()
        else:
            print("Please respond with 'yes' or 'no'")
            remove()

def unconfigure (file_input): # This function performs the unconfiguration of the pam modules.
    if os.path.exists(file_input):
        logger.info('Unconfiguring ' + file_input) 
        for line in fileinput.input(file_input, inplace=True): 
            if not re.match(line_to_test, line): 
                sys.stdout.write (line) 

def installqas ():
    global debug_flag
    if debug_flag is True:
        logger.info("***Debugging is enabled***")
        yes = set(['yes','y', 'ye', ''])
        no = set(['no','n'])
        print("***Would you like to install QAS with debugging enabled? (yes/no)***")
        choice = raw_input.lower() # Ask for Debug install
        if choice in yes:
            if os.path.exists('./install.sh'):
                os.system("sudo ./install.sh -a")
            else:
                logger.error("***QAS cannot be installed***") # if it cannot find the QAS install.sh file 
                logger.info(install_missing)
        elif choice in no:
            return()
        else:
            print("Please respond with 'yes' or 'no'")
            installqas()
    else:
        if os.path.exists('./install.sh'):# install normally if no debugging flag
            os.system("sudo ./install.sh -a")
        else:
            logger.error("***QAS cannot be installed***")# Ask for Debug install
            logger.info(install_missing)

def backup_pam (file_to_backup): # Function to backup PAM files.
    global debug_flag
    if debug_flag is True:
        logger.debug('Backup pam for' + file_to_backup + ' waiting for path exist flag...')
    if os.path.exists(file_to_backup):
        if debug_flag is True:
            logger.debug('path exists...')
        movedir = script_path + "/pam_backups" # Original DIR
        if debug_flag is True:
            logger.debug('movedir variable created: ' + movedir)
        filename = os.path.basename(file_to_backup)
        if debug_flag is True:
            logger.debug('filename variable created: ' + filename)
        base, extension = os.path.splitext(filename)
        if debug_flag is True:
            logger.debug('base and extension variables created: ' + base + ' ' + extension)
        backup_file = movedir + '/' + base + '_backup'
        if debug_flag is True:
            logger.debug('backup_file variable created: ' + backup_file)
        if not os.path.exists(backup_file):
            if not os.path.exists(movedir):
                os.mkdir(movedir)
            shutil.copy2(file_to_backup, backup_file)
            logger.info(file_to_backup + ' was backed up to ' + backup_file)
        else:
            logger.info('Another backup was detected!')
            backup_file = movedir + '/' + base + '_backup_' + current_date + '_' + current_time
            if not os.path.exists(backup_file):
                if not os.path.exists(movedir):
                    os.mkdir(movedir)
                shutil.copy2(file_to_backup, backup_file)
                logger.info(file_to_backup + ' was backed up to ' + backup_file)
            else:
                logger.error('***Backups FAILED***')
                exit_script(0)
#
# END OF FUNCTIONS DEFINITION
#

#
# PROGRAM DEFINITION
#

check_os()
ask_continue()
installqas()
remove()
check_vastool()
backup_pam('/etc/pam.d/password-auth')# Backups for password-auth PAM file used in Cent/RHEL/OpenSuse
backup_pam('/etc/pam.d/login')# Backups for login PAM file used in all OS's
backup_pam('/etc/pam.d/gdm-password')# Backups for gdm-password PAM file used in Cent/RHEL/OpenSuse
backup_pam('/etc/pam.d/gdm-smartcard')# Backups for gdm-password PAM file used in Cent/RHEL/OpenSuse
backup_pam('/etc/pam.d/lightdm')# Backups for lightdm PAM file used in Ubuntu and Mint
backup_pam('/etc/pam.d/lightdm-greeter')# Backups for lightdm-greeter PAM file used in Ubuntu and Mint
backup_pam('/etc/pam.d/common-auth')# Backups for common-auth PAM file used in Ubuntu and Mint
backup_pam('/usr/share/mdm/defaults.conf')# Backups for mdm/defaults.conf PAM file used in Ubuntu and Mint
package_install()# install dependencies per OS
pkcs11_config()# configure the pkcs11 library depending on which one exists
vasd_config()
check_displaymanagers()
manipulate_pam_files('/etc/pam.d/password-auth', line_to_test) # Used in Cent/RHEL/OpenSuse for SSH and Lock-Screen (commented out until ssh issues are resolved) REMOVE THIS TO ENFORCE
manipulate_pam_files('/etc/pam.d/login', line_to_test) # Used on all Linux Systems
manipulate_pam_files('/etc/pam.d/lightdm', line_to_test) # Used with Ubuntu and Mint primarily
manipulate_pam_files('/etc/pam.d/mdm', line_to_test) # Used on Mint primarily # covered with common-auth
manipulate_pam_files('/etc/pam.d/lightdm-greeter', line_to_test) # Used with Ubuntu and Mint
manipulate_pam_files('/etc/pam.d/common-auth', line_to_test) # Used with Ubuntu and Mint SSH and Lock-Screen (commented out until ssh issues are resolved) REMOVE THIS TO ENFORCE
print(outro_text)
exit_script(0)

#
# END OF PROGRAM DEFINITION
#
