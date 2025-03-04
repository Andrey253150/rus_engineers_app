from pathlib import Path

from eralchemy import render_er

from app import create_app, db

app = create_app()

# Путь для сохранения ER-диаграммы
BASE_DIR = Path(__file__).resolve().parent
erd_path = str(BASE_DIR / "source" / "static" / "images" / "erd_russian-engineers.png")

with app.app_context():
    try:
        render_er(db.Model, erd_path)
        app.logger.info(f"ER-диаграмма успешно сохранена в {erd_path}")
    except Exception as e:
        app.logger.error(f"Ошибка при генерации ER-диаграммы: {e}")
