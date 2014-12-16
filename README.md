SC930 LRQ Finder

A simple program to find Long Running Queries in SC930 trace files.

* Written in Python with a Tk GUI for maximum portability.  
* CLI mode for scripting.
* Parses multiple files (typically you have more than one log)

ToDO list:

* formatting options
* sort an option or a prompt?
* CLI flags
* search for qrytext
* 'short' query type ('insert', 'delete' etc)
* report format (header, filenames etc)
* add files to list (multiple locations)
* progress dialog if loading takes longer than x
* ~~DBMS Pid & Session ID from filename~~
* ~~log text area~~ 
* ~~or 'save to file'~~
* ~~file-card version~~
* ~~sort - largest first?~~
* ~initial screen resizable~
* ~out of memory protection?~
* ~jump to qryno~
* ~~protect display only fields~~
* ~~non-editable fields as labels not entry fields~~