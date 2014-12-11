__author__ = 'Paul Mason'

import sys
import os
from Tkinter import *
from ttk import Entry,Style
import tkFileDialog
import ScrolledText
import tkMessageBox
from pympler.asizeof import asizeof


SC930_QQRY = ["QRY","QUEL","REQUEL","REQUERY"]
SC930_OQRY = ["ABORT", "ABSAVE", "ADD-CURSORID", "AUTOCOMMIT", "BGNTRANS", "CLOSE",
              "COMMIT", "DELETE CURSOR", "ENDTRANS", "EXECUTE", "EXECUTE PROCEDURE", "FETCH", "PREPCOMMIT",
              "QCLOSE", "QFETCH", "RLSAVE", "ROLLBACK", "SVEPOINT", "UNKNOWN", "XA_COMM", "XA_END",
              "XA_PREP", "XA_RBCK", "XA_STRT", "XA_UNKNOWN"]
SC930_EQY = ["EQY"]
SC930_KEYW = ["TDESC", "COL", "QEP","PARM", "PARMEXEC"]
SLIDER_RANGES = [[0,0.5,0.05,0.01],
                 [0.5,2,0.1,0.1],
                 [2,10,1,1],
                 [10,30,2,1],
                 [30,100,5,1],
                 [100,500,25,1],
                 [500,1000,100,1],
                 [1000,3600,250,1]]


NANO_PER_SEC=1000000000
THRESHOLD = 0.01

dbmspid="<dbmspid>"
sessid = "<session>"

LRQ_sorted = LRQ_list = []
gui = False
sort = True

def ignore():
    pass

def EndQry(qtext,begin_ts,end_ts,nano_thresh):

    dur = GetTimestamp(end_ts) - GetTimestamp(begin_ts)
    if dur > nano_thresh:
        LRQ_list.append([qtext,begin_ts,end_ts,dur,dbmspid,sessid])
    return

def GetTimestamp(tstxt):
    t = tstxt.split('/')
    secs = int(t[0])
    nano = int(t[1])
    return ((secs * NANO_PER_SEC) + nano)

def FindLRQ(path,nano_thresh):
    global dbmspid, sessid, LRQ_list

    fpath = os.path.basename(path)
    sess_str = fpath[:5]
    if sess_str == "sess_":
        sess_parts = fpath.split("_")
        if len(sess_parts) == 3:
            dbmspid = sess_parts[1]
            sessid = sess_parts[2]

    start_found = False
    try:
        fh = open(path)
    except:
        if gui:
            tkMessageBox.showerror(title='Failed Opening file',
                                   message='Unable to open %s' % path)
        else:
            print "Unable to open '%s'" % path
        return

    qtext = ''
    begin_ts = 0
    for line in fh.readlines():
        words = line.split(":")
        rectype = words[0].rstrip('\n')

        if rectype in SC930_QQRY:
            start_found = True
            q = words[1].split('?')
            tstxt = q[0]
            qtext = q[1].rstrip('\n').lstrip()
            begin_ts = tstxt
        elif rectype in SC930_OQRY:
            start_found = True
            qtext = rectype
            begin_ts = words[1]
        elif rectype in SC930_EQY:
            end_ts = words[1]
            if start_found:
                EndQry(qtext,begin_ts,end_ts,nano_thresh)
        elif rectype in SC930_KEYW:
            ignore()
        else:
            qtext = qtext+'\n'+rectype

    fh.close()


def cli_main(argv=sys.argv):
    global LRQ_sorted, LRQ_list

    progname = os.path.basename(argv[0])
    print "This is the CLI dude!"
    for i in range(len(argv)):
        fullpath = os.path.normpath(argv[i])
        print "fullpath=",fullpath
        FindLRQ(fullpath, NANO_PER_SEC * THRESHOLD)
    if sort:
        LRQ_sorted = sorted(LRQ_list,key=lambda item: item[3], reverse=True)
        LRQ_list = []
    else:
        LRQ_sorted = LRQ_list

    for lrq in LRQ_sorted:
        qtext = lrq[0]
        begin_ts = lrq[1]
        end_ts = lrq[2]
        dur = lrq[3]
        dbmspid = lrq[4]
        sessid = lrq[5]
        print "Query:     ", qtext
        print "Begin:     ", begin_ts
        print "End:       ", end_ts
        print "Duration:   %020.9f secs" % (float (dur)/NANO_PER_SEC)
        print "DBMS PID:  ", dbmspid
        print "Session ID:", sessid

    print "Found %d queries that took longer than %9.4f seconds" % (len(LRQ_sorted),THRESHOLD)


class SC930Chooser(Frame):
    global LRQ_sorted, LRQ_list

    def __init__(self, root):
        Frame.__init__(self, root, border=5)
        self.parent=root

        self.parent.title("SC930 Long Running Query Finder")
        self.style = Style()
        self.style.theme_use("default")
        frame = Frame(self, relief=RAISED, borderwidth=1)
        frame.pack(fill=BOTH, expand=1)
        self.pack(fill=BOTH, expand=1)

        quitButton = Button(self, text="Quit", command=quit)
        quitButton.pack(side=RIGHT,padx=5,pady=5)
        LRQButton = Button(self, text="Find L.R.Q.s",command=self.FindLRQGo)
        LRQButton.pack(side=RIGHT, padx=5)
        InfoButton = Button(self,text="Info",command=self.display_info)
        InfoButton.pack(side=LEFT)

        self.ThreshSlider = Scale(frame,orient=HORIZONTAL,length=500,
                                  from_=0, to=10.0, resolution=1,
                                  tickinterval=1.0, command=self.scale_changed,
                                  showvalue=TRUE)
        self.ThreshSlider.grid(column=0,sticky="W")
        self.ThreshSlider.set(5.0)
        self.parent.bind('<Key>',self.scroll_key_left)
        self.max_slider_val = self.ThreshSlider.cget('to')
        lb =Label(frame,text="threshold:")
        lb.grid(row=0,column=1,sticky="E")

        vcmd = (self.parent.register(self.focus_left_thresh),'%P')
        self.threshentry = Entry(frame,width=5,validate='focusout',
                                 validatecommand=vcmd)
        self.threshentry.grid(row=0,column=2,sticky="W")
        self.threshentry.insert(0,'5.0')
        self.threshentry.bind('<Return>',self.enter_pressed)
        self.enter_pressed('5.0')
        lb2 = Label(frame,text="secs")
        lb2.grid(row=0,column=3,sticky="W")

        FileButton = Button(frame,text="SC930 Files...",command=self.get_files)
        FileButton.grid(row=1,column=0,sticky='W')
        self.filebox = ScrolledText.ScrolledText(frame,height=6)
        self.filebox.grid(row=2,column=0,columnspan=4)
        self.filelist = []

    def scroll_key_left(self,event):
        fw = self.parent.focus_get()
        if fw == self.threshentry or fw == self.filebox:
            return
        curr_tick = self.ThreshSlider.cget('tickinterval')
        curr_slideval =  self.ThreshSlider.get()
        if event.keysym == 'Left':
            new_slideval = curr_slideval - curr_tick
            if new_slideval <= 0:
                new_slideval = 0
            self.change_thresh(new_slideval)
        if event.keysym == 'Right':
            new_slideval = curr_slideval + curr_tick
            if new_slideval > 3600:
                new_slideval = 3600
            self.change_thresh(new_slideval)

    def enter_pressed(self,event):
        self.check_scale()
        self.change_thresh(self.threshentry.get())


    def check_scale(self):
        scaleval = self.ThreshSlider.get()
        if scaleval < (0.25 * self.max_slider_val):
            self.slider_rescale(scaleval)
        if scaleval == self.max_slider_val and scaleval < 3600:
            self.slider_rescale(scaleval)

    def focus_left_thresh(self,newtext_P):
        self.change_thresh(newtext_P)
        return newtext_P

    def scale_changed(self,value):
        self.slider_rescale(value)
        self.change_thresh_entry(value)

    def slider_rescale(self,value):
        new_tick = self.ThreshSlider.cget('tickinterval')
        Range_found = False
        for r in SLIDER_RANGES:
            if float(value) >= r[0] and float(value) < r[1] and not Range_found:
                self.max_slider_val = r[1]
                new_tick = r[2]
                new_res = r[3]
                Range_found = True

        if not Range_found:
            self.max_slider_val = r[1]
            new_tick = r[2]
            new_res = r[3]

        self.ThreshSlider.configure(to=self.max_slider_val,
                                    resolution=new_res,
                                    tickinterval=new_tick)

    def display_info(self):
        print "INFO:"
        print "  ThreshSlider:"
        print "    from:         %s" % self.ThreshSlider.cget('from')
        print "    to:           %s" % self.ThreshSlider.cget('to')
        print "    res:          %s" % self.ThreshSlider.cget('resolution')
        print "    tickinterval: %s" % self.ThreshSlider.cget('tickinterval')
        print " "
        print"   self.max_slider_val: %s" % self.max_slider_val
        print " "
        print "  threshentry:"
        print "    contents:     %s" % self.threshentry.get()


    def change_thresh_entry(self,value):
        self.threshentry.delete(0,'end')
        self.threshentry.insert(0,value)

    def change_thresh(self,new_val):
        '''
        change_thresh - changes the threshold value
        '''
        try:
            retval = float(new_val)
        except:
            retval = float(self.ThreshSlider.get())
        self.change_thresh_entry(retval)
        self.slider_rescale(retval)

        self.ThreshSlider.set(retval)
        self.ThreshSlider.cget('to')

    def get_files(self):
        selectedfiles = tkFileDialog.askopenfilename(
            parent=None, title='Select SC930 Session file',
            filetypes=[('SC930 session files', 'sess*'),
                                                ('All Files', '*')],
            multiple = True)
        if selectedfiles:
            self.filelist=list(selectedfiles)
            self.filebox.delete(1.0,'end')
            idx=1
            for file in selectedfiles:
                pos=str(idx)+'.0'
                self.filebox.insert(pos,os.path.normpath(file)+'\n')
                idx+=1
        return

    def FindLRQGo(self):
        global LRQ_sorted, LRQ_list

        if len(self.filelist) == 0:
            tkMessageBox.showerror(title='No SC930 Files',
                                   message='No SC930 Files have been selected!')
            return

        flt_thresh = float(self.threshentry.get())
        for file in self.filelist:
            FindLRQ(file,int(NANO_PER_SEC * flt_thresh))
        if len(LRQ_list) == 0:
            tkMessageBox.showinfo(title='No LRQs',
                                   message='No queries found running longer than the threshold!')
            return
        print "Pre-sort:"
        print " LRQ_list - [len,size] = [%d,%d]" % (len(LRQ_list),asizeof(LRQ_list))
        print " LRQ_sorted - [len,size] = [%d,%d]" % (len(LRQ_sorted),asizeof(LRQ_sorted))
        if sort:
            LRQ_sorted = sorted(LRQ_list,key=lambda item: item[3], reverse=True)
            LRQ_list = []
        else:
            LRQ_sorted = LRQ_list
        print "Post-sort:"
        print " LRQ_list - [len,size] = [%d,%d]" % (len(LRQ_list),asizeof(LRQ_list))
        print " LRQ_sorted - [len,size] = [%d,%d]" % (len(LRQ_sorted),asizeof(LRQ_sorted))

        output_win(self.parent)
        return

def output_win(root):
    output_win.qrynum = num_lrq = 0

    def write_to_file():
        pass

    def quit_out():
        global LRQ_list, LRQ_sorted

        LRQ_list = []
        LRQ_sorted =[]
        Owin.grab_release()
        Owin.destroy()

    def populate(qno):
        Owin.qrybox.delete(1.0,'end')
        Owin.begin_ts.delete(0,'end')
        Owin.end_ts.delete(0,'end')
        Owin.duration.delete(0,'end')
        Owin.dbms.delete(0,'end')
        Owin.session.delete(0,'end')
        Owin.qryno.delete(0,'end')
        Owin.qryno.insert(0,qno+1)
        Owin.qrybox.insert(1.0,LRQ_sorted[qno][0])
        Owin.begin_ts.insert(0,LRQ_sorted[qno][1])
        Owin.end_ts.insert(0,LRQ_sorted[qno][2])
        show_dur = "%18.9f" % (float(LRQ_sorted[qno][3]) /NANO_PER_SEC)
        Owin.duration.insert(0,show_dur)
        Owin.dbms.insert(0,LRQ_sorted[qno][4])
        Owin.session.insert(0,LRQ_sorted[qno][5])


    def Right():
        print "Right"

        if output_win.qrynum < num_lrq-1:
            output_win.qrynum += 1
            populate(output_win.qrynum)

    def Left():
        print "Left"
        if output_win.qrynum > 0:
            output_win.qrynum -= 1
            populate(output_win.qrynum)

    def First():
        print "First"
        if num_lrq > 0:
            output_win.qrynum = 0
            populate(output_win.qrynum)

    def Last():
        print "Last"
        if num_lrq > 0:
            output_win.qrynum = num_lrq-1
            populate(output_win.qrynum)

    Owin = Toplevel(root)
    Owin.style = Style()
    Owin.style.theme_use("default")

    l1 = Label(Owin, text="QryNo:")
    l1.grid(row=0,column=0,sticky=(W),padx=5)
    Owin.qryno = Entry(Owin,width=5,justify=RIGHT)
    Owin.qryno.grid(row=0,column=1,padx=5,sticky=(E))
    l2 = Label(Owin, text="Begin:")
    l2.grid(row=0,column=2,sticky=(W),padx=5)
    Owin.begin_ts = Entry(Owin,width=22,justify=RIGHT)
    Owin.begin_ts.grid(row=0,column=3,sticky=(E),padx=5)
    l3 = Label(Owin, text="Duration (ns):")
    l3.grid(row=1,column=0,sticky=(W),padx=5)
    Owin.duration = Entry(Owin,width=18,justify=RIGHT)
    Owin.duration.grid(row=1,column=1,padx=5,sticky=(E))
    l4 = Label(Owin, text="End:")
    l4.grid(row=1,column=2,sticky=(W),padx=5)
    Owin.end_ts = Entry(Owin,width=22,justify=RIGHT)
    Owin.end_ts.grid(row=1,column=3,sticky=(E),padx=5)
    l5 = Label(Owin, text="DBMS Pid:")
    l5.grid(row=2,column=0,sticky=(W),padx=5)
    Owin.dbms = Entry(Owin,width=10,justify=RIGHT)
    Owin.dbms.grid(row=2,column=1,padx=5,sticky=(E))
    l6 = Label(Owin, text="Session id:")
    l6.grid(row=2,column=2,sticky=(W),padx=5)
    Owin.session = Entry(Owin,width=10,justify=RIGHT)
    Owin.session.grid(row=2,column=3,padx=5,sticky=(E))
    Owin.qrybox = ScrolledText.ScrolledText(Owin,width=200,height=16)
    Owin.qrybox.grid(row=3,column=0,padx=5,columnspan=5)
    # Owin.qrybox.grid_rowconfigure(3,weight=1)
    # Owin.qrybox.grid_columnconfigure(0,weight=1)

    ButtFrame1 = Frame(Owin,relief=SUNKEN, borderwidth=1)
    ButtFrame1.grid(row=4,column=1,padx=5,columnspan=3)
    FirstButton = Button(ButtFrame1, text = "<<", command=First)
    FirstButton.grid(row=0,column=0,padx=15,sticky=(W))
    LeftButton = Button(ButtFrame1,text="<",command=Left)
    LeftButton.grid(row=0,column=1,padx=15,pady=5,sticky=(W))
    RightButton = Button(ButtFrame1, text=">",command=Right)
    RightButton.grid(row=0,column=2,padx=15,pady=5,sticky=(E))
    LastButton = Button(ButtFrame1, text = ">>", command=Last)
    LastButton.grid(row=0,column=3,padx=15,pady=5,sticky=(E))
    ButtFrame2 = Frame(Owin,relief=SUNKEN, borderwidth=1)
    ButtFrame2.grid(row=4,column=4,padx=5,sticky=(E))
    saveButton = Button(ButtFrame2, text="save to file", command=write_to_file)
    saveButton.grid(row=0,column=0,padx=5,pady=5)
    quitButton = Button(ButtFrame2, text="close", command=quit_out)
    quitButton.grid(row=0,column=1,padx=5,pady=5)
    Owin.columnconfigure(0,weight=1)
    Owin.columnconfigure(1,weight=1)
    Owin.columnconfigure(2,weight=1)
    Owin.columnconfigure(3,weight=1)
    Owin.rowconfigure(0,weight=0)
    Owin.rowconfigure(1,weight=0)
    Owin.rowconfigure(2,weight=0)
    Owin.rowconfigure(3,weight=3)
    Owin.rowconfigure(4,weight=1)
    num_lrq = len(LRQ_sorted)

    title = "Long-Running Queries: 1/"+"%d" % num_lrq
    Owin.title(title)
    Owin.geometry('700x400')
    Owin.grab_set()
    Owin.protocol("WM_DELETE_WINDOW",quit_out)
    qrynum = num_lrq-1
    if num_lrq > 0:
        qrynum = 0
        populate(qrynum)

def gui_main():
    global gui

    gui = True
    root = Tk()
    root.geometry("700x250+300+300")
    SC930Chooser(root)
    root.mainloop()
    return 0

if __name__ == '__main__':
    if len(sys.argv) > 1:
        sys.exit(cli_main())
    sys.exit(gui_main())

