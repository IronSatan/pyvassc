#!/usr/bin/env python
# Title:    Python QAS Install
# Author:   Matthew Williams
# Date:     2/22/2017
# Latest Update:   3/30/2017
#
# Description: Python Code to Install/Upgrade
# Quest Authentication Services Smart Card Configuration
#
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
file_to_test = 'nothing'
line_to_test = 'auth\s*\[success=ok default=die\]\s*pam_localuser.so'
dist_name = platform.linux_distribution()[0] # For Linux Distro's store the distribution name
dist_version = platform.linux_distribution()[1] # For Linux Distro's store the version number
smartcard_line = 'auth\s*requisite\s*pam_vas_smartcard\.so\s*echo_return'
mdm_line = '\AIncludeAll=true.*' # variable to detect MDM's include all = true
mdm_pam_line = '\Aauth\s*sufficient\s*pam_succeed_if.so\s*user\s*ingroup\s*nopasswdlogin'
script_path = os.path.abspath(os.path.dirname(sys.argv[0])) # Location script is ran from.
current_time = time.strftime("%H:%M:%S")
current_date = time.strftime("%d/%m/%Y")
log_file_path = 'QASscript_' + dist_name + dist_version + '_' + current_date + '_' + current_time + '.log'
debug_flag = False
intro_text = """
##################################################################
#Title:    Python QAS Install
# Author:   Matthew Williams
# Date:     2/22/2017
# Latest Update:   3/30/2017
#
# Description: Script to Install/Upgrade
# Quest Authentication Services Smart Card Configuration
#
# *** NOTE: This script must be ran from within the same folder as ***
# *** the install.sh file                                          ***
#
# This script is to be used on the following OS's:
# CentOS 7+
# Ubuntu 16.04+
# OpenSuse Leap 42.2+
# Mint 18.3+
# RHEL 7.3+
#
# If you are utilizing this script on any other OS you
# accept all risks and responsibilities for any data lost
# or misconfiguration that may occur.
"""
outro_text = """
# The script is has completed!
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
# FUNCTIONS DEFINITION
#
def check_exists(local_file_to_test, local_line_to_test): #Checks to see if auth    [success=ok default=die]    pam_localuser.so already exists in the file before making any changes.
    line_matched_check = False
    test_file = open(local_file_to_test, "r")
    for line in test_file:
        if line_matched_check is False :
            if re.match(local_line_to_test, line):
                print('Line exists already')
                line_matched_check = True
                return True

def check_os(): # Function to determine OS and whether or not to continue
    from sys import platform
    if platform == "linux" or platform == "linux2": # Linux...
        print (intro_text)
        print ("Your OS:"),
        print (dist_name),
        print (dist_version)
        return()
            # End Linux...
    elif platform == "darwin": #OS X...
        print ("Your OS is MAC")
        print ("This script is for Linux Machines only...")
        exit_script(0)
            # End OS X...
    elif platform == "win32": # Windows...
        print ("Your OS is Windows")
        print ("This script is for Linux Machines only...")
        exit_script(0)
            # End Windows...
    else:
        print ("I cannot determine your Operating System type...")
        exit_script(0)

def exit_script(exit_code): # Function to exit script, will build exception handling in the future
    print("Exiting script.")
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
                        print(local_file_to_test + " is already configured! Not making any changes...") # If it does exist make no changes.
                    else:
                        for line in fileinput.input(local_file_to_test, inplace=1):
                            print (line),
                            if re.match(smartcard_line, line):
                                print ('auth    [success=ok default=die]    pam_localuser.so') # Enforce via pam_local.so module
                        print ('Configuring' + local_file_to_test) # Configure Message. Inform user of which files are being configured
    if file_exists is True:
        if line_matched is False: # Debug to see if file is smartcard configured
            print (local_file_to_test + " check failed")
            print ("This means the files exists but is not configured for smartcard use.")
            print ("Please configure " + local_file_to_test + " for smartcards.")
            print ("Then restart this script.")
            exit_script(0)

def file_copy(src_path, dst_path, file):
    #if the destination path doesn't exist, create it
    file_dstpath = dst_path + "/" + file
    file_srcpath = src_path + "/" + file
    if not os.path.exists(dst_path):
        os.makedir(dst_path)
    try:
        shutil.copy2(file_srcpath, file_dstpath)
    except shutil.Error as e:
        print(file_dstpath + ' not copied. Error: %s' % e)
    except OSError as e:
        print(file_dstpath + ' not copied. Error: %s' % e)

def check_displaymanagers (): # Check for display managers.
    line_matched = False
    os.system("sudo /opt/quest/bin/vastool smartcard configure pam login") # All OS's need this file configured
    if os.path.exists('/etc/pam.d/common-auth'):
        print ('Configuring /etc/pam.d/common-auth')
        os.system("sudo /opt/quest/bin/vastool smartcard configure pam common-auth") # common-auth
    if os.path.exists('/etc/pam.d/common-auth-pc'):
        os.system("sudo /opt/quest/bin/vastool smartcard configure pam common-auth-pc")
    if os.path.exists('/etc/pam.d/common-auth-smartcard'):
        os.system("sudo /opt/quest/bin/vastool smartcard configure pam common-auth-smartcard")
    if os.path.exists('/etc/pam.d/password-auth'):
        print ('Configuring /etc/pam.d/password-auth')
        os.system("sudo /opt/quest/bin/vastool smartcard configure pam password-auth") # password-auth
    if os.path.exists('/etc/pam.d/mdm'): # MDM
        print ('MDM was detected, configuring...')
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
                print('MDM /usr/share/mdm/defaults.conf has been configured')
            print('You will need to restart the mdm service after this script in order to function properly.')
        else:
            print ('***/usr/share/mdm/defaults.conf was not detected. MDM was not configured correctly.***')
    if os.path.exists('/etc/pam.d/lightdm'): #LightDM
        print ('LightDM was detected, configuring...')
        os.system("sudo /opt/quest/bin/vastool smartcard configure pam lightdm")
        os.system("sudo /opt/quest/bin/vastool smartcard configure pam lightdm-greeter")
        if os.path.exists(script_path + '/10-ubuntu.conf'):
            file_copy(script_path, '/etc/lightdm/lightdm.conf.d', '10-ubuntu.conf')
        else:
            print ('***Script was not ran from original location. LightDM has not been completely configured.***')
    if os.path.exists('/etc/pam.d/gdm'): #GDM
        print ('GDM was detected, configuring...')
        os.system("sudo /opt/quest/bin/vastool smartcard configure pam gdm")
    if 'Red' not in dist_name:  
        if os.path.exists('/etc/pam.d/gdm-password'):
            print ('GDM was detected, configuring /etc/pam.d/gdm-password...')
            os.system("sudo /opt/quest/bin/vastool smartcard configure pam gdm-password")
    if os.path.exists('/etc/pam.d/sddm'): #SDDM - We don't currently have it configured but we would like to find a solution.
        print ('SDDM was detected, however, we have no current configuration for SDDM.')
        print ('Please use GDM or LightDM for your primary display manager.')
        os.system("sudo /opt/quest/bin/vastool smartcard configure pam sddm")
        
def vasd_config (): # Configure vasd with the vastool
    os.system("sudo /opt/quest/bin/vastool configure vas vasd username-attr-name samAccountName") # Configure vasd to allow samAccountName as the primary human-readable identifier
    os.system("sudo /opt/quest/bin/vastool configure vas vasd allow-upn-login True") # Configure vasd to allow UPN login for smartcards

def package_install (): # run package managers for each OS
    if 'CentOS' in dist_name:
        print ("CENTOS MATCHED!")
        os.system("sudo yum install -y coolkey opensc esc pam_pkcs11 pcsc-lite ccid opencryptoki libc.so.6 libresolv.so.2 librt.so.1 libpam.so.0")
        os.system("sudo rpm -i ./add-ons/smartcard/linux-x86_64/vassc-4.1.0-21853.x86_64.rpm") # VASSC rpm package install.
        os.system("sudo systemctl restart pcscd")
        os.system("sudo /opt/quest/bin/vastool smartcard configure pkcs11 lib /usr/lib64/opensc-pkcs11.so")
        return()
    elif 'Ubuntu' in dist_name:
        print ("Ubuntu MATCHED!")
        os.system("sudo apt-get install -y libpcsclite1 pcscd pcsc-tools pkg-config opensc coolkey libccid libacsccid1 ")
        os.system("sudo dpkg -iE ./add-ons/smartcard/linux-x86_64/vassc_4.1.0-21854_amd64.deb") # VASSC deb package install, will not install if already installed.
        os.system("sudo systemctl restart pcscd")
        os.system("sudo /opt/quest/bin/vastool smartcard configure pkcs11 lib /usr/lib64/opensc-pkcs11.so")
        return()
    elif 'SUSE' in dist_name:
        print ("SUSE MATCHED!")
        os.system("sudo zypper install -y opensc pam_pkcs11 pcsc-lite pcsc-ccid openCryptoki libc.so.6 libresolv.so.2 librt.so.1 libpam.so.0") #Zypper dependencies package installs
        os.system("sudo rpm -i ./add-ons/smartcard/linux-x86_64/vassc-4.1.0-21853.x86_64.rpm") # VASSC rpm package install.
        os.system("sudo systemctl restart pcscd")
        os.system("sudo /opt/quest/bin/vastool smartcard configure pkcs11 lib /usr/lib64/opensc-pkcs11.so")
        return()
    elif 'Mint' in dist_name:
        print ("Mint MATCHED!")
        os.system("sudo apt-get install -y libpcsclite1 pcscd pcsc-tools pkg-config opensc coolkey libccid libacsccid1 ")
        os.system("sudo dpkg -iE ./add-ons/smartcard/linux-x86_64/vassc_4.1.0-21854_amd64.deb") # VASSC deb package install, will not install if already installed.
        os.system("sudo systemctl restart pcscd")
        if os.path.exists('/usr/lib/x86_64-linux-gnu/pkcs11/opensc-pkcs11.so'):
            os.system("sudo /opt/quest/bin/vastool smartcard configure pkcs11 lib /usr/lib/x86_64-linux-gnu/pkcs11/opensc-pkcs11.so")
        if os.path.exists('/usr/lib64/opensc-pkcs11.so'):
            os.system("sudo /opt/quest/bin/vastool smartcard configure pkcs11 lib /usr/lib64/opensc-pkcs11.so")
        return()
    elif 'Red' in dist_name:
        print ("Red MATCHED!")
        os.system("sudo yum install -y coolkey esc pam_pkcs11 pcsc-lite ccid opencryptoki libc.so.6 libresolv.so.2 librt.so.1 libpam.so.0")
        os.system("sudo rpm -i ./add-ons/smartcard/linux-x86_64/vassc-4.1.0-21853.x86_64.rpm") # VASSC rpm package install.
        os.system("sudo systemctl restart pcscd")
        return()
        
def check_vastool (): # ensure VAS/QAS is installed before allowing script to run.
    if os.path.exists('/opt/quest/bin/vastool'):
        return()
    else:
        print ("VAS/QAS has not been installed. Please reinstall QAS and run the script again.")
        exit_script(0)
        
def ask_continue (): # Verify if user wants to configure QAS and has the option to enable debugging mode
    yes = set(['yes','y', 'ye', ''])
    no = set(['no','n'])
    debug = set(['debug','d'])
    global debug_flag
    print("Would you like to configure QAS now?")
    choice = raw_input().lower()
    if choice in yes:
        debug_flag is False
        return True
    elif choice in debug: 
        debug_flag = True
        if debug_flag is True:
            print("***DEBUGGING ENABLED***")
    elif choice in no:
        exit_script(0)
    else:
        print("Please respond with 'yes' or 'no'")
        ask_continue ()# Just ask if the user wishes to continue

def remove (): # This function is called only when debugging is enabled to ask if the user wants to unconfigure QAS files that are not unconfigured normally when removing QAS.
    global debug_flag
    if debug_flag is True:
        print("Debug Flag was successful")
        yes = set(['yes','y', 'ye', ''])
        no = set(['no','n'])
        print("***Would you like to remove QAS? (yes/no)***")
        choice = raw_input().lower()
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
                print("***QAS has been removed and unconfigured***")
            else:
                print("***QAS has been unconfigured but not removed***")
                print(install_missing)
            exit_script(0)
        elif choice in no:
            return()
        else:
            print("Please respond with 'yes' or 'no'")
            remove()

def unconfigure (file_input): # This function performs the unconfiguration of the pam modules.
    if os.path.exists(file_input):
        print ('Unconfiguring ' + file_input)
        for line in fileinput.input(file_input, inplace=True):
            if not re.match(line_to_test, line):
                sys.stdout.write (line)

def installqas ():
    global debug_flag
    if debug_flag is True:
        print("***Debugging is enabled***")
        yes = set(['yes','y', 'ye', ''])
        no = set(['no','n'])
        print("***Would you like to install QAS with debugging enabled? (yes/no)***")
        choice = raw_input().lower()
        if choice in yes:
            if os.path.exists('./install.sh'):
                os.system("sudo ./install.sh -a")
            else:
                print("***QAS cannot be installed***")
                print(install_missing)
        elif choice in no:
            return()
        else:
            print("Please respond with 'yes' or 'no'")
            installqas()
    else:
        if os.path.exists('./install.sh'):
            os.system("sudo ./install.sh -a")
        else:
            print("***QAS cannot be installed***")
            print(install_missing)

#
# END OF FUNCTIONS DEFINITION
#

#
# PROGRAM DEFINITION
#

#os.system("echo Testing from Python") # Sending command to bash from python
check_os()
ask_continue()
installqas()
remove()
check_vastool()
print (dist_name)
package_install()
print (script_path)
vasd_config()
check_displaymanagers()
#file_copy(script_path, '/etc/pam.d', 'test') # Debugging
#manipulate_pam_files('/etc/pam.d/test', line_to_test) # Test file for debugging purposes (commented out until debugging is needed)
manipulate_pam_files('/etc/pam.d/password-auth', line_to_test) # Used in Cent/RHEL/OpenSuse for SSH and Lock-Screen (commented out until ssh issues are resolved) REMOVE THIS TO ENFORCE
manipulate_pam_files('/etc/pam.d/login', line_to_test) # Used on all Linux Systems
manipulate_pam_files('/etc/pam.d/lightdm', line_to_test) # Used with Ubuntu and Mint primarily
manipulate_pam_files('/etc/pam.d/mdm', line_to_test) # Used on Mint primarily # covered with common-auth
manipulate_pam_files('/etc/pam.d/lightdm-greeter', line_to_test) # Used with Ubuntu and Mint
if 'Red' and 'SUSE' not in dist_name:
    manipulate_pam_files('/etc/pam.d/gdm-password', line_to_test) # Used in Cent/RHEL/OpenSuse with GDM
manipulate_pam_files('/etc/pam.d/common-auth', line_to_test) # Used with Ubuntu and Mint SSH and Lock-Screen (commented out until ssh issues are resolved) REMOVE THIS TO ENFORCE
print (outro_text)
exit_script(0)

#
# END OF PROGRAM DEFINITION
#