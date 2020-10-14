import requests
import time
import random

# Get ID from @BotFather and create a file called config.py
# with a single line 'BOT_ID = {your bot ID}'
from config import BOT_ID
from functions import get_data


########################################
#         Important variables          #
########################################


DB_FILENAME = "db.txt"        # Where to save gathered data identifiers
CHATS_FILENAME = "chats.txt"  # Where to save subscribed chats
QUERIES_FILENAME = "queries.txt"
SLEEP = 30                   # Time to wait between data fetches
VARIANCE = 30

DB = []                       # Database in memory
CHATS = []                    # Subscribed chat list in memory
QUERIES = []


########################################
#           Helper functions           #
########################################


def load_file(filename):
    """ Load file into in-memory list """
    arr = []
    with open(filename, "a+") as f:
        f.seek(0)
        for row in f:
            arr.append(row.rstrip())
    return arr


def append_file(filename, text):
    """ Add a line of text to file """
    with open(filename, "a") as f:
        f.write(text + "\n")


def remove_from_file(filename, text):
    """ Remove a line of text from file """
    with open(filename, "r+") as f:
        lines = f.readlines()
        f.seek(0)
        for line in lines:
            if line != text + "\n":
                f.write(line)
        f.truncate()


def get_updates(offset=0):
    """ Get all Telegram updates """
    response = requests.get(
        url="https://api.telegram.org/bot{}/getUpdates".format(BOT_ID),
        data={"offset": offset}
    ).json()

    if response["ok"]:
        return response["result"]
    else:
        raise Exception("ERROR: Failed to get updates!")


def poll_new_chats(chats, queries, db):
    """ See if any new chats subscribed or unsubscribed for updates """
    updates = get_updates()  # Get all fresh updates

    current_offset = 0
    for update in updates:
        try:
            message = update["message"]["text"]
        except KeyError:
            continue
        chat_id = str(update["message"]["chat"]["id"])
        current_offset = update["update_id"]

        if message == "/start" and chat_id not in chats:
            append_file(CHATS_FILENAME, chat_id)
            chats.append(chat_id)
            send_message("I will now spam you :)", chat_id)
            print("INFO: Added chat {}".format(chat_id))
        elif message == "/stop" and chat_id in chats:
            remove_from_file(CHATS_FILENAME, chat_id)
            chats.remove(chat_id)
            send_message("I will stop spamming you :(", chat_id)
            print("INFO: Removed chat {}".format(chat_id))
        elif message.startswith("/add"):
            query = message.split()[1]
            if query in queries:
                continue
            append_file(QUERIES_FILENAME, query)
            queries.append(query)

            items = get_data(query)
            for item in items:
                identifier = item["identifier"]
                if identifier not in db:
                    db.append(identifier)
                    append_file(DB_FILENAME, identifier)

            send_message("Added query for {}".format(query), chat_id)
            print("INFO: Added query {}".format(query))
        elif message.startswith("/remove"):
            query = message.split()[1]
            if query not in queries:
                continue
            remove_from_file_file(QUERIES_FILENAME, query)
            queries.remove(query)
            send_message("Removed query {}".format(query), chat_id)
            print("INFO: Removed query {}".format(query))


    get_updates(current_offset)  # Mark processed updates done


def send_message(text, chat):
    """ Send a text message to chat """
    response = requests.post(
        url="https://api.telegram.org/bot{}/sendMessage".format(BOT_ID),
        data={"chat_id": chat, "text": text}
    ).json()
    if response["ok"]:
        return response
    else:
        print(response)
        raise Exception("ERROR: Failed to send message!")


########################################
#            Main function             #
########################################


def main():
    print("INFO: Initializing...")
    DB = load_file(DB_FILENAME)
    CHATS = load_file(CHATS_FILENAME)
    QUERIES = load_file(QUERIES_FILENAME)

    # Initiate main loop
    while True:
        print("INFO: Polling for chat additions or removals...")
        poll_new_chats(CHATS, QUERIES, DB)

        print("INFO: Fetching fresh data...")
        for query in QUERIES:
            items = get_data(query)
    
            print("INFO: Processing data for {}...".format(query))
            for item in items:
                identifier = item["identifier"]
                message = item["message"]
    
                if identifier not in DB:
                    print("INFO: Sending messages...")
                    for chat in CHATS:
                        send_message(message, int(chat))
                        time.sleep(1)
    
                    append_file(DB_FILENAME, identifier)
                    DB.append(identifier)
    
            sleep_duration = SLEEP + random.randint(0, VARIANCE)
            print("INFO: Sleeping for {} secs...".format(sleep_duration))
            time.sleep(sleep_duration)
        time.sleep(10)


if __name__ == "__main__":
    main()
