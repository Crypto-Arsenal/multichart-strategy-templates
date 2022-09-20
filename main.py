# pip install pyyaml
import yaml
# pip install requests
import requests
import re
import time
import os
# pip install watchdog
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

URL = 'https://crypto-arsenal.io/trading-signal/webhook'

CONFIG = None

with open("./ca_setup.yaml", "r") as stream:
    try:
        CONFIG = yaml.safe_load(stream)
        STRATEGIES_CONFIG = CONFIG.get("STRATEGIES")
        print("loadedd config", CONFIG)
    except yaml.YAMLError as exc:
        print(exc)

DIRECTORY_TO_WATCH = CONFIG.get("WATCH_DIR", "Z:\CA Test")


def parse_and_send_txt(filepath):
    signal = None
    try:
        with open(filepath) as f:
            for line in f:
                signal = line.strip()
    except:
        # print("failed to read signal")
        return

    # print(signal, filepath)

    if not signal:
        # print("signal is none")
        return

    strategyName = re.search("\w*\.*\.txt", filepath).group(0)

    if not strategyName:
        print("invalid filepath")
        return

    strategy_connector = STRATEGIES_CONFIG.get(strategyName)

    if not strategy_connector:
        # print("strategy_connector not found")
        return

    if signal == strategy_connector.get("lastSignal"):
        # print("same signal")
        return

    strategy_connector["lastSignal"] = signal

    curPosition = None
    signal_items = signal.split(",")

    if len(signal_items) > 1:
        curPosition = signal_items[1]

    if not curPosition:
        return

    curPosition = int(curPosition)

    if curPosition == strategy_connector.get("lastPosition"):
        # print("same signal")
        return

    strategy_connector["lastPosition"] = curPosition

    ca_signal = {"action": "update", "connectorName": strategy_connector.get(
        "connectorName"), "connectorToken": strategy_connector.get("connectorToken"), "log": signal}
    print("ca_signal", ca_signal)

    # ⚠️ start a simulation/live trade first to see trades in real time
    response = requests.post(URL, json=ca_signal)
    print("✅" if response.text == "ok" else "⚠️")  # ok


class Watcher:

    def __init__(self):
        self.observer = Observer()

    def run(self):
        event_handler = Handler()
        self.observer.schedule(
            event_handler, DIRECTORY_TO_WATCH, recursive=True)
        self.observer.start()
        try:
            while True:
                time.sleep(3)
        except Exception as e:
            self.observer.stop()
            print("Error", e)

        self.observer.join()


class Handler(FileSystemEventHandler):

    @staticmethod
    def on_any_event(event):
        if event.is_directory:
            return None

        elif event.event_type == 'created':
            # Take any action here when a file is first created.
            print("Received created event - %s." % event.src_path)

        elif event.event_type == 'modified':
            # Taken any action here when a file is modified.
            print("Received modified event 👀 - %s." % event.src_path)
            try:
                parse_and_send_txt(event.src_path)
            except Exception as e:
                print("Failed - notify", e)


if __name__ == '__main__':
    for strategy in STRATEGIES_CONFIG:
        filepath = os.path.join(DIRECTORY_TO_WATCH, strategy)
        print("init filepath ", filepath)
        try:
            parse_and_send_txt(filepath)
        except Exception as e:
            print("Failed - notify", e)
    w = Watcher()
    w.run()
