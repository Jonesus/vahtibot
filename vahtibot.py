import requests
import time

# Get ID from @BotFather and create a file called config.py
# with a single line 'BOT_ID = {your bot ID}'
from config import BOT_ID
from functions import get_data


########################################
#         Important variables          #
########################################


DB_FILENAME = "db.txt"        # Where to save gathered data identifiers
CHATS_FILENAME = "chats.txt"  # Where to save subscribed chats
SLEEP = 30                    # Time to wait between data fetches

DB = []                       # Database in memory
CHATS = []                    # Subscribed chat list in memory


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


def poll_new_chats(chats):
    """ See if any new chats subscribed or unsubscribed for updates """
    updates = get_updates()  # Get all fresh updates

    current_offset = 0
    for update in updates:
        message = update["message"]["text"]
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

    get_updates(current_offset)  # Mark processed updates done


def send_message(text, chat):
    """ Send a text message to chat """
    response = requests.post(
        url="https://api.telegram.org/bot{}/sendMessage".format(BOT_ID),
        data={"chat_id": chat, "text": text, "parse_mode": "Markdown"}
    ).json()
    if response["ok"]:
        return response
    else:
        raise Exception("ERROR: Failed to send message!")


########################################
#            Main function             #
########################################


def main():
    print("INFO: Initializing...")
    DB = load_file(DB_FILENAME)
    CHATS = load_file(CHATS_FILENAME)

    # Initiate main loop
    while True:
        print("INFO: Polling for chat additions or removals...")
        poll_new_chats(CHATS)

        print("INFO: Fetching fresh data...")
        items = get_data()

        print("INFO: Processing data...")
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

        print("INFO: Sleeping for {} secs...".format(SLEEP))
        time.sleep(SLEEP)


if __name__ == "__main__":
    main()
