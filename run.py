from media.utils.general import MediaEnum
from media.image_ops import PyplotGraph
from media.blog_writer import WebPageFactory
from media.tweet_ops import build_tweet_text_image_and_post


def lambda_handler(event: dict,
                   context: dict):
    """
    AWS Lambda handler entry
    Args:
        event: Dictionary with keys: lower, upper, reference
        context:

    Returns:
        Dictionary of coins in between the limits
    """
    event_type = event["type"]
    assert event_type in MediaEnum.__members__, f"Event was {event}"
    if MediaEnum.plotly_image_update == MediaEnum(event_type):
        PyplotGraph.publish_image_overall(event["all_coin_history"],
                                          event["eth_full_history"])
    elif MediaEnum.blog_main_page == MediaEnum(event_type):
        webpage_factory_instance = WebPageFactory()
        crypto_update_page = webpage_factory_instance.get_webpage_concrete("crypto_update_main")
        crypto_update_page.publish_online(event["eth_full_history"])
    elif MediaEnum.blog_ind_page == MediaEnum(event_type):
        webpage_factory_instance = WebPageFactory()
        crypto_update_page = webpage_factory_instance.get_webpage_concrete("crypto_update_blog")
        return crypto_update_page.publish_online(event["last_dict_of_coins"],
                                                 event["replaced_rows"],
                                                 event["eth_full_history"],
                                                 event['new_rows']
                                                 )
    elif MediaEnum.tweet == MediaEnum(event_type):
        return build_tweet_text_image_and_post(event["replaced_rows"],
                                               event["new_rows"],
                                               event["eth_full_history"]
                                               )
    else:
        raise ValueError(f"Received {event_type} as the event type")

    return 0


if __name__ == "__main__":
    lambda_handler(event={}, context={})
