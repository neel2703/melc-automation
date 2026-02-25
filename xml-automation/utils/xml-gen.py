from math import nan
import os
import pandas as pd
import numpy as np
from lxml import etree
import json

xml_file = 'xml-automation/automatic_xml_creator/template_base.xml'
xl_file = pd.read_excel('xml-automation/automatic_xml_creator/Template_Juergen_Sandy_test.xlsx', sheet_name=None)
run_settings_df = xl_file['Run_settings']
marker_df = xl_file['MELC_panel']

with open('xml-automation/utils/mapper.json', 'r') as f:
    mapper = json.load(f)

# Parse the template XML file
tree = etree.parse(xml_file)
root = tree.getroot()
ns = 'http://www.meltec.de/2004/xschema'
xlink_ns = 'http://www.w3.org/1999/xlink'

def tag(name):
    return f'{{{ns}}}{name}'

# slice the marker_df to only include the rows where the second column is not empty
xl_file_clean = marker_df.iloc[1:].copy()
xl_file_clean = xl_file_clean.dropna(subset=[xl_file_clean.columns[1]])
xl_file_clean.iloc[:, 0] = xl_file_clean.iloc[:, 0].ffill() # fill the first column with the previous value to make it easier for reading the data when grouped
xl_file_clean.iloc[:, 7] = xl_file_clean.iloc[:, 7].ffill()

groups = list(xl_file_clean.groupby(xl_file_clean.iloc[:, 0]))
step_count = len(groups)
visual_field_count = int(run_settings_df.columns[1])
img_count = int(run_settings_df.iloc[0,1])

# run_setting xml elements
run_setting = root.find(tag('runSetting'))
if run_setting is not None:
    sc_elem = run_setting.find(tag('stepCount'))
    if sc_elem is not None:
        sc_elem.text = str(step_count)
    vfc_elem = run_setting.find(tag('visualFieldCount'))
    if vfc_elem is not None:
        vfc_elem.text = str(visual_field_count)
    for vfc in run_setting.findall(tag('visualFieldConfig')):
        stack = vfc.find(tag('stack'))
        if stack is not None:
            neg = stack.find(tag('imageCountNegative'))
            if neg is not None:
                neg.text = str(img_count)
            pos = stack.find(tag('imageCountPositive'))
            if pos is not None:
                pos.text = str(img_count)

# function to add a channelStep element
def add_channel_step(parent, step_num, marker_full, bleachtime, bleachcycle, fluorescence_filter, bleach_filter, marker_conc):
    """Helper to add a channelStep element."""
    channel_elem = etree.SubElement(parent, 'channelStep', stepNumber=str(step_num))
    etree.SubElement(channel_elem, 'type').text = 'full'
    etree.SubElement(channel_elem, 'exposureTime').text = '450'
    etree.SubElement(channel_elem, 'bleachTime').text = str(bleachtime)
    etree.SubElement(channel_elem, 'bleachCycle').text = str(bleachcycle)
    marker_elem = etree.SubElement(channel_elem, 'marker', name=marker_full)
    marker_elem.set('{http://www.w3.org/1999/xlink}href', 'URN:LSID:lsid.meltec.de:marker:1002')
    etree.SubElement(channel_elem, 'markerConcentration').text = marker_conc
    fluor_elem = etree.SubElement(channel_elem, 'fluorescenceFilter', name=str(fluorescence_filter))
    fluor_elem.set('{http://www.w3.org/1999/xlink}href', 'URN:LSID:lsid.meltec.de:filter:1')
    bleach_elem = etree.SubElement(channel_elem, 'bleachFilter', name=str(bleach_filter))
    bleach_elem.set('{http://www.w3.org/1999/xlink}href', 'URN:LSID:lsid.meltec.de:filter:1')
    etree.SubElement(channel_elem, 'stopAfterImaging').text = 'false'


# Process each incStep
for idx, (incstep_count, group) in enumerate(groups):
    incstep_count = int(incstep_count)

    # Dyes in current group
    current_dyes = set()
    for _, row in group.iterrows():
        dye = row.iloc[2]
        if pd.notna(dye):
            current_dyes.add(str(dye).strip())

    # Dyes in next group (for prep): if a dye in next step wasn't used in current, add prep channelStep
    next_dyes = set()
    if idx + 1 < len(groups):
        next_group = groups[idx + 1][1]
        for _, row in next_group.iterrows():
            dye = row.iloc[2]
            if pd.notna(dye):
                next_dyes.add(str(dye).strip())
    dyes_to_prep = next_dyes - current_dyes

    # Get well info from first row
    first_row = group.iloc[0]
    well_let = 'A'  # Default values
    well_num = '1'
    if pd.notna(first_row.iloc[3]):
        well = first_row.iloc[3]
        well_let, well_num = well[0], well[1:]
    
    incubation_time = int(group.iloc[0, 7])

    # Create incStep element
    incstep_elem = etree.SubElement(root, 'incStep', stepNumber=str(incstep_count))
    
    # Add incStep children
    etree.SubElement(incstep_elem, 'incTime').text = str(incubation_time)
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
    for _, row in group.iterrows():
        bleachtime = int(row.iloc[8])
        bleachcycle = bleachtime // 100
        marker = row.iloc[1]
        dye = row.iloc[2]
        fluorescenceFilter = mapper.get(dye)
        bleachFilter = fluorescenceFilter
        marker_full = f"{marker}-{dye}_450"
        marker_conc = row.iloc[5]
        marker_conc = "1:" + str(marker_conc)
        add_channel_step(incstep_elem, channel_step_num, marker_full, bleachtime, bleachcycle, fluorescenceFilter, bleachFilter, marker_conc)
        channel_step_num += 1

    # Add prep channelSteps for dyes used in next step but not in current
    for dye in sorted(dyes_to_prep):
        fluorescenceFilter = mapper.get(dye)
        bleachFilter = fluorescenceFilter
        marker_full = f"PBS-{dye}_450"
        add_channel_step(incstep_elem, channel_step_num, marker_full, 0, 0, fluorescenceFilter, bleachFilter, "1")
        channel_step_num += 1

# Write the XML to file (indent ensures generated incSteps are properly formatted)
etree.indent(tree, space="  ")
tree.write('output_new_test.xml', pretty_print=True, xml_declaration=True, encoding='UTF-8')

print("XML file created successfully: output.xml")