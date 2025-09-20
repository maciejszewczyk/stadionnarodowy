import requests
from bs4 import BeautifulSoup
from datetime import datetime

def check_parking_icon():
    now = datetime.now()
    current_month = f"{now.month:02d}"
    current_year = str(now.year)
    unix_time = int(now.timestamp() * 1000)

    URL = (
        f"https://www.pgenarodowy.pl/calendar/calendar-graphic.php?"
        f"month={current_month}&year={current_year}&type=1{unix_time}"
    )
    # 1. Dzisiejszy dzień
    today_day = str(now.day)
    #today_day = "8"

    # 2. Pobranie strony
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:142.0) Gecko/20100101 Firefox/142.0"
    }

    response = requests.get(URL, headers=headers)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    # 3. Szukanie dużego diva z datą
    containers = soup.find_all("div", class_="calendar--day-top")

    for container in containers:
        day_div = container.find("div", class_="calendar--day-number", string=today_day)
        if day_div:
            parking_img = container.find("img", {
                "src": "/assets/img/svg/ico-parking.svg",
                "title": "Parking zewnętrzny płatny",
                "alt": "Parking zewnętrzny płatny"
            })

            blocked_img = container.find("img", {
                "src": "/assets/img/svg/ico-other.svg",
                "title": "Uwaga! Parking na błoniach niedostępny!",
                "alt": "Uwaga! Parking na błoniach niedostępny!"
            })

            any_parking_img = container.find("img", title=lambda t: t and "parking" in t.lower())

            # Zwróć True, jeśli parking/blocked/any_parking istnieje (nie jest None), w przeciwnym razie zwróć False
            return (
                parking_img is not None
                or blocked_img is not None
                or any_parking_img is not None
            )

    return False  # jeśli żaden kontener z dzisiejszym dniem nie został znaleziony