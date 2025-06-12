"""
volby.py: volby 2017

Leila Váňová
vanov86039@mot.sps-dopravni.cz
"""
import sys
import requests
from bs4 import BeautifulSoup
import csv
from urllib.parse import urljoin


def get_soup(url):
    response = requests.get(url)
    response.encoding = 'utf-8'  # správné kódování pro CZ stránky
    return BeautifulSoup(response.text, "html.parser")


def get_links_to_obce(main_url):
    soup = get_soup(main_url)
    links = soup.select("td.cislo a")
    return [(link.text, urljoin(main_url, link["href"])) for link in links]


def get_obec_data(url):
    soup = get_soup(url)

    # Název obce
    obec_name = soup.find("h3").text.strip()

    # Statistické hodnoty
    tds = soup.find_all("td")
    data = {"location": obec_name}


    for i in range(len(tds)):
        text = tds[i].get_text()
        if "Voliči v seznamu" in text:
            data["registered"] = int(tds[i + 1].get_text().replace("\xa0", "").replace(" ", ""))
        elif "Vydané obálky" in text:
            data["envelopes"] = int(tds[i + 1].get_text().replace("\xa0", "").replace(" ", ""))
        elif "Platné hlasy" in text:
            data["valid"] = int(tds[i + 1].get_text().replace("\xa0", "").replace(" ", ""))

    # Hlasy stran
    # Hlasy stran
    party_votes = {}
    tables = soup.find_all("table", {"class": "table"})  # jen relevantní tabulky

    for table in tables:
        rows = table.find_all("tr")[2:]  # přeskoč hlavičky
        for row in rows:
            cells = row.find_all("td")
            if len(cells) >= 3:
                party = cells[1].get_text(strip=True)
                vote_text = cells[2].get_text(strip=True).replace('\xa0', '').replace(' ', '').replace(',', '')
                try:
                    votes = int(vote_text)
                except ValueError:
                    votes = 0
                party_votes[party] = votes

    data.update(party_votes)
    return data


def main():
    if len(sys.argv) != 3:
        print(" Zadej 2 argumenty: URL a výstupní soubor, např.:")
        print('python projekt_3.py "https://volby.cz/pls/ps2017nss/..." "vysledky.csv"')
        sys.exit(1)

    input_url = sys.argv[1]
    output_file = sys.argv[2]

    if not input_url.startswith("http") or "volby.cz" not in input_url:
        print(" Neplatný odkaz, musí být z domény volby.cz")
        sys.exit(1)

    print(" Stahuji seznam obcí ")
    obce = get_links_to_obce(input_url)

    print(f" Nalezeno {len(obce)} obcí ")

    results = []
    all_parties = set()

    for code, link in obce:
        data = get_obec_data(link)
        data["code"] = code
        results.append(data)
        all_parties.update(data.keys())

    parties = sorted([p for p in all_parties if p not in {"code", "location", "registered", "envelopes", "valid"}])
    fieldnames = ["code", "location", "registered", "envelopes", "valid"] + parties

    with open(output_file, mode="w", newline="", encoding="utf-8") as f:
        fieldnames = ["code", "location", "registered", "envelopes", "valid"] + parties
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for row in results:
            for party in parties:
                row.setdefault(party, 0)
            writer.writerow(row)

    print(f" Výsledky uloženy do {output_file}")


if __name__ == "__main__":
    main()