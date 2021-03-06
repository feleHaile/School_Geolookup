import googlemaps
import csv
import pandas as pd
import usaddress
from time import sleep

def geo_lookup(input_names):
    # read in API key
    with open("api_key.txt", "r") as file:
        api_key = file.read()
    # start gmaps api
    gmaps = googlemaps.Client(key=api_key)
    # load cached data
    cached_df = pd.read_csv('cached.txt', sep='\t')
    cached = cached_df['Raw_Name'].tolist()
    # compare input names to cached
    remaining = list(set(input_names) - set(cached))
    # iterate over list of remaing locations and get geolocation
    for location in remaining:
        # TODO rate handling
        lookup_loc = location
        try:
            gmaps_json = gmaps.places(lookup_loc, location='Minnesota', radius=1000, types='school')
        except googlemaps.exceptions.Timeout:
            sleep(5)
            try:
                gmaps_json = gmaps.places(lookup_loc, location='Minnesota', radius=1000, types='school')
            # hit daily rate limit, break and write out to cache
            except googlemaps.exceptions.Timeout:
                break
        df = geo_parser(location, gmaps_json)
        cached_df = cached_df.append(df)

    # overwrite
    cached_df.to_csv('cached.txt', sep='\t', index=False, mode='w')
    return cached_df


def geo_parser(location, gmaps_json):
    # parse json response
    try:
        results = gmaps_json["results"][0]
        std_name = results['name']
        print(std_name)
        lat = results['geometry']['location']['lat']
        lng = results['geometry']['location']['lng']
        std_address = results['formatted_address']
        # parse address
        try:
            parsed_address = usaddress.tag(std_address)
            city = parsed_address[0]['PlaceName']
            state = parsed_address[0]['StateName']
        except:
            parsed_address = usaddress.parse(std_address)
            # traverse parsed address list if the tagger fails
            city = ''
            state = ''
            for addr_tup in parsed_address:
                print(addr_tup)
                if addr_tup[1] == 'PlaceName':
                    city += ' ' + addr_tup[0]
                if addr_tup[1] == 'StateName':
                    state += ' ' + addr_tup[0]
                city = city.strip()
        print(city)
        df = pd.DataFrame([[location, std_name, lat, lng, city, state]], columns=['Raw_Name', 'Name', 'Latitude', 'Longitude', 'City', 'State'])
        return df

    except IndexError:
        print(gmaps_json)
        df = pd.DataFrame()
        return



def read_raw_data(file_opts):
    file_name = file_opts[0]
    # offset header by 1 since most people will look at it in excel
    header_row = int(file_opts[1]) - 1
    sheet_name = file_opts[3]

    # determine how to handle the file based on extension
    file_path = 'INPUT/' + file_name
    if file_name.endswith('.csv'):
        # process comma delimited
        data_df = pd.read_csv(file_path, sep=',', header=header_row)
    elif file_name.endswith('.tsv'):
        # procss tab delimited
        data_df = pd.read_csv(file_path, sep='\t', header=header_row)
    elif file_name.endswith('.xlsx') or file_name.endswith('.xls'):
        # process excel sheet
        data_df = pd.read_excel(file_path, sheetname=sheet_name, header=header_row)
    else:
        # TODO raise exception here
        print(file_name, "has an unknown extension, skipping. Only csv, tsv, xls and xlsx are supported.")
    return data_df


if __name__ == "__main__":
    # read in the input options and process through each one
    with open("Input_Options.csv") as input_opts_file:
        reader = csv.reader(input_opts_file, delimiter=',')
        # skip the headers
        next(reader, None)
        # initialize output dataframe
        input_names = []
        # iterate over all files in input_options.csv
        for file_opts in reader:
            file_df = read_raw_data(file_opts)
            column_name = file_opts[2]
            school_names = file_df[column_name].str.lower()
            unique_names = pd.unique(school_names).tolist()
            # remove extra whitespace and remove all districts
            for name in unique_names:
                if 'district' not in name:
                    input_names.append(name.strip())
        unique_input_names = set(input_names)
        myval = geo_lookup(unique_input_names)


# perform join
# write out copy of data with geolocation
