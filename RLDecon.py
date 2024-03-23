import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)
from RLDecon import get_inputs, run_5d_decon

variables = get_inputs()
if variables is not None:
    [input_file_str, dat, mdata, psfs, x_res, y_res, z_spacing, niter, pad_amount, channel] = variables
    run_5d_decon(input_file_str, dat, mdata, psfs, x_res, y_res, z_spacing[0], niter[0], pad_amount, channel)
