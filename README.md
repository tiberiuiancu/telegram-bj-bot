# Telegram blackjack bot
Telegram blackjack bot that also acts as a dealer.

### How to run
Make sure you have the following python3 packages installed (as well as [python3](https://www.python.org/downloads/)): requests, numpy

#### On linux:
```
sudo pip3 install requests numpy
```

#### On windows:
[Make sure python is in your path](https://projects.raspberrypi.org/en/projects/using-pip-on-windows/5). <br />
[Make sure pip is installed](https://projects.raspberrypi.org/en/projects/using-pip-on-windows/6). <br />
Run cmd as admin and type: 
```
pip install requests numpy
```
First [create a new bot](https://core.telegram.org/bots#6-botfather) and copy the api token that botfather gave you. <br /><br />
Once you clone the repository, you will have to create 2 files in the main folder: <br />
**api_token.txt**: in here paste the api token that botfather gave you when you created the bot.<br />
**OPTIONAL: chat_id.txt**: in here place the chat id in which your bot will run.<br />
NOTE: if you do not provide a chat id, the bot will listen on all groups and private chats for the /start command.<br />

#### How to get a chat's id
1. If the chat is a group, add the bot to the group and make it admin. Also disable the privacy mode of the bot (this might not be needed but I haven't tested with privacy mode enabled). Send a message in that group.<br /><br />
If the chat you want is a private chat, just message the bot anything.<br /><br />
2. Make sure that the bot's api token is in **api_token.txt**. From the downloaded project folder run get_chat_id.py in terminal (or cmd on Windows).
```
python3 get_chat_id.py
```
For each chat the bot received a message from, you should see an id. Copy that id and paste it into **api_token.txt**. (You have to create this file yourself).<br />

Now that all that is done, simply run bot.py:
```
python3 bot.py
```
<br />
Now to run the bot just type /start in the chat.<br />

#### Dealer algorithm
Given the bets of all players and their cards, the dealer computes the expecteed outcome of hit and stand:<br />
**stand**: compares the value of the player's cards with its own and decides, based on the bets, the value of standing.<br />
**hit**: knowing the probability of drawing each card (or otherwise assuming an even probability distribution), it computes the expected value by multiplying the probability of drawing a specific card by the maximum expected value of hitting and standing (while having that card in hand). <br /><br />
In other words:
```
max_expected_value(game_state) = max( expected_value(stand, game_state), max_expected_value(game_state.draw_card()) )
```
Doing it recursively means that there are millions of possible states, but in reality we only care about the sum of the cards (20 possible states: 2 to 21) and if the dealer has an ace (2 possible states: true or false). Therefore we only have to worry about a maximum of 40 states that we can cache and use later in recursion. 
