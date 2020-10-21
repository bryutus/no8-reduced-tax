# -*- coding: utf-8 -*-

import os
import sys
import tabula


def to_csv():
    args = sys.argv

    if len(args) != 2:
        print('変換するファイルを1ファイル指定してください')
        quit()

    file_path = args[1]
    if os.path.isfile(file_path) is False:
        print('変換するファイルが存在しません')
        quit()

    path, ext = os.path.splitext(file_path)
    tabula.convert_into(file_path,
                        f'{path}.csv',
                        pages='all',
                        output_format='csv')
