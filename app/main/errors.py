from flask import render_template

from . import main_bp


@main_bp.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@main_bp.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500
