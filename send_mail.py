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
    "Debout, c'est ton jour ! Joyeux anniversaire Yahel ! 🎂",
    "Ceci est le premier mail d'une longue série. Tu n'es pas prête.",
    "Un mail toutes les 10 minutes, toute la journée. Oui, j'ai bien dit toute la journée.",
    "Tu as un an de plus, mais honnêtement ça te va très bien.",
    "Petit conseil : commence la journée avec un petit déj digne d'un anniversaire.",
    "Aujourd'hui, tu as officiellement le droit de manger du gâteau à toute heure. 🍰",
    "Message d'utilité publique : tu es une personne vraiment cool.",
    "Si tu lis ça avec le sourire, ma mission est déjà en bonne voie. 😄",
    "Info du jour : le monde est un peu mieux depuis que tu es dedans.",
    "Je n'ai pas de super-pouvoirs, mais je peux t'envoyer plein de mails. C'est déjà ça.",
    "Que cette journée soit remplie de bonnes surprises. La première, c'est moi.",
    "Petit rappel : tu as le droit de te faire plaisir aujourd'hui. Interdiction de t'en priver.",
    "J'espère que tes premiers cadeaux t'ont plu. Sinon, on en reparlera. 🎁",
    "Déjà plein de mails reçus, et on n'est qu'au début. Courage ! 💪",
    # Fin de matinée
    "Question importante : as-tu déjà fait un vœu aujourd'hui ? Fais-en un gros.",
    "Je suis très content de t'avoir dans ma vie. Voilà, c'est dit. 💙",
    "Je ne sais pas écrire de poèmes, mais je sais écrire des mails. Beaucoup de mails.",
    "Oui, c'est bien toi sur la photo. Et oui, tu es très bien dessus.",
    "Statistique du jour : 100 % des mails d'aujourd'hui contiennent une belle personne. Spoiler : c'est toi.",
    "Tu mérites une journée où tout se passe bien. Je croise les doigts.",
    "Hydratation : bois un verre d'eau. Après, tu pourras reprendre du gâteau.",
    "Cette phrase n'a aucun intérêt, mais elle est là pour t'envoyer plein de bonnes ondes.",
    "Il paraît qu'on grandit à chaque anniversaire. Toi, tu rayonnes surtout.",
    "Si tu as faim, c'est normal. Si tu as envie de dessert, c'est encore plus normal.",
    "J'espère que tu as déjà reçu plein de messages. Le mien est le plus régulier, au moins.",
    "Ce que j'aime chez toi ? Plein de choses. La liste est longue, je continue demain.",
    "Fait scientifique (non vérifié) : sourire en lisant ce mail ajoute 3 minutes de bonheur.",
    "Bientôt midi ! Pense à manger quelque chose de bon. C'est un ordre doux.",
    # Midi
    "Pause déjeuner : le moment parfait pour un repas d'anniversaire.",
    "Ton plat préféré t'attend peut-être quelque part. Va le chercher.",
    "Un anniversaire sans dessert, c'est comme un mail sans photo de toi : ça n'existe pas.",
    "Je t'écris entre deux bouchées virtuelles. Bon appétit ! 🍽️",
    "Je suis fier de ce que tu es, et de ce que tu deviens.",
    "Tu fais partie des gens qui rendent les journées plus légères. Merci pour ça.",
    "Si le déjeuner était un cadeau, tu aurais déjà tout gagné.",
    "Petite sieste autorisée aujourd'hui. Mais je continue les mails pendant ce temps. 😴",
    "Le jour de son anniversaire, on a le droit de faire ce qu'on veut. Enfin, c'est ma théorie.",
    "Moment sincérité : merci d'être la personne que tu es.",
    "Je te laisse digérer tranquillement. Je reviens dans dix minutes, comme prévu.",
    "Tu es probablement en train de sourire. Je le sens d'ici.",
    "Si tu avais un super-pouvoir aujourd'hui, ce serait d'illuminer toutes les pièces.",
    "Tu te demandes sûrement quand ça va s'arrêter. Réponse : ce soir.",
    # Après-midi
    "L'après-midi commence. Le gâteau est encore valable, ne l'oublie pas.",
    "Je pense à toi même quand je n'envoie pas de mail. Là, j'en envoie beaucoup, mais bon.",
    "Un conseil : prends le temps de profiter. Aujourd'hui, c'est ton jour.",
    "Si on faisait un classement des meilleures personnes, tu serais sur le podium. Peut-être même première.",
    "Je te dois au moins mille câlins. Je te les livrerai en personne.",
    "Ce mail est sponsorisé par l'envie de te faire sourire.",
    "Tu as vu comme tu es photogénique ? Moi, je le sais depuis longtemps.",
    "Si tu es fatiguée de tous ces mails, tu peux répondre « stop ». Je ne m'arrêterai pas, mais c'est gentil de demander.",
    "Chaque année avec toi est une bonne année. Surtout celle-ci.",
    "Je te souhaite des rires, du chocolat et des gens qui t'aiment. Dans cet ordre ou un autre.",
    "J'ai de la chance de te connaître. C'est pas une blague, enfin si un peu. Mais surtout non.",
    "Allez, courage, il reste encore plein de mails à lire. Tu vas y arriver.",
    "Quel est le plus beau cadeau d'aujourd'hui ? Ces mails, évidemment.",
    "J'espère que ton goûter est à la hauteur de l'occasion. 🍰",
    "Petit rappel : tu es capable de grandes choses. Et de petites aussi, mais surtout de grandes.",
    "Merci d'exister, sincèrement.",
    "Je suis à court d'idées de blagues, donc je mise tout sur la gentillesse.",
    "Si tu penses à moi en ce moment, c'est normal : je t'inonde de mails.",
    "Il paraît que les anniversaires rendent plus sage. Ne change rien, surtout.",
    "La soirée approche, et avec elle la fin des mails. Peut-être.",
    # Soirée
    "Début de soirée : l'heure idéale pour un dîner d'anniversaire.",
    "Si quelqu'un te propose de cuisiner ce soir, accepte. C'est un cadeau.",
    "Et si on faisait un truc sympa bientôt, juste nous ? Pense-y.",
    "Je suis content d'avoir pu partager cette journée avec toi, même à distance.",
    "Ma phrase préférée de la journée : « Joyeux anniversaire Yahel ». Elle est vraie.",
    "Il reste de moins en moins de mails. Je te vois déjà soulagée. Ou un peu triste ?",
    "Souviens-toi : tu es drôle, tu es géniale, et tu es très forte pour recevoir des mails.",
    "Ce soir, fais un dernier vœu. Je suis sûr qu'il se réalisera.",
    "Je t'écris depuis le futur : tu vas passer une très belle soirée.",
    "Merci d'avoir lu tous ces mails. Tu es une championne.",
    "Résumé de la journée : gâteau, rires, câlins virtuels et moi dans ta boîte mail.",
    "Je ne te l'ai pas encore assez dit : tu comptes énormément pour moi. 💙",
    "Les bougies sont presque soufflées. Garde un peu de chance pour l'année qui arrive.",
    "Cette année va être belle. Je le sens, et je me trompe rarement.",
    "On approche de la fin. Respire, tu as survécu à une journée de mails.",
    "J'ai de la chance de t'avoir dans ma vie, tout simplement.",
    "Quoi qu'il arrive cette année, sache que je suis dans ton camp. Toujours.",
    "Dernière ligne droite : plus que quelques mails avant la fin de la fête.",
    "Merci d'avoir été la star de cette journée. Tu le méritais largement.",
    "Avant-dernier mail ! Le dernier arrive dans dix minutes. Reste là.",
    "Pour finir : que cette nouvelle année soit remplie de joie, de rires et de belles surprises.",
    "Voilà, c'est fini ! Joyeux anniversaire Yahel, et bonne nuit. 🌙💙",
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


def choisir_photo(index):
    """Photo n°index dans l'ordre alphabétique (on repart au début à la fin)."""
    photos = lister_photos()
    for decalage in range(len(photos)):
        chemin = photos[(index + decalage) % len(photos)]
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
    position = (numero - 1) % total
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
    <div style="max-width:480px;margin:0 auto;text-align:center;color:#1d3557;
                background:#ffffff;border-radius:24px;padding:24px;
                border:3px dashed #4f8cff;">
      <div style="line-height:1.4;">{confettis()}</div>
      <div style="font-size:42px;margin:6px 0;">🎂 🎈 🎉</div>
      <h1 style="margin:4px 0;color:#1d3557;font-size:28px;">Joyeux anniversaire Yahel! </h1>
     
      {bloc_photo}
      <p style="font-size:17px;line-height:1.5;background:#e8f1ff;border-radius:14px;padding:14px;color:#1d3557;">
        {escape(phrase)}
      </p>
      <div style="font-size:26px;margin:10px 0;">💙 ✨ 💛 🥳 💚 ✨ 💙</div>
      
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
    image = choisir_photo(numero - 1)

    msg = construire_mail(utilisateur, destinataire, numero, image)
    envoyer(msg, utilisateur, mot_de_passe)


if __name__ == "__main__":
    main()