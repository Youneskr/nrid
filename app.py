import os
import requests
from flask import Flask, render_template, request, url_for  # ✅ ajouter request + url_for
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")  # ✅ nom unique et cohérent

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

def call_openrouter(prompt: str) -> str:
    if not OPENROUTER_API_KEY:
        return "Erreur configuration : OPENROUTER_API_KEY est manquante côté serveur."

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        # Optionnels mais utiles:
        # "HTTP-Referer": "http://localhost:5000",
        # "X-Title": "NIRD Campus",
    }

    payload = {
        "model": "google/gemma-3n-e4b-it:free",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
        "max_tokens": 900,
    }

    try:
        r = requests.post(url, headers=headers, json=payload, timeout=30)
        if r.status_code != 200:
            return f"Erreur IA (HTTP {r.status_code}). Détails: {r.text[:300]}"

        data = r.json()
        choices = data.get("choices", [])
        if not choices:
            return "Réponse vide de l’IA (aucun choix retourné)."

        message = choices[0].get("message") or {}
        content = message.get("content")

        if isinstance(content, str) and content.strip():
            return content.strip()

        return "Réponse vide de l’IA (contenu absent)."

    except requests.exceptions.Timeout:
        return "La requête IA a expiré (timeout). Veuillez réessayer."
    except requests.exceptions.RequestException:
        return "Erreur de connexion au service IA. Vérifiez votre réseau."
    except Exception:
        return "Une erreur inattendue s’est produite côté IA."

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

    result = call_openrouter(prompt)

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
