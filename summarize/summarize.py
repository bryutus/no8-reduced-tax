# -*- coding: utf-8 -*-

import csv
import os
import re
import sys
from typing import List, Dict, Tuple, Any, Union

import pandas as pd

from . import products

SUMMARIZED_FILE = 'resources/summarized_r_by_customer.csv'

PRODUCT_CODES: Dict[str, List[str]] = {
    'georina': ['51'],
    'soap': ['1120'],
    'pack': ['1130'],
    'lotion': ['1121', '1131', '1141', '49'],
    'big_lotion': ['917', '918', '919'],
    'essence': ['1124', '1134', '1144', '50'],
    'set3': ['156', '157', '158'],
    'best4': ['914', '915', '916'],
}

def main() -> None:
    args = sys.argv

    if len(args) != 2:
        print('集計するファイルを1ファイル指定してください')
        quit()

    file_path = args[1]
    if os.path.isfile(file_path) is False:
        print('集計するファイルが存在しません')
        quit()

    handle(file_path)


def handle(filepath: str) -> None:
    df = pd.read_csv(filepath,
                     header=0,
                     usecols=[3, 4, 5, 8, 10, 11, 12, 13],
                     names=[
                         'bc_code',
                         'name',
                         'product_code',
                         'quantity',
                         'selling_amount',
                         'total_selling_amount',
                         'retail_amount',
                         'total_retail_amount'],
                     dtype={
                         'bc_code': 'unicode',
                         'name': 'unicode',
                         'product_code': 'unicode',
                     },
                     skipinitialspace=True)

    body: List[List[Any]] = []
    total: Dict[str, int] = {
        'cosmetics': 0,
        'supplement': 0,
        'promotion': 0,
        'georina': 0,
        'soap': 0,
        'pack': 0,
        'lotion': 0,
        'big_lotion': 0,
        'essence': 0,
        'set3': 0,
        'best4': 0,
    }
    is_counting, summarized = reset_summarized()

    df.dropna(how='all')
    for index, row in df.iterrows():
        if is_ignore_row(row):
            continue

        if is_counting is False:
            is_counting = True
            summarized['name'] = row['name']
            summarized['bc_code'] = row['bc_code']
            continue

        if pd.notnull(row['total_retail_amount']):
            validate_selling_retail_amount(
                summarized, row['total_selling_amount'])
            validate_total_retail_amount(
                summarized, row['total_retail_amount'])

            body = add_body(body, summarized)

            total = sum_total(
                total,
                summarized)

            is_counting, summarized = reset_summarized()
            continue

        validate_exists_product(row['product_code'])

        product = products.SCHEME[row['product_code']]
        summarized = sumup(
            summarized,
            product['type'],
            row['selling_amount'],
            row['retail_amount'])
        summarized = sumup_quantity(
            summarized, row['product_code'], int(float(row['quantity'])))

    write_csv(body, total)


def reset_summarized() -> Tuple[bool, Dict[str, Any]]:
    skeleton: Dict[str, Any] = {
        'name': '',
        'bc_code': '',
        'selling_amount': {'cosmetics': 0, 'supplement': 0, 'promotion': 0, },
        'retail_amount': {'cosmetics': 0, 'supplement': 0, 'promotion': 0, },
        'quantity': {'georina': 0, 'soap': 0, 'pack': 0, 'lotion': 0, 'big_lotion': 0, 'essence': 0, 'set3': 0, 'best4': 0, },
    }

    return (False, skeleton)


def is_ignore_row(row: pd.Series) -> bool:
    return pd.isnull(row['name']) and pd.isnull(
        row['product_code']) and pd.isnull(row['total_retail_amount'])


def number_unformat(price: str) -> int:
    price = re.sub('^\\(', '-', price)
    return int(re.sub('[^0-9\\-]', '', price))


def sumup(summarized: Dict[str, Any], type: str, selling_amount: str, retail_amount: str) -> Dict[str, Any]:
    unformated_retail_amount = number_unformat(retail_amount)
    unformated_selling_amount = number_unformat(selling_amount)

    if type == 'cosmetics':
        summarized['retail_amount']['cosmetics'] += unformated_retail_amount
        summarized['selling_amount']['cosmetics'] += unformated_selling_amount
    elif type == 'supplement':
        summarized['retail_amount']['supplement'] += unformated_retail_amount
        summarized['selling_amount']['supplement'] += unformated_selling_amount
    elif type == 'promotion':
        summarized['retail_amount']['promotion'] += unformated_retail_amount
        summarized['selling_amount']['promotion'] += unformated_selling_amount
    else:
        raise Exception(
            '定義されていない種別が存在しています 種別: {type}'.format(type=type))

    return summarized


def sumup_quantity(summarized: Dict[str, Any], code: str, quantity: int) -> Dict[str, Any]:
    if code in PRODUCT_CODES['georina']:
        summarized['quantity']['georina'] += quantity
    elif code in PRODUCT_CODES['soap']:
        summarized['quantity']['soap'] += quantity
    elif code in PRODUCT_CODES['pack']:
        summarized['quantity']['pack'] += quantity
    elif code in PRODUCT_CODES['lotion']:
        summarized['quantity']['lotion'] += quantity
    elif code in PRODUCT_CODES['big_lotion']:
        summarized['quantity']['big_lotion'] += quantity
    elif code in PRODUCT_CODES['essence']:
        summarized['quantity']['essence'] += quantity
    elif code in PRODUCT_CODES['set3']:
        summarized['quantity']['set3'] += quantity
    elif code in PRODUCT_CODES['best4']:
        summarized['quantity']['best4'] += quantity

    return summarized


def validate_exists_product(code: str) -> None:
    if code not in products.SCHEME:
        raise Exception(
            '商品マスタに存在しない商品の売上が計上されています 商品コード: {product_code}'.format(
                product_code=code))


def validate_selling_retail_amount(summarized: Dict[str, Any], row_amount: str) -> None:
    calculated_amount = total_amount(summarized['selling_amount'])
    unformatted = number_unformat(row_amount)
    if calculated_amount != unformatted:
        raise Exception('売価金額合計が一致しません BC: {bc_code} {name}, '
                        '売価金額（計算）: {calculated_amount}, '
                        '売価金額（ファイル）: {row_amount}'
                        .format(name=summarized['name'],
                                bc_code=summarized['bc_code'],
                                calculated_amount=calculated_amount,
                                row_amount=unformatted))


def validate_total_retail_amount(summarized: Dict[str, Any], row_amount: str) -> None:
    calculated_amount = total_amount(summarized['retail_amount'])
    unformatted = number_unformat(row_amount)
    if calculated_amount != unformatted:
        raise Exception('上代金額合計が一致しません BC: {bc_code} {name}, '
                        '上代金額（計算）: {calculated_amount}, '
                        '上代金額（ファイル）: {row_amount}'
                        .format(name=summarized['name'],
                                bc_code=summarized['bc_code'],
                                calculated_amount=calculated_amount,
                                row_amount=unformatted))


def total_amount(amount: Dict[str, int]) -> int:
    return sum(amount.values())


def add_body(body: List[List[Any]], summarized: Dict[str, Any]) -> List[List[Any]]:
    body.append([summarized['bc_code'],
                 summarized['name'],
                 "{:,}".format(summarized['retail_amount']['cosmetics']),
                 "{:,}".format(summarized['retail_amount']['supplement']),
                 "{:,}".format(summarized['selling_amount']['promotion']),
                 "{:,}".format(
        summarized['retail_amount']['cosmetics'] + summarized['retail_amount']['supplement'] + summarized['selling_amount']['promotion']),
        summarized['quantity']['georina'] if summarized['quantity']['georina'] != 0 else '',
        summarized['quantity']['soap'] if summarized['quantity']['soap'] != 0 else '',
        summarized['quantity']['pack'] if summarized['quantity']['pack'] != 0 else '',
        summarized['quantity']['lotion'] if summarized['quantity']['lotion'] != 0 else '',
        summarized['quantity']['big_lotion'] if summarized['quantity']['big_lotion'] != 0 else '',
        summarized['quantity']['essence'] if summarized['quantity']['essence'] != 0 else '',
        summarized['quantity']['set3'] if summarized['quantity']['set3'] != 0 else '',
        summarized['quantity']['best4'] if summarized['quantity']['best4'] != 0 else '',
    ])

    return body


def sum_total(total: Dict[str, int], summarized: Dict[str, Any]) -> Dict[str, int]:
    total['cosmetics'] += summarized['retail_amount']['cosmetics']
    total['supplement'] += summarized['retail_amount']['supplement']
    total['promotion'] += summarized['selling_amount']['promotion']
    total['georina'] += summarized['quantity']['georina']
    total['soap'] += summarized['quantity']['soap']
    total['pack'] += summarized['quantity']['pack']
    total['lotion'] += summarized['quantity']['lotion']
    total['big_lotion'] += summarized['quantity']['big_lotion']
    total['essence'] += summarized['quantity']['essence']
    total['set3'] += summarized['quantity']['set3']
    total['best4'] += summarized['quantity']['best4']

    return total


def write_csv(body: List[List[Any]], total: Dict[str, int]) -> None:
    with open(SUMMARIZED_FILE, 'w') as f:
        header = [
            'BCコード',
            '得意先名',
            '化粧品',
            '健食',
            '販促',
            '合計',
            '酵素（製品コード：' + '/'.join(PRODUCT_CODES['georina']) + '）',
            '石鹸（製品コード：' + '/'.join(PRODUCT_CODES['soap']) + '）',
            'パック（製品コード：' + '/'.join(PRODUCT_CODES['pack']) + '）',
            'ローション（製品コード：' + '/'.join(PRODUCT_CODES['lotion']) + '）',
            'ビッグローション（製品コード：' + '/'.join(PRODUCT_CODES['big_lotion']) + '）',
            'エッセンス（製品コード：' + '/'.join(PRODUCT_CODES['essence']) + '）',
            'セット3（製品コード：' + '/'.join(PRODUCT_CODES['set3']) + '）',
            'ベスト4（製品コード：' + '/'.join(PRODUCT_CODES['best4']) + '）',
        ]
        footer = [
            '',
            '合計',
            "{:,}".format(total['cosmetics']),
            "{:,}".format(total['supplement']),
            "{:,}".format(total['promotion']),
            "{:,}".format(
                total['cosmetics'] +
                total['supplement'] +
                total['promotion']),
            total['georina'] if total['georina'] != 0 else '',
            total['soap'] if total['soap'] != 0 else '',
            total['pack'] if total['pack'] != 0 else '',
            total['lotion'] if total['lotion'] != 0 else '',
            total['big_lotion'] if total['big_lotion'] != 0 else '',
            total['essence'] if total['essence'] != 0 else '',
            total['set3'] if total['set3'] != 0 else '',
            total['best4'] if total['best4'] != 0 else '',
        ]
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(body)
        writer.writerow(footer)
