#!/usr/bin/env python3
"""Envoie un mail quotidien avec une photo d'animal, puis incrémente counter.json.

Variables d'environnement requises (secrets GitHub) :
    SMTP_USER      adresse Gmail d'envoi
    SMTP_PASSWORD  mot de passe d'application Gmail
    DEST_EMAIL     adresse de la destinataire

Le compteur n'est modifié qu'après un envoi réussi : si une erreur survient,
le script s'arrête avec un code d'erreur et le workflow ne commit rien.
"""

import json
import os
import random
import smtplib
import sys
from email.message import EmailMessage
from email.utils import formataddr, formatdate, make_msgid
from html import escape
from pathlib import Path
import requests


COUNTER_FILE = Path(__file__).parent / "counter.json"


SITE_URL = "https://tototipi07-eng.github.io/Projet-harcellement/"


FALLBACK_URL = "https://raw.githubusercontent.com/tototipi07-eng/Projet-harcellement/main/secours.jpg"

SENDER_NAME = "Projet Harcèlement"
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 465
TIMEOUT = 15  
MAX_IMAGE_BYTES = 8 * 1024 * 1024

CAPTIONS = [

    "Ceci est un harcèlement officiel. Merci de ne pas résister.",
    "Cet animal te regarde avec de grandes attentes.",
    "Rapport du jour : tu es toujours en train de lire mes mails.",
    "Ce mail s'autodétruira dans... non, finalement il reste là.",
    "Je ne dis pas que cet animal te ressemble. Je le pense très fort.",
    "Mise à jour du dossier : Mmmmm non je continue.",
    "Ceci est le mail du jour. Demain, il y en aura un autre. Et ainsi de suite.",
    "Cette photo a été choisie au hasard, mais avec amour.",
    "Je t'ai harcelée aujourd'hui. Tu peux me remercier, c'est gratuit.",
    "j'ai plus d'idées là ",
    "comment ça va ?",
    "Je t'envoie ce mail pour te rappeler que tu es harcelée. C'est important.",
    "67 67 67 67 tasty croustilles",
    "le pianiste n'est plus disponible désolé :(",
    "j'aurais kiffer qu'on aille au zoo, le problème c'est que j'ai peur qu'ils te gardent",
    

]

def photo_chat():
    r = requests.get("https://api.thecatapi.com/v1/images/search", timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()[0]["url"]


def photo_chien():
    r = requests.get("https://dog.ceo/api/breeds/image/random", timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()["message"]

def photo_renard():
    r = requests.get("https://randomfox.ca/floof/", timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()["image"]

def photo_capybara():
    r = requests.get("https://api.capy.lol/v1/capybara?json=true", timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()["data"]["url"]


SOURCES = [
    ("chat", photo_chat),
    ("chien", photo_chien),
    ("renard", photo_renard),
    ("capybara", photo_capybara),
]


def telecharger(url):
    r = requests.get(url, timeout=TIMEOUT)
    r.raise_for_status()
    content_type = r.headers.get("Content-Type", "").split(";")[0].strip().lower()
    if not content_type.startswith("image/"):
        raise ValueError(f"Contenu inattendu : {content_type or 'inconnu'}")
    if len(r.content) > MAX_IMAGE_BYTES:
        raise ValueError("Image trop lourde")
    maintype, subtype = content_type.split("/", 1)
    return r.content, maintype, subtype


def recuperer_photo():
    sources = SOURCES[:]
    random.shuffle(sources)
    for animal, fetch in sources:
        try:
            return animal, telecharger(fetch())
        except Exception as err:  # noqa: BLE001 - on veut tout rattraper ici
            print(f"[photo] {animal} indisponible : {err}")

    try:
        print("[photo] utilisation de la photo de secours")
        return "animal mystère", telecharger(FALLBACK_URL)
    except Exception as err:  # noqa: BLE001
        print(f"[photo] photo de secours indisponible : {err}")
        return None, None


def lire_compteur():
    with open(COUNTER_FILE, encoding="utf-8") as f:
        return int(json.load(f)["count"])


def ecrire_compteur(valeur):
    with open(COUNTER_FILE, "w", encoding="utf-8") as f:
        json.dump({"count": valeur}, f)
        f.write("\n")

def construire_mail(expediteur, destinataire, numero, animal, image):
    legende = random.choice(CAPTIONS)
    sujet = f"Harcèlement : ton {animal} du jour"
    if image is None:
        sujet = f"Harcèlement: les animaux sont en grève"
        legende = "Les animaux sont en grève aujourd'hui, mais le harcèlement continue."

    msg = EmailMessage()
    msg["Subject"] = sujet
    msg["From"] = formataddr((SENDER_NAME, expediteur), charset="utf-8")
    msg["To"] = destinataire
    msg["Date"] = formatdate(localtime=True)

    texte = (
        f"{legende}\n\n"
        f"Harcèlement \n"
        f"clique ici pour le site officiel : {SITE_URL}\n"
    )
    msg.set_content(texte)

    cid = make_msgid(domain="harcelement.local")
    bloc_photo = ""
    if image is not None:
        bloc_photo = (
            f'<img src="cid:{cid[1:-1]}" alt="Photo du jour" '
            'style="max-width:100%;border-radius:12px;margin:16px 0;">'
        )

    html = f"""\
<html>
  <body style="font-family:Arial,Helvetica,sans-serif;background:#faf7f2;margin:0;padding:24px;">
    <div style="max-width:480px;margin:0 auto;text-align:center;color:#333;">
      <h2 style="margin-bottom:4px;">Harcèlement n°{numero}</h2>
      {bloc_photo}
      <p style="font-size:16px;line-height:1.5;">{escape(legende)}</p>
      <p style="font-size:13px;color:#888;">
        <a href="{escape(SITE_URL)}" style="color:#888;">Consulter le compteur officiel</a>
      </p>
    </div>
  </body>
</html>
"""
    msg.add_alternative(html, subtype="html")

    if image is not None:
        octets, maintype, subtype = image
        msg.get_payload()[1].add_related(octets, maintype, subtype, cid=cid)

    return msg


def envoyer(msg, utilisateur, mot_de_passe):
    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=30) as smtp:
        smtp.login(utilisateur, mot_de_passe)
        smtp.send_message(msg)


def main():
    utilisateur = os.environ.get("SMTP_USER", "").strip()
    mot_de_passe = os.environ.get("SMTP_PASSWORD", "").replace(" ", "")
    destinataire = os.environ.get("DEST_EMAIL", "").strip()

    manquantes = [
        nom
        for nom, valeur in [
            ("SMTP_USER", utilisateur),
            ("SMTP_PASSWORD", mot_de_passe),
            ("DEST_EMAIL", destinataire),
        ]
        if not valeur
    ]
    if manquantes:
        sys.exit(f"Variables d'environnement manquantes : {', '.join(manquantes)}")

    numero = lire_compteur() + 1
    animal, image = recuperer_photo()

    msg = construire_mail(utilisateur, destinataire, numero, animal, image)
    envoyer(msg, utilisateur, mot_de_passe)
    
    ecrire_compteur(numero)
    print(f"[ok] mail n°{numero} envoyé ({'avec' if image else 'sans'} photo)")


if __name__ == "__main__":
    main()