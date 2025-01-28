# Файл для экспериментов, не относится к приложению.

config = {
    'development': 'DevelopmentConfig',
    'testing': 'TestingConfig',

    'default': 'DevelopmentConfig'
}


# input_config = input("Введите конфиг:")
# if input_config not in config:
#     print(f'Нет такого конфига. Сейчас доступны: {list(config.keys())}')
# else:
#     print('Норм конфиг!')

print(f'Дефолтный кокнфиг: {config.get("default")}')

