import numpy as np
import bioformats.omexml as ome
import tifffile
import sys
import argparse
import os
import logging
from scipy import ndimage, signal, stats
from math import floor, ceil
from flowdec import data as fd_data
from flowdec import psf as fd_psf
from flowdec import restoration as fd_restoration
from xml.etree import cElementTree as ElementTree
from tqdm import tqdm
import tensorflow as tf
import tkinter as tk
from tkinter import simpledialog, messagebox, filedialog


def choose_image_file(root, default_folder = '../', title_message ='Open an image file', csv = False):
    """Open a dialog to choose an image file and return the file path."""
    # This prevents the root Tkinter window from appearing
    


    default_file_type = ('Image files', '*.tif')
    
    if csv:
        default_file_type = ('PSF CSV files', '*.csv')
    
    
    # Define options for opening the file dialog
    filetypes = (
        default_file_type,
        ('All files', '*.*')
    )
    
    # Open the file dialog and get the selected file path
    filepath = filedialog.askopenfilename(
        title=title_message,
        initialdir=default_folder,
        filetypes=filetypes)

    return filepath

class MultipleInputFileDialog(simpledialog.Dialog):
    def __init__(self, master, title="Input", defaults=None, **kwargs):
        if defaults is None:
            defaults = {'image_file': 'Z:/Shared243/storal/', 'csv_488': 'Z:/Shared243/storal/', 'csv_640': 'Z:/Shared243/storal/'}

        self.root = master
        self.defaults = defaults
        super().__init__(master, title=title, **kwargs)

    def body(self, master):
        # Existing input fields setup...
        
        # Additional setup for file selection
        tk.Label(master, text="Image file:").grid(row=0, column=0, sticky="w")
        self.image_file_entry = tk.Entry(master)
        self.image_file_entry.grid(row=0, column=1, sticky="ew")
        self.image_file_entry.insert(0, str(self.defaults['image_file']))
        tk.Button(master, text="Select", command=self.select_image_file).grid(row=0, column=2)

        tk.Label(master, text="psf488 CSV file:").grid(row=1, column=0, sticky="w")
        self.csv_488_entry = tk.Entry(master)
        self.csv_488_entry.grid(row=1, column=1, sticky="ew")
        self.csv_488_entry.insert(0, str(self.defaults['csv_488']))
        tk.Button(master, text="Select", command=self.select_csv_488).grid(row=1, column=2)

        tk.Label(master, text="psf640 CSV file:").grid(row=2, column=0, sticky="w")
        self.csv_640_entry = tk.Entry(master)
        self.csv_640_entry.grid(row=2, column=1, sticky="ew")
        self.csv_640_entry.insert(0, str(self.defaults['csv_640']))
        tk.Button(master, text="Select", command=self.select_csv_640).grid(row=2, column=2)


        # Ensure the dialog is wide enough to fit the file paths
        master.grid_columnconfigure(1, weight=1)

    def select_image_file(self):
        filepath = choose_image_file(self.root, default_folder='Z:/Shared243/storal/', title_message='Open an image file', csv=False)
        if filepath:
            self.image_file_entry.delete(0, tk.END)
            self.image_file_entry.insert(0, filepath)

    def select_csv_488(self):
        filepath = choose_image_file(self.root, default_folder='Z:/Shared243/storal/', title_message='Select a CSV file', csv=True)
        if filepath:
            self.csv_488_entry.delete(0, tk.END)
            self.csv_488_entry.insert(0, filepath)

    def select_csv_640(self):
        filepath = choose_image_file(self.root, default_folder='Z:/Shared243/storal/', title_message='Select a CSV file', csv=True)
        if filepath:
            self.csv_640_entry.delete(0, tk.END)
            self.csv_640_entry.insert(0, filepath)

    def apply(self):
        # Existing apply method to handle other inputs...
        self.result = {}
        invalid = False
        try:
            self.result['image_file'] = self.image_file_entry.get()
            self.result['csv_488'] = self.csv_488_entry.get()
            self.result['csv_640'] = self.csv_640_entry.get()
            
        except ValueError:
            messagebox.showwarning("Invalid input", "Please enter valid file paths.")
            self.result = None

class MultipleInputNumericDialog(simpledialog.Dialog):
    def __init__(self, master, title="Input", defaults=None, **kwargs):
        if defaults is None:
            defaults = {'z_spacing': mdata['spacing']*10, 'niter': 10, 'pad_amount': 16}
        self.defaults = defaults
        super().__init__(master, title=title, **kwargs)

    def body(self, master):
        # Existing input fields setup...

        tk.Label(master, text="Z spacing of Image:").grid(row=0, column=0, sticky="w")
        self.z_spacing_entry = tk.Entry(master)
        self.z_spacing_entry.grid(row=0, column=1)
        self.z_spacing_entry.insert(0, str(self.defaults['z_spacing']))

        tk.Label(master, text="Number of RL iterations:").grid(row=1, column=0, sticky="w")
        self.niter_entry = tk.Entry(master)
        self.niter_entry.grid(row=1, column=1)
        self.niter_entry.insert(0, str(self.defaults['niter']))

        tk.Label(master, text="Padding amount:").grid(row=2, column=0, sticky="w")
        self.pad_amount_entry = tk.Entry(master)
        self.pad_amount_entry.grid(row=2, column=1)
        self.pad_amount_entry.insert(0, str(self.defaults['pad_amount']))

        # Ensure the dialog is wide enough to fit the file paths
        master.grid_columnconfigure(1, weight=1)



    def apply(self):
        # Existing apply method to handle other inputs...
        self.result = {}
        try:
            self.result['z_spacing'] = float(self.z_spacing_entry.get()),
            self.result['niter'] = int(self.niter_entry.get()),
            self.result['pad_amount'] = int(self.pad_amount_entry.get())
            
        except ValueError:
            messagebox.showwarning("Invalid input", "Please enter valid numbers.")
            self.result = None
        

def get_multiple_file_inputs(master, title, defaults):
    dialog = MultipleInputFileDialog(master, title, defaults=defaults)
    return dialog.result

def get_multiple_numeric_inputs(master, title, defaults):
    dialog = MultipleInputNumericDialog(master, title, defaults=defaults)
    return dialog.result

def get_inputs():
    
    print("Num GPUs Available: ", len(tf.config.experimental.list_physical_devices('GPU')))

    
    root = tk.Tk()
    root.withdraw()  # Optionally hide the root window
    valid = False
    while(not valid):
        try:
            
            file_defaults = { 'image_file': 'Z:/Shared243/storal/', 'csv_488': 'Z:/Shared243/storal/', 'csv_640': 'Z:/Shared243/storal/'}
            file_inputs = get_multiple_file_inputs(root, "File Inputs", file_defaults)
            
            input_file_str = file_inputs['image_file']
            bead488_image_file_str = file_inputs['csv_488']
            bead640_image_file_str = file_inputs['csv_640']
            
            psf488 = np.genfromtxt(bead488_image_file_str, delimiter=',')
            psf640 = np.genfromtxt(bead640_image_file_str, delimiter=',')
            with tifffile.TiffFile(input_file_str) as tif:
                    mdata = tif.imagej_metadata
                    dat = tif.asarray()
            valid = True
            
        except OSError as e:
                # Handle the error (e.g., log it, inform the user)
                messagebox.showerror("Error", f"Failed to open file: {e}")
    
    numeric_defaults = {'z_spacing': mdata['spacing']*10, 'niter': 10, 'pad_amount': 16}
    numeric_inputs = get_multiple_numeric_inputs(root, "Numeric Inputs", numeric_defaults)
    z_spacing = numeric_inputs['z_spacing']
    niter = numeric_inputs['niter']
    pad_amount = numeric_inputs['pad_amount']
    
    root.destroy()
    return input_file_str, dat, mdata, psf488, psf640, z_spacing, niter, pad_amount


