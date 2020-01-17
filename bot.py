from api import update_all, send_message, remove_keyboard_markup
from time import sleep, time
from entities import User
import re
from game import Game
import json
from dealer import get_best_move
import pickle

try:
    with open('chat_id.txt', 'r') as f:
        chat_id = int(f.readline().strip())
except:
    chat_id = None

game_obj = Game()
INITIAL_MONEY = 10000
user_money = {}


def load_user_money():
    print('[+]loading user money...', end='', flush=True)
    global user_money
    try:
        with open('./database/user_money.pickle', 'rb') as f:
            user_money = pickle.load(f)
        print('done', flush=True)
    except:
        print('failed', flush=True)


def save_user_money():
    print('[+]saving user money...', end='', flush=True)
    try:
        with open('./database/user_money.pickle', 'wb') as f:
            pickle.dump(user_money, f)
        print('done', flush=True)
        return True
    except:
        print('failed', flush=True)
        return False


def user_in_lobby(user, lobby):
    if type(lobby) != list:
        return

    if type(user) != User:
        return

    for x in lobby:
        if x.id == user.id:
            return True

    return False


def remove_user_from_lobby(user, lobby):
    if type(lobby) != list:
        return lobby

    if type(user) != User:
        return lobby

    for i, x in enumerate(lobby):
        if user.id == x.id:
            del lobby[i]
            return lobby

    return lobby


def wait_for(chat_id, msg, must_equal=True, from_user=None, wrong_command_msg=None, max_wait=None):
    if type(msg) == str:
        msg = [msg]

    if type(msg) != list:
        return

    if type(from_user) != int and from_user is not None:
        return

    start_time = time()
    while True:
        msg_list = update_all(chat_id)
        for x in msg_list:
            if x.text is None:
                continue

            for y in msg:
                if (must_equal and x.text == y) or (not must_equal and y in x.text):
                    if from_user is not None and x.user is not None and from_user == x.user.id:
                        return x
                    elif from_user is None:
                        return x
                else:
                    if from_user is not None and x.user is not None and wrong_command_msg is not None:
                        send_message(wrong_command_msg, chat_id, reply_id=x.id)

        if max_wait is not None and time() - start_time > max_wait:
            return
        sleep(0.1)


def start_bot(chat_id=None):
    if chat_id is None:
        print('WARNING: BOT WILL TAKE THE /START COMMAND FROM ALL CHATS AT THE SAME TIME')

    # update messages in order to bot start because of a message while offline
    update_all(chat_id)
    print('[+]bot started...waiting for /start command')
    while True:
        start_game(wait_for(chat_id, msg='/start'))


def wait_for_bets(user_map, chat_id, max_wait=60):
    bets = {}
    send_message('You have ' + str(max_wait) + ' seconds to place your bets with "/bet [amount]"\nExample:\n/bet 13', chat_id)

    send_user_money_str = 'Available funds:\n'
    for user in user_map:
        username = user_map[user].first_name if user_map[user].username is None else '@' + user_map[user].username
        send_user_money_str += username + ': ' + str(user_money[user]) + '\n'
    send_message(send_user_money_str, chat_id)

    start_time = time()
    cnt = 0
    while cnt < len(user_map) and time() - start_time < max_wait:
        for msg in update_all(chat_id):
            if msg.user is None or msg.text is None:
                continue

            # remove double spaces and strip message
            msg_text = msg.text
            msg_text = re.sub(' +', ' ', msg_text.strip())
            msg_text = msg_text.split(' ')
            if len(msg_text) != 2 or msg_text[0] != '/bet':
                continue
            try:
                msg_text[1] = float(msg_text[1])
                if msg.user.id not in user_map:
                    send_message("You are not in the game", chat_id, reply_id=msg.id)
                    continue
            except:
                send_message('To place a bet type "/bet [amount]" where amount is a positive number', chat_id, reply_id=msg.id)
                continue

            if msg_text[1] <= 0:
                send_message('Bets must be greater than 0', chat_id, reply_id=msg.id)
                continue

            if msg_text[1] <= user_money[msg.user.id]:
                if msg.user.id not in bets:
                    send_message(msg.user.first_name + ' placed ' + str(msg_text[1]), chat_id)
                    cnt += 1
                else:
                    send_message('Bet of ' + msg.user.first_name + ' updated to: ' + str(msg_text[1]), chat_id)
                bets[msg.user.id] = msg_text[1]
            else:
                send_message('You only have ' + str(user_money[msg.user.id]) + ' money', chat_id, reply_id=msg.id)

    send_message('Betting is over', chat_id)
    no_bet = []
    for user in user_map:
        if user not in bets:
            no_bet.append(user)

    if len(no_bet) > 0:
        no_bet_str = 'The following players have not placed bets and will be excluded from this round: '
        for user in no_bet:
            no_bet_str += user_map[user].first_name + ' '
            del user_map[user]
        send_message(no_bet_str, chat_id)

    if len(user_map) > 0:
        final_bets_str = 'Final bets:\n'
        for user in bets:
            final_bets_str += user_map[user].first_name + ': ' + str(bets[user]) + '\n'

        send_message(final_bets_str, chat_id)

    return bets


def start_game(starting_message):
    if starting_message.user is None:
        return

    chat_id = starting_message.chat.id
    lobby_leader = starting_message.user
    users_in_lobby = [lobby_leader]

    # give lobby leader INITIAL_MONEY funds if they have never played
    if lobby_leader.id not in user_money:
        user_money[lobby_leader.id] = INITIAL_MONEY
        username = '@' + lobby_leader.username if lobby_leader.username is not None else lobby_leader.first_name
        send_message(username + ' you now have ' + str(INITIAL_MONEY) + ' credits!\nBet them wisely.', chat_id)


    send_message('Lobby commands:\n"/join" to join the lobby\n"/exit" to exit the lobby"\n"/play" to start the game\n"/stop" to stop the game\n"/funds" to see your funds',
                 chat_id, reply_markup=remove_keyboard_markup)

    while True:
        last_command = wait_for(chat_id, msg=['/join', '/exit', '/play', '/stop', '/funds'])

        if last_command.text == '/join':
            if last_command.user is None:
                continue
            else:
                if user_in_lobby(last_command.user, users_in_lobby):
                    send_message('You are already in the lobby', chat_id, reply_id=last_command.id)
                else:
                    if last_command.user.id not in user_money:
                        user_money[last_command.user.id] = INITIAL_MONEY
                        username = '@' + last_command.user.username if last_command.user.username is not None else last_command.user.first_name
                        send_message(username + ' you now have ' + str(INITIAL_MONEY) + ' credits!.', chat_id)
                    users_in_lobby.append(last_command.user)
                    send_message(last_command.user.first_name + ' joined the lobby', chat_id)
        elif last_command.text == '/exit':
            if last_command.user is not None:
                if user_in_lobby(last_command.user, users_in_lobby):
                    users_in_lobby = remove_user_from_lobby(last_command.user, users_in_lobby)
                    send_message(last_command.user.first_name + ' left the lobby', chat_id, reply_id=last_command.id)
                    if len(users_in_lobby) == 0:
                        send_message('Lobby is empty. Exitting', chat_id)
                        return
                    elif last_command.user.id == lobby_leader.id:
                        lobby_leader = users_in_lobby[0]
                        send_message('The lobby leader left; ' + lobby_leader.first_name + ' is now the new leader', chat_id)
                else:
                    send_message('You are not in the lobby', chat_id, reply_id=last_command.id)
        elif last_command.text == '/stop':
            if last_command.user.id == lobby_leader.id:
                send_message('Stopped the game', chat_id, reply_id=last_command.id)
                save_user_money()
                return
            else:
                send_message('Only the lobby leader can stop the game', chat_id, reply_id=last_command.id)
        elif last_command.text == '/play':
            if last_command.user.id == lobby_leader.id:
                start_game_msg = 'Starting game with players: '
                for player in users_in_lobby:
                    start_game_msg += player.first_name + ' '
                send_message(start_game_msg, chat_id)
                start_round(users_in_lobby, chat_id)
                send_message('Lobby commands:\n"/join" to join the lobby\n"/exit" to exit the lobby"\n"/play" to start the game\n"/stop" to stop the game\n"/funds" to see your funds',
                    chat_id, reply_markup=remove_keyboard_markup)
            else:
                send_message('Only the lobby leader can start the game', chat_id, reply_id=last_command.id)
        elif last_command.text == '/funds':
            if last_command.user.id in user_money:
                send_message('You have ' + str(user_money[last_command.user.id]) + ' funds', chat_id, reply_id=last_command.id)

        sleep(0.5)


def end_of_game_message(outcome, bets, user_map):
    if type(outcome) != list:
        return "Error"

    results = {}

    game_end_str = "Outcome of the game:\n"
    sum = 0
    for x, user in zip(outcome, user_map):
        if (type(bets[user]) == float or type(bets[user]) == int) and (type(x) == int or type(x) == float):
            sum += (x - 1) * bets[user]
            game_end_str += user_map[user].first_name + ': ' + str((x - 1) * bets[user]) + '\n'
            results[user] = (x - 1) * bets[user]
        elif type(bets[user]) == list and type(x) == list:
            s = 0
            for i, j in zip(x, bets[user]):
                s += (i - 1) * j
            game_end_str += user_map[user].first_name + ': ' + str(s) + '\n'
            results[user] = s
            sum += s

    game_end_str += 'Dealer: ' + str(-sum)
    return game_end_str, results


def start_of_game_message(game_obj, user_map):
    # generates message with dealer and user cards to be displayed on round start
    game_start_str = "Cards:\n"
    for i, user in enumerate(user_map):
        game_start_str += user_map[user].first_name + ': ' + Game.human_readable_cards(game_obj.game_state[i]) + '\n'
    game_start_str += 'Dealer: ' + Game.human_readable_cards(game_obj.game_state[-1])
    game_start_str = game_start_str[:-1] + '?'

    return game_start_str


def make_keyboard(valid_moves=None):
    if len(valid_moves) == 0:
        return ""

    if len(valid_moves) == 1:
        keyboard = {
            'keyboard': [
                [valid_moves[0]]
            ],
            'selective': True
        }

    elif len(valid_moves) == 2:
        keyboard = {
            'keyboard': [
                [valid_moves[0], valid_moves[1]]
            ],
            'selective': True
        }

    elif len(valid_moves) == 3:
        keyboard = {
            'keyboard': [
                [valid_moves[0], valid_moves[1], valid_moves[2]]
            ],
            'selective': True
        }

    elif len(valid_moves) == 4:
        keyboard = {
            'keyboard': [
                [valid_moves[0], valid_moves[1]],
                [valid_moves[2], valid_moves[3]]
            ],
            'selective': True
        }

    else:
        keyboard = {
            'keyboard': [
                [valid_moves[0], valid_moves[1]],
                [valid_moves[2], valid_moves[3], valid_moves[4]]
            ],
            'selective': True
        }

    return json.dumps(keyboard)


def start_round(users, chat_id):
    user_map = {user.id : user for user in users}
    bets = wait_for_bets(user_map, chat_id, max_wait=60)

    if len(user_map) == 0:
        send_message("All players failed to bet...how do you even", chat_id)
        return

    outcome = game_obj.start_round(len(user_map))
    send_message(start_of_game_message(game_obj, user_map), chat_id)

    # case where dealer has blackjack
    if outcome:
        send_message("Dealer blackjack!", chat_id)
        end_message, results = end_of_game_message(outcome, bets, user_map)
        for user in results:
            user_money[user] += results[user]
        send_message(end_message, chat_id)
        return

    # dealer bets holds the bets of each player as needed for the AI
    dealer_bets = [0 for _ in range(game_obj.n_players)]
    for i, user in enumerate(user_map):
        base_user_bet = bets[user]
        dealer_bets[i] = base_user_bet
        name = user_map[user].first_name if user_map[user].username is None else '@' + user_map[user].username

        if Game.is_blackjack(game_obj.game_state[i]):
            move_msg = name + ' you have a blackjack'
            send_message(move_msg, chat_id)
            # empty step to skip player turn
            game_obj.step()
            continue

        while i == game_obj.to_play:
            valid_moves = game_obj.get_valid_moves()

            # remove double if the user doesn't have enough money
            if user_money[user] < 2 * base_user_bet and 'double' in valid_moves:
                valid_moves.remove('double')

            # remove split if the user doesn't have enough money
            # case1: this is the first time the user splits: doubles the bet
            # case2: user has split this turn before, so see if one more split can be done
            if 'split' in valid_moves and \
                    ((game_obj.split_queue[i] and user_money[user] < (len(game_obj.split_queue[i]) + 1) * base_user_bet) or
                    (not game_obj.split_queue[i] and user_money[user] < 2 * base_user_bet)):
                valid_moves.remove('split')

            if game_obj.split_queue[i]:
                move_msg = name + ' split hand to play:\n' + Game.human_readable_cards(game_obj.split_queue[i][game_obj.split_index]) + '\nValid moves: ' + ', '.join(valid_moves)
                send_message(move_msg, chat_id, reply_markup=make_keyboard(valid_moves))
            else:
                move_msg = name + ' your cards:\n' + Game.human_readable_cards(game_obj.game_state[i]) + '\nValid moves: ' + ', '.join(valid_moves)
                send_message(move_msg, chat_id, reply_markup=make_keyboard(valid_moves))

            msg = wait_for(chat_id, valid_moves, from_user=user, max_wait=30)
            if msg is None:
                send_message('Time\'s up. Move defaults to stand', chat_id)
                game_obj.step('stand')
                continue

            last_split_index = game_obj.split_index
            game_obj.step(msg.text)
            if game_obj.split_queue[i]:
                if msg.text == 'split' or (msg.text == 'hit' and game_obj.split_index == last_split_index):
                    player_cards = game_obj.split_queue[i][game_obj.split_index]
                else:
                    player_cards = game_obj.split_queue[i][game_obj.split_index - 1]
            else:
                player_cards = game_obj.game_state[i]

            if msg.text == 'double':
                dealer_bets[i] = 2 * base_user_bet
                bets[user] = 2 * base_user_bet
                move_msg = name + ' your cards:\n' + Game.human_readable_cards(player_cards)
                if game_obj.is_bust(player_cards):
                    move_msg += '\nBUST'
                send_message(move_msg, chat_id)
            elif msg.text == 'hit' and Game.is_bust(player_cards):
                move_msg = name + ' your cards: \n' + Game.human_readable_cards(player_cards) + '\nBUST'
                send_message(move_msg, chat_id)
            elif msg.text == 'split':
                if type(bets[user]) == float:
                    bets[user] = [base_user_bet, base_user_bet]
                    dealer_bets[i] = [base_user_bet, base_user_bet]
                else:
                    bets[user].append(base_user_bet)
                    dealer_bets[i].append(base_user_bet)

    # do dealer play
    while not game_obj.game_over:
        send_message('Dealer cards:\n' + game_obj.human_readable_cards(game_obj.game_state[-1]), chat_id)
        dealer_move = get_best_move(game_obj, dealer_bets, hard_mode=True)
        send_message('Dealer chose to ' + dealer_move, chat_id)
        game_obj.step(dealer_move)
        if Game.is_bust(game_obj.game_state[-1]):
            send_message('Dealer cards:\n' + Game.human_readable_cards(game_obj.game_state[-1]) +'\nDealer BUST', chat_id)

    game_end_msg, results = end_of_game_message(game_obj.outcomes, bets, user_map)
    send_message(game_end_msg, chat_id, reply_markup=remove_keyboard_markup)

    for user in results:
        user_money[user] += results[user]

    save_user_money()
    if game_obj.deck_replaced:
        send_message("Deck has been replaced", chat_id)
        game_obj.deck_replaced = False


if __name__ == '__main__':
    load_user_money()
    start_bot(chat_id)
