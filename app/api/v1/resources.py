from flask import abort, g, jsonify, request, url_for
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


@api_v1_bp.route('/posts/')
def get_posts():
    posts = db.session.scalars(select(Post))
    return jsonify(
        {'posts': [post.to_json() for post in posts]}
    )


@api_v1_bp.route('/posts/<int:id>')
def get_post(id):
    post = db.session.get(Post, id)
    if post is None:
        return abort(404)

    return jsonify(post.to_json()), 200


@api_v1_bp.route('/posts/', methods=['POST'])
@permission_required(Permission.WRITE_ARTICLES)
def new_post():
    post = Post.from_json(request.json)
    post.author = g.current_user
    db.session.add(post)
    db.session.commit()

    return jsonify(post.to_json()), 201, {'Location': url_for('api_v1.get_post', id=post.id, _external=True)}


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
def get_author_profile(username):
    author = db.session.scalar(select(User).where(User.username == username))
    if author is None:
        return abort(404)

    return jsonify(author.to_json())


@api_v1_bp.route('/posts/<int:id>/comments')
def get_post_comments(id):
    comments = db.session.scalars(select(Comment).where(Comment.post_id == id))
    if Comment.post_id is None:
        return abort(404)

    return jsonify(comments), 200


@api_v1_bp.route('/comments')
def get_all_comments():
    comments = db.session.scalars(select(Comment))
    if comments is None:
        return jsonify('Комментов пока нет'), 200

    return jsonify({'posts': [comment.to_json() for comment in comments]}), 200


@api_v1_bp.route('/comments/<int:id>')
def get_comment(id):
    comment = db.session.get(Comment, id)
    if comment is None:
        abort(404)

    return jsonify(comment.to_json()), 200
