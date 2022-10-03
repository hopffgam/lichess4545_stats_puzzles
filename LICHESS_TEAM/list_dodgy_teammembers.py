import urllib.request, urllib.parse, urllib.error
import lxml.html
import requests
import ndjson as json


def getDodgyUsersOfTeam(teamname):
    print("Fetching player data from https://lichess.org/api/team/{0}/users".format(teamname))
    r = requests.get("https://lichess.org/api/team/{0}/users".format(teamname))
    print(r)
    players = json.loads(r.text)
    cheaters = []
    closed_accounts = []
    for player_json in players:
        name = player_json.get("id")
        tos_violation = player_json.get("tosViolation", False)
        closed = player_json.get("disabled", False)
        if tos_violation:
            cheaters.append(name)
        if closed:
            closed_accounts.append(name)
    return cheaters, closed_accounts

cheaters, closed_accounts = getDodgyUsersOfTeam("lichess4545-league")

print("Cheaters:")
print(cheaters)
print("")
print("Closed:")
print(closed_accounts)
    