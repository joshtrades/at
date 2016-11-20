import datetime

from abc import abstractmethod, ABCMeta
from bson import ObjectId

from trading.account.portfolio import Portfolio
from trading.broker import MarketOrder
from trading.constants.order import SIDE_BUY, ORDER_MARKET
from trading.constants.granularity import GRANULARITY_HOUR
from trading.constants.interval import INTERVAL_FORTY_CANDLES
from trading.db import get_database
from trading.util.log import Logger


class Strategy(object):
    __metaclass__ = ABCMeta

    name = 'Base_Strategy'

    _db = None
    _logger = None

    interval = 600
    strategy_data = {}
    data_window = INTERVAL_FORTY_CANDLES
    granularity = GRANULARITY_HOUR

    def __init__(self, strategy_id, instrument, base_pair, quote_pair, classifier_id=None):
        self.classifier_id = classifier_id
        self.instrument = instrument
        self.strategy_id = strategy_id
        self.portfolio = Portfolio(instrument, base_pair, quote_pair)

        self.logger.info('Starting Portfolio', data=self.portfolio)

    @abstractmethod
    def analyze_data(self, market_data):
        raise NotImplementedError

    @abstractmethod
    def make_decision(self):
        raise NotImplementedError

    @abstractmethod
    def calc_units_to_buy(self, current_price):
        raise NotImplementedError

    @abstractmethod
    def calc_units_to_sell(self, current_price):
        raise NotImplementedError

    @abstractmethod
    def allocate_tradeable_amount(self):
        raise NotImplementedError

    def load_strategy(self, strategy_id):
        query = {'_id': ObjectId(strategy_id)}

        strategy = self.db.strategies.find_one(query)

        try:
            strategy_data = strategy['strategy_data']
            instrument = strategy_data['instrument']
            base_pair = strategy_data['base_pair']
            quote_pair = strategy_data['quote_pair']
        except KeyError:
            raise ValueError  # Todo make strategy specific exceptions

        return instrument, base_pair, quote_pair

    def update_portfolio(self, order_responses):
        self.portfolio.update(order_responses)

    def log_strategy_data(self):
        self.logger.debug('Strategy Indicator Data:')
        for indicator in self.strategy_data:
            self.logger.debug('Indicator {indicator} with value {value}'
                              .format(indicator=indicator, value=self.strategy_data[indicator]))

    def make_order(self, asking_price, order_side=SIDE_BUY):
        trade_expire = datetime.datetime.utcnow() + datetime.timedelta(days=1)
        trade_expire = trade_expire.isoformat("T") + "Z"

        if order_side == SIDE_BUY:
            units = self.calc_units_to_buy(asking_price)
        else:
            units = self.calc_units_to_sell(asking_price)

        self.logger.info('Calculated units {units} and side {side}'.format(units=units, side=order_side))

        instrument = self.portfolio.instrument
        side = order_side
        order_type = ORDER_MARKET
        price = asking_price

        return MarketOrder(instrument, units, side, order_type, price, trade_expire)

    def serialize(self):

        base_pair = self.portfolio.base_pair
        quote_pair = self.portfolio.quote_pair

        config = {
            'instrument': self.portfolio.instrument,
            'base_pair': {'currency': base_pair.currency, 'starting_units': base_pair.starting_units,
                          'tradeable_units': base_pair.tradeable_units},
            'quote_pair': {'currency': quote_pair.currency, 'starting_units': quote_pair.starting_units,
                           'tradeable_units': quote_pair.tradeable_units}
        }

        strategy = {
            'name': self.name,
            'config': config,
            'profit': self.portfolio.profit,
            'data_window': self.data_window,
            'interval': self.interval,
            'indicators': self.strategy_data.keys(),
            'instrument': self.instrument,
        }

        return strategy

    @property
    def logger(self):
        if self._logger is None:
            self._logger = Logger()
        return self._logger

    @property
    def db(self):
        if self._db is None:
            self._db = get_database()
        return self._db
