import os
from enum import Enum
from typing import List, Dict

import boto3


class MediaEnum(Enum):
    tweet = "tweet"
    blog_main_page = "blog_main_page"
    blog_ind_page = "blog_ind_page"
    plot_image_update = "plot_image_update"


def get_total_holding_from_rows(rows: List[Dict]):
    return sum([row['COIN_ETH_VALUE'] for row in rows])


def get_parameter_from_ssm(key):
    client = boto3.client("ssm")
    return client.get_parameter(Name=key)['Parameter']['Value']

