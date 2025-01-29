#!/usr/bin/env python3

import os
import time
import glob

import click
from PIL import Image
from rgbmatrix import RGBMatrix, RGBMatrixOptions


def get_latest_image_path(folder):
    """
    指定フォルダ内のファイルのうち、もっとも新しい「画像ファイル」のパスを返す。
    画像ファイルが無い場合は None を返す。
    """
    valid_extensions = (".jpg", ".jpeg", ".png", ".gif", ".bmp")
    files = glob.glob(os.path.join(folder, "*"))

    if not files:
        return None

    # 更新時刻が新しい順にソート
    files.sort(key=os.path.getmtime, reverse=True)

    # 画像ファイルかどうかをチェックして、最初に見つかったものを返す
    for file_path in files:
        if file_path.lower().endswith(valid_extensions):
            return file_path

    return None


def setup_matrix(rows, cols, chain_length, parallel,
                 hardware_mapping, gpio_slowdown):
    """
    rpi-rgb-led-matrix のオプションを設定し、RGBMatrix インスタンスを返す。
    """
    options = RGBMatrixOptions()
    options.rows = rows
    options.cols = cols
    options.chain_length = chain_length
    options.parallel = parallel
    options.hardware_mapping = hardware_mapping
    if gpio_slowdown is not None:
        options.gpio_slowdown = gpio_slowdown

    matrix = RGBMatrix(options=options)
    return matrix


@click.command()
@click.option('--watch-folder', '-w', default='/home/pi/watch_folder',
              help='監視するフォルダのパス')
@click.option('--rows', default=64, help='パネル1枚あたりの行数')
@click.option('--cols', default=64, help='パネル1枚あたりの列数')
@click.option('--chain-length', default=3, help='横方向に連結されたパネル数')
@click.option('--parallel', default=3, help='縦方向に連結されたパネル数')
@click.option('--hardware-mapping', default='regular',
              help='rpi-rgb-led-matrix での配線方法 (例: "regular", "adafruit-hat", 等)')
@click.option('--gpio-slowdown', default=None, type=int,
              help='GPIO のスローダウン設定')
def main(watch_folder, rows, cols, chain_length, parallel,
         hardware_mapping, gpio_slowdown):
    """
    指定されたオプションを使って LED パネルをセットアップし、
    監視フォルダにある最も新しい画像ファイルを 3x3(合計9枚)のパネルに表示。
    新たな画像が入るまで表示を保持する。
    """
    # LED マトリックスのセットアップ
    matrix = setup_matrix(rows, cols, chain_length, parallel,
                          hardware_mapping, gpio_slowdown)

    # パネル全体の解像度 (3x3, 64x64 の場合は 192x192)
    total_width = cols * chain_length
    total_height = rows * parallel

    # 現在表示中のファイルパスを記録しておくための変数
    current_displayed_path = None

    while True:
        latest_image_path = get_latest_image_path(watch_folder)

        # 新しい画像ファイルが見つかった場合のみ再表示
        if latest_image_path and latest_image_path != current_displayed_path:
            try:
                image = Image.open(latest_image_path).convert("RGB")
                # 合計解像度にリサイズ
                image = image.resize((total_width, total_height), Image.Resampling.LANCZOS)

                matrix.SetImage(image, 0, 0)
                current_displayed_path = latest_image_path
                print(f"[INFO] Displayed new image: {latest_image_path}")
            except Exception as e:
                print(f"[ERROR] Failed to display {latest_image_path}: {e}")

        # 1秒ごとに監視フォルダを再確認
        time.sleep(1)


if __name__ == '__main__':
    main()
