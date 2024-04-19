import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

import numpy as np
import tifffile
import sys
import argparse
import os
import logging
import tensorflow as tf
from skimage import exposure#, external
from scipy import ndimage, signal, stats
from math import floor, ceil
from flowdec import data as fd_data
from flowdec import psf as fd_psf
from flowdec import restoration as fd_restoration
from tqdm import tqdm


def get_kernel(psf, z_spacing = 2.705078):
    kernel_shape = (51,51,51)
    kernel_shape = (25,25,25)
    kernel = np.zeros(kernel_shape) #(51,51,51)) #Note may not work if this size is too big relative to the image
    for offset in [0,1]:
        kernel[tuple((np.array(kernel.shape) - offset) // 2)] = 1
    #assume bead image at different resolution in z to actual data, and difference is a factor of 3.08 (308nm versus 100nm)
    #estimated and stored 3d psf, but assume here diagonal psf. Could adjust this, but already very close to diagonal
    kernel = ndimage.gaussian_filter(kernel, sigma=[np.sqrt(psf[2,2])/z_spacing,np.sqrt(psf[0,0]),np.sqrt(psf[1,1])])
    return kernel

def run_3d_decon(timepoint, kernel, niter, algo):
    nonzero = timepoint[np.where(timepoint>0)]
    bkgd_mode = stats.mode(nonzero)[0][0]
    bkgd_std = stats.tstd(nonzero)
    indz,indy,indx = np.where(timepoint==0)
    timepoint[indz, indy, indx] = bkgd_mode + bkgd_std*np.random.randn(len(indz))
    return algo.run(fd_data.Acquisition(data=timepoint, kernel=kernel), niter=niter).data

def run_decon(input_files, dats, mdata, psfs, x_res, y_res, z_spacing, input_rl, pad_amount, channels, debug_iterations):
    if debug_iterations:
        iterations = [x for x in range(1,input_rl+1) if x % 5 == 0]
        if input_rl % 5 != 0: iterations.append(input_rl)
    else:
        iterations = [input_rl]
        

    for (input_file_str, dat) in zip(input_files, dats):
        for niter in iterations:
            run_5d_decon(input_file_str, dat, mdata, psfs, x_res, y_res, z_spacing, niter, pad_amount, channels)


def run_5d_decon(input_file_str, dat, mdata, psfs, x_res, y_res, z_spacing, niter, pad_amount, channels):
    os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # FATAL
    logging.getLogger('tensorflow').setLevel(logging.FATAL)
    print(dat.shape)
    data = np.copy(dat) 
    res = np.zeros(data.shape)

    

    if len(data.shape) == 3:
        res = np.expand_dims(res, 0)
        data = np.expand_dims(data, 0)

    if len(psfs[0].shape) == 2:
        kernel488 = get_kernel(psfs[0], z_spacing)
    else:
        kernel488 = psfs[0]

    
    if channels == 1:
        
        
        if len(data.shape) == 5:
            res = res[:, :, 0]
        res = np.expand_dims(res, 2)
        data = np.expand_dims(data, 2)
        
    
    if channels == 2:
        if len(psfs[1].shape) == 2:
            kernel640 = get_kernel(psfs[1], z_spacing)
        else:
            kernel640 = psfs[1]
        
    
    ndim = 3 #data.ndim 
    algo = fd_restoration.RichardsonLucyDeconvolver(ndim, pad_mode='none', pad_min=[pad_amount,pad_amount,pad_amount]).initialize() 
    
    for i,image in tqdm(enumerate(data), total=data.shape[0], desc='Deconvolving: '):
        res[i, :, 0] = run_3d_decon(image[:,0], kernel488, niter, algo)  
        if channels ==2:
            res[i, :, 1] = run_3d_decon(image[:,0], kernel640, niter, algo)
    
    suffix = f"_2024-03-05_MC191_488Ndc80EGFP_4sec_5dayAVGsigma_rl{niter}.tif"
    output_file_str = input_file_str.replace(".tif", suffix)
    mdata['channels'] = channels

    tifffile.imwrite(output_file_str, res.astype(np.uint16), imagej = True, metadata=mdata, resolution=(x_res, y_res))
    print('All finished\n')