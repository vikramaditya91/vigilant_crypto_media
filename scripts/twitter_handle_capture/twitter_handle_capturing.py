import re
import twitter
import pathlib
import json
import requests
from binance import client
from googlesearch import search
from collections import OrderedDict

def get_all_base_assets():
    a = client.Client("", "")
    b = a.get_exchange_info()
    symbols = b["symbols"]
    all_base_assets = set()
    [all_base_assets.add(item["baseAsset"]) for item in symbols]
    return all_base_assets


def get_number_of_followers(twitter_handle):
    response = requests.get(
        f"https://cdn.syndication.twimg.com/widgets/followbutton/info.json?screen_names={twitter_handle}")
    try:
        num_followers = re.search(r'"followers_count":(.*?),', response.content.decode()).groups(0)[0]
    except:
        num_followers = 0
    num_followers = int(num_followers)
    return num_followers


def get_handle_with_most_followers(list_of_handles, top=1):
    handle_followers_dict = OrderedDict()
    if len(list_of_handles) == 1:
        return list_of_handles[0]
    for tweet_handle in list_of_handles:
        if any(exchange_handle in tweet_handle for exchange_handle in ["binance", "coinbase", "kucoin", "bitfinex"]):
            continue
        num_followers = get_number_of_followers(tweet_handle)
        handle_followers_dict[tweet_handle] = num_followers
    sorted_list = sorted(handle_followers_dict.items(), key=lambda x: x[1])
    required_items =  sorted_list[-min(top, len(sorted_list)):]
    required_items.reverse()
    return [item[0] for item in required_items]


def get_handle_from_search_lists(search_list):
    matched_handles = []
    for item in search_list:
        if item.startswith("https://twitter.com/hashtag") is False:
            if item.startswith("https://twitter.com/") and item.endswith("?lang=en"):
                if item.find("/status/") == -1 and item.find("/media/") == -1:
                    matched_handles.append(re.match(r"https://twitter.com/(.*)\?lang=en", item).group(1))
                elif item.find("/media/") == -1:
                    matched_handles.append(re.match(r"https://twitter.com/(.*)/status/(.*)\?lang=en", item).group(1))
                elif item.find("/status/") == -1:
                    matched_handles.append(re.match(r"https://twitter.com/(.*)/media/\?lang=en", item).group(1))
    return get_handle_with_most_followers(matched_handles, top=2)


def get_destination_json():
    parent_dir = pathlib.Path(__file__).parents[2]
    return pathlib.Path(parent_dir, "project_core", 'vigilant_crypto', "media", 'twitter_handle.json')


def load_coin_name():
    coin_dict = {}
    # https://github.com/crypti/cryptocurrencies
    with open(pathlib.Path(pathlib.Path(__file__).parent/ "coin_list"), "r") as fp:
        for item in fp.readlines():
            matched = re.match("\| `(.*?)` \| (.*?) \|\\n", item)
            coin_symbol = matched.group(1)
            coin_string = matched.group(2)
            coin_dict[coin_symbol] = coin_string
    return coin_dict


if __name__ == "__main__":
    final_json = {}
    all_coin_dict = load_coin_name()

    for asset in get_all_base_assets():
        search_string = f"{asset} {all_coin_dict.get(asset, '')} coin twitter"
        print(f"Searching for {search_string}")
        a = search(search_string, num_results=15)
        handle = get_handle_from_search_lists(a)
        print(f"Handle for {asset} is {handle}")
        if len(handle) > 0:
            final_json[asset] = handle

    with open(get_destination_json(), "w") as json_dest:
        json.dump(final_json, json_dest, indent=2)
    a = 1



