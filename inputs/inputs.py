import io
import os
import pandas as pd
from datetime import date, timedelta, datetime

from app import dbx
# current path

# only need to change currentpath to import all datasets under different machines
# currentpath = '/Users/jf3375/PycharmProjects/plotydashtrial'
currentpath = '/var/www/plotydashtrial'

# Import Dataset
# PCA Rhos
os.chdir(os.path.join(currentpath, 'data/tuning_final_files/pca'))

def process_date_column(df, date_column='index'):
    df[date_column] = df[date_column].apply(
        lambda x: datetime.strptime(x[:13], "%Y-%m-%d %H"))
    df = df.rename(columns={'index': 'time'})
    return df

# Non PCA Rhos
# os.chdir('C:/Users/fjying/PycharmProjects/plotydashtrial/data/tuning_final_files')
os.chdir(os.path.join(currentpath, 'data/tuning_final_files'))
df_escores_rhos_solar_nonpca = pd.read_csv(
    '{}_avg_on_tuning_{}_rhos.csv'.format('escores', 'solar'))

df_escores_rhos_load_nonpca = pd.read_csv(
    '{}_avg_on_tuning_{}_rhos.csv'.format('escores', 'load'))

df_escores_rhos_wind_nonpca = pd.read_csv(
    '{}_avg_on_tuning_{}_rhos.csv'.format('escores', 'wind'))

# Texas7K
# PCA
os.chdir(os.path.join(currentpath, 'data/tuning_final_files/texas7k/pca'))
df_escores_rhos_solar_pca_t7k = pd.read_csv(
    '{}_avg_on_tuning_{}_rhos.csv'.format('escores', 'solar'))


# NonPCA
os.chdir(os.path.join(currentpath, 'data/tuning_final_files/texas7k'))
df_escores_rhos_solar_nonpca_t7k = pd.read_csv(
    '{}_avg_on_tuning_{}_rhos.csv'.format('escores', 'solar'))

df_escores_rhos_load_nonpca_t7k = pd.read_csv(
    '{}_avg_on_tuning_{}_rhos.csv'.format('escores', 'load'))

df_escores_rhos_wind_nonpca_t7k = pd.read_csv(
    '{}_avg_on_tuning_{}_rhos.csv'.format('escores', 'wind'))

# Find the list of asset ids
# RTS
solar_asset_ids = list(df_escores_rhos_solar_nonpca['solar'].unique())
solar_asset_ids.append('AVG')

load_asset_ids = list(df_escores_rhos_load_nonpca['load'].unique())
load_asset_ids.append('AVG')

wind_asset_ids = list(df_escores_rhos_wind_nonpca['wind'].unique())
wind_asset_ids.append('AVG')

# Texas7k
solar_asset_ids_t7k = list(
    df_escores_rhos_solar_nonpca_t7k['solar'].unique())
solar_asset_ids_t7k.append('AVG')

load_asset_ids_t7k = list(
    df_escores_rhos_load_nonpca_t7k['load'].unique())
load_asset_ids_t7k.append('AVG')

wind_asset_ids_t7k = list(df_escores_rhos_wind_nonpca_t7k['wind'].unique())
wind_asset_ids_t7k.append('AVG')

# Create date values for Texas7k
date_values_rts = pd.date_range(start='2020-01-01', end='2020-12-29')
date_values_rts = [str(i)[:10] for i in date_values_rts]

date_values_t7k = pd.date_range(start='2018-01-02', end='2018-12-31')
date_values_t7k = [str(i)[:10] for i in date_values_t7k]

energy_types = ['load', 'wind', 'solar']
energy_types_asset_ids = {
    'load': load_asset_ids,
    'wind': wind_asset_ids,
    'solar': solar_asset_ids
}

energy_types_asset_ids_wind_solar = {
    'wind': wind_asset_ids,
    'solar': solar_asset_ids
}

energy_types_asset_ids_t7k = {
    'load': load_asset_ids_t7k,
    'wind': wind_asset_ids_t7k,
    'solar': solar_asset_ids_t7k
}

energy_types_asset_ids_t7k_csv = {
    'load': [i.replace(' ', '_') for i in load_asset_ids_t7k],
    'wind': [i.replace(' ', '_') for i in wind_asset_ids_t7k],
    'solar': [i.replace(' ', '_') for i in solar_asset_ids_t7k]
}

energy_types_asset_ids_wind_solar_t7k = {
    'wind': wind_asset_ids_t7k,
    'solar': solar_asset_ids_t7k
}

energy_types_asset_ids_rts_csv = {
    'load': load_asset_ids[:-1],
    'wind': wind_asset_ids[:-1],
    'solar': solar_asset_ids[:-1]
}

# Select the Day DF

# Risk Allocation
# Use relative path
folder_path = '/ORFEUS-Alice/data/reliability_cost_index_data'
file_path = folder_path + '/rts/daily_type-allocs_rts_type_allocs.csv'
_, type_allocs_rts = dbx.files_download(file_path)
with io.BytesIO(type_allocs_rts.content) as stream:
    type_allocs_rts = pd.read_csv(stream, index_col=0).reset_index()

file_path = folder_path + '/rts/daily_type-allocs_rts_asset_allocs.csv'
_, asset_allocs_rts = dbx.files_download(file_path)
with io.BytesIO(asset_allocs_rts.content) as stream:
    asset_allocs_rts = pd.read_csv(stream, index_col=0).reset_index()


file_path = folder_path + '/t7k/daily_type-allocs_t7k_type_allocs.csv'
_, type_allocs_t7k = dbx.files_download(file_path)
with io.BytesIO(type_allocs_t7k.content) as stream:
    type_allocs_t7k = pd.read_csv(stream, index_col=0).reset_index()

file_path = folder_path + '/t7k/daily_type-allocs_t7k_asset_allocs.csv'
_, asset_allocs_t7k = dbx.files_download(file_path)
with io.BytesIO(asset_allocs_t7k.content) as stream:
    asset_allocs_t7k = pd.read_csv(stream, index_col=0).reset_index()

type_allocs_rts = process_date_column(type_allocs_rts)
asset_allocs_rts = process_date_column(asset_allocs_rts)
type_allocs_t7k = process_date_column(type_allocs_t7k)
asset_allocs_t7k = process_date_column(asset_allocs_t7k)

# read grid data
bus = pd.read_csv(os.path.join(currentpath,
                               'data/Vatic_Grids/Texas-7k/TX_Data/SourceData/bus.csv'))
branch = pd.read_csv(os.path.join(currentpath,
                                  'data/Vatic_Grids/Texas-7k/TX_Data/SourceData/branch.csv'))
gens = pd.read_csv(os.path.join(currentpath,
                                'data/Vatic_Grids/Texas-7k/TX_Data/SourceData/gen.csv'))

branch['Cont Rating'] = branch['Cont Rating'].replace(0, 1e6)
# Consider the case that one bus may have multiple generators, put the list of enerators inside array
gens_busid = gens[['Bus ID', 'GEN UID']].groupby(['Bus ID'])[
    'GEN UID'].unique().reset_index()
bus = pd.merge(bus, gens_busid, how='left', on='Bus ID')
bus['GEN UID'] = bus['GEN UID'].fillna('Not Gen')

