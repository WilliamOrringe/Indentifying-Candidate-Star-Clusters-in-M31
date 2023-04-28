# import pandas as pd
# from astropy.coordinates import SkyCoord
# from astropy import units as u
# import glob
# import os
# from scipy.spatial import cKDTree
# from tqdm import tqdm
#
# # Read in catalog data
# catalog = pd.read_csv('observations.txt', delimiter=' ')
# master_catalog = pd.read_csv('mastercopy.csv', delimiter=',')
# print(master_catalog)
# print('Starting loop...')
#
# # Create dictionary of SkyCoord objects for each FieldID
# field_coords = {}
# with tqdm(total=len(catalog['FieldID'].unique())) as first_bar:
#     for field_id in catalog['FieldID'].unique():
#         file_path = os.path.join('Cleaned', f'c{field_id}p.ascd')
#         if not glob.glob(file_path):
#             print(f'Error: File not found for FieldID {field_id}')
#             continue
#         file_data = pd.read_csv(file_path, delimiter=' ')
#         field_coords[field_id] = SkyCoord(ra=file_data['RA'], dec=file_data['Dec'], unit=(u.hourangle, u.deg))
#         first_bar.update(1)
# # Build a KDTree from the SkyCoord objects in field_coords
# kdtrees = {}
# for field_id, coords in field_coords.items():
#     kdtrees[field_id] = cKDTree(coords.cartesian.xyz.value.T)

# # Loop over unique FieldIDs
# master_catalog_coords = SkyCoord(ra=master_catalog['RADEG'], dec=master_catalog['DECDEG'], unit=(u.deg, u.deg))
# catalog_coord = SkyCoord(ra=(catalog['RAh']*15 + catalog['RAm']*0.25 + catalog['RAs']*0.00416667) * u.deg,
#                          dec=(catalog['DEd'] + catalog['DEm']/60 + catalog['DEs']/3600) * u.deg)
# with tqdm(total=len(master_catalog_coords)) as pbar:
#     for index, row in master_catalog_coords.iterrows():
#         # Find matching file based on FieldID
#         idx, d2d, _ = row.match_to_catalog_sky(catalog_coord)
#         field_id = catalog.loc[idx]['FieldID']
#         kdtree = kdtrees.get(field_id, None)
#         if kdtree is None:
#             print(f'Error: KDTree not found for FieldID {field_id}')
#             continue
#         # Use the KDTree to find the nearest point in the field's coordinates
#         idx = kdtree.query(row.cartesian.xyz.value)[1]
#         file_data = field_coords[field_id].to_pandas()
#         i_value = file_data.loc[idx, 'i']
#         g_value = file_data.loc[idx, 'g']
#         # Add i and g values to catalog
#         master_catalog.loc[index, ['i', 'g']] = [i_value, g_value]
#         pbar.update(1)
#
# # Write out updated catalog
# master_catalog.to_csv('master_updated_done_finish_5')
import pandas as pd
from astropy.coordinates import SkyCoord
from astropy import units as u
import glob
import os
from scipy.spatial import cKDTree
from tqdm import tqdm
from multiprocessing import Pool, cpu_count


# Function to process each FieldID
def process_field(field_id):
    file_path = os.path.join('Cleaned', f'c{field_id}p.ascd')
    if not glob.glob(file_path):
        print(f'Error: File not found for FieldID {field_id}')
        return None
    file_data = pd.read_csv(file_path, delimiter=' ')
    field_coords = SkyCoord(ra=file_data['RA'], dec=file_data['Dec'], unit=(u.hourangle, u.deg))
    kdtree = cKDTree(field_coords.cartesian.xyz.value.T)
    return field_id, field_coords, kdtree


if __name__ == '__main__':
    # Read in catalog data
    catalog = pd.read_csv('observations.txt', delimiter=' ')
    master_catalog = pd.read_csv('mastercopy.csv', delimiter=',')
    print(master_catalog)
    print('Starting loop...')

    # Create list of unique FieldIDs
    unique_field_ids = catalog['FieldID'].unique()

    # Use multiprocessing Pool to process each FieldID
    with Pool(cpu_count()) as p:
        results = list(
            tqdm(p.imap(process_field, unique_field_ids), total=len(unique_field_ids), desc="Processing FieldIDs"))

    # Build a dictionary of SkyCoord objects and KDTree for each FieldID
    field_coords = {}
    kdtrees = {}
    for result in results:
        if result is None:
            continue
        field_id, coords, kdtree = result
        field_coords[field_id] = coords
        kdtrees[field_id] = kdtree

    # Loop over master catalog coordinates and find nearest field coordinates
    master_catalog_coords = SkyCoord(ra=master_catalog['RADEG'], dec=master_catalog['DECDEG'], unit=(u.deg, u.deg))
    catalog_coord = SkyCoord(ra=(catalog['RAh'] * 15 + catalog['RAm'] * 0.25 + catalog['RAs'] * 0.00416667) * u.deg,
                             dec=(catalog['DEd'] + catalog['DEm'] / 60 + catalog['DEs'] / 3600) * u.deg)

    with Pool(cpu_count()) as p:
        results = list(
            tqdm(p.imap_unordered(process_coordinates, master_catalog_coords), total=len(master_catalog_coords),
                 desc="Processing Coordinates"))

    # Update master catalog with i and g values
    for result in results:
        if result is None:
            continue
        index, i_value, g_value = result
        master_catalog.loc[index, ['i', 'g']] = [i_value, g_value]

    # Write out updated catalog
    master_catalog.to_csv('master_updated_done_finish_5')
