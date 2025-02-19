# SSH経由で転送する先の設定

PI_CONFIG = {
    # 共通設定
    'gpio-slowdown': 1,
    'no_hardware_pulse': True,
    'led-pwm-bits': 4,
    # 各転送先の設定（ここに最大20件程度追加可能）
    'settings': [
        {
            'host': 'zero2wh01.local', #zero2wh04.local
            'target_dir': './share/12x6',
            'chain_length': 12,
            'parallel': 6,
            'idx': 1,
        },
        {
            'host': 'zero2wh02.local', #zero2wh04.local
            'target_dir': './share/12x6',
            'chain_length': 12,
            'parallel': 6,
            'idx': 2,
        },
        {
            'host': 'zero2wh03.local', #zero2wh04.local
            'target_dir': './share/12x6',
            'chain_length': 12,
            'parallel': 6,
            'idx': 3,
        },
        {
            'host': 'zero2wh04.local', #zero2wh04.local
            'target_dir': './share/12x6',
            'chain_length': 12,
            'parallel': 6,
            'idx': 4,
        },
        {
            'host': 'zero2wh05.local', #zero2wh04.local
            'target_dir': './share/12x6',
            'chain_length': 12,
            'parallel': 6,
            'idx': 5,
        },
        {
            'host': 'zero2wh06.local', #zero2wh04.local
            'target_dir': './share/12x6',
            'chain_length': 12,
            'parallel': 6,
            'idx': 6,
        },
    ]
}
