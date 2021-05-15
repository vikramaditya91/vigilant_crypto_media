import datetime
import logging
from jinja2 import Template
from abc import ABC, abstractmethod
from media.s3_file_access import S3FileAccessAbstract
from media.utils.postpro import PredictionOperations
logger = logging.getLogger(__name__)


class WebPageFactory:
    _creators = {}

    def register_format(self, identifier, concrete_class_name):
        self._creators[identifier] = concrete_class_name

    def get_webpage_concrete(self, identifier):
        creator = self._creators.get(identifier)
        if not creator:
            raise ValueError(identifier)
        return creator()


def add_to_factory(identifier):
    """Responsible for adding classes to the dictionary whenever decorated"""
    def middle_decorator(class_name):
        class NewCls(object):
            pass
        WebPageFactory().register_format(identifier=identifier, concrete_class_name=class_name)
        return NewCls

    return middle_decorator


class WebPage(ABC):
    def __init__(self):
        self.simulation_start_date = datetime.datetime(2020, 2, 2)
        self.relative_template = ""
        self.file_exists = None

    @abstractmethod
    def get_destination_relative_path(self):
        pass

    @abstractmethod
    def get_posted_url(self, destination_path):
        pass

    @abstractmethod
    def prepare_dict(self, *args, **kwargs):
        raise NotImplementedError

    def publish_online(self,
                       *args,
                       **kwargs):
        dict_to_replace_crypto_update = self.prepare_dict(*args, **kwargs)
        page_path = self.publish_file(
            dict_to_replace_crypto_update)
        return page_path

    @staticmethod
    def get_template_file_content(relative_template):
        """Returns the content of the template file"""
        with S3FileAccessAbstract(file_name=relative_template) as main_template_file:
            with open(main_template_file, 'r') as fp:
                template_handle = Template(fp.read())
        logger.info(f"Obtained the template from {relative_template}")
        return template_handle

    def publish_file(self, dict_to_replace):
        """Update the markdown file the template by replacing the contents in {{ }}"""
        template = self.get_template_file_content(self.relative_template)
        rendered_file_content = template.render(dict_to_replace)
        destination_file = self.get_destination_relative_path()
        logger.info(f"rendered file content is available by replacing the dict {dict_to_replace}\n"
                    f"on the file: {destination_file}")
        with S3FileAccessAbstract(file_name=destination_file,
                                  push_back=True,
                                  file_exists=self.file_exists) as templated:
            with open(templated, "w") as fp:
                fp.write(rendered_file_content)
        return destination_file

    @staticmethod
    def get_percentage_diff_html_format(time_delta, eth_vs_ts_history_full):
        percent_diff = PredictionOperations().get_percentage_diff_for_history(time_delta, eth_vs_ts_history_full)
        percentage_representation = f"{percent_diff:>3.2f}%"
        logger.info(f"Calculated the percentage difference for {time_delta}")
        if percent_diff >= 0:
            return f'<font color="green">+{percentage_representation}</font>'
        else:
            return f'<font color="red">{percentage_representation}</font>'

    def prepare_general_dict(self, eth_vs_ts_history_full):
        """Prepare the list of strings to replace the markdowned template"""
        current_eth_holding = eth_vs_ts_history_full[-1][1]
        logger.info("Preparing the general dictionary for the web-pages")
        # TODO This can be speeded up https://stackoverflow.com/a/12141511/2542835
        return {"last_updated_on": datetime.datetime.now().astimezone().strftime("%m/%d/%Y, %H:%M:%S %Z"),
                "current_eth_holding": f"{current_eth_holding:>10.2f} ETH",
                "overall_eth_percent": self.get_percentage_diff_html_format(datetime.timedelta(weeks=99999),
                                                                            eth_vs_ts_history_full),
                "change_last_week": self.get_percentage_diff_html_format(datetime.timedelta(days=7),
                                                                         eth_vs_ts_history_full),
                "change_last_month": self.get_percentage_diff_html_format(datetime.timedelta(days=30),
                                                                          eth_vs_ts_history_full)
                }


@add_to_factory("crypto_update_main")
class MainWebPage(WebPage):
    """Responsible for updating the crypto_update.md"""
    def __init__(self):
        super().__init__()
        self.relative_template = "_layouts/template-eth-challenge-main.md"
        self.file_exists = True

    def get_posted_url(self, destination_path):
        """Get the final url where it is going to be posted"""
        return self.general_url + "crypto_update"

    def get_destination_relative_path(self):
        """Gets the destination path of the file after processing"""
        return "crypto_update.md"

    def prepare_dict(self, eth_vs_ts_history_full):
        """Prepare the dict specific to the crypto_update.md template"""
        parent_dict = self.prepare_general_dict(eth_vs_ts_history_full)
        current_eth_holding = eth_vs_ts_history_full[-1][1]
        parent_dict.update({"predicted_value_end_of_year": self.predict_end_of_year_value(current_eth_holding)})
        return parent_dict

    def predict_end_of_year_value(self, current_holding):
        """Predicts the end of year value of ETH holding based on the past record.
        # TODO Make a compound prediction. Not a linear prediction"""
        expected_change = PredictionOperations.predict_end_of_year_value(current_holding,
                                                                         start_date=self.simulation_start_date,
                                                                         starting_value=10)
        return f"{expected_change:>10.2f} ETH"


@add_to_factory("crypto_update_blog")
class BlogWebPage(WebPage):
    def __init__(self):
        super().__init__()
        self.base_name_for_blog = "10-eth-challenge"
        self.relative_template = "_layouts/template-eth-challenge-blog.md"
        self.file_exists = False

    def get_destination_relative_path(self):
        """Produces the destination of the renderer taking into account account if a
        blog already was written that date
        :return pathlib.Path object to the destination file
        """
        now = datetime.datetime.now()
        date_string = f"{now.year}-{now.month}-{now.day}"
        blog_post_dir = "_posts/crypto"
        files_in_dir = S3FileAccessAbstract(file_name=blog_post_dir).list_files(
            prefix_add=f"/{now.year}-{now.month}-{now.day}"
        )
        file_names_in_dir = [f['Key'] for f in files_in_dir]
        same_date_file_list = [item for item in file_names_in_dir if date_string in item]
        suffix = "" if len(same_date_file_list) == 0 else len(same_date_file_list)
        return f"{blog_post_dir}/{date_string}-{self.base_name_for_blog}{suffix}.md"

    def get_posted_url(self, destination_path):
        """Get the final url where it is going to be posted"""
        filename_slices = destination_path.name.split("-")
        year, month, day = filename_slices[0:3]

        # Cutting out the .md from the filename and reconstructing the filename
        filename_slices[-1] = filename_slices[-1][:-3]
        return f"{self.general_url}/{year}/{month}/{day}/{'-'.join(filename_slices[3:])}"

    @staticmethod
    def get_replaced_coins_string(replaced_rows):
        """Produces the string which does the replacing. Returns empty string if nothing to replace"""
        replaced_string = ""
        for orig_dict, new_dict in replaced_rows:
            price_of_sold_coin = new_dict['QUANTITY'] * new_dict['COIN_ETH_VALUE'] / orig_dict['QUANTITY']

            replaced_string += f"Sold: {orig_dict['COIN']}, quantity: {orig_dict['QUANTITY']:12.2f}, " \
                             f"price: {price_of_sold_coin:12.8f}<br>" \
                             f"Bought: {new_dict['COIN']}, quantity: {new_dict['QUANTITY']:12.2f}, " \
                             f"price: {new_dict['COIN_ETH_VALUE']:12.8f}<br>"
        return replaced_string

    def prepare_dict(self, list_of_coin_dicts, replaced_rows, eth_vs_time_history_full, new_rows):
        """
        Creates the dict used by the jinja2 renderer to replace text
        :param list_of_coin_dicts: list of coin dicts which contain information to be printed
        :param replaced_rows: list of tuples of replaced coins and new coins
        :param eth_vs_time_history_full: Full history of what has happened with the ETH vs time
        :return: a dict which is going to be used to replace in the renderer
        """
        dict_to_return = self.prepare_general_dict(eth_vs_time_history_full)
        dict_to_return.update(
            {"table_content": self.table_format_vertical_current_holding(list_of_coin_dicts, new_rows),
             "title_date": datetime.datetime.now().strftime('%d %b %Y'),
             "detailed_date_time": datetime.datetime.now().astimezone().strftime("%m/%d/%Y, %H:%M:%S %Z"),
             "changes_in_coins_held": self.get_replaced_coins_string(replaced_rows),
             "date_time_format_yaml": datetime.datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %z")},)
        return dict_to_return

    @staticmethod
    def table_format_horizontal_current_holding(list_of_coin_dicts):
        """Formats the table horizontally as
        | Coin ticker    | ETH | ETH | ETH | ETH | ETH | ETH | ETH | ETH | ETH | ETH |
        |----------------|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|
        | Predicted on   | 1    |  1   |1     |  1   |1     |   1  | 1    |   1  | 1    |    1 |
        | Sell target    |  1   | 1    | 1    | 1    | 1    |  1   |  1   |  1   |   1  |     1|
        | Sell latest by |   1  |1     |  1   |1     |  1   | 1    |   1  | 1    |  1   |     1|
        This does not fit very well if there are more than 5 coins
        """
        list_of_coins = [item["COIN"] for item in list_of_coin_dicts]
        joined_string = f"|Coin ticker|{'|'.join(list_of_coins)}|\n"
        joined_string += "---".join(["|"] * (len(list_of_coin_dicts) + 1)) + "\n"
        list_of_qty = [item["QUANTITY"] for item in list_of_coin_dicts]
        joined_string += f"|Quantity|{'|'.join(format(x, '10.3f') for x in list_of_qty)}|\n"
        list_of_sell_targets = [item["SELL_TARGET"] for item in list_of_coin_dicts]
        joined_string += f"|Sell target|{'|'.join(format(x, '10.3f') for x in list_of_sell_targets)}|\n"
        list_of_sell_by = [item["SELL_BY"] for item in list_of_coin_dicts]
        joined_string += f"|Sell by|{'|'.join(datetime.datetime.fromtimestamp(x / 1000).strftime('%d %b %Y') for x in list_of_sell_by)}|\n"
        return joined_string

    @staticmethod
    def table_format_vertical_current_holding(list_of_coin_dicts, new_rows):
        """Formats the table vertically as
        Current holdings from the ETH Challenge
        Coin ticker 	Quantity 	Sell target
        coin/ETH 	Sell latest by
        GVT 	163.26 	0.00551250 	25 Apr 2020
        KEY 	198803.21 	0.00000434 	01 May 2020
        PPT 	902.07 	0.00160125 	16 Apr 2020
        MFT 	784907.45 	0.00000352 	02 May 2020
        IOTX 	54540.77 	0.00001699 	16 Apr 2020
        EDO 	2181.2 	0.00096180 	15 Apr 2020
        HOT 	481984.36 	0.00000222 	02 May 2020
        TNB 	191782.49 	0.00000807 	22 Apr 2020
        AE 	824.96 	0.00066780 	30 Apr 2020
        MTH 	23240.5 	0.00004304 	16 Apr 2020
        """
        joined_string = "|Coin ticker|Quantity|Sell target<br>coin/ETH|Eqv ETH<br>value|Sell latest by|\n" \
                        "|-----------|--------|-----------|-----------|--------------|\n"
        for coin_dict, new_row in zip(list_of_coin_dicts, new_rows):
            joined_string += f"{coin_dict['COIN']}|{coin_dict['QUANTITY']}|" \
                f"{coin_dict['SELL_TARGET']:12.8f}|" \
                f"{float(coin_dict['QUANTITY']) * new_row['COIN_ETH_VALUE']:.2f}|" \
                f"{datetime.datetime.fromtimestamp(coin_dict['SELL_BY']/1000).strftime('%d %b %Y')}|\n"
        logger.info("Generated the table for printing")
        return joined_string





