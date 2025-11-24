import requests
from bs4 import BeautifulSoup
import json
import time
import os

# --- CARREGA CONFIG ---
with open("config.json", "r", encoding="utf-8") as f:
    cfg = json.load(f)

TOKEN = cfg["telegram_token"]
CHAT_ID = cfg["chat_id"]

# --- CARREGA PRODUTOS ---
with open("produtos.json", "r", encoding="utf-8") as f:
    produtos = json.load(f)

# --- FUNÇÃO DE ALERTA TELEGRAM ---
def enviar(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})

# --- PEGAR PREÇO AMAZON ---
def preco_amazon(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    html = requests.get(url, headers=headers).text
    soup = BeautifulSoup(html, "html.parser")
    preco_tag = soup.find("span", class_="a-offscreen")
    if preco_tag:
        preco = preco_tag.text.replace("R$", "").replace(".", "").replace(",", ".")
        return float(preco)
    return None

# --- PEGAR PREÇO MERCADO LIVRE ---
def preco_mercadolivre(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    html = requests.get(url, headers=headers).text
    soup = BeautifulSoup(html, "html.parser")
    preco_tag = soup.find("span", class_="price-tag-fraction")
    if preco_tag:
        preco = preco_tag.text.replace(".", "")
        return float(preco)
    return None

# --- PEGAR PREÇO CORRETO ---
def pegar_preco(url):
    if "amazon.com.br" in url:
        return preco_amazon(url)
    elif "mercadolivre.com.br" in url:
        return preco_mercadolivre(url)
    return None

# --- SALVAR HISTÓRICO ---
def salvar_historico(nome, preco):
    if not os.path.exists("historico.json"):
        historico = []
    else:
        with open("historico.json", "r", encoding="utf-8") as f:
            historico = json.load(f)
    historico.append({"produto": nome, "preco": preco, "timestamp": time.time()})
    with open("historico.json", "w", encoding="utf-8") as f:
        json.dump(historico, f, indent=4, ensure_ascii=False)

# --- PEGAR MENOR PREÇO HISTÓRICO ---
def menor_preco(nome):
    if not os.path.exists("historico.json"):
        return float("inf")
    with open("historico.json", "r", encoding="utf-8") as f:
        historico = json.load(f)
    precos = [h["preco"] for h in historico if h["produto"] == nome]
    return min(precos) if precos else float("inf")

# --- LOOP PRINCIPAL ---
def monitorar():
    print("⏳ Iniciando monitoramento...")
    for prod in produtos:
        nome = prod["nome"]
        url = prod["url"]
        alvo = prod["alvo"]

        preco = pegar_preco(url)
        if preco is None:
            print(f"❌ Não consegui pegar preço de: {nome}")
            enviar(f"❌ Não consegui pegar preço de: {nome}")
            continue

        print(f"{nome}: R$ {preco}")
        salvar_historico(nome, preco)
        menor = menor_preco(nome)

        if preco <= alvo:
            enviar(f"🔥 PREÇO BAIXOU!\n{nome}\nAtual: R$ {preco}\nAlvo: R$ {alvo}\nMenor histórico: R$ {menor}\n{url}")

while True:
    monitorar()
    print("⏳ Esperando 30 minutos para próxima verificação...")
    time.sleep(1800)
