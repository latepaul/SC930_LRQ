SC930 LRQ Finder

A simple program to find Long Running Queries in SC930 trace files.

* Written in Python with a Tk GUI for maximum portability.  
* CLI mode for scripting.
* Parses multiple files (typically you have more than one log)

To Run:

    python <options> SC930_LRQ.py <filename> [<filename>...]


If no arguments are given, then a GUI is launched, otherwise it runs in command line mode and output is to the console.

Windows:

If you have python with tkinter installed you can run exactly as above. However there is an installer package (which comes with an embedded python interpreter etc) for windows. This will create a desktop shortcut and install to C:\Program Files\SC930_LRQ (by default).
The shortcut points to the gui version (SC930_LRQ_gui.exe) but there is a command line version (SC930_LRQ.exe) in the install directory also. Note the command line version will launch the GUI if no arguments are given, however if run from a shortcut it will also open a console window in the background.

Download:

The latest version of is at http://code.ingres.com/samples/python/SC930_LRQ. To run you need SC930_LRQ.py and constants.py. setup.py and SC930_LRQ_gui.py are required if you wish to build the Windows installer. Note, for this you also need the python package cx_Freeze.

ToDO list:

* formatting options
* sort an option or a prompt?
* search for qrytext
* 'short' query type ('insert', 'delete' etc)
* report format (header, filenames etc)
* add files to list (multiple locations)
* progress dialog if loading takes longer than x
