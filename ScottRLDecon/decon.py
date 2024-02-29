import cupy as cp

def regularized_richardson_lucy(image, psf, iterations, use_regularization=True, regularization_constant=1e-2, use_cutoff=False, cutoff_frequency=0.5, convergence_ratio=0.25):
    """
    Perform Richardson-Lucy deconvolution with optional regularization and high-frequency cutoff filter.

    Parameters:
    - image: CuPy array, the observed (blurred and noisy) 3D image.
    - psf: CuPy array, the 3D point spread function.
    - iterations: int, the maximum number of iterations to perform.
    - use_regularization: bool, whether to apply regularization.
    - regularization_constant: float, to avoid division by zero in the frequency domain if regularization is used.
    - use_cutoff: bool, whether to apply a high-frequency cutoff filter.
    - cutoff_frequency: float, the cutoff frequency as a fraction of the Nyquist frequency (used if use_cutoff is True).
    - convergence_ratio: float, the ratio of the change in MSE to its initial value at which to stop the iterations.

    Returns:
    - CuPy array: the deconvolved (restored) 3D image.
    """
    # Convert the PSF to OTF (Optical Transfer Function)
    otf = cp.fft.fftn(cp.fft.fftshift(psf), s=image.shape)
    if use_cutoff:
        filter = create_frequency_filter_3d(image.shape, cutoff_frequency)
        otf *= filter

    if use_regularization:
        otf = cp.where(otf == 0, regularization_constant, otf)  # Apply regularization
    else:
        otf = cp.where(otf == 0, 0, otf)  # Avoid modifying OTF if regularization is not used

    observed_ft = cp.fft.fftn(image)
    estimate_ft = observed_ft.copy()
    initial_mse_change = None
    previous_estimate = None

    for i in range(iterations):
        estimated_image = cp.fft.ifftn(estimate_ft).real
        if use_regularization:
            correction_factor = cp.maximum(cp.fft.ifftn(observed_ft / (estimate_ft + regularization_constant)).real, regularization_constant)
        else:
            correction_factor = cp.fft.ifftn(observed_ft / estimate_ft).real

        estimate_ft *= cp.fft.fftn(correction_factor) / otf

        if previous_estimate is not None:
            mse_change = cp.mean((estimated_image - previous_estimate) ** 2)
            if i == 1:
                initial_mse_change = mse_change
            elif mse_change < initial_mse_change * convergence_ratio:
                print(f"Convergence reached at iteration {i}.")
                break
        previous_estimate = estimated_image.copy()

    print(f"Total iterations executed: {i + 1}")
    return estimated_image

def create_frequency_filter_3d(shape, cutoff):
    depth, rows, cols = shape
    center_depth, center_row, center_col = depth // 2, rows // 2, cols // 2
    z, y, x = cp.ogrid[:depth, :rows, :cols]
    distance_from_center = cp.sqrt((x - center_col)**2 + (y - center_row)**2 + (z - center_depth)**2)
    max_distance = cp.sqrt(center_col**2 + center_row**2 + center_depth**2)
    filter = cp.where(distance_from_center / max_distance <= cutoff, 1, 0)
    return filter

# Assuming `image` and `psf` are CuPy arrays of the observed image and PSF, respectively
iterations = 10
use_regularization = False  # Disable regularization
use_cutoff = False  # Optionally, disable the cutoff filter as well

deconvolved_image = regularized_richardson_lucy(image, psf, iterations, use_regularization, use_cutoff=use_cutoff)

# Convert back to NumPy array if necessary for further processing/display
# deconvolved_image_np = cp.asnumpy(deconvolved_image)
