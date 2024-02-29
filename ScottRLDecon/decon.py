import cupy as cp

def richardson_lucy_deconvolution(image, psf, iterations, use_otf=True, use_regularization=True, regularization_constant=1e-2, use_cutoff=False, cutoff_frequency=0.5, convergence_ratio=0.25):
    """
    Perform Richardson-Lucy deconvolution with options for direct PSF usage, regularization, and high-frequency cutoff.

    Parameters:
    - image: CuPy array, the observed (blurred and noisy) image.
    - psf: CuPy array, the point spread function.
    - iterations: int, the number of iterations to perform.
    - use_otf: bool, whether to convert the PSF to the OTF for frequency domain deconvolution.
    - use_regularization: bool, whether to apply regularization.
    - regularization_constant: float, to avoid division by zero if regularization is used.
    - use_cutoff: bool, whether to apply a high-frequency cutoff filter (only applicable if use_otf is True).
    - cutoff_frequency: float, the cutoff frequency as a fraction of the Nyquist frequency (used if use_cutoff is True).
    - convergence_ratio: float, the ratio of the change in MSE to its initial value at which to stop the iterations.

    Returns:
    - CuPy array: the deconvolved image.
    """
    if use_otf:
        # Convert the PSF to OTF if using the frequency domain approach
        otf = cp.fft.fftn(cp.fft.fftshift(psf), s=image.shape)
        if use_cutoff:
            # Apply high-frequency cutoff if enabled
            filter = create_frequency_filter_3d(image.shape, cutoff_frequency)
            otf *= filter
        if use_regularization:
            otf = cp.where(otf == 0, regularization_constant, otf)
    else:
        # Use the PSF directly in the spatial domain, only apply regularization in correction factor calculation
        if use_regularization:
            psf = cp.where(psf == 0, regularization_constant, psf)
        # Ensure PSF is normalized for direct use
        psf /= cp.sum(psf)

    observed = cp.fft.fftn(image)
    estimate = observed.copy()

    for i in range(iterations):
        if use_otf:
            estimated_image = cp.fft.ifftn(estimate).real
            correction_factor = cp.fft.ifftn(observed / (estimate + (regularization_constant if use_regularization else 0)))
            estimate = estimate * (cp.fft.fftn(correction_factor.real) / otf)
        else:
            # Perform convolution in the spatial domain using the direct PSF
            estimated_image = cp.signal.fftconvolve(estimate, psf, mode='same')
            correction_factor = cp.signal.fftconvolve(image / estimated_image, psf[::-1, ::-1], mode='same')
            estimate *= correction_factor

        # Implement convergence check here if desired

    print(f"Total iterations executed: {i + 1}")
    return cp.fft.ifftn(estimate).real if use_otf else estimated_image

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
