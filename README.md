SublimeCFAutoMock
=================

A light sublime plugin that automatically creates MXUnit unit tests from a coldfusion component (cftags only - cfscript to come).


Capabilities
============
  1. Create Setup and Teardown methods
  2. Create unit test shells (user has to finish them) with the following:
    1. Instance of ObjectToBeTested
    2. Mocked components from the variables scope and all their respective methods.
    3. Call to MethodToBeTested from ObjectToBeTested
    4. Dummy assertion call
  3. Create "Missing Arguments" unit tests 
  4. Create private method to get ObjectToBeTested


Install
=======
  CFAutoMock can now be installed via Package Control https://sublime.wbond.net/installation<br>
  Sublime > Preferences > Package Control > Install Package > Type CFAutoMock > Install > Enjoy!
  
Hwo to use
==========
  Open a CFC in Sublime 2 and press CTRL + K (win,linux) or Super + K (mac)
