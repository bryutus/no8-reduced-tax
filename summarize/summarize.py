# -*- coding: utf-8 -*-

import csv
import re

import pandas as pd

from . import products

SUMMARIZED_SOURCE_FILE = 'resources/r_by_customer.csv'
SUMMARIZED_FILE = 'resources/summarized_r_by_customer.csv'


def main():
    handle(SUMMARIZED_SOURCE_FILE)


def handle(filepath):
    df = pd.read_csv(filepath,
                     header=None,
                     usecols=[0, 4, 6],
                     names=['name', 'quantity', 'retail_amount'],
                     skipinitialspace=True)

    body = []
    total = {
        'cosmetics': 0,
        'supplement': 0,
        'promotion': 0,
        '85': 0,
        '156': 0,
        '157': 0,
        '158': 0,
        '914': 0,
        '915': 0,
        '916': 0,
    }
    is_counting, summarized = reset_summarized()

    df.dropna(how='all')
    for index, row in df.iterrows():
        if is_ignore_row(row['name']) is not None:
            continue

        if is_counting is False:
            is_counting = True
            summarized['name'] = row['name']
            continue

        if row['name'] == '【  得意先計  】':
            validate_total_amount(summarized, row['retail_amount'])
            body = add_body(body, summarized)
            total = sum_total(
                total,
                summarized['amount'],
                summarized['quantity'])

            is_counting, summarized = reset_summarized()
            continue

        product_code = extract_product_code(row['name'])
        validate_exists_product(product_code)

        product = products.SCHEME[product_code]
        summarized = sumup(summarized, product['type'], row['retail_amount'])
        summarized = sumup_quantity(
            summarized, product_code, int(float(row['quantity'])))

    write_csv(body, total)


def reset_summarized():
    skeleton = {
        'name': '',
        'amount': {'cosmetics': 0, 'supplement': 0, 'promotion': 0, },
        'quantity': {'85': 0, '156': 0, '157': 0, '158': 0, '914': 0, '915': 0, '916': 0, },
    }
    return (False, skeleton)


def is_ignore_row(name):
    if pd.isnull(name):
        return name

    return re.match('^[期間\\s.+|得意先コード 得意先名|商品コード 商品名]|【  合  計  】',
                    name)


def number_unformat(price):
    return int(re.sub('[^0-9\\-]', '', price))


def sumup(summarized, type, retail_amount):
    unformated_retail_amount = number_unformat(retail_amount)

    if type == 'cosmetics':
        summarized['amount']['cosmetics'] += unformated_retail_amount
    elif type == 'supplement':
        summarized['amount']['supplement'] += unformated_retail_amount
    elif type == 'promotion':
        summarized['amount']['promotion'] += unformated_retail_amount
    else:
        raise Exception(
            '定義されていない種別が存在しています 種別: {type}'.format(type=type))

    return summarized


def sumup_quantity(summarized, code, quantity):
    if code == '85':
        summarized['quantity']['85'] += quantity
    elif code == '156':
        summarized['quantity']['156'] += quantity
    elif code == '157':
        summarized['quantity']['157'] += quantity
    elif code == '158':
        summarized['quantity']['158'] += quantity
    elif code == '914':
        summarized['quantity']['914'] += quantity
    elif code == '915':
        summarized['quantity']['915'] += quantity
    elif code == '916':
        summarized['quantity']['916'] += quantity

    return summarized


def extract_product_code(name):
    matched = re.match('^([0-9]+)\\s.+', name)
    if matched is None:
        return 'none'
    return matched.group(1)


def validate_exists_product(code):
    if code not in products.SCHEME:
        raise Exception(
            '商品マスタに存在しない商品の売上が計上されています 商品コード: {product_code}'.format(
                product_code=code))


def validate_total_amount(summarized, row_amount):
    calculated_amount = total_amount(summarized['amount'])
    row_amount = number_unformat(row_amount)
    if calculated_amount != row_amount:
        raise Exception('合計金額が一致しません BC: {name}, '
                        '上代金額（計算）: {calculated_amount}, '
                        '上代金額（ファイル）: {row_amount}'
                        .format(name=summarized['name'],
                                calculated_amount=calculated_amount,
                                row_amount=row_amount))


def total_amount(amount):
    total = 0
    for v in amount.values():
        total += v
    return total


def add_body(body, summarized):
    bc = parse_bc(summarized['name'])
    body.append([bc.group(1),
                 bc.group(2),
                 "{:,}".format(summarized['amount']['cosmetics']),
                 "{:,}".format(summarized['amount']['supplement']),
                 "{:,}".format(
        summarized['amount']['cosmetics'] + summarized['amount']['supplement']),
        summarized['quantity']['85'] if summarized['quantity']['85'] != 0 else '',
        summarized['quantity']['156'] if summarized['quantity']['156'] != 0 else '',
        summarized['quantity']['157'] if summarized['quantity']['157'] != 0 else '',
        summarized['quantity']['158'] if summarized['quantity']['158'] != 0 else '',
        summarized['quantity']['914'] if summarized['quantity']['914'] != 0 else '',
        summarized['quantity']['915'] if summarized['quantity']['915'] != 0 else '',
        summarized['quantity']['916'] if summarized['quantity']['916'] != 0 else ''])

    return body


def parse_bc(bc):
    matched = re.match('^([0-9]+)\\s(.+)', bc)
    if matched is None:
        return ''
    return matched


def sum_total(total, amount, quantity):
    total['cosmetics'] += amount['cosmetics']
    total['supplement'] += amount['supplement']
    total['promotion'] += amount['promotion']
    total['85'] += quantity['85']
    total['156'] += quantity['156']
    total['157'] += quantity['157']
    total['158'] += quantity['158']
    total['914'] += quantity['914']
    total['915'] += quantity['915']
    total['916'] += quantity['916']

    return total


def write_csv(body, total):
    with open(SUMMARIZED_FILE, 'w') as f:
        header = [
            '得意先コード',
            '得意先名',
            '化粧品',
            '健食',
            '合計',
            '85 酵素',
            '156 セット3 I',
            '157 セット3 II',
            '158 セット3 セル',
            '914 ベスト4アルソアセットI',
            '915 ベスト4アルソアセットII',
            '916 ベスト4アルソアセットCELL',
        ]
        footer = [
            '',
            '合計',
            "{:,}".format(total['cosmetics']),
            "{:,}".format(total['supplement']),
            "{:,}".format(total['cosmetics'] + total['supplement']),
            total['85'] if total['85'] != 0 else '',
            total['156'] if total['156'] != 0 else '',
            total['157'] if total['157'] != 0 else '',
            total['158'] if total['158'] != 0 else '',
            total['914'] if total['914'] != 0 else '',
            total['915'] if total['915'] != 0 else '',
            total['916'] if total['916'] != 0 else '',
        ]
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(body)
        writer.writerow(footer)
