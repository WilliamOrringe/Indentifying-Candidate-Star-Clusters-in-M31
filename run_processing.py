import pandas as pd
from astropy.coordinates import SkyCoord
from astropy import units as u
import glob
from concurrent.futures import ThreadPoolExecutor

# Read in catalog data
catalog = pd.read_csv('observations.txt', delimiter=' ')
print('Starting loop...')


def process_field(field_id):
    # Find matching file based on FieldID
    file_path = f'very_clean/c{field_id}p.ascd'
    if not glob.glob(file_path):
        print(f'Error: File not found for FieldID {field_id}')
        return None
    # Read in file data
    file_data = pd.read_csv(file_path, delimiter=' ')
    print('+=================+')
    print('Processing : ', field_id, '(', counter, ' / ', total, ')')
    file_coords = SkyCoord(ra=file_data['RA'], dec=file_data['Dec'], unit=(u.hourangle, u.deg))
    file_coords = SkyCoord(file_coords)
    print('File Coords Processed')
    # Loop over catalog data for this FieldID
    for index, row in catalog[catalog['FieldID'] == field_id].iterrows():
        # Create SkyCoord object for catalog data
        ra_deg = float(row['RAh']) * 15 + float(row['RAm']) * 0.25 + float(row['RAs']) * 0.00416667
        dec_deg = float(row['DEd']) + (float(row['DEm']) / 60) + (float(row['DEs']) / 3600)
        catalog_coord = SkyCoord(ra=ra_deg * u.deg, dec=dec_deg * u.deg)
        # Find the closest match in file data
        idx, d2d, _ = catalog_coord.match_to_catalog_sky(file_coords)
        # Get i and g values for closest match
        i_value = file_data.loc[idx, 'i']
        g_value = file_data.loc[idx, 'g']
        # Add i and g values to catalog
        catalog.at[index, 'i'] = i_value
        catalog.at[index, 'g'] = g_value
    print('Matched Coords.')
    catalog.to_csv(f'very_clean_outputs/catalog_updated_{field_id}.csv', index=False)


total = len(catalog['FieldID'].unique())
counter = 0
with ThreadPoolExecutor(max_workers=4) as executor:
    futures = []
    for field_id in catalog['FieldID'].unique():
        futures.append(executor.submit(process_field, field_id))
        counter += 1
        print(f"Started task for field ID {field_id} ({counter} / {total})")
    for future in futures:
        result = future.result()

# Write out updated catalog
print('Done!')
catalog.to_csv('very_clean_master_catalog.csv', index=False)
