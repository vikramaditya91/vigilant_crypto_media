from enum import Enum
from typing import List, Dict

import boto3


class MediaEnum(Enum):
    tweet = "tweet"
    blog_main_page = "blog_main_page"
    blog_ind_page = "blog_ind_page"
    plotly_image_update = "plotly_image_update"


def get_total_holding_from_rows(rows: List[Dict]):
    return sum([row['COIN_ETH_VALUE'] for row in rows])


def get_parameter_from_ssm(key):
    client = boto3.client("ssm")
    return client.get_parameter(Name=key)['Parameter']['Value']

def alternate_sort_by_key(list_of_dicts,
                          key="TOTAL_ETH_EQUIVALENT"):
    sorted_items = sorted(list_of_dicts, key=lambda x: x[key])
    alternating_rows = []
    while len(sorted_items) > 0:
        alternating_rows.append(sorted_items.pop())

        if len(sorted_items)>0:
            alternating_rows.append(sorted_items.pop(0))
    return alternating_rows
