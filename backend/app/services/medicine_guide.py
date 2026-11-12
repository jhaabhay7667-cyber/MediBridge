import re
import httpx

OPENFDA_URL = "https://api.fda.gov/drug/label.json"

USER_AGENT = "MediBridge/1.0 (medicine information guide)"


def clean_search_term(value: str) -> str:
    """
    Keep search input simple and prevent openFDA query syntax injection.
    """
    value = re.sub(r"[^a-zA-Z0-9\s-]", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value[:100]


def extract_section(record, *keys):
    """
    Return the first available label section.
    """
    for key in keys:
        value = record.get(key)

        if isinstance(value, list):
            text = "\n".join(str(item) for item in value if item)

            if text.strip():
                return text[:5000]

        elif isinstance(value, str) and value.strip():
            return value[:5000]

    return None


async def search_medicine(medicine_name: str):
    term = clean_search_term(medicine_name)

    if len(term) < 2:
        raise ValueError("Enter at least 2 valid characters.")

    # Search generic and brand names in public FDA label records.
    search_query = (
        f'openfda.generic_name:"{term}" OR '
        f'openfda.brand_name:"{term}"'
    )

    params = {
        "search": search_query,
        "limit": 5,
    }

    async with httpx.AsyncClient(
        timeout=20.0,
        headers={"User-Agent": USER_AGENT},
    ) as client:

        response = await client.get(
            OPENFDA_URL,
            params=params,
        )

        if response.status_code == 404:
            return []

        response.raise_for_status()
        payload = response.json()

    medicines = []

    for record in payload.get("results", []):
        openfda = record.get("openfda", {})

        brands = openfda.get("brand_name", [])
        generics = openfda.get("generic_name", [])
        manufacturers = openfda.get("manufacturer_name", [])

        medicines.append({
            "brand_names": brands[:5],
            "generic_names": generics[:5],
            "manufacturers": manufacturers[:5],

            "purpose": extract_section(
                record,
                "purpose",
                "indications_and_usage",
            ),

            "indications_and_usage": extract_section(
                record,
                "indications_and_usage",
            ),

            "warnings": extract_section(
                record,
                "warnings",
                "warnings_and_cautions",
            ),

            "contraindications": extract_section(
                record,
                "contraindications",
            ),

            "adverse_reactions": extract_section(
                record,
                "adverse_reactions",
            ),

            "drug_interactions": extract_section(
                record,
                "drug_interactions",
            ),

            "effective_time": record.get("effective_time"),

            "source": "US FDA public drug labeling data",
            "source_url": (
                "https://open.fda.gov/apis/drug/label/"
            ),
        })

    return medicines