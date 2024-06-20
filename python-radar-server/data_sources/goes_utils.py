import datetime
import os
import shutil

def parse_goes_query_params(args):
    start_year = int(args.get('start_year'))
    start_month = int(args.get('start_month'))
    start_day = int(args.get('start_day'))
    start_hour = int(args.get('start_hour'))
    start_minute = int(args.get('start_minute'))
    end_year = int(args.get('end_year'))
    end_month = int(args.get('end_month'))
    end_day = int(args.get('end_day'))
    end_hour = int(args.get('end_hour'))
    end_minute = int(args.get('end_minute'))

    start = datetime.datetime(start_year, start_month, start_day, start_hour, start_minute)
    end = datetime.datetime(end_year, end_month, end_day, end_hour, end_minute)

    if not (start_year and start_month and start_day):
        raise ValueError("Missing required parameters: year, month, day")

    return start, end

def copy_files_to_directory(source_dir, key, dest_dir):
    source_dir = os.path.join(source_dir,key)
    dest_dir = os.path.join(dest_dir,key)
    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir, exist_ok=True)
    for filename in os.listdir(source_dir):
        full_file_name = os.path.join(source_dir, filename)
        if not os.path.isfile(os.path.join(dest_dir, filename)):
            if os.path.isfile(full_file_name):
                print('moving')
                shutil.copy(full_file_name, dest_dir)
            else:
                print('skipping files')
        else:
            print(f'{filename} already exists. Skipping..')
