import logging

# Создаём логгер
logger = logging.getLogger('my_app')
logger.setLevel(logging.INFO)

# Настройка формата
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Добавляем обработчик для вывода в консоль
handler = logging.StreamHandler()
handler.setFormatter(formatter)
logger.addHandler(handler)
