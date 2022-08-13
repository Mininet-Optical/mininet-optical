Directory name: cross-validation-tests

Description:

These files will execute a cross-validation test of the Mininet-Optical simulation system against that of the GNPy project [1].

IMPORTANT NOTE: THE MAIN SCRIPT, cross_validation.sh, MUST BE EXECUTED FROM INSIDE THIS FOLDER (i.e., cd cross-validation-tests).
Execution note: for the cross-validation tests to run correctly, the dynamic effects modeled from Mininet-Optical must be turned off (i.e, SRS, WDG).


In the parent folder you will find the following files (f) and directories (d):

(f) auto_tests.py*: Python script that will execute a couple of simulation tests using Mininet-Optical and will log the outputs for later analysis. See script description for more details.

(f) cross_val_test.py: Python script that will use the outputs from auto_tests.py, both from Mininet-Optical and GNPy, and will indicate whether the simulation systems are statistically similar. See script description for more details.

(f) cross_validation.sh: Bash script that will coordinate the execution of the simulation tests with Mininet-Optical and GNPy. See script description for more details.

(d) gnpy-files: this folder has two files: elements.py and eqpt_config.json; which are files from the GNPy project that we have edited to include customized logging functions and models**.

(d) gnpy-mytests: this folder has two files: auto_tests.py and helper_structs.py, the former is the analogous version of the auto_tests.py script described above, but for executing the simulation tests using GNPy; the latter is a Python file with helper structures for the execution of the simulation tests.

(d) patches: this folder has two files: elementspatch.patch and eqptpatch.path, the former is a patch to be applied to gnpy/core/elements.py in the main GNPy project and the latter the patch applied to tests/data/eqpt_config.json.

(f) README.md: this file you are reading right now.





* auto_tests.py can also be used to generate 14400 tests, see script description for more details.

** The files in this folder (gnpy-files) have been edited as follows:

File name: eqpt_config.json
Absolute path to file: oopt-gnpy/tests/data/eqpt_config.json
Description: contains the definitions of the equipment to be used (i.e., EDFAs, Fibre, etc.). In the file in this folder there are the manually added EDFAs for the different fibre spans used in the different topologies generated by auto_tests.py (lines 22 to 35).

File name: elements.py
Absolute path to file: oopt-gnpy/gnpy/core/elements.py
Description: contains the physical effect models of the network elements. A log_data function has been added to the Transceiver class in order to log the results.





[1] GNPy project. https://github.com/Telecominfraproject/oopt-gnpy