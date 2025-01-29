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

    # 上から順に画像ファイルかどうかを確認し、一番最初に見つかった画像ファイルを返す
    for file_path in files:
        if file_path.lower().endswith(valid_extensions):
            return file_path

    return None


def setup_matrix(rows, cols, chain_length, parallel,
                 hardware_mapping, gpio_slowdown, no_hardware_pulse):
    """
    rpi-rgb-led-matrix のオプションを設定し、RGBMatrix インスタンスを返す。
    --no-hardware-pulse（hardware_pulsing を無効化）指定時は root 不要で実行可能
    """
    options = RGBMatrixOptions()
    options.rows = rows
    options.cols = cols
    options.chain_length = chain_length
    options.parallel = parallel
    options.hardware_mapping = hardware_mapping

    # GPIO スローダウン設定
    if gpio_slowdown is not None:
        options.gpio_slowdown = gpio_slowdown

    # --no-hardware-pulse ならハードウェアパルス生成を無効化
    if no_hardware_pulse:
        # rpi-rgb-led-matrix の Python ラッパーでは disable_hardware_pulsing に True を設定
        options.disable_hardware_pulsing = True

    return RGBMatrix(options=options)


@click.command()
@click.option('--watch-folder', '-w', default='./samples',
              help='監視するフォルダのパス')
@click.option('--rows', default=64, help='パネル1枚あたりの行数')
@click.option('--cols', default=64, help='パネル1枚あたりの列数')
@click.option('--chain-length', default=3, help='横方向に連結されたパネル数')
@click.option('--parallel', default=3, help='縦方向に連結されたパネル数')
@click.option('--hardware-mapping', default='regular',
              help='rpi-rgb-led-matrix での配線方法 (例: "regular", "adafruit-hat" 等)')
@click.option('--gpio-slowdown', default=None, type=int,
              help='GPIO のスローダウン設定')
@click.option('--no-hardware-pulse', is_flag=True,
              help='--led-no-hardware-pulse 相当。root 権限不要で実行する場合に指定する。')
def main(watch_folder, rows, cols, chain_length, parallel,
         hardware_mapping, gpio_slowdown, no_hardware_pulse):
    """
    指定されたオプションを使って LED パネルをセットアップし、
    監視フォルダにある最も新しい画像ファイルを 3x3(合計9枚)のパネルに表示。
    新たな画像が入るまで表示を保持する。
    """
    # LED マトリックスのセットアップ
    matrix = setup_matrix(rows, cols, chain_length, parallel,
                          hardware_mapping, gpio_slowdown,
                          no_hardware_pulse)

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
