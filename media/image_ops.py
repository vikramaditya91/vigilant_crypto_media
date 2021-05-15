import datetime
import functools
import logging
import operator
import pathlib
from typing import List, Dict, Tuple

import chart_studio
import numpy as np
import plotly.graph_objects as go
from matplotlib import dates as mdates
from matplotlib import pyplot as plt
from matplotlib.offsetbox import OffsetImage, AnnotationBbox

from media.utils.postpro import PredictionOperations
from media.utils.general import get_parameter_from_ssm, alternate_sort_by_key

logger = logging.getLogger(__name__)


class GeneralGraph:
    @staticmethod
    def sanitize_data_for_plotting(data_from_db):
        """
        Converts the data obtained from the DB into printable format
        :param data_from_db: list of 2-item tuples which are to be plotted
        :return: Separated lists which should be plotted
        """
        epoch_time_milliseconds, values = zip(*data_from_db)
        epoch_time_seconds = tuple(epoch_time / 1000 for epoch_time in epoch_time_milliseconds)
        x_axis_date = mdates.epoch2num(epoch_time_seconds)
        return x_axis_date, values

    @staticmethod
    def flatten_all_history_to_coin_name_quantity(raw_dict_all_coin_history):
        """
        From the dict of list of raw-dicts provided, it generates the dict suitable for printing
        :param raw_dict_all_coin_history: dict of list of dicts of coins
        :return: dict of ts (key): string for graph(value)
        """
        required_info_table = {}
        for timestamp, raw_coin_history in raw_dict_all_coin_history.items():
            coin_content_string = "Coin       quantity    ETH-value<br>"
            for coin_dict in raw_coin_history:
                coin_content_string += f"{coin_dict['COIN']:5}{coin_dict['QUANTITY']:12.2f}" \
                                       f"{coin_dict['TOTAL_ETH_EQUIVALENT']:8.2f}<br>"
            required_info_table[timestamp] = coin_content_string
        return required_info_table


class CryptoCoinImage:
    """The images from the cryptocurrency sub-module are available here"""
    def __init__(self):
        self.image_root = pathlib.Path(
            pathlib.Path(__file__).parents[2],
            "submodules",
            "cryptocurrency-icons"
        )

    def get_icon_image_of(self,
                          coin: str,
                          directory: str = "128") -> pathlib.Path:
        """Obtains the icon of the coin"""
        return pathlib.Path(self.image_root / directory / "color" / f"{coin.lower()}.png")


class MatplotlibGraph(GeneralGraph):
    """
    Involved in generating the graphs and the twitter pictures
    """

    def __init__(self):
        self.ratio_multiplier = 5
        self.fig, self.main_axis = plt.subplots(1, 1)
        self.pie_axis = self.main_axis.inset_axes((-0.25, 0.19,
                                                   1, 1))
        self.font_size = 24 * self.ratio_multiplier
        self.table_font_size = 3 * self.ratio_multiplier
        self.width_of_donut = 0.4
        self.table_border_color = "k"
        self.table_header_color = '#40466e'
        self.row_colors = ['#f1f1f2', 'w']

    def format_the_graph(self):
        """
        Sets the format for the graph ticks and what not
        :return:Nothing
        """
        date_fmt = '%d-%b-%y'
        date_formatter = mdates.DateFormatter(date_fmt)
        self.main_axis.xaxis.set_major_formatter(date_formatter)
        self.main_axis.tick_params(axis='both', which='major', pad=10 * self.ratio_multiplier)
        self.main_axis.set_xlabel('Time', fontsize=self.font_size, labelpad=10*self.ratio_multiplier)
        self.main_axis.set_ylabel('Total value [in ETH/Ξ]', fontsize=self.font_size, labelpad=10*self.ratio_multiplier)
        self.main_axis.set_ylim(bottom=10)
        self.main_axis.grid(True)
        self.main_axis.grid(linewidth=2, linestyle="--")
        locator = mdates.AutoDateLocator(minticks=3, maxticks=7)
        self.main_axis.xaxis.set_major_locator(locator)
        plt.setp(self.main_axis.get_xticklabels(), fontsize=self.font_size)
        plt.setp(self.main_axis.get_yticklabels(), fontsize=self.font_size)

    def generate_history_graph(self,
                               eth_vs_ts_history_full: List[Dict]):
        """
        Generates the graph and formats it accordingly
        :param eth_vs_ts_history_full: data from the DB rows
        :return: Nothing
        """
        x_axis_data, y_axis_data = self.sanitize_data_for_plotting(eth_vs_ts_history_full)
        self.main_axis.fill_between(x_axis_data, y_axis_data, y2=10, alpha=0.4)
        self.format_the_graph()

    def generate_donut_chart(self,
                             coin_rows: List[Dict]):
        """Generates the donut-chart from the rows of coins from the DB"""
        coin_rows = alternate_sort_by_key(coin_rows)
        coins = [item["COIN"] for item in coin_rows]
        eth_equivalent_list = [item["TOTAL_ETH_EQUIVALENT"] for item in coin_rows]

        wedges, text = self.pie_axis.pie(eth_equivalent_list,
                                         radius=0.5,
                                         wedgeprops=dict(width=self.width_of_donut/2,
                                                         edgecolor="None"),
                                         startangle=90,
                                         textprops={"fontsize": self.font_size/1.5}
                                         )
        self.annotate_text_and_icons_to_wedges(wedges, coins)

    def generate_inner_text(self,
                            coin_overall_rows: List[Dict]):
        """
        Generates the inner-text
        :param coin_overall_rows: Overall coin rows. List of dicts
        :return:
        """
        total_eth = functools.reduce(
            operator.add,
            map(lambda x: x["TOTAL_ETH_EQUIVALENT"], coin_overall_rows)
        )
        self.pie_axis.text(0, 0.09,
                           f"{total_eth:.2f} Ξ",
                           ha="center",
                           color="white",
                           fontsize=self.font_size)

    def generate_inner_circle(self,
                              coin_overall_rows: [Dict],
                              eth_vs_ts_history_full: List[Tuple]):
        """
        Generates the inner-circle with some text on the ETH and the percentage
        :param coin_overall_rows: All the coin rows in the form of a list of dicts
        :param eth_vs_ts_history_full: The history of the coin in list of tuple
        """
        self.generate_inner_text(coin_overall_rows)

        prediction = PredictionOperations()
        monthly_change = prediction.get_percentage_diff_for_history(
            datetime.timedelta(days=30),
            eth_vs_ts_history_full
        )
        weekly_change = prediction.get_percentage_diff_for_history(
            datetime.timedelta(days=7),
            eth_vs_ts_history_full
        )
        self.pie_axis.text(0, -0.05,
                           f"week: {weekly_change:.2f} %",
                           ha="center",
                           color="white",
                           fontsize=self.font_size/2)
        self.pie_axis.text(0, -0.15,
                           f"month: {monthly_change:.2f} %",
                           ha="center",
                           color="white",
                           fontsize=self.font_size/2)

        if (monthly_change > 0) or (weekly_change > 0):
            color = "green"
        else:
            color = "red"

        self.pie_axis.add_artist(plt.Circle((0, 0),
                                            (1-self.width_of_donut)/2,
                                            facecolor=color,
                                            alpha=0.5,
                                            edgecolor="None"))

    def annotate_text_and_icons_to_wedges(self,
                                          wedges: List,
                                          coins: List[str]):
        """
        Adds text and icons to the wedges
        :param wedges: wedges generated from the ax.pie
        :param coins: coins list
        """
        bbox_props = dict(facecolor="w", ec="None")
        kw = dict(arrowprops=dict(arrowstyle="-"),
                  bbox=bbox_props, zorder=0, va="center",
                  fontsize=20 * self.ratio_multiplier)

        for coin, wedge in zip(coins, wedges):
            ang = (wedge.theta2 - wedge.theta1) / 2. + wedge.theta1
            y = np.sin(np.deg2rad(ang))/2
            x = np.cos(np.deg2rad(ang))/2
            horizontalalignment = {-1: "right", 1: "left"}[int(np.sign(x))]
            connectionstyle = "angle,angleA=0,angleB={}".format(ang)
            kw["arrowprops"].update({"connectionstyle": connectionstyle})
            self.pie_axis.annotate(coin,
                                   xy=(x, y),
                                   xytext=(0.75 * np.sign(x), 1.4 * y),
                                   horizontalalignment=horizontalalignment,
                                   **kw)
            self.insert_symbol_into_annotation(coin, position=(x, y))

    def insert_symbol_into_annotation(self,
                                      coin: str,
                                      position: Tuple[float, float]):
        """
        Inserts the symbol into the annotation
        :param coin: coin whose symbol needs to be added
        :param position: Position of the edge-of-circle
        """
        image_location = CryptoCoinImage()
        if image_location.get_icon_image_of(coin).exists():
            im = plt.imread(image_location.get_icon_image_of(coin).__str__(), format='png')
            imagebox = OffsetImage(im, zoom=1)
            imagebox.image.axes = self.pie_axis
            ab = AnnotationBbox(imagebox,
                                (0.65 * np.sign(position[0]), 1.4 * position[1]),
                                bboxprops={"edgecolor": "None"})
            self.pie_axis.add_artist(ab)

    def save_image(self, image_path):
        """
        Saves the image into the path specified
        :param image_path: path of the image (str/pathlib.Path)
        :return: Nothing
        """
        if pathlib.Path(image_path).exists() is True:
            figure = plt.gcf()  # get current figure
            figure.set_size_inches(16 * self.ratio_multiplier,
                                   9 * self.ratio_multiplier)
            plt.savefig(image_path)
        else:
            raise IOError(f"Image path does not exist at {image_path}")


class PyplotGraph(GeneralGraph):
    """Pyplot graph for the blog"""
    def __init__(self):
        self.fig = go.Figure()
        username = get_parameter_from_ssm('PLOTLY_USERNAME')
        api_key = get_parameter_from_ssm('PLOTLY_API_KEY')
        chart_studio.tools.set_credentials_file(username=username,
                                                api_key=api_key)
        logger.info("Generated the plotly object and logged in with the credentials")

    def format_xlabel(self):
        self.fig.update_layout(xaxis={"type": "date"})
        self.fig.update_layout(
            xaxis_tickformatstops=[
                dict(dtickrange=[None, 1000], value="%H:%M:%S.%L ms"),
                dict(dtickrange=[1000, 60000], value="%H:%M:%S s"),
                dict(dtickrange=[60000, 3600000], value="%H:%M m"),
                dict(dtickrange=[3600000, 86400000], value="%H:%M h"),
                dict(dtickrange=[86400000, 604800000], value="%e. %b d"),
                dict(dtickrange=[604800000, "M1"], value="%e. %b"),
                dict(dtickrange=["M1", "M12"], value="%b '%y M"),
                dict(dtickrange=["M12", None], value="%Y Y")
            ]
        )
        logger.info("Modified the xlabels for better aesthetics")

    def format_graph(self):
        """Sets the formats for the plotly graph"""
        self.format_xlabel()
        self.fig.update_xaxes(showspikes=True, spikethickness=2)
        self.fig.update_yaxes(showspikes=True, spikethickness=2)
        self.fig.update_layout(
            title="10 ETH Challenge",
            xaxis_title="Date",
            yaxis_title="Equivalent ETH value",
            font=dict(
                family="Courier New, monospace",
                size=18,
                color="#7f7f7f"
            )
        )
        logger.info("Modified the general format of the plotly graph")

    def generate_graph(self, entire_history_dict, dict_each_coin_timestamped):
        # TODO Use datetime object. But plotly does not plot smooth graph
        date_plot_list = [datetime.datetime.fromtimestamp(x[0] / 1000) for x in dict_each_coin_timestamped]
        eth_value_list = [x[1] for x in dict_each_coin_timestamped]
        flattened_coin_history_dict = self.flatten_all_history_to_coin_name_quantity(entire_history_dict)
        coin_name_list = [flattened_coin_history_dict.get(ts[0], "") for ts in dict_each_coin_timestamped]
        self.fig.add_trace(go.Scatter(
            x=date_plot_list,
            y=eth_value_list,
            mode="lines",
            name="Lines",
            hovertext=coin_name_list,
            textposition="top right",
        ))
        self.format_graph()
        logger.info("Plotly graph has been plot and formatted")
        return self.fig

    @staticmethod
    def save_image_to_location(figure_handle, path_to_write):
        save_result = figure_handle.write_image(path_to_write)
        return save_result

    @staticmethod
    def upload_image_to_server(fig, filename):
        logger.info("Attempting to load the graph on the chart_studio")
        chart_studio.plotly.plot(fig, filename=filename, auto_open=False)

    @classmethod
    def publish_image_overall(cls,
                              entire_coin_history_vs_timestamp,
                              eth_vs_timestamp_history_full):
        plotly_graph_handle = PyplotGraph()
        figure = plotly_graph_handle.generate_graph(entire_coin_history_vs_timestamp,
                                                    eth_vs_timestamp_history_full)
        plotly_graph_handle.upload_image_to_server(figure, filename="blog_10eth_challenge_history")



