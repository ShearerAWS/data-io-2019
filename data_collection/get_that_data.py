import sys
import spotipy
import spotipy.util as util
import random
import json
import numpy as np

def generate_data(sp):
  count = 0
  
  random_queries = ['%25a%25', 'a%25', '%25e%25', 'e%25', '%25i%25', 'i%25', '%25o%25', 'o%25']
  offsets = { e : 0 for e in random_queries }

  f = open('temp.txt', 'a')
  not_similar = []
  while count < 2000:
    query = random_queries[int(random.random()*len(random_queries))]
    results = sp.search(q=query, limit=50, offset=offsets[query])
    # print(results)
    for item in results['tracks']['items']:
        if count % 50 == 0:
          print(count)
          
        if count < 1000:
          rec = sp.recommendations(seed_tracks=[item['id']], limit=1)['tracks']
          if len(rec) == 0:
            offsets[query] += 1
            continue
          rec = rec[0]
          artist = sp.artist(item['artists'][0]['id'])
          item['genres'] = artist['genres']
          item['audio_features'] = sp.audio_features(item['id'])
          not_similar.append(item)
          artist = sp.artist(rec['artists'][0]['id'])
          rec['genres'] = artist['genres']
          rec['audio_features'] = sp.audio_features(rec['id'])
          f.write(json.dumps([item, rec]) + '\n')

          # f.write(json.dumps(item) + '\n')
          
        else:
          if count == 1000:
            print('we out here')
          artist = sp.artist(item['artists'][0]['id'])
          item['genres'] = artist['genres']
          item['audio_features'] = sp.audio_features(item['id'])
          f.write(json.dumps([random.choice(not_similar), item]) + '\n')

          
        count += 1
        offsets[query] += 1


  f.close()

def get_top_tracks(api):
  offset = 0
  count = 0
  tracks = []
  print('Processing top tracks...')
  while count < 50:
    for item in api.current_user_top_tracks(limit=20, offset=offset, time_range='short_term')['items']:
      artist = api.artist(item['artists'][0]['id'])
      item['genres'] = artist['genres']
      item['audio_features'] = api.audio_features(item['id'])
      tracks.append(item)
      count += 1
      offset += 1
  return tracks

def genreOverlap(track1, track2):
  count = 0
  for genre in track1['genres']:
    if genre in track2['genres']:
      count += 1
  return count

def similarity_score(track1, track2):
  vec = [
    5.904e-2 * genreOverlap(track1, track2),
    -7.436e-5 * abs(track1['duration_ms'] - track2['duration_ms'])/1000,
    -2.284e-1 * abs(track1['audio_features'][0]['energy'] - track2['audio_features'][0]['energy']),
    -6.892e-3 * abs(track1['audio_features'][0]['loudness'] - track2['audio_features'][0]['loudness']),
    -5.638e-4 * abs(track1['audio_features'][0]['tempo'] - track2['audio_features'][0]['tempo']),
    -3.415e-1 * abs(track1['audio_features'][0]['danceability'] - track2['audio_features'][0]['danceability']),
    8.212e-3 * abs(track1['popularity'] - track2['popularity']),
    -1.119e-1 * abs(track1['audio_features'][0]['valence'] - track2['audio_features'][0]['valence']),
    2.415e-2 * abs(track1['audio_features'][0]['liveness'] - track2['audio_features'][0]['liveness']),
    -1.526e-1 * abs(track1['audio_features'][0]['acousticness'] - track2['audio_features'][0]['acousticness']),
    -2.129e-1 * abs(track1['audio_features'][0]['instrumentalness'] - track2['audio_features'][0]['instrumentalness'])
  ]
  total = sum(vec) + 8.512e-1
  return total

if len(sys.argv) > 1:
  username = sys.argv[1]
else:
  print("Usage: %s username" % (sys.argv[0],))
  sys.exit()

token = util.prompt_for_user_token(
  username,
  scope='scope',
  client_id='client_id',
  client_secret='client_secret',
  redirect_uri='redirect_uri'
)

if token:
  top_recent = None
  print('Why was I recommended this song?')
  api = spotipy.Spotify(auth=token)
  while True:
    song_id = input('Enter a song id: ')

    if top_recent == None:
      top_recent = get_top_tracks(api)

    input_track = api.track(song_id)
    artist = api.artist(input_track['artists'][0]['id'])
    input_track['genres'] = artist['genres']
    input_track['audio_features'] = api.audio_features(input_track['id'])

    song_score = []
    for track in top_recent:
      score = similarity_score(input_track, track)
      song_score.append((track['name'] + ' - ' + track['artists'][0]['name'], score))

    print('\nHere\'s some information about ' + input_track['name'] +':')
    print('Genres: ', input_track['genres'])
    print('Danceability: ', input_track['audio_features'][0]['danceability'])
    print('Speechiness', input_track['audio_features'][0]['speechiness'])
    print('Energy', input_track['audio_features'][0]['energy'])
    print('Instrumentalness', input_track['audio_features'][0]['instrumentalness'])
    print('Acousticness', input_track['audio_features'][0]['acousticness'])
    print('Valence', input_track['audio_features'][0]['valence'])
    print('\n')

    print('Top 5 songs that influenced the recommendation of ' + input_track['name'] +':')
    for track in reversed(sorted(song_score, key= lambda x: x[1])[-5:]):
      print(track[0])

    print('\n\n')


else:
    print("Can't get token for", username)
