import urllib.request, urllib.parse, urllib.error
import lxml.html
import requests
import json
import time
import numpy as np

def getPlayersFromRounds(season_from, season_to):
    players = {}
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
                            playername = player.split()[0].lower()
                            if playername in players.keys():
                                players[playername]['league_games'] += 1
                            else:
                                players[playername] = {}
                                players[playername]["league_games"] = 1
    print("Number of players: {0}".format(len(players.keys())))
    return players


def getPlayerPerfsBulk(players):
    performances_normal = []
    performances_cheat = []
    request_players = []
    player_count = 0
    closed_players_count = 0
    cheat_players_count = 0
    normal_players_count = 0
    for player in players.keys():
        player_count += 1
        request_players.append(player)
        # lichess users endpoint accepts max 300 players per call
        if len(request_players)==300 or player_count==len(players.keys()):
            r = requests.post("https://lichess.org/api/users", data=",".join(request_players), )
            request_players = []
            playersdata = json.loads(r.text)
            time.sleep(0.5) #avoid to hit endpoint too often
                       
            for playerdata in playersdata:
                
                classical = playerdata.get('perfs', {}).get('classical', {}).get('rating', 0)
                classical_count = playerdata.get('perfs', {}).get('classical', {}).get('games', 0)
                classical_rd = playerdata.get('perfs', {}).get('classical', {}).get('rd', 0)
                
                rapid = playerdata.get('perfs', {}).get('rapid', {}).get('rating', 0)
                rapid_count = playerdata.get('perfs', {}).get('rapid', {}).get('games', 0)
                rapid_rd = playerdata.get('perfs', {}).get('rapid', {}).get('rd', 0)
                
                blitz = playerdata.get('perfs', {}).get('blitz', {}).get('rating', 0)
                blitz_count = playerdata.get('perfs', {}).get('blitz', {}).get('games', 0)
                blitz_rd = playerdata.get('perfs', {}).get('blitz', {}).get('rd', 0)
                
                league_games = players[playerdata.get('id').lower()]["league_games"]
                
                tosviolation = playerdata.get('tosViolation', False)
                disabled = playerdata.get('disabled', False)
                
                player_numbers = [classical, classical_count, classical_rd, 
                                  rapid, rapid_count, rapid_rd, 
                                  blitz, blitz_count, blitz_rd, league_games]
                
                if disabled:
                    closed_players_count += 1
                elif tosviolation:
                    cheat_players_count += 1
                    performances_cheat.append(player_numbers)
                else:
                    normal_players_count += 1
                    performances_normal.append(player_numbers)
                        
    print("normal players: {0}, closed players: {1}, cheating players: {2}".format(normal_players_count, closed_players_count, cheat_players_count ))
    return performances_normal, performances_cheat

    
        
players = getPlayersFromRounds(1,28)

performances_normal, performances_cheat = getPlayerPerfsBulk(players)
print("normal players: {0}, cheating players: {1}".format(len(performances_normal),len(performances_cheat)))
performances_normal_array = np.array(performances_normal, dtype=np.int16)
performances_cheat_array = np.array(performances_cheat, dtype=np.int16)
header_text="classical, classical_games, classical_rd, rapid, rapid_games, rapid_rd, blitz, blitz_games, blitz_rd, league_games" 
np.savetxt("ratings_normal.csv", performances_normal_array, fmt="%d", delimiter=',', header=header_text, comments="")
np.savetxt("ratings_cheat.csv", performances_cheat_array, fmt="%d", delimiter=',', header=header_text, comments="")

