from math import nan
import pandas as pd
import numpy as np 
from lxml import etree
import json

xml_file = 'xml-automation/automatic_xml_creator/20260212_mu_Lung_GATA3eGFP_3FOVs_Juergen.xml'
xl_file = pd.read_excel('xml-automation/automatic_xml_creator/20260212_mu_Lung_GATA3eGFP_3FOVs_Juergen.xlsx')

with open('xml-automation/utils/mapper.json', 'r') as f:
    mapper = json.load(f)

# Parse the template XML file
tree = etree.parse(xml_file)
root = tree.getroot()

xl_file_clean = xl_file.iloc[2:].copy()
xl_file_clean = xl_file_clean.dropna(subset=[xl_file_clean.columns[1]])
xl_file_clean.iloc[:, 0] = xl_file_clean.iloc[:, 0].ffill()

# Process each incStep
for incstep_count, group in xl_file_clean.groupby(xl_file_clean.iloc[:, 0]):
    incstep_count = int(incstep_count)
    
    # Get well info from first row
    first_row = group.iloc[0]
    well_let = 'A'  # Default values
    well_num = '1'
    if pd.notna(first_row.iloc[5]):
        well = first_row.iloc[5]
        well_let, well_num = well[0], well[1:]
    
    # Create incStep element
    incstep_elem = etree.SubElement(root, 'incStep', stepNumber=str(incstep_count))
    
    # Add incStep children
    etree.SubElement(incstep_elem, 'incTime').text = '3000'
    etree.SubElement(incstep_elem, 'pipVolume').text = '100'
    etree.SubElement(incstep_elem, 'pipABRatio').text = '50'
    etree.SubElement(incstep_elem, 'pipABMixCount').text = '1'
    etree.SubElement(incstep_elem, 'cleanCycle').text = '30'
    etree.SubElement(incstep_elem, 'noImaging').text = 'false'
    
    # Add well element
    well_elem = etree.SubElement(incstep_elem, 'well', plateName="AK96_1_1")
    plateLSID = etree.SubElement(well_elem, 'plateLSID')
    plateLSID.set('{http://www.w3.org/1999/xlink}href', 'URN:LSID:lsid.meltec.de:plate:2')
    etree.SubElement(well_elem, 'letter').text = well_let
    etree.SubElement(well_elem, 'number').text = str(well_num)
    etree.SubElement(well_elem, 'volume').text = '60'
    
    # Process each channelStep
    channel_step_num = 1
    for i, row in group.iterrows():
        bleachtime = int(row.iloc[12])
        bleachcycle = bleachtime // 100
        marker = row.iloc[1]
        dye = row.iloc[2]
        fluorescenceFilter = mapper.get(dye)
        bleachFilter = fluorescenceFilter
        marker_full = f"{marker}-{dye}_450"
        
        # Create channelStep element
        channel_elem = etree.SubElement(incstep_elem, 'channelStep', stepNumber=str(channel_step_num))
        
        etree.SubElement(channel_elem, 'type').text = 'full'
        etree.SubElement(channel_elem, 'exposureTime').text = '450'
        etree.SubElement(channel_elem, 'bleachTime').text = str(bleachtime)
        etree.SubElement(channel_elem, 'bleachCycle').text = str(bleachcycle)
        
        marker_elem = etree.SubElement(channel_elem, 'marker', name=marker_full)
        marker_elem.set('{http://www.w3.org/1999/xlink}href', 'URN:LSID:lsid.meltec.de:marker:1002')
        
        etree.SubElement(channel_elem, 'markerConcentration').text = '1:50'
        
        fluor_elem = etree.SubElement(channel_elem, 'fluorescenceFilter', name=str(fluorescenceFilter))
        fluor_elem.set('{http://www.w3.org/1999/xlink}href', 'URN:LSID:lsid.meltec.de:filter:1')
        
        bleach_elem = etree.SubElement(channel_elem, 'bleachFilter', name=str(bleachFilter))
        bleach_elem.set('{http://www.w3.org/1999/xlink}href', 'URN:LSID:lsid.meltec.de:filter:1')
        
        etree.SubElement(channel_elem, 'stopAfterImaging').text = 'false'
        
        channel_step_num += 1

# Write the XML to file
tree.write('output.xml', pretty_print=True, xml_declaration=True, encoding='UTF-8')

print("XML file created successfully: output.xml")