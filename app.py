from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash
import psycopg2
from psycopg2.extras import RealDictCursor
import io
import pandas as pd
from flask import Response
from reportlab.pdfgen import canvas

app = Flask(__name__)

# ---------------- SECRET KEY ----------------
app.secret_key = "1a8309ad37ffde4ba90bed9784c99948"

# ---------------- SUPABASE DATABASE CONNECTION ----------------
def get_db_connection():
    return psycopg2.connect(
        host="db.zjoqsopnssmrxcnbavvj.supabase.co",
        database="postgres",
        user="postgres",
        password="aide-et-action",
        port="5432"
    )

# ---------------- LOGIN ----------------
@app.route("/", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        cur.execute(
            "SELECT * FROM users WHERE username=%s AND password=%s",
            (username, password)
        )

        user = cur.fetchone()

        cur.close()
        conn.close()

        if user:
            session["username"] = username
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid login!")

    return render_template("login.html")

# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():

    if "username" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("SELECT COUNT(*) AS total FROM projects")
    total_projects = cur.fetchone()["total"]

    cur.execute("SELECT COUNT(*) AS ongoing FROM projects WHERE status='Ongoing'")
    ongoing_projects = cur.fetchone()["ongoing"]

    cur.execute("SELECT COUNT(*) AS completed FROM projects WHERE status='Closed'")
    completed_projects = cur.fetchone()["completed"]

    cur.close()
    conn.close()

    return render_template(
        "dashboard.html",
        total_projects=total_projects,
        ongoing_projects=ongoing_projects,
        completed_projects=completed_projects
    )

# ---------------- EXPORT TO EXCEL (ADDED) ----------------
@app.route("/export_excel")
def export_excel():

    if "username" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("SELECT * FROM projects")
    data = cur.fetchall()

    cur.close()
    conn.close()

    df = pd.DataFrame(data)

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Projects')

    output.seek(0)

    return Response(
        output,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment;filename=projects.xlsx"}
    )

# ---------------- EXPORT TO PDF (ADDED) ----------------
@app.route("/export_pdf")
def export_pdf():

    if "username" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("SELECT project_name, status, total_budget_inr FROM projects")
    data = cur.fetchall()

    cur.close()
    conn.close()

    buffer = io.BytesIO()
    p = canvas.Canvas(buffer)

    y = 800
    p.drawString(200, 820, "PROJECT REPORT")

    for row in data:
        text = f"{row['project_name']} | {row['status']} | ₹{row['total_budget_inr']}"
        p.drawString(50, y, text)
        y -= 20

    p.save()
    buffer.seek(0)

    return Response(
        buffer,
        mimetype="application/pdf",
        headers={"Content-Disposition": "attachment;filename=projects.pdf"}
    )

# ---------------- SEARCH PROJECTS ----------------
@app.route("/projects", methods=["GET", "POST"])
def search():

    if "username" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    current_year = datetime.now().year
    financial_years = [f"{y}-{y+1}" for y in range(2010, current_year + 2)]

    query = "SELECT * FROM projects WHERE 1=1"
    params = []

    selected_fy = ""

    status_from_dashboard = request.args.get("status")

    if status_from_dashboard:
        query += " AND status=%s"
        params.append(status_from_dashboard)

    if request.method == "POST":

        project_year = request.form.get("project_initiated_year", "").strip()
        thematic = request.form.get("thematic", "").strip()
        erp_code = request.form.get("erp_code", "").strip()

        if project_year:
            query += " AND project_initiated_year=%s"
            params.append(project_year)

        if thematic:
            query += " AND thematic ILIKE %s"
            params.append(f"%{thematic}%")

        if erp_code:
            query += " AND erp_code ILIKE %s"
            params.append(f"%{erp_code}%")

    query += " ORDER BY id DESC"

    cur.execute(query, params)

    results = cur.fetchall()

    for row in results:
        row["financial_year"] = "-"

    cur.close()
    conn.close()

    return render_template(
        "search.html",
        results=results,
        financial_years=financial_years,
        selected_fy=selected_fy,
        from_dashboard=bool(status_from_dashboard)
    )

# ---------------- ADD PROJECT ----------------
@app.route("/add_project", methods=["GET", "POST"])
def add_project():

    if "username" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":

        data = (
            request.form.get("erp_code"),
            request.form.get("project_name"),
            request.form.get("project_initiated_year"),
            request.form.get("thematic"),
            request.form.get("ro"),
            request.form.get("mou_start_date"),
            request.form.get("mou_end_date"),
            request.form.get("donor"),
            request.form.get("budget_2024"),
            request.form.get("total_budget_inr"),
            request.form.get("status"),
            request.form.get("state"),
            request.form.get("districts"),
            request.form.get("block"),
            request.form.get("location"),
            request.form.get("rural_urban")
        )

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO projects (
                erp_code,
                project_name,
                project_initiated_year,
                thematic,
                ro,
                mou_start_date,
                mou_end_date,
                donor,
                budget_2024,
                total_budget_inr,
                status,
                state,
                districts,
                block,
                location,
                rural_urban
            )
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, data)

        conn.commit()

        cur.close()
        conn.close()

        flash("Project added successfully!")

        return redirect(url_for("dashboard"))

    return render_template("add_project.html")

# ---------------- EDIT PROJECT ----------------
@app.route("/edit_project/<int:id>", methods=["GET", "POST"])
def edit_project(id):

    if "username" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("SELECT * FROM projects WHERE id=%s", (id,))
    project = cur.fetchone()

    if request.method == "POST":

        data = (
            request.form.get("erp_code"),
            request.form.get("project_name"),
            request.form.get("project_initiated_year"),
            request.form.get("thematic"),
            request.form.get("ro"),
            request.form.get("mou_start_date"),
            request.form.get("mou_end_date"),
            request.form.get("donor"),
            request.form.get("budget_2024"),
            request.form.get("total_budget_inr"),
            request.form.get("status"),
            request.form.get("state"),
            request.form.get("districts"),
            request.form.get("block"),
            request.form.get("location"),
            request.form.get("rural_urban"),
            id
        )

        cur.execute("""
            UPDATE projects SET
                erp_code=%s,
                project_name=%s,
                project_initiated_year=%s,
                thematic=%s,
                ro=%s,
                mou_start_date=%s,
                mou_end_date=%s,
                donor=%s,
                budget_2024=%s,
                total_budget_inr=%s,
                status=%s,
                state=%s,
                districts=%s,
                block=%s,
                location=%s,
                rural_urban=%s
            WHERE id=%s
        """, data)

        conn.commit()

        cur.close()
        conn.close()

        flash("Project updated successfully!")

        return redirect(url_for("search"))

    cur.close()
    conn.close()

    return render_template("edit_project.html", project=project)

# ---------------- DELETE PROJECT ----------------
@app.route("/delete_project/<int:id>")
def delete_project(id):

    if "username" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("DELETE FROM projects WHERE id=%s", (id,))

    conn.commit()

    cur.close()
    conn.close()

    flash("Project deleted successfully!")

    return redirect(url_for("search"))

# ---------------- PROJECTS BY DATE ----------------
@app.route("/projects_by_date", methods=["GET", "POST"])
def projects_by_date():

    if "username" not in session:
        return redirect(url_for("login"))

    projects_ongoing = []
    projects_closed = []
    selected_date = ""

    if request.method == "POST":

        selected_date = request.form.get("selected_date")

        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        cur.execute("""
            SELECT * FROM projects
            WHERE status='Ongoing'
            ORDER BY id DESC
        """)

        projects_ongoing = cur.fetchall()

        cur.execute("""
            SELECT * FROM projects
            WHERE status='Closed'
            ORDER BY id DESC
        """)

        projects_closed = cur.fetchall()

        cur.close()
        conn.close()

    return render_template(
        "projects_by_date.html",
        projects_ongoing=projects_ongoing,
        projects_closed=projects_closed,
        selected_date=selected_date
    )

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("login"))

# ---------------- RUN APP ----------------
if __name__ == "__main__":
    app.run(debug=True)
