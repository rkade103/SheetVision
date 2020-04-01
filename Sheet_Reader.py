import tkinter as tk
from tkinter.ttk import *
import sys
import queue
import os

from threading import Thread
from threading import Event

from tkinter import filedialog
from tkinter import messagebox
from AnalysisComponent import AnalysisComponent
from ExcelWriter import ExcelWriter
import ErrorDetection

import traceback
from PIL import Image
from pygments import highlight
from pygments.lexers import PythonLexer
from pygments.formatters import HtmlFormatter

class Sheet_Reader(tk.Frame):

    def __init__(self, master=None):
        tk.Frame.__init__(self, master)
        self.master = master
        self.master.protocol("WM_DELETE_WINDOW", self.client_exit)
        self.picEntry = None
        self.midiEntry = None
        self.open_main_window()
        self.create_window()
        self.is_done = False
        self.thread = None

    def centreWindow(self):
        w = 500
        h = 300
        sw = self.master.winfo_screenwidth()
        sh = self.master.winfo_screenheight()
        x = (sw - w)/2
        y = (sh - h)/2
        self.master.geometry('%dx%d+%d+%d' % (w, h, x, y))

    def open_main_window(self):

        #Set the title of the window
        self.master.title("Sheet Reader")
        
        #Fill the space of the root window.
        self.pack(fill=tk.BOTH, expand=1)

        #Create a quit button and place it.
        self.quitButton = tk.Button(self, text="Quit", command=self.client_exit)
        self.quitButton.place(x=400, y=140)

        #Create a generate button and place it.
        self.generateButton = tk.Button(self, text="Generate", command=self.generate_sheet)
        self.generateButton.place(x=175, y=140)

        #Create an open folder button, place it and disable it.
        self.openFolderButton = tk.Button(self, text="Open Folder", command=self.open_folder)
        self.openFolderButton.place(x=280, y = 230)
        self.openFolderButton.config(state="disabled")

    def client_exit(self):
        if self.thread:
            self.thread.stop()
        sys.exit()

    def create_window(self):
        tk.Label(self, wraplength=600, text="Welcome to the SheetReader! This tool is designed to generate an excerpt sheet that" + 
                                " will be used by the Midi Analyzer. Supply an image of the line as well as a model file" +
                                " that represents a perfect run-through, and this tool will generate the excerpt sheet for you!").grid(row=0, columnspan=3)

        
        tk.Label(self, text="Excerpt Picture:").grid(row=4, column=0)
        self.picEntry = tk.Entry(self, width=70)
        self.picEntry.grid(row=4, column=1)
        self.picButton = tk.Button(self, text="Browse", command=self.browse_for_picture)
        self.picButton.grid(row=4, column=2)

        tk.Label(self, text="Model File:").grid(row=5)
        self.midiEntry = tk.Entry(self, width=70)
        self.midiEntry.grid(row=5, column=1)
        self.midiButton = tk.Button(self, text="Browse", command=self.browse_for_midi)
        self.midiButton.grid(row=5, column=2)

        tk.Label(self, text="Destination Folder:").grid(row=6)
        self.destEntry = tk.Entry(self, width=70)
        self.destEntry.grid(row=6, column=1)
        self.destButton = tk.Button(self, text="Browse", command=self.browse_for_folder)
        self.destButton.grid(row=6, column=2)

        self.progress_bar = Progressbar(self, orient=tk.HORIZONTAL, length=400, mode='determinate')

        self.progress_label = tk.Label(self)

    def browse_for_picture(self):
        file_path = filedialog.askopenfilename(title="Choose an image file",
                                               filetypes=[('image files', ('.png', '.jpg', '.bmp'))])
        if file_path:
            self.picEntry.delete(0, 'end')
            self.picEntry.insert(0, file_path)

    def browse_for_midi(self):
       file_path = filedialog.askopenfilename(title="Choose a midi file",
                                               filetypes=[('midi files', (".MID",".MIDI", ".mid", "midi"))])
       if file_path:
           self.midiEntry.delete(0, 'end')
           self.midiEntry.insert(0, file_path)

    def browse_for_folder(self):
        folder_path = filedialog.askdirectory()

        if folder_path:
            self.destEntry.delete(0, 'end')
            self.destEntry.insert(0, folder_path)

    def open_folder(self):
        if not (self.check_path_to_folder()):
            return;
        path = os.path.realpath(self.destEntry.get())
        os.startfile(path)

    def generate_sheet(self):
        if not self.check_path_to_pic():
            return;
        if not self.check_path_to_midi():
            return;
        if not self.check_path_to_folder():
            return;
        if not self.check_excerpt_sheet():
            return;
        self.generateButton.config(state="disabled")
        path_to_pic = self.picEntry.get()
        path_to_midi = self.midiEntry.get()
        dest = self.destEntry.get()
        self.progress_label.place(x=100, y=175)
        self.progress_bar.place(x=100, y=200)
        self.queue = queue.Queue()
        self.thread = ThreadedTask(self.queue, path_to_pic, path_to_midi, dest)
        self.thread.start()
        self.master.after(100, self.periodiccall)
        self.progress_bar.grid_forget()

    def check_path_to_pic(self):
        path_to_pic = self.picEntry.get()
        if not path_to_pic:
            messagebox.showwarning("No picture given", "No picture path was given. Please give a path to an image of an excerpt sheet.")
            return False
        if not os.path.exists(path_to_pic):
            messagebox.showwarning("Invalid picture path", "The path given for the picture file is invalid. Please enter a different path.")
            return False
        im = Image.open(path_to_pic)
        width, height = im.size
        if width <= 59 or height <= 170:
            messagebox.showwarning("Invalid picture size", "The picture given is too small for analysis. Make sure the width is over 59 pixels, and the height is over 170 pixels.")
            return False
        message = ErrorDetection.check_if_only_white(path_to_pic)
        if message != None:
            messagebox.showwarning("Invalid Picture", message)
            return False
        return True

    def check_path_to_midi(self):
        path_to_midi = self.midiEntry.get()
        if not path_to_midi:
            messagebox.showwarning("No midi file given", "No midi file path was given. Please give a path to a midi file representing a playthrough with no errors.")
            return False
        if not os.path.exists(path_to_midi):
            messagebox.showwarning("Invalid midi file path", "The path given for the midi file is invalid. Please enter a different path.")
            return False
        return True

    def check_path_to_folder(self):
        dest_path = self.destEntry.get()
        if not dest_path:
            messagebox.showwarning("No destination folder given", "No destination folder was given. Please give a destination folder to save the output to.")
            return False
        if not os.path.exists(dest_path):
            messagebox.showwarning("Invalid destination folder", "The destination folder was invalid. Please enter a different folder path.")
            return False
        return True

    def check_excerpt_sheet(self):
        excerpt_sheet_path = self.destEntry.get()+"/excerptSheet.xlsx"
        if os.path.exists(excerpt_sheet_path):
            try:
                file = open(excerpt_sheet_path, "r+")
                file.close()
                return True
            except IOError:
                messagebox.showwarning("Excerpt File Open", "The output excerptSheet.xlsx file is open at the destination folder. " + 
                                                            "Please close the file or select a different destination folder.")
                return False
        return True #If the file doesn't exist, there's no way it could be open.
    
    def check_for_slurs_and_ties(self):
        excerpt_sheet_path = self.destEntry.get()+"/excerptSheet.xlsx"
        writer = ExcelWriter(self.destEntry.get(), self.midiEntry.get())
        if writer.check_for_ties_and_slurs():
            messagebox.showwarning("Inconsistent note count", "The number of notes detected in the sheet and the number\n" + 
                                                            "of notes in the model file do not match. Are there any\n" + 
                                                            "slurs or ties in the excerpt? If so, make sure to remove\n" +
                                                            "the notes that should not be played from the excerptSheet\n")
            return False
        return True

    def run_analysis_component(self, path_to_pic, path_to_midi, dest_path):
        analysis_component = AnalysisComponent()
        return analysis_component.run(path_to_pic, path_to_midi, dest_path, self.progress_bar)
        
    def periodiccall(self):
        self.process_queue()
        if self.thread.is_alive():
            self.after(100, self.periodiccall)
        else:
            self.generateButton.config(state="active")
            self.openFolderButton.config(state="active")
            self.check_for_slurs_and_ties()
            self.stacktraces();

    def process_queue(self):
        try:
            msg = self.queue.get_nowait()
            if(msg.split("|")[0] == "ERROR"):
                return False;
            else:
                percentage = int(msg.split("|")[0])
                message = msg.split("|")[1]
                self.progress_label['text'] = message
                self.progress_bar['value'] = percentage
                if percentage >= 100:
                    return True
        except queue.Empty:
            self.master.after(100, self.process_queue)

    def stacktraces(self):
        code = []
        for threadId, stack in sys._current_frames().items():
            code.append("\n# ThreadID: %s" % threadId)
            for filename, lineno, name, line in traceback.extract_stack(stack):
                code.append('File: "%s", line %d, in %s' % (filename, lineno, name))
                if line:
                    code.append("  %s" % (line.strip()))

        highlighted = highlight("\n".join(code), PythonLexer(), HtmlFormatter(
          full=False,
          # style="native",
          noclasses=True))
        print(highlighted)
        return highlighted

class ThreadedTask(Thread):
    def __init__(self, queue, pic_path, midi_path, destination_folder):
        Thread.__init__(self)
        self.queue = queue
        self.pic_path = pic_path
        self.midi_path = midi_path
        self.destination_folder = destination_folder
        self.analysis_component = AnalysisComponent(self.pic_path, self.midi_path, self.destination_folder, self.queue)
        
    def run(self):
        self.analysis_component.run(self.pic_path, self.midi_path, self.destination_folder)

    def stop(self):
        self.analysis_component.stop()

root = tk.Tk()
root.geometry("600x260")
root.resizable(width=False, height=False)
rows = 0
cols = 0
while (rows < 4):
    root.rowconfigure(rows, weight=1)
    #root.columnconfigure(rows, weight=1)
    rows += 1
while (cols < 3):
    root.columnconfigure(cols, minsize=50)
    root.grid_columnconfigure(cols, weight=1)
    cols += 1
app = Sheet_Reader(root)
app.pack_propagate(0)
root.tk.call('wm', 'iconphoto', root._w, tk.PhotoImage(file=r'piano lab icon.gif'))
root.mainloop()
input("Press any key to continue...")

