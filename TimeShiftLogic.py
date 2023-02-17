#coding=utf8 

# this module is for housing a collection of logics used to shift the times of lines 

import os
import pysubs2 
from pysubs2.time import ms_to_str as MsToStr 
import numpy as np


def LoadTStandards() -> tuple: 
    ''' 
    load in t_standards dictionary from TimeStandards.txt file 
    this is the standards of timing
    is should only have these items 
    e2e, end to end gap, 0 default
    s2e, start to end, 0 default 
    e2s, end to start, 300 default
    s2s, start to start, 0 default
    minlen, minimum length of a sub, 500 default 
    para_weight, weights of paragraphs where start and end connect, 3 default 
    time is in miliseconds 
    returns tuple (message,t_standards dictionary) 
    ''' 
    message = '' 
    try:
        with open('TStandards.txt', 'r') as f: 
            t_standards = eval(f.readline()) 
    except Exception: 
        message += 'Error loading time standards, using defaults' 
        message += os.linesep 
        t_standards = {'e2s':300, 
                       'e2e':0, 
                       's2s':0, 
                       's2e':0, 
                       'minlen':500, 
                       'by_style':0, 
                       'para_weight':3} 
        message += f"{str(t_standards)}" 
        message += os.linesep
        return (message,t_standards) 
    
    for k,v in t_standards.items(): 
        if type(k)!=str or type(v)!=int or not(k in {'e2s','s2s','s2e','e2e','minlen','by_style','para_weight'}): 
            message += 'Error loading time standards, using defaults' 
            message += os.linesep 
            t_standards = {'e2s':300, 
                        'e2e':0, 
                        's2s':0, 
                        's2e':0, 
                        'minlen':500, 
                        'by_style':0, 
                        'para_weight':3} 
    
    message += f"Timing standards are: {os.linesep}"
    message += f"{str(t_standards)} {os.linesep}"
    return (message,t_standards)
    
    
    

def FindViolations(full_subs:pysubs2.SSAFile, t_standards:dict) -> tuple: 
    ''' 
    this function takes a subtitle file and find violations, 
    violations includes: 
    gaps that are too small 
    or subs that are too short
    and returns a message and list of tuples (ind1,ind2,conflict_str) indexing conflict subs 
    t_standards is the dictionary for timing standards 
    conflict_str is one string of e2e, s2s, e2s, s2e, minlen
    if ind1==ind2, that is a sub too short 
    ''' 
    # sort all non-comment subs by start time into list of (start,end,ind) tuples
    subs = [(sub.start,sub.end,ind) for (ind,sub) in enumerate(full_subs) if not(sub.is_comment)]
    subs.sort(key=lambda x:x[0]) 
    
    t_violations = list() 
    message = '>>> timing standards violation found in...' 
    message += os.linesep
    for i in range(len(subs)): 
        s1,e1,i1 = subs[i]
        # check minlen 
        if (e1-s1) < t_standards['minlen']: 
            t_violations.append((i1,i1,'minlen')) 
            message += f">>> [{i1+1}] is too short" 
            message += os.linesep 
        
        # check s2s, e2e, s2e, e2s 
        # inefficient N^2 algorithm, but better readibility
        for n in range(len(subs)): 
            # s2 is strictly <= s1
            s2,e2,i2 = subs[n] 
            # if we choose to ignore violations by different style (speaker) 
            if t_standards['by_style'] and (full_subs[i1].style != full_subs[i2].style): continue
            # check s2s, start of 2 is later than start of 1
            if ((s2-s1) > 0) and ((s2-s1) < t_standards['s2s']): 
                t_violations.append((i1,i2,'s2s')) 
                message += f">>> [{i1+1}]->[{i2+1}] start to start" 
                message += os.linesep
            # check e2e, end of 2 is later than end of 1
            if ((e2-e1) > 0) and ((e2-e1) < t_standards['e2e']): 
                t_violations.append((i1,i2,'e2e')) 
                message += f">>> [{i1+1}]->[{i2+1}] end to end"
                message += os.linesep 
            # check s2e, where end of line 2 is later than end of line 1 
            if ((e2-s1) > 0) and ((e2-s1) < t_standards['s2e']): 
                t_violations.append((i2,i1,'s2e')) 
                message += f">>> [{i2+1}]->[{i1+1}] start to end" 
                message += os.linesep 
            # check e2s, where start of line 2 is later than end of line 1
            if ((s2-e1) > 0) and ((s2-e1) < t_standards['e2s']): 
                t_violations.append((i1,i2,'e2s')) 
                message += f">>> [{i1+1}]->[{i2+1}] end to start"
                message += os.linesep 
            else: pass 
            
    message += os.linesep 
    return (message,t_violations)


    
def IsParagraphEnd(subs:pysubs2.SSAFile, ind:int) -> bool: 
    ''' 
    check if a line is the end of a paragraph, 
    it is when there is no line with the same style immediately following it 
    a single line can be a paragraph by itself
    ''' 
    current_line = subs[ind] 
    for line in subs: 
        if (line.style == current_line.style) and (line.start == current_line.end): 
            return False 
    return True 



def ExtendEnds(subs:pysubs2.SSAFile, t_violations:list, t_std:dict) -> tuple: 
    ''' 
    simple shift and end points of all the t_violations 
    while keeping long sentences by same style fixed 
    returns (message,changed subs)
    simplest method for line correction 
    ''' 
    message = '' 
    s2e = t_std['s2e'] 
    e2e = t_std['e2e'] 
    min_len = t_std['minlen'] 
    # e2s = t_std['e2s'] # not need since we merge end to start
    for (i1, i2, conf_type) in t_violations: 
        # if sub is too short and end of paragraph, extend the end 
        if (conf_type == 'minlen') and IsParagraphEnd(subs,i1): 
            message += f">>> [{i1+1}] end: [{MsToStr(subs[i1].end,fractions=True)}]->" 
            subs[i1].end=(subs[i1].start+min_len) 
            message += f"[{MsToStr(subs[i1].end,fractions=True)}]" 
            message += os.linesep 
            continue
        # if e2s and line 1 is end of paragraph, extend to next start
        elif (conf_type == 'e2s') and IsParagraphEnd(subs, i1): 
            message += f">>> [{i1+1}] end: [{MsToStr(subs[i1].end,fractions=True)}]->" 
            subs[i1].end = subs[i2].start 
            message += f"[{MsToStr(subs[i1].end,fractions=True)}]" 
            message += os.linesep 
            continue
        # if s2e and line 2 is end of paragraph, extend to minimum gap
        elif (conf_type == 's2e') and IsParagraphEnd(subs, i2): 
            message += f">>> [{i2+1}] end: [{MsToStr(subs[i2].end,fractions=True)}]->" 
            subs[i2].end=(subs[i1].start+s2e) 
            message += f"[{MsToStr(subs[i2].end,fractions=True)}]" 
            message += os.linesep 
            continue
        # if e2e, more conditions
        elif (conf_type == 'e2e'): 
            # extend the line 1, if end of paragraph 
            if IsParagraphEnd(subs,i1): 
                message += f">>> [{i1+1}] end: [{MsToStr(subs[i1].end,fractions=True)}]->" 
                subs[i1].end = subs[i2].end 
                message += f"[{MsToStr(subs[i1].end,fractions=True)}]" 
                message += os.linesep 
                continue
            # extend line 2 if line 1 in paragraph 
            elif IsParagraphEnd(subs,i2): 
                message += f">>> [{i2+1}] end: [{MsToStr(subs[i2].end,fractions=True)}]->" 
                subs[i2].end=(subs[i1].end+e2e) 
                message += f"[{MsToStr(subs[i2].end,fractions=True)}]" 
                message += os.linesep 
                continue 
            # if both in paragraph, just continue to next conflict 
            else: continue 
        # after checking this conflict, move to next one 
        else: continue 
    
    message += '>>> Other lines are fixed in long sentences' 
    message += os.linesep
    return (message,subs)
            
                
        

def main(): 
    subs = pysubs2.load('sample.ass') 
    message,t_std = LoadTStandards() 
    print(message) 
    message,t_violations = FindViolations(subs,t_std) 
    print(message) 
    return 

if __name__=='__main__': 
    main() 