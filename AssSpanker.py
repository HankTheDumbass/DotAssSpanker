#coding=utf8 

# This is the main module for the AssSpanker application

# import the needed modules
import pysubs2
import os
import traceback 
import TimeShiftLogic 
from datetime import datetime 


#================== define module functions =========================== 
def AskForAss() -> str: 
    '''
    ask for the path and file name of the .ass file 
    keep asking until one existing file is passed
    '''

    file_not_found = True 
    # file_path = ''
    file_path = input('Looking for one ♂ Hugh Jass ♂: ') 
    return file_path 


def LoadAss(file_path:str) -> pysubs2.SSAFile: 
    '''
    load in a .ass file into ram and return said ssafile
    raise an exception if file cannot be properly loaded
    ''' 
    subs = pysubs2.load(file_path)
    return subs 


def LoadSwapMap() -> tuple: 
    '''
    load in SwapMap
    which is a dictionary that contains symbols for swapping,  
    in order to proofread the .ass file 
    ''' 
    message = '' 
    # default protocol if one is not specified
    swap_map = {'。。。':'...', 
                    '【':'「', 
                    '】':'」', 
                    ',':'  ', 
                    '，':'  '} 
    
    if not(os.path.isfile('SwapMap.txt')):
        message += 'SwapMap not found, using default' 
        message += os.linesep 
    else: 
        swap_map = dict() 
        with open('SwapMap.txt', 'r', encoding='utf-8') as f: 
            lines = [i.strip(os.linesep) for i in f.readlines()]
        for i in lines: 
            temp = i.split('-->') 
            swap_map[temp[0]] = temp[1] 
    
    for k,v in swap_map.items(): 
        message += f">>> swapping [{k}] for [{v}]" 
        message += os.linesep 
    
    message += 2*os.linesep 
    return (message, swap_map) 



def SwapSymbols(subs:pysubs2.SSAFile) -> tuple: 
    '''
    swap charactersymbols specified in the protocol 
    use default protocol is not specified
    ''' 
    message,swap_map = LoadSwapMap() 
    num_swapped = 0
    for i in range(len(subs)): 
        line = subs[i].text 
        for k,v in swap_map.items(): 
            if k in line: 
                line = v.join(line.split(k)) 
                num_swapped += 1
                message += f">>> in line [{i+1}] swapping[{k}] for [{v}]" 
                message += os.linesep 
        subs[i].text = line 
        
    message += f"Swapped [{num_swapped}] symbols" 
    message += os.linesep 
    return (message,subs)
    

#================== main function ================================

def main(): 
    file_path = AskForAss() 
    subs = LoadAss(file_path) 
    message,subs = SwapSymbols(subs) 
    print(message) 
    subs.save('Spanked.ass') 
    print('file saved')
    message,t_std = TimeShiftLogic.LoadTStandards() 
    print(message) 
    message,t_violations = TimeShiftLogic.FindViolations(subs,t_std) 
    print(message) 
    return 


if __name__=='__main__': 
    try:
        main() 
    except Exception as e: 
        traceback.print_exc() 
        # put error into a log txt file with date time
        now = datetime.now() 
        now = now.strftime("%Y-%b-%d-%H-%M-%S") 
        with open(f"Error{now}.txt", 'w', encoding='utf-8') as f: 
            traceback.print_exc(file=f) 
        print('Please restart and try again')
        input('Press enter to exit')
