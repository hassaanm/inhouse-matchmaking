import requests
import trueskill
import itertools
from sets import Set

# Roles.
top = "Top"
jng = "Jungle"
mid = "Mid"
adc = "ADC"
sup = "Support"

# The 10 players that are playing in the game and their roles.
player_map = {
    'gaR': Set([mid, top]),
    'all3nvan': Set([mid, adc, sup]),
    'edzwoo': Set([mid, adc, sup]),
    'idontcareeee': Set([mid, adc, jng, sup]),
    'dat hass': Set([top, sup]),
    'Ngoskills': Set([mid, adc, jng, sup]),
    'cerealcereal': Set([top, jng]),
    'CoolCoachDan': Set([top, sup, jng]),
    'Arata Y': Set([jng, top, adc]),
    'bakarich': Set([mid, sup, jng]),
}
players = player_map.keys()

# Pull match data.
url = 'https://league-tracker-api-stage.herokuapp.com/single_page_app_initializations'
response = requests.get(url).json()

# Build lookup maps.
summoner_id_to_name = {}
for sid, obj in response['summoners'].iteritems():
    summoner_id_to_name[int(sid)] = obj['name']

summoner_name_to_id = {name: sid for sid, name in summoner_id_to_name.iteritems()}

summoner_id_to_rating = {}
for sid in summoner_id_to_name.iterkeys():
    summoner_id_to_rating[int(sid)] = trueskill.Rating()

# Sort games by create time.
sorted_games = [g for g in response['games'].itervalues()]
sorted_games.sort(key=lambda o: o['createTime'])

# Iterate through all games and calculate ratings.
for game in sorted_games:
    winning_team = []
    losing_team = []
    for pid in game['gameParticipantIds']:
        if response['gameParticipants'][pid]['win']:
            winning_team.append(response['gameParticipants'][pid]['summonerId'])
        else:
            losing_team.append(response['gameParticipants'][pid]['summonerId'])

    winning_team_ratings = [summoner_id_to_rating[p] for p in winning_team]
    losing_team_ratings = [summoner_id_to_rating[p] for p in losing_team]

    new_winning_team_ratings, new_losing_team_ratings =  trueskill.rate([
        winning_team_ratings, losing_team_ratings], ranks=[0, 1])

    for p, r in zip(winning_team, new_winning_team_ratings):
        summoner_id_to_rating[p] = r
    for p, r in zip(losing_team, new_losing_team_ratings):
        summoner_id_to_rating[p] = r

# Generate a sorted ranking.
rankings = [(summoner_id_to_name[sid], trueskill.expose(rating)) for sid, rating in summoner_id_to_rating.iteritems()]
rankings.sort(reverse=True, key=lambda t: t[1])
for r in rankings:
    print r[0], r[1]

# Calculate match quality for all possible combinations of teams.
qualities = []
all_player_ids = set([summoner_name_to_id[p] for p in players])
for left_team in itertools.combinations(all_player_ids, 5):
    right_team = set(all_player_ids) - set(left_team)

    left_team_names = [summoner_id_to_name[p] for p in left_team]
    right_team_names = [summoner_id_to_name[p] for p in right_team]

    left_team_ratings = [summoner_id_to_rating[p] for p in left_team]
    right_team_ratings = [summoner_id_to_rating[p] for p in right_team]

    quality = trueskill.quality([left_team_ratings, right_team_ratings])
    qualities.append((quality, left_team_names, right_team_names))

qualities.sort(key=lambda t: t[0], reverse=True)

# Filter out teams without enough role diversity.
def is_team_balanced(player_map, players, roles=Set(), spot=0):
    if spot == len(players):
        return len(roles) == len(players)
    
    for role in player_map[players[spot]]:
        if is_team_balanced(player_map, players, roles | Set([role]), spot+1):
            return True
        
    return False

balanced_teams = filter(lambda q: is_team_balanced(player_map, q[1]) and is_team_balanced(player_map, q[2]), qualities)

truncated = balanced_teams[0:5]
for q in truncated:
    print q[0]
    print q[1]
    print q[2]
