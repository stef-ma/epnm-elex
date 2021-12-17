# from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
# from matplotlib.figure import Figure
import tkinter as tk
# from tkinter import ttk
# from rm_setup import *

# mpl.use("TkAgg")

# import time

LARGE_FONT = ("Cambria", 12)


class NewFrame(tk.Frame):
    """Blank black frame to use as basis for buiding the app"""

    def __init__(self, parent, width, pane_height):
        tk.Frame.__init__(self, parent, width=width, height=pane_height, borderwidth=0)
        self.configure(background='black')


class Blank(tk.Frame):
    """Blank black frame to use as basis for buiding the app,no width or height specified."""

    def __init__(self, parent, controller):  # Controller must be included
        # so I can call it together with InstCont in gui.
        tk.Frame.__init__(self, parent)
        self.configure(background='black', borderwidth=0)

