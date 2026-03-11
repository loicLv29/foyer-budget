import hashlib
import json
from datetime import date, datetime
from pathlib import Path
import calendar

import pandas as pd
import streamlit as st

# Config
st.set_page_config(
    page_title="FoyerBudget",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
)

APP_DIR = Path(__file__).parent
DATA_DIR = APP_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

USERS_FILE = DATA_DIR / "users.json"
EXPENSES_FILE = DATA_DIR / "expenses.csv"
BUDGETS_FILE = DATA_DIR / "budgets.json"

CATEGORIES = [
    "🛒 Courses", "⛽ Essence", "🍽️ Restaurant", "💊 Santé",
    "👕 Vêtements", "🏠 Logement", "💡 Énergie", "📱 Abonnements",
    "🎬 Loisirs", "🏫 Éducation", "🚌 Transport", "🐾 Animaux", "📦 Autre"
]

MONTHS_FR = [
    "", "Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
    "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"
]

st.markdown("""
<style>
    .block-container {
        padding-top: 1rem;
        padding-bottom: 3rem;
        max-width: 1200px;
    }

    .app-shell {
        background: linear-gradient(180deg, #F8FAFC 0%, #EEF2F7 100%);
        border-radius: 22px;
        padding: 1.1rem;
        margin-bottom: 1rem;
        border: 1px solid rgba(15, 23, 42, 0.06);
    }

    .hero {
        background: linear-gradient(135deg, #0F172A 0%, #1D4ED8 55%, #38BDF8 100%);
        color: white;
        border-radius: 22px;
        padding: 1.4rem 1.3rem;
        margin-bottom: 1rem;
        box-shadow: 0 10px 30px rgba(37, 99, 235, 0.18);
    }

    .hero-title {
        font-size: 2rem;
        font-weight: 800;
        line-height: 1.05;
        margin: 0;
    }

    .hero-sub {
        margin-top: .45rem;
        color: rgba(255,255,255,.88);
        font-size: .98rem;
    }

    .glass-card {
        background: rgba(255,255,255,.86);
        backdrop-filter: blur(8px);
        border-radius: 18px;
        padding: 1rem 1rem;
        border: 1px solid rgba(15, 23, 42, 0.06);
        box-shadow: 0 6px 20px rgba(15, 23, 42, 0.06);
        margin-bottom: .9rem;
    }

    .kpi-card {
        background: white;
        border-radius: 18px;
        padding: 1rem;
        border: 1px solid rgba(15, 23, 42, 0.06);
        box-shadow: 0 4px 16px rgba(15, 23, 42, 0.06);
    }

    .kpi-label {
        color: #64748B;
        font-size: .86rem;
        margin-bottom: .2rem;
    }

    .kpi-value {
        font-size: 1.6rem;
        font-weight: 800;
        color: #0F172A;
    }

    .expense-card {
        background: white;
        border-radius: 16px;
        padding: .95rem 1rem;
        border: 1px solid rgba(15, 23, 42, 0.06);
        box-shadow: 0 4px 14px rgba(15, 23, 42, 0.05);
        margin-bottom: .75rem;
    }

    .expense-top {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: .8rem;
    }

    .expense-cat {
        font-weight: 700;
        color: #0F172A;
    }

    .expense-amt {
        font-weight: 800;
        color: #111827;
    }

    .expense-meta {
        margin-top: .35rem;
        font-size: .9rem;
        color: #64748B;
    }

    .tag {
        display: inline-block;
        padding: .2rem .55rem;
        border-radius: 999px;
        background: #EFF6FF;
        color: #1D4ED8;
        font-size: .78rem;
        font-weight: 600;
        margin-right: .35rem;
        margin-top: .35rem;
    }

    .prog-wrap {
        background:#E5E7EB;
        border-radius:999px;
        height:10px;
        margin-top:8px;
        overflow:hidden;
    }

    .prog-fill {
        height:10px;
        border-radius:999px;
        transition: width .4s;
    }

    .card {
        background: white;
        border-radius: 16px;
        padding: 1rem 1rem;
        margin-bottom: .8rem;
        border-left: 4px solid #2563EB;
        border: 1px solid rgba(15, 23, 42, 0.06);
        box-shadow: 0 4px 14px rgba(15, 23, 42, 0.05);
    }

    .card-warn { border-left-color: #F59E0B; }
    .card-danger { border-left-color: #EF4444; }
    .card-ok { border-left-color: #10B981; }

    .section-title {
        font-size: 1.15rem;
        font-weight: 800;
        color: #0F172A;
        margin-bottom: .55rem;
    }

    [data-testid="stMetricValue"] {
        font-size: 1.45rem !important;
    }

    @media (max-width: 768px) {
        .block-container { padding: .8rem .8rem 2.5rem; }
        .hero-title { font-size: 1.6rem; }
    }
</style>
""", unsafe_allow_html=True)


def hash_pw(pwd: str) -> str:
    return hashlib.sha256(pwd.encode()).hexdigest()


def load_users():
    if not USERS_FILE.exists():
        return {}
    return json.loads(USERS_FILE.read_text(encoding="utf-8"))


def save_users(users):
    USERS_FILE.write_text(json.dumps(users, ensure_ascii=False, indent=2), encoding="utf-8")


def load_expenses():
    if EXPENSES_FILE.exists():
        df = pd.read_csv(EXPENSES_FILE, parse_dates=["date"])

        if "id" not in df.columns:
            df["id"] = range(1, len(df) + 1)

        if "montant" not in df.columns and "amount" in df.columns:
            df["montant"] = df["amount"]

        if "categorie" not in df.columns and "category" in df.columns:
            df["categorie"] = df["category"]

        if "description" not in df.columns and "label" in df.columns:
            df["description"] = df["label"]
        elif "description" not in df.columns:
            df["description"] = ""

        if "membre" not in df.columns and "paid_by" in df.columns:
            df["membre"] = df["paid_by"]
        elif "membre" not in df.columns:
            df["membre"] = st.session_state.get("username", "inconnu")

        if "partage" not in df.columns:
            df["partage"] = "[]"

        expected = ["id", "date", "montant", "categorie", "description", "membre", "partage"]
        for col in expected:
            if col not in df.columns:
                df[col] = ""

        return df[expected]

    return pd.DataFrame(columns=["id", "date", "montant", "categorie", "description", "membre", "partage"])



def save_expenses(df):
    df.to_csv(EXPENSES_FILE, index=False)


def add_expense(date_val, montant, categorie, desc, membre, partage):
    df = load_expenses()

    if len(df) == 0:
        next_id = 1
    else:
        numeric_ids = pd.to_numeric(df["id"], errors="coerce").fillna(0)
        next_id = int(numeric_ids.max()) + 1

    row = pd.DataFrame([{
        "id": next_id,
        "date": pd.to_datetime(date_val),
        "montant": float(montant),
        "categorie": categorie,
        "description": desc or "",
        "membre": membre,
        "partage": json.dumps(partage, ensure_ascii=False),
    }])

    df = pd.concat([df, row], ignore_index=True)
    save_expenses(df)



def delete_expense(eid):
    df = load_expenses()
    save_expenses(df[df["id"] != eid])


def load_budgets():
    if not BUDGETS_FILE.exists():
        return {}
    return json.loads(BUDGETS_FILE.read_text(encoding="utf-8"))


def save_budgets(budgets):
    BUDGETS_FILE.write_text(json.dumps(budgets, ensure_ascii=False, indent=2), encoding="utf-8")


def parse_partage(value):
    if pd.isna(value) or value in ("", "[]", None):
        return []
    if isinstance(value, list):
        return value
    return json.loads(value)


def progress_bar(pct):
    pct_clamped = min(max(pct, 0), 100)
    color = "#10B981" if pct < 75 else "#F59E0B" if pct < 100 else "#EF4444"
    return f"""
    <div class="prog-wrap">
        <div class="prog-fill" style="width:{pct_clamped}%;background:{color}"></div>
    </div>
    """


def card_class(pct):
    if pct >= 100:
        return "card card-danger"
    if pct >= 75:
        return "card card-warn"
    return "card card-ok"


def render_shell_start():
    st.markdown('<div class="app-shell">', unsafe_allow_html=True)


def render_shell_end():
    st.markdown('</div>', unsafe_allow_html=True)


def hero(title, subtitle):
    st.markdown(f"""
    <div class="hero">
        <div class="hero-title">{title}</div>
        <div class="hero-sub">{subtitle}</div>
    </div>
    """, unsafe_allow_html=True)


def kpi_card(label, value):
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
    </div>
    """, unsafe_allow_html=True)


def show_login():
    hero("🏠 FoyerBudget", "Vos dépenses en famille, simplement.")
    users = load_users()
    tab1, tab2 = st.tabs(["🔑 Connexion", "✨ Créer un compte"])

    with tab1:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        with st.form("login"):
            username = st.text_input("Identifiant")
            password = st.text_input("Mot de passe", type="password")
            submitted = st.form_submit_button("Se connecter", use_container_width=True, type="primary")
            if submitted:
                if username in users and users[username]["password"] == hash_pw(password):
                    st.session_state.update(
                        logged_in=True,
                        username=username,
                        display_name=users[username]["display_name"],
                        role=users[username].get("role", "membre"),
                    )
                    st.rerun()
                st.error("Identifiants incorrects")
        st.markdown('</div>', unsafe_allow_html=True)

    with tab2:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        with st.form("register"):
            new_username = st.text_input("Identifiant", placeholder="ex: alice")
            new_display = st.text_input("Prénom / Surnom", placeholder="ex: Alice")
            new_password = st.text_input("Mot de passe", type="password")
            confirm_password = st.text_input("Confirmer", type="password")
            role = "admin" if len(users) == 0 else "membre"

            submitted = st.form_submit_button("Créer mon compte", use_container_width=True, type="primary")
            if submitted:
                if not all([new_username, new_display, new_password]):
                    st.error("Tous les champs sont requis")
                elif new_password != confirm_password:
                    st.error("Les mots de passe ne correspondent pas")
                elif len(new_password) < 6:
                    st.error("Minimum 6 caractères")
                elif new_username in users:
                    st.error("Identifiant déjà pris")
                else:
                    users[new_username] = {
                        "password": hash_pw(new_password),
                        "display_name": new_display,
                        "role": role,
                        "created_at": datetime.now().isoformat(),
                    }
                    save_users(users)
                    st.success(f"Compte créé ! {'(Administrateur)' if role == 'admin' else ''} Connectez-vous.")
        st.markdown('</div>', unsafe_allow_html=True)


def show_sidebar():
    with st.sidebar:
        st.markdown("## 🏠 FoyerBudget")
        st.caption(f"Connecté : {st.session_state.display_name}")
        if st.session_state.role == "admin":
            st.caption("🛡️ Administrateur")

        st.divider()

        page = st.radio("", [
            "📊 Tableau de bord",
            "➕ Ajouter une dépense",
            "📋 Mes dépenses",
            "👥 Dépenses partagées",
            "🎯 Budgets",
            "📅 Rapport mensuel",
            "⚙️ Paramètres",
        ], label_visibility="collapsed")

        st.divider()

        if st.button("🚪 Déconnexion", use_container_width=True):
            for key in ["logged_in", "username", "display_name", "role"]:
                st.session_state.pop(key, None)
            st.rerun()

    return page


def page_dashboard():
    render_shell_start()
    hero("📊 Tableau de bord", "Vue rapide du mois en cours.")
    df = load_expenses()
    users = load_users()
    budgets = load_budgets()

    if df.empty:
        st.info("🎉 Bienvenue ! Commencez par ajouter une dépense.")
        render_shell_end()
        return

    df["date"] = pd.to_datetime(df["date"])
    now = datetime.now()
    df_month = df[(df["date"].dt.month == now.month) & (df["date"].dt.year == now.year)]
    df_mine = df_month[df_month["membre"] == st.session_state.username]
    df_part = df_month[df_month["membre"] != st.session_state.username]
    partner_total = df_part["montant"].sum()

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        kpi_card("💶 Foyer ce mois", f"{df_month['montant'].sum():.2f} €")
    with c2:
        kpi_card("👤 Mes dépenses", f"{df_mine['montant'].sum():.2f} €")
    with c3:
        kpi_card("👫 Mon/Ta part", f"{df_mine['montant'].sum():.2f} / {partner_total:.2f} €")
    with c4:
        kpi_card("📝 Transactions", str(len(df_month)))

    if budgets:
        cat_spend = df_month.groupby("categorie")["montant"].sum()
        alerts = []
        for cat, budget in budgets.items():
            spent = cat_spend.get(cat, 0)
            pct = (spent / budget * 100) if budget > 0 else 0
            if pct >= 75:
                alerts.append(f"{'🔴' if pct >= 100 else '🟡'} **{cat}** : {spent:.0f} € / {budget:.0f} € ({pct:.0f}%)")
        if alerts:
            with st.expander("⚠️ Alertes budget", expanded=True):
                for alert in alerts:
                    st.markdown(alert)

    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("🏷️ Par catégorie")
        cat_data = df_month.groupby("categorie")["montant"].sum().sort_values(ascending=False)
        if not cat_data.empty:
            st.bar_chart(cat_data)

    with col_b:
        st.subheader("👥 Par membre")
        m_data = df_month.groupby("membre")["montant"].sum()
        m_data.index = [users.get(member, {}).get("display_name", member) for member in m_data.index]
        if not m_data.empty:
            st.bar_chart(m_data)

    st.subheader("📈 Évolution mensuelle")
    df["mois"] = df["date"].dt.to_period("M").astype(str)
    monthly = df.groupby("mois")["montant"].sum().reset_index()
    monthly.columns = ["Mois", "Total (€)"]
    st.line_chart(monthly.set_index("Mois"))

    st.subheader("🕐 Dernières dépenses")
    recent = df.sort_values("date", ascending=False).head(8).copy()
    recent["membre"] = recent["membre"].map(lambda member: users.get(member, {}).get("display_name", member))
    for _, row in recent.iterrows():
        st.markdown(f"""
        <div class="expense-card">
            <div class="expense-top">
                <div class="expense-cat">{row['categorie']}</div>
                <div class="expense-amt">{row['montant']:.2f} €</div>
            </div>
            <div class="expense-meta">
                {pd.to_datetime(row['date']).strftime("%d/%m/%Y")} · {row['description'] or 'Sans description'} · {row['membre']}
            </div>
        </div>
        """, unsafe_allow_html=True)

    render_shell_end()


def page_add():
    render_shell_start()
    hero("➕ Ajouter une dépense", "Saisie rapide, pensée mobile.")
    users = load_users()
    members = {key: value["display_name"] for key, value in users.items()}

    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    with st.form("add_form"):
        c1, c2 = st.columns(2)
        with c1:
            date_val = st.date_input("📅 Date", value=date.today())
            montant = st.number_input("💶 Montant (€)", min_value=0.01, step=0.01, format="%.2f")
            categorie = st.selectbox("🏷️ Catégorie", CATEGORIES)
        with c2:
            description = st.text_input("📝 Description", placeholder="Ex: Carrefour drive")
            others = [key for key in members if key != st.session_state.username]
            partage = st.multiselect(
                "👥 Partager avec",
                options=others,
                format_func=lambda x: members[x],
            )

        submitted = st.form_submit_button("✅ Enregistrer", use_container_width=True, type="primary")
        if submitted:
            add_expense(date_val, montant, categorie, description, st.session_state.username, partage)
            st.success(f"{montant:.2f} € enregistrés.")
            st.balloons()
    st.markdown('</div>', unsafe_allow_html=True)
    render_shell_end()


def page_my_expenses():
    render_shell_start()
    hero("📋 Mes dépenses", "Filtre, tri et suppression rapide.")
    df = load_expenses()
    df = df[df["membre"] == st.session_state.username].copy()

    if df.empty:
        st.info("Aucune dépense enregistrée pour vous.")
        render_shell_end()
        return

    df["date"] = pd.to_datetime(df["date"])

    c1, c2, c3 = st.columns(3)
    months = sorted(df["date"].dt.to_period("M").astype(str).unique(), reverse=True)
    month_filter = c1.selectbox("📅 Mois", ["Tous"] + list(months))
    category_filter = c2.selectbox("🏷️ Catégorie", ["Toutes"] + CATEGORIES)
    sort_by = c3.selectbox("🔃 Trier par", ["Date (récent)", "Montant ↓"])

    if month_filter != "Tous":
        df = df[df["date"].dt.to_period("M").astype(str) == month_filter]
    if category_filter != "Toutes":
        df = df[df["categorie"] == category_filter]

    df = df.sort_values("date" if sort_by.startswith("Date") else "montant", ascending=False)

    k1, k2 = st.columns(2)
    with k1:
        kpi_card("💶 Total filtré", f"{df['montant'].sum():.2f} €")
    with k2:
        kpi_card("📝 Nb transactions", str(len(df)))

    for _, row in df.iterrows():
        cmain, cdel = st.columns([12, 1])
        with cmain:
            st.markdown(f"""
            <div class="expense-card">
                <div class="expense-top">
                    <div class="expense-cat">{row['categorie']}</div>
                    <div class="expense-amt">{row['montant']:.2f} €</div>
                </div>
                <div class="expense-meta">
                    {pd.to_datetime(row['date']).strftime("%d/%m/%Y")} · {row['description'] or 'Sans description'}
                </div>
            </div>
            """, unsafe_allow_html=True)
        with cdel:
            if st.button("🗑️", key=f"del_{row['id']}"):
                delete_expense(int(row["id"]))
                st.rerun()

    render_shell_end()


def page_shared():
    render_shell_start()
    hero("👥 Dépenses partagées", "Vue claire des remboursements et équilibres.")
    df = load_expenses()
    users = load_users()
    me = st.session_state.username

    if df.empty:
        st.info("Aucune dépense enregistrée.")
        render_shell_end()
        return

    shared_with_me = df[df["partage"].apply(lambda x: me in parse_partage(x))].copy()
    my_shared = df[(df["membre"] == me) & (df["partage"].apply(lambda x: bool(parse_partage(x))))].copy()

    owed_by_me = sum(row["montant"] / (len(parse_partage(row["partage"])) + 1) for _, row in shared_with_me.iterrows())
    owed_to_me = sum(row["montant"] - row["montant"] / (len(parse_partage(row["partage"])) + 1) for _, row in my_shared.iterrows())
    balance = owed_to_me - owed_by_me

    c1, c2, c3 = st.columns(3)
    with c1:
        kpi_card("💸 Je dois rembourser", f"{owed_by_me:.2f} €")
    with c2:
        kpi_card("💰 On me doit", f"{owed_to_me:.2f} €")
    with c3:
        kpi_card("⚖️ Balance", f"{balance:.2f} €")

    st.subheader("💸 Ce que je dois rembourser")
    if shared_with_me.empty:
        st.success("✅ Rien à rembourser !")
    else:
        for _, row in shared_with_me.iterrows():
            parts = parse_partage(row["partage"])
            my_share = row["montant"] / (len(parts) + 1)
            payer = users.get(row["membre"], {}).get("display_name", row["membre"])
            st.markdown(f"""
            <div class="card">
                <strong>{row['categorie']}</strong> — {row['description'] or '—'}<br>
                Payé par <b>{payer}</b> · Total : {row['montant']:.2f} € ·
                <span style="color:#EF4444"><b>Votre part : {my_share:.2f} €</b></span>
            </div>
            """, unsafe_allow_html=True)

    st.subheader("💰 Ce qu'on me doit")
    if my_shared.empty:
        st.info("Aucune dépense partagée de votre côté.")
    else:
        for _, row in my_shared.iterrows():
            parts = parse_partage(row["partage"])
            their_share = row["montant"] * len(parts) / (len(parts) + 1)
            names = [users.get(user, {}).get("display_name", user) for user in parts]
            st.markdown(f"""
            <div class="card card-ok">
                <strong>{row['categorie']}</strong> — {row['description'] or '—'}<br>
                Partagé avec <b>{', '.join(names)}</b> ·
                <span style="color:#10B981"><b>Ils doivent : {their_share:.2f} €</b></span>
            </div>
            """, unsafe_allow_html=True)

    render_shell_end()


def page_budgets():
    render_shell_start()
    hero("🎯 Budgets", "Suivi visuel de chaque catégorie.")
    budgets = load_budgets()
    df = load_expenses()
    now = datetime.now()

    if not df.empty:
        df["date"] = pd.to_datetime(df["date"])
        df_month = df[(df["date"].dt.month == now.month) & (df["date"].dt.year == now.year)]
        cat_spend = df_month.groupby("categorie")["montant"].sum().to_dict()
    else:
        cat_spend = {}

    with st.expander("✏️ Définir / modifier les budgets mensuels", expanded=len(budgets) == 0):
        with st.form("budget_form"):
            new_budgets = {}
            cols = st.columns(2)
            for i, cat in enumerate(CATEGORIES):
                with cols[i % 2]:
                    val = st.number_input(cat, min_value=0.0, step=10.0, format="%.0f", value=float(budgets.get(cat, 0)), key=f"b_{cat}")
                    if val > 0:
                        new_budgets[cat] = val
            if st.form_submit_button("💾 Enregistrer les budgets", use_container_width=True, type="primary"):
                save_budgets(new_budgets)
                st.success("Budgets enregistrés !")
                st.rerun()

    if not budgets:
        st.info("Définissez vos budgets pour commencer le suivi.")
        render_shell_end()
        return

    days_in_month = calendar.monthrange(now.year, now.month)[1]
    days_elapsed = now.day
    month_pct = days_elapsed / days_in_month * 100

    st.caption(f"📅 Jour {days_elapsed}/{days_in_month} du mois ({month_pct:.0f}% écoulé)")

    total_budget = sum(budgets.values())
    total_spent = sum(cat_spend.get(c, 0) for c in budgets)
    global_pct = (total_spent / total_budget * 100) if total_budget > 0 else 0

    st.metric("💶 Budget global", f"{total_spent:.2f} € / {total_budget:.2f} €", delta=f"{total_budget - total_spent:.2f} € restants")
    st.markdown(progress_bar(global_pct), unsafe_allow_html=True)

    for cat, budget in sorted(budgets.items()):
        spent = cat_spend.get(cat, 0)
        remaining = budget - spent
        pct = (spent / budget * 100) if budget > 0 else 0
        status = "🔴 Dépassé !" if pct >= 100 else "🟡 Attention" if pct >= 75 else "✅ OK"

        st.markdown(f"""
        <div class="{card_class(pct)}">
            <div style="display:flex;justify-content:space-between;align-items:center">
                <span style="font-weight:700">{cat}</span>
                <span style="font-size:.85rem;color:#64748B">{status}</span>
            </div>
            <div style="display:flex;justify-content:space-between;margin-top:4px">
                <span><b>{spent:.2f} €</b> dépensés</span>
                <span style="color:{'#EF4444' if remaining < 0 else '#10B981'}">
                    {abs(remaining):.2f} € {'de dépassement' if remaining < 0 else 'restants'}
                </span>
            </div>
            {progress_bar(pct)}
            <div style="text-align:right;font-size:.75rem;color:#94A3B8;margin-top:2px">
                Budget : {budget:.0f} € · {pct:.0f}%
            </div>
        </div>
        """, unsafe_allow_html=True)

    render_shell_end()


def page_rapport():
    render_shell_start()
    hero("📅 Rapport mensuel", "Synthèse détaillée du mois choisi.")
    df = load_expenses()
    users = load_users()
    budgets = load_budgets()

    if df.empty:
        st.info("Aucune dépense enregistrée.")
        render_shell_end()
        return

    df["date"] = pd.to_datetime(df["date"])
    months_available = sorted(df["date"].dt.to_period("M").astype(str).unique(), reverse=True)
    selected_month = st.selectbox("📅 Choisir le mois", months_available, index=0)

    year, month = map(int, selected_month.split("-"))
    df_m = df[(df["date"].dt.month == month) & (df["date"].dt.year == year)]

    if df_m.empty:
        st.warning("Aucune dépense pour ce mois.")
        render_shell_end()
        return

    total = df_m["montant"].sum()

    c1, c2, c3 = st.columns(3)
    with c1:
        kpi_card("💶 Total dépensé", f"{total:.2f} €")
    with c2:
        kpi_card("📝 Nb transactions", str(len(df_m)))
    with c3:
        kpi_card("📆 Moyenne / jour", f"{total / max(df_m['date'].dt.day.max(), 1):.2f} €")

    st.subheader("👥 Répartition par membre")
    membre_totals = df_m.groupby("membre")["montant"].sum()
    for uname, amt in membre_totals.items():
        dname = users.get(uname, {}).get("display_name", uname)
        pct = amt / total * 100 if total > 0 else 0
        st.markdown(f"""
        <div class="card">
            <div style="display:flex;justify-content:space-between">
                <b>👤 {dname}</b>
                <b>{amt:.2f} € ({pct:.1f}%)</b>
            </div>
            {progress_bar(pct)}
        </div>
        """, unsafe_allow_html=True)

    st.subheader("🏷️ Détail par catégorie")
    cat_totals = df_m.groupby("categorie")["montant"].sum().sort_values(ascending=False)
    cols = st.columns(2)
    for i, (cat, amt) in enumerate(cat_totals.items()):
        pct_of_total = amt / total * 100 if total > 0 else 0
        budget = budgets.get(cat, 0)
        budget_line = ""
        budget_bar = ""
        if budget > 0:
            bpct = amt / budget * 100
            budget_line = f"<br><small>Budget : {budget:.0f} € · {bpct:.0f}% consommé</small>"
            budget_bar = progress_bar(bpct)

        with cols[i % 2]:
            st.markdown(f"""
            <div class="card">
                <b>{cat}</b> — {amt:.2f} € ({pct_of_total:.1f}%)
                {budget_line}
                {budget_bar}
            </div>
            """, unsafe_allow_html=True)

    st.subheader("📊 Graphiques")
    gc1, gc2 = st.columns(2)
    with gc1:
        st.bar_chart(cat_totals)
    with gc2:
        m_chart = membre_totals.copy()
        m_chart.index = [users.get(member, {}).get("display_name", member) for member in m_chart.index]
        st.bar_chart(m_chart)

    st.subheader("📈 Dépenses jour par jour")
    daily = df_m.groupby(df_m["date"].dt.day)["montant"].sum()
    daily.index = [f"J{d}" for d in daily.index]
    st.bar_chart(daily)

    st.subheader("📋 Toutes les dépenses du mois")
    display = df_m.sort_values("date", ascending=False).copy()
    display["membre"] = display["membre"].map(lambda member: users.get(member, {}).get("display_name", member))
    display["date"] = display["date"].dt.strftime("%d/%m/%Y")
    display["montant"] = display["montant"].map("{:.2f} €".format)
    st.dataframe(
        display[["date", "montant", "categorie", "description", "membre"]].rename(columns={
            "date": "Date",
            "montant": "Montant",
            "categorie": "Catégorie",
            "description": "Description",
            "membre": "Membre",
        }),
        use_container_width=True,
        hide_index=True,
    )

    csv = df_m.to_csv(index=False).encode("utf-8")
    st.download_button(
        f"⬇️ Exporter {MONTHS_FR[month]} {year} en CSV",
        csv,
        f"depenses_{year}_{month:02d}.csv",
        "text/csv",
        use_container_width=True,
    )

    render_shell_end()


def page_settings():
    render_shell_start()
    hero("⚙️ Paramètres", "Profil, membres et export global.")
    users = load_users()
    me = st.session_state.username

    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    with st.form("profile"):
        new_display = st.text_input("Prénom / Surnom", value=users[me]["display_name"])
        new_password = st.text_input("Nouveau mot de passe (vide = inchangé)", type="password")
        confirm_password = st.text_input("Confirmer", type="password")
        submitted = st.form_submit_button("💾 Mettre à jour", type="primary")

        if submitted:
            if new_display:
                users[me]["display_name"] = new_display
                st.session_state.display_name = new_display

            if new_password:
                if new_password != confirm_password:
                    st.error("Mots de passe différents")
                    st.stop()
                if len(new_password) < 6:
                    st.error("Minimum 6 caractères")
                    st.stop()
                users[me]["password"] = hash_pw(new_password)

            save_users(users)
            st.success("Profil mis à jour !")
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    if st.session_state.role == "admin":
        st.subheader("🛡️ Membres du foyer")
        for uname, udata in users.items():
            c1, c2, c3 = st.columns([3, 2, 1])
            c1.write(f"**{udata['display_name']}** (`{uname}`)")
            c2.write(udata.get("role", "membre"))
            if uname != me and c3.button("🗑️", key=f"du_{uname}"):
                del users[uname]
                save_users(users)
                st.rerun()

        st.subheader("📤 Export global")
        df = load_expenses()
        if not df.empty:
            st.download_button(
                "⬇️ Toutes les dépenses (CSV)",
                df.to_csv(index=False).encode("utf-8"),
                "depenses_foyer_complet.csv",
                "text/csv",
                use_container_width=True,
            )

    render_shell_end()


def main():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        show_login()
        return

    page = show_sidebar()

    pages = {
        "📊 Tableau de bord": page_dashboard,
        "➕ Ajouter une dépense": page_add,
        "📋 Mes dépenses": page_my_expenses,
        "👥 Dépenses partagées": page_shared,
        "🎯 Budgets": page_budgets,
        "📅 Rapport mensuel": page_rapport,
        "⚙️ Paramètres": page_settings,
    }
    pages[page]()


if __name__ == "__main__":
    main()
