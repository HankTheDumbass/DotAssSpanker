#coding=utf8 
# GUI execution of the application

import tkinter as tk 
from tkinter import messagebox
from tkinter import filedialog 
import AssSpanker 
import traceback 
from datetime import datetime 
import os
import pysubs2 
import TimeShiftLogic 
import LinalgSpank 
import time 
    

# define a window and error handling 
win = tk.Tk() 
# win.geometry('600x600') 
win.title('♂ AssSpanker ♂') 
def GUIExcHandling(exc, val, tb): 
    now = datetime.now() 
    now = now.strftime("%Y-%b-%d-%H-%M-%S") 
    with open(f"Error{now}.txt", 'w', encoding='utf-8') as f: 
        traceback.print_exc(file=f) 
    messagebox.showerror(title='ERROR', message='An error happend, go check the log') 
    exit() 

win.report_callback_exception = GUIExcHandling 


# make label for file entry 
file_elabel = tk.Label(win, text='♂ Spanking: ♂') 
file_elabel.grid(row=0, column=0, padx=10, pady=2) 

# make entry for file path 
file_entry = tk.Entry(master=win, width=69) 
file_entry.insert(0, 'Looking for one Hugh Jass') 
file_entry.grid(row=0, column=1, pady=2) 
# make main text output 
out_text = tk.Text(win, height=30, width=50) 
out_text.grid(row=1, column=1, rowspan=30, pady=2) 
out_text.insert('end','Output goes here:') 
out_text.insert('end', os.linesep) 
# check if SwapMap.txt is here
if not os.path.isfile('SwapMap.txt'): 
    out_text.insert('end', 'SwapMap.txt not found, proceeding anyway...'+os.linesep) 
    out_text.see('end') 
else: 
    out_text.insert('end', 'SwapMap.txt found, proceeding...'+os.linesep) 
    out_text.see('end') 
# check if TStandards.txt is here
if not os.path.isfile('TStandards.txt'): 
    out_text.insert('end', 'TStandards.txt not found, proceeding anyway...'+os.linesep) 
    out_text.see('end') 
else: 
    out_text.insert('end', 'TStandards.txt found, proceeding...'+os.linesep) 
    out_text.see('end') 
out_text.insert('end', "Don't forget to save file at the end"+os.linesep) 
out_text.see('end') 


# create a spaking session dict for later processing 
spanking = {'subs':None, 'save_to':None, 't_std':None, 't_violations':None} 



# make button for finding file 
def FindAssPath() -> str: 
    ''' 
    function for calling a window to find .ass file 
    ''' 
    f_path = filedialog.askopenfilename(title = 'where is the ♂.ass♂', filetypes=[('ass files', '*.ass')]) 
    f_path = os.path.abspath(f_path) 
    file_entry.delete(0, 'end') 
    file_entry.insert(0, f_path) 
    
file_button = tk.Button(win, text='Find .ass', command=FindAssPath, width=10) 
file_button.grid(row=0, column=2, pady=2, padx=10) 





# make a button to load in file 
def LoadAssGUI(): 
    file_path = file_entry.get()
    try: 
        spanking['subs'] = AssSpanker.LoadAss(file_path) 
    except Exception: 
        spanking['subs'] = None 
        out_text.insert('end', 'Error loading file, change path and try again'+os.linesep) 
        out_text.see('end') 
        return 
    # configure global variables for later processing
    file_name = os.path.basename(file_path) 
    path_ext = os.path.splitext(file_path) 
    spanking['save_to'] = path_ext[0] + '[Spanked]' + path_ext[1]
    out_text.insert('end', f"File [{file_name}] loaded successfully"+os.linesep) 
    out_text.see('end') 
    return 

lf_button = tk.Button(win, text='Load .ass', command=LoadAssGUI) 
lf_button.grid(row=1, column=0, pady=2) 



# make a swap symbol button 
def SwapSymbolsGUI(): 
    if spanking['subs'] is None: 
        out_text.insert('end', 'Ass not found, load .ass first'+os.linesep) 
        out_text.see('end')
        return 
    msg,subs = AssSpanker.SwapSymbols(spanking['subs']) 
    spanking['subs'] = subs 
    out_text.insert('end', msg+os.linesep) 
    out_text.insert('end', '♂ Spanked ♂'+os.linesep)
    out_text.see('end') 
    return 
    
swap_symbol_btn = tk.Button(win, text='Swap Symbols', command=SwapSymbolsGUI) 
swap_symbol_btn.grid(row=2, column=0, pady=2) 



# make a button for saving the file 
def SaveAss(): 
    ''' 
    button function for saving subtitle to original folder 
    with [Spanked] added to the name 
    ''' 
    if spanking['subs'] is None or spanking['save_to'] is None: 
        out_text.insert('end', 'No .ass spanked yet, spank an .ass first'+os.linesep) 
        out_text.see('end') 
        return 
    spanking['subs'].save(spanking['save_to']) 
    out_text.insert('end', f"Spanked .ass saved to: {os.linesep}{spanking['save_to']}"+os.linesep) 
    out_text.see('end') 
    return 

save_file_btn = tk.Button(win, text='Save file', command=SaveAss) 
save_file_btn.grid(row=1, column=2, pady=2) 



# make a button for detecting time standatd violations 
def FindBadLinesGUI(): 
    ''' 
    function for button to find time standards violations 
    ''' 
    if spanking['subs'] is None or spanking['save_to'] is None: 
        out_text.insert('end', 'Ass not found, load .ass first'+os.linesep) 
        out_text.see('end') 
        return 
    # load in timing standards 
    message,t_std = TimeShiftLogic.LoadTStandards() 
    spanking['t_std'] = t_std
    out_text.insert('end', message+os.linesep)  
    # find timing violations 
    message,t_violations = TimeShiftLogic.FindViolations(spanking['subs'], t_std) 
    spanking['t_violations'] = t_violations
    out_text.insert('end', message+os.linesep) 
    out_text.insert('end', '♂ Spanked ♂'+os.linesep)
    out_text.see('end') 
    return 

find_bad_lines_btn = tk.Button(win, text='Find Bad Lines', command=FindBadLinesGUI) 
find_bad_lines_btn.grid(row=3, column=0, pady=2) 



# make a button to simply extend ends 
def ExtendEndsGUI(): 
    ''' 
    gui button function for simply extending the ends 
    ''' 
    if spanking['subs'] is None or spanking['save_to'] is None: 
        out_text.insert('end', 'Ass not found, load .ass first'+os.linesep) 
        out_text.see('end') 
        return 
    if spanking['t_std'] is None or spanking['t_violations'] is None: 
        out_text.insert('end', 'Bad lines not found, find them first'+os.linesep) 
        out_text.see('end') 
        return 
    message,subs = TimeShiftLogic.ExtendEnds(spanking['subs'], spanking['t_violations'], spanking['t_std']) 
    spanking['subs'] = subs 
    spanking['t_violations'] = None 
    out_text.insert('end',message+os.linesep) 
    out_text.insert('end', '♂ Spanked ♂'+os.linesep)
    out_text.see('end') 
    return 

extend_ends_btn = tk.Button(win, text='Extend Ends Only', command=ExtendEndsGUI) 
extend_ends_btn.grid(row=4, column=0, pady=2, padx=2)
    
  
    
# make a button for linear algebra spanking of timing 
def LinalgSpankGUI(): 
    ''' 
    gui button function for timing changes using linear algebra 
    because it usually takes a few spankings, we loop until no violations are found 
    ''' 
    if spanking['subs'] is None or spanking['save_to'] is None: 
        out_text.insert('end', 'Ass not found, load .ass first'+os.linesep) 
        out_text.see('end') 
        return 
    if spanking['t_std'] is None or spanking['t_violations'] is None: 
        out_text.insert('end', 'Bad lines not found, find them first'+os.linesep) 
        out_text.see('end') 
        return 
    # out_text.insert('end', 'It usually takes a few spanks.'+os.linesep)
    # out_text.insert('end', 'Processing...'+os.linesep) 
    # out_text.see('end') 
    
    message,subs = LinalgSpank.LinalgSpank(spanking['subs'], spanking['t_violations'], spanking['t_std']) 
    spanking['subs'] = subs 
    out_text.insert('end', message+os.linesep) 
    _,spanking['t_violations'] = TimeShiftLogic.FindViolations(spanking['subs'], spanking['t_std']) 
    out_text.insert('end', f"Found [{len(spanking['t_violations'])}] more violations{os.linesep}") 
    if (len(spanking['t_violations']) > 0): 
        out_text.insert('end', 'Come on, spank again!'+os.linesep) 
    else: 
        out_text.insert('end', '♂ Done and Dusted ♂'+os.linesep) 
        # spanking['t_violations'] = None 
    out_text.see('end') 
        
    return 

linalg_spank_btn = tk.Button(win, text='♂ LinAlg SPANK ♂', command=LinalgSpankGUI) 
linalg_spank_btn.grid(row=5, column=0, pady=2, padx=2)







if __name__=='__main__': 
    try: 
        win.mainloop()
    except Exception: 
        now = datetime.now() 
        now = now.strftime("%Y-%b-%d-%H-%M-%S") 
        with open(f"Error{now}.txt", 'w', encoding='utf-8') as f: 
            traceback.print_exc(file=f)