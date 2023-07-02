from flask import Flask, render_template, redirect, url_for, request, abort, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    login_required,
    logout_user,
    current_user,
)
from functools import wraps
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer, SignatureExpired
from datetime import datetime, timedelta, date
from flask import jsonify

import datetime

from datetime import datetime


app = Flask(__name__)
app.config["SECRET_KEY"] = "Thisisasecret!"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///db.sqlite"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
"""""
app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'WikingGym@gmail.com'
app.config['MAIL_PASSWORD'] = 'vecdqtoerqohryvu'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True

mail = Mail(app)

s = URLSafeTimedSerializer(app.config['SECRET_KEY'])
""" ""

login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    surname = db.Column(db.String(100))
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    is_admin = db.Column(db.Boolean, default=False)
    classroom_id = db.Column(db.Integer, db.ForeignKey("classroom.id"), nullable=True)

    """""
    confirmed = db.Column(db.Boolean, nullable=False, default=False)
    """ ""


class Classroom(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    users = db.relationship("User", backref="classroom", lazy=True)
    lessons = db.relationship("Lesson", backref="classroom", lazy=True)


class Lesson(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    day_of_week = db.Column(db.String(10), nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    classroom_id = db.Column(db.Integer, db.ForeignKey("classroom.id"), nullable=False)


class Grade(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    value = db.Column(db.Integer, nullable=False)
    lesson_id = db.Column(db.Integer, db.ForeignKey("lesson.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    lesson = db.relationship("Lesson", backref="grades")


class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    lesson_id = db.Column(db.Integer, db.ForeignKey("lesson.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    is_present = db.Column(db.Boolean, default=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    lesson = db.relationship("Lesson", backref=db.backref("attendances", lazy=True))


"""""
@app.route('/confirm_email/<token>')
def confirm_email(token):
    try:
        email = s.loads(token, max_age=3600)
    except SignatureExpired:
        return '<h1>The token is expired!</h1>'

    user = User.query.filter_by(email=email).first()
    user.confirmed = True
    db.session.add(user)
    db.session.commit()

    return redirect(url_for('login'))
""" ""


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            return abort(403)
        return f(*args, **kwargs)

    return decorated_function


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user = User.query.filter_by(username=username).first()

        if not user or not check_password_hash(user.password, password):
            error_message = "Błędny login lub hasło."
            return render_template("login.html", error_message=error_message)
        """""
        if not user.confirmed:
            return '<h1>Confirm your email first!</h1>'
            """ ""

        login_user(user)
        return redirect(url_for("dashboard"))

    return render_template("login.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form.get("name")
        surname = request.form.get("surname")
        username = request.form.get("username")
        password = request.form.get("password")
        email = request.form.get("email")

        user = User.query.filter_by(username=username).first()
        if user:
            return "Username already exists"

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return "Email already exists"

        new_user = User(
            name=name,
            surname=surname,
            username=username,
            password=generate_password_hash(password, method="sha256"),
            email=email,
        )

        db.session.add(new_user)
        db.session.commit()
        """""
        token = s.dumps(new_user.email, salt='email-confirm')
        msg = Message('Confirm Email', sender='WikingGym@gmail.com', recipients=[new_user.email])
        link = url_for('confirm_email', token=token, _external=True)
        msg.body = 'Your link is {}'.format(link)
        mail.send(msg)
        """ ""
        flash(
            "Rejestracja powiodła się! Sprawdź swoją skrzynkę pocztową, aby potwierdzić rejestrację."
        )
        return render_template("success_sign_up.html", name=name, link=url_for("login"))

    return render_template("signup.html")


@app.route("/dashboard")
@login_required
def dashboard():
    if current_user.is_admin:
        return redirect(url_for("admin_dashboard"))
    return render_template("dashboard.html")


@app.route("/admin")
@login_required
@admin_required
def admin_dashboard():
    all_users = User.query.all()
    return render_template("admin.html", users=all_users)


@app.route("/admin/user/delete/<int:user_id>", methods=["POST"])
@login_required
@admin_required
def admin_delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash("Użytkownik został usunięty.")
    return redirect(url_for("admin_dashboard"))


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("home"))


@app.route("/classrooms", methods=["GET", "POST"])
@login_required
@admin_required
def manage_classrooms():
    if request.method == "POST":
        classroom_name = request.form.get("classroom_name")

        new_classroom = Classroom(name=classroom_name)
        db.session.add(new_classroom)
        db.session.commit()

    all_classrooms = Classroom.query.all()
    return render_template("classrooms.html", classrooms=all_classrooms)


@app.route("/classrooms/<int:classroom_id>/edit", methods=["GET", "POST"])
@login_required
@admin_required
def edit_classroom(classroom_id):
    classroom = Classroom.query.get_or_404(classroom_id)
    days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    lessons = {day: [] for day in days_of_week}

    users = User.query.filter_by(classroom_id=classroom_id).all()

    for lesson in (
        Lesson.query.filter_by(classroom_id=classroom_id)
        .order_by(Lesson.start_time)
        .all()
    ):
        lessons[lesson.day_of_week].append(lesson)


    lesson_id = request.args.get("lesson_id")
    lesson = Lesson.query.get_or_404(lesson_id) if lesson_id else None

    if request.method == "POST":
        classroom.name = request.form.get("classroom_name")

        db.session.commit()
        return redirect(url_for("manage_classrooms"))

    return render_template(
        "edit_classroom.html",
        classroom=classroom,
        lessons=lessons,
        users=users,
        lesson=lesson,
    )


@app.route("/classrooms/<int:classroom_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_classroom(classroom_id):
    classroom = Classroom.query.get_or_404(classroom_id)
    for lesson in classroom.lessons:
        db.session.delete(lesson)
    db.session.delete(classroom)
    db.session.commit()

    return redirect(url_for("manage_classrooms"))


@app.route("/classrooms/<int:classroom_id>/add_user", methods=["POST"])
@login_required
@admin_required
def add_user_to_classroom(classroom_id):
    username = request.form.get("username")
    user = User.query.filter_by(username=username).first()
    if not user:
        return "No user found with this username", 400

    for classroom in Classroom.query.all():
        if user in classroom.users:
            return "This student is already in a classroom", 400

    classroom = Classroom.query.get_or_404(classroom_id)

    classroom.users.append(user)
    db.session.commit()

    return redirect(url_for("edit_classroom", classroom_id=classroom_id))


@app.route("/classrooms/<int:classroom_id>/remove_user", methods=["POST"])
@login_required
@admin_required
def remove_user_from_classroom(classroom_id):
    username = request.form.get("username")
    user = User.query.filter_by(username=username).first()
    if not user:
        return "No user found with this username", 400

    classroom = Classroom.query.get_or_404(classroom_id)

    if user not in classroom.users:
        return "This student is not in the classroom", 400

    classroom.users.remove(user)
    db.session.commit()

    return redirect(url_for("edit_classroom", classroom_id=classroom_id))


@app.route("/api/usernames", methods=["GET"])
def get_usernames():
    users = User.query.all()
    usernames = [user.username for user in users]
    return jsonify(usernames)


@app.route("/classrooms/<int:classroom_id>/add_lesson", methods=["POST"])
@login_required
@admin_required
def add_lesson_to_classroom(classroom_id):
    lesson_name = request.form.get("lesson_name")
    day_of_week = request.form.get("day_of_week")
    start_time = datetime.strptime(request.form.get("start_time"), "%H:%M").time()
    end_time = datetime.strptime(request.form.get("end_time"), "%H:%M").time()

    new_lesson = Lesson(
        name=lesson_name,
        day_of_week=day_of_week,
        start_time=start_time,
        end_time=end_time,
        classroom_id=classroom_id,
    )

    db.session.add(new_lesson)
    db.session.commit()

    print("Dodano nową lekcję:", new_lesson.name)
    print("ID klasy dla nowej lekcji:", new_lesson.classroom_id)
    print("Lekcje w klasie po dodaniu nowej lekcji:")
    classroom = Classroom.query.get(classroom_id)
    for lesson in classroom.lessons:
        print(lesson.name)

    return redirect(url_for("edit_classroom", classroom_id=classroom_id))


@app.route(
    "/classrooms/<int:classroom_id>/remove_lesson/<int:lesson_id>", methods=["POST"]
)
@login_required
@admin_required
def remove_lesson_from_classroom(classroom_id, lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)

    if lesson.classroom_id != classroom_id:
        return "This lesson is not in the classroom", 400

    db.session.delete(lesson)
    db.session.commit()

    return redirect(url_for("edit_classroom", classroom_id=classroom_id))


@app.route(
    "/classrooms/<int:classroom_id>/lessons/<int:lesson_id>/add_grade",
    methods=["GET", "POST"],
)
@login_required
@admin_required
def add_grade(classroom_id, lesson_id):
    classroom = Classroom.query.get_or_404(classroom_id)
    lesson = Lesson.query.get_or_404(lesson_id)
    if request.method == "POST":
        user_id = request.form.get("user_id")
        grade_value = request.form.get("grade_value")

        user = User.query.get_or_404(user_id)

        if user.classroom_id != classroom_id:
            return "This student is not in the classroom", 400

        new_grade = Grade(value=grade_value, lesson_id=lesson_id, user_id=user_id)

        db.session.add(new_grade)
        db.session.commit()

        return redirect(
            url_for("add_grade", classroom_id=classroom_id, lesson_id=lesson_id)
        )
    else:
        grades = Grade.query.filter_by(lesson_id=lesson_id).all()
        return render_template(
            "add_grade.html", classroom=classroom, lesson=lesson, grades=grades
        )


@app.route("/classrooms/<int:classroom_id>/select_lesson", methods=["GET", "POST"])
@login_required
@admin_required
def select_lesson(classroom_id):
    classroom = Classroom.query.get_or_404(classroom_id)

    if request.method == "POST":
        lesson_id = request.form.get("lesson_id")
        return redirect(
            url_for("add_grade", classroom_id=classroom_id, lesson_id=lesson_id)
        )
    else:
        unique_lessons = set()
        lessons_options = []

        for lesson in classroom.lessons:
            print(lesson.name)
            if lesson.name not in unique_lessons:
                unique_lessons.add(lesson.name)
                lessons_options.append((lesson.id, lesson.name))

        return render_template(
            "select_lesson.html", classroom=classroom, lessons_options=lessons_options
        )


@app.route(
    "/classrooms/<int:classroom_id>/lessons/<int:lesson_id>/grades/<int:grade_id>/delete",
    methods=["POST"],
)
@login_required
@admin_required
def delete_grade(classroom_id, lesson_id, grade_id):
    grade = Grade.query.get_or_404(grade_id)
    if grade.lesson_id != lesson_id or grade.user.classroom_id != classroom_id:
        abort(404)
    db.session.delete(grade)
    db.session.commit()
    return redirect(
        url_for("add_grade", classroom_id=classroom_id, lesson_id=lesson_id)
    )


@app.route(
    "/classrooms/<int:classroom_id>/lessons/<int:lesson_id>/attendance",
    methods=["GET", "POST"],
)
@login_required
@admin_required
def attendance(classroom_id, lesson_id):
    classroom = Classroom.query.get_or_404(classroom_id)
    lesson = Lesson.query.get_or_404(lesson_id)

    if request.method == "POST":
        lesson_id = request.form.get("lesson_id")

        for user in classroom.users:
            attendance = Attendance.query.filter_by(
                lesson_id=lesson_id, user_id=user.id
            ).first()

            if attendance:
                attendance.is_present = bool(request.form.get("attendance_value"))
            else:
                attendance = Attendance(
                    is_present=bool(request.form.get("attendance_value")),
                    lesson_id=lesson_id,
                    user_id=user.id,
                )
                db.session.add(attendance)

        db.session.commit()
        return redirect(
            url_for("attendance", classroom_id=classroom_id, lesson_id=lesson_id)
        )

    else:
        attendances = Attendance.query.filter_by(lesson_id=lesson_id).all()
        return render_template(
            "attendance.html",
            classroom=classroom,
            lesson=lesson,
            attendances=attendances,
        )


@app.route(
    "/classrooms/<int:classroom_id>/select_lesson_attendance", methods=["GET", "POST"]
)
@login_required
@admin_required
def select_lesson_attendance(classroom_id):
    classroom = Classroom.query.get_or_404(classroom_id)

    if request.method == "POST":
        lesson_id = request.form.get("lesson_id")
        return redirect(
            url_for("attendance", classroom_id=classroom_id, lesson_id=lesson_id)
        )
    else:
        unique_lessons = set()
        lessons_options = []

        for lesson in classroom.lessons:
            print(lesson.name)
            if lesson.name not in unique_lessons:
                unique_lessons.add(lesson.name)
                lessons_options.append((lesson.id, lesson.name))

        return render_template(
            "select_lesson_attendance.html",
            classroom=classroom,
            lessons_options=lessons_options,
        )


@app.route("/my_attendance")
@login_required
def my_attendance():
    user_id = current_user.id
    attendances = Attendance.query.filter_by(user_id=user_id).all()
    return render_template("my_attendance.html", attendances=attendances)


@app.route("/attendance/update", methods=["POST"])
@login_required
def update_attendance():
    attendance_id = request.form.get("attendance_id")
    attendance = Attendance.query.get_or_404(attendance_id)

    attendance.is_present = not attendance.is_present
    db.session.commit()

    return redirect(url_for("my_attendance"))


@app.route("/my_grades")
@login_required
def my_grades():
    user_id = current_user.id
    grades = Grade.query.filter_by(user_id=user_id).all()
    subjects = set()

    for grade in grades:
        subjects.add(grade.lesson.name)

    grades_dict = {}
    for subject in subjects:
        grades_dict[subject] = []

    for grade in grades:
        grades_dict[grade.lesson.name].append(
            float(grade.value)
        )  

    averages_dict = {}
    for subject, grades_list in grades_dict.items():
        averages_dict[subject] = sum(grades_list) / len(grades_list)

    return render_template("my_grades.html", grades=grades_dict, averages=averages_dict)


@app.route("/my_lessons")
@login_required 
def my_lessons():
    user_classroom = current_user.classroom  

    if user_classroom:
        day_lessons = {}
        lessons = (
            user_classroom.lessons
        )  

 
        for lesson in lessons:
            day = lesson.day_of_week
            if day in day_lessons:
                day_lessons[day].append(lesson)
            else:
                day_lessons[day] = [lesson]
    else:
        day_lessons = {}

    return render_template("my_lessons.html", day_lessons=day_lessons)


if __name__ == "__main__":
    with app.app_context():
        db.create_all()

        admin_user = User.query.filter_by(username="admin").first()
        if not admin_user:
            admin = User(
                name="Admin",
                username="admin",
                password=generate_password_hash("admin", method="sha256"),
                email="admin@example.com",
                is_admin=True,
            )
            db.session.add(admin)
            db.session.commit()

    app.run(debug=True)
