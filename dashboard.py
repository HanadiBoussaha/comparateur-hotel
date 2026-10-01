# ============================================================
# DASHBOARD - COMPARATEUR INTELLIGENT D'HÔTELS (V3)
# Affiche EXACTEMENT les scores et sentiments produits par
# l'analyseur (CSV). Aucun seuil, aucun recalcul de sentiment.
# ============================================================

import os
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Comparateur intelligent d'hôtels",
    page_icon="🏨",
    layout="wide"
)

CSV_PATH = "data/avis_theme_sentiment.csv"

# ============================================================
# STYLE
# ============================================================

st.markdown(
    """
    <style>
    .main-title {
        font-size: 36px; font-weight: 800; margin-bottom: 4px;
        background: linear-gradient(90deg, #1a56db, #0e9f6e);
        -webkit-background-clip: text;
        
    }
    .subtitle { font-size: 17px; color: #666; margin-bottom: 20px; }
    .section-title {
        font-size: 22px; font-weight: 700; margin-top: 28px;
        margin-bottom: 12px; padding-bottom: 6px;
        border-bottom: 2px solid #eef2f7;
    }
    .winner-box {
        background: linear-gradient(135deg, #0e9f6e18, #1a56db18);
        border: 2px solid #0e9f6e; border-radius: 14px;
        padding: 20px 24px; margin: 10px 0;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown(
    '<div class="main-title">🏨 Comparateur intelligent d’hôtels</div>',
    unsafe_allow_html=True
)
st.markdown(
    '<div class="subtitle">Analyse automatique des avis clients par thème '
    'et sentiment — avec recommandation personnalisée</div>',
    unsafe_allow_html=True
)

# ============================================================
# CHARGEMENT
# ============================================================

if not os.path.exists(CSV_PATH):
    st.error(f"Fichier introuvable : {CSV_PATH}")
    st.stop()

df = pd.read_csv(CSV_PATH)

required = ["hotel_id", "review_id", "theme", "sentiment", "score"]
missing = [c for c in required if c not in df.columns]
if missing:
    st.error("Colonnes manquantes : " + ", ".join(missing))
    st.stop()

# ============================================================
# NORMALISATION (uniquement le format, pas les valeurs)
# ============================================================

df["hotel_id"] = df["hotel_id"].astype(str).str.strip()
df["theme"] = df["theme"].astype(str).str.strip()
df["sentiment"] = df["sentiment"].astype(str).str.strip().str.lower()
df["score"] = pd.to_numeric(df["score"], errors="coerce")
df = df.dropna(subset=["score"])

# Simple harmonisation des libellés : la valeur du sentiment
# reste celle fournie par l'analyseur.
sentiment_map = {
    "pos": "positive", "positif": "positive", "positive": "positive",
    "neg": "negative", "negatif": "negative", "négatif": "negative",
    "negative": "negative",
    "neu": "neutral", "neutre": "neutral", "neutral": "neutral",
}
df["sentiment"] = df["sentiment"].map(sentiment_map).fillna(df["sentiment"])

if "phrases" not in df.columns:
    df["phrases"] = ""

SENT_EMOJI = {"positive": "🟢", "negative": "🔴", "neutral": "⚪"}
SENT_LABEL = {
    "positive": "🟢 Positif",
    "negative": "🔴 Négatif",
    "neutral": "⚪ Neutre",
}


def main_sentiment(series):
    """Sentiment le plus fréquent dans le CSV (aucun seuil appliqué)."""
    m = series.mode()
    return m.iloc[0] if not m.empty else "neutral"


# ============================================================
# HÔTELS DISPONIBLES
# ============================================================

hotel_ids = sorted(df["hotel_id"].unique().tolist())
available_themes = set(df["theme"].dropna().unique())

if not hotel_ids:
    st.warning("Aucun hôtel disponible.")
    st.stop()

# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.header("⚙️ Paramètres")

selected_hotels = st.sidebar.multiselect(
    "Sélectionner les hôtels",
    hotel_ids,
    default=hotel_ids[:3],
    max_selections=3
)

st.sidebar.markdown("---")
st.sidebar.subheader("🎯 Préférences du client")

activite_choices = {
    "Sport & activités": "sport_activites",
    "Piscine": "piscine",
    "Plage": "plage",
    "Animation & divertissement": "animation",
}
sel_activites = st.sidebar.multiselect(
    "Activités souhaitées", list(activite_choices.keys()), default=[]
)

voyage_map = {
    "Indifférent": [],
    "Famille": ["famille", "animation", "piscine"],
    "Couple": ["couple", "spa et bien être", "ambiance", "chambre"],
    "Seul / solo": ["seul", "ambiance", "emplacement"],
}
sel_voyage = st.sidebar.selectbox("Type de voyage", list(voyage_map.keys()))

bienetre_choices = {
    "Spa & bien-être": "spa et bien être",
    "Équipements": "équipements",
    "Climatisation": "climatisation",
}
sel_bienetre = st.sidebar.multiselect(
    "Confort & bien-être", list(bienetre_choices.keys()), default=[]
)

sel_budget = st.sidebar.selectbox(
    "Budget / rapport qualité-prix",
    ["Peu importe", "Rapport qualité-prix important"]
)

strategy = st.sidebar.radio(
    "Stratégie de recommandation",
    ["⭐ Meilleure qualité d'avis",
     "🧩 Meilleure couverture des préférences"]
)

# ============================================================
# CONSTRUCTION DES PRÉFÉRENCES
# ============================================================

requested_themes = []
requested_themes += [activite_choices[k] for k in sel_activites]
requested_themes += voyage_map[sel_voyage]
requested_themes += [bienetre_choices[k] for k in sel_bienetre]
if sel_budget == "Rapport qualité-prix important":
    requested_themes.append("rapport qualité-prix")

requested_themes = list(dict.fromkeys(requested_themes))

pref_themes = [t for t in requested_themes if t in available_themes]
missing_pref_themes = [t for t in requested_themes
                       if t not in available_themes]

if missing_pref_themes:
    st.sidebar.warning(
        "Certains thèmes demandés ne sont pas présents dans les données "
        "analysées : " + ", ".join(missing_pref_themes)
    )

if not selected_hotels:
    st.warning("Sélectionnez au moins un hôtel.")
    st.stop()

df_selected = df[df["hotel_id"].isin(selected_hotels)].copy()

# ============================================================
# RECOMMANDATION
# (utilise les scores du CSV, sans modifier le sentiment)
# ============================================================

if pref_themes:

    st.markdown(
        '<div class="section-title">'
        '🎯 Hôtel recommandé selon vos préférences</div>',
        unsafe_allow_html=True
    )
    st.caption("Thèmes pris en compte : " + ", ".join(pref_themes))

    ranking = []

    for hid in selected_hotels:
        sub = df_selected[df_selected["hotel_id"] == hid]
        scores, found_themes = [], []

        for th in pref_themes:
            rows = sub[sub["theme"] == th]
            if not rows.empty:
                scores.append(float(rows["score"].mean()))
                found_themes.append(th)

        if scores:
            mean_score = float(pd.Series(scores).mean())
            coverage = len(found_themes) / len(pref_themes)
        else:
            mean_score, coverage = 0.0, 0.0

        if "Meilleure couverture" in strategy:
            final_score = mean_score * coverage
        else:
            final_score = mean_score - 0.10 * (1 - coverage)

        ranking.append({
            "hotel_id": hid,
            "score_pref": float(final_score),
            "score_brut": float(mean_score),
            "couverture": float(coverage),
            "themes_ok": found_themes,
        })

    ranking.sort(key=lambda x: x["score_pref"], reverse=True)
    winner = ranking[0]

    col_w1, col_w2, col_w3 = st.columns([2, 1, 1])

    with col_w1:
        st.markdown(
            f'<div class="winner-box">'
            f'<div style="font-size:15px;color:#555;">🏆 Hôtel le plus adapté</div>'
            f'<div style="font-size:28px;font-weight:800;">'
            f'Hôtel {winner["hotel_id"]}</div>'
            f'<div style="font-size:14px;color:#444;margin-top:6px;">'
            f'Score préférence : <b>{winner["score_pref"]:+.2f}</b> '
            f'({len(winner["themes_ok"])} thème(s) analysé(s))</div>'
            f'</div>',
            unsafe_allow_html=True
        )

    with col_w2:
        st.metric("Score du gagnant", f'{winner["score_pref"]:+.2f}')

    with col_w3:
        st.metric(
            "2ᵉ choix",
            f'Hôtel {ranking[1]["hotel_id"]}' if len(ranking) > 1 else "—"
        )

    st.caption(
        f"Qualité moyenne des thèmes analysés : {winner['score_brut']:+.2f}"
        f" — Couverture : {len(winner['themes_ok'])}/{len(pref_themes)}"
    )

    rank_df = pd.DataFrame([
        {
            "Rang": i + 1,
            "Hôtel": f"Hôtel {r['hotel_id']}",
            "Score préférence": round(r["score_pref"], 3),
            "Qualité moyenne": round(r["score_brut"], 3),
            "Thèmes couverts": f'{len(r["themes_ok"])}/{len(pref_themes)}',
            "Points forts (thèmes)": (
                ", ".join(r["themes_ok"][:5]) if r["themes_ok"] else "—"
            ),
        }
        for i, r in enumerate(ranking)
    ])
    st.dataframe(rank_df, use_container_width=True, hide_index=True)

    chart = pd.DataFrame(
        {f"Hôtel {r['hotel_id']}": r["score_pref"] for r in ranking},
        index=["Score préférence"]
    ).T
    st.bar_chart(chart, color="#1a56db")

else:
    st.info(
        "Sélectionnez au moins une préférence pour obtenir "
        "une recommandation personnalisée."
    )

# ============================================================
# KPI GÉNÉRAUX (sentiment du CSV)
# ============================================================

st.markdown('<div class="section-title">📊 Vue d’ensemble</div>',
            unsafe_allow_html=True)

c1, c2, c3, c4 = st.columns(4)
c1.metric("🏨 Hôtels", len(selected_hotels))
c2.metric("📝 Avis analysés", df_selected["review_id"].nunique())
c3.metric("🟢 Positifs",
          int(df_selected["sentiment"].eq("positive").sum()))
c4.metric("🔴 Négatifs",
          int(df_selected["sentiment"].eq("negative").sum()))

# ============================================================
# COMPARAISON PAR THÈME
# ============================================================

st.markdown('<div class="section-title">🔎 Comparaison par thème</div>',
            unsafe_allow_html=True)

themes = sorted(df_selected["theme"].dropna().unique())


def cell_data(hid, theme):
    """Score et sentiment tels qu'ils sont dans le CSV."""
    rows = df_selected[
        (df_selected["hotel_id"] == hid) & (df_selected["theme"] == theme)
    ]
    if rows.empty:
        return None
    pos = int((rows["sentiment"] == "positive").sum())
    neg = int((rows["sentiment"] == "negative").sum())
    neu = int((rows["sentiment"] == "neutral").sum())
    if len(rows) == 1:
        return float(rows["score"].iloc[0]), rows["sentiment"].iloc[0], ""
    # Couleur : sentiment dominant parmi les avis (aucun seuil)
    dominant = max([("positive", pos), ("negative", neg), ("neutral", neu)],
                   key=lambda t: t[1])[0]
    return (float(rows["score"].mean()), dominant,
            f" (🟢{pos} ⚪{neu} 🔴{neg})")


table_rows = []
for th in themes:
    row = {"Thème": th}
    for hid in selected_hotels:
        data = cell_data(hid, th)
        if data is None:
            row[f"Hôtel {hid}"] = "—"
        else:
            score, sent, detail = data
            row[f"Hôtel {hid}"] = (
                f"{SENT_EMOJI.get(sent, '⚪')} {score:+.2f}{detail}"
            )
    table_rows.append(row)

table_df = pd.DataFrame(table_rows)


def color_sent(v):
    # Couleur selon le premier emoji (le sentiment de la cellule)
    if isinstance(v, str):
        if v.startswith("🟢"):
            return "background-color: #d9f2e3"
        if v.startswith("🔴"):
            return "background-color: #fbdcdc"
        if v.startswith("⚪"):
            return "background-color: #eeeeee"
    return ""


try:
    styled_table = table_df.style.map(color_sent)
except AttributeError:
    styled_table = table_df.style.applymap(color_sent)

st.dataframe(styled_table, use_container_width=True, hide_index=True)

# ============================================================
# GRAPHIQUE DES SCORES PAR THÈME
# ============================================================

st.markdown(
    '<div class="section-title">📈 Scores de sentiment par thème</div>',
    unsafe_allow_html=True
)

chart_df = (
    df_selected.groupby(["theme", "hotel_id"])["score"].mean().unstack()
)
st.bar_chart(chart_df)

# ============================================================
# DÉTAIL PAR HÔTEL
# ============================================================

st.markdown('<div class="section-title">🏨 Détail par hôtel</div>',
            unsafe_allow_html=True)

hotel_to_view = st.selectbox("Choisir un hôtel", selected_hotels)
hotel_df = df_selected[df_selected["hotel_id"] == hotel_to_view].copy()

# Chaque occurrence est affichée séparément, telle qu'elle est dans le CSV
# (aucune moyenne, aucun regroupement, aucun recalcul).
occ = hotel_df.sort_values(["theme", "score"], ascending=[True, False]).copy()

n_pos = int((occ["sentiment"] == "positive").sum())
n_neg = int((occ["sentiment"] == "negative").sum())
n_neu = int((occ["sentiment"] == "neutral").sum())

st.caption(
    f"{len(occ)} occurrence(s) : {n_pos} positive(s) | "
    f"{n_neg} négative(s) | {n_neu} neutre(s)"
)

occ["Sentiment"] = occ["sentiment"].map(
    lambda v: SENT_LABEL.get(v, "⚪ Neutre")
)
occ["Score"] = occ["score"].round(2)

occ_view = occ.rename(columns={
    "theme": "Thème",
    "review_id": "Avis",
    "phrases": "Phrase(s) analysée(s)",
})[["Thème", "Sentiment", "Score", "Avis", "Phrase(s) analysée(s)"]]


def color_row(row):
    s = row["Sentiment"]
    if s.startswith("🟢"):
        c = "background-color: #d9f2e3"
    elif s.startswith("🔴"):
        c = "background-color: #fbdcdc"
    else:
        c = "background-color: #eeeeee"
    return [c] * len(row)


st.dataframe(
    occ_view.style.apply(color_row, axis=1),
    use_container_width=True,
    hide_index=True
)

# ============================================================
# DÉTAIL DES AVIS ANALYSÉS (valeurs brutes du CSV)
# ============================================================

st.markdown('<div class="section-title">📝 Détail des avis analysés</div>',
            unsafe_allow_html=True)

f1, f2 = st.columns(2)

with f1:
    theme_filter = st.selectbox(
        "Filtrer par thème",
        ["Tous"] + sorted(df_selected["theme"].dropna().unique().tolist())
    )

with f2:
    sentiment_filter = st.selectbox(
        "Filtrer par sentiment",
        ["Tous", "positive", "negative", "neutral"]
    )

details = df_selected.copy()

if theme_filter != "Tous":
    details = details[details["theme"] == theme_filter]

if sentiment_filter != "Tous":
    details = details[details["sentiment"] == sentiment_filter]

display_columns = [
    c for c in ["hotel_id", "review_id", "language", "theme",
                "sentiment", "score", "phrases"]
    if c in details.columns
]

st.dataframe(details[display_columns],
             use_container_width=True, hide_index=True)

# ============================================================
# MÉTHODOLOGIE
# ============================================================

st.markdown('<div class="section-title">ℹ️ Méthodologie</div>',
            unsafe_allow_html=True)

st.info(
    """
Les avis sont analysés automatiquement :

- détection des thèmes par mots-clés (+ modèle sémantique en secours)
- analyse du sentiment par fenêtre d'aspect
- agrégation des scores par thème et par hôtel

Le dashboard affiche **exactement** les scores et sentiments produits
par l'analyseur, sans recalcul ni seuil supplémentaire.

Un thème absent des avis n'est **pas considéré comme négatif** :
il est simplement indiqué comme non documenté.

La **couverture** indique la proportion des préférences pour lesquelles
l'hôtel dispose effectivement d'avis analysés.

La stratégie « Meilleure qualité d'avis » privilégie le score moyen des
thèmes disponibles avec une légère pénalité de couverture.

La stratégie « Meilleure couverture des préférences » combine le score
moyen et la couverture des thèmes.
"""
)

st.markdown("---")
st.caption(
    "Prototype — Analyse automatique des avis hôteliers par thème et sentiment"
)
