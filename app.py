from flask import (Flask, abort, flash, g, redirect, render_template, request,
                   send_from_directory, session, url_for)
from flask_bcrypt import Bcrypt
from functools import wraps
import json
import re
import sqlite3

DATABASE = "assignment3.db"

app = Flask(__name__)
app.jinja_env.trim_blocks = True
app.jinja_env.lstrip_blocks = True
app.secret_key = "6ffeefbdcbf9f2515ece205d6d2b5675"

bcrypt = Bcrypt(app)

def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.execute(
            """INSERT INTO Users
            VALUES('student1', 'student', 'Student One', ?)""",
            [bcrypt.generate_password_hash("student1")]
        )
        db.execute(
            """INSERT INTO Users
            VALUES('student2', 'student', 'Student Two', ?)""",
            [bcrypt.generate_password_hash("student2")]
        )
        db.execute(
            """INSERT INTO Users
            VALUES('instructor1', 'instructor', 'Instructor One', ?)""",
            [bcrypt.generate_password_hash("instructor1")]
        )
        db.execute(
            """INSERT INTO Users
            VALUES('instructor2', 'instructor', 'Instructor Two', ?)""",
            [bcrypt.generate_password_hash("instructor2")]
        )
        db.execute("INSERT INTO Assessments VALUES(1, 'ass', 'Assignment 1')")
        db.execute("INSERT INTO Assessments VALUES(2, 'lab', 'Lab 1')")
        db.execute("INSERT INTO Marks VALUES('student1', 1, 79)")
        db.execute("INSERT INTO Marks VALUES('student2', 1, 69)")
        db.execute("INSERT INTO Marks VALUES('student1', 2, 100)")
        db.execute(
            """INSERT INTO FeedbackQuestions VALUES(
                1,
                'What do you like about the instructor teaching?'
            )"""
        )
        db.execute(
            """INSERT INTO FeedbackQuestions VALUES(
                2,
                'What do you recommend the instructor do to improve their teaching?'
            )"""
        )
        db.execute(
            """INSERT INTO FeedbackQuestions VALUES(
                3,
                'What do you like about the labs?'
            )"""
        )
        db.execute(
            """INSERT INTO FeedbackQuestions VALUES(
                4,
                'What do you recommend the lab instructors do to improve their lab teaching?'
            )"""
        )
        db.commit()

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

def need_login(func):
    @wraps(func)
    def inner(*args, **kwargs):
        if "username" not in session:
            abort(403)
        return func(*args, **kwargs)
    return inner

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        if "username" in session:
            return redirect(url_for("dashboard"))
        return render_template("login.html")

    username = request.form.get("username")
    password = request.form.get("password")

    db = get_db()
    db.row_factory = sqlite3.Row

    row = query_db("SELECT * FROM Users WHERE username = ?",
                   [username], one=True)
    if (row is None
        or not bcrypt.check_password_hash(row["password"], password)):
        flash("Invalid username or password.")
        db.close()
        return redirect(url_for("login"))

    db.close()
    session["username"] = username
    session["acc_type"] = row["type"]
    session["name"] = row["name"]
    return redirect(url_for("dashboard"))

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "GET":
        if "username" in session:
            return redirect(url_for("dashboard"))
        return render_template("signup.html")

    username, acc_type, name, password = tuple(
        request.form.get(field) for field
            in ["username", "acc-type", "name", "password"]
    )

    if acc_type not in ["student", "instructor"]:
        flash("Invalid user type.")
        return redirect(url_for("signup"))

    # Verify username format
    if re.fullmatch(r"[0-9a-zA-Z]+", username) is None:
        flash("Invalid username format.")
        return redirect(url_for("signup"))

    db = get_db()
    db.row_factory = sqlite3.Row

    # Check if user already exists
    row = query_db("SELECT username FROM Users WHERE username = ?",
                   [username], one=True)
    if row is not None:
        flash("That username is already taken.")
        db.close()
        return redirect(url_for("signup"))

    db.execute("INSERT INTO Users VALUES (?, ?, ?, ?)", [
        username,
        acc_type,
        name,
        bcrypt.generate_password_hash(password)
    ])
    db.commit()
    db.close()
    return redirect(url_for("login"))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

@app.route("/dashboard", methods=["GET", "POST"])
@need_login
def dashboard():
    db = get_db()
    db.row_factory = sqlite3.Row
    if session["acc_type"] == "student":
        if request.method == "POST":
            instructor = request.form.get("instructor")
            q_id = request.form.get("question")
            try:
                q_id = int(q_id)
            except:
                db.close()
                abort(400)

            if query_db(
                """SELECT * FROM Users
                WHERE username = ? AND type = 'instructor'""",
                [instructor],
                one=True
            ) is None or query_db(
                "SELECT * FROM FeedbackQuestions WHERE id = ?",
                [q_id],
                one=True
            ) is None:
                db.close()
                abort(400)

            db.execute(
                """INSERT INTO Feedback(instructor, q_id, response)
                VALUES(?, ?, ?)""",
                [request.form.get(field) for field in
                ["instructor", "question", "response"]]
            )
            db.commit()
            db.close()
            session["redirecting"] = None
            return redirect(url_for("feedback_confirmed"))

        ass_marks = query_db(
            """SELECT id, A.name, mark
            FROM Assessments AS A CROSS JOIN Users AS U LEFT JOIN Marks AS M
            ON U.username = M.username AND id = ass_id
            WHERE U.username = ? AND A.type = 'ass'""",
            [session["username"]]
        )
        lab_marks = query_db(
            """SELECT id, A.name, mark
            FROM Assessments AS A CROSS JOIN Users AS U LEFT JOIN Marks AS M
            ON U.username = M.username AND id = ass_id
            WHERE U.username = ? AND A.type = 'lab'""",
            [session["username"]]
        )
        test_marks = query_db(
            """SELECT id, A.name, mark
            FROM Assessments AS A CROSS JOIN Users AS U LEFT JOIN Marks AS M
            ON U.username = M.username AND id = ass_id
            WHERE U.username = ? AND A.type = 'test'""",
            [session["username"]]
        )
        remarks = {row["id"] : (row["why"], row["status"]) for row in query_db(
            """SELECT id, why, status
            FROM Assessments AS A CROSS JOIN Users AS U LEFT JOIN Remarks AS R
            ON U.username = R.username AND id = ass_id
            WHERE U.username = ?""",
            [session["username"]]
        )}

        instructors = query_db("SELECT * FROM Users WHERE type = 'instructor'")
        questions = query_db("SELECT * FROM FeedbackQuestions")
        db.close()
        return render_template("dashboard-student.html", ass_marks=ass_marks,
                               lab_marks=lab_marks, test_marks=test_marks,
                               remarks=remarks, instructors=instructors,
                               questions=questions)
    asses = query_db("SELECT * FROM Assessments")
    feedback = query_db(
        """SELECT question, response
        FROM Feedback JOIN FeedbackQuestions AS Q ON q_id = Q.id
        WHERE instructor = ?""",
        [session["username"]]
    )
    remarks = query_db(
        """SELECT username, U.name, ass_id, A.name AS ass, why
        FROM Remarks JOIN Assessments AS A ON ass_id = id
        JOIN Users AS U USING(username)
        WHERE status = 'open'"""
    )
    db.close()
    return render_template("dashboard-instructor.html", asses=asses, feedback=feedback, remarks=remarks)

@app.route("/dashboard/feedback-confirmed")
@need_login
def feedback_confirmed():
    if "redirecting" not in session:
        return redirect(url_for("dashboard"))
    del session["redirecting"]
    return render_template("feedback-confirmed.html")

@app.route("/dashboard/remark", methods=["GET", "POST"])
@need_login
def remark():
    if session["acc_type"] != "student":
        abort(403)
    if request.method == "GET":
        ass_id = request.args.get("id")
    else:
        ass_id = request.form.get("id")
    try:
        ass_id = int(ass_id)
    except:
        abort(400)

    db = get_db()
    db.row_factory = sqlite3.Row
    ass = query_db("SELECT * FROM Assessments WHERE id = ?", [ass_id],
                    one=True)
    if ass is None:
        db.close()
        abort(400)

    allowed = query_db(
        """SELECT * FROM Remarks
        WHERE username = ? AND ass_id = ?""",
        [session["username"], ass_id],
        one=True
    ) is None and query_db(
        """SELECT * FROM Marks
        WHERE username = ? AND ass_id = ?""",
        [session["username"], ass_id],
        one=True
    ) is not None
    if request.method == "GET":
        db.close()
        return render_template("remark.html", ass=ass, allowed=allowed)

    if not allowed:
        db.close()
        abort(400)

    db.execute("INSERT INTO Remarks VALUES (?, ?, ?)", [
        session["username"],
        ass_id,
        request.form.get("why")
    ])
    db.commit()
    db.close()
    session["redirecting"] = None
    return redirect(url_for("remark_confirmed"))

@app.route("/dashboard/remark/confirmed")
@need_login
def remark_confirmed():
    if "redirecting" not in session:
        return redirect(url_for("dashboard"))
    del session["redirecting"]
    return render_template("remark-confirmed.html")

@app.route("/dashboard/remark/update-status", methods=["GET", "POST"])
@need_login
def remark_status():
    if session["acc_type"] != "instructor":
        abort(403)
    if request.method == "GET":
        return redirect(url_for("dashboard"))

    username = request.form.get("username")
    ass_id = request.form.get("ass-id")
    status = request.form.get("status")

    try:
        ass_id = int(ass_id)
    except:
        abort(400)

    db = get_db()
    db.row_factory = sqlite3.Row

    # Validate data
    req = query_db(
        """SELECT * FROM Remarks
        WHERE username = ? AND ass_id = ? AND status = 'open'""",
        [username, ass_id],
        one=True
    )
    if req is None:
        db.close()
        abort(400)
    if status not in ["accepted", "rejected"]:
        abort(400)

    db.execute(
        """UPDATE Remarks SET status = ?
        WHERE username = ? AND ass_id = ?""",
        [status, username, ass_id]
    )
    db.commit()
    db.close()
    return redirect(url_for("dashboard"))

@app.route("/dashboard/new-assessment", methods=["GET", "POST"])
@need_login
def new_ass():
    if session["acc_type"] != "instructor":
        abort(403)
    if request.method == "GET":
        return redirect(url_for("dashboard"))

    db = get_db()
    db.row_factory = sqlite3.Row
    ass = request.form.get("ass")
    if query_db("SELECT * FROM Assessments WHERE name = ?", [ass],
                one=True) is not None:
        flash("That assignment already exists.")
        db.close()
        return redirect(url_for("dashboard"))

    ass_type = request.form.get("type")
    if ass_type not in ["ass", "lab", "test"]:
        db.close()
        abort(400)

    db.execute("INSERT INTO Assessments(type, name) VALUES(?, ?)",
               [ass_type, ass])
    db.commit()
    db.close()
    return redirect(url_for("dashboard"))

@app.route("/dashboard/marks", methods=["GET", "POST"])
@need_login
def marks():
    if session["acc_type"] != "instructor":
        abort(403)
    if request.method == "GET":
        return redirect(url_for("dashboard"))
    ass_id = request.form.get("ass")
    try:
        ass_id = int(ass_id)
    except:
        abort(400)

    db = get_db()
    db.row_factory = sqlite3.Row
    ass = query_db("SELECT * FROM Assessments WHERE id = ?", [ass_id],
                   one=True)
    if ass is None:
        db.close()
        abort(400)
    db.close()
    return redirect(url_for("marks_for_ass", ass_id=ass_id))

@app.route("/dashboard/marks/<ass_id>")
@need_login
def marks_for_ass(ass_id):
    if session["acc_type"] != "instructor":
        abort(403)
    try:
        ass_id = int(ass_id)
    except:
        abort(400)

    db = get_db()
    db.row_factory = sqlite3.Row

    ass = query_db("SELECT name FROM Assessments WHERE id = ?", [ass_id],
                   one=True)
    if ass is None:
        db.close()
        abort(400)
    marks = query_db(
        """SELECT id, U.username, U.name, mark
        FROM Assessments AS A CROSS JOIN Users AS U LEFT JOIN Marks AS M
        ON U.username = M.username AND id = ass_id
        WHERE U.type = "student" AND id = ?
        ORDER BY U.name""",
        [ass_id]
    )
    db.close()
    return render_template("marks.html", ass_id=ass_id, ass=ass, marks=marks)

@app.route("/dashboard/edit-marks", methods=["GET", "POST"])
@need_login
def edit_marks():
    if session["acc_type"] != "instructor":
        abort(403)
    if request.method == "GET":
        return redirect(url_for("dashboard"))

    ass_id = request.form.get("id")
    try:
        ass_id = int(ass_id)
        data = request.form.get("data")
        data = json.loads(data)
    except:
        abort(400)

    db = get_db()
    db.row_factory = sqlite3.Row

    # Validate data
    ass = query_db("SELECT * FROM Assessments WHERE id = ?", [ass_id],
                   one=True)
    if ass is None:
        db.close()
        abort(400)
    for user in data:
        if query_db(
            "SELECT * FROM Users WHERE username = ? AND type = 'student'",
            [user],
            one=True
        ) is None:
            db.close()
            abort(400)
        try:
            data[user] = int(data[user])
        except:
            db.close()
            abort(400)

    for user in data:
        row = query_db("SELECT * FROM Marks WHERE username = ? AND ass_id = ?",
                       [user, ass_id], one=True)
        if row is not None:
            db.execute(
                """UPDATE Marks SET mark = ?
                WHERE username = ? AND ass_id = ?""",
                [data[user], user, ass_id]
            )
        else:
            db.execute("INSERT INTO Marks VALUES(?, ?, ?)",
                       [user, ass_id, data[user]])
    db.commit()
    db.close()
    return redirect(url_for("marks_for_ass", ass_id=ass_id))

@app.route("/lectures")
@need_login
def lectures():
    return render_template("lectures.html")

@app.route("/assignments")
@need_login
def assignments():
    return render_template("assignments.html")

@app.route("/labs")
@need_login
def labs():
    return render_template("labs.html")

@app.route("/tests")
@need_login
def tests():
    return render_template("tests.html")

@app.route("/resources")
@need_login
def resources():
    return render_template("resources.html")

@app.route("/static/files/<file>")
@need_login
def files(file):
    return send_from_directory("static/files", file)

@app.errorhandler(400)
def bad_request(e):
    return render_template("400.html"), 400

@app.errorhandler(403)
def forbidden(e):
    return render_template("403.html"), 403

@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404

@app.errorhandler(500)
def internal_error(e):
    return render_template("500.html"), 500

if __name__ == "__main__":
    app.run()
