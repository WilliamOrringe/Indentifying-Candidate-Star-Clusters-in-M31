import pandas as pd
from astropy.coordinates import SkyCoord
from astropy import units as u
import glob

# Read in catalog data
catalog = pd.read_csv('observations.txt', delimiter=' ')
master_catalog = pd.read_csv('master_updated2.csv', delimiter=',')
print(master_catalog)
print('Starting loop...')

# Loop over unique FieldIDs
counter = 0
master_catalog_coords = SkyCoord(ra=master_catalog['RADEG'], dec=master_catalog['DECDEG'], unit=(u.deg, u.deg))
total = len(master_catalog_coords)
ra_deg = (catalog['RAh']) * 15 + (catalog['RAm']) * 0.25 + (catalog['RAs']) * 0.00416667
dec_deg = (catalog['DEd']) + ((catalog['DEm'])/60) + ((catalog['DEs'])/3600)
catalog_coord = SkyCoord(ra=ra_deg * u.deg, dec=dec_deg * u.deg)
# print(len(master_catalog_coords))
for index in range(total):
    # Find matching file based on FieldID
    idx, d2d, _ = master_catalog_coords[index].match_to_catalog_sky(catalog_coord)
    # print(catalog.loc[idx])
    field_id = catalog.loc[idx]['FieldID']
    file_path = f'Cleaned/c{field_id}p.ascd'
    if not glob.glob(file_path):
        print(f'Error: File not found for FieldID {field_id}')
        continue
    # Read in file data
    file_data = pd.read_csv(file_path, delimiter=' ')
    print('+=================+')
    print('Processing : ', field_id, '(', index, ' / ', total,')')
    file_coords = SkyCoord(ra=file_data['RA'], dec=file_data['Dec'], unit=(u.hourangle, u.deg))
    idx, _, _ = master_catalog_coords[index].match_to_catalog_sky(file_coords)
    # print(file_coords.loc[idx])
    i_value = file_data.loc[idx, 'i']
    g_value = file_data.loc[idx, 'g']
    # Add i and g values to catalog
    master_catalog.at[index, 'i'] = i_value
    master_catalog.at[index, 'g'] = g_value
    print('Coords Processed')
    master_catalog.to_csv('master_updated3.csv', index=False)
# Write out updated catalog
print('Outputing to csv')
master_catalog.to_csv('master_updated.csv', index=False)
print('Done!')
