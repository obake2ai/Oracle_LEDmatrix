#!/usr/bin/env python3
import os
import time
import glob

import click
from PIL import Image
from rgbmatrix import RGBMatrix, RGBMatrixOptions


def get_latest_image_path(folder):
    """
    指定フォルダ内のファイルのうち、もっとも新しい画像ファイルのパスを返す。
    画像ファイルが無い場合は None を返す。
    """
    valid_extensions = (".jpg", ".jpeg", ".png", ".gif", ".bmp")
    files = glob.glob(os.path.join(folder, "*"))

    if not files:
        return None

    # 更新時刻が新しい順にソート
    files.sort(key=os.path.getmtime, reverse=True)

    # 画像ファイルかどうかを確認し、一番最初に見つかった画像ファイルを返す
    for file_path in files:
        if file_path.lower().endswith(valid_extensions):
            return file_path

    return None


def setup_matrix(rows, cols, chain_length, parallel,
                 hardware_mapping, gpio_slowdown, no_hardware_pulse,
                 pwm_bits, pwm_lsb_nanoseconds):
    """
    rpi-rgb-led-matrix のオプションを設定し、RGBMatrix インスタンスを返す。
    PWM 関連のパラメータを設定することでフレッシュレートの向上を試みる。
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

    # ハードウェアパルス無効化の設定
    if no_hardware_pulse:
        options.disable_hardware_pulsing = True

    # PWM 関連の設定
    options.pwm_bits = pwm_bits
    options.pwm_lsb_nanoseconds = pwm_lsb_nanoseconds

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
@click.option('--gpio-slowdown', default=0, type=int,
              help='GPIO のスローダウン設定。0 で最大フレッシュレート (ただしハードウェアの安定性に注意)')
@click.option('--no-hardware-pulse', is_flag=True,
              help='--led-no-hardware-pulse 相当。root 権限不要で実行する場合に指定する。')
@click.option('--pwm-bits', default=7, type=int,
              help='PWM ビット数。低い値ほど高フレッシュレートになるが色の階調が減少')
@click.option('--pwm-lsb-nanoseconds', default=80, type=int,
              help='PWM LSB nanoseconds。低い値ほど高フレッシュレートになる')
def main(watch_folder, rows, cols, chain_length, parallel,
         hardware_mapping, gpio_slowdown, no_hardware_pulse,
         pwm_bits, pwm_lsb_nanoseconds):
    """
    LED パネルをセットアップし、監視フォルダにある最新の画像を表示します。

    改善点:
    - ダブルバッファリング (CreateFrameCanvas と SwapOnVSync) により更新時のちらつきを低減
    - PWM ビット数と PWM LSB nanoseconds の調整により、フレッシュレート向上を試みる
    """
    # LEDマトリックスのセットアップ
    matrix = setup_matrix(rows, cols, chain_length, parallel,
                          hardware_mapping, gpio_slowdown, no_hardware_pulse,
                          pwm_bits, pwm_lsb_nanoseconds)

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
                    # 合計解像度にリサイズ（Lanczos フィルタで高品質リサイズ）
                    image = image.resize((total_width, total_height), Image.Resampling.LANCZOS)

                    # キャンバスをクリアして新しい画像をセット
                    canvas.Clear()
                    canvas.SetImage(image, 0, 0)
                    # ダブルバッファリングでスムーズに画面更新
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
