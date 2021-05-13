import tempfile
from project_core.vigilant_crypto.media import image_ops, twitter_funcs


def generate_the_image_for_twitter(time_stamp_eth_holding_rows, overall_rows):
    """Generates the image that will be posted on twitter"""
    twitter_image_generator = image_ops.MatplotlibGraph()
    twitter_image_generator.generate_history_graph(time_stamp_eth_holding_rows)
    twitter_image_generator.generate_donut_chart(overall_rows)
    twitter_image_generator.generate_inner_circle(overall_rows, time_stamp_eth_holding_rows)
    return twitter_image_generator


def post_the_eth_challenge_tweet(twitter_image_handle, tweet_message):
    """
    Posts the tweet for the ETH challenge
    :param twitter_image_handle: handle to the image that was generated (but not saved yet)
    :param tweet_message: str, text to tweet
    :return: information of the tweet
    """
    twitter_instance = twitter_funcs.Twitter()
    with tempfile.NamedTemporaryFile(suffix=".png") as tmp_file:
        twitter_image_handle.save_image(tmp_file.name)
        tweet_info = twitter_instance.tweet_status_eth_challenge(tweet_message, media=tmp_file.name)
    return tweet_info


def build_tweet_text_image_and_post(substituted_rows, all_new_rows, binance_object,
                                    total_eth_holding, time_stamp_eth_holding_rows):
    """

    :param substituted_rows: List of rows that were substituted. Used for twitter text
    :param all_new_rows: All new rows for the image which has the table
    :param binance_object: Binance object to know reference coin
    :param total_eth_holding: Total ETH held by the all_new_rows
    :param time_stamp_eth_holding_rows: Full history of the timestamp vs eth-holding
    :return: tweet_info
    """
    tweet_message = twitter_funcs.generate_tweet_text_for_eth_challenge(substituted_rows,
                                                                        binance_object,
                                                                        total_eth_holding)
    twitter_image_handle = generate_the_image_for_twitter(time_stamp_eth_holding_rows, all_new_rows)
    tweet_info = post_the_eth_challenge_tweet(twitter_image_handle, tweet_message)
    return tweet_info
