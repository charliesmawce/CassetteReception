import tkinter as tk
import json
import re
from rootToPlotAndCSV import dfToIVPlot, plotADC
from databaseFunc import getDataFromTestedMod, getDataFromManufMod
#import tkinter.tkk as tkk

large_font = ("Verdana", 15)

class cassetteReceptionGUI(tk.Tk):
    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)
        container = tk.Frame(self)
        
        container.pack(side="top", fill="both",expand="true")
        
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)
        
        self.frames = {}
        
        for f in (startFrame, testFrame):
            frame = f(container, self)
            self.frames[f] = frame
            frame.grid(row=0, column=0, sticky="nsew")
        
        self.showFrame(startFrame)
    
    def showFrame(self, cont):
        frame = self.frames[cont]
        frame.tkraise()

class startFrame(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        label = tk.Label(self, text="startpage", font="large_font")
        label.pack(pady=10,padx=10)
        
        test_frame_btn = tk.Button(self, text="to test page", command=lambda:controller.showFrame(testFrame))
        test_frame_btn.pack(pady=10,padx=10)

class testFrame(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        
        mod_name_title = tk.StringVar()
        mod_name_title.set("mode_name")
        mod_name_lbl = tk.Label(self, textvariable=mod_name_title)
        mod_name_lbl.pack(pady=10)
        
        test_metadata_txt = tk.StringVar()
        test_metadata_txt.set("metadata here pls!")
        test_metadata_lbl = tk.Label(self, textvariable=test_metadata_txt)
        test_metadata_lbl.pack(pady=5)
        
        results = tk.StringVar()
        results.set("Mod Passed")
        test_result_lbl = tk.Label(self, textvariable=results, foreground="green", font=("Helvetica", 14, "bold"))
        test_result_lbl.pack(pady=10)
        
        test_result_frame = tk.Frame(self)
        test_result_frame.pack(padx=3, pady=15)
        
        failed_tests, skipped_tests = ["a","b","c"],["x","y","z"] #checkIfPasssed(test_file_path)
        
        skipped_test_lbl = tk.Label(test_result_frame, text="Skipped Tests")
        skipped_test_lbl.grid(row=0, column=1, padx=5, pady=5)
        skipped_test_textbox = tk.Text(test_result_frame, state = 'normal')
        skipped_test_textbox.grid(row=1, column=1, padx=5, pady=5)
        for test in skipped_tests:
            #test = re.sub(r"\[.*?\]", "", test).strip()
            skipped_test_textbox.insert(tk.END, test + "\n")
            #print("skipped")
        skipped_test_textbox.configure(state='disabled')
        skipped_scrollbar = tk.Scrollbar(skipped_test_textbox, orient=tk.VERTICAL, command=tk.Text.yview)
        skipped_test_textbox.configure(yscrollcommand=skipped_scrollbar.set)
        
        if failed_tests != []:
            results.set("Mod Failed")
            test_result_lbl['foreground'] ="red"
            failed_test_lbl = tk.Label(test_result_frame, text="Failed Tests")
            failed_test_lbl.grid(row=0, column=0, padx=5, pady=5)
            failed_test_textbox = tk.Text(test_result_frame, state = 'normal')
            failed_test_textbox.grid(row=1, column=0, padx=5, pady=5)
            for test in failed_tests:
                #test = re.sub(r"\[.*?\]", "", test).strip()
                failed_test_textbox.insert(tk.END, test + "\n")
            failed_test_textbox.configure(state='disabled')
            failed_scrollbar = tk.Scrollbar(failed_test_textbox, orient=tk.VERTICAL, command=tk.Text.yview)
            failed_test_textbox.configure(yscrollcommand=failed_scrollbar.set)
            
            make_plot_btn = tk.Button(self, text = "make plots! (no functionality yet)", state='disabled', 
                                        command=lambda:controller.showFrame(startFrame))
            make_plot_btn.pack(pady=10)

gui = cassetteReceptionGUI()
gui.mainloop()