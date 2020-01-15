from game import Game, CARDS_IN_DECK

aces_cache = {}
non_aces_cache = {}

def compute_unfinished(game_state, outcomes, split_queue, bets):
    # returns a list of all unfinished games (that the dealer has to take into account)
    global aces_cache
    global non_aces_cache

    aces_cache = {}
    non_aces_cache = {}

    tbds = []
    for i, value in enumerate(outcomes):
        if value == 'split':
            for j, cards in enumerate(split_queue[i]):
                if Game.get_cards_value(cards) <= 21:
                    tbds.append([cards, bets[i][j]])
        elif value == 'tbd':
            tbds.append([game_state[i], bets[i]])

    return tbds


def compute_expected_stand(dealer_cards, tbds):
    # computes the expected value of move stand
    expected = 0
    dealer_cards_value = Game.get_cards_value(dealer_cards)
    for tbd in tbds:
        player_cards_value = Game.get_cards_value(tbd[0])
        if player_cards_value < dealer_cards_value:
            expected += tbd[1]
        elif player_cards_value > dealer_cards_value:
            expected -= tbd[1]

    return expected


def compute_expected(dealer_cards, tbds, probabilities=None):
    # computes the best expected value possible
    if Game.is_bust(dealer_cards):
        return -sum([i[1] for i in tbds])

    dealer_value = Game.get_cards_value(dealer_cards)
    if 0 in dealer_cards:
        if dealer_value in aces_cache:
            return aces_cache[dealer_value]
    elif dealer_value in non_aces_cache:
        return non_aces_cache[dealer_value]

    if probabilities is None:
        probabilities = [1/CARDS_IN_DECK for _ in range(CARDS_IN_DECK)]

    # compute expected value of hit
    expected = 0
    basic_prob = 1/CARDS_IN_DECK
    for i in range(CARDS_IN_DECK):
        if probabilities is None:
            expected += basic_prob * compute_expected(dealer_cards + [i], tbds)
        else:
            expected += probabilities[i] * compute_expected(dealer_cards + [i], tbds, probabilities)

    # returns the maximum between the expected of stand and hit
    res = max(compute_expected_stand(dealer_cards, tbds), expected)

    if 0 in dealer_cards:
        aces_cache[dealer_value] = res
    else:
        non_aces_cache[dealer_value] = res

    return res


def get_best_move(game, bets, hard_mode=False):
    # takes a game object and the bets of each player and returns the best move for the dealer
    # hard mode allows the dealer to peek into the deck and see how many cards of each type there are
    tbds = compute_unfinished(game.game_state, game.outcomes, game.split_queue, bets)

    if hard_mode:
        probabilities = [game.cards[i] / game.n_cards for i in range(CARDS_IN_DECK)]
    else:
        probabilities = None

    if compute_expected(game.game_state[-1], tbds, probabilities) == compute_expected_stand(game.game_state[-1], tbds):
        return 'stand'
    else:
        return 'hit'

