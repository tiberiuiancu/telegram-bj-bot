import numpy as np

CARDS_IN_DECK = 13

class Game:
    def __init__(self, n_packs=6, min_cards_percentage=0.5):
        self.n_packs = n_packs * 4
        self.cards = {i : self.n_packs for i in range(CARDS_IN_DECK)}
        self.max_cards = self.n_packs * CARDS_IN_DECK
        self.n_cards = self.max_cards
        self.game_state = None
        self.min_cards_percentage = min_cards_percentage
        self.game_over = False
        self.n_players = 0
        self.to_play = None
        self.outcomes = None
        self.split_queue = []
        self.split_index = -1
        self.deck_replaced = False


    def restart(self):
        self.__init__(self.n_packs // CARDS_IN_DECK, self.min_cards_percentage)


    def replace_deck(self):
        self.cards = {i: self.n_packs for i in range(CARDS_IN_DECK)}
        self.n_cards = self.max_cards
        self.deck_replaced = True


    def deal_card(self):
        if self.n_cards < self.max_cards * self.min_cards_percentage:
            print('too few cards...replacing deck')
            self.replace_deck()

        chosen = np.random.choice(CARDS_IN_DECK, p=[self.cards[i] / self.n_cards for i in range(CARDS_IN_DECK)])
        self.n_cards -= 1
        self.cards[chosen] -= 1
        return chosen


    def deal(self, n_players):
        if n_players < 1:
            return []

        cards = []
        for i in range(n_players + 1):
            cards.append([self.deal_card(), self.deal_card()])

        return cards


    @staticmethod
    def human_readable_cards(cards):
        if type(cards) != list:
            return []

        ret = []
        for x in cards:
            if x == 0:
                ret.append('A')
            elif x == 10:
                ret.append('J')
            elif x == 11:
                ret.append('Q')
            elif x == 12:
                ret.append('K')
            else:
                ret.append(str(x + 1))

        return ', '.join(ret)


    @staticmethod
    def get_cards_value(cards):
        if type(cards) != list:
            return -1

        cards_val = 0
        ace_cnt = 0
        for card in cards:
            if card == 0:
                ace_cnt += 1
            elif card >= 9:
                cards_val += 10
            else:
                cards_val += card + 1

        if ace_cnt == 0:
            return cards_val

        if cards_val + 11 + ace_cnt - 1 > 21:
            cards_val += ace_cnt
        else:
            cards_val += 11 + ace_cnt - 1

        return cards_val


    @staticmethod
    def is_blackjack(cards):
        if type(cards) != list or len(cards) != 2:
            return False

        if (cards[0] == 0 and 9 <= cards[1] <= 12) or (cards[1] == 0 and 9 <= cards[0] <= 12):
            return True

        return False


    @staticmethod
    def is_bust(cards):
        if type(cards) != list or len(cards) < 2:
            return False

        cards_val = 0
        ace_cnt = 0
        for card in cards:
            if card == 0:
                ace_cnt += 1
            elif card >= 9:
                cards_val += 10
            else:
                cards_val += card + 1

        if ace_cnt == 0:
            return cards_val > 21

        if cards_val + 11 + ace_cnt - 1 > 21:
            cards_val += ace_cnt
        else:
            return False

        return cards_val > 21


    def dealer_blackjack(self):
        # returns a list of rewards: 0 if the player lost, 1 if the player drew
        if Game.is_blackjack(self.game_state[-1]):
            rewards = []
            # check if any other player has blackjack
            for player in self.game_state[:-1]:
                if Game.is_blackjack(player):
                    rewards.append(1)
                else:
                    rewards.append(0)

            return rewards

        return []


    def start_round(self, n_players):
        self.n_players = n_players
        self.to_play = 0
        self.game_over = False
        self.game_state = self.deal(n_players)
        self.outcomes = [None for _ in range(n_players)]
        self.split_queue = [[] for _ in range(n_players)]

        dealer_has_blackjack = self.dealer_blackjack()
        if dealer_has_blackjack:
            self.game_over = True
        return dealer_has_blackjack


    def get_valid_moves(self):
        if self.game_over:
            return []

        if self.to_play == self.n_players:
            # dealer's turn to play
            return ['stand', 'hit']

        # check moves after player split
        if self.split_queue[self.to_play]:
            player_cards = self.split_queue[self.to_play][self.split_index]
        else:
            player_cards = self.game_state[self.to_play]

        if Game.is_bust(player_cards):
            return []

        valid_moves = ['hit', 'stand']

        # check split, double and surrender
        if len(player_cards) == 2:
            valid_moves.append('double')
            valid_moves.append('surrender')
            if player_cards[0] == player_cards[1]:
                valid_moves.append('split')

        return valid_moves


    def step(self, move=None):
        if self.game_over:
            print('WARNING: STEP REQUESTED WHEN GAME ALREADY FINISHED')
            return None

        if move is None and Game.is_blackjack(self.game_state[self.to_play]):
            self.outcomes[self.to_play] = 2.5
            self.to_play += 1
            return None

        # check dealer play
        if self.to_play == self.n_players:
            if move == 'stand':
                self.game_over = True
                return self.game_outcome()
            elif move == 'hit':
                self.game_state[-1].append(self.deal_card())
                if self.is_bust(self.game_state[-1]):
                    self.game_over = True
                    return self.game_outcome()
                return self.game_state
            else:
                return None

        # split in play
        if self.split_queue[self.to_play]:
            if move not in self.get_valid_moves():
                print('WARNING: ILLEGAL MOVE.')
                return None
            if move == 'stand':
                self.split_index += 1
            elif move == 'hit':
                self.split_queue[self.to_play][self.split_index].append(self.deal_card())
                if Game.is_bust(self.split_queue[self.to_play][self.split_index]):
                    self.split_index += 1
            elif move == 'split':
                # split one more time
                split_card = self.split_queue[self.to_play][self.split_index][0]
                # split queue will delete the current hand and instead add 2 more hands
                self.split_queue[self.to_play] = self.split_queue[self.to_play][:self.split_index] + \
                                                [split_card, self.deal_card()] + \
                                                [split_card, self.deal_card()] + \
                                                self.split_queue[self.to_play][self.split_index + 1:]
            elif move == 'double':
                self.split_queue[self.to_play][self.split_index].append(self.deal_card())
                self.split_index += 1
            elif move == 'surrender':
                self.split_queue[self.to_play][self.split_index] = []
                self.split_index += 1
            
            if self.split_index >= len(self.split_queue[self.to_play]):
                # split finished; go to the next player
                self.to_play += 1
        elif move not in self.get_valid_moves():
            print('WARNING: ILLEGAL MOVE.')
            return None
        elif move == 'surrender':
            self.outcomes[self.to_play] = 0.5
            self.to_play += 1
        elif move == 'stand':
            self.outcomes[self.to_play] = 'tbd'
            self.to_play += 1
        elif move == 'hit':
            self.game_state[self.to_play].append(self.deal_card())
            if self.is_bust(self.game_state[self.to_play]):
                self.outcomes[self.to_play] = 0
                self.to_play += 1
        elif move == 'double':
            self.game_state[self.to_play].append(self.deal_card())
            if self.is_bust(self.game_state[self.to_play]):
                self.outcomes[self.to_play] = 0
            else:
                self.outcomes[self.to_play] = 'tbd'
            self.to_play += 1
        elif move == 'split':
            split_value = self.game_state[self.to_play][0]
            self.split_queue[self.to_play].append([split_value, self.deal_card()])
            self.split_queue[self.to_play].append([split_value, self.deal_card()])
            self.split_index = 0
            self.outcomes[self.to_play] = 'split'

        return self.game_state, self.game_over


    def game_outcome(self):
        # returns a list (that might contain other lists in case of splits) that will be used to determine the rewards of each player
        dealer_busted = Game.is_bust(self.game_state[-1])
        dealer_value = Game.get_cards_value(self.game_state[-1])

        for i, value in enumerate(self.outcomes):
            if type(value) == int:
                continue
            elif value == 'tbd':
                if dealer_busted:
                    self.outcomes[i] = 2
                else:
                    card_value = Game.get_cards_value(self.game_state[i])
                    if card_value > dealer_value:
                        self.outcomes[i] = 2
                    elif card_value < dealer_value:
                        self.outcomes[i] = 0
                    else:
                        self.outcomes[i] = 1
            elif value == 'split':
                outcome = []
                for cards in self.split_queue[i]:
                    if Game.is_bust(cards):
                        outcome.append(0)
                    elif dealer_busted:
                        outcome.append(2)
                    else:
                        card_value = Game.get_cards_value(cards)
                        if card_value > dealer_value:
                            outcome.append(2)
                        elif card_value < dealer_value:
                            outcome.append(0)
                        else:
                            outcome.append(1)
                self.outcomes[i] = outcome

        return self.outcomes
