from flask.cli import FlaskGroup
from flask_migrate import MigrateCommand

from app import create_app


# Создаем объект FlaskGroup
def create_cli_app(config_name=None):
    app = create_app(config_name)
    return app


cli = FlaskGroup(create_cli_app)
cli.add_command('db', MigrateCommand)

if __name__ == "__main__":
    cli()
