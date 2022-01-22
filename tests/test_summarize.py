# -*- coding: utf-8 -*-

import filecmp
import unittest

from summarize import summarize


class TestSummarize(unittest.TestCase):
    def test_number_unformat(self):
        test_cases = [
            ('1,000', 1000),
            ('¥1,500', 1500),
            ('-¥100,000', -100000),
            ('(30,000)', -30000),
        ]

        for number, expected in test_cases:
            with self.subTest(number=number, expected=expected):
                self.assertEqual(summarize.number_unformat(number), expected)

    def test_summarize(self):
        test_file = 'tests/files/summarize/green.csv'
        expected_file = 'tests/files/summarize/expected/green.csv'

        with self.subTest(file=test_file, expected=expected_file):
            summarize.handle(test_file)
            self.assertTrue(
                filecmp.cmp(
                    'resources/summarized_r_by_customer.csv',
                    expected_file))

    def test_exception(self):
        test_cases = [
            ('tests/files/summarize/red_invalid_product_code.csv',
             '商品マスタに存在しない商品の売上が計上されています 商品コード: 0987654321'),
            ('tests/files/summarize/red_total_amount_not_match.csv',
             '合計金額が一致しません BC: 得意先B, 上代金額（計算）: 83700, 上代金額（ファイル）: 83705')
        ]

        for test_file, expected in test_cases:
            with self.assertRaises(Exception) as ex:
                summarize.handle(test_file)
            actual = ex.exception.args[0]
            with self.subTest(actual=actual, expected=expected):
                self.assertEqual(actual, expected)


if __name__ == '__main__':
    unittest.main()
