# import matplotlib as mpl
# from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
# from matplotlib.figure import Figure
# import tkinter as tk
from tkinter import ttk

# from mylibs.RmSetup import *
# from mylibs.BaseFrames import *
from mylibs.InstCont import *

# mpl.use("TkAgg")

# import time

LARGE_FONT = ("Cambria", 12)


class InstSelect(NewFrame):
    """The Instrument Selection Frame. Uses rm_setup functions,
    passes selected k2612B_instrument to root and allows entrance into Instrument Control."""

    def __init__(self, parent, controller):
        # Init the New_Frame
        NewFrame.__init__(self, parent, controller.width, controller.pane_height * 4)
        # Get a k2612B_instrument dictionary from inst_seek() in rm_setup
        instrument_dict = inst_seek()
        # Create a listbox to hold the dictionary keys
        instrument_listbox = tk.Listbox(self, fg='white', bg='black')
        instrument_listbox.pack(padx=10, pady=10, fill='x')
        i = 0
        for key in instrument_dict.keys():
            instrument_listbox.insert(i, key)  # Populate the listbox. This will usually iterate only once.
            i += 1
        instrument_list = list(instrument_dict.values())  # Get the addresses as a list for easier handling.

        frame=NewFrame(self,controller.width-5,controller.pane_height*2-5)
        frame.pack()
        frame1=NewFrame(frame,controller.width/2-5,controller.pane_height*2-5)
        frame1.pack(side='left')

        frame2=NewFrame(frame,controller.width/2-5,controller.pane_height*2-5)
        frame2.pack(side='right')
        # Create Select k2612B_instrument button.
        button2 = ttk.Button(frame1, text="Select Instument: K2612B",
                             command=lambda: controller._setInstrument_K2612B(instrument_listbox, instrument_list))
        button2.pack(padx=10, pady=10, )
        # Create Select k2612B_instrument button.
        button3 = ttk.Button(frame1, text="Select Instument: K2182A",
                             command=lambda: controller._setInstrument_K2182A(instrument_listbox, instrument_list))
        button3.pack(padx=10, pady=10, )
        # Create Select k2612B_instrument button.
        button4 = ttk.Button(frame1, text="Select Instument K6221",
                             command=lambda: controller._setInstrument_K6221(instrument_listbox, instrument_list))
        button4.pack(padx=10, pady=10, )
        # Create Switch to InstCont_K2612B button.
        button5 = ttk.Button(frame2, text="SETUP: K2612B SOLO",
                            command=lambda: controller._showFrame(InstCont_K2612B))
        button5.pack(padx=10, pady=10, )
        button6 = ttk.Button(frame2, text="SETUP: K2612B + K2182A",
                            command=lambda: controller._showFrame(InstCont_K2612BandK2182A))
        button6.pack(padx=10, pady=10, )

        button7 = ttk.Button(frame2, text="SETUP: K6221 + K2182A",
                            command=lambda: controller._showFrame(InstCont_K6221andK2182A))
        button7.pack(padx=10, pady=10, )

