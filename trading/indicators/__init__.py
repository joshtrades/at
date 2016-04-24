import scipy

from trading.indicators.volatility_indicators import calc_average_true_range

TRADING_PERIOD_MONTH = 22

INTERVAL_NINETY_DAYS = 90 # Long Interval
INTERVAL_FORTY_DAYS = 40 # Medium Interval
INTERVAL_TEN_DAYS = 10 # Short Interval


def get_period_high(daily_highs, days=1):
    """
    Gets high price of primary pair for target num days
    :param num_days: target num of days
    :returns: high price (float) over specified period
    """
    target_range = daily_highs[: days]
    return max(target_range)


def get_period_low(daily_lows, days=1):
    """
    Gets low price of primary pair for target num days
    :param num_days: target num of days
    :returns: low price (float) over specified period
    """
    target_range = daily_lows[: days]
    return min(target_range)


def calc_chandalier_exits(closing_data, high_data, low_data, volatility_threshold=3,
                          trading_period=TRADING_PERIOD_MONTH):
    """
    Volatility-based system that identifies outsized price movements
    Indicator provides a buffer that is three times the volatility
    A decline strong enough to break this level warrants a reevaluation of long positions
    """
    month_high = get_period_high(closing_data, trading_period)
    month_low = get_period_low(closing_data, trading_period)
    atr = calc_average_true_range(closing_data, high_data, low_data, trading_period)
    long_exit = month_high - (atr * volatility_threshold)
    short_exit = month_low + (atr * volatility_threshold)

    return long_exit, short_exit


def moving_average(data, period):
    target_range = data[period:]
    return scipy.mean(target_range)