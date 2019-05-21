import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import spotipy.util as util
import requests
import bs4
import datetime
from pprint import pprint

# ============================ FUNCTIONS ============================

# Description: removes special characters for better searching in a list or string
# Returns: a string list or string depending on what is passed in
def getTrueString(inputList):
    if type(inputList) == str:
        inputList.replace('ë', 'e').replace('í', 'i').replace('ñ', 'n')
        if '(' in inputList:
            inputList = inputList[:inputList.index(' (')]

        if 'Featuring' in inputList:
            inputList = inputList[:inputList.index(' Featuring')]

        return inputList

    for i in range(len(inputList)):
        inputList[i] = inputList[i].replace('ë', 'e').replace('í', 'i').replace('ñ', 'n')

        if '(' in inputList[i]:
            inputList[i] = inputList[i][:inputList[i].index(' (')]

        if 'Featuring' in inputList[i]:
            inputList[i] = inputList[i][:inputList[i].index(' Featuring')]

    return inputList

# ============================ SCRIPT ============================

# setting up reading the url and BeautifulSoup object
res = requests.get('https://www.billboard.com/charts/r-b-hip-hop-songs')
res.raise_for_status()
elements = bs4.BeautifulSoup(res.text, features="html5lib")

# reads billboard.com for the top 50 hiphop & r&b songs and the corresponding artists
rawSongText = elements.find_all("span", class_="chart-list-item__title-text")
rawArtistsText = elements.find_all("div", class_="chart-list-item__artist")

# cleans up the artist and song titles and stores them into lists
songData = []
artistData = []
for song in rawSongText:
    songData.append(song.text.strip())

for artist in rawArtistsText:
    artistData.append(artist.text.strip())

# fixes songs and artist names to ready them for spotify search
songData = getTrueString(songData)
artistData = getTrueString(artistData)


# ---------SPOTIPY SETUP---------

# reads credentials.txt file for spotify API and user credentials
fh = open("credentials.txt")
credentials = fh.read().split('\n')
credentials = {'cid': credentials[0][credentials[0].index('=') + 1:].strip(' '),
               'secret': credentials[1][credentials[1].index('=') + 1:].strip(' '),
               'username': credentials[2][credentials[2].index('=') + 1:].strip(' '),
               'pid': credentials[3][credentials[3].index('=') + 1:].strip(' '),
               'ppid': credentials[4][credentials[4].index('=') + 1:].strip(' ')}
fh.close()

client_credentials_manager = SpotifyClientCredentials(client_id=credentials['cid'], client_secret=credentials['secret'])
sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

# Reads the preferred artists file
fh = open("artists.txt")
preferredArtists = fh.read().split('\n')
fh.close()

# token used for user authentication, will open browser on first run
token = util.prompt_for_user_token(credentials['username'],
        scope='playlist-modify-private,playlist-modify-public',
        client_id=credentials['cid'],
        client_secret= credentials['secret'],
        redirect_uri='https://localhost:8080')
if token:
    sp = spotipy.Spotify(auth=token)
else:
    print("Can't get token for ", credentials['username'])


# searches and adds all songs to allTracks and preferred artist songs to preferredTracks
allTracks = []
preferredTracks = []

result = sp.user_playlist_tracks(credentials['username'], playlist_id=credentials['ppid'], fields=None, limit=100, offset=0, market=None)

for i in range(0, len(result['items'])):
    preferredTracks.append(result['items'][i]['track']['id'])

for song in songData:
    result = sp.search(song, limit=1, offset=0, type='track')
    spotifyURI = result['tracks']['items'][0]['id']

    # goes through all artists in the song and checks if the artist is in the artist.txt file
    artistName = getTrueString(result['tracks']['items'][0]['artists'][0]['name'])
    artistCount = 0
    while artistName is not None:
        if artistName in preferredArtists:
            if spotifyURI not in preferredTracks:
                preferredTracks.append(spotifyURI)

        # checks for multiple artists in a single song
        artistCount += 1
        try:
            artistName = getTrueString(result['tracks']['items'][0]['artists'][artistCount]['name'])
        except IndexError:
            artistName = None

    allTracks.append(spotifyURI)

# replaces all songs to top 50 billboard and preferred artist playlist
sp.user_playlist_replace_tracks(user=credentials['username'], playlist_id=credentials['pid'], tracks=allTracks)
sp.user_playlist_replace_tracks(user=credentials['username'], playlist_id=credentials['ppid'], tracks=preferredTracks)
