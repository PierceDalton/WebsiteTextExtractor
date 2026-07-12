from fastapi import FastAPI
from pydantic import BaseModel
import requests
import trafilatura
from urllib.parse import urlparse, unquote


app = FastAPI(title="BURYA Website Extractor API")


class ExtractRequest(BaseModel):
    url: str


@app.get("/")
def home():
    return {
        "status": "Server is running!"
    }


def get_page(url: str):

    session = requests.Session()

    session.headers.update({
        "User-Agent": (
            "Mozilla/5.0 "
            "(Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 "
            "(KHTML, like Gecko) "
            "Chrome/138.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": (
            "text/html,"
            "application/xhtml+xml,"
            "application/xml;q=0.9,"
            "image/avif,"
            "image/webp,"
            "*/*;q=0.8"
        )
    })

    response = session.get(
        url,
        timeout=30
    )

    response.raise_for_status()

    return response.text



def extract_wikipedia_section(text: str, url: str):

    parsed = urlparse(url)

    if (
        "wikipedia.org" not in parsed.netloc
        or not parsed.fragment
    ):
        return text


    section = unquote(
        parsed.fragment
    ).replace("_", " ").lower()


    text = text.replace(
        "[edit]",
        ""
    )


    lines = text.splitlines()


    start = None


    for i, line in enumerate(lines):

        if line.strip().lower() == section:

            start = i
            break


    if start is None:

        return text


    result = []


    for line in lines[start:]:

        clean = line.strip()


        if (
            clean
            and clean.lower() != section
            and len(clean.split()) <= 8
            and clean[0].isupper()
        ):
            break


        result.append(line)


    return "\n".join(result)



@app.post("/extract")
def extract(request: ExtractRequest):

    try:

        downloaded = get_page(
            request.url
        )


        metadata = trafilatura.extract_metadata(
            downloaded
        )


        text = trafilatura.extract(
            downloaded,
            include_links=False,
            include_tables=True
        )


        if not text:

            return {
                "success": False,
                "url": request.url,
                "error": "No readable content found."
            }


        # Wikipedia section filtering
        text = extract_wikipedia_section(
            text,
            request.url
        )


        title = None

        if metadata:
            title = metadata.title


        return {
            "success": True,
            "url": request.url,
            "title": title,
            "content": text
        }


    except Exception as e:

        return {
            "success": False,
            "url": request.url,
            "error": str(e)
        }
