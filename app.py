import os
import google.generativeai as genai
from flask import Flask, render_template, request, url_for
from dotenv import load_dotenv

# Charger les variables d’environnement
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# Configuration Gemini
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    # Modèle principal
    model = genai.GenerativeModel(GEMINI_MODEL)
    # Option : chat persistant (si un jour tu veux garder un historique global)
    chat = model.start_chat(history=[])
else:
    model = None
    chat = None

app = Flask(__name__)

@app.get("/")
def index():
    return render_template("index.html", active="index")

@app.get("/demarche")
def demarche():
    return render_template("demarche.html", active="demarche")

@app.get("/reconditionnement")
def reconditionnement():
    return render_template("reconditionnement.html", active="reconditionnement")

@app.get("/collectivites")
def collectivites():
    return render_template("collectivites.html", active="collectivites")

@app.get("/assistant")
def assistant():
    return render_template("assistant.html", active="assistant")


def call_gemini(prompt: str) -> str:
    """
    Appel à Gemini via la lib officielle google.generativeai,
    en s’inspirant de ta logique avec start_chat + stream.
    On consomme le stream pour retourner une seule string.
    """
    if not GEMINI_API_KEY or model is None:
        return "Erreur configuration : GEMINI_API_KEY est manquante ou invalide côté serveur."

    try:
        # Variante “chat” + stream (comme ton exemple)
        # Si tu ne veux pas de contexte global, on pourrait aussi faire :
        #   response = model.generate_content(prompt)
        #   return (response.text or '').strip()
        stream = chat.send_message(prompt, stream=True)

        chunks = []
        for chunk in stream:
            # Selon la lib, chunk.text contient le texte incrémental
            if hasattr(chunk, "text") and chunk.text:
                chunks.append(chunk.text)

        full_text = "".join(chunks).strip()
        if not full_text:
            return "Réponse vide de l’IA (aucun texte reçu)."

        return full_text

    except Exception as e:
        # Tu peux logger e côté serveur si tu veux plus de détails
        return f"Une erreur s’est produite côté IA : {e}"


@app.post("/assistant")
def assistant_submit():
    etab_type = request.form.get("etab_type", "").strip()
    parc = request.form.get("parc", "").strip()
    reseau = request.form.get("reseau", "").strip()
    objectif = request.form.get("objectif", "").strip()
    contraintes = request.form.get("contraintes", "").strip()
    autres = request.form.get("autres", "").strip()

    prompt = f"""
Tu es un assistant IA de NIRD Campus.
Ta mission : produire un rapport professionnel, actionnable et structuré pour aider un établissement scolaire à déployer
un numérique inclusif, responsable et durable (démarche NIRD) et à publier un site web sobre et accessible.

Contexte fourni par l’établissement :
- Type d’établissement : {etab_type}
- Parc / matériel : {parc}
- Réseau / contraintes techniques : {reseau}
- Objectif principal : {objectif}
- Contraintes et exigences : {contraintes}
- Autres informations : {autres}

Exigences de conception web à respecter :
- Contenu texte prioritaire ; médias chargés uniquement à la demande
- Pages légères (cible : < 50 KB par page, hors médias)
- Accessibilité : navigation clavier, focus visible, contrastes, HTML sémantique
- Compatibilité navigateurs texte (w3m / links / lynx)
- Dépendances minimales ; aucune ressource externe obligatoire ; pas de tracking
- Limiter les requêtes : une requête HTML principale par page ; médias uniquement après action utilisateur

Consignes de rédaction :
- Réponds en français, ton professionnel, phrases courtes, recommandations concrètes.
- N’invente pas de contraintes non mentionnées. Si une info manque, fais une hypothèse explicitement signalée.

Format obligatoire du rapport :
1) Synthèse (5 lignes maximum)
2) Plan d’action NIRD en 3 jalons (Mobilisation / Expérimentation / Intégration)
   - Pour chaque jalon : objectifs, actions clés, livrables, acteurs impliqués
3) Checklist “site web sobre & accessible” (points vérifiables, en cases à cocher)
4) Risques & mesures de mitigation (3 à 6 items)
5) Prochaine action recommandée (une seule, très concrète)
""".strip()

    result = call_gemini(prompt)

    return render_template(
        "assistant_result.html",
        active="assistant",
        result=result,
        back_url=url_for("assistant")
    )


@app.errorhandler(404)
def not_found(_):
    return render_template(
        "base.html",
        active=None,
        page_title="NIRD Campus — Page introuvable",
        page_description="Erreur 404",
        content_override="""
<h1>Page introuvable</h1>
<p>Le lien demandé n’existe pas (404).</p>
<p><a href="/">Retour à l’accueil</a></p>
"""
    ), 404


if __name__ == "__main__":
    app.run(debug=True)
