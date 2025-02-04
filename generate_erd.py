from eralchemy import render_er

from app import create_app, db

app = create_app()
output_file = 'docs/erd_russian-engineers.png'

with app.app_context():
    try:
        render_er(db.Model, output_file)
        print(f"ER-диаграмма сохранена в {output_file}")
    except Exception as e:
        print(f"Ошибка при генерации ER-диаграммы: {e}")

app.logger.info('Диаграмма успешно сохранена в docs/erd_russian-engineers.png')
