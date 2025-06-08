import asyncio
import websockets
import json
import random
from colorama import Fore, Style, init
import secrets
import secrets

def generate_user_token():
    chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+-"
    return ''.join(chars[secrets.randbelow(len(chars))] for _ in range(16))

with open('config.json', 'r') as f:
    config = json.load(f)
init(autoreset=True)

URL = "wss://phoenix.jklm.fun/socket.io/?EIO=4&transport=websocket"
ROOM_CODE = config.get("ROOM_CODE", "")
NICKNAME = config.get("NICKNAME", "KrishVi")
FILE_PATH = config.get("FILE_PATH", "wordlist.txt")
USER_TOKEN = generate_user_token()
GAME_ID = "bombparty"
LANGUAGE = "en-US"
if not ROOM_CODE:
    print(Fore.RED + "Error: ROOM_CODE is not set in config.json")
    exit(1)
blacklist = ["2", "setPlayerWord", "chatterAdded", "setPlayerCount", "chatterRemoved", "nextTurn", "livesLost", "addPlayer", "clearUsedWords", "setMilestone", "correctWord"]
with open(FILE_PATH, 'r') as f:
    wordlist = [line.strip().lower() for line in f if line.strip()]

used_words = set()

def log(symbol, msg, color=Fore.WHITE):
    print(f"{color}{symbol} {msg}{Style.RESET_ALL}")
log("[*]", f"Starting JKLm Bot with Token -> [{USER_TOKEN}]", Fore.YELLOW)
async def choose_word(fragment, max_tries=3):
    fragment = fragment.lower()
    tries = 0
    while tries < max_tries:
        random.shuffle(wordlist)
        for word in wordlist:
            if fragment in word and word not in used_words:
                used_words.add(word)
                return word
        tries += 1
        await asyncio.sleep(0.1)
    return "placeholder"

async def first_socket(start_second_event: asyncio.Event):
    async with websockets.connect(URL) as ws:
        greeting = await ws.recv()
        log("[*]", f"First socket greeting: {greeting}", Fore.CYAN)

        await ws.send("40")
        log("[+]", "Sent 40 (handshake)", Fore.GREEN)

        join_msg = f'420["joinRoom",{{"roomCode":"{ROOM_CODE}","userToken":"{USER_TOKEN}","nickname":"{NICKNAME}","language":"{LANGUAGE}"}}]'
        await ws.send(join_msg)
        log("[+]", f"Sent joinRoom to room '{ROOM_CODE}' as '{NICKNAME}'", Fore.GREEN)

        first_ping_received = False
        async for message in ws:
            if not any(bad in message for bad in blacklist):
                log("[<]", f"WS ⇐ {message}", Fore.MAGENTA)
            if message == "2":
                await ws.send("3")
                if not first_ping_received:
                    first_ping_received = True
                    log("[=]", "Received ping. Triggering second socket.", Fore.YELLOW)
                    start_second_event.set()
            if message.startswith("42"):
                try:
                    payload = json.loads(message[2:])
                except Exception:
                    log("[!]", "Failed to parse payload", Fore.RED)
                    continue
                if not isinstance(payload, list) or len(payload) < 2:
                    continue

                event = payload[0]
                data = payload[1]
                if event == "chatterAdded":
                    log("[+]", f"Chatter added: {data.get('nickname', 'Unknown')}", Fore.GREEN)

async def second_socket():
    peer_id = None
    curr_fragment = ""

    async with websockets.connect(URL) as ws:
        await ws.recv()
        await ws.send("40")
        log("[*]", "Second socket connected", Fore.CYAN)

        await ws.send(f'42["joinGame","{GAME_ID}","{ROOM_CODE}","{USER_TOKEN}"]')
        log("[+]", "Sent joinGame", Fore.GREEN)

        await asyncio.sleep(1)
        await ws.send('42["joinRound"]')
        log("[+]", "Sent joinRound", Fore.GREEN)

        async for message in ws:
            if not any(bad in message for bad in blacklist):
                log("[<]", f"WS ⇐ {message}", Fore.MAGENTA)

            if message == "2":
                await ws.send("3")

            if message.startswith("42"):
                try:
                    payload = json.loads(message[2:])
                except Exception:
                    log("[!]", "Failed to parse payload", Fore.RED)
                    continue

                if not isinstance(payload, list) or len(payload) < 2:
                    continue

                event = payload[0]
                data = payload[1]

                if event == "addPlayer" and data.get("profile", {}).get("nickname") == NICKNAME:
                    peer_id = data["profile"]["peerId"]
                    log("[+]", f"Assigned peerId: {peer_id}", Fore.BLUE)

                elif event == "setMilestone":
                    if data.get("name") == "round":
                        if data.get("currentPlayerPeerId") == peer_id:
                            curr_fragment = data.get("syllable", "")
                            word = await choose_word(curr_fragment)
                            log("[>]", f"Your turn: Fragment '{curr_fragment}' ⇒ Word '{word}'", Fore.CYAN)
                            await ws.send(f'42["setWord","{word}",true]')
                    elif data.get("name") == "seating":
                        if data.get('lastRound').get('winner').get('peerId') == peer_id:
                            log("[*]", "You won the last round!", Fore.GREEN)
                        


                elif event == "nextTurn":
                    if len(payload) >= 3:
                        turn_peer_id = payload[1]
                        curr_fragment = payload[2]
                        if peer_id == turn_peer_id:
                            word = await choose_word(curr_fragment)
                            log("[>]", f"Next turn: Fragment '{curr_fragment}' ⇒ Word '{word}'", Fore.CYAN)
                            await ws.send(f'42["setWord","{word}",true]')

                elif event == "failWord" and data == peer_id:
                    word = await choose_word(curr_fragment)
                    log("[!]", f"Retry after failure ⇒ New word: '{word}'", Fore.RED)
                    await ws.send(f'42["setWord","{word}",true]')
                elif event == "addPlayer":
                    if not data.get("profile", {}).get("peerId") == peer_id:
                        log("[+]", f"New player added to game: {data.get('profile', {}).get('nickname', 'Unknown')}", Fore.GREEN)
                elif event == "correctWord":
                    if data.get("playerPeerId") == peer_id:
                        log("[*]", f"Correct word played by us.", Fore.GREEN)
                    else:
                        log("[*]", f"Other player played correct word.", Fore.YELLOW)

async def main():
    start_second_event = asyncio.Event()

    log("[*]", "Connecting to first socket...", Fore.YELLOW)
    task1 = asyncio.create_task(first_socket(start_second_event))
    await start_second_event.wait()
    
    log("[=]", "First socket ready. Launching second socket...", Fore.YELLOW)
    task2 = asyncio.create_task(second_socket())

    await asyncio.gather(task1, task2)

if __name__ == "__main__":
    asyncio.run(main())
