#coding=utf8 

# this module is for housing the linear algebra spanking algorithm 
# this method is complicated to explain  

import os
from unittest.loader import VALID_MODULE_NAME
import pysubs2 
from pysubs2.time import ms_to_str as MsToStr 
import numpy as np 



''' 
this method is a little bit more complicated and should be explained in details 
go google CLS problem if you do not know what I am talking about 
or watch this playlist https://www.youtube.com/playlist?list=PLoROMvodv4rMz-WbFQtNUsUElIh2cPmN9 
;)


so our goal is: 

> let's put the problem to words
> with a list of timing violations, which is a list of (ind,ind,type str) 
> these violations can be translated into desired outcomes 
> this outcome is expressed as (t1-t2==t_desired), where t1 and t2 are starts/ends depending on type 
> explained in words, we want the difference of some time points to be a desired number 
> but this is not enough, as the simpliest way would be to scatter all lines sparsely along a long timeline 
> then we need another objective to keep lines close to their original timings 
> then we want to resolve timing violations with minimum time point changes 
> one more requirement is to keep paragraphs intact
> paragraphs are connected lines with the same style, and we must keep them contineous

> let's make the problem into linear algebra
> written in math, we want ||T0-T1||^2 minimized while achieving D==D1 & P==P1
> where T0 is original timings, T1 is changed timings, D is resulting timing diff and D1 is desired timing diff 
> in linear algebra, T0 and T1 would be 2N vectors with N being number of lines 
> D and D1 are len(t_vio) vectors (as in timing violations) 
> P and P1 are #para vectors (as in number of contineous points in paragraphs, not number of paragraphs itself) 
> D and P can both be expressed as some transformation matrix times T1, since D is timing difference and P is combination of T1 
> assuming such transformation matrix is C 
> then the only unknown is T1, with D1 and P1 a linear combination is T1 
> then we are minimizing 
                ||T0-T1||^2 
> with the constraint 
                C@T1==|D1| 
                      |P1| 

> for example, with lines [0,300],[310,500],[650,1000],[1000,1500]
> there is one timing violation from end of line 1 to start of line 2, and same line2->line3 
> we want to close the gap between 300 and 310 and enlarge the 500-650 gap to 300ms
> but we want to keep timing of 1000 contineous when changing
> T0 is expressed as [0,300,310,500,650,1000,1000,1500] vector 
> transformation matrix C is 
                    [[0 -1  1  0  0  0  0  0]
                     [0  0  0 -1  1  0  0  0]
                     [0  0  0  0  0  1 -1  0]] 
                     
> the top two rows specifies two timing violations and bottom one specifies contineous points 
> C@T0 gives us [10,150,1000,1000], but we want [0,300,1000,1000], which is C@T1
> but we also want ||T0-T1||^2 to be as as small as possible  
> this is a constraint least square (CLS) problem, a derivation of least square problem of ||Ax-b||^2 

> after applying the Lagrangian multipliers, we have a Karush-Kuhn-Tucker (KKT) equation: 
                    |2I  C^T| @ |T1| == |2T0 | 
                    | C   0 |   |z |    |C@T1| 
> z is the Lagrangian multipliers that can be ignored, I is identity matrix 
> T1 is unknown but C@T1 is known, we can use normal least square to solve this 
> the following algorithm will use these steps 
''' 



# first we need to make matrix T0 from all the timings 
# this is for main function to print results 
# not used as helper 
def Subs2Mat(subs:pysubs2.SSAFile): 
    ''' 
    make a collection of N subtitles into 2N vector array 
    the vector is [start1,end1,start2,end2...endN] 
    not a helper function in algorithm 
    ''' 
    times = np.array([(i.start,i.end) for i in subs], dtype=np.int32) 
    return times.flatten() 


# we need the lower part of matrix C and C@T1, which is checked by paragraph
def FindParagraphMats(subs:pysubs2.SSAFile) -> tuple: 
    ''' 
    takes subs and find paragraph points that needs to not stay contineous 
    return a tuple of (mat,mat,list)
    first is the lower matrix of C, this is #fixed points/2 x 2x#subs matrix 
    second is #fixed points/2 vector with all zero entries, this is lower part of C@T1 
    list is all int indeces of paragraphs in the 2*len(subs) T0 vector 
    we can put more weights on keeping paragraphs timings unchanged by using this 
    ''' 
    # find time points that cannot change, indexing it inside 2xlen(subs) vector 
    # because a continuity is bi-points, it is a list of two-tuples 
    keep_conti = list() 
    for i,subi in enumerate(subs): 
        for n,subn in enumerate(subs): 
            # different style, ignore
            if subi.style != subn.style: continue 
            # start is in paragraph if it follows an end of same style
            # index in 2x#subs array is 2i if start, 2i+1 if end 
            # also check if that point pair is already in there, but in reverse order
            if (subi.start == subn.end) and not((2*n+1,2*i) in keep_conti): keep_conti.append((2*i,2*n+1)) 
            # end is in if it is followed by a start of same style 
            elif (subi.end == subn.start) and not((2*n,2*i+1) in keep_conti): keep_conti.append((2*i+1,2*n)) 
            else: continue 

    # then the matrix is len(keep_conti) x 2*len(subs), because keep_conti is half the number of points
    lower_C = np.zeros((len(keep_conti),len(subs)*2), dtype=np.int32) 
    
    # flatten the contineous point pairs into paragraph indeces
    paragraph_points = list() 
    for (i1,i2) in keep_conti: 
        paragraph_points.append(i1) 
        paragraph_points.append(i2) 
    
    # points contineous means the two points have difference of 0, hence +p1-p2
    for i in range(len(keep_conti)): 
        lower_C[i,keep_conti[i][0]] = 1 
        lower_C[i,keep_conti[i][1]] = -1 
    
    # lower part of C@T1 are all zero
    return (lower_C, np.zeros(lower_C.shape[0], dtype=np.int32), paragraph_points) 



    
# we need the upper part of matrix C and C@T1, which is determined by timing violations 
def FindTVioMats(subs:pysubs2.SSAFile, t_vio:list, t_std:dict) -> tuple: 
    ''' 
    takes a timing violation list 
    returns a tuple of (mat,mat)
    first is transformation len(t_vio) x 2N matrix specifying how to get those t_vio, 
    second is desired len(t_vio) vector of timing gaps (not violations anymore) as C@T1 
    both matrices are upper parts 
    ''' 
    # first make the base zero matrices
    upper_C = np.zeros((len(t_vio),2*len(subs)), dtype=np.int32) 
    upper_CT1 = np.zeros(len(t_vio), dtype=np.int32) 
    
    # for each violation 
    for i,(i1,i2,vio_type) in enumerate(t_vio): 
        sub1 = subs[i1] 
        sub2 = subs[i2] 
        # depending on the type, we have desired gap length 
        desired_gap = t_std[vio_type] 
        # if type is min_len, line too short 
        if vio_type=='min_len': 
            # we want end-start to be long enough 
            upper_C[i,2*i1+1] = 1 
            upper_C[i,2*i1] = -1 
            upper_CT1[i] = desired_gap 
            continue 
        
        # if gap is less than desired/2, we close the gap 
        # if gap is wider, we widen it to desired gap length
        # note in TimeShiftLogic, only positivly-valued gaps are kept 
        # then it is always line2-line1, while violation type is (line1-2-line2)
        
        # if type is s2s
        elif (vio_type == 's2s'): 
            gap = sub2.start - sub1.start 
            # gap small, close it 
            if (gap < desired_gap/2): desired_gap = 0 
            # set proper values in matrices 
            upper_C[i,2*i2] = 1 
            upper_C[i,2*i1] = -1 
            upper_CT1[i] = desired_gap 
            continue 
        
        elif (vio_type=='e2e'): 
            gap = sub2.end - sub1.end 
            if (gap < desired_gap/2): desired_gap = 0 
            upper_C[i,2*i2+1] = 1 
            upper_C[i,2*i1+1] = -1 
            upper_CT1[i] = desired_gap 
            continue 
        
        elif (vio_type=='s2e'): 
            gap = sub2.end - sub1.start 
            if (gap < desired_gap/2): desired_gap = 0 
            upper_C[i,2*i2+1] = 1 
            upper_C[i,2*i1] = -1 
            upper_CT1[i] = desired_gap 
            continue 
        
        elif (vio_type=='e2s'): 
            gap = sub2.start - sub1.end 
            if (gap < desired_gap/2): desired_gap = 0 
            upper_C[i,2*i2] = 1 
            upper_C[i,2*i1+1] = -1 
            upper_CT1[i] = desired_gap 
            continue 
        
        # no other cases 
        else: continue 
    
    # now we have iterated through all of t_vio 
    return (upper_C,upper_CT1)



# helper function turning N lines of subs into list of timings for easier processing 
# different from Subs2Mat, list is to better record time changes (kind of) 
def Subs2Times(subs:pysubs2.SSAFile) -> list: 
    ''' 
    takes a subs file and extract timings into list of (start,end) tuples 
    because list has the same order as the subs, no explicit indexing is necessary 
    ''' 
    # do it in one line
    return [(sub.start,sub.end) for sub in subs] 



# helper function turning N times of subs into 2N vector 
def Times2Vec(times:list) -> np.array: 
    ''' 
    function takes a sub file of length N and turns it into 2N vector array of time ints
    the timings are ordered as start1,end1,start2...endN 
    ''' 
    # one line o yeah
    return np.array(times, dtype=np.int32).flatten()


# helper function turning a vector with length>2N into N times list 
def Vec2Times(vec:np.array, N:int) -> list: 
    ''' 
    takes a vector of T1 and z stacked vertically and extract only T1 with N time pairs 
    z is the Lagrangian multiplier resulting from the computation, we ignore 
    hence length needs to be specified as N 
    ''' 
    # one line hehehe (remember we need integers)
    return [(round(vec[2*i]),round(vec[2*i+1])) for i in range(N)] 


# all we have to do is assemble and let the algorithm run 
def LinalgSpank(subs:pysubs2.SSAFile, t_vio:list, t_std:dict) -> tuple: 
    ''' 
    adjust timing of timing violations using linear algebra and given timing standards
    check source code for detailed explanation 
    returns (message,new subs) tuple 
    ''' 
    message = '' 
    # get upper part of C and C@T1, it is from timing violations 
    upper_C,upper_CT1 = FindTVioMats(subs=subs, t_vio=t_vio, t_std=t_std) 
    
    # get lower part, as well as paragraph indeces for increasing weights 
    lower_C,lower_CT1,para_inds = FindParagraphMats(subs=subs) 
    # weight of paragraphs, should be >=1, 1 is normal weights as any other timings
    para_weights = 10
    
    # getting ||Ax-b|| 
    # first we need b by concatenating [2*T0,upper_CT1,lower_CT1], with paragraphs in T0 increased in weights 
    Times0 = Subs2Times(subs) 
    T0 = Times2Vec(times=Times0)*2 
    for i in para_inds: 
        T0[i] *= para_weights 
    b = np.concatenate([T0,upper_CT1,lower_CT1]) 
    
    # to obtain A, we need C, C transpose, and 2*identity matrix adjusted by paragraph weights 
    C = np.vstack([upper_C,lower_C]) 
    # sanity check
    if (C.shape[1] != 2*len(subs)): 
        raise Exception(f"C matrix dimensions wrong, is {C.shape}") 
    # identity matrix correspond to numbers of time points, hence 2N x 2N, or row length of C 
    # it is better we construct it by first using a 2N vector then make it diagonal
    idntty = np.ones(2*len(subs), dtype=np.int32)*2 
    for i in para_inds: 
        idntty[i] *= para_weights
    idntty = np.diag(idntty) 
    # sanity check 
    if (idntty.shape[0] != C.shape[1]) or (idntty.shape[1] != C.shape[1]): 
        raise Exception(f"identity matrix dimension wrong, is {idntty.shape}") 
    # assemble matrix A 
    upper_A = np.concatenate([idntty,C.T], axis=1) 
    lower_A = np.concatenate([C,np.zeros((C.shape[0],C.shape[0]), dtype=np.int32)], axis=1) 
    A = np.vstack((upper_A, lower_A)) 
    
    # sanity check 
    if (A.shape[0] != b.shape[0]): 
        raise Exception(f"A and b dimension mis-match, A:{A.shape}, b:{b.shape}")
    # then we solve this using numpy's linear algebra least square 
    T1z,_,_,_ = np.linalg.lstsq(a=A, b=b, rcond=None) 
    # and extract the timings 
    Times1 = Vec2Times(vec=T1z, N=len(subs)) 
    # sanity check 
    if (len(Times1) != len(Times0)): 
        raise Exception(f"Wanted [{len(Times0)}] subs, got [{len(Times1)}] subs")
    # modify subs and message to indicate changes 
    n_changes = 0 
    ms_changes = 0 
    for i in range(len(subs)): 
        s0,e0 = Times0[i] 
        s1,e1 = Times1[i] 
        # the solution often makes 1ms differences, hence we ignore those 
        # if (abs(s1-s0) <= 1) or (abs(e1-e0) <= 1): continue 
        if (s1==s0) and (e1==e0): continue 
        n_changes += 1 
        ms_changes += abs(s0-s1) 
        ms_changes += abs(e0-e1) 
        subs[i].start = s1 
        subs[i].end = e1
        message += f">>> Line [{i+1}]:{os.linesep}" 
        message += f"old: [{MsToStr(s0,fractions=True)}]:[{MsToStr(e0,fractions=True)}] {os.linesep}" 
        message += f"new: [{MsToStr(s1,fractions=True)}]:[{MsToStr(e1,fractions=True)}] {os.linesep}" 
        # message += ('='*30 + os.linesep) 
    
    message += f">>> Changed [{n_changes}] lines {os.linesep}" 
    message += f">>> Changed [{ms_changes}] ms in total"
    return (message,subs)
        
        

    
    
    

# main is for testing the module, no actual work is done 
if __name__=='__main__': 
    file_path = input('Enter file path:') 
    subs = pysubs2.load(file_path) 
    print('The timings in Nx2 matrix is:') 
    print(Subs2Mat(subs).reshape([len(subs),2])) 
    print('paragraph matrix is:') 
    mat,_,p_pts = FindParagraphMats(subs) 
    print(np.array2string(mat, max_line_width=300)) 
    print(f"one paragraph esample: ") 
    print(mat[0])
    print(f"shape is {mat.shape}") 
    print('paragraph points found in: ') 
    print(p_pts) 
    print(f"num of paragraph points is [{len(p_pts)}]")
    
    # msg,t_std = TimeShiftLogic.LoadTStandards() 
    # print(msg) 
    # msg,t_vio = TimeShiftLogic.FindViolations(subs, t_std) 
    # print(msg) 
    # upper_C,upper_CT1 = FindTVioMats(subs, t_vio, t_std) 
    # print('upper matrices found are') 
    # print(upper_C) 
    # print(f"shape {upper_C.shape}")
    # print(upper_CT1) 
    # print(f"shape {upper_CT1.shape}")