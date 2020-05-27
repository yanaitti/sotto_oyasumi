from flask import Flask, Response, render_template
from flask_caching import Cache
import uuid
import random
import collections
import json
import os
import copy
import numpy as np

'''
    A  B  C  D
0:  0  1  2  3 J(4
1:  5  6  7  8 J(9
2: 10 11 12 13 J(14
3: 15 16 17 18 J(19
4: 20 21 22 23 J(24
5: 25 26 27 28 J(29
6: 30 31 32 33 J(34
'''


app = Flask(__name__, static_folder='img')

# Cacheインスタンスの作成
cache = Cache(app, config={
    'CACHE_TYPE': 'redis',
    'CACHE_REDIS_URL': os.environ.get('REDIS_URL', 'redis://localhost:6379'),
    'CACHE_DEFAULT_TIMEOUT': 60 * 60 * 2,
})


@app.route('/')
def homepage():
    return render_template('index.html')


# create the game group
@app.route('/create/<nickname>')
def create_game(nickname):
    game = {
        'status': 'waiting',
        'routeidx': 0,
        'routeid': '',
        'slept': [],
        'players': []}
    player = {}

    gameid = str(uuid.uuid4())
    game['gameid'] = gameid
    player['playerid'] = gameid
    player['nickname'] = nickname
    player['holdcards'] = []
    player['status'] = False
    game['players'].append(player)

    app.logger.debug(gameid)
    app.logger.debug(game)
    cache.set(gameid, game)
    return gameid


# re:wait the game
@app.route('/<gameid>/waiting')
def waiting_game(gameid):
    game = cache.get(gameid)
    game.status = 'waiting'
    cache.set(gameid, game)
    return 'reset game status'


# join the game
@app.route('/<gameid>/join')
@app.route('/<gameid>/join/<nickname>')
def join_game(gameid, nickname='default'):
    game = cache.get(gameid)
    if game['status'] == 'waiting':
        player = {}

        playerid = str(uuid.uuid4())
        player['playerid'] = playerid
        if nickname == 'default':
            player['nickname'] = playerid
        else:
            player['nickname'] = nickname

        player['holdcards'] = []
        player['status'] = False
        game['players'].append(player)

        cache.set(gameid, game)
        return playerid + ' ,' + player['nickname'] + ' ,' + game['status']
    else:
        return 'Already started'


# processing the game
@app.route('/<gameid>/start')
def start_game(gameid):
    game = cache.get(gameid)
    game['status'] = 'started'

    routelist = copy.copy(game['players'])
    random.shuffle(routelist)
    game['routelist'] = routelist
    game['routeid'] = routelist[0]['playerid']

    players = game['players']

    # shuffle card for delivery
    stocks = list(range(5 * len(game['players'])))

    # delivery the cards
    for player in players:
        while len(player['holdcards']) < 5:
            player['holdcards'].append(stocks.pop(random.randint(0, len(stocks) - 1)))

    cache.set(gameid, game)
    return json.dumps(game['routelist'])


# move on to next player with card
@app.route('/<gameid>/<playerid>/next/<int:cardnum>')
def processing_game(gameid, playerid, cardnum):
    game = cache.get(gameid)

    # previous player
    players = game['routelist']
    prev_player = [player for player in game['players'] if player['playerid'] == playerid][0]
    app.logger.debug(prev_player)

    for hId, holdcard in enumerate(prev_player['holdcards']):
        if holdcard == cardnum:
            prev_player['holdcards'].pop(hId)

    game['routeidx'] = (game['routeidx'] + 1) % len(game['players'])

    # next player
    next_player = players[game['routeidx']]
    app.logger.debug(next_player)
    next_player['holdcards'].append(int(cardnum))
    game['routeid'] = next_player['playerid']

    cache.set(gameid, game)
    return 'go on to the next user'


# change status to sleep
@app.route('/<gameid>/<playerid>/sleep')
def setcard_game(gameid, playerid):
    game = cache.get(gameid)

    for idx, player in enumerate(game['routelist']):
        if player['playerid'] == playerid:
            # go to the sleep
            player['status'] = True
            game['slept'].append(player)
            game['routelist'].pop(idx)

    # available check
    cardtypes = np.array(player['holdcards'])

    cache.set(gameid, game)
    return 'ok'


# all status the game
@app.route('/<gameid>/status')
def game_status(gameid):
    game = cache.get(gameid)

    return json.dumps(game)


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port) # heroku
    # app.run(debug=True)
