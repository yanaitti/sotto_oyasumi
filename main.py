from flask import Flask, Response, render_template, url_for
from flask_caching import Cache
import uuid
import random
from collections import Counter
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


app = Flask(__name__)


@app.context_processor
def override_url_for():
    return dict(url_for=dated_url_for)


def dated_url_for(endpoint, **values):
    if endpoint == 'static':
        filename = values.get('filename', None)
        if filename:
            file_path = os.path.join(app.root_path,
                                     endpoint, filename)
            values['q'] = int(os.stat(file_path).st_mtime)
    return url_for(endpoint, **values)


@app.after_request
def add_header(r):
    """
    Add headers to both force latest IE rendering engine or Chrome Frame,
    and also to cache the rendered page for 10 minutes.
    """
    r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    r.headers['Cache-Control'] = 'public, max-age=0'
    return r


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


@app.route('/<gameid>/join')
def invited_join_game(gameid):
    print('gameid:' + gameid)
    return render_template('index.html', gameid=gameid)


# join the game
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
    game['routeidx'] = 0
    game['slept'] = []

    players = game['players']

    # shuffle card for delivery
    stocks = list(range(5 * len(game['players'])))

    # delivery the cards
    for player in players:
        player['holdcards'] = []
        for idx in list(range(5)):
            player['holdcards'].append(stocks.pop(random.randint(0, len(stocks) - 1)))
        player['status'] = False

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

    pIdx, player = [(_pIdx, _player) for _pIdx, _player in enumerate(game['routelist']) if _player['playerid'] == playerid][0]

    if len(game['slept']) == 0:
        card = player['holdcards']
        card_wo_j = [_c for _c in card if _c % 5 != 4]
        card_j = [_c for _c in card if _c % 5 == 4]

        # card = [0, 5, 7, 8, 14]
        # # listをnumpy
        card_np = np.array(card_wo_j)

        # 5の商を算出
        card2_np = card_np // 5
        card2_np

        # numpyを配列に変換
        card_array = card2_np.tolist()

        cc = Counter(card_array).most_common()
        if cc[0][1] + len(card_j) < 4:
            return 'ng'

    # go to the sleep
    player['status'] = True
    game['slept'].append(player)
    game['routelist'].pop(pIdx)

    # for idx, player in enumerate(game['routelist']):
    #     if player['playerid'] == playerid:
    #         card = player['holdcards']
    #         card_wo_j = [_c for _c in card if _c % 5 != 4]
    #         card_j = [_c for _c in card if _c % 5 == 4]
    #
    #         # card = [0, 5, 7, 8, 14]
    #         # # listをnumpy
    #         card_np = np.array(card_wo_j)
    #
    #         # 5の商を算出
    #         card2_np = card_np // 5
    #         card2_np
    #
    #         # numpyを配列に変換
    #         card_array = card2_np.tolist()
    #
    #         cc = Counter(card_array).most_common()
    #         if cc[0][1] + len(card_j) >= 4:
    #             # go to the sleep
    #             player['status'] = True
    #             game['slept'].append(player)
    #             game['routelist'].pop(idx)
    #         else:
    #             return 'ng'

    # available check
    # cardtypes = np.array(player['holdcards'])

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
