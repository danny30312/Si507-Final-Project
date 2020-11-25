#########################################
##### Name: Chieh-Hao Chuang        #####
##### Uniqname: chchuang            #####
#########################################

from requests_oauthlib import OAuth1
import json
import time
import requests
import final_secret as secrets
import plotly.graph_objs as go
import webbrowser
import sqlite3

CACHE_FILENAME = "spotify_cache.json"

client_key = secrets.SPOTIFY_API_KEY
client_secret = secrets.SPOTIFY_API_SECRET

grant_type = 'client_credentials'
body_params = {'grant_type' : grant_type}

url_token = 'https://accounts.spotify.com/api/token'
response = requests.post(url_token, data=body_params, auth=(client_key, client_secret))

token_raw = json.loads(response.text)
token = token_raw["access_token"]

headers = {"Authorization": "Bearer {}".format(token)}

URL = 'https://api.spotify.com/v1/search'


def test_oauth():
    ''' Helper function that returns an HTTP 200 OK response code and a 
    representation of the requesting user if authentication was 
    successful; returns a 401 status code and an error message if 
    not. Only use this method to test if supplied user credentials are 
    valid. Not used to achieve the goal of this assignment.'''

    r = requests.get(url='https://api.spotify.com/v1/search', headers=headers, params={'q': "beatles", 'type': 'artist'})
    print(r.text)


def open_cache():
    ''' Opens the cache file if it exists and loads the JSON into
    the CACHE_DICT dictionary.
    if the cache file doesn't exist, creates a new cache dictionary
    
    Parameters
    ----------
    None
    
    Returns
    -------
    The opened cache: dict
    '''
    try:
        cache_file = open(CACHE_FILENAME, 'r')
        cache_contents = cache_file.read()
        cache_dict = json.loads(cache_contents)
        cache_file.close()
    except:
        cache_dict = {}
    return cache_dict


def save_cache(cache_dict):
    ''' Saves the current state of the cache to disk
    
    Parameters
    ----------
    cache_dict: dict
        The dictionary to save
    
    Returns
    -------
    None
    '''
    dumped_json_cache = json.dumps(cache_dict)
    fw = open(CACHE_FILENAME,"w")
    fw.write(dumped_json_cache)
    fw.close() 


def construct_unique_key(baseurl, params):
    ''' constructs a key that is guaranteed to uniquely and 
    repeatably identify an API request by its baseurl and params
    
    Parameters
    ----------
    baseurl: string
        The URL for the API endpoint
    params: dict
        A dictionary of param:value pairs
    
    Returns
    -------
    string
        the unique key as a string
    '''
    param_list = []
    if params != None:
        for key, val in params.items():
            param_list.append(str(key) + "_" + str(val))
    
    param_list.sort()
    unique_key = baseurl + "_" + "_".join(param_list)

    return unique_key


def make_url_request_using_cache_API(unique_key, url, params, cache):
    ''' Looking for data in the cache.
    If can't find it, make a request and store it into cache.
    
    Parameters
    ----------
    unique_key: string
        As key to store in dict
    url: string
        The url to make request
    params: dict
        The params to make request
    cache: dict
        The cache to look for data
    
    Returns
    -------
    cache[url]: string
        Text of the web
    '''
    if (unique_key in cache.keys()):
        return cache[unique_key]
    else:
        time.sleep(0.1)
        response = requests.get(url, headers=headers, params=params)
        cache[unique_key] = response.json()
        save_cache(cache)
        return cache[unique_key]


def artist_list(URL, CACHE_DICT):

    artist_dict = {}
    artist_array = []

    artist = input("\nEnter a artist name, or \"exit\" to quit: ")
    ExitProgram(artist)
    params = {'q': artist, 'type': 'artist'}
    artist_unique_key = construct_unique_key(URL, params)
    artist_response = make_url_request_using_cache_API(artist_unique_key, URL, params, CACHE_DICT)['artists']['items']

    for art in artist_response:
        artist_dict[art['name']] = art['id']
        artist_array.append(art['name'])
        database_artist(str(art['name']), str(art['genres']), str(art['external_urls']['spotify']), str(art['href']), str(art['popularity']))
        
    return artist_dict, artist_array, artist
    

def album_list(artist_num, artist_dict, artist_array, CACHE_DICT):

    album_dict = {}
    album_array = []

    artist_url = "https://api.spotify.com/v1/artists/" + artist_dict[artist_array[int(artist_num) - 1]] + "/albums"
    params = {'include_groups': 'album,single', 'limit': 50}
    album_unique_key = construct_unique_key(artist_url, params)
    album_response = make_url_request_using_cache_API(album_unique_key, artist_url, params, CACHE_DICT)['items']

    for album in album_response:
        album_dict_array = []
        album_dict_array.append(album["external_urls"]["spotify"])
        album_dict_array.append(album["href"])
        album_dict[album['name']] = album_dict_array
        album_array.append(album['name'])
        album_artist = []
        for a in album['artists']:
            album_artist.append(a['name'])
        database_album(", ".join(album_artist), str(album['name']), str(album['available_markets']), str(album['external_urls']['spotify']), str(album['href']))

    return album_dict, album_array


def popularity(artist, album_dict, CACHE_DICT):

    xvals = []
    yvals = []

    for key, val in album_dict.items():
        album_unique_key = construct_unique_key(val[1], None)
        album_response = make_url_request_using_cache_API(album_unique_key, val[1], None, CACHE_DICT)
        xvals.append(key)
        yvals.append(album_response['popularity'])
        update_database(key, str(album_response['popularity']))
    
    bar_data = go.Bar(x=xvals, y=yvals)
    basic_layout = go.Layout(title=f"Popularity of {artist}'s Albums")
    fig = go.Figure(data=bar_data, layout=basic_layout)
    print(f"\nLauching Popularity of {artist}'s Albums in web browser...\n")
    fig.show()


def create_database():

    conn = sqlite3.connect('spotify.sqlite')
    cur = conn.cursor()

    create_artist = '''
        CREATE TABLE IF NOT EXISTS "artist" (
            "Id"    INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE,
            "Name"  TEXT NOT NULL,
            "Genres"    TEXT NOT NULL,
            "External_urls" TEXT NOT NULL,
            "Href"  TEXT NOT NULL,
            "Popularity"    INTERGER NOT NULL
        );
    '''

    create_album = '''
        CREATE TABLE IF NOT EXISTS "album" (
            "Id"    INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE,
            "Artist"    TEXT NOT NULL,
            "Name"  TEXT NOT NULL,
            "Available_markets"    TEXT NOT NULL,
            "External_urls" TEXT NOT NULL,
            "Href"  TEXT NOT NULL,
            "Popularity"  TEXT NOT NULL
        );
    '''

    cur.execute(create_artist)
    cur.execute(create_album)
    conn.commit()


def delete_database():

    conn = sqlite3.connect('spotify.sqlite')
    cur = conn.cursor()

    drop_artist = '''
        DROP TABLE IF EXISTS "artist";
    '''
    drop_album = '''
        DROP TABLE IF EXISTS "album";
    '''

    cur.execute(drop_artist)
    cur.execute(drop_album)
    conn.commit()


def database_artist(Name, Genres, External_urls, Href, Popularity):

    conn = sqlite3.connect('spotify.sqlite')
    cur = conn.cursor()

    insert_artist = '''
        INSERT INTO artist
        VALUES (NULL, ?, ?, ?, ?, ?)
    '''

    artist_array = [Name, Genres, External_urls, Href, Popularity]
    cur.execute(insert_artist, artist_array)
    conn.commit()


def update_database(Name, Popularity):

    conn = sqlite3.connect('spotify.sqlite')
    cur = conn.cursor()

    update_album = '''
        UPDATE album
        SET Popularity = ?
        WHERE Name = ?
    '''

    album_update = [Popularity, Name]
    cur.execute(update_album, album_update)
    conn.commit()


def database_album(Artist, Name, Available_markets, External_urls, Href):

    conn = sqlite3.connect('spotify.sqlite')
    cur = conn.cursor()

    insert_album = '''
        INSERT INTO album
        VALUES (NULL, ?, ?, ?, ?, ?, ?)
    '''

    album_array = [Artist, Name, Available_markets, External_urls, Href, '0']
    cur.execute(insert_album, album_array)
    conn.commit()


def print_list(array):
    count = 1
    for item in array:
        print(f"{count} - {item}")
        count += 1


def ExitProgram(search):
    if search.lower() == "exit":
        print("Bye!")
        quit()


def Lauching(album_dict, album_array, album_num):
    print("\nLauching")
    print(album_dict[album_array[int(album_num) - 1]][0])
    print("in web browser...")
    webbrowser.open(album_dict[album_array[int(album_num) - 1]][0])

if __name__ == "__main__":

    CACHE_DICT = open_cache()
    create_database()
    
    artist_dict = {}
    artist_array = []
    artist = None

    while True:
        artist_dict, artist_array, artist = artist_list(URL, CACHE_DICT)
        
        if len(artist_array) != 0:
            print_list(artist_array)
            break
        else:
            print("\nERROR: NO RESULT, PLEASE INPUT A VALID ARTIST!")
    
    album_dict = {}
    album_array = []

    while True:
        artist_num = input("\nEnter a artist number you want, or \"exit\" to quit: ")
        ExitProgram(artist_num)

        if artist_num.isnumeric():
            if int(artist_num) <= len(artist_array) and int(artist_num) != 0:
                album_dict, album_array = album_list(artist_num, artist_dict, artist_array, CACHE_DICT)

                if len(album_array) != 0:
                    popularity(artist, album_dict, CACHE_DICT)
                    print_list(album_array)
                    break
                else:
                    print("\nERROR: NO ALBUM RELEASED, PLEASE SELECT ANOTHER ARTIST!")
            else:
                print("\nERROR: PLEASE ENTER A NUMBER LESS THAN OR EQUAL TO: " + str(len(artist_array)))
        else:
            print("\nERROR: PLEASE ENTER A NUMBER LESS THAN OR EQUAL TO: " + str(len(artist_array)))
    
    while True:
        album_num = input("\nSelect a album (Enter a number) for more details, or \"exit\" to quit: ")
        ExitProgram(album_num)

        if album_num.isnumeric():
            if int(album_num) <= len(album_array) and int(album_num) != 0:
                Lauching(album_dict, album_array, album_num)
            else:
                print("\nERROR: PLEASE ENTER A NUMBER LESS THAN OR EQUAL TO: " + str(len(album_array)))
        else:
            print("\nERROR: PLEASE ENTER A NUMBER LESS THAN OR EQUAL TO: " + str(len(album_array)))