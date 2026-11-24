#!/usr/bin/env python3
"""Envoie un mail d'anniversaire avec une photo de Yahel et une phrase,
puis incrémente counter.json.

Chaque exécution envoie le mail suivant : la phrase n°N et la photo n°N
(dans l'ordre), N étant le compteur. Quand on arrive au bout de la liste,
on repart au début.

Variables d'environnement requises (secrets GitHub) :
    SMTP_USER      adresse Gmail d'envoi
    SMTP_PASSWORD  mot de passe d'application Gmail
    DEST_EMAIL     adresse de la destinataire

Photos : à mettre dans le dossier photos/ à côté de ce script, nommées dans
l'ordre voulu (001.jpg, 002.jpg, ...). Formats : jpg, jpeg, png, webp, gif.

Le compteur n'est modifié qu'après un envoi réussi : si une erreur survient,
le script s'arrête avec un code d'erreur et le workflow ne commit rien.
"""

import json
import mimetypes
import os
import random
import smtplib
import sys
from email.message import EmailMessage
from email.utils import formataddr, formatdate, make_msgid
from html import escape
from pathlib import Path


COUNTER_FILE = Path(__file__).parent / "counter.json"
PHOTOS_DIR = Path(__file__).parent / "photos"
EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}

SITE_URL = "https://tototipi07-eng.github.io/Projet-harcellement/"

SENDER_NAME = "Surprise anniversaire 🎈"
PRENOM = "Yahel"
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 465
MAX_IMAGE_BYTES = 8 * 1024 * 1024

# Une phrase par mail, dans l'ordre. 84 phrases = 14 h à raison d'un mail / 10 min.
PHRASES = [
    # Matin
    "Bonjour Joyeux anniversaire Yahel ! 🎂",
    "Ceci est le premier mail d'une longue série. Tu n'es pas prête.",

    "tu as 19 ans t'es vielle de fou bahahhhahahaha",
    "j'aime bien cette photo t'es jolie je commence doucement.",
    "Aujourd'hui, tu as officiellement le droit de ne pas être gentille. ",
    "Message d'utilité publique : BONNE ANNNNIIIIVERRRSAIRREEE YAHELLLL.",
    "Si tu lis ça avec le sourire, ma mission est déjà réussi.",
    "Info du jour : le monde est un peu mieux depuis que tu es dedans. ps:c'est pas de moi celle là mais je la trouve vraie.",
    "Que cette journée soit remplie de bonnes surprises.",
    "tu as le droit de te faire plaisir aujourd'hui. Interdiction de t'en priver.",
    "Déjà 11 mails reçus, et on n'est qu'au début. Courage...",
    "Question ? as-tu déjà fait un vœu aujourd'hui ? Fais-en un gros.",
    "Je suis très content de t'avoir dans ma vie. Voilà, c'est dit.",
    "att je vais chercher des phrases d'accroche pout toi",
    "Je viens vérifier si tu es toujours aussi incroyable qu'hier. C'est pour mes statistiques.",
    "Je voulais écrire quelque chose d'intelligent, mais tu me fais perdre mes moyens. pas mal celle là non ?",
    "J'espère que ta journée est aussi belle que toi. ouffff elle est trop bien",
    "Certaines personnes prennent de belles photos. Toi, tu rends les photos belles.",
    "Statistique du jour : 100 % des mails d'aujourd'hui contiennent une belle personne.",
    "Il existe plus de flamants roses en plastique dans le monde que de vrais flamants roses",
    "Tu mérites une journée où tout se passe bien. Je croise les doigts.",


    "Cette phrase n'a aucun intérêt, j'espère que tu la lira pas ",
    "Il paraît qu'on grandit à chaque anniversaire. Toi, tu rayonnes surtout. j'ai plus trop d'inspi là dsl",
    "Si tu as faim tu peux aller manger, c'est logique ",
    "Si tu as soif tu peux aller boire, c'est logique aussi",
    "Une porte ouverte est généralement plus ouverte qu'une porte fermée.",
    "si tu as chaud tu peux enlever ton écharpe, c'est logique aussi",
    "Si tu as froid je peux te réchauffer si tu veux",
    "J'espère que ça va marcher et que ça ne servent à rien :(.",
    "Ce que j'aime chez toi ? Plein de choses. La liste est longue.",
    "Les vaches ont des meilleures amies et stressent quand elles sont séparées.",
    "ehh yaaaa moyennn ouuuuu ??? ",
    "Une girafe se nettoie les oreilles avec sa langue.",

    # Midi
    "Tu fais partie des gens qui rendent les journées plus légères. Merci pour ça.",
    "Je pense que tu sous-estimes ton niveau de photogénie. je sais pas si ça s'écrit comme ça mdr ",
    "Le jour de son anniversaire, on a le droit de dire et faire ce qu'on veut. je pose ça la",
    "Attention, être aussi jolie est normalement soumis à une réglementation strict.",
    "Bonjour mademoiselle, je vous arrête pour excès de beauté.",
    "dsl pour les fautes d'orthographe jsuis trop nul pour ça",
    "Ce qu'il y a devant l'objectif est beau, mais ce qu'il y a derrière palalalalaa. dsl il est tard pour moi",
    "Je reviens dans dix minutes att",
    "Je reviens dans dix minutes encore je dois regarder the pianist sans toi",
    "je t'ai manqué ???????",
    "Tu es probablement en train de sourire. Je le sens d'ici.",

    # Après-midi

    "prends le temps de profiter. Aujourd'hui, c'est ton jour, par contre demain tu vas voir....",
    "Si on faisait un classement des plus belle personnes, tu serais comme dans la musique de squeezie",

    "Une journée sur Vénus est plus longue qu'une année sur Vénus.c'est fou en vrai",
    "Je suis content d'avoir pu partager cette journée avec toi même par mail mdrr ",
    "Tu as vu comme tu es photogénique ? ",
    "Je viens de vérifier. Oui, c'est toujours ton anniversaire.",
    "Si tu es fatiguée de tous ces mails, tu peux répondre « stop ». Je ne m'arrêterai pas, mais c'est gentil de demander.",

   
    "Allez, courage, il reste encore plein de mails à lire. Tu vas y arriver.",
    "Quel est le plus beau cadeau d'aujourd'hui ? Ces mails, évidemment.",
   
    "yahel ... ... NON RIEN ahaahahahahahaahah",
    "Merci d'exister, sincèrement.",
    "Je suis à court d'idées de blagues, donc je mise tout sur la gentillesse.",

    "Il paraît que les anniversaires rendent plus vieux c'est vrai ? ",
    "Les gens qui ont 19 ans ont généralement 1 an de plus que les gens qui ont 18 ans.",
    # Soirée
    "Les personnes vivantes ont tendance à ne pas être mortes.", 
    "J'ai remarqué que les anniversaires tombent toujours le même jour de l'année.",

    "Si quelqu'un te propose de cuisiner ce soir, accepte. C'est un cadeau.",
    "Plus une pizza est grande, plus il y a de pizza dedans.",
    "Plus il y a de gens dans une file d'attente, plus la file d'attente est longue",
    "si tu mets un pizza sur une autre pizza ça fait 2 pizzas mais si tu mets une lazzagne sur une autre lazzagne ça fait une lazzagne. à mériter",
    "c'est fou toute les photos sont belle de ouf bizzare",
    
    "fais un vœu , Je suis sûr qu'il se réalisera à part si je trouve qu'il est nul donc il se réalisera pas",
    "Je t'écris depuis le futur : tu vas passer une très belle année de 19 ans.",
    "Contrôle qualité terminé : résultat, toujours parfaite. je deviens fou ",
    "La soirée approche, et avec elle la fin des mails. c'est triste",
    "Quoi qu'il arrive cette année, sache que je suis dans ton camp. Toujours.",
    "Pour finir : que cette nouvelle année soit remplie de joie, de rires et de belles surprises.",
    "Voilà, c'est fini ! Joyeux anniversaire Yahel, et bonne soiré. 🌙",
    "allez une petit dernière pour la route",
]

CONFETTI_COULEURS = ["#2f6fed", "#ffb703", "#2a9d8f", "#e63946", "#8ecae6", "#fb8500", "#90be6d"]
CONFETTI_FORMES = ["●", "◆", "■", "▲", "★", "♥", "✦"]
COULEURS_FOND = ["#eaf2ff", "#fff0f3", "#f0f7e9", "#fff6e5", "#f3edff", "#e8f7f5"]


def confettis(n=22):
    """Ligne de confettis colorés aléatoires (compatible clients mail)."""
    morceaux = []
    for _ in range(n):
        forme = random.choice(CONFETTI_FORMES)
        couleur = random.choice(CONFETTI_COULEURS)
        taille = random.choice([12, 16, 20, 24])
        morceaux.append(
            f'<span style="color:{couleur};font-size:{taille}px;margin:0 3px;">{forme}</span>'
        )
    return "".join(morceaux)


def lister_photos():
    if not PHOTOS_DIR.is_dir():
        return []
    return sorted(
        p for p in PHOTOS_DIR.iterdir() if p.suffix.lower() in EXTENSIONS
    )


def charger_photo(chemin):
    octets = chemin.read_bytes()
    if len(octets) > MAX_IMAGE_BYTES:
        raise ValueError("Image trop lourde")
    type_mime, _ = mimetypes.guess_type(chemin.name)
    if not type_mime or not type_mime.startswith("image/"):
        raise ValueError(f"Type inattendu : {type_mime or 'inconnu'}")
    maintype, subtype = type_mime.split("/", 1)
    return octets, maintype, subtype


def choisir_photo():
    """Choisit une photo au hasard, en essayant les autres si elle est invalide."""
    photos = lister_photos()
    random.shuffle(photos)
    for chemin in photos:
        try:
            return charger_photo(chemin)
        except Exception as err:  # noqa: BLE001 - on passe à la photo suivante
            print(f"[photo] {chemin.name} inutilisable : {err}")
    print("[photo] aucune photo disponible dans photos/")
    return None


def lire_compteur():
    with open(COUNTER_FILE, encoding="utf-8") as f:
        return int(json.load(f)["count"])


def ecrire_compteur(valeur):
    with open(COUNTER_FILE, "w", encoding="utf-8") as f:
        json.dump({"count": valeur}, f)
        f.write("\n")


def construire_mail(expediteur, destinataire, numero, image):
    total = len(PHRASES)
    position = (numero) % total
    phrase = PHRASES[position]
    couleur_fond = random.choice(COULEURS_FOND)
    sujet = f"Joyeux anniversaire Yahel!"

    msg = EmailMessage()
    msg["Subject"] = sujet
    msg["From"] = formataddr((SENDER_NAME, expediteur), charset="utf-8")
    msg["To"] = destinataire
    msg["Date"] = formatdate(localtime=True)

    texte = (
        f"🎉 Joyeux anniversaire Yahel! 🎉\n\n"
        f"{phrase}\n\n"
    )
    msg.set_content(texte)

    cid = make_msgid(domain="anniversaire.local")
    bloc_photo = ""
    if image is not None:
        bloc_photo = (
            f'<img src="cid:{cid[1:-1]}" alt="Photo de {escape(PRENOM)}" '
            'style="max-width:100%;border-radius:18px;margin:16px 0;'
            'border:5px solid #4f8cff;box-shadow:0 6px 18px rgba(47,111,237,0.3);">'
        )

    html = f"""\
<html>
  <body style="font-family:Arial,Helvetica,sans-serif;background:{couleur_fond};margin:0;padding:24px;">
    <div style="max-width:480px;margin:0 auto;text-align:center;color:{couleur_fond};
                background:#ffffff;border-radius:24px;padding:24px;
                border:3px dashed #4f8cff;">
      <div style="line-height:1.4;">{confettis()}</div>
      <div style="font-size:42px;margin:6px 0;"> 🎉 🎉 🎉 🎂  🎉 🎉 🎉</div>
      <h1 style="margin:4px 0;color:#1d3557;font-size:28px;">Joyeux anniversaire Yahel! </h1>
     
      {bloc_photo}
      <p style="font-size:17px;line-height:1.5;background:{couleur_fond};border-radius:14px;padding:14px;color:#1d3557;">
        {escape(phrase)}
      </p>
      <div style="font-size:26px;margin:10px 0;">❤️ ✨ ❤️ 🥳 ❤️ ✨ ❤️</div>
      
      <div style="line-height:1.4;margin-top:18px;">{confettis()}</div>
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
    image = choisir_photo()

    msg = construire_mail(utilisateur, destinataire, numero, image)
    envoyer(msg, utilisateur, mot_de_passe)

    ecrire_compteur(numero)


if __name__ == "__main__":
    main()