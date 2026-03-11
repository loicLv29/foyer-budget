import calendar
import json
from datetime import date, datetime
from pathlib import Path

import pandas as pd
import streamlit as st

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

st.markdown("""
<style>
    .block-container { padding-top: 1rem; padding-bottom: 3rem; max-width: 1200px; }
    .app-shell {
        background: linear-gradient(180deg, #F8FAFC 0%, #EEF2F7 100%);
        border-radius: 22px; padding: 1.1rem; margin-bottom: 1rem;
        border: 1px solid rgba(15, 23, 42, 0.06);
    }
    .hero {
        background: linear-gradient(135deg, #0F172A 0%, #1D4ED8 55%, #38BDF8 100%);
        color: white; border-radius: 22px; padding: 1.4rem 1.3rem; margin-bottom: 1rem;
        box-shadow: 0 10px 30px rgba(37, 99, 235, 0.18);
    }
    .hero-title { font-size: 2rem; font-weight: 800; line-height: 1.05; margin: 0; }
    .hero-sub { margin-top: .45rem; color: rgba(255,255,255,.88); font-size: .98rem; }
    .glass-card {
        background: rgba(255,255,255,.86); backdrop-filter: blur(8px);
        border-radius: 18px; padding: 1rem; border: 1px solid rgba(15, 23, 42, 0.06);
        box-shadow: 0 6px 20px rgba(15, 23, 42, 0.06); margin-bottom: .9rem;
    }
    .kpi-card {
        background: white; border-radius: 18px; padding: 1rem;
        border: 1px solid rgba(15, 23, 42, 0.06);
        box-shadow: 0 4px 16px rgba(15, 23, 42, 0.06);
    }
    .kpi-label { color: #64748B; font-size: .86rem; margin-bottom: .2rem; }
    .kpi-value { font-size: 1.6rem; font-weight: 800; color: #0F172A; }
    .expense-card {
        background: white; border-radius: 16px; padding: .95rem 1rem;
        border: 1px solid rgba(15, 23, 42, 0.06);
        box-shadow: 0 4px 14px rgba(15, 23, 42, 0.05); margin-bottom: .75rem;
    }
    .expense-top { display: flex; justify-content: space-between; align-items: center; gap: .8rem; }
    .expense-cat { font-weight: 700; color: #0F172A; }
    .expense-amt { font-weight: 800; color: #111827; }
    .expense-meta { margin-top: .35rem; font-size: .9rem; color: #64748B; }
    .prog-wrap { background:#E5E7EB; border-radius:999px; height:10px; margin-top:8px; overflow:hidden; }
    .prog-fill { height:10px; border-radius:999px; transition: width .4s; }
    .card {
        background: white; border-radius: 16px; padding: 1rem; margin-bottom: .8rem;
        border-left: 4px solid #2563EB; border: 1px solid rgba(15, 23, 42, 0.06);
        box-shadow: 0 4px 14px rgba(15, 23, 42, 0.05);
    }
    .card-warn { border-left-color: #F59E0B; }
    .card-danger { border-left-color: #EF4444; }
    .card-ok { border-left-color: #10B981; }
</style>
""", unsafe_allow_html=True)


def load_users():
    if not USERS_FILE.exists():
        return {}
    raw = USERS_FILE.read_text(encoding="utf-8").strip()
    if not raw:
        return {}
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else {}
    except json.JSONDecodeError:
        return {}


def save_users(users):
    USERS_FILE.write_text(json.dumps(users, ensure_ascii=False, indent=2), encoding="utf-8")


def load_budgets():
    if not BUDGETS_FILE.exists():
        return {}
    raw = BUDGETS_FILE.read_text(encoding="utf-8").strip()
    if not raw:
        return {}
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else {}
    except json.JSONDecodeError:
        return {}


def save_budgets(budgets):
    BUDGETS_FILE.write_text(json.dumps(budgets, ensure_ascii=False, indent=2), encoding="utf-8")


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
            df["membre"] = "inconnu"
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
    save_expenses(pd.concat([df, row], ignore_index=True))


def delete_expense(eid):
    df = load_expenses()
    save_expenses(df[df["id"] != eid])


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


def current_user():
    if st.session_state.get("authenticated") is not True:
        return None

    display_name = st.session_state.get("display_name", "Invite")
    username = st.session_state.get("username", "guest")

    users = load_users()
    if username not in users:
        users[username] = {
            "display_name": display_name,
            "role": "admin" if len(users) == 0 else "membre",
            "created_at": datetime.now().isoformat(),
        }
        save_users(users)

    return {
        "username": username,
        "display_name": users[username].get("display_name", display_name),
        "role": users[username].get("role", "membre"),
    }


def show_login():
    hero("🏠 FoyerBudget", "Entrez le mot de passe secret pour acceder a l'application.")
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)

    with st.form("secret_login"):
        display_name = st.text_input("Prenom / surnom", placeholder="Ex: Loic")
        password = st.text_input("Mot de passe", type="password")
        submitted = st.form_submit_button("Entrer", use_container_width=True, type="primary")

        if submitted:
            expected_password = st.secrets["app_password"]
            if password == expected_password:
                safe_name = (display_name or "Invite").strip()
                safe_key = safe_name.lower().replace(" ", "_")
                st.session_state["authenticated"] = True
                st.session_state["display_name"] = safe_name
                st.session_state["username"] = safe_key
                st.rerun()
            else:
                st.error("Mot de passe incorrect")

    st.markdown('</div>', unsafe_allow_html=True)


def show_sidebar():
    with st.sidebar:
        st.markdown("## 🏠 FoyerBudget")
        st.caption(f"Connecte : {st.session_state.display_name}")
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
            for key in ["authenticated", "display_name", "username", "role"]:
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
        st.info("🎉 Commencez par ajouter une depense.")
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
        kpi_card("👤 Mes depenses", f"{df_mine['montant'].sum():.2f} €")
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
        st.subheader("🏷️ Par categorie")
        cat_data = df_month.groupby("categorie")["montant"].sum().sort_values(ascending=False)
        if not cat_data.empty:
            st.bar_chart(cat_data)

    with col_b:
        st.subheader("👥 Par membre")
        m_data = df_month.groupby("membre")["montant"].sum()
        m_data.index = [users.get(member, {}).get("display_name", member) for member in m_data.index]
        if not m_data.empty:
            st.bar_chart(m_data)

    st.subheader("📈 Evolution mensuelle")
    df["mois"] = df["date"].dt.to_period("M").astype(str)
    monthly = df.groupby("mois")["montant"].sum().reset_index()
    monthly.columns = ["Mois", "Total (€)"]
    st.line_chart(monthly.set_index("Mois"))

    st.subheader("🕐 Dernieres depenses")
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
    hero("➕ Ajouter une depense", "Saisie rapide.")
    users = load_users()
    members = {key: value["display_name"] for key, value in users.items()}

    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    with st.form("add_form"):
        c1, c2 = st.columns(2)
        with c1:
            date_val = st.date_input("📅 Date", value=date.today())
            montant = st.number_input("💶 Montant (€)", min_value=0.01, step=0.01, format="%.2f")
            categorie = st.selectbox("🏷️ Categorie", CATEGORIES)
        with c2:
            description = st.text_input("📝 Description", placeholder="Ex: Carrefour drive")
            others = [key for key in members if key != st.session_state.username]
            partage = st.multiselect("👥 Partager avec", options=others, format_func=lambda x: members[x])

        if st.form_submit_button("✅ Enregistrer", use_container_width=True, type="primary"):
            add_expense(date_val, montant, categorie, description, st.session_state.username, partage)
            st.success(f"{montant:.2f} € enregistres.")
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    render_shell_end()


def page_my_expenses():
    render_shell_start()
    hero("📋 Mes depenses", "Historique personnel.")
    df = load_expenses()
    df = df[df["membre"] == st.session_state.username].copy()

    if df.empty:
        st.info("Aucune depense enregistree pour vous.")
        render_shell_end()
        return

    df["date"] = pd.to_datetime(df["date"])
    c1, c2, c3 = st.columns(3)
    months = sorted(df["date"].dt.to_period("M").astype(str).unique(), reverse=True)
    month_filter = c1.selectbox("📅 Mois", ["Tous"] + list(months))
    category_filter = c2.selectbox("🏷️ Categorie", ["Toutes"] + CATEGORIES)
    sort_by = c3.selectbox("🔃 Trier par", ["Date (recent)", "Montant ↓"])

    if month_filter != "Tous":
        df = df[df["date"].dt.to_period("M").astype(str) == month_filter]
    if category_filter != "Toutes":
        df = df[df["categorie"] == category_filter]

    df = df.sort_values("date" if sort_by.startswith("Date") else "montant", ascending=False)

    k1, k2 = st.columns(2)
    with k1:
        kpi_card("💶 Total filtre", f"{df['montant'].sum():.2f} €")
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
    hero("👥 Depenses partagees", "Remboursements et equilibre.")
    df = load_expenses()
    me = st.session_state.username

    if df.empty:
        st.info("Aucune depense enregistree.")
        render_shell_end()
        return

    shared_with_me = df[df["partage"].apply(lambda x: me in parse_partage(x))].copy()
    my_shared = df[(df["membre"] == me) & (df["partage"].apply(lambda x: bool(parse_partage(x))))].copy()

    owed_by_me = sum(row["montant"] / (len(parse_partage(row["partage"])) + 1) for _, row in shared_with_me.iterrows())
    owed_to_me = sum(row["montant"] - row["montant"] / (len(parse_partage(row["partage"])) + 1) for _, row in my_shared.iterrows())
    balance = owed_to_me - owed_by_me

    c1, c2, c3 = st.columns(3)
    with c1:
        kpi_card("💸 Je dois", f"{owed_by_me:.2f} €")
    with c2:
        kpi_card("💰 On me doit", f"{owed_to_me:.2f} €")
    with c3:
        kpi_card("⚖️ Balance", f"{balance:.2f} €")

    render_shell_end()


def page_budgets():
    render_shell_start()
    hero("🎯 Budgets", "Suivi par categorie.")
    budgets = load_budgets()
    df = load_expenses()
    now = datetime.now()

    if not df.empty:
        df["date"] = pd.to_datetime(df["date"])
        df_month = df[(df["date"].dt.month == now.month) & (df["date"].dt.year == now.year)]
        cat_spend = df_month.groupby("categorie")["montant"].sum().to_dict()
    else:
        cat_spend = {}

    with st.expander("✏️ Definir / modifier les budgets mensuels", expanded=len(budgets) == 0):
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
                st.success("Budgets enregistres !")
                st.rerun()

    if not budgets:
        st.info("Definissez vos budgets pour commencer le suivi.")
        render_shell_end()
        return

    days_in_month = calendar.monthrange(now.year, now.month)[1]
    days_elapsed = now.day
    month_pct = days_elapsed / days_in_month * 100
    st.caption(f"📅 Jour {days_elapsed}/{days_in_month} du mois ({month_pct:.0f}% ecoule)")

    total_budget = sum(budgets.values())
    total_spent = sum(cat_spend.get(c, 0) for c in budgets)
    global_pct = (total_spent / total_budget * 100) if total_budget > 0 else 0

    st.metric("💶 Budget global", f"{total_spent:.2f} € / {total_budget:.2f} €", delta=f"{total_budget - total_spent:.2f} € restants")
    st.markdown(progress_bar(global_pct), unsafe_allow_html=True)

    for cat, budget in sorted(budgets.items()):
        spent = cat_spend.get(cat, 0)
        remaining = budget - spent
        pct = (spent / budget * 100) if budget > 0 else 0
        status = "🔴 Depasse !" if pct >= 100 else "🟡 Attention" if pct >= 75 else "✅ OK"

        st.markdown(f"""
        <div class="{card_class(pct)}">
            <div style="display:flex;justify-content:space-between;align-items:center">
                <span style="font-weight:700">{cat}</span>
                <span style="font-size:.85rem;color:#64748B">{status}</span>
            </div>
            <div style="display:flex;justify-content:space-between;margin-top:4px">
                <span><b>{spent:.2f} €</b> depenses</span>
                <span style="color:{'#EF4444' if remaining < 0 else '#10B981'}">
                    {abs(remaining):.2f} € {'de depassement' if remaining < 0 else 'restants'}
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
    hero("📅 Rapport mensuel", "Synthese detaillee du mois.")
    df = load_expenses()

    if df.empty:
        st.info("Aucune depense enregistree.")
        render_shell_end()
        return

    df["date"] = pd.to_datetime(df["date"])
    months_available = sorted(df["date"].dt.to_period("M").astype(str).unique(), reverse=True)
    selected_month = st.selectbox("📅 Choisir le mois", months_available, index=0)

    year, month = map(int, selected_month.split("-"))
    df_m = df[(df["date"].dt.month == month) & (df["date"].dt.year == year)]

    if df_m.empty:
        st.warning("Aucune depense pour ce mois.")
        render_shell_end()
        return

    total = df_m["montant"].sum()

    c1, c2, c3 = st.columns(3)
    with c1:
        kpi_card("💶 Total depense", f"{total:.2f} €")
    with c2:
        kpi_card("📝 Nb transactions", str(len(df_m)))
    with c3:
        kpi_card("📆 Moyenne / jour", f"{total / max(df_m['date'].dt.day.max(), 1):.2f} €")

    render_shell_end()


def page_settings():
    render_shell_start()
    hero("⚙️ Parametres", "Profil et export.")
    users = load_users()
    me = st.session_state.username

    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    with st.form("profile"):
        new_display = st.text_input("Prenom / surnom", value=users[me]["display_name"])
        if st.form_submit_button("💾 Mettre a jour", type="primary"):
            if new_display:
                users[me]["display_name"] = new_display
                st.session_state.display_name = new_display
            save_users(users)
            st.success("Profil mis a jour !")
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    render_shell_end()


def main():
    user = current_user()

    if not user:
        show_login()
        return

    st.session_state.username = user["username"]
    st.session_state.display_name = user["display_name"]
    st.session_state.role = user["role"]

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
