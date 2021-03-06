from trading.constants.order import SIDE_SELL, SIDE_BUY

MAP_ORDER_TYPES = {
    SIDE_SELL: False,
    SIDE_BUY: True
}


def normalize_portfolio_update(portfolio_update):
    opened = portfolio_update['opened']
    closed = portfolio_update['closed']
    price = portfolio_update['price']

    if isinstance(opened, dict):
        opened = [opened]

    if isinstance(closed, dict):
        closed = [closed]

    opened = [order for order in opened if order.get('id')]
    closed = [order for order in closed if order.get('id')]

    return {
        'closed': closed,
        'opened': opened,
        'price': price
    }
