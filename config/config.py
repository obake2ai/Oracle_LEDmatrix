# SSH経由で転送する先の設定

PI_CONFIG = {
    # 共通設定
    'gpio-slowdown': 1,
    'no_hardware_pulse': True,
    'led-pwm-bits': 4,
    # 各転送先の設定（ここに最大20件程度追加可能）
    'settings': [
        {
            'host': 'zero2wh06',
            'target_dir': './share/12x3',
            'chain_length': 12,
            'parallel': 3,
            'idx': 1,
        },
        {
            'host': 'zero2wh05',
            'target_dir': './share/12x3',
            'chain_length': 12,
            'parallel': 3,
            'idx': 2,
        },
        {
            'host': 'zero2wh07',
            'target_dir': './share/12x3',
            'chain_length': 12,
            'parallel': 3,
            'idx': 3,
        },
        {
            'host': 'zero2wh02',
            'target_dir': './share/12x3',
            'chain_length': 12,
            'parallel': 3,
            'idx': 1,
        },
        {
            'host': 'zero2wh03',
            'target_dir': './share/12x3',
            'chain_length': 12,
            'parallel': 3,
            'idx': 2,
        },
        {
            'host': 'zero2wh01',
            'target_dir': './share/12x3',
            'chain_length': 12,
            'parallel': 3,
            'idx': 3,
        },
    ]
}
