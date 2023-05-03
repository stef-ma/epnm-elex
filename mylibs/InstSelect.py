from tkinter import ttk
from mylibs.InstCont import *

LARGE_FONT = ("Cambria", 12)

class InstSelect(NewFrame):
    """The Instrument Selection Frame. Uses rm_setup functions,
    passes selected InstClass to root and allows entrance into Instrument Control."""

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
        lbut1 = ttk.Button(frame1, text="Select Instument: K2612B",
                             command=lambda: controller._setInstrument_K2612B(instrument_listbox, instrument_list))
        lbut1.pack(padx=10, pady=10, )
        # Create Select k2612B_instrument button.
        lbut2 = ttk.Button(frame1, text="Select Instument: K2182A",
                             command=lambda: controller._setInstrument_K2182A(instrument_listbox, instrument_list))
        lbut2.pack(padx=10, pady=10, )
        # Create Select k2612B_instrument button.
        lbut3 = ttk.Button(frame1, text="Select Instument K6221",
                             command=lambda: controller._setInstrument_K6221(instrument_listbox, instrument_list))
        lbut3.pack(padx=10, pady=10, )
        # Create Select k2400_instrument button.
        lbut4 = ttk.Button(frame1, text="Select Instument K2400",
                             command=lambda: controller._setInstrument_K2400(instrument_listbox, instrument_list))
        lbut4.pack(padx=10, pady=10, )

        # Create Control Board Selectors
        rbut1 = ttk.Button(frame2, text="SETUP: K2612B SOLO",
                             command=lambda: controller._show_frame(InstCont_K2612B))
        rbut1.pack(padx=10, pady=10, )

        rbut2 = ttk.Button(frame2, text="SETUP: K2612B + K2182A",
                             command=lambda: controller._show_frame(InstCont_K2612BandK2182A))
        rbut2.pack(padx=10, pady=10, )

        rbut3 = ttk.Button(frame2, text="SETUP: K6221 + K2182A",
                             command=lambda: controller._show_frame(InstCont_K6221andK2182A))
        rbut3.pack(padx=10, pady=10, )

        rbut4 = ttk.Button(frame2, text="SETUP: K2400 + K2182A",
                             command=lambda: controller._show_frame(InstCont_K2400andK2182A))
        rbut4.pack(padx=10, pady=10, )

