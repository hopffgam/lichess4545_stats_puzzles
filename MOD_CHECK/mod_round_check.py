#! /usr/bin/env python

import urllib.request, urllib.parse, urllib.error
import argparse
import ssl
import requests
import lxml.html
import time
import json
import webbrowser
import sys
import pandas as pd
from functools import reduce


GAME_END_MOVES = 3  # consider as the end of the game
MINS_FOR_STALL_AT_GAME_END = 5
MINS_FOR_STALL_FOR_TIMEOUT = 3  # report if game was lost by timeout and clock ran down for more than this
EVAL_THRESHOLD_BAD_POSITION = 2  # Pawn equivalents for engine eval to consider a position bad

parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument('-l', '--league',type=str,
                    help='team4545 / lonewolf / chess960')
parser.add_argument('-s', '--season', type=str,
                    help='the number of the season')
parser.add_argument('-r', '--round', type=str,
                    help='the number of the round')
parser.add_argument('--shortgamesply', type=int,
                    help='Max ply to consider a game short. Default 20', default=20)
parser.add_argument('--minsforstall', type=int,
                    help='Minimum thinking time (minutes) to identify move as potential stall. Default 15', 
                    default=15)

args = parser.parse_args()

PLY_FOR_SHORT = args.shortgamesply
MINS_FOR_STALL = args.minsforstall  # Identify move as potential stall if move time increases this and the move is not at  the end of the game

LEAGUE = args.league
if LEAGUE is None:
    LEAGUE = input("team4545/lonewolf/chess960: ")
SEASON = args.season
if SEASON is None:
    SEASON = input("season: ")
r = args.round
if r is None:
    r = input("round (n+ for full season & consecutive rounds with first,last): ")

if "," in r:
    r = r.split(",")
    ROUNDNUMS = (int(r[0]), int(r[1]) + 1)
else:
    if r[-1:] == "+":
        ROUNDNUMS = (1, int(r[:-1]) + 1)
    else:
        ROUNDNUMS = (int(r), int(r) + 1)

GAMESFILENAME = "{0}GamesS{1}R{2}".format(LEAGUE, SEASON, ROUNDNUMS) 
LICHESSURL = "https://lichess.org/"

# setting the correct xpath to get game links from team4545 or lonewolf areas of lichess4545.com website
if LEAGUE == "team4545":
    XPATHCLASS = "cell-game-result"
    SECTIONS = [SEASON]
elif LEAGUE == "lonewolf":
    XPATHCLASS = "text-center text-nowrap"
    SECTIONS = [SEASON, SEASON + "u1800"]
elif LEAGUE == "chess960":
    XPATHCLASS = "text-center text-nowrap"
    SECTIONS = [SEASON]

def gameList():
    # build list of gameIDs from the round(s) by scraping lichess4545.com website
    gameIDs = []
    print("Getting games for rounds {0} to {1}".format(ROUNDNUMS[0], ROUNDNUMS[1]))
    for roundnum in range(ROUNDNUMS[0], ROUNDNUMS[1]):
        for SECTION in SECTIONS:
            connection = urllib.request.urlopen('https://www.lichess4545.com/{0}/season/{1}/round/{2}/pairings/'.format(LEAGUE, SECTION, roundnum))
            dom = lxml.html.fromstring(connection.read())
            for link in dom.xpath('//td[@class="{0}"]/a/@href'.format(XPATHCLASS)):
                gameIDs.append(link[-8:])
    return gameIDs


def getGames(gameIDs):
    # get game data from games listed in gameIDs using lichess.org API
    games = {}
    for num, gameid in enumerate(gameIDs):
        try:
            response = requests.get("https://en.lichess.org/api/game/{0}?with_analysis=1&with_movetimes=1&with_opening=1&with_moves=1".format(gameid))
            games[gameid] = json.loads(response.text)
            time.sleep(1)  # wait to prevent server overload
            print("got game", num, "/", str(len(gameIDs)), gameid)
        except:
            print("could not load game", num, "/", str(len(gameIDs)), gameid)
    return games


# get games in dictionary format - from file if present in working directory or lichess.org if not
gameIDs = gameList()
try:
    infile = open(GAMESFILENAME, 'r')
    games = json.load(infile)
    infile.close()
    newgames = set(gameIDs) - set(games.keys())
    if newgames:
        games.update(getGames(newgames))
        outfile = open(GAMESFILENAME, 'w')
        json.dump(games, outfile, indent=4)
        print("This data was updated with:", newgames)
    print("This data was read from file.")
except Exception as e:
    print(e)
    games = getGames(gameIDs)
    outfile = open(GAMESFILENAME, 'w')
    json.dump(games, outfile, indent=4)
    print("This data was fetched from web.")
    outfile.close()

# exclude listed players' games from stats results e.g. for cheater games
gamevalues = []
for game in list(games.values()):
    print(game["id"])
    gamevalues.append(game)


# convert lichess 1/100ths of a second into easily readable format
def convert(time):
    minutes = time // 6000
    seconds = round(((((time / 6000.0) - minutes)) * 60), 0)
    return  str(minutes) + " minutes " + str(seconds) + " seconds"

def getLoserData(winner_color):
    if winner_color == 'white':
        color = 'black'
    if winner_color == 'black':
        color = 'white'
    runout_time = game.get('players').get(color).get('moveCentis')[-1]
    game_end_movetimes = game.get('players').get(color).get('moveCentis')[-GAME_END_MOVES:]
    losing_player = game.get('players').get(color).get('userId')
    try:
        final_eval = game.get('analysis', None)[-1].get('eval',0) /100.0
    except:
        final_eval = 0
    if color == 'black':
        final_eval = final_eval * (-1)
    return runout_time, game_end_movetimes, losing_player, final_eval
        
short_games = {}
timeout_games = {}
stalls = []
stall_at_end_games = {}
stall_resigns = {}
####  Generate per board stats #####
for game in gamevalues:
    # find all timeouts
    game_end_movetimes = ()
    runout_time = 0
    winner = game.get('winner', None)
    if winner is not None:
        runout_time, game_end_movetimes, losing_player, final_eval = getLoserData(winner)
            
    if (runout_time // 6000 >= MINS_FOR_STALL_FOR_TIMEOUT) and game.get('status') == 'outoftime':
        timeout_games[game.get('id')] = "Game {0}{1} ended by timeout after {2:>3} ply. {3} vs {4}. {5} lost on time with {6} minutes on their clock and an evaluation of {7}".format(
            LICHESSURL, game.get('id'), game['turns'],
            game.get('players').get('white').get('userId'),
            game.get('players').get('black').get('userId'),
            losing_player, convert(runout_time), final_eval)
        continue
    
    if (runout_time // 6000 >= MINS_FOR_STALL_AT_GAME_END):
        stall_resigns[game.get('id')] = "Game {0}{1} ended by late resign after {2:>3} ply. {3} vs {4}. {5} resigned after thinking for {6} minutes and an evaluation of {7}".format(
            LICHESSURL, game.get('id'), game['turns'],
            game.get('players').get('white').get('userId'),
            game.get('players').get('black').get('userId'),
            losing_player, convert(runout_time), final_eval)
        continue
    
    for movetime in game_end_movetimes:
        if movetime // 6000 >= MINS_FOR_STALL_AT_GAME_END:
            stall_at_end_games[game.get('id')] = "Game {0}{1} had late stall and ended after {2:>3} ply. {3} vs {4}. {5} stalled for {6} minutes within the last {7} moves before losing the game".format(
            LICHESSURL, game.get('id'), game['turns'],
            game.get('players').get('white').get('userId'),
            game.get('players').get('black').get('userId'),
            losing_player, convert(movetime), GAME_END_MOVES)
            

    # find short games that should be investigated
    if game['turns'] <= PLY_FOR_SHORT:
        short_games[game.get('id')] = "Game {0}{1} short - {2:>3} ply. {3} vs {4}".format(
            LICHESSURL, game.get('id'), game['turns'],
            game.get('players').get('white').get('userId'),
            game.get('players').get('black').get('userId')
            )
    
    whitetimes = game.get('players').get('white').get('moveCentis')[:]
    blacktimes = game.get('players').get('black').get('moveCentis')[:]

    # find long move times that might indicate stall
    times=(whitetimes,blacktimes)
    for c, colour in enumerate(times):
        for move, time in enumerate(colour):
            if (time // 6000 >= MINS_FOR_STALL):
                stalls.append("potential stall in game {0}{1} - move {2:>3} took {3}. {4} vs {5}".format(
                    LICHESSURL, game.get('id'), move + 1, convert(time), 
                    game.get('players').get('white').get('userId'), 
                    game.get('players').get('black').get('userId')))

print("=============== Short Games ===============")
for game in short_games.keys():
    print (short_games.get(game))
print("=============== Timeout Games ===============")
for game in timeout_games.keys():
    print(timeout_games.get(game))
print("=============== Late Resigns ===============")
for game in stall_resigns.keys():
    print(stall_resigns.get(game))
print("=============== Stall at End of Game ===============")
for game in stall_at_end_games.keys():
    print(stall_at_end_games.get(game))
print("=============== Mid Game Stalls===============")
for game in stalls:
    print(game)
