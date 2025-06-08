# JKLM.fun BombParty WebSocket Bot

A fully **headless**, no-browser, no-WebDriver bot for [JKLM.fun](https://jklm.fun)'s **BombParty** game.  
It connects directly to the game’s WebSocket server and plays valid words based on syllables using a wordlist.

## Features

- No browser automation – **only raw WebSocket**
- Automatically finds words from fragments using a dictionary
- Persistent user token generation to allow joining games
- Joins rooms, reads turns, and sends words automatically
- Configuration via config.json

---

## Requirements

- Python 3.8+
- Dependencies:

```bash
pip install websockets colorama
```

## Setup

Clone the repository:

```bash
git clone https://github.com/KrishhVii/JKLM-bot.git
cd JKLM-bot
```

Edit config.json:

```json
{
  "ROOM_CODE": "ABCD",
  "NICKNAME": "KrishVi",
  "FILE_PATH": "wordlist.txt"
}
```

Add a wordlist.txt file with one word per line:

```text
ilovesyd
hi
ok
...
```

Run the bot:

```bash
python bot.py
```

## User Token

To simulate a persistent identity (like JKLM does with localStorage), we generate a random 16-character token with the allowed character set:

```python
def generate_user_token():
    chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+-"
    return ''.join(chars[secrets.randbelow(len(chars))] for _ in range(16))
```

This allows joining the games and avoids being flagged.

## How It Works

- **First Socket:** Handles room joining and initial handshake.
- **Second Socket:** Handles game logic, syllables, and word sending.
- **Word Search:** When it’s your turn, the bot finds a valid word containing the syllable that hasn’t been used.

Sample logic:

```python
if data.get("currentPlayerPeerId") == peer_id:
    curr_fragment = data.get("syllable", "")
    word = await choose_word(curr_fragment)
    await ws.send(f'42["setWord","{word}",true]')
```

## Customization

- Use your own wordlist to improve performance.
- Adjust the retry limit or delay in choose_word() for better randomness.
- Use colorama to tweak log colors if desired.
- Optionally log all raw WebSocket messages for debugging.

## Notes

- This is for educational purposes only.
- Don’t abuse the game or ruin others’ experience.
- JKLM developers could change their API at any time, which may break this.

## My Coding Journey

This project was born out of curiosity. I wanted to make a bot for JKLM.fun without relying on headless browsers or puppeteers. Instead, I:

- Reverse-engineered WebSocket traffic from browser dev tools.
- Created a Python client using websockets.
- Implemented async logic to respond to real-time game events.
- Designed a word fragment searcher with random.shuffle() to make responses look natural.
- Added proper token generation to simulate localStorage identity.

It was fun and a great way to learn asynchronous Python, WebSocket protocols, and real-world bot creation.

## License

MIT – do whatever you want, just don’t be retarded and make JKLM block everyone 😅

## Contribute

Pull requests and suggestions are welcome.  
Open an issue if you have a bug, idea, or improvement!
