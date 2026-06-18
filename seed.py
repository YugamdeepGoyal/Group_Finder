"""
Populates the database with demo data the first time the app is run,
so you have something to click around immediately instead of an empty app.

All demo accounts use the password: forgemate123
"""

from models import JoinRequest, Project, ProjectMember, ProjectRole, Skill, User, db

DEMO_PASSWORD = "forgemate123"


def _make_user(username, full_name, role_title, location, github_url, website_url, bio):
    u = User(
        username=username,
        email=f"{username}@example.com",
        full_name=full_name,
        role_title=role_title,
        location=location,
        github_url=github_url,
        website_url=website_url,
        bio=bio,
    )
    u.set_password(DEMO_PASSWORD)
    db.session.add(u)
    return u


def _add_skills(user, skill_pairs):
    for name, level in skill_pairs:
        db.session.add(Skill(user_id=user.id, name=name, level=level))


def seed_demo_data():
    if User.query.count() > 0:
        return  # already seeded, don't duplicate

    arjun = _make_user(
        "arjunverma", "Arjun Verma", "Full-Stack · Smart Contract Lead", "Bengaluru, Karnataka",
        "github.com/arjunverma-dev", "arjunverma.dev",
        "CS @ IIT Bombay. Focused on cross-chain state synchronization layers and "
        "offline-first client replication protocols. I like shipping code that "
        "works under real constraints.",
    )
    priya = _make_user(
        "priyasharma", "Priya Sharma", "React Developer", "Hyderabad, Telangana",
        "github.com/priyasharma", "",
        "I build telemetry dashboards and state-machine driven interfaces. "
        "Previously worked on analytics tooling for DeFi vault products.",
    )
    rohit = _make_user(
        "rohitnair", "Rohit Nair", "ML Engineer", "Chennai, Tamil Nadu",
        "github.com/rohitnair-ml", "",
        "Doing MEV simulation and forecasting research at IISc. I like "
        "turning messy on-chain data into something a model can actually use.",
    )
    neha = _make_user(
        "nehajoshi", "Neha Joshi", "Lead UX Designer", "Mumbai, Maharashtra",
        "github.com/nehajoshi", "nehajoshi.design",
        "Designed multiple DeFi aggregator dashboards. I care about making "
        "complicated systems feel obvious to use.",
    )
    ananya = _make_user(
        "ananyasingh", "Ananya Singh", "Solidity Developer", "Pune, Maharashtra",
        "github.com/ananya-builds", "",
        "Smart contract engineer focused on gas-efficient vault and "
        "auction mechanisms.",
    )
    vikram = _make_user(
        "vikramgupta", "Vikram Gupta", "Systems / Indexing Engineer", "Delhi, NCR",
        "github.com/vgupta", "",
        "I like building the boring infrastructure that everything else "
        "quietly depends on: indexers, sync layers, queues.",
    )

    db.session.flush()  # assign ids so we can attach skills/projects

    _add_skills(arjun, [
        ("Solidity", "expert"), ("React / Next.js", "expert"), ("TypeScript", "expert"),
        ("Rust", "mid"), ("Hardhat", "mid"), ("wagmi", "mid"),
        ("ZK / Circom", "beginner"), ("PostgreSQL", "beginner"),
    ])
    _add_skills(priya, [("React", "expert"), ("wagmi", "mid"), ("TypeScript", "mid")])
    _add_skills(rohit, [("Python", "expert"), ("PyTorch", "mid"), ("SQL", "mid")])
    _add_skills(neha, [("Figma", "expert"), ("UX Research", "expert")])
    _add_skills(ananya, [("Solidity", "expert"), ("Hardhat", "mid")])
    _add_skills(vikram, [("Rust", "expert"), ("Python", "mid"), ("Node.js", "mid")])

    def make_project(lead, title, desc, event, tags, icon, open_role_titles, roster):
        """roster: list of (user, role_label) already-on-the-team members."""
        p = Project(
            title=title, description=desc, event=event, tags=tags,
            icon_emoji=icon, lead_id=lead.id,
        )
        db.session.add(p)
        db.session.flush()
        for rt in open_role_titles:
            db.session.add(ProjectRole(project_id=p.id, title=rt, filled=False))
        for member_user, role_label in roster:
            db.session.add(ProjectMember(
                project_id=p.id, user_id=member_user.id,
                role_label=role_label, is_lead=False,
            ))
        return p

    aether = make_project(
        arjun, "Aether Vaults",
        "Cross-chain yield coordinator that auto-rebalances vault assets across "
        "decentralized indexes.",
        "ETHGlobal Brussels", "Solidity,React,DeFi", "🔗",
        ["Frontend Lead / React Architect", "ML / Forecasting Systems Lead"],
        [(ananya, "Solidity Developer"), (vikram, "Sub-system Indexing Engineer")],
    )

    telescope = make_project(
        rohit, "Telescope SDK",
        "Distributed logging and execution tracing agent designed for "
        "light-weight SQLite database syncs.",
        "HackMIT 2026", "Python,LLM,React", "💻",
        ["Backend Python Engineer", "Frontend React Developer", "Data Viz Lead"],
        [],
    )

    sapling = make_project(
        neha, "Sapling Protocol",
        "On-chain registry with satellite coverage telemetry verification for "
        "agricultural conservation.",
        "Climate Hack 2026", "Solidity,Python,IoT", "🌱",
        ["IoT Sensor Integration Engineer"],
        [(arjun, "Smart Contract Developer"), (vikram, "Backend Engineer")],
    )

    pixelforge = make_project(
        ananya, "PixelForge",
        "Asymmetric digital canvas engine with provable creator attribution "
        "and lightweight sync layers.",
        "ETHGlobal Brussels", "Solidity,WebGL,React", "🎨",
        ["WebGL Engineer", "Smart Contract Auditor"],
        [(neha, "Design Lead")],
    )

    tessera = make_project(
        vikram, "Tessera Ledger",
        "Privacy-preserving state record coordination using zero-knowledge "
        "verification frameworks.",
        "TreeHacks", "ZK / Circom,Rust,React", "🔐",
        ["Rust Cryptography Engineer", "Frontend Integration Engineer"],
        [(priya, "Frontend Developer")],
    )

    stems = make_project(
        priya, "Stems Audio",
        "Decentralized royalties indexing system for collaborative audio "
        "stems and modular track licensing.",
        "Calhacks 12", "Solidity,Node.js,Figma", "🎵",
        [],  # fully staffed
        [(vikram, "Backend Engineer"), (ananya, "Solidity Developer"), (neha, "Design Lead")],
    )

    db.session.flush()

    def find_role(project, title):
        return project.roles.filter_by(title=title).first()

    # a handful of pending sync requests so inboxes aren't empty on first login
    db.session.add(JoinRequest(
        project_id=aether.id, applicant_id=priya.id,
        role_id=find_role(aether, "Frontend Lead / React Architect").id,
        message="Have built telemetry dashboards for DeFi vaults. Would "
                "love to own the state machine interface layer for Aether.",
        status="pending",
    ))
    db.session.add(JoinRequest(
        project_id=aether.id, applicant_id=rohit.id,
        role_id=find_role(aether, "ML / Forecasting Systems Lead").id,
        message="Doing MEV simulation and forecasting research at IISc. I "
                "can build the asset rebalance signaling model in Python.",
        status="pending",
    ))
    db.session.add(JoinRequest(
        project_id=telescope.id, applicant_id=vikram.id,
        role_id=find_role(telescope, "Backend Python Engineer").id,
        message="I've built sync layers and indexers for a few hackathon "
                "projects before — happy to own the SQLite sync logic here.",
        status="pending",
    ))
    db.session.add(JoinRequest(
        project_id=sapling.id, applicant_id=ananya.id,
        role_id=find_role(sapling, "IoT Sensor Integration Engineer").id,
        message="I've worked with low-power sensor telemetry before and can "
                "help get the satellite verification layer talking to the "
                "contracts.",
        status="pending",
    ))

    db.session.commit()
