__author__ = 'Paul Mason'


import sys
import os
from Tkinter import *
from ttk import Entry,Style
import tkFileDialog
import ScrolledText
import tkMessageBox
import constants
import argparse

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
DEF_THRESH = 5.0
flt_thresh = DEF_THRESH

dbmspid="<dbmspid>"
sessid = "<session>"

LRQ_sorted = LRQ_list = []
gui = False

def ignore():
    pass

def EndQry(qtext,begin_ts,end_ts,nano_thresh):
    dur = GetTimestamp(end_ts) - GetTimestamp(begin_ts)
    if dur > nano_thresh:
        try:
            LRQ_list.append([qtext,begin_ts,end_ts,dur,dbmspid,sessid])
        except:
            if gui:
                tkMessageBox.showerror(title='Failed to expand list',
                                       message='Failed to add an item to the LRQ list, possibly out of memory, try a higher threshold or fewer, smaller trace files' )
            else:
                print 'Failed to add an item to the LRQ list, possibly out of memory, try a higher threshold or fewer, smaller trace files'
            return False
    return True

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
        return 0

    num_qrys = 0
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
                if not EndQry(qtext,begin_ts,end_ts,nano_thresh):
                    fh.close()
                    return num_qrys
                else:
                    start_found = False
                    num_qrys += 1

        elif rectype in SC930_KEYW:
            ignore()
        else:
            qtext = qtext+'\n'+rectype

    fh.close()
    return num_qrys


def cli_main(argv=sys.argv):
    global LRQ_sorted, LRQ_list, options

    progname = os.path.basename(argv[0]).split('.')[0]

    parser = argparse.ArgumentParser(usage="%s [-sr] [-t time] [file(s)]" % progname,
                                     version="%s %s" % (progname,constants.SC930_LRQ_VER))
    parser.add_argument("-s","--sort",action="store_true",
                      dest="sort", default=True,help="sort results (longest to shortest)")
    parser.add_argument("-r",action="store_true",
                      dest="revsort", default=False,help="reverse sort (shortest to longest)")
    parser.add_argument("-t","--threshold",
                      dest="thresh",default=DEF_THRESH,type=float,help="threshold time, in seconds")
    parser.add_argument("files",default=[],nargs="*")

    options = parser.parse_args()

    if options.revsort:
        options.sort = True

    if len(options.files) == 0:
        print "No SC930 files given"
        return

    for file in options.files:
        FindLRQ(file, NANO_PER_SEC * options.thresh)

    if options.sort:
        try:
            if options.revsort:
                LRQ_sorted = sorted(LRQ_list,key=lambda item: item[3], reverse=False)
            else:
                LRQ_sorted = sorted(LRQ_list,key=lambda item: item[3], reverse=True)
            LRQ_list = []
        except:
            print 'Failed to sort LRQ list - possibly out of memory, try a higher threshold or fewer, smaller trace files'
            print '(results will not be sorted)'
    else:
        LRQ_sorted = LRQ_list

    for lrq in LRQ_sorted:
        qtext = lrq[0]
        begin_ts = lrq[1]
        end_ts = lrq[2]
        dur = lrq[3]
        dbmspid = lrq[4]
        sessid = lrq[5]
        print "\nQuery:     ", qtext
        print "Begin:     ", begin_ts
        print "End:       ", end_ts
        print "Duration:   %020.9f secs" % (float (dur)/NANO_PER_SEC)
        print "DBMS PID:  ", dbmspid
        print "Session ID:", sessid

    print "\nFound %d queries that took longer than %9.4f seconds" % (len(LRQ_sorted),options.thresh)


class SC930Chooser(Frame):
    global LRQ_sorted, LRQ_list

    def __init__(self, root):
        Frame.__init__(self, root, border=5)
        self.parent=root

        self.parent.title("SC930 Long Running Query Finder")
        self.style = Style()
        self.style.theme_use("default")
        frame = Frame(self, relief=RAISED, borderwidth=1)
        frame.grid(row=0,column=0,columnspan=4,padx=5,pady=5)

        self.ThreshSlider = Scale(frame,orient=HORIZONTAL,length=450,
                                  from_=0, to=10.0, resolution=1,
                                  tickinterval=1.0, command=self.scale_changed,
                                  showvalue=TRUE)
        self.ThreshSlider.grid(column=0,sticky="W")
        self.ThreshSlider.set(5.0)
        self.parent.bind('<Key>',self.scroll_key_left)
        self.max_slider_val = self.ThreshSlider.cget('to')
        lb =Label(frame,text="Queries longer than:")
        lb.grid(row=0,column=1,sticky="E",padx=5,pady=5)

        vcmd = (self.parent.register(self.focus_left_thresh),'%P')
        self.threshentry = Entry(frame,width=5,validate='focusout',
                                 validatecommand=vcmd)
        self.threshentry.grid(row=0,column=2,sticky="W",padx=5,pady=5)
        self.threshentry.insert(0,'5.0')
        self.threshentry.bind('<Return>',self.enter_pressed)
        self.enter_pressed('5.0')
        lb2 = Label(frame,text="secs")
        lb2.grid(row=0,column=3,sticky="W",padx=5,pady=5)

        FileButton = Button(frame,text="SC930 Files...",command=self.get_files)
        FileButton.grid(row=1,column=0,sticky='W',padx=5,pady=5)
        self.filebox = ScrolledText.ScrolledText(frame,height=50,width=200)
        self.filebox.grid(row=2,column=0,columnspan=4,padx=5,pady=5)
        self.filelist = []

        quitButton = Button(self, text="Quit", command=sys.exit)
        quitButton.grid(row=1,column=3,padx=5,pady=5)
        LRQButton = Button(self, text="Find L.R.Q.s",command=self.FindLRQGo)
        LRQButton.grid(row=1,column=2, padx=5)
        InfoButton = Button(self,text="Info",command=self.display_info)
        InfoButton.grid(column=0,row=1,sticky=(W))
        frame.columnconfigure(3,weight=1)
        frame.rowconfigure(2,weight=1)
        self.rowconfigure(0,weight=1)
        self.columnconfigure(0,weight=1)
        self.pack()
        self.parent.minsize(675,250)

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
        msg='SC930 Long-Running-Query Finder'
        msg = msg + '\n\nby Paul Mason'
        msg = msg + '\n (c) Actian Corp 2014'
        msg = msg + '\nSee %s for latest version' % constants.SC930_LRQ_LINK
        msg = msg + '\nversion %s' % constants.SC930_LRQ_VER
        tkMessageBox.showinfo(title='SC930 LRQ Finder',
                                   message=msg)


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
        global LRQ_sorted, LRQ_list, flt_thresh

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
        if sort:
            LRQ_sorted = sorted(LRQ_list,key=lambda item: item[3], reverse=True)
            LRQ_list = []
        else:
            LRQ_sorted = LRQ_list

        output_win(self.parent)
        return

def output_win(root):
    output_win.qrynum = output_win.num_lrq = 0

    def write_to_file():
        outputfile = tkFileDialog.asksaveasfilename(
            parent=None, title='Select Output File',
            initialfile = 'sc930lrq.txt',
            filetypes=[('Text File', '*.txt'),
                                                ('All Files', '*')])
        try:
            of = open(outputfile,"w")
        except:
            if gui:
                tkMessageBox.showerror(title='Failed Opening file',
                                       message='Unable to open %s' % outputfile)
            else:
                print "Unable to open '%s'" % outputfile
            return

        for record in LRQ_sorted:
            of.write("Query:      %s\n" % record[0])
            of.write("Begin:      %s\n" % record[1])
            of.write("End:        %s\n" % record[2])
            of.write("Duration:   %020.9f secs\n" % (float(record[3])/NANO_PER_SEC))
            of.write("DBMS PID:   %s\n" % record[4])
            of.write("Session ID: %s\n\n" % record[5])

        of.write("Found %d queries that took longer than %9.4f seconds\n" % (len(LRQ_sorted),THRESHOLD))

        of.close()

    def quit_out():
        global LRQ_list, LRQ_sorted

        LRQ_list = []
        LRQ_sorted =[]
        Owin.grab_release()
        Owin.destroy()

    def populate(qno):
        global flt_thresh

        title = "Long-Running Queries ( > %6.2fs): %d/%d" % (flt_thresh,qno+1,output_win.num_lrq)
        Owin.title(title)
        Owin.qrybox.configure(state='normal')
        Owin.qrybox.delete(1.0,'end')
        Owin.qrybox.insert(1.0,LRQ_sorted[qno][0])
        Owin.qrybox.configure(state='disabled')
        Owin.qryno.delete(0,'end')
        Owin.qryno.insert(0,qno+1)
        txt = "%s" % LRQ_sorted[qno][1]
        Owin.begin_ts.configure(text=txt)
        txt = "%s" % LRQ_sorted[qno][2]
        Owin.end_ts.configure(text=txt)
        txt = "%18.9f" % (float(LRQ_sorted[qno][3]) /NANO_PER_SEC)
        Owin.duration.configure(text=txt)
        txt = "%s" % LRQ_sorted[qno][4]
        Owin.dbms.configure(text=txt)
        txt = "%s" % LRQ_sorted[qno][5]
        Owin.session.configure(text=txt)


    def Right():
        if output_win.qrynum < output_win.num_lrq-1:
            output_win.qrynum += 1
            populate(output_win.qrynum)

    def Left():
        if output_win.qrynum > 0:
            output_win.qrynum -= 1
            populate(output_win.qrynum)

    def First():
        if output_win.num_lrq > 0:
            output_win.qrynum = 0
            populate(output_win.qrynum)

    def Last():
        if output_win.num_lrq > 0:
            output_win.qrynum = output_win.num_lrq-1
            populate(output_win.qrynum)

    def focus_left_qryno(newtext_P):
        jump_to_qry()
        return newtext_P

    def enter_pressed(event):
        jump_to_qry()

    def jump_to_qry():
        entered_no = int(Owin.qryno.get())
        if entered_no > 0 and entered_no <= output_win.num_lrq:
            output_win.qrynum = entered_no - 1;
        populate(output_win.qrynum)

    Owin = Toplevel(root)
    Owin.style = Style()
    Owin.style.theme_use("default")

    l1 = Label(Owin, text="QryNo:")
    l1.grid(row=0,column=0,sticky=(W),padx=5,pady=5)
    vcmd = (Owin.register(focus_left_qryno),'%P')
    Owin.qryno = Entry(Owin,width=8,justify=RIGHT, validate='focusout',validatecommand=vcmd)
    Owin.qryno.grid(row=0,column=1,padx=5,pady=5,sticky=(E))
    Owin.qryno.bind('<Return>',enter_pressed)
    l2 = Label(Owin, text="Begin:")
    l2.grid(row=0,column=2,sticky=(W),padx=5)
    Owin.begin_ts = Label(Owin, text="000000/000000", bd=3, relief=RIDGE)
    Owin.begin_ts.grid(row=0,column=3,sticky=(E),pady=5,padx=5)
    l3 = Label(Owin, text="Duration (s):")
    l3.grid(row=1,column=0,sticky=(W),padx=5)
    Owin.duration = Label(Owin, text="0.0", bd=3, relief=RIDGE)
    Owin.duration.grid(row=1,column=1,padx=5,sticky=(E))
    l4 = Label(Owin, text="End:")
    l4.grid(row=1,column=2,sticky=(W),padx=5)
    Owin.end_ts = Label(Owin, text="000000/000000", bd=3, relief=RIDGE)
    Owin.end_ts.grid(row=1,column=3,sticky=(E),padx=5)
    l5 = Label(Owin, text="DBMS Pid:")
    l5.grid(row=2,column=0,sticky=(W),padx=5,pady=5)
    Owin.dbms = Label(Owin, text="dbms", bd=3, relief=RIDGE)
    Owin.dbms.grid(row=2,column=1,padx=5,sticky=(E))
    l6 = Label(Owin, text="Session id:")
    l6.grid(row=2,column=2,sticky=(W),padx=5,pady=5)
    Owin.session = Label(Owin, text="session", bd=3, relief=RIDGE)
    Owin.session.grid(row=2,column=3,padx=5,sticky=(E))
    Owin.qrybox = ScrolledText.ScrolledText(Owin,width=250,height=50)
    Owin.qrybox.grid(row=3,column=0,padx=5,columnspan=5)
    Owin.qrybox.configure(state='disabled')

    ButtFrame1 = Frame(Owin,relief=SUNKEN, borderwidth=1)
    ButtFrame1.grid(row=4,column=1,padx=5,pady=5,columnspan=3)
    FirstButton = Button(ButtFrame1, text = "<<", command=First)
    FirstButton.grid(row=0,column=0,padx=5,pady=5)
    LeftButton = Button(ButtFrame1,text="<",command=Left)
    LeftButton.grid(row=0,column=1,padx=5,pady=5)
    RightButton = Button(ButtFrame1, text=">",command=Right)
    RightButton.grid(row=0,column=2,padx=5,pady=5)
    LastButton = Button(ButtFrame1, text = ">>", command=Last)
    LastButton.grid(row=0,column=3,padx=5,pady=5)
    ButtFrame2 = Frame(Owin,relief=SUNKEN, borderwidth=1)
    ButtFrame2.grid(row=4,column=4,padx=5,pady=5,sticky=(E))
    saveButton = Button(ButtFrame2, text="save to file", command=write_to_file)
    saveButton.grid(row=0,column=0,padx=5,pady=5)
    quitButton = Button(ButtFrame2, text="close", command=quit_out)
    quitButton.grid(row=0,column=1,padx=5,pady=5)
    Owin.columnconfigure(0,weight=0)
    Owin.columnconfigure(1,weight=0)
    Owin.columnconfigure(2,weight=0)
    Owin.columnconfigure(3,weight=0)
    Owin.columnconfigure(4,weight=1)
    Owin.rowconfigure(0,weight=0)
    Owin.rowconfigure(1,weight=0)
    Owin.rowconfigure(2,weight=0)
    Owin.rowconfigure(3,weight=1)
    Owin.rowconfigure(4,weight=0)
    Owin.minsize(660,175)

    output_win.num_lrq = len(LRQ_sorted)

    title = "Long-Running Queries: 1/"+"%d" % output_win.num_lrq
    Owin.title(title)
    Owin.geometry('700x400')
    Owin.grab_set()
    Owin.protocol("WM_DELETE_WINDOW",quit_out)
    if output_win.num_lrq > 0:
        populate(0)

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