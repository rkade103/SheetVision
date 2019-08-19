import tkinter as tk
from tkinter.ttk import *
import sys
import queue

from threading import Thread

from tkinter import filedialog
from AnalysisComponent import AnalysisComponent

class Sheet_Reader(tk.Frame):

    def __init__(self, master=None):
        tk.Frame.__init__(self, master)
        self.master = master
        self.picEntry = None
        self.midiEntry = None
        self.open_main_window()
        self.create_window()
        self.is_done = False
        #self.centreWindow()

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

    def client_exit(self):
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
       file_path = filedialog.askopenfilename(title="Choose an image file",
                                               filetypes=[('midi files', (".MID",".MIDI", ".mid", "midi"))])
       if file_path:
           self.midiEntry.delete(0, 'end')
           self.midiEntry.insert(0, file_path)

    def browse_for_folder(self):
        folder_path = filedialog.askdirectory()

        if folder_path:
            self.destEntry.delete(0, 'end')
            self.destEntry.insert(0, folder_path)

    def generate_sheet(self):
        self.generateButton.config(state="disabled")
        path_to_pic = self.picEntry.get()
        dest = self.destEntry.get()
        self.progress_label.place(x=100, y=175)
        self.progress_bar.place(x=100, y=200)
        self.queue = queue.Queue()
        self.thread = ThreadedTask(self.queue, path_to_pic, dest)
        self.thread.start()
        self.master.after(100, self.periodiccall)
        self.progress_bar.grid_forget()

    def run_analysis_component(self, path_to_pic, dest_path):
        analysis_component = AnalysisComponent()
        return analysis_component.run(path_to_pic, dest_path, self.progress_bar)
        
    def periodiccall(self):
        self.process_queue()
        if self.thread.is_alive():
            self.after(100, self.periodiccall)
        else:
            self.generateButton.config(state="active")

    def process_queue(self):
        try:
            msg = self.queue.get_nowait()
            percentage = int(msg.split("|")[0])
            message = msg.split("|")[1]
            self.progress_label['text'] = message
            self.progress_bar['value'] = percentage
            if percentage >= 100:
                return True
        except queue.Empty:
            self.master.after(100, self.process_queue)

class ThreadedTask(Thread):
    def __init__(self, queue, pic_path, destination_folder):
        Thread.__init__(self)
        self.queue = queue
        self.pic_path = pic_path
        self.destination_folder = destination_folder
    
    def run(self):
        analysis_component = AnalysisComponent(self.pic_path, self.destination_folder, self.queue)
        analysis_component.run(self.pic_path, self.destination_folder)

root = tk.Tk()
root.geometry("600x240")
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
root.mainloop()
#interface = UI_SR()
#interface.open_main_window()

