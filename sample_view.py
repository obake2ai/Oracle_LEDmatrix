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
    監視フォルダにある最も新しい画像ファイルを直列に接続されたパネルに表示します。
    新たな画像が入るまで表示を保持します。

    改善点:
    - ダブルバッファリング (matrix.CreateFrameCanvas() と SwapOnVSync) により更新時のちらつきを低減
    - GPIOスローダウンやハードウェアパルス無効化のオプションも引き続き利用可能
    """
    # LEDマトリックスのセットアップ
    matrix = setup_matrix(rows, cols, chain_length, parallel,
                          hardware_mapping, gpio_slowdown, no_hardware_pulse)

    # パネル全体の解像度 (例: 3x3パネル、各64x64 → 192x192)
    total_width = cols * chain_length
    total_height = rows * parallel

    # ダブルバッファリング用キャンバスの作成
    canvas = matrix.CreateFrameCanvas()

    # 現在表示中の画像パスを記録
    current_displayed_path = None

    try:
        while True:
            latest_image_path = get_latest_image_path(watch_folder)

            # 新しい画像ファイルが見つかった場合のみ再表示
            if latest_image_path and latest_image_path != current_displayed_path:
                try:
                    image = Image.open(latest_image_path).convert("RGB")
                    # 合計解像度にリサイズ（高品質な Lanczos フィルタを使用）
                    image = image.resize((total_width, total_height), Image.Resampling.LANCZOS)

                    # キャンバスをクリアして新しい画像をセット
                    canvas.Clear()
                    canvas.SetImage(image, 0, 0)
                    # ダブルバッファリングにより、SwapOnVSync() でスムーズに更新
                    canvas = matrix.SwapOnVSync(canvas)

                    current_displayed_path = latest_image_path
                    print(f"[INFO] Displayed new image: {latest_image_path}")
                except Exception as e:
                    print(f"[ERROR] Failed to display {latest_image_path}: {e}")

            # 1秒ごとに監視フォルダを再確認
            time.sleep(1)
    except KeyboardInterrupt:
        print("Exiting gracefully.")


if __name__ == '__main__':
    main()
