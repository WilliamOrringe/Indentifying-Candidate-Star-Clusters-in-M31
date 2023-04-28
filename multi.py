import pandas as pd
from astropy.coordinates import SkyCoord
from astropy import units as u
import glob
import concurrent.futures

# Read in catalog data
catalog = pd.read_csv('observations.txt', delimiter=' ')
master_catalog = pd.read_csv('master_catalog_jan_2023.csv', delimiter=',')
print(master_catalog)
print('Starting loop...')


# Define a function to process a single field
def process_field(index):
    global master_catalog, catalog, field_data, master_catalog_coords, catalog_coord
    idx, d2d, _ = master_catalog_coords[index].match_to_catalog_sky(catalog_coord)

    # Get the field ID and check if the corresponding file exists
    field_id = catalog.loc[idx]['FieldID']
    file_path = f'cleaned_half/c{field_id}p.ascd'

    if not glob.glob(file_path):
        print(f'Error: File not found for FieldID {field_id}')
        return

    # Read in file data
    if field_id not in field_data:
        field_data[field_id] = pd.read_csv(file_path, delimiter=' ')
    file_data = field_data[field_id]
    print('+=================+')
    print('Processing : ', field_id, '(', index, ' / ', total, ')')
    file_coords = SkyCoord(ra=file_data['RA'], dec=file_data['Dec'], unit=(u.hourangle, u.deg))
    idx, _, _ = master_catalog_coords[index].match_to_catalog_sky(file_coords)
    i_value = file_data.loc[idx, 'i']
    g_value = file_data.loc[idx, 'g']
    # Add i and g values to catalog
    master_catalog.at[index, 'i'] = i_value
    master_catalog.at[index, 'g'] = g_value
    print('Coords Processed')


# Loop over unique FieldIDs
counter = 0
master_catalog_coords = SkyCoord(ra=master_catalog['RADEG'], dec=master_catalog['DECDEG'], unit=(u.deg, u.deg))
total = len(master_catalog_coords)
ra_deg = (catalog['RAh']) * 15 + (catalog['RAm']) * 0.25 + (catalog['RAs']) * 0.00416667
dec_deg = (catalog['DEd']) + ((catalog['DEm']) / 60) + ((catalog['DEs']) / 3600)
catalog_coord = SkyCoord(ra=ra_deg * u.deg, dec=dec_deg * u.deg)
field_data = {}

# Define the number of threads to use
num_threads = 8

# Process the fields using multiple threads
with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
    futures = []
    for index in range(total):
        future = executor.submit(process_field, index)
        futures.append(future)
    concurrent.futures.wait(futures)

# Write out updated catalog
print('Outputting to csv')
master_catalog.to_csv('cleaned_half/master_updated.csv', index=False)
print('Done!')
