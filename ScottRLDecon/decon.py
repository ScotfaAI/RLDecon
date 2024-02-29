import cupy as cp

def create_frequency_filter_3d(shape, cutoff):
    """
    Create a spherical low-pass frequency filter for 3D images using CuPy.

    Parameters:
    - shape: tuple, the shape of the filter (should match the image shape).
    - cutoff: float, the cutoff frequency as a fraction of the Nyquist frequency.

    Returns:
    - CuPy array: the frequency filter.
    """
    depth, rows, cols = shape
    center_depth, center_row, center_col = depth // 2, rows // 2, cols // 2
    z, y, x = cp.ogrid[:depth, :rows, :cols]
    distance_from_center = cp.sqrt((x - center_col)**2 + (y - center_row)**2 + (z - center_depth)**2)
    max_distance = cp.sqrt(center_col**2 + center_row**2 + center_depth**2)
    filter = cp.where(distance_from_center / max_distance <= cutoff, 1, 0)
    return filter

def regularized_richardson_lucy_with_cutoff_3d(image, psf, iterations, regularization_constant=1e-2, cutoff_frequency=0.5):
    """
    Perform Richardson-Lucy deconvolution in the frequency domain with regularization and high-frequency cutoff for 3D images using CuPy.

    Parameters:
    - image: CuPy array, the observed (blurred and noisy) 3D image.
    - psf: CuPy array, the point spread function for 3D.
    - iterations: int, the number of iterations to perform.
    - regularization_constant: float, a small constant to avoid division by zero in the frequency domain.
    - cutoff_frequency: float, the cutoff frequency as a fraction of the Nyquist frequency.

    Returns:
    - CuPy array: the deconvolved (restored) 3D image.
    """
    # Convert the PSF to OTF (Optical Transfer Function)
    otf = cp.fft.fftn(cp.fft.fftshift(psf), s=image.shape)

    # Apply high-frequency cutoff
    filter = create_frequency_filter_3d(image.shape, cutoff_frequency)
    otf *= filter

    # Add a small constant to the OTF to avoid division by zero
    otf = cp.where(otf == 0, regularization_constant, otf)

    # Fourier transform of the observed image
    observed_ft = cp.fft.fftn(image)

    # Initial guess is the observed image
    estimate_ft = observed_ft.copy()

    for _ in range(iterations):
        # Convolution via multiplication in the frequency domain
        estimated_image = cp.fft.ifftn(estimate_ft).real

        # Avoid division by zero or small numbers in the correction factor
        correction_factor = cp.maximum(cp.fft.ifftn(observed_ft / (estimate_ft + regularization_constant)).real, regularization_constant)

        # Update estimate in the frequency domain
        estimate_ft *= cp.fft.fftn(correction_factor) / (otf + regularization_constant)

    # Return the final estimate in the spatial domain
    return cp.fft.ifftn(estimate_ft).real

# Note: Convert your numpy arrays to cupy arrays before using them with this function.
# image_cp = cp.asarray(image)  # 'image' should be a 3D numpy array representing your 3D image
# psf_cp = cp.asarray(psf)      # 'psf' should be a 3D numpy array representing your 3D PSF
# deconvolved_image_cp = regularized_richardson_lucy_with_cutoff_3d(image_cp, psf_cp, iterations, regularization_constant, cutoff_frequency)
# deconvolved_image_np = cp.asnumpy(deconvolved_image_cp)  # Convert back to NumPy array if needed
