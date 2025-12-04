import os
import google.generativeai as genai
from flask import Flask, render_template, request, url_for
from dotenv import load_dotenv


load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel(GEMINI_MODEL)
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

@app.get("/linux")
def linux():
    return render_template("linux.html", active="linux")

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
    Produit un rapport très court, minimaliste, et directement actionnable.
    Objectif : aider un établissement à démarrer la démarche NIRD.

    Contexte :
    - Type : {etab_type}
    - Parc : {parc}
    - Réseau : {reseau}
    - Objectif : {objectif}
    - Contraintes : {contraintes}
    - Autres : {autres}

    Règles :
    - Réponse courte (10 lignes max).
    - Style simple, direct, phrases très courtes.
    - Pas d'introduction longue.
    - Pas de justification théorique.
    - Pas de checklist.
    - Trois jalons uniquement.
    - Chaque jalon = 2 lignes : objectif + 3 actions clés.
    - Si une info manque, indiquer "hypothèse minimale".

    Format obligatoire :

    1) Synthèse (3 lignes max)
    2) Jalon 1 — Mobilisation (objectif + 3 actions)
    3) Jalon 2 — Expérimentation (objectif + 3 actions)
    4) Jalon 3 — Intégration (objectif + 3 actions)
    5) Prochaine action (une seule, très courte)
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
