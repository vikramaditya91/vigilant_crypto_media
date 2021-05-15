import datetime


class PredictionOperations:
    @staticmethod
    def _calculate_percentage_diff_raw(new_value, original_value):
        """Converts raw values to HTML text with percentage diff for printing"""
        return (float(new_value) - original_value) * 100 / original_value

    def get_percentage_diff_for_history(self, time_delta, eth_vs_ts_history_full):
        """Returns the percentage difference from the eth history vs time_delta"""
        current_eth_holding = eth_vs_ts_history_full[-1][1]
        x_time_ago_epoch = datetime.datetime.now().timestamp() - time_delta.total_seconds()
        available_closest_tuple = min(eth_vs_ts_history_full, key=lambda x: abs(x[0] / 1000 - x_time_ago_epoch))
        percent_diff = self._calculate_percentage_diff_raw(new_value=current_eth_holding,
                                                           original_value=available_closest_tuple[1])
        return percent_diff

    @staticmethod
    def predict_end_of_year_value(current_value, start_date, starting_value):
        """
        Predicts the value of a quantity if this trend continues
        :param current_value: value of currently held item
        :param start_date: when was the reference start date
        :param starting_value: how many items did you have at the start
        :return:
        """
        current_date = datetime.datetime.now()
        end_of_year_date = datetime.datetime(current_date.year, 12, 31)
        time_left_in_year = end_of_year_date - current_date
        time_since_simulation_began = current_date - start_date
        change_in_value = current_value - starting_value
        expected_change = starting_value + change_in_value * \
                          time_left_in_year.total_seconds() / time_since_simulation_began.total_seconds()
        return expected_change
