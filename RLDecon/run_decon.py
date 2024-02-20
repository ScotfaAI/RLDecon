import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

import numpy as np
import bioformats.omexml as ome
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
from xml.etree import cElementTree as ElementTree
from tqdm import tqdm


def get_kernel(psf, z_spacing = 2.705078):
    kernel_shape = (51,51,51)
    kernel = np.zeros(kernel_shape) #(51,51,51)) #Note may not work if this size is too big relative to the image
    for offset in [0,1]:
        kernel[tuple((np.array(kernel.shape) - offset) // 2)] = 1
    #assume bead image at different resolution in z to actual data, and difference is a factor of 3.08 (308nm versus 100nm)
    #estimated and stored 3d psf, but assume here diagonal psf. Could adjust this, but already very close to diagonal
    kernel = ndimage.gaussian_filter(kernel, sigma=[np.sqrt(psf[2,2])/z_spacing,np.sqrt(psf[0,0]),np.sqrt(psf[1,1])])
    return kernel


def run_5d_decon(input_file_str, dat, mdata, psf488, psf640, z_spacing, niter, pad_amount):
    # print(dat.shape)
    kernel488 = get_kernel(psf488, z_spacing)
    kernel640 = get_kernel(psf640, z_spacing)
    data = np.copy(dat) 
    res = np.zeros(data.shape)
    ndim = 3 #data.ndim 
    algo = fd_restoration.RichardsonLucyDeconvolver(ndim, pad_mode='none', pad_min=[pad_amount,pad_amount,pad_amount]).initialize() 
    
    for i,image in tqdm(enumerate(data), total=data.shape[0], desc='Deconvolving: '):
        # print(image.shape)
        tt488 = image[:,0]
        nonzero = tt488[np.where(tt488>0)]
        bkgd_mode = stats.mode(nonzero)[0][0]
        bkgd_std = stats.tstd(nonzero)
        indz,indy,indx = np.where(tt488==0)
        tt488[indz, indy, indx] = bkgd_mode + bkgd_std*np.random.randn(len(indz))
        # Note that deconvolution initialization is best kept separate from 
        # execution since the "initialize" operation corresponds to creating 
        # a TensorFlow graph, which is a relatively expensive operation and 
        # should not be repeated across iterations if deconvolving more than 
        # one image
        res[i, :, 0] = algo.run(fd_data.Acquisition(data=tt488, kernel=kernel488), niter=niter).data
    
        tt640 = image[:,1]
        nonzero = tt640[np.where(tt640>0)]
        bkgd_mode = stats.mode(nonzero)[0][0]
        bkgd_std = stats.tstd(nonzero)
        indz,indy,indx = np.where(tt640==0)
        tt640[indz, indy, indx] = bkgd_mode + bkgd_std*np.random.randn(len(indz))
        # Note that deconvolution initialization is best kept separate from 
        # execution since the "initialize" operation corresponds to creating 
        # a TensorFlow graph, which is a relatively expensive operation and 
        # should not be repeated across iterations if deconvolving more than 
        # one image
        res[i, :, 1] = algo.run(fd_data.Acquisition(data=tt640, kernel=kernel640), niter=niter).data
    
    suffix = f"_scottdecon_niter{niter}_padding{pad_amount}.tif"
    output_file_str = input_file_str.replace(".tif", suffix)
    ####################
    # print('Done. Now writing to file\n')
    # # create numpy array with correct order
    # if is_single_time_pt:
    #     img5d = np.expand_dims(np.expand_dims(res, axis=1), axis=0) 
    # else:
    #     img5d = np.expand_dims(res, axis=1)
    # # write file and save OME-XML as description
    tifffile.imwrite(output_file_str, res.astype(np.uint16), imagej = True, metadata=mdata)
    print('All finished\n')