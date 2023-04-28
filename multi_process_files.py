import pandas as pd
from astropy.coordinates import SkyCoord
from astropy import units as u
import glob
import os
from scipy.spatial import cKDTree
from tqdm import tqdm
from multiprocessing import Pool, cpu_count

def process_chunk(chunk):
    global master_catalog, field_coords, kdtrees, catalog_coord
    for file_path in chunk:
        # Find matching FieldID
        field_id = int(os.path.splitext(os.path.basename(file_path))[0][1:])
        kdtree = kdtrees.get(field_id, None)
        if kdtree is None:
            print(f'Error: KDTree not found for FieldID {field_id}')
            continue
        # Load file data and create SkyCoord object
        file_data = pd.read_csv(file_path, delimiter=' ')
        coords = SkyCoord(ra=file_data['RA'], dec=file_data['Dec'], unit=(u.hourangle, u.deg))
        # Query KDTree to find the nearest point in field's coordinates
        _, idx = kdtree.query(coords.cartesian.xyz.value.T)
        i_value = file_data.loc[idx, 'i']
        g_value = file_data.loc[idx, 'g']
        # Add i and g values to master catalog
        master_catalog.loc[master_catalog['FieldID'] == field_id, ['i', 'g']] = [i_value, g_value]

if __name__ == '__main__':
    # Read in catalog data
    catalog = pd.read_csv('observations.txt', delimiter=' ')
    master_catalog = pd.read_csv('mastercopy.csv', delimiter=',')
    print(master_catalog)
    print('Starting loop...')

    # Create dictionary of file paths for each FieldID
    field_files = {}
    with tqdm(total=len(catalog['FieldID'].unique())) as first_bar:
        for field_id in catalog['FieldID'].unique():
            file_path = os.path.join('Cleaned', f'c{field_id}p.ascd')
            if not glob.glob(file_path):
                print(f'Error: File not found for FieldID {field_id}')
                continue
            field_files[field_id] = file_path
            first_bar.update(1)
    # Build a KDTree from the SkyCoord objects in field_coords
    field_coords = {field_id: SkyCoord(ra=pd.read_csv(file_path, delimiter=' ')['RA'], dec=pd.read_csv(file_path, delimiter=' ')['Dec'], unit=(u.hourangle, u.deg)) for field_id, file_path in field_files.items()}
    kdtrees = {field_id: cKDTree(coords.cartesian.xyz.value.T) for field_id, coords in field_coords.items()}

    # Process each file in a separate process
    file_paths = list(field_files.values())
    num_processes = cpu_count()
    chunk_size = len(file_paths) // num_processes
    chunks = [file_paths[i:i+chunk_size] for i in range(0, len(file_paths), chunk_size)]
    with Pool(processes=num_processes) as pool:
        pool.map(process_chunk, chunks)

    print(master_catalog)

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

    # Create dictionary of file paths for each FieldID
    field_files = {}
    with tqdm(total=len(catalog['FieldID'].unique())) as first_bar:
        for field_id in catalog['FieldID'].unique():
            file_path = os.path.join('Cleaned', f'c{field_id}p.ascd')
            if not glob.glob(file_path):
                print(f'Error: File not found for FieldID {field_id}')
                continue
            field_files[field_id] = file_path
            first_bar.update(1)

    # Process field_coords and kdtrees in parallel
    field_ids = list(field_files.keys())
    with Pool(processes=num_processes) as pool:
        results = []
        with tqdm(total=len(field_ids)) as second_bar:
            for chunk_start in range(0, len(field_ids), chunk_size):
                chunk_ids = field_ids[chunk_start:chunk_start+chunk_size]
                chunk_results = pool.map(process_field, chunk_ids)
                results.extend([r for r in chunk_results if r is not None])
                second_bar.update(len(chunk_ids))

    # Build a dictionary of field_coords and kdtrees from the results
    field_coords = {}
    kdtrees = {}
    for field_id, coords, kdtree in results:
        field_coords[field_id] = coords
        kdtrees[field_id] = kdtree
