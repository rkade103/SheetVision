import tkinter as tk
import sys

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
        self.quitButton.place(x=400, y=115)

        #Create a generate button and place it.
        self.generateButton = tk.Button(self, text="Generate", command=self.generate_sheet)
        self.generateButton.place(x=175, y=115)

    def client_exit(self):
        sys.exit()

    def create_window(self):
        tk.Label(self, wraplength=600, text="Welcome to the SheetReader! This tool is designed to generate an excerpt sheet that" + 
                                " will be used by the Midi Analyzer. Supply an image of the line as well as a model file" +
                                " that represents a perfect run-through, and this tool will generate the excerpt sheet for you!").grid(row=0, columnspan=3)

        ''
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

    def generate_sheet(self):
        analysis_component = AnalysisComponent()
        path_to_pic = self.picEntry.get()
        analysis_component.run(path_to_pic)

root = tk.Tk()
root.geometry("600x150")
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

