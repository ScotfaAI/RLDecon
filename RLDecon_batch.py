import warnings
# warnings.simplefilter(action='ignore', category=FutureWarning)



from RLDecon.get_inputs_batch import get_inputs_batch
from RLDecon.get_inputs import get_inputs
from RLDecon.run_decon_debug import run_decon

batch = True
debug = False
if batch:
    variables = get_inputs_batch()
else:
    variables = get_inputs()
    

# print(variables)
if variables is not None:
    

    if batch:
        [input_files, dats, mdata, psfs, x_res, y_res, z_spacing, niter, pad_amount, channel] = variables
        run_decon(input_files, dats, mdata, psfs, x_res, y_res, z_spacing[0], niter[0], pad_amount, channel, debug)

    