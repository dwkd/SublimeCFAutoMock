SublimeCFAutoMock
=================

A light sublime plugin that automatically creates MXUnit unit tests from a coldfusion component.


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
