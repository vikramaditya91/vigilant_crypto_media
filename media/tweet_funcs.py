import logging
import twitter
import pathlib
import json
from media.utils.general import get_parameter_from_ssm

logger = logging.getLogger(__name__)


class Twitter(object):
    """Responsible for performing actions related to Twitter"""
    def __init__(self):
        self.api = twitter.Api(consumer_key=get_parameter_from_ssm('VC_TWEET_CONSUMER_KEY'),
                               consumer_secret=get_parameter_from_ssm('VC_TWEET_CONSUMER_SECRET'),
                               access_token_key=get_parameter_from_ssm('VC_TWEET_ACCESS_TOKEN_KEY'),
                               access_token_secret=get_parameter_from_ssm('VC_TWEET_ACCESS_TOKEN_SECRET'))
        logger.info("Created the Twitter init object")

    @staticmethod
    def map_coin_to_handle(coin):
        with open(pathlib.Path(__file__).parent / "resources" / "twitter_handle.json") as json_file:
            map_of_twitter_handle = json.load(json_file)
        return map_of_twitter_handle.get(coin, [])

    def tweet_status_eth_challenge(self, tweet_message, media):
        if media is not None:
            assert pathlib.Path(media).exists(), f"Media unavailable from {media}"
        # TODO Generate seperate tweets if this happens
        tweet_message = tweet_message[-279:]
        tweet_info = self.api.PostUpdate(tweet_message, media=media)
        return tweet_info


def generate_tweet_text_for_eth_challenge(replaced_rows, total_eth_holding):
    """
    Generates the tweet text for the ETH challenge
    :param replaced_rows: The rows which were replaced by this run of the bot
    :param total_eth_holding: Total ETH held by the ETH challenge now
    :return: str, twitter text
    """
    tweet_message = ""
    twitter_instance = Twitter()
    for replacement_instance in replaced_rows:
        original_dict, new_dict = replacement_instance
        price_of_sold_coin = new_dict['QUANTITY'] * new_dict['COIN_ETH_VALUE'] / original_dict['QUANTITY']
        tweet_message += f"#SELL ${original_dict['COIN']}, qty: {original_dict['QUANTITY']:.0f}, " \
                         f"at {price_of_sold_coin} ETH\n" \
                         f"#BUY ${new_dict['COIN']}, qty: {new_dict['QUANTITY']:.0f}, " \
                         f"at {new_dict['COIN_ETH_VALUE']} ETH\n"

        for item in twitter_instance.map_coin_to_handle(original_dict['COIN']):
            tweet_message += f"@{item} "

        for item in twitter_instance.map_coin_to_handle(new_dict['COIN']):
            tweet_message += f"@{item} "

        if (twitter_instance.map_coin_to_handle(original_dict['COIN']) == "") and \
            (twitter_instance.map_coin_to_handle(new_dict['COIN']) != ""):
            tweet_message += f"#Crypto #10ETHChallenge $ETH #cryptotrade #bitcoin"

    tweet_message += f"\n10 $ETH on 10-Feb-2020 is now {total_eth_holding:.2f}\n $ETH $BTC " \
                     f"#cryptotrade #cryptobot"
    return tweet_message
