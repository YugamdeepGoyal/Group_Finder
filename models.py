from datetime import datetime

from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

db = SQLAlchemy()


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    full_name = db.Column(db.String(120))
    role_title = db.Column(db.String(150), default="")
    location = db.Column(db.String(120), default="")
    github_url = db.Column(db.String(200), default="")
    website_url = db.Column(db.String(200), default="")
    bio = db.Column(db.Text, default="")

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    skills = db.relationship(
        "Skill", backref="user", cascade="all, delete-orphan", lazy="dynamic"
    )
    led_projects = db.relationship(
        "Project", backref="lead", foreign_keys="Project.lead_id", lazy="dynamic"
    )
    memberships = db.relationship(
        "ProjectMember", backref="user", cascade="all, delete-orphan", lazy="dynamic"
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def display_name(self):
        return self.full_name or self.username

    @property
    def initials(self):
        parts = [p for p in self.display_name.split() if p]
        if not parts:
            return "?"
        if len(parts) == 1:
            return parts[0][:2].upper()
        return (parts[0][0] + parts[1][0]).upper()

    @property
    def avatar_color(self):
        # deterministic color from a small fixed palette, based on user id
        palette = ["#0038FF", "#14532D", "#7C2D12", "#55555C", "#0F0F11"]
        return palette[self.id % len(palette)]

    @property
    def pending_inbox_count(self):
        return JoinRequest.query.join(Project).filter(
            Project.lead_id == self.id, JoinRequest.status == "pending"
        ).count()


class Skill(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    level = db.Column(db.String(20), default="mid")  # expert / mid / beginner


class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, default="")
    event = db.Column(db.String(150), default="")
    tags = db.Column(db.String(300), default="")  # comma separated
    icon_emoji = db.Column(db.String(10), default="🔗")
    lead_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    manual_status = db.Column(db.String(20), default="")  # "", "open", "closing", "full"

    roles = db.relationship(
        "ProjectRole", backref="project", cascade="all, delete-orphan", lazy="dynamic"
    )
    members = db.relationship(
        "ProjectMember", backref="project", cascade="all, delete-orphan", lazy="dynamic"
    )
    requests = db.relationship(
        "JoinRequest", backref="project", cascade="all, delete-orphan", lazy="dynamic"
    )

    @property
    def tag_list(self):
        return [t.strip() for t in (self.tags or "").split(",") if t.strip()]

    @property
    def open_roles(self):
        return self.roles.filter_by(filled=False).all()

    @property
    def spots_open(self):
        return len(self.open_roles)

    @property
    def status(self):
        # If lead manually set a status, respect it
        if self.manual_status in ("open", "closing", "full"):
            return self.manual_status
        # Auto-derive from roles
        if self.roles.count() == 0:
            return "open"
        if self.spots_open == 0:
            return "full"
        if self.spots_open == 1:
            return "closing"
        return "open"

    @property
    def status_label(self):
        return self.status.upper()

    @property
    def team_size(self):
        # current roster (members + lead) plus however many open seats remain
        return self.members.count() + 1 + self.spots_open

    @property
    def filled_count(self):
        return self.members.count() + 1

    def pending_request_for(self, user_id):
        return self.requests.filter_by(applicant_id=user_id, status="pending").first()

    def is_member(self, user_id):
        if self.lead_id == user_id:
            return True
        return self.members.filter_by(user_id=user_id).first() is not None


class ProjectRole(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("project.id"), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    filled = db.Column(db.Boolean, default=False)

    join_requests = db.relationship("JoinRequest", backref="role", lazy="dynamic")


class ProjectMember(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("project.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    role_label = db.Column(db.String(150), default="")
    is_lead = db.Column(db.Boolean, default=False)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)


class JoinRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("project.id"), nullable=False)
    applicant_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey("project_role.id"), nullable=True)
    message = db.Column(db.Text, default="")
    status = db.Column(db.String(20), default="pending")  # pending/accepted/declined
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    applicant = db.relationship("User")
