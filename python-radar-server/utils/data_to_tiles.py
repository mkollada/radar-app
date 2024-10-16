import logging
import rasterio
from rasterio.transform import from_origin, from_bounds
import subprocess
import os
import xarray as xr
import numpy as np
from PIL import Image
from netCDF4 import Dataset
import gzip
import shutil

def read_netcdf(netcdf_file, variable_name):
    try:
        print("Reading NetCDF file...")
        # Open the file using netCDF4
        nc_file = Dataset(netcdf_file, 'r')

        # Convert to xarray Dataset
        ds = xr.open_dataset(xr.backends.NetCDF4DataStore(nc_file))

        if ('lon' in ds) and ('lat' in ds):
            ds = ds.rename_vars({'lon':'longitude'})

        if 'lat' in ds:
            ds = ds.rename_vars({'lat':'latitude'})
            
        
        data = ds[variable_name]
        if 'time' in data.dims:
            data = data.isel(time=0)
    except Exception as e:
        logging.error(f'Error reading netcdf {netcdf_file}:', e)
        return False
    return data

def preprocess_satellite_netcdf(data: xr.Dataset, output_tif: str):
    try:
        data = xr.Dataset(
            {'data': (('latitude', 'longitude'), data.values)},
            coords={'latitude': data.latitude.values.transpose()[0], 'longitude': data.longitude.values[0]},
            attrs={'units': 'none'}
        )['data']

        # Extract variables
        lat = data.latitude.values
        lon = data.longitude.values

        # Create a meshgrid for the latitude and longitude values
        lon2d, lat2d = np.meshgrid(lon, lat)

        # Define the bounds of the original data
        lon_min, lon_max = lon.min(), lon.max()
        lat_min, lat_max = lat.min(), lat.max()

        # Define the target resolution and grid size
        res = 0.02  # Adjust the resolution as needed
        target_lon = np.arange(lon_min, lon_max, res)
        target_lat = np.arange(lat_min, lat_max, res)
        target_lon2d, target_lat2d = np.meshgrid(target_lon, target_lat)

        # Interpolate data to the regular grid
        data_regrid = data.interp(longitude=target_lon, latitude=target_lat, method='linear')

        # Define the transformation for the GeoTIFF
        transform = from_bounds(lon_min, lat_min, lon_max, lat_max, target_lon2d.shape[1], target_lat2d.shape[0])

        # Write the reprojected data to a GeoTIFF
        with rasterio.open(
            output_tif, 'w',
            driver='GTiff',
            height=target_lat2d.shape[0],
            width=target_lon2d.shape[1],
            count=1,
            dtype=data_regrid.dtype,
            crs='+proj=latlong',
            transform=transform,
        ) as dst:
            dst.write(data_regrid.values, 1)

        logging.info("GeoTIFF file has been created successfully: %s", output_tif)

        

    except Exception as e:
        logging.error('Error processing satellite netcdf:', e)
        return False

    return True

def read_grib2(grib2_file, variable_name, type_of_level, filter_grib=True):
    print("Reading GRIB2 file...")
    try:
        ds = None
        if filter_grib:
            ds = xr.open_dataset(grib2_file, engine='cfgrib', filter_by_keys={'typeOfLevel': type_of_level, 'stepType': 'instant'})
        else:
            ds = xr.open_dataset(grib2_file, engine='cfgrib')
        data = ds[variable_name]
        if 'time' in data.dims:
            data = data.isel(time=0)
    except Exception as e:
        logging.error(f'Error reading grib {grib2_file}', e)
        return False
    return data

def clip_latitude(data):
    try:
        print("Clipping latitude values to the valid range for Mercator projection...")
        data = data.where((data.latitude >= -85.05112878) & (data.latitude <= 85.05112878), drop=True)
        if data.shape[0] == 0 or data.shape[1] == 0:
            logging.error("Clipping resulted in an empty dataset.")
            return False
    except Exception as e:
        logging.error(f'Error clipping latitudes:', e)
        return False
    return data

def convert_to_geotiff(data, output_tif):
    print("Converting to GeoTIFF...")
    try:
        if len(data.longitude.shape) == 2:
            long0 = data.longitude[0][1]
            long1 = data.longitude[0][2]
        elif len(data.longitude.shape) == 1:
            long0 = data.longitude[1]
            long1 = data.longitude[2]

        long_val = np.abs(long1 - long0).values

        if len(data.longitude.shape) == 2:
            lat0 = data.latitude[0][0]
            lat1 = data.latitude[1][0]
        elif len(data.longitude.shape) == 1:
            lat0 = data.latitude[0]
            lat1 = data.latitude[1]

        lat_val = np.abs(lat1 - lat0).values

        transform = from_origin(data.longitude.min().values, data.latitude.max().values, 
                                long_val, 
                                lat_val)
        if 'units' in data.attrs:
            if data.units == 'K':
                data.values = data.values - 273.15  # Example conversion if the data is in Kelvin

        print(data.shape)
        print('------')
        
        with rasterio.open(
            output_tif, 'w', driver='GTiff',
            height=data.shape[0], width=data.shape[1],
            count=1, dtype='float32',
            crs='+proj=latlong', transform=transform,
        ) as dst:
            dst.write(data.values, 1)
    except Exception as e:
        logging.error(f'Error converting to geotiff {output_tif}', e)
        return False
    return True

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
        return False

    gdal_translate_command = [
        'gdal_translate', '-of', 'GTiff', 'temp.vrt', output_8bit_tif
    ]
    
    try:
        subprocess.run(gdal_translate_command, check=True)
    except subprocess.CalledProcessError as e:
        logging.error(f"Error during gdal_translate to GeoTIFF: {e}")
        return False

    return True

def reproject_geotiff(input_tif, reprojected_tif, target_crs):
    print(f"Reprojecting GeoTIFF to {target_crs}...")
    gdalwarp_command = [
        'gdalwarp', '-t_srs', target_crs, input_tif, reprojected_tif
    ]

    try:
        subprocess.run(gdalwarp_command, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error during gdalwarp: {e}")
        return False
    
    return True

def generate_tiles(input_tif, output_tiles, profile='mercator'):
    print(f"Generating map tiles using {profile} profile...")
    if not os.path.exists(output_tiles):
        os.makedirs(output_tiles)

    gdal2tiles_command = ['gdal2tiles.py', '-p', profile, input_tif, output_tiles, '-z', '0-5', '--xyz']
    
    try:
        subprocess.run(gdal2tiles_command, check=True)
        print(f"Tiles created successfully in {output_tiles}")
    except subprocess.CalledProcessError as e:
        print(f"Error during tile creation: {e}")
        return False
    
    return True

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
        'gdaldem', 'color-relief', '-alpha', input_tif, color_relief_file, output_colored_tif
    ]

    try:
        subprocess.run(gdal_dem_command, check=True)
        print(f"Color relief applied successfully to {output_colored_tif}")
    except subprocess.CalledProcessError as e:
        print(f"Error during color relief application: {e}")
        return False
    
    return True



def process_netcdf_to_tiles(
        netcdf_file, 
        variable_name, 
        output_tiles, 
        color_relief_file, 
        target_crs='EPSG:3857',
        remove=True,
        satellite=False
):
    
    base_temp_file_name = os.path.splitext(os.path.basename(netcdf_file))[0]
    output_tif = base_temp_file_name + '.tif'
    output_8bit_tif = base_temp_file_name + '_8bit.tif'
    output_colored_tif = base_temp_file_name + '_colored.tif'
    reprojected_tif = base_temp_file_name + '_3857.tif'
    
    
    data = read_netcdf(netcdf_file, variable_name)
    
    data = clip_latitude(data)

    if satellite:
        geotiff_success = preprocess_satellite_netcdf(data, output_tif)
    else:
    
        geotiff_success = convert_to_geotiff(data, output_tif)

    if geotiff_success:
        color_success = apply_color_relief(output_tif, color_relief_file, output_colored_tif)
    else:
        return False
    
    if color_success:
        bit_success = convert_to_8bit(output_colored_tif, output_8bit_tif)
    else:
        return False
    
    if bit_success:
        reproject_success = reproject_geotiff(output_8bit_tif, reprojected_tif, target_crs)
    else:
        return False
    
    if reproject_success:
        tiles_success = generate_tiles(reprojected_tif, output_tiles, profile='mercator')
    else:
        return False

    if remove:
        remove_intermediate_files([output_tif, output_8bit_tif, reprojected_tif, output_colored_tif, 'temp.vrt'])

    return tiles_success

def process_grib2_to_tiles(
        grib_file, 
        variable_name, 
        type_of_level,
        output_tiles, 
        color_relief_file, 
        target_crs='EPSG:3857',
        filter_grib=True,
        remove=True
    ):

    base_temp_file_name = os.path.splitext(os.path.basename(grib_file))[0]
    output_tif = base_temp_file_name + '.tif'
    output_8bit_tif = base_temp_file_name + '_8bit.tif'
    output_colored_tif = base_temp_file_name + '_3857.tif'
    reprojected_tif = base_temp_file_name + '_colored.tif'

    data = read_grib2(grib_file, variable_name, type_of_level, filter_grib=filter_grib)
    data = clip_latitude(data)
    geotiff_success = convert_to_geotiff(data, output_tif)

    if geotiff_success:
        color_success = apply_color_relief(output_tif, color_relief_file, output_colored_tif)
    else:
        return False
    
    if color_success:
        bit_success = convert_to_8bit(output_colored_tif, output_8bit_tif)
    else:
        return False
    
    if bit_success:
        reproject_success = reproject_geotiff(output_8bit_tif, reprojected_tif, target_crs)
    else:
        return False
    
    if reproject_success:
        tiles_success = generate_tiles(reprojected_tif, output_tiles, profile='mercator')
    else:
        return False

    if remove:
        remove_intermediate_files([output_tif, output_8bit_tif, reprojected_tif, output_colored_tif, 'temp.vrt'])

    return tiles_success

def process_tif_to_tiles(
        input_tif, 
        output_tiles, 
        color_relief_file,
        remove=True
):
    base_temp_file_name = os.path.splitext(os.path.basename(input_tif))[0]
    output_8bit_tif = base_temp_file_name + '_8bit.tif'
    output_colored_tif = base_temp_file_name + '_3857.tif'
    reprojected_tif = base_temp_file_name + '_colored.tif'

    # apply_color_relief(input_tif, color_relief_file, output_colored_tif)
    # generate_tiles(output_colored_tif, output_tiles, profile='mercator')
    # remove_intermediate_files([output_8bit_tif, reprojected_tif, output_colored_tif, 'temp.vrt'])

    
    color_success = apply_color_relief(input_tif, color_relief_file, output_colored_tif)
    
    if color_success:
        tiles_success = generate_tiles(output_colored_tif, output_tiles, profile='mercator')
    else:
        return False

    if remove:
        remove_intermediate_files([output_8bit_tif, reprojected_tif, output_colored_tif, 'temp.vrt'])

    return tiles_success

def process_zipped_grib2_to_tiles(
        gzipped_grib2_file, 
        variable_name, 
        type_of_level,  
        output_tiles, 
        color_relief_file, 
        target_crs='EPSG:3857',
        filter_grib=True
    ):
    print(f"Processing {gzipped_grib2_file}...")
    try:
        # Decompress the gzipped GRIB2 file
        grib2_file = gzipped_grib2_file.replace('.gz', '')
        with gzip.open(gzipped_grib2_file, 'rb') as f_in:
            with open(grib2_file, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
    except Exception as e:
        logging.error(f'Error decompressing {gzipped_grib2_file}:', e)

    # Process the decompressed GRIB2 file as normal
    success = process_grib2_to_tiles(
        grib2_file, 
        variable_name, 
        type_of_level, 
        # output_tif, 
        # output_8bit_tif, 
        # reprojected_tif, 
        # output_colored_tif, 
        output_tiles, 
        color_relief_file, 
        target_crs,
        filter_grib=filter_grib)

    # Remove the decompressed GRIB2 file
    try:
        os.remove(grib2_file)
        print(f"Removed {grib2_file}")
    except FileNotFoundError:
        print(f"{grib2_file} not found, skipping.")
    except Exception as e:
        print(f"Error removing {grib2_file}: {e}")

    return success
