# Richardson lucy deconvolution for ImageJ 5D tifs
Authors: Scott Brooks and Sara Toral Perez

## Installation
`git clone https://github.com/scottbrooks98/RLDecon`

`cd <repo>`

`conda env create -f environment.yml`

## How to run this:
Open anaconda prompt

`conda activate flowdecimport`

`python C:\Users\u1604360\Documents\GitHub\RLDecon\RLDecon.py`

## Project Requirements
- It should take in imageJ tifs not ome.tiffs - DONE
- It should take in 2 channel images and produce a deconvolution as a single tif - DONE
- Add a file chooser - DONE
- Step size entry, with default and reference to mdata DONE
- change the padding method (currently padded with 0s)
- change the number of iterations DONE
- 
  
## Advanced
- Choose between Jonathan vs Scott fitting vs raw PSF
- threading
- output at every 5 iterations
- output ome.tiff as well

### Averaging specify a folder
- Raw PSF Averaging
- sigma averaging


to get new z spacing after deskewing on warwick llsm, spacing*cos(57.2)

To run currently boot up flowdec anaconda
