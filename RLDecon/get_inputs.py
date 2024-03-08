import numpy as np
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
    def __init__(self, root, title="Input", defaults=None, **kwargs):
        if defaults is None:
            defaults = {'image_file': '', 'csv_ch1': '', 'csv_ch2': 'none', 'channels':1}
        self.root = root

        self.defaults = defaults
        self.channel_mode = tk.IntVar(value=defaults['channels'])  # Default to 1 Channel
        
        super().__init__(root, title=title, **kwargs)
        

    def make_layout_flexible(self):
        # Configure the rows and columns to be flexible
        for i in range(5):  # Assuming you might have up to 4 rows; adjust as necessary
            self.master.grid_rowconfigure(i, weight=1)
        for j in range(3):  # Assuming up to 3 columns (label, entry, button)
            self.master.grid_columnconfigure(j, weight=1)

    def body(self, master):
        self.master = master
        default_folder = str(self.defaults['image_file'])
        tk.Label(self.master, text="Image file:").grid(row=0, column=0, sticky="w")
        self.image_file_entry = tk.Entry(self.master, width=50)
        self.image_file_entry.grid(row=0, column=1, sticky="ew")
        self.image_file_entry.insert(0, default_folder)
        tk.Button(self.master, text="Select", command=lambda: self.select_file(default_folder,self.image_file_entry, False)).grid(row=0, column=2)

        # Radio buttons for channel selection
        tk.Radiobutton(self.master, text="1 Channel", variable=self.channel_mode, value=1, command=lambda: self.update_csv_fields()).grid(row=1, column=0, sticky="w")
        tk.Radiobutton(self.master, text="2 Channels", variable=self.channel_mode, value=2, command=lambda: self.update_csv_fields()).grid(row=1, column=1, sticky="w")

        # Initially create one CSV entry field; adjust based on mode
        self.csv_entry_widgets = []
        self.csv_extra_widgets = []
        self.update_csv_fields()
        # self.make_layout_flexible(master)

    def select_file(self,default_folder,  entry_widget, csv):
        filepath = choose_image_file(self.master, default_folder= default_folder, title_message='Select a file', csv=csv)
        if filepath:
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, filepath)

    def update_csv_fields(self ):
        # Clear existing CSV fields and secondary widgets
        for widget in self.csv_entry_widgets:
            widget.grid_forget()

        for widget in self.csv_extra_widgets:
            widget.grid_forget()
            
        self.csv_entry_widgets.clear()
        self.csv_extra_widgets.clear()
        
        print(self.channel_mode.get())
        # Depending on the channel mode, create appropriate CSV file fields
        if self.channel_mode.get() == 1:
            self.create_csv_field("CSV file:", 2, self.defaults['csv_ch1'])
        elif self.channel_mode.get() == 2:
            self.create_csv_field("psf488 CSV file:", 2, self.defaults['csv_ch1'])
            self.create_csv_field("psf640 CSV file:", 3, self.defaults['csv_ch2'])

    def create_csv_field(self, label_text, row, default_value):
        # print(f'Creating field at row {row} with default value "{default_value}"')
        label = tk.Label(self.master, text=label_text)
        label.grid(row=row, column=0, sticky="w")
        # print(f'Label grid info: {label.grid_info()}')
        
        entry = tk.Entry(self.master)
        entry.grid(row=row, column=1, sticky="ew")
        entry.insert(0, str(default_value))
        # print(f'Entry grid info: {entry.grid_info()}')
    
        button = tk.Button(self.master, text="Select", command=lambda: self.select_file(label_text, entry, True))
        button.grid(row=row, column=2)
        # print(f'Button grid info: {button.grid_info()}')

        self.csv_extra_widgets.append(label)
        self.csv_entry_widgets.append(entry)
        self.csv_extra_widgets.append(button)


    def apply(self):

        self.result = {}
        invalid = False
        try:
            self.result = {'image_file': self.image_file_entry.get()}
            self.result['channels'] = self.channel_mode.get()
            if self.channel_mode.get() == 1:
                self.result['csv_ch1'] = self.csv_entry_widgets[0].get()
            elif self.channel_mode.get() == 2:
                self.result['csv_ch1'] = self.csv_entry_widgets[0].get()
                self.result['csv_ch2'] = self.csv_entry_widgets[1].get()
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
    return dialog.result, dialog.root

def get_multiple_numeric_inputs(master, title, defaults):
    dialog = MultipleInputNumericDialog(master, title, defaults=defaults)
    return dialog.result

def get_inputs():
    
    print("Num GPUs Available: ", len(tf.config.experimental.list_physical_devices('GPU')))

    
    root = tk.Tk()
    root.withdraw()  # Optionally hide the root window
    valid = False
    psfs = []
    
    while(not valid):
        try:
            default_inputs = { 'image_file': 'Z:/Shared243/storal/', 'csv_ch1': 'Z:/Shared243/storal/', 'csv_ch2': 'Z:/Shared243/storal/', 'channels':2}
            file_inputs, root = get_multiple_file_inputs(root, "File Inputs", default_inputs)
            if file_inputs is None:
                print('Cancelled.')
                root.destroy()
                return
            
            channels = int(file_inputs['channels'])
            
            input_file_str = file_inputs['image_file']

            
            psf_ch1_file_str = file_inputs['csv_ch1']
            psfs.append(np.genfromtxt(psf_ch1_file_str, delimiter=','))

            if channels == 2:
                psf_ch2_file_str = file_inputs['csv_ch2']
                psfs.append(np.genfromtxt(psf_ch2_file_str, delimiter=','))
                
            with tifffile.TiffFile(input_file_str) as tif:
                    mdata = tif.imagej_metadata
                    dat = tif.asarray()
            valid = True
            
        except OSError as e:
                # Handle the error (e.g., log it, inform the user)
                messagebox.showerror("Error", f"Failed to open file: {e}")
        except KeyError:
            # Handle KeyError here
            print("A Value was not selected.")
    
    numeric_defaults = {'z_spacing': mdata['spacing']*10, 'niter': 10, 'pad_amount': 16}
    numeric_inputs = get_multiple_numeric_inputs(root, "Numeric Inputs", numeric_defaults)
    if numeric_inputs is None:
        print('Cancelled.')
        root.destroy()
        return
    
    z_spacing = numeric_inputs['z_spacing']
    niter = numeric_inputs['niter']
    pad_amount = numeric_inputs['pad_amount']
    
    root.destroy()
    return [input_file_str, dat, mdata, psfs, z_spacing, niter, pad_amount, channels]


