import requests
from bs4 import BeautifulSoup
import json
import time


with open("config.json", "r", encoding="utf-8") as f:
    cfg = json.load(f)

TOKEN = cfg["telegram_token"]
CHAT_ID = cfg["chat_id"]


def enviar(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})


def preco_amazon(url):
    h = {
        "User-Agent": "Mozilla/5.0",
    }
    html = requests.get(url, headers=h).text
    soup = BeautifulSoup(html, "html.parser")

    preco = soup.find("span", class_="a-offscreen")
    if preco:
        return float(preco.text.replace("R$", "").replace(",", "."))
    return None


while True:
    for prod in cfg["produtos"]:
        nome = prod["nome"]
        url = prod["url"]
        alvo = prod["preco_alvo"]

        preco = preco_amazon(url)

        if preco is None:
            enviar(f"❌ Não consegui pegar preço de: {nome}")
            continue

        print(f"{nome}: R$ {preco}")

        if preco <= alvo:
            enviar(f"🔥 BAIXOU!\n{nome}\nPreço atual: R$ {preco}\nAlvo: R$ {alvo}\n{url}")

    time.sleep(1800)  # espera 30 minutos
