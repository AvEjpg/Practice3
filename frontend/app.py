from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file
import requests as http
import io
from functools import wraps
import logging
from datetime import datetime

app = Flask(__name__)
app.secret_key = "service-center-secret-key-123"
app.config['BOOTSTRAP_SERVE_LOCAL'] = True

API_URL = "http://127.0.0.1:8000"

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==========

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "token" not in session or "role" not in session:
            flash("Для доступа к этой странице необходимо войти в систему", "warning")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if "token" not in session or "role" not in session:
                flash("Для доступа к этой странице необходимо войти в систему", "warning")
                return redirect(url_for('login'))
            if session.get("role") not in roles:
                flash("У вас недостаточно прав для доступа к этой странице", "danger")
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def api_headers():
    token = session.get("token")
    return {"Authorization": f"Bearer {token}"} if token else {}

def make_api_request(method, endpoint, **kwargs):
    try:
        url = f"{API_URL}{endpoint}"
        headers = kwargs.get('headers', {})
        
        if "token" in session:
            token = session.get("token")
            headers["Authorization"] = f"Bearer {token}"
            kwargs['headers'] = headers
        
        if method == 'GET':
            response = http.get(url, **kwargs)
        elif method == 'POST':
            response = http.post(url, **kwargs)
        elif method == 'PUT':
            response = http.put(url, **kwargs)
        elif method == 'DELETE':
            response = http.delete(url, **kwargs)
        else:
            return None, "Неверный метод запроса"
        
        if response.status_code in [200, 201]:
            return response, None
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get("detail", "Неизвестная ошибка")
            except:
                error_msg = f"Ошибка {response.status_code}"
            
            if response.status_code == 401:
                session.clear()
                flash("Сессия истекла. Пожалуйста, войдите снова.", "warning")
            
            return response, error_msg
    except Exception as e:
        logger.error(f"API request error: {e}")
        return None, f"Ошибка подключения к серверу: {str(e)}"

# ========== ОСНОВНЫЕ МАРШРУТЫ ==========

@app.route("/")
def index():
    """Главная страница"""
    return render_template("index.html", 
                         role=session.get("role"),
                         title="Главная - Система учета заявок")

@app.route("/login", methods=["GET", "POST"])
def login():
    """Страница входа"""
    if request.method == "POST":
        data = {
            "login": request.form["login"],
            "password": request.form["password"]
        }
        
        response, error = make_api_request('POST', '/auth/login', json=data)
        
        if error is None and response:
            payload = response.json()
            session["token"] = payload.get("access_token")
            session["role"] = payload.get("role", "Оператор")
            session["user_id"] = payload.get("user_id")
            
            flash("Вход выполнен успешно!", "success")
            return redirect(url_for("index"))
        else:
            flash(error or "Неверный логин или пароль", "danger")
    
    return render_template("login.html", title="Вход в систему")

@app.route("/logout")
def logout():
    """Выход из системы"""
    session.clear()
    flash("Вы успешно вышли из системы", "info")
    return redirect(url_for("index"))

# ========== МАРШРУТЫ ДЛЯ ЗАЯВОК ==========

@app.route("/requests")
@login_required
@role_required("Оператор", "Специалист", "Менеджер", "Менеджер по качеству")
def requests_list():
    """Список всех заявок"""
    response, error = make_api_request('GET', '/requests/', headers=api_headers())
    
    if error is None and response:
        requests_data = response.json()
    else:
        requests_data = []
        if error:
            flash(error, "danger")
    
    return render_template("requests_list.html", 
                         requests=requests_data, 
                         role=session.get("role"),
                         title="Список заявок")

@app.route("/requests/search")
@login_required
@role_required("Оператор", "Специалист", "Менеджер", "Менеджер по качеству")
def search_requests():
    """Поиск заявок"""
    params = {k: v for k, v in request.args.items() if v}
    response, error = make_api_request('GET', '/requests/search', params=params, headers=api_headers())
    
    if error is None and response:
        requests_data = response.json()
    else:
        requests_data = []
    
    return render_template("requests_list.html", 
                         requests=requests_data, 
                         role=session.get("role"),
                         search_params=params,
                         title="Результаты поиска")

@app.route("/requests/new", methods=["GET", "POST"])
@login_required
@role_required("Оператор", "Специалист", "Менеджер")
def new_request():
    """Создание новой заявки"""
    if request.method == "POST":
        data = {
            "start_date": request.form["start_date"],
            "tech_type": request.form["tech_type"],
            "tech_model": request.form["tech_model"],
            "problem_description": request.form["problem_description"],
            "request_status": "Новая заявка",
            "client_id": int(request.form["client_id"]),
        }
        
        response, error = make_api_request('POST', '/requests/', json=data, headers=api_headers())
        
        if error is None and response:
            flash("Заявка успешно создана!", "success")
            return redirect(url_for("requests_list"))
        else:
            flash(error or "Ошибка создания заявки", "danger")
    
    today = datetime.now().strftime("%Y-%m-%d")
    return render_template("request_create.html", 
                         role=session.get("role"),
                         today=today,
                         title="Создание новой заявки")

@app.route("/requests/<int:request_id>")
@login_required
@role_required("Оператор", "Специалист", "Менеджер", "Менеджер по качеству")
def request_detail(request_id):
    """Детали заявки"""
    response, error = make_api_request('GET', f'/requests/{request_id}', headers=api_headers())
    
    if error is None and response:
        request_data = response.json()
        
        # Получаем комментарии к этой заявке
        comments_response, comments_error = make_api_request('GET', '/comments/', headers=api_headers())
        if comments_error is None and comments_response:
            all_comments = comments_response.json()
            request_comments = [c for c in all_comments if c.get('request_id') == request_id]
        else:
            request_comments = []
        
        return render_template("request_detail.html", 
                             request=request_data, 
                             comments=request_comments,
                             role=session.get("role"),
                             title=f"Заявка #{request_id}")
    else:
        flash(error or "Заявка не найдена", "danger")
        return redirect(url_for("requests_list"))

@app.route("/requests/<int:request_id>/edit", methods=["POST"])
@login_required
@role_required("Оператор", "Специалист", "Менеджер", "Менеджер по качеству")
def edit_request(request_id):
    """Редактирование заявки"""
    update_data = {}
    if request.form.get("request_status"):
        update_data["request_status"] = request.form["request_status"]
    if request.form.get("completion_date"):
        update_data["completion_date"] = request.form["completion_date"]
    if request.form.get("repair_parts"):
        update_data["repair_parts"] = request.form["repair_parts"]
    if request.form.get("master_id"):
        update_data["master_id"] = int(request.form["master_id"])
    
    if update_data:
        response, error = make_api_request('PUT', f'/requests/{request_id}', json=update_data, headers=api_headers())
        
        if error is None and response:
            flash("Заявка успешно обновлена!", "success")
        else:
            flash(error or "Ошибка обновления заявки", "danger")
    
    return redirect(url_for("request_detail", request_id=request_id))

# ========== МАРШРУТЫ ДЛЯ ЗАКАЗЧИКОВ ==========

@app.route("/my-requests")
@login_required
def my_requests():
    """Мои заявки (для заказчиков)"""
    if session.get("role") != "Заказчик":
        flash("Эта страница только для заказчиков", "warning")
        return redirect(url_for("index"))
    
    response, error = make_api_request('GET', '/client/my-requests', headers=api_headers())
    
    if error is None and response:
        requests_data = response.json()
    else:
        requests_data = []
    
    return render_template("client_requests.html", 
                         requests=requests_data, 
                         role=session.get("role"),
                         title="Мои заявки")

@app.route("/my-requests/new", methods=["GET", "POST"])
@login_required
def new_my_request():
    """Создание заявки заказчиком"""
    if session.get("role") != "Заказчик":
        flash("Эта страница только для заказчиков", "warning")
        return redirect(url_for("index"))
    
    if request.method == "POST":
        data = {
            "start_date": request.form["start_date"],
            "tech_type": request.form["tech_type"],
            "tech_model": request.form["tech_model"],
            "problem_description": request.form["problem_description"],
        }
        
        response, error = make_api_request('POST', '/client/my-requests', json=data, headers=api_headers())
        
        if error is None and response:
            flash("Заявка успешно создана!", "success")
            return redirect(url_for("my_requests"))
        else:
            flash(error or "Ошибка создания заявки", "danger")
    
    today = datetime.now().strftime("%Y-%m-%d")
    return render_template("client_request_create.html", 
                         role=session.get("role"),
                         today=today,
                         title="Создание новой заявки")

@app.route("/my-requests/<int:request_id>")
@login_required
def my_request_detail(request_id):
    """Детали заявки для клиента"""
    if session.get("role") != "Заказчик":
        flash("Эта страница только для заказчиков", "warning")
        return redirect(url_for("index"))
    
    response, error = make_api_request('GET', f'/client/my-requests/{request_id}', headers=api_headers())
    
    if error is None and response:
        request_data = response.json()
        
        # Получаем комментарии для этой заявки
        comments_response, comments_error = make_api_request('GET', '/comments/', headers=api_headers())
        if comments_error is None and comments_response:
            all_comments = comments_response.json()
            request_comments = [c for c in all_comments if c.get('request_id') == request_id]
        else:
            request_comments = []
        
        return render_template("request_detail.html", 
                             request=request_data, 
                             comments=request_comments,
                             role=session.get("role"),
                             title=f"Моя заявка #{request_id}")
    else:
        flash(error or "Заявка не найдена", "danger")
        return redirect(url_for("my_requests"))

# ========== МАРШРУТЫ ДЛЯ МЕНЕДЖЕРА ПО КАЧЕСТВУ ==========

@app.route("/requests/<int:request_id>/assign", methods=["POST"])
@login_required
@role_required("Менеджер", "Менеджер по качеству")
def assign_master(request_id):
    """Назначение мастера"""
    data = {"master_id": int(request.form["master_id"])}
    
    response, error = make_api_request('POST', f'/requests/{request_id}/assign', json=data, headers=api_headers())
    
    if error is None and response:
        flash("Мастер успешно назначен!", "success")
    else:
        flash(error or "Ошибка назначения мастера", "danger")
    
    return redirect(url_for("request_detail", request_id=request_id))

@app.route("/requests/<int:request_id>/extend", methods=["POST"])
@login_required
@role_required("Менеджер", "Менеджер по качеству")
def extend_deadline(request_id):
    """Продление срока"""
    data = {
        "new_deadline_date": request.form["new_deadline_date"],
        "reason": request.form.get("reason", "")
    }
    
    response, error = make_api_request('POST', f'/requests/{request_id}/extend', json=data, headers=api_headers())
    
    if error is None and response:
        flash("Срок выполнения успешно продлён!", "success")
    else:
        flash(error or "Ошибка продления срока", "danger")
    
    return redirect(url_for("request_detail", request_id=request_id))

# ========== МАРШРУТЫ ДЛЯ УПРАВЛЕНИЯ ПОЛЬЗОВАТЕЛЯМИ ==========

@app.route("/users")
@login_required
@role_required("Менеджер", "Менеджер по качеству")
def users_list():
    """Управление пользователями"""
    response, error = make_api_request('GET', '/users/', headers=api_headers())
    
    if error is None and response:
        users = response.json()
    else:
        users = []
        flash(error or "Ошибка загрузки пользователей", "danger")
    
    return render_template("users_list.html", 
                         users=users, 
                         role=session.get("role"),
                         title="Управление пользователями")

@app.route("/users/create", methods=["GET", "POST"])
@login_required
@role_required("Менеджер")
def create_user():
    """Создание нового пользователя"""
    if request.method == "POST":
        user_data = {
            "fio": request.form["fio"],
            "phone": request.form["phone"],
            "login": request.form["login"],
            "password": request.form["password"],
            "user_type": request.form["user_type"],
        }
        
        response, error = make_api_request('POST', '/users/', json=user_data, headers=api_headers())
        
        if error is None and response:
            flash("Пользователь успешно создан!", "success")
            return redirect(url_for("users_list"))
        else:
            flash(error or "Ошибка создания пользователя", "danger")
    
    return render_template("user_create.html", 
                         role=session.get("role"),
                         title="Создание пользователя")

@app.route("/users/delete/<int:user_id>", methods=["POST"])
@login_required
@role_required("Менеджер")
def delete_user(user_id):
    """Удаление пользователя"""
    if request.form.get("confirm") != "yes":
        flash("Удаление отменено", "warning")
        return redirect(url_for("users_list"))
    
    response, error = make_api_request('DELETE', f'/users/{user_id}', headers=api_headers())
    
    if error is None and response:
        flash("Пользователь успешно удалён", "success")
    else:
        flash(error or "Ошибка удаления пользователя", "danger")
    
    return redirect(url_for("users_list"))

@app.route("/users/edit/<int:user_id>", methods=["GET", "POST"])
@login_required
@role_required("Менеджер", "Менеджер по качеству")
def edit_user(user_id):
    """Редактирование пользователя"""
    # Для GET запроса - показываем форму
    if request.method == "GET":
        # Получаем данные пользователя
        response, error = make_api_request('GET', f'/users/{user_id}', headers=api_headers())
        
        if error is None and response:
            user_data = response.json()
            return render_template("user_edit.html", 
                                 user=user_data, 
                                 role=session.get("role"),
                                 title="Редактирование пользователя")
        else:
            flash(error or "Пользователь не найден", "danger")
            return redirect(url_for("users_list"))
    
    # Для POST запроса - обновляем пользователя
    if request.method == "POST":
        update_data = {}
        if request.form.get("fio"):
            update_data["fio"] = request.form["fio"]
        if request.form.get("phone"):
            update_data["phone"] = request.form["phone"]
        if request.form.get("password"):
            update_data["password"] = request.form["password"]
        if request.form.get("user_type"):
            update_data["user_type"] = request.form["user_type"]
        
        if update_data:
            response, error = make_api_request('PUT', f'/users/{user_id}', 
                                             json=update_data, headers=api_headers())
            
            if error is None and response:
                flash("Пользователь успешно обновлён!", "success")
                return redirect(url_for("users_list"))
            else:
                flash(error or "Ошибка обновления пользователя", "danger")
    
    return redirect(url_for("users_list"))

# ========== МАРШРУТЫ ДЛЯ КОММЕНТАРИЕВ ==========

@app.route("/comments")
@login_required
@role_required("Оператор", "Специалист", "Менеджер", "Менеджер по качеству")
def comments_list():
    """Список комментариев"""
    response, error = make_api_request('GET', '/comments/', headers=api_headers())
    
    if error is None and response:
        comments = response.json()
    else:
        comments = []
        flash(error or "Ошибка загрузки комментариев", "danger")
    
    return render_template("comments_list.html", 
                         comments=comments, 
                         role=session.get("role"),
                         title="Комментарии")

@app.route("/comments/new", methods=["GET", "POST"])
@login_required
@role_required("Специалист", "Менеджер", "Менеджер по качеству")
def new_comment():
    """Создание комментария"""
    if request.method == "POST":
        data = {
            "message": request.form["message"],
            "master_id": int(request.form["master_id"]),
            "request_id": int(request.form["request_id"]),
        }
        
        response, error = make_api_request('POST', '/comments/', json=data, headers=api_headers())
        
        if error is None and response:
            flash("Комментарий успешно добавлен!", "success")
            return redirect(url_for("comments_list"))
        else:
            flash(error or "Ошибка добавления комментария", "danger")
    
    return render_template("comment_create.html", 
                         role=session.get("role"),
                         title="Новый комментарий")

# ========== QR КОД ОБРАТНОЙ СВЯЗИ ==========

@app.route("/qr/feedback")
@login_required
def qr_feedback():
    """QR код для обратной связи"""
    try:
        response = http.get(f"{API_URL}/qr/feedback", headers=api_headers())
        if response.status_code == 200:
            return send_file(io.BytesIO(response.content), mimetype="image/png")
    except Exception as e:
        logger.error(f"QR generation error: {e}")
    
    # Если не удалось получить QR от API, генерируем локально
    try:
        import qrcode
        FEEDBACK_URL = "https://docs.google.com/forms/d/e/1FAIpQLSdhZcExx6LSIXxk0ub55mSu-WIh23WYdGG9HY5EZhLDo7P8eA/viewform?usp=sf_link"
        img = qrcode.make(FEEDBACK_URL)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        return send_file(buf, mimetype="image/png")
    except ImportError:
        flash("Для генерации QR-кода установите библиотеку qrcode", "warning")
        return redirect(url_for("index"))

# ========== СТАТИСТИКА ==========

@app.route("/statistics")
@login_required
def statistics():
    """Статистика работы"""
    stats_data = {}
    
    # Получаем статистику из API
    endpoints = ['count', 'avg-time', 'by-tech', 'by-problem-type']
    
    for endpoint in endpoints:
        response, error = make_api_request('GET', f'/requests/stats/{endpoint}', headers=api_headers())
        if error is None and response:
            stats_data[endpoint] = response.json()
        else:
            stats_data[endpoint] = None
    
    return render_template("statistics.html",
                         stats=stats_data,
                         role=session.get("role"),
                         title="Статистика")

# ========== ОШИБКИ ==========

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html', title="Страница не найдена"), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html', title="Внутренняя ошибка сервера"), 500

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)