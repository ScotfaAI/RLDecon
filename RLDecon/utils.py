import xml.etree.ElementTree as ET

def get_mdata(xml_data):
    # Parse the XML string
    root = ET.fromstring(xml_data)
    
    # Define the XML namespace to access the elements properly
    namespace = {'ome': 'http://www.openmicroscopy.org/Schemas/OME/2016-06'}
    
    # Find the 'Pixels' element
    pixels_element = root.find('.//ome:Pixels', namespaces=namespace)
    
    # Extracting metadata
    slices = int(pixels_element.attrib['SizeZ'])
    frames = int(pixels_element.attrib['SizeT'])
    spacing = float(pixels_element.attrib['PhysicalSizeZ'])
    images = int(pixels_element.attrib['SizeX']) * int(pixels_element.attrib['SizeY']) * slices * frames * int(pixels_element.attrib['SizeC'])
    
    # Constructing the metadata dictionary
    mdata = {
        'images': images,
        'slices': slices,
        'frames': frames,
        'hyperstack': True,
        'unit': 'micron',
        'spacing': spacing,
        'loop': False
    }
    
    return mdata
