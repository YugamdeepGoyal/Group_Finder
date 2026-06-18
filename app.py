import os

from flask import Flask, abort, flash, redirect, render_template, request, url_for
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)

from models import JoinRequest, Project, ProjectMember, ProjectRole, Skill, User, db
from seed import seed_demo_data

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config["SECRET_KEY"] = "dev-secret-key-change-this-before-deploying"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(basedir, "forgemate.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
login_manager.login_message = "Please log in to access that page."
login_manager.login_message_category = "info"


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


SKILL_LEVELS = ["expert", "mid", "beginner"]


@app.context_processor
def inject_active_page():
    section_map = {
        "directory": "directory", "project_detail": "directory", "new_project": "directory",
        "my_profile": "profile", "view_profile": "profile", "edit_profile": "profile",
        "inbox": "inbox",
    }
    return {"active_page": section_map.get(request.endpoint, "")}


# ───────────────────────── PUBLIC PAGES ─────────────────────────

@app.route("/")
def landing():
    all_projects = Project.query.all()
    stats = {
        "projects": len(all_projects),
        "builders": User.query.count(),
        "open": sum(1 for p in all_projects if p.status != "full"),
    }
    return render_template("landing.html", stats=stats)


@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("directory"))

    if request.method == "POST":
        username = request.form.get("username", "").strip().lower()
        email = request.form.get("email", "").strip().lower()
        full_name = request.form.get("full_name", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        errors = []
        if not username or not email or not password:
            errors.append("Username, email and password are all required.")
        if " " in username:
            errors.append("Username can't contain spaces.")
        if password and len(password) < 6:
            errors.append("Password must be at least 6 characters.")
        if password != confirm_password:
            errors.append("Passwords don't match.")
        if username and User.query.filter_by(username=username).first():
            errors.append("That username is already taken.")
        if email and User.query.filter_by(email=email).first():
            errors.append("An account with that email already exists.")

        if errors:
            for e in errors:
                flash(e, "error")
            return render_template("register.html", form=request.form)

        user = User(username=username, email=email, full_name=full_name or username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        login_user(user)
        flash("Welcome to Forgemate — your builder card is live.", "success")
        return redirect(url_for("edit_profile"))

    return render_template("register.html", form={})


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("directory"))

    if request.method == "POST":
        identifier = request.form.get("identifier", "").strip().lower()
        password = request.form.get("password", "")
        user = User.query.filter(
            (User.username == identifier) | (User.email == identifier)
        ).first()

        if user and user.check_password(password):
            login_user(user)
            flash(f"Welcome back, {user.display_name}.", "success")
            next_url = request.args.get("next")
            return redirect(next_url or url_for("directory"))

        flash("Invalid username/email or password.", "error")
        return render_template("login.html", form=request.form)

    return render_template("login.html", form={})


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You've been logged out.", "info")
    return redirect(url_for("landing"))


# ───────────────────────── DIRECTORY ─────────────────────────

@app.route("/directory")
@login_required
def directory():
    q = request.args.get("q", "").strip().lower()
    status_filter = request.args.get("status", "all")
    event_filters = request.args.getlist("event")
    skill_filters = request.args.getlist("skill")

    everything = Project.query.order_by(Project.created_at.desc()).all()
    projects = everything

    if q:
        projects = [
            p for p in projects
            if q in p.title.lower()
            or q in (p.description or "").lower()
            or any(q in t.lower() for t in p.tag_list)
        ]

    if status_filter != "all":
        projects = [p for p in projects if p.status == status_filter]

    if event_filters:
        projects = [p for p in projects if p.event in event_filters]

    if skill_filters:
        projects = [
            p for p in projects
            if all(any(sf.lower() == t.lower() for t in p.tag_list) for sf in skill_filters)
        ]

    all_events = sorted({p.event for p in everything if p.event})
    all_tags = sorted({t for p in everything for t in p.tag_list})
    status_counts = {
        "all": len(everything),
        "open": sum(1 for p in everything if p.status == "open"),
        "closing": sum(1 for p in everything if p.status == "closing"),
        "full": sum(1 for p in everything if p.status == "full"),
    }

    return render_template(
        "directory.html",
        projects=projects,
        all_events=all_events,
        all_tags=all_tags,
        status_counts=status_counts,
        q=request.args.get("q", ""),
        status_filter=status_filter,
        event_filters=event_filters,
        skill_filters=skill_filters,
    )


@app.route("/project/<int:project_id>")
@login_required
def project_detail(project_id):
    project = Project.query.get_or_404(project_id)
    pending_request = project.pending_request_for(current_user.id)
    user_is_lead = project.lead_id == current_user.id
    user_is_member = project.is_member(current_user.id)
    return render_template(
        "project_detail.html",
        project=project,
        pending_request=pending_request,
        user_is_lead=user_is_lead,
        user_is_member=user_is_member,
    )


@app.route("/project/new", methods=["GET", "POST"])
@login_required
def new_project():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        event = request.form.get("event", "").strip()
        tags = request.form.get("tags", "").strip()
        icon_emoji = request.form.get("icon_emoji", "").strip() or "🔗"
        roles_raw = request.form.get("roles", "")
        role_titles = [r.strip() for r in roles_raw.splitlines() if r.strip()]

        if not title:
            flash("Give your project a title.", "error")
            return render_template("project_new.html", form=request.form)

        project = Project(
            title=title, description=description, event=event,
            tags=tags, icon_emoji=icon_emoji, lead_id=current_user.id,
        )
        db.session.add(project)
        db.session.flush()

        for rt in role_titles:
            db.session.add(ProjectRole(project_id=project.id, title=rt, filled=False))

        db.session.commit()
        flash("Project vault registered.", "success")
        return redirect(url_for("project_detail", project_id=project.id))

    return render_template("project_new.html", form={})


@app.route("/project/<int:project_id>/apply", methods=["POST"])
@login_required
def apply_to_project(project_id):
    project = Project.query.get_or_404(project_id)

    if project.lead_id == current_user.id:
        flash("You can't apply to your own project.", "error")
    elif project.is_member(current_user.id):
        flash("You're already on this team.", "error")
    elif project.pending_request_for(current_user.id):
        flash("You already have a pending request for this project.", "error")
    else:
        role_id = request.form.get("role_id") or None
        message = request.form.get("message", "").strip()
        jr = JoinRequest(
            project_id=project.id, applicant_id=current_user.id,
            role_id=role_id, message=message, status="pending",
        )
        db.session.add(jr)
        db.session.commit()
        flash("Sync request sent to the project lead.", "success")

    return redirect(url_for("project_detail", project_id=project.id))


# ───────────────────────── INBOX ─────────────────────────

@app.route("/inbox")
@login_required
def inbox():
    led_project_ids = [p.id for p in current_user.led_projects]
    pending = (
        JoinRequest.query.filter(
            JoinRequest.project_id.in_(led_project_ids),
            JoinRequest.status == "pending",
        )
        .order_by(JoinRequest.created_at.desc())
        .all()
    )
    return render_template("inbox.html", requests=pending)


@app.route("/inbox/<int:request_id>/accept", methods=["POST"])
@login_required
def accept_request(request_id):
    jr = JoinRequest.query.get_or_404(request_id)
    project = jr.project
    if project.lead_id != current_user.id:
        abort(403)

    role_label = request.form.get("role_label", "").strip()
    if not role_label:
        role_label = jr.role.title if jr.role else "Contributor"

    member = ProjectMember(
        project_id=project.id, user_id=jr.applicant_id,
        role_label=role_label, is_lead=False,
    )
    db.session.add(member)

    if jr.role:
        jr.role.filled = True

    jr.status = "accepted"
    db.session.commit()
    flash(f"{jr.applicant.display_name} added to {project.title}.", "success")
    return redirect(url_for("inbox"))


@app.route("/inbox/<int:request_id>/decline", methods=["POST"])
@login_required
def decline_request(request_id):
    jr = JoinRequest.query.get_or_404(request_id)
    if jr.project.lead_id != current_user.id:
        abort(403)

    jr.status = "declined"
    db.session.commit()
    flash(f"Declined sync request from {jr.applicant.display_name}.", "info")
    return redirect(url_for("inbox"))


# ───────────────────────── PROFILE ─────────────────────────

@app.route("/profile")
@login_required
def my_profile():
    return redirect(url_for("view_profile", username=current_user.username))


@app.route("/profile/<username>")
@login_required
def view_profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    led_projects = user.led_projects.order_by(Project.created_at.desc()).all()
    memberships = ProjectMember.query.filter_by(user_id=user.id).all()
    return render_template(
        "profile.html",
        profile_user=user,
        led_projects=led_projects,
        memberships=memberships,
        is_own=(user.id == current_user.id),
    )


@app.route("/profile/edit", methods=["GET", "POST"])
@login_required
def edit_profile():
    if request.method == "POST":
        current_user.full_name = request.form.get("full_name", "").strip() or current_user.username
        current_user.role_title = request.form.get("role_title", "").strip()
        current_user.location = request.form.get("location", "").strip()
        current_user.github_url = request.form.get("github_url", "").strip()
        current_user.website_url = request.form.get("website_url", "").strip()
        current_user.bio = request.form.get("bio", "").strip()
        db.session.commit()
        flash("Profile updated.", "success")
        return redirect(url_for("my_profile"))

    return render_template("profile_edit.html", levels=SKILL_LEVELS)


@app.route("/profile/skills/add", methods=["POST"])
@login_required
def add_skill():
    name = request.form.get("skill_name", "").strip()
    level = request.form.get("skill_level", "mid")
    if level not in SKILL_LEVELS:
        level = "mid"
    if name:
        db.session.add(Skill(user_id=current_user.id, name=name, level=level))
        db.session.commit()
        flash(f"Added skill: {name}", "success")
    return redirect(url_for("edit_profile"))


@app.route("/profile/skills/<int:skill_id>/delete", methods=["POST"])
@login_required
def delete_skill(skill_id):
    skill = Skill.query.get_or_404(skill_id)
    if skill.user_id != current_user.id:
        abort(403)
    db.session.delete(skill)
    db.session.commit()
    return redirect(url_for("edit_profile"))


with app.app_context():
    db.create_all()
    seed_demo_data()


if __name__ == "__main__":
    app.run(debug=True, port=5000)
