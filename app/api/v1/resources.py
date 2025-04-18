from collections import OrderedDict

from flask import (abort, current_app, g, json, jsonify, make_response,
                   request, url_for)
from flask_httpauth import HTTPBasicAuth
from sqlalchemy import select

from app.models import AnonymousUser, Comment, Permission, Post, User, db

from . import api_v1_bp
from .decorators import permission_required

# Расширение Flask-HTTPAuth инициализируется в пакете этого макета, а не в пакете приложения,
# т.к. этот тип аутентификации будет использоваться только в рамках макета API.
auth = HTTPBasicAuth()


@api_v1_bp.before_request
@auth.login_required
def before_request():
    if not g.current_user.confirmed:
        return abort(400)


@auth.verify_password
def verify_password(email_or_token, password) -> bool:
    """Проверяет аутентификацию пользователя через email/пароль или токен.

    Поддерживает три режима аутентификации:
    1. Анонимный доступ (если учётные данные не переданы).
    2. По токену (если пароль пустой).
    3. По email и паролю (классическая аутентификация).

    Args:
        email_or_token (str):
            - Email пользователя (для входа по паролю).
            - Или токен аутентификации (если пароль пустой).
            - Пустая строка для анонимного доступа.
        password (str):
            - Пароль пользователя.
            - Пустая строка, если используется токен.

    Returns:
        bool:
            - True: аутентификация успешна. Пользователь сохраняется в `g.current_user`.
            - False: неверные учётные данные (пользователь не найден/некорректный пароль/токен).

    Side Effects:
        - Устанавливает глобальные объекты Flask:
            - `g.current_user`: объект пользователя (User/AnonymousUser).
            - `g.token_used`: флаг (True, если аутентификация по токену).

    Raises:
        - Неявно: может вызывать исключения из `User.verify_auth_token()` или SQLAlchemy.

    Examples:
        #### Анонимный доступ (публичный API)
        ```http
        GET /api/public
        Authorization: Basic
        ```

        #### Аутентификация по токену
        ```http
        GET /api/protected
        Authorization: Bearer ваш.токен.тут
        ```

        #### Аутентификация по email/паролю
        ```http
        GET /api/protected
        Authorization: Basic email:пароль
        ```
    """
    if email_or_token == '':
        g.current_user = AnonymousUser()
        return True

    if password == '':
        g.current_user = User.verify_auth_token(email_or_token)
        g.token_used = True
        return g.current_user is not None

    user = db.session.scalar(select(User).where(User.email == email_or_token))
    if not user:
        return abort(401)

    g.current_user = user
    g.token_used = False

    return user.verify_password(password)


@api_v1_bp.route('/token')
def get_token():
    if g.current_user.is_anonymous or g.token_used:
        return abort(401)

    return jsonify({
        'token': g.current_user.generate_auth_token(expiration=216000),
        'expiration': 216000})


@api_v1_bp.route('/posts')
def get_posts():
    page = request.args.get('page', 1, type=int)

    pagination = db.paginate(
        select(Post).order_by(Post.timestamp.desc()),
        page=page,
        per_page=current_app.config["POSTS_PER_PAGE"],
        error_out=False
    )

    prev_page = url_for('api_v1.get_posts', page=page - 1, _external=True) if pagination.has_prev else None
    next_page = url_for('api_v1.get_posts', page=page + 1, _external=True) if pagination.has_next else None

    data = OrderedDict([
        ('posts', [
            post.to_json(include_disabled_comments=g.current_user.can(Permission.ADMINISTER), only_few_comments=True)
            for post in pagination.items
        ]),
        ('page', f'{page} of {pagination.pages}'),
        ('prev_page', prev_page),
        ('next_page', next_page),
        ('posts_count', pagination.total)
    ])

    # Сохраняем порядок атрибутов в ответе
    response = make_response(json.dumps(data, ensure_ascii=False, sort_keys=False), 200)
    response.headers['Content-Type'] = 'application/json'

    return response


@api_v1_bp.route('/posts/<int:id>')
def get_post(id):

    post = db.session.get(Post, id)
    if post is None:
        return abort(404)

    stmt = select(Comment).where(Comment.post_id == id)
    if not g.current_user.can(Permission.ADMINISTER):
        # Исключаем отключенные комменты для неадминов
        stmt = stmt.where(Comment.disabled.isnot(True))

    stmt = stmt.order_by(Comment.created_at.asc())

    page = request.args.get('page', 1, type=int)
    pagination = db.paginate(
        stmt,
        page=page,
        per_page=current_app.config['COMMENTS_PER_PAGE'],
        error_out=False
    )

    post_data = post.to_json()
    # Переопределяем комменты для их пагинации
    post_data['comments'] = [comment.to_json() for comment in pagination.items]
    post_data['pages'] = f'{page} of {pagination.pages}'
    post_data['comments_count'] = pagination.total
    post_data['next_page'] = url_for('api_v1.get_post', id=id, page=page + 1, _external=True) if pagination.has_next else None
    post_data['prev_page'] = url_for('api_v1.get_post', id=id, page=page - 1, _external=True) if pagination.has_prev else None

    return jsonify(post_data), 200


@api_v1_bp.route('/posts/', methods=['POST'])
@permission_required(Permission.WRITE_ARTICLES)
def new_post():
    post = Post.from_json(request.json)
    post.author = g.current_user
    db.session.add(post)
    db.session.commit()

    response = make_response(jsonify(post.to_json()), 201)
    response.headers['Location'] = url_for('api_v1.get_post', id=post.id, _external=True)

    return response


@api_v1_bp.route('/posts/<int:id>', methods=['PUT'])
def edit_post(id):
    post = db.session.get(Post, id)
    if post is None:
        return abort(404)

    if g.current_user != post.author and not g.current_user.can(Permission.ADMINISTER):
        return abort(403)

    post.body = request.json.get('body', post.body)
    db.session.add(post)
    db.session.commit()

    return jsonify(post.to_json()), 200


@api_v1_bp.route('/profile/<username>')
def get_user_profile(username):
    user = db.session.scalar(select(User).where(User.username == username))
    if user is None:
        return abort(404)

    user_data = user.to_json()

    # Исключение самого себя из подписчиков/подписок
    following_list = [u for u in user_data['following_list'] if u != user.username]
    followers_list = [u for u in user_data['followers_list'] if u != user.username]
    user_data['following_list'] = following_list
    user_data['followers_list'] = followers_list

    return jsonify(user_data), 200


@api_v1_bp.route('/profile/<username>/posts')
def get_user_posts(username):

    user = db.session.scalar(select(User).where(User.username == username))
    if not user:
        abort(404)

    page = request.args.get('page', 1, type=int)
    pagination = db.paginate(
        select(Post).where(Post.author_id == user.id).order_by(Post.timestamp.desc()),
        page=page,
        per_page=current_app.config['POSTS_PER_PAGE'],
        error_out=False
    )

    next_page = url_for('api_v1.get_user_posts', username=username, page=page + 1, _external=True) if pagination.has_next else None
    prev_page = url_for('api_v1.get_user_posts', username=username, page=page - 1, _external=True) if pagination.has_prev else None

    return jsonify({
        'posts': [
            post.to_json(include_disabled_comments=g.current_user.can(Permission.ADMINISTER), only_few_comments=True)
            for post in pagination.items
        ],
        'page': f'{page} of {pagination.pages}',
        'prev_page': prev_page,
        'next_page': next_page,
        'posts_count': pagination.total,
    }), 200


@api_v1_bp.route('/profile/<username>/feed')
def get_user_feed(username):
    user = db.session.scalar(select(User).where(User.username == username))
    if not user:
        abort(404)

    page = request.args.get('page', 1, type=int)
    pagination = db.paginate(
        user.feed_posts,
        page=page,
        per_page=current_app.config['POSTS_PER_PAGE'],
        error_out=False
    )

    next_page = url_for('api_v1.get_user_posts', username=username, page=page + 1, _external=True) if pagination.has_next else None
    prev_page = url_for('api_v1.get_user_posts', username=username, page=page - 1, _external=True) if pagination.has_prev else None

    return jsonify({
        'posts': [
            post.to_json(include_disabled_comments=g.current_user.can(Permission.ADMINISTER), only_few_comments=True)
            for post in pagination.items
        ],
        'page': f'{page} of {pagination.pages}',
        'prev_page': prev_page,
        'next_page': next_page,
        'posts_count': pagination.total,
    }), 200


@api_v1_bp.route('/posts/<int:id>/comments')
def get_post_comments(id):

    post = db.session.get(Post, id)
    if post is None:
        return abort(404)

    stmt = select(Comment).where(Comment.post_id == id)
    if not g.current_user.can(Permission.ADMINISTER):
        # Исключаем отключенные комменты для неадминов
        stmt = stmt.where(Comment.disabled.isnot(True))

    stmt = stmt.order_by(Comment.created_at.asc())
    page = request.args.get('page', 1, type=int)
    pagination = db.paginate(
        stmt,
        page=page,
        per_page=current_app.config["COMMENTS_PER_PAGE"],
        error_out=False
    )

    prev_page = url_for('api_v1.get_comments', page=page - 1, _external=True) if pagination.has_prev else None
    next_page = url_for('api_v1.get_comments', page=page + 1, _external=True) if pagination.has_next else None

    return jsonify({
        'comments': [comment.to_json() for comment in pagination.items],
        'next_page': next_page,
        'page': f'{page} of {pagination.pages}',
        'prev_page': prev_page,
        'next_page': next_page,
        'comments_count': pagination.total
    }), 200


@api_v1_bp.route('/posts/<int:id>/comments', methods=['POST'])
@permission_required(Permission.COMMENT)
def new_post_comment(id):

    post = db.session.get(Post, id)
    if post is None:
        abort(404)

    user = g.current_user

    if not request.get_json(silent=True):  # Не вызывает ошибку, вернёт None при проблемах
        current_app.logger.warning('Некорректный формат в запросе для создания коммента.')
        abort(400, description='Поддерживается только формат JSON')

    body = request.json.get('body')

    if not body or len(body.strip()) == 0 or not isinstance(body, str):
        current_app.logger.warning('Попытка создать пустой комментарий.')
        abort(400, description='Нельзя делать пустые комменты')

    if len(body.strip()) > 20:
        current_app.logger.warning('Попытка создать комментарий > 20 символов.')
        abort(400, description='Максимальная длина коммента - 20 символов')

    comment = Comment(body=body, author=user, post_id=post.id)

    try:
        db.session.add(comment)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.warning(f'Ошибка при создании коммента: {e}')
        abort(500, 'Ошибка БД при создании комментария')

    response = make_response(jsonify(comment.to_json()), 201)
    response.headers['Location'] = url_for('api_v1.get_comment', id=comment.id, _external=True)
    response.headers['Content-Type'] = 'application/json'

    return response


@api_v1_bp.route('/comments')
def get_comments():

    stmt = select(Comment)
    if not g.current_user.can(Permission.ADMINISTER):
        # Исключаем отключенные комменты для неадминов
        stmt = stmt.where(Comment.disabled.isnot(True))

    stmt = stmt.order_by(Comment.created_at.desc())

    page = request.args.get('page', 1, type=int)
    pagination = db.paginate(
        stmt,
        page=page,
        per_page=current_app.config["COMMENTS_PER_PAGE"],
        error_out=False
    )

    prev_page = url_for('api_v1.get_comments', page=page - 1, _external=True) if pagination.has_prev else None
    next_page = url_for('api_v1.get_comments', page=page + 1, _external=True) if pagination.has_next else None

    return jsonify({
        'comments': [comment.to_json() for comment in pagination.items],
        'next_page': next_page,
        'page': f'{page} of {pagination.pages}',
        'prev_page': prev_page,
        'next_page': next_page,
        'comments_count': pagination.total
    }), 200


@api_v1_bp.route('/comments/<int:id>')
def get_comment(id):
    comment = db.session.get(Comment, id)
    if comment is None:
        abort(404)

    if comment.disabled and not g.current_user.can(Permission.ADMINISTER):
        abort(403)

    return jsonify(comment.to_json()), 200


@api_v1_bp.route('comments/<int:id>/delete', methods=['DELETE'])
def delete_comment(id):
    comment = db.session.get(Comment, id)
    if not comment:
        abort(404)

    if not g.current_user.can(Permission.ADMINISTER) and g.current_user != comment.author:
        abort(403)  # , "Удалять может либо автор, либо админ")

    db.session.delete(comment)
    db.session.commit()

    return jsonify(
        {"status": "success",
         "message": "Comment deleted"
         }), 200
