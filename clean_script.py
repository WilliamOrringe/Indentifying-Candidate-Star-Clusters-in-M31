import os
import pandas as pd

# Define the directory path
dir_path = 'CATALOGS/'

# Loop over all file names in the directory
for filename in os.listdir(dir_path):
    # Check if the filename matches the pattern 'mXXXp.ascd'
    if filename.startswith('m') and filename.endswith('p.ascd'):
        # Read the file into a DataFrame
        df = pd.read_csv(os.path.join(dir_path, filename), delim_whitespace=True)

        # Remove the rows where 'ig' or 'ii' are less than or equal to 0
        df = df[(df['ig'] > 0) & (df['ii'] > 0) & (df['g'] <= 23) & (df['i'] <= 23)]

        # Remove the columns 'iccd', 'xg', 'yg', 'dg', 'ig', 'xi', 'yi', 'di', 'ii', 'ia', and 'field'
        df.drop(columns=['iccd', 'xg', 'yg', 'dg', 'ig', 'xi', 'yi', 'di', 'ii', 'ia', 'field'], inplace=True)

        # Write the modified DataFrame to a new file with a 'c' prefix
        df.to_csv(os.path.join('cleaned_half/', 'c' + filename), index=False, sep=' ')
