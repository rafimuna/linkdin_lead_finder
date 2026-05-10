import requests
from bs4 import BeautifulSoup


def search_linkedin_profiles(keyword):

    query = f"site:linkedin.com/in {keyword}"

    url = "https://www.google.com/search"

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/135.0 Safari/537.36"
        )
    }

    params = {
        "q": query
    }

    response = requests.get(
        url,
        headers=headers,
        params=params
    )

    print(response.status_code)

    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )

    links = []

    for link in soup.find_all("a"):

        href = link.get("href")

        if href and "linkedin.com/in/" in href:

            clean_url = href.split("&")[0]

            clean_url = clean_url.replace("/url?q=", "")

            if clean_url not in links:
                links.append(clean_url)

    return links