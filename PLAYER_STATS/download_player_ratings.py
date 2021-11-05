import urllib.request, urllib.parse, urllib.error
import lxml.html
import requests
import json
import time
import numpy as np

def getPlayersFromRounds(season_from, season_to):
    players = set()
    for season in range(season_from, season_to+1):
        for round in range(1,9):
            print('https://www.lichess4545.com/team4545/season/{0}/round/{1}/pairings'.format(season,round))
            connection = urllib.request.urlopen('https://www.lichess4545.com/team4545/season/{0}/round/{1}/pairings'.format(season,round))
            dom =  lxml.html.fromstring(connection.read())
    
            domclasses = ["pairing-player player-white", "pairing-player player-black", 
                          "text-right pairing-player player-white", "text-right pairing-player player-black" ]
            
            for domclass in domclasses:
                for player in dom.xpath('//td[@class="{0}"]/a/text()'.format(domclass)):
                    if player.split() != []:
                        if not player.split()[0].startswith("("):
                            players.add(player.split()[0])
    print("Number of players: {0}".format(len(players)))
    return players


def getPlayerPerfsBulk(players):
    performances_normal = []
    performances_cheat = []
    request_players = []
    player_count = 0
    closed_players_count = 0
    cheat_players_count = 0
    normal_players_count = 0
    for player in players:
        player_count += 1
        request_players.append(player)
        if len(request_players)==300 or player_count==len(players):
            r = requests.post("https://lichess.org/api/users", data=",".join(request_players), )
            request_players = []
            playersdata = json.loads(r.text)
                       
            for playerdata in playersdata:
                classical = playerdata.get('perfs', {}).get('classical', {}).get('rating', 0)
                rapid = playerdata.get('perfs', {}).get('rapid', {}).get('rating', 0)
                blitz = playerdata.get('perfs', {}).get('blitz', {}).get('rating', 0)
                tosviolation = playerdata.get('tosViolation', False)
                disabled = playerdata.get('disabled', False)
                if disabled:
                    closed_players_count += 1
                elif tosviolation:
                    cheat_players_count += 1
                    performances_cheat.append([classical, rapid, blitz])
                else:
                    normal_players_count += 1
                    performances_normal.append([classical, rapid, blitz])
                        
    print("normal players: {0}, closed players: {1}, cheating players: {2}".format(normal_players_count, closed_players_count, cheat_players_count ))
    return performances_normal, performances_cheat

    
        
players = getPlayersFromRounds(1,28)

performances_normal, performances_cheat = getPlayerPerfsBulk(players)
print("normal players: {0}, cheating players: {1}".format(len(performances_normal),len(performances_cheat)))
performances_normal_array = np.array(performances_normal, dtype=np.int16)
performances_cheat_array = np.array(performances_cheat, dtype=np.int16)
np.savetxt("ratings_normal.csv", performances_normal_array, fmt="%d", delimiter=',', header="classical,rapid,blitz", comments="")
np.savetxt("ratings_cheat.csv", performances_cheat_array, fmt="%d", delimiter=',', header="classical,rapid,blitz", comments="")

