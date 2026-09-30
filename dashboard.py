# ============================================================
# DASHBOARD - COMPARATEUR INTELLIGENT D'HÔTELS
# Analyse automatique des avis par thème et sentiment
# ============================================================

import os
import pandas as pd
import streamlit as st


# ============================================================
# CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Comparateur intelligent d'hôtels",
    page_icon="🏨",
    layout="wide"
)

CSV_PATH = "data/avis_theme_sentiment.csv"


# ============================================================
# STYLE
# ============================================================

st.markdown("""
<style>

.main-title {
    font-size: 34px;
    font-weight: 700;
    margin-bottom: 5px;
}

.subtitle {
    font-size: 17px;
    color: #666;
    margin-bottom: 25px;
}

.section-title {
    font-size: 24px;
    font-weight: 650;
    margin-top: 30px;
    margin-bottom: 15px;
}

.positive {
    color: #16803c;
    font-weight: 700;
}

.negative {
    color: #c62828;
    font-weight: 700;
}

.neutral {
    color: #777;
    font-weight: 700;
}

.score {
    font-weight: 600;
}

</style>
""", unsafe_allow_html=True)


# ============================================================
# TITRE
# ============================================================

st.markdown(
    '<div class="main-title">🏨 Comparateur intelligent d’hôtels</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">'
    'Analyse automatique des avis clients par thème et sentiment'
    '</div>',
    unsafe_allow_html=True
)


# ============================================================
# CHARGEMENT DES DONNÉES
# ============================================================

if not os.path.exists(CSV_PATH):
    st.error(f"Fichier introuvable : {CSV_PATH}")
    st.stop()

df = pd.read_csv(CSV_PATH)


# ============================================================
# VERIFICATION DES COLONNES
# ============================================================

required_columns = [
    "hotel_id",
    "review_id",
    "theme",
    "sentiment",
    "score"
]

missing = [c for c in required_columns if c not in df.columns]

if missing:
    st.error(
        "Colonnes manquantes dans le CSV : "
        + ", ".join(missing)
    )
    st.stop()


# ============================================================
# NORMALISATION
# ============================================================

df["hotel_id"] = df["hotel_id"].astype(str)
df["theme"] = df["theme"].astype(str)
df["sentiment"] = df["sentiment"].astype(str).str.lower()

df["score"] = pd.to_numeric(
    df["score"],
    errors="coerce"
)

df = df.dropna(subset=["score"])


# ============================================================
# LISTE DES HÔTELS
# ============================================================

hotel_ids = sorted(df["hotel_id"].unique().tolist())


if len(hotel_ids) == 0:
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

if not selected_hotels:
    st.warning("Sélectionnez au moins un hôtel.")
    st.stop()


df_selected = df[
    df["hotel_id"].isin(selected_hotels)
].copy()


# ============================================================
# STATISTIQUES GÉNÉRALES
# ============================================================

st.markdown(
    '<div class="section-title">📊 Vue d’ensemble</div>',
    unsafe_allow_html=True
)

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "🏨 Hôtels sélectionnés",
    len(selected_hotels)
)

col2.metric(
    "📝 Avis analysés",
    df_selected["review_id"].nunique()
)

col3.metric(
    "🏷️ Thèmes détectés",
    df_selected["theme"].nunique()
)

positive_count = (
    df_selected["sentiment"]
    .eq("positive")
    .sum()
)

negative_count = (
    df_selected["sentiment"]
    .eq("negative")
    .sum()
)

neutral_count = (
    df_selected["sentiment"]
    .eq("neutral")
    .sum()
)


# ============================================================
# SENTIMENT GLOBAL
# ============================================================

st.markdown(
    '<div class="section-title">😊 Répartition des sentiments</div>',
    unsafe_allow_html=True
)

c1, c2, c3 = st.columns(3)

c1.metric(
    "🟢 Positifs",
    positive_count
)

c2.metric(
    "🔴 Négatifs",
    negative_count
)

c3.metric(
    "⚪ Neutres",
    neutral_count
)


# ============================================================
# COMPARAISON PAR THÈME
# ============================================================

st.markdown(
    '<div class="section-title">🔎 Comparaison des hôtels par thème</div>',
    unsafe_allow_html=True
)

st.caption(
    "Le sentiment et le score sont calculés automatiquement "
    "à partir de l'analyse des avis clients."
)


themes = sorted(df_selected["theme"].unique())


# ============================================================
# FONCTION AFFICHAGE
# ============================================================

def format_result(hotel_id, theme):

    rows = df_selected[
        (df_selected["hotel_id"] == hotel_id)
        &
        (df_selected["theme"] == theme)
    ]

    if rows.empty:
        return "—"

    score = rows["score"].mean()

    # Sentiment majoritaire
    sentiment_counts = rows["sentiment"].value_counts()

    sentiment = sentiment_counts.index[0]

    if sentiment == "positive":
        emoji = "🟢"
        label = "Positif"

    elif sentiment == "negative":
        emoji = "🔴"
        label = "Négatif"

    else:
        emoji = "⚪"
        label = "Neutre"

    return f"{emoji} {label}  \n**{score:+.2f}**"


# ============================================================
# TABLEAU COMPARATIF
# ============================================================

comparison = []

for theme in themes:

    row = {
        "Thème": theme
    }

    for hotel_id in selected_hotels:

        row[f"Hôtel {hotel_id}"] = format_result(
            hotel_id,
            theme
        )

    comparison.append(row)


comparison_df = pd.DataFrame(comparison)


st.dataframe(
    comparison_df,
    use_container_width=True,
    hide_index=True
)


# ============================================================
# GRAPHIQUE DES SCORES
# ============================================================

st.markdown(
    '<div class="section-title">📈 Scores de sentiment par thème</div>',
    unsafe_allow_html=True
)

chart_df = (
    df_selected
    .groupby(["theme", "hotel_id"])["score"]
    .mean()
    .unstack()
)

st.bar_chart(chart_df)


# ============================================================
# DÉTAIL PAR HÔTEL
# ============================================================

st.markdown(
    '<div class="section-title">🏨 Détail par hôtel</div>',
    unsafe_allow_html=True
)

hotel_to_view = st.selectbox(
    "Choisir un hôtel",
    selected_hotels
)

hotel_df = df_selected[
    df_selected["hotel_id"] == hotel_to_view
].copy()


# ============================================================
# MATRICE DE L'HÔTEL
# ============================================================
# ============================================================
# MATRICE DE L'HÔTEL + PHRASES
# ============================================================

hotel_summary = (
    hotel_df
    .groupby("theme")
    .agg(
        score=("score", "mean"),
        sentiment=("sentiment", "first"),
        occurrences=("theme", "count"),
        phrases=("phrases", lambda x: " | ".join(
            str(v) for v in x if pd.notna(v)
        ))
    )
    .reset_index()
)

hotel_summary["score"] = hotel_summary["score"].round(2)


def sentiment_display(value):

    if value == "positive":
        return "🟢 Positif"

    if value == "negative":
        return "🔴 Négatif"

    return "⚪ Neutre"


hotel_summary["sentiment"] = (
    hotel_summary["sentiment"]
    .apply(sentiment_display)
)


hotel_summary = hotel_summary.rename(
    columns={
        "theme": "Thème",
        "score": "Score",
        "sentiment": "Sentiment",
        "occurrences": "Occurrences",
        "phrases": "Phrase(s) analysée(s)"
    }
)


# Réorganisation des colonnes
hotel_summary = hotel_summary[
    [
        "Thème",
        "Sentiment",
        "Score",
        "Occurrences",
        "Phrase(s) analysée(s)"
    ]
]


st.dataframe(
    hotel_summary,
    use_container_width=True,
    hide_index=True
)

# ============================================================
# DÉTAIL DES AVIS
# ============================================================

st.markdown(
    '<div class="section-title">📝 Détail des avis analysés</div>',
    unsafe_allow_html=True
)


# Filtres

f1, f2 = st.columns(2)

with f1:

    theme_filter = st.selectbox(
        "Filtrer par thème",
        ["Tous"] + sorted(
            hotel_df["theme"].unique().tolist()
        )
    )

with f2:

    sentiment_filter = st.selectbox(
        "Filtrer par sentiment",
        ["Tous", "positive", "negative", "neutral"]
    )


details = hotel_df.copy()


if theme_filter != "Tous":

    details = details[
        details["theme"] == theme_filter
    ]


if sentiment_filter != "Tous":

    details = details[
        details["sentiment"] == sentiment_filter
    ]


# ============================================================
# COLONNES À AFFICHER
# ============================================================

display_columns = []

for column in [
    "review_id",
    "rating",
    "language",
    "title",
    "theme",
    "sentiment",
    "score",
    "phrases"
]:

    if column in details.columns:
        display_columns.append(column)


st.dataframe(
    details[display_columns],
    use_container_width=True,
    hide_index=True
)


# ============================================================
# MÉTHODOLOGIE
# ============================================================

st.markdown(
    '<div class="section-title">ℹ️ Méthodologie</div>',
    unsafe_allow_html=True
)

st.info(
    """
Les avis clients sont analysés automatiquement afin d'identifier
les différents thèmes abordés et leur sentiment associé.

Pour chaque thème, le système détermine une polarité :

🟢 **Positif** — sentiment favorable  
🔴 **Négatif** — sentiment défavorable  
⚪ **Neutre** — sentiment faible ou non clairement orienté

Le score représente l'intensité du sentiment détecté automatiquement
pour le thème concerné.

Les scores présentés dans ce dashboard sont donc des **scores
automatiques issus de l'analyse des avis clients**.
"""
)


# ============================================================
# FOOTER
# ============================================================

st.markdown("---")

st.caption(
    "Prototype — Analyse automatique des avis hôteliers par thème et sentiment"
)