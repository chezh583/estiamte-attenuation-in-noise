#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Sep 25 11:57:42 2026

@author: chezh
"""

import numpy as np

__all__ = ['npmle_median']


EM_ITER = 400    # max turn of loop
EM_TOL = 1e-9     
CDF_TOL = 1e-12 



def turnbull_intervals(exact, lower, upper, low_end=-np.inf):
    points=[]
    for x in exact:
        points.append((x,0))
        points.append((x,1))
        
    for L in lower:
        points.append((L,0))
        points.append((np.inf,1))
        
    for U in upper:
        points.append((low_end,0))
        points.append((U,1))
        
    #%%    
    points = sorted(set(points))
    
    p, q = [],[]
    for i in range(len(points)-1):
        if points[i][1] == 0 and points[i+1][1] == 1:
            p.append(points[i][0])
            q.append(points[i+1][0])
    
    return np.array(p), np.array(q)


def npmle_fit(exact, lower=None, upper=None, low_end=-np.inf,
              n_iter=EM_ITER, tol=EM_TOL):
    # 1. Clean input: 1-D float arrays, NaN/inf dropped
    def clean(v):
        v = np.array([], float) if v is None else np.asarray(v, float).ravel()
        return v[np.isfinite(v)]

    exact, lower, upper = clean(exact), clean(lower), clean(upper)
    n = exact.size + lower.size + upper.size

    # 2. Intervals where mass can go
    p, q = turnbull_intervals(exact, lower, upper, low_end)
    K = p.size

    # 3. Box index for each observation
    k_exact = np.searchsorted(p, exact)                     
    k_first = np.searchsorted(p, lower)                     
    k_last = np.searchsorted(q, upper, side='right') - 1    

    # 4. EM: split every observation over its allowed boxes in proportion to w
    w = np.full(K, 1.0 / K)                                 
    for _ in range(n_iter):
        mass = np.bincount(k_exact, minlength=K).astype(float)   

        for r in k_first:                                   
            total = w[r:].sum()
            if total > 0:
                mass[r:] += w[r:] / total

        for u in k_last:                                    
            total = w[:u + 1].sum()
            if total > 0:
                mass[:u + 1] += w[:u + 1] / total

        new = mass / n
        if np.max(np.abs(new - w)) < tol:
            return p, q, new
        w = new
    return p, q, w


def npmle_median(p, q, w, tol=CDF_TOL):
    F = np.cumsum(w)                          
    k = np.argmax(F >= 0.5 - tol)             
    if abs(F[k] - 0.5) <= tol:                    
        k2 = k + 1 + np.argmax(w[k + 1:] > tol)   
        lo, hi = q[k], p[k2]                      
    else:
        lo, hi = p[k], q[k]                       

    if lo == hi:
        return lo                                 
    if np.isfinite(lo) and np.isfinite(hi):
        return 0.5 * (lo + hi)
    return np.nan    








