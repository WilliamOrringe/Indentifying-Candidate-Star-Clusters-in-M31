import pandas as pd
from astropy.coordinates import SkyCoord
from astropy import units as u
import glob
import os
from scipy.spatial import cKDTree
from tqdm import tqdm
from multiprocessing import Pool, Manager, freeze_support
import pickle
import json
import sys


# Define a function to create SkyCoord objects for a given field_id
def create_skycoord(field_id):
    file_path = os.path.join('very_clean', f'c{field_id}p.ascd')
    if not glob.glob(file_path):
        print(f'Error: File not found for FieldID {field_id}')
        return None
    file_data = pd.read_csv(file_path, delimiter=' ')
    coords = SkyCoord(ra=file_data['RA'], dec=file_data['Dec'], unit=(u.hourangle, u.deg))
    return field_id, coords


if __name__ == '__main__':

    freeze_support()
    # Read in catalog data
    catalog = pd.read_csv('observations.txt', delimiter=' ')
    master_catalog = pd.read_csv('mastercopy.csv', delimiter=',')
    print(master_catalog)
    print('Starting loop...')
    # Create dictionary of SkyCoord objects for each FieldID
    field_coords = Manager().dict()
    with Pool() as p:
        for result in tqdm(p.imap_unordered(create_skycoord, catalog['FieldID'].unique()),
                           total=len(catalog['FieldID'].unique())):
            if result is not None:
                field_coords[result[0]] = result[1]

    # Build a KDTree from the SkyCoord objects in field_coords
    kdtrees = {}
    small_test = {}
    for field_id, coords in field_coords.items():
        kdtrees[field_id] = cKDTree(coords.cartesian.xyz.value.T)
        try:
            small_test[field_id] = coords.cartesian.xyz.value.T
        except:
            pass

    try:
        with open('kdtrees2.pickle', 'wb') as f:
            pickle.dump(kdtrees, f)

        # Read kdtrees back in from file and verify that it matches the original kdtrees
        with open('kdtrees2.pickle', 'rb') as f:
            kdtrees_new = pickle.load(f)
    except:
        print('failed on pickle')

    if kdtrees == kdtrees_new:
        sys.exit()
    # Verify that the two dictionaries match
    assert kdtrees == kdtrees_new
