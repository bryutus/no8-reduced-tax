# -*- coding: utf-8 -*-

import csv
import re

import pandas as pd

from . import products


def main():
    filepath = 'resources/r_by_customer.csv'
    handle(filepath)


def handle(filepath):
    df = pd.read_csv(filepath,
                     header=None,
                     usecols=[0, 6],
                     names=['name', 'retail_amount'],
                     skipinitialspace=True)

    is_counting = False
    bc_name = ''
    cosmetics_amount = 0
    supplement_amount = 0
    promotion_amount = 0

    summarized = list()

    df.dropna(how='all')
    for index, row in df.iterrows():
        if is_ignore_row(row['name']) is not None:
            continue

        if is_counting is False:
            bc_name = row['name']
            is_counting = True
            continue

        if row['name'] == '【  得意先計  】':
            calculated_total_retail_amount = cosmetics_amount + \
                supplement_amount + promotion_amount
            row_total_retail_price = number_unformat(row['retail_amount'])
            if calculated_total_retail_amount != row_total_retail_price:
                raise Exception('合計金額が一致しません BC: {name}, 上代金額（計算）: {calculated_total_retail_amount}, 上代金額（ファイル）: {row_total_retail_price}'
                                .format(name=bc_name,
                                        calculated_total_retail_amount=calculated_total_retail_amount,
                                        row_total_retail_price=row_total_retail_price))

            bc = parse_bc(bc_name)
            summarized.append([bc.group(1),
                               bc.group(2),
                               cosmetics_amount,
                               supplement_amount,
                               promotion_amount])

            is_counting = False
            bc_name = ''
            cosmetics_amount = 0
            supplement_amount = 0
            promotion_amount = 0
            continue

        product_code = extract_product_code(row['name'])
        if product_code not in products.SCHEME:
            raise Exception(
                '商品マスタに存在しない商品の売上が計上されています 商品コード: {product_code}'.format(
                    product_code=product_code))

        product = products.SCHEME[product_code]

        row['subed_retail_amount'] = number_unformat(row['retail_amount'])

        if product['type'] == 'cosmetics':
            cosmetics_amount += row['subed_retail_amount']
        elif product['type'] == 'supplement':
            supplement_amount += row['subed_retail_amount']
        elif product['type'] == 'promotion':
            promotion_amount += row['subed_retail_amount']
        else:
            raise Exception(
                '定義されていない種別が存在しています 商品コード: {product_code}, 種別: {type}'.format(
                    product_code=product_code, type=product['type']))

    write_csv(summarized)


def is_ignore_row(name):
    return re.match('^[期間\\s.+|得意先コード 得意先名|商品コード 商品名]|【  合  計  】',
                    name)


def parse_bc(bc):
    matched = re.match('^([0-9]+)\\s(.+)', bc)
    if matched is None:
        return ''
    return matched


def extract_product_code(name):
    matched = re.match('^([0-9]+)\\s.+', name)
    if matched is None:
        return 'none'
    return matched.group(1)


def number_unformat(price):
    return int(re.sub('[^0-9\\-]', '', price))


def write_csv(body):
    with open('resources/summarized_r_by_customer.csv', 'w') as f:
        header = ['得意先コード', '得意先名', '化粧品', '健食', '販促']
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(body)
