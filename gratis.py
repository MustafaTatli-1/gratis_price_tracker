from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import csv
from datetime import datetime
import os
import requests


TOKEN = "Buraya telegramdan tokenimizi yazıyoruz"
CHAT_ID = "burası da telegramdan oluşturduğumuz bota mesaj atan hesabın chat_id sini yazıyoruz"

target_url = ""  # Başlangıçta boş bırakabilirsin  Telegram'dan dolduracağız
last_update_id = 0  # Mesaj takibi için şart


def telegram_mesaj_gonder(mesaj):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": mesaj, "parse_mode": "HTML"}
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print(f"Bağlantı Hatası: {e}")


def excele_yaz(urun_adi, n_fiyat, i_fiyat):
    dosya_adi = "gratis_fiyat_takip.csv"
    tarih = datetime.now().strftime("%d-%m-%Y %H:%M")
    if os.path.exists(dosya_adi):
        with open(dosya_adi, mode ='r', encoding='utf-16') as dosya:
            satirlar = list(csv.reader(dosya, delimiter='\t'))
            if satirlar:
                try:
                    son_fiyat = float(satirlar[-1][3])
                    if son_fiyat == i_fiyat:
                        print(f"Fiyat değişmedi ({i_fiyat} TL). Excel kaydı atlanıyor.")
                        return
                except:
                    pass
    with open(dosya_adi, mode='a', newline='', encoding='utf-16') as dosya:
        yazici = csv.writer(dosya, delimiter='\t')
        yazici.writerow([tarih, urun_adi, n_fiyat, i_fiyat])

def gratis_islem():
    global target_url
    if not target_url: return
    print(f"[{datetime.now().strftime('%H:%M:%S')}] İşlem başlatılıyor...")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service)
    try:
        driver.get(target_url)
        driver.maximize_window()

        wait = WebDriverWait(driver, 15)
        # XPath'leri siteye göre kontrol etmeyi unutma
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "h1")))

        productName = driver.find_element(By.XPATH, "/html/body/div[2]/div[2]/div[2]/div[2]/div/div[1]/h1").text
        newPrice_raw = driver.find_element(By.XPATH,
                                           "/html/body/div[2]/div[2]/div[2]/div[2]/div/div[3]/div[1]/div/h2").text
        normalPrice_raw = driver.find_element(By.XPATH,
                                              "/html/body/div[2]/div[2]/div[2]/div[2]/div/div[3]/div[1]/p").text

        normalPrice = float(normalPrice_raw.replace(" TL", "").replace(".", "").replace(",", "."))
        newPrice = float(newPrice_raw.replace(" TL", "").replace(".", "").replace(",", "."))

        excele_yaz(productName, normalPrice, newPrice)

        rapor_mesaji = (
            f"📅 <b>Fiyat Raporu</b>\n\n"
            f"📦 <b>Ürün:</b> {productName}\n"
            f"💰 <b>Güncel Fiyat:</b> {newPrice} TL\n"
            f"🏷️ <b>Liste Fiyatı:</b> {normalPrice} TL"
        )
        telegram_mesaj_gonder(rapor_mesaji)

    except Exception as e:
        print(f"Hata: {e}")
    finally:
        driver.quit()


def telegram_dinle_ve_karar_ver():
    global target_url, last_update_id
    url = f"https://api.telegram.org/bot{TOKEN}/getUpdates?offset={last_update_id + 1}"
    try:
        cevap = requests.get(url).json()
        if cevap["ok"] and cevap["result"]:
            for guncelleme in cevap["result"]:
                last_update_id = guncelleme["update_id"]
                if "message" in guncelleme and "text" in guncelleme["message"]:
                    gelen_metin = guncelleme["message"]["text"].strip()
                    kucuk_metin = gelen_metin.lower()

                    if kucuk_metin == "merhaba":
                        telegram_mesaj_gonder("Merhaba Link gönderirsen takibe başlarım.")
                    elif "gratis.com" in kucuk_metin:
                        target_url = gelen_metin
                        telegram_mesaj_gonder("Link alındı! Hemen kontrol ediyorum...")
                        gratis_islem()
                    else:
                        telegram_mesaj_gonder("Lütfen geçerli bir Gratis linki gönder. ")
    except Exception as e:
        print(f"Dinleme hatası: {e}")


# --- ANA DÖNGÜ ---
print("Bot aktif... Telegram'dan mesaj bekleniyor.")
while True:
    telegram_dinle_ve_karar_ver()  # İsim burada düzeltildi
    su_an = datetime.now().strftime("%H:%M")

    if su_an == "09:00" and target_url != "":
        gratis_islem()
        time.sleep(70)

    time.sleep(1)
