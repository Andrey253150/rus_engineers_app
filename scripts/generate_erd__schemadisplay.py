# Эксперементальный скрипт, не добавлен в pre-commit 

from sqlalchemy_schemadisplay import create_schema_graph

from app import create_app, db

# Создаём Flask-приложение
app = create_app()

# Входим в контекст приложения
with app.app_context():

    # Строим ER-диаграмму
    graph = create_schema_graph(
        metadata=db.metadata,
        engine=db.engine,       # Получаем engine из SQLAlchemy
        show_datatypes=True,
        show_indexes=False,
        show_column_keys=True,
        rankdir='LR',
        concentrate=False
    )

    # Сохраняем PNG
    graph.write_png("docs/erd.png")
    print("✅ ER-диаграмма сохранена в docs/erd.png")
