# ============================================================
# DASHBOARD - COMPARATEUR INTELLIGENT D'HÔTELS  (V2)
# + Recommandation selon préférences client
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

st.markdown("""
<style>

.main-title {
    font-size: 36px;
    font-weight: 800;
    margin-bottom: 4px;
    background: linear-gradient(90deg, #1a56db, #0e9f6e);
    -webkit-background-clip: text;
   
}

.subtitle {
    font-size: 17px;
    color: #666;
    margin-bottom: 20px;
}

.section-title {
    font-size: 22px;
    font-weight: 700;
    margin-top: 28px;
    margin-bottom: 12px;
    padding-bottom: 6px;
    border-bottom: 2px solid #eef2f7;
}

.pref-box {
    background: #f0f7ff;
    border: 1px solid #c7e0ff;
    border-radius: 10px;
    padding: 14px 16px;
    margin-bottom: 10px;
}

.winner-box {
    background: linear-gradient(135deg, #0e9f6e18, #1a56db18);
    border: 2px solid #0e9f6e;
    border-radius: 14px;
    padding: 20px 24px;
    margin: 10px 0;
}

</style>
""", unsafe_allow_html=True)


st.markdown(
    '<div class="main-title">🏨 Comparateur intelligent d’hôtels</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">'
    'Analyse automatique des avis clients par thème et sentiment '
    '— avec recommandation personnalisée'
    '</div>',
    unsafe_allow_html=True
)


# ============================================================
# CHARGEMENT
# ============================================================

if not os.path.exists(CSV_PATH):
    st.error(f"Fichier introuvable : {CSV_PATH}")
    st.stop()


df = pd.read_csv(CSV_PATH)


required = [
    "hotel_id",
    "review_id",
    "theme",
    "sentiment",
    "score"
]

missing = [c for c in required if c not in df.columns]

if missing:
    st.error(
        "Colonnes manquantes : " +
        ", ".join(missing)
    )
    st.stop()


# ============================================================
# NORMALISATION
# ============================================================

df["hotel_id"] = df["hotel_id"].astype(str).str.strip()
df["theme"] = df["theme"].astype(str).str.strip()
df["sentiment"] = (
    df["sentiment"]
    .astype(str)
    .str.strip()
    .str.lower()
)

df["score"] = pd.to_numeric(
    df["score"],
    errors="coerce"
)

df = df.dropna(subset=["score"])


# Normalisation des sentiments éventuels
sentiment_map = {
    "pos": "positive",
    "positif": "positive",
    "positive": "positive",

    "neg": "negative",
    "negatif": "negative",
    "négatif": "negative",
    "negative": "negative",

    "neu": "neutral",
    "neutre": "neutral",
    "neutral": "neutral"
}

df["sentiment"] = (
    df["sentiment"]
    .map(sentiment_map)
    .fillna(df["sentiment"])
)


hotel_ids = sorted(
    df["hotel_id"].unique().tolist()
)

available_themes = set(
    df["theme"].dropna().unique()
)


if not hotel_ids:
    st.warning("Aucun hôtel disponible.")
    st.stop()


# ============================================================
# SIDEBAR — HÔTELS + PRÉFÉRENCES CLIENT
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


# ============================================================
# 1. ACTIVITÉS
# ============================================================

activite_choices = {
    "Sport & activités": "sport_activites",
    "Piscine": "piscine",
    "Plage": "plage",
    "Animation & divertissement": "animation",
}

sel_activites = st.sidebar.multiselect(
    "Activités souhaitées",
    list(activite_choices.keys()),
    default=[]
)


# ============================================================
# 2. TYPE DE VOYAGE
# ============================================================

voyage_map = {
    "Indifférent": [],
    "Famille": [
        "famille",
        "animation",
        "piscine"
    ],
    "Couple": [
        "couple",
        "spa et bien être",
        "ambiance",
        "chambre"
    ],
    "Seul / solo": [
        "seul",
        "ambiance",
        "emplacement"
    ],
}

sel_voyage = st.sidebar.selectbox(
    "Type de voyage",
    list(voyage_map.keys())
)


# ============================================================
# 3. CONFORT & BIEN-ÊTRE
# ============================================================

bienetre_choices = {
    "Spa & bien-être": "spa et bien être",
    "Équipements": "équipements",
    "Climatisation": "climatisation",
}

sel_bienetre = st.sidebar.multiselect(
    "Confort & bien-être",
    list(bienetre_choices.keys()),
    default=[]
)


# ============================================================
# 4. RAPPORT QUALITÉ-PRIX
# ============================================================

sel_budget = st.sidebar.selectbox(
    "Budget / rapport qualité-prix",
    [
        "Peu importe",
        "Rapport qualité-prix important"
    ]
)


# ============================================================
# STRATÉGIE
# ============================================================

strategy = st.sidebar.radio(
    "Stratégie de recommandation",
    [
        "⭐ Meilleure qualité d'avis",
        "🧩 Meilleure couverture des préférences"
    ]
)


# ============================================================
# CONSTRUCTION DES PRÉFÉRENCES
# ============================================================

requested_themes = []

requested_themes += [
    activite_choices[k]
    for k in sel_activites
]

requested_themes += voyage_map[sel_voyage]

requested_themes += [
    bienetre_choices[k]
    for k in sel_bienetre
]

if sel_budget == "Rapport qualité-prix important":
    requested_themes.append(
        "rapport qualité-prix"
    )


# Suppression des doublons
requested_themes = list(
    dict.fromkeys(requested_themes)
)


# ============================================================
# THÈMES DISPONIBLES / ABSENTS
# ============================================================

pref_themes = [
    theme
    for theme in requested_themes
    if theme in available_themes
]

missing_pref_themes = [
    theme
    for theme in requested_themes
    if theme not in available_themes
]


# ============================================================
# MESSAGE SI THÈMES NON DISPONIBLES
# ============================================================

if missing_pref_themes:

    st.sidebar.warning(
        "Certains thèmes demandés ne sont pas présents "
        "dans les données analysées : "
        + ", ".join(missing_pref_themes)
    )


# ============================================================
# VÉRIFICATION HÔTELS
# ============================================================

if not selected_hotels:

    st.warning(
        "Sélectionnez au moins un hôtel."
    )

    st.stop()


df_selected = df[
    df["hotel_id"].isin(selected_hotels)
].copy()


# ============================================================
# RECOMMANDATION
# ============================================================

if pref_themes:

    st.markdown(
        '<div class="section-title">'
        '🎯 Hôtel recommandé selon vos préférences'
        '</div>',
        unsafe_allow_html=True
    )

    st.caption(
        "Thèmes pris en compte : "
        + ", ".join(pref_themes)
    )

    ranking = []


    # ========================================================
    # CALCUL POUR CHAQUE HÔTEL
    # ========================================================

    for hid in selected_hotels:

        sub = df_selected[
            df_selected["hotel_id"] == hid
        ]

        scores = []
        found_themes = []


        # ----------------------------------------------------
        # ANALYSE DES THÈMES PRÉFÉRÉS
        # ----------------------------------------------------

        for th in pref_themes:

            rows = sub[
                sub["theme"] == th
            ]

            if not rows.empty:

                theme_score = rows["score"].mean()

                scores.append(
                    float(theme_score)
                )

                found_themes.append(th)


        # ====================================================
        # CALCUL APRÈS LA BOUCLE
        # ====================================================

        if scores:

            mean_score = float(
                pd.Series(scores).mean()
            )

            coverage = (
                len(found_themes)
                / len(pref_themes)
            )

        else:

            mean_score = 0.0
            coverage = 0.0


        # ====================================================
        # STRATÉGIE DE RECOMMANDATION
        # ====================================================

        if "Meilleure couverture" in strategy:

            # Le score dépend à la fois de la qualité
            # et du nombre de préférences réellement documentées.
            final_score = (
                mean_score * coverage
            )

        else:

            # La priorité est donnée à la qualité des avis.
            # Une petite pénalité est appliquée lorsque
            # certains thèmes ne sont pas documentés.
            final_score = (
                mean_score
                - 0.10 * (1 - coverage)
            )


        ranking.append({
            "hotel_id": hid,
            "score_pref": float(final_score),
            "score_brut": float(mean_score),
            "couverture": float(coverage),
            "themes_ok": found_themes,
        })


    # ========================================================
    # CLASSEMENT
    # ========================================================

    ranking.sort(
        key=lambda x: x["score_pref"],
        reverse=True
    )

    winner = ranking[0]


    # ========================================================
    # BLOC GAGNANT
    # ========================================================

    col_w1, col_w2, col_w3 = st.columns(
        [2, 1, 1]
    )


    with col_w1:

        st.markdown(
            f'<div class="winner-box">'
            f'<div style="font-size:15px;color:#555;">'
            f'🏆 Hôtel le plus adapté'
            f'</div>'
            f'<div style="font-size:28px;font-weight:800;">'
            f'Hôtel {winner["hotel_id"]}'
            f'</div>'
            f'<div style="font-size:14px;color:#444;margin-top:6px;">'
            f'Score préférence : '
            f'<b>{winner["score_pref"]:+.2f}</b> '
            f'({len(winner["themes_ok"])} thème(s) analysé(s))'
            f'</div>'
            f'</div>',
            unsafe_allow_html=True
        )


    with col_w2:

        st.metric(
            "Score du gagnant",
            f'{winner["score_pref"]:+.2f}'
        )


    with col_w3:

        if len(ranking) > 1:

            st.metric(
                "2ᵉ choix",
                f'Hôtel {ranking[1]["hotel_id"]}'
            )

        else:

            st.metric(
                "2ᵉ choix",
                "—"
            )


    # ========================================================
    # INFORMATION SUR LA COUVERTURE
    # ========================================================

    st.caption(
        f"Qualité moyenne des thèmes analysés : "
        f"{winner['score_brut']:+.2f} "
        f"— Couverture : "
        f"{len(winner['themes_ok'])}/{len(pref_themes)}"
    )


    # ========================================================
    # TABLEAU DU CLASSEMENT
    # ========================================================

    rank_df = pd.DataFrame([

        {
            "Rang": i + 1,
            "Hôtel": f"Hôtel {r['hotel_id']}",
            "Score préférence": round(
                r["score_pref"],
                3
            ),
            "Qualité moyenne": round(
                r["score_brut"],
                3
            ),
            "Thèmes couverts": (
                f'{len(r["themes_ok"])}'
                f'/{len(pref_themes)}'
            ),
            "Points forts (thèmes)": (
                ", ".join(
                    r["themes_ok"][:5]
                )
                if r["themes_ok"]
                else "—"
            ),
        }

        for i, r in enumerate(ranking)
    ])


    st.dataframe(
        rank_df,
        use_container_width=True,
        hide_index=True
    )


    # ========================================================
    # BAR CHART DU CLASSEMENT
    # ========================================================

    chart = pd.DataFrame(
        {
            f"Hôtel {r['hotel_id']}":
            r["score_pref"]
            for r in ranking
        },
        index=["Score préférence"]
    ).T

    st.bar_chart(
        chart,
        color="#1a56db"
    )


else:

    st.info(
        "Sélectionnez au moins une préférence "
        "pour obtenir une recommandation personnalisée."
    )


# ============================================================
# KPI GÉNÉRAUX
# ============================================================

st.markdown(
    '<div class="section-title">'
    '📊 Vue d’ensemble'
    '</div>',
    unsafe_allow_html=True
)


c1, c2, c3, c4 = st.columns(4)


c1.metric(
    "🏨 Hôtels",
    len(selected_hotels)
)

c2.metric(
    "📝 Avis analysés",
    df_selected["review_id"].nunique()
)

c3.metric(
    "🟢 Positifs",
    int(
        df_selected["sentiment"]
        .eq("positive")
        .sum()
    )
)

c4.metric(
    "🔴 Négatifs",
    int(
        df_selected["sentiment"]
        .eq("negative")
        .sum()
    )
)


# ============================================================
# COMPARAISON PAR THÈME
# ============================================================

st.markdown(
    '<div class="section-title">'
    '🔎 Comparaison par thème'
    '</div>',
    unsafe_allow_html=True
)


themes = sorted(
    df_selected["theme"].unique()
)


# ============================================================
# CELLULE THÈME / HÔTEL
# ============================================================

def cell_data(hid, theme):

    rows = df_selected[
        (df_selected["hotel_id"] == hid)
        &
        (df_selected["theme"] == theme)
    ]

    if rows.empty:
        return None


    score = float(
        rows["score"].mean()
    )


    # Sentiment associé au score moyen.
    # On calcule le score moyen de chaque sentiment.
    sentiment_scores = (
        rows.groupby("sentiment")["score"]
        .mean()
        .sort_values(ascending=False)
    )


    if not sentiment_scores.empty:

        sent = sentiment_scores.index[0]

    else:

        sent = "neutral"


    return score, sent


# ============================================================
# CONSTRUCTION TABLEAU
# ============================================================

table_rows = []


for th in themes:

    row = {
        "Thème": th
    }


    for hid in selected_hotels:

        data = cell_data(
            hid,
            th
        )


        if data is None:

            row[
                f"Hôtel {hid}"
            ] = "—"

        else:

            score, sent = data

            emoji = {
                "positive": "🟢",
                "negative": "🔴",
                "neutral": "⚪"
            }

            emoji_sent = emoji.get(
                sent,
                "⚪"
            )

            row[
                f"Hôtel {hid}"
            ] = (
                f"{emoji_sent} "
                f"{score:+.2f}"
            )


    table_rows.append(row)


table_df = pd.DataFrame(
    table_rows
)


# ============================================================
# COLORATION
# ============================================================

def color_sent(v):

    if isinstance(v, str):

        if "🟢" in v:
            return "background-color: #d9f2e3"

        if "🔴" in v:
            return "background-color: #fbdcdc"

        if "⚪" in v:
            return "background-color: #eeeeee"

    return ""


try:

    styled_table = table_df.style.map(
        color_sent
    )

except AttributeError:

    styled_table = table_df.style.applymap(
        color_sent
    )


st.dataframe(
    styled_table,
    use_container_width=True,
    hide_index=True
)


# ============================================================
# GRAPHIQUE DES SCORES PAR THÈME
# ============================================================

st.markdown(
    '<div class="section-title">'
    '📈 Scores de sentiment par thème'
    '</div>',
    unsafe_allow_html=True
)


chart_df = (
    df_selected
    .groupby(
        ["theme", "hotel_id"]
    )["score"]
    .mean()
    .unstack()
)


st.bar_chart(
    chart_df
)


# ============================================================
# DÉTAIL PAR HÔTEL
# ============================================================

st.markdown(
    '<div class="section-title">'
    '🏨 Détail par hôtel'
    '</div>',
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
# FONCTION SENTIMENT MAJORITAIRE
# ============================================================

def majority_sentiment(series):

    counts = (
        series
        .value_counts()
    )

    if counts.empty:
        return "neutral"

    return counts.index[0]


# ============================================================
# COLONNE PHRASES
# ============================================================

if "phrases" not in hotel_df.columns:

    hotel_df["phrases"] = ""


# ============================================================
# RÉSUMÉ HÔTEL
# ============================================================

hotel_summary = (
    hotel_df
    .groupby("theme")
    .agg(
        score=("score", "mean"),
        sentiment=("sentiment", majority_sentiment),
        occurrences=("theme", "count"),
        phrases=(
            "phrases",
            lambda x:
            " | ".join(
                str(v)
                for v in x
                if pd.notna(v)
                and str(v).strip()
            )
        )
    )
    .reset_index()
)


hotel_summary["score"] = (
    hotel_summary["score"]
    .round(2)
)


def sent_disp(v):

    return {
        "positive": "🟢 Positif",
        "negative": "🔴 Négatif",
        "neutral": "⚪ Neutre"
    }.get(
        v,
        "⚪ Neutre"
    )


hotel_summary["sentiment"] = (
    hotel_summary["sentiment"]
    .apply(sent_disp)
)


hotel_summary = hotel_summary.rename(
    columns={
        "theme": "Thème",
        "score": "Score",
        "sentiment": "Sentiment",
        "occurrences": "Occurrences",
        "phrases": "Phrase(s) analysée(s)"
    }
)[
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
    '<div class="section-title">'
    '📝 Détail des avis analysés'
    '</div>',
    unsafe_allow_html=True
)

f1, f2 = st.columns(2)

with f1:

    theme_filter = st.selectbox(
        "Filtrer par thème",
        [
            "Tous"
        ]
        +
        sorted(
            df_selected["theme"].dropna().unique().tolist()
        )
    )

with f2:

    sentiment_filter = st.selectbox(
        "Filtrer par sentiment",
        [
            "Tous",
            "positive",
            "negative",
            "neutral"
        ]
    )

# IMPORTANT :
# On part de df_selected = TOUS les hôtels sélectionnés
details = df_selected.copy()

# Filtre thème
if theme_filter != "Tous":

    details = details[
        details["theme"] == theme_filter
    ]

# Filtre sentiment
if sentiment_filter != "Tous":

    details = details[
        details["sentiment"] == sentiment_filter
    ]

# Colonnes affichées
display_columns = [
    c
    for c in [
        "hotel_id",
        "review_id",
        "language",
        "theme",
        "sentiment",
        "score",
        "phrases"
    ]
    if c in details.columns
]

st.dataframe(
    details[display_columns],
    use_container_width=True,
    hide_index=True
)



# ============================================================
# MÉTHODOLOGIE
# ============================================================

st.markdown(
    '<div class="section-title">'
    'ℹ️ Méthodologie'
    '</div>',
    unsafe_allow_html=True
)


st.info("""
Les avis sont analysés automatiquement : détection des thèmes
par mots-clés (+ modèle sémantique en secours), puis score de
sentiment par fenêtre d'aspect (±100 caractères autour du
mot-clé).

🟢 **Positif** — sentiment favorable  
🔴 **Négatif** — sentiment défavorable  
⚪ **Neutre** — sentiment neutre

**Recommandation :** pour chaque hôtel, les scores des thèmes
correspondant aux préférences du client sont moyennés.

Un thème absent des avis n'est **pas considéré comme négatif** :
il est simplement indiqué comme non documenté.

La **couverture** indique la proportion des préférences pour
lesquelles l'hôtel dispose effectivement d'avis analysés.

La stratégie « Meilleure qualité d'avis » privilégie le score
moyen des thèmes disponibles avec une légère pénalité de
couverture.

La stratégie « Meilleure couverture des préférences » combine
le score moyen et la couverture des thèmes.
""")


st.markdown("---")

st.caption(
    "Prototype — Analyse automatique des avis hôteliers "
    "par thème et sentiment"
)
