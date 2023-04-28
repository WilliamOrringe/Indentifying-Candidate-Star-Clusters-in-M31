from multiprocessing import freeze_support, Pool, Manager

import pandas as pd
from astropy.coordinates import SkyCoord
from astropy import units as u
import glob
from concurrent.futures import ProcessPoolExecutor
from tqdm import tqdm


def process_field(index):
    idx, d2d, _ = master_catalog_coords[index].match_to_catalog_sky(catalog_coord)
    field_id = catalog.loc[idx]['FieldID']
    file_path = f'very_clean/c{field_id}p.ascd'
    if not glob.glob(file_path):
        print(f'Error: File not found for FieldID {field_id}')
        return
    file_data = pd.read_csv(file_path, delimiter=' ')
    # print('+=================+')
    # print('Processing : ', field_id, '(', index, ' / ', total ,')')
    file_coords = SkyCoord(ra=file_data['RA'], dec=file_data['Dec'], unit=(u.hourangle, u.deg))
    idx, _, _ = master_catalog_coords[index].match_to_catalog_sky(file_coords)
    i_value = file_data.loc[idx, 'i']
    g_value = file_data.loc[idx, 'g']
    master_catalog.at[index, 'i'] = i_value
    master_catalog.at[index, 'g'] = g_value
    # print('Coords Processed')
    master_catalog.to_csv('very_clean_outputs/master_very_clean_catalog1.csv', index=False)
    return field_id, file_coords

catalog = pd.read_csv('observations.txt', delimiter=' ')
master_catalog = pd.read_csv('master_catalog_jan_2023.csv', delimiter=',')
# print(master_catalog)
# print('Starting loop...')

# Loop over unique FieldIDs
counter = 0
master_catalog_coords = SkyCoord(ra=master_catalog['RADEG'], dec=master_catalog['DECDEG'], unit=(u.deg, u.deg))
total = len(master_catalog_coords)
ra_deg = (catalog['RAh']) * 15 + (catalog['RAm']) * 0.25 + (catalog['RAs']) * 0.00416667
dec_deg = (catalog['DEd']) + ((catalog['DEm']) / 60) + ((catalog['DEs']) / 3600)
catalog_coord = SkyCoord(ra=ra_deg * u.deg, dec=dec_deg * u.deg)
field_data_dict = {}
if __name__ == "__main__":
    freeze_support()
    # Read in catalog data

    field_coords = Manager().dict()
    # Use a process pool executor to parallelize the processing of field IDs
    with Pool() as p:
        for result in tqdm(p.imap_unordered(process_field, range(total)), total=total):
            if result is not None:
                field_coords[result[0]] = result[1]

    # Write out updated catalog
    print('Outputting to csv')
    master_catalog.to_csv('master_very_clean_catalog.csv', index=False)
    print('Done!')
