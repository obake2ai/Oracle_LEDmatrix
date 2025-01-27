#!/usr/bin/env python3

import os
import time
import glob
from PIL import Image
from rgbmatrix import RGBMatrix, RGBMatrixOptions

# 監視するフォルダ (絶対パス or 相対パス)
WATCH_FOLDER = "/home/pi/watch_folder"

def setup_matrix():
    """
    rpi-rgb-led-matrix のオプションを設定し、RGBMatrix インスタンスを返す。
    """
    options = RGBMatrixOptions()
    options.rows = 64            # パネル1枚あたりの行数
    options.cols = 64            # パネル1枚あたりの列数
    options.chain_length = 3     # 横方向に連結されたパネル数
    options.parallel = 3         # 縦方向に連結されたパネル数
    options.hardware_mapping = 'regular'  # 配線方法に応じて変更
    # 下記のように必要に応じて設定可能
    # options.gpio_slowdown = 4

    matrix = RGBMatrix(options=options)
    return matrix


def get_latest_image_path(folder):
    """
    指定フォルダ内のファイルのうち、もっとも新しい「画像ファイル」のパスを返す。
    画像ファイルが無い場合は None を返す。
    """
    # 監視したい拡張子(ここではjpg/png/gif/bmpあたりを想定)
    valid_extensions = (".jpg", ".jpeg", ".png", ".gif", ".bmp")

    # フォルダ内のファイル一覧を取得して、更新日時順にソート
    files = glob.glob(os.path.join(folder, "*"))
    if not files:
        return None

    # 更新時刻が新しいファイル順にソート
    files.sort(key=os.path.getmtime, reverse=True)

    # 上から順に画像ファイルかどうか確認し、一番最初に見つかった画像ファイルを返す
    for file_path in files:
        if file_path.lower().endswith(valid_extensions):
            return file_path

    return None


def main():
    # LEDマトリックスのセットアップ
    matrix = setup_matrix()

    # 表示中のファイルパスを記録しておくための変数
    current_displayed_path = None

    while True:
        latest_image_path = get_latest_image_path(WATCH_FOLDER)

        # 新しい画像ファイルが見つかった場合
        if latest_image_path and latest_image_path != current_displayed_path:
            try:
                # 画像を読み込んで 192x192 にリサイズ
                image = Image.open(latest_image_path)
                image = image.convert("RGB")
                image = image.resize((192, 192), Image.ANTIALIAS)

                # LEDマトリックスに表示
                matrix.SetImage(image, 0, 0)

                # 現在表示中のファイルパスを更新
                current_displayed_path = latest_image_path

                print(f"[INFO] New image displayed: {latest_image_path}")
            except Exception as e:
                print(f"[ERROR] Failed to display image {latest_image_path}: {e}")

        # 1秒ごとに監視フォルダを再確認
        time.sleep(1)


if __name__ == "__main__":
    main()
