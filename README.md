# pyvassc
Python Script to Enforce Linux Machines to utilize SmartCards via QAS/VAS

This script has been created for the automatice configuration of QAS 4.1.0 with VAsSC
to require a smartcard to login on all QAS/Domain user accounts.

Local accounts should not be affected.

This script modifies the following PAM configuration files in /etc/pam.d/

password-auth
login
lightdm
mdm
lightdm-greeter
gdm-password
common-auth

Any other display manager can be configured to use the same method if the PAM changes
can be configured for it. *Most are caught by common-auth and password-auth*

Note, this will also prevent the user from using SSH from a domain account if your SSH
config just uses common-auth or password-auth.

The PAM line that provides this enforcement is:
auth    [success=ok default=die]    pam_localuser.so

This line just uses the pam_localuser.so module to verify if the user account is local
or not. If it is then it can continue along past the QAS modules. If the account is not
recognized as local the PAM stack will die and not allow the user in unless they auth
via the QAS smartcard module.
