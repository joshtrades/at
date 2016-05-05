import sys
import traceback

from bson import ObjectId
from flask import request
from flask_restful import Resource

from trading.api import ok
from trading.db import get_database, transform_son


def _find_target_candle(target_candle, date_id_map):
    target_date = target_candle['date']
    matching_candle = date_id_map[target_date]
    return matching_candle


def make_date_id_map(candles):
    date_id_map = {}

    for candle in candles:
        date = candle['date']
        formatted_date = str(date['year']) + '-' + str(date['month']) + '-' + str(date['day']) + '-' + str(date['hour'])
        date_id_map[formatted_date] = candle
    return date_id_map


class Candle(Resource):
    def get(self):
        print('At Candle GET Endpoint')

        db = get_database()
        chart_data = transform_son(db.candle_data.find_one())
        title = chart_data['title']
        y_params = chart_data['y_params']
        x_params = chart_data['x_params']
        candles = chart_data['candles']

        return {'candles': candles, 'chart_id': chart_data['id'], 'title': title, 'y_params': y_params, 'x_params': x_params}


    def post(self):
        print('At Candle POST Endpoint')
        request_data = request.get_json()
        start_date = request_data.get('start_date')
        end_date = request_data.get('end_date')
        granularity = request_data.get('granularity')
        candle = request_data.get('candle')
        pattern = request_data.get('pattern')
        chart_id = request_data.get('chart_id')

        db = get_database()

        try:
            chart_id = ObjectId(chart_id)
            chart_data = transform_son(db.candle_data.find_one({'_id': chart_id}))
            date_id_map = make_date_id_map(chart_data['candles'])
            target_candle = _find_target_candle(candle, date_id_map)
            target_candle_id = target_candle['id']

            target_candle['pattern'] = pattern
            query = {'_id': chart_id, 'candles.id': target_candle_id}
            update = {'$set': {'candles.$': target_candle}}

            print(query, update)
            db.candle_data.update(query, update)

        except Exception as e:
            print('E', e)
            traceback.print_exc(file=sys.stdout)
        return ok(202)


def find_marked_candles(charts):
    chart_id_candle_map = {}

    for chart in charts:
        chart_id = chart['id']
        candles = chart['candles']
        patterned_candles = [candle for candle in candles if candle.get('pattern')]
        chart_id_candle_map[chart_id] = patterned_candles

    return chart_id_candle_map


class CandleCharts(Resource):
    def get(self):
        db = get_database()
        charts = db.candle_data.find()
        charts = map(transform_son, charts)

        chart_data = {}

        for chart in charts:
            chart_id = chart['id']
            granularity = chart['granularity']
            candles = chart['candles']
            num_candles = len(candles)
            start_date = chart['start_date']
            end_date = chart['end_date']
            chart_data[chart_id] = {
                'granularity': granularity,
                'num_candles': num_candles,
                'start_date': start_date,
                'end_date': end_date
            }


        return chart_data


class CandlePattern(Resource):
    def get(self):
        db = get_database()
        charts = db.candle_data.find()
        charts = map(transform_son, charts)

        marked_candles = find_marked_candles(charts)

        return {'candles': marked_candles}
