import rasterio
from rasterio.transform import from_origin
import subprocess
import os
import xarray as xr
import numpy as np

def read_netcdf(netcdf_file, variable_name):
    print("Reading NetCDF file...")
    ds = xr.open_dataset(netcdf_file)
    data = ds[variable_name]
    if 'time' in data.dims:
        data = data.isel(time=0)
    return data

def read_grib2(grib2_file, variable_name, type_of_level):
    print("Reading GRIB2 file...")
    ds = xr.open_dataset(grib2_file, engine='cfgrib', filter_by_keys={'typeOfLevel': type_of_level, 'stepType': 'instant'})
    data = ds[variable_name]
    if 'time' in data.dims:
        data = data.isel(time=0)
    return data

def clip_latitude(data):
    print("Clipping latitude values to the valid range for Mercator projection...")
    data = data.where((data.latitude >= -85.05112878) & (data.latitude <= 85.05112878), drop=True)
    if data.shape[0] == 0 or data.shape[1] == 0:
        raise ValueError("Clipping resulted in an empty dataset.")
    return data

def convert_to_geotiff(data, output_tif):
    print("Converting to GeoTIFF...")
    transform = from_origin(data.longitude.min().values, data.latitude.max().values, 
                            np.abs(data.longitude[1] - data.longitude[0]).values, 
                            np.abs(data.latitude[1] - data.latitude[0]).values)

    if data.units == 'K':
        data.values = data.values - 273.15  # Example conversion if the data is in Kelvin

    with rasterio.open(
        output_tif, 'w', driver='GTiff',
        height=data.shape[0], width=data.shape[1],
        count=1, dtype='float32',
        crs='+proj=latlong', transform=transform,
    ) as dst:
        dst.write(data.values, 1)

def convert_to_8bit(input_tif, output_8bit_tif):
    print("Converting GeoTIFF to 8-bit format...")
    gdal_translate_command = [
        'gdal_translate', '-of', 'VRT', '-ot', 'Byte', '-scale',
        input_tif, 'temp.vrt'
    ]
    
    try:
        subprocess.run(gdal_translate_command, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error during gdal_translate: {e}")
        return

    gdal_translate_command = [
        'gdal_translate', '-of', 'GTiff', 'temp.vrt', output_8bit_tif
    ]
    
    try:
        subprocess.run(gdal_translate_command, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error during gdal_translate to GeoTIFF: {e}")

def reproject_geotiff(input_tif, reprojected_tif, target_crs):
    print(f"Reprojecting GeoTIFF to {target_crs}...")
    gdalwarp_command = [
        'gdalwarp', '-t_srs', target_crs, input_tif, reprojected_tif
    ]

    try:
        subprocess.run(gdalwarp_command, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error during gdalwarp: {e}")

def generate_tiles(input_tif, output_tiles, profile='mercator'):
    print(f"Generating map tiles using {profile} profile...")
    if not os.path.exists(output_tiles):
        os.makedirs(output_tiles)
    
    gdal2tiles_command = ['gdal2tiles.py', '-p', profile, input_tif, output_tiles, '-z', '0-3', '--xyz']
    
    try:
        subprocess.run(gdal2tiles_command, check=True)
        print(f"Tiles created successfully in {output_tiles}")
    except subprocess.CalledProcessError as e:
        print(f"Error during tile creation: {e}")

def remove_intermediate_files(files):
    print("Removing intermediate files...")
    for file in files:
        try:
            os.remove(file)
            print(f"Removed {file}")
        except FileNotFoundError:
            print(f"{file} not found, skipping.")
        except Exception as e:
            print(f"Error removing {file}: {e}")

def apply_color_relief(input_tif, color_relief_file, output_colored_tif):
    print("Applying color relief...")
    gdal_dem_command = [
        'gdaldem', 'color-relief', input_tif, color_relief_file, output_colored_tif
    ]

    try:
        subprocess.run(gdal_dem_command, check=True)
        print(f"Color relief applied successfully to {output_colored_tif}")
    except subprocess.CalledProcessError as e:
        print(f"Error during color relief application: {e}")

def process_netcdf_to_tiles(netcdf_file, variable_name, output_tif, output_8bit_tif, reprojected_tif, output_colored_tif, output_tiles, color_relief_file, target_crs='EPSG:3857'):
    data = read_netcdf(netcdf_file, variable_name)
    data = clip_latitude(data)
    convert_to_geotiff(data, output_tif)
    apply_color_relief(output_tif, color_relief_file, output_colored_tif)
    convert_to_8bit(output_colored_tif, output_8bit_tif)
    reproject_geotiff(output_8bit_tif, reprojected_tif, target_crs)
    generate_tiles(reprojected_tif, output_tiles, profile='mercator')
    remove_intermediate_files([output_tif, output_8bit_tif, reprojected_tif, output_colored_tif, 'temp.vrt'])

def process_grib2_to_tiles(grib_file, variable_name, type_of_level, output_tif, output_8bit_tif, reprojected_tif, output_colored_tif, output_tiles, color_relief_file, target_crs='EPSG:3857'):
    data = read_grib2(grib_file, variable_name, type_of_level)
    data = clip_latitude(data)
    convert_to_geotiff(data, output_tif)
    apply_color_relief(output_tif, color_relief_file, output_colored_tif)
    convert_to_8bit(output_colored_tif, output_8bit_tif)
    reproject_geotiff(output_8bit_tif, reprojected_tif, target_crs)
    generate_tiles(reprojected_tif, output_tiles, profile='mercator')
    remove_intermediate_files([output_tif, output_8bit_tif, reprojected_tif, output_colored_tif, 'temp.vrt'])

