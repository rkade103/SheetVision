import sys
import subprocess
import cv2
import time
import os
import queue
import numpy as np
from threading import Thread
from threading import Event
from best_fit import fit
from rectangle import Rectangle
from note import Note
from random import randint
from midiutil.src.midiutil.MidiFile3 import MIDIFile
from ExcelWriter import ExcelWriter
from MidiReader import MidiReader


def check_if_only_white(path):
    try:
        print("TRYING TO CHECK COLORS.")
        this_img = cv2.imread(path)
        gray = cv2.cvtColor(this_img, cv2.COLOR_BGR2GRAY)
        return None;
    except Exception as e:
        return "The image given contains no colors. Please provide an image of a single line of sheet music."

