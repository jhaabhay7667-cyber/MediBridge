import httpx

from fastapi import APIRouter, HTTPException, Query

from ..services.medicine_guide import search_medicine

router = APIRouter(
    prefix="/api/medicines",
    tags=["medicine-guide"],
)


@router.get("/search")
async def medicine_search(
    q: str = Query(..., min_length=2, max_length=100),
):
    try:
        results = await search_medicine(q)

        return {
            "query": q,
            "count": len(results),
            "source": "US FDA public drug labeling data",
            "notice": (
                "This information is for education only. "
                "It is not a prescription or a substitute for a "
                "doctor or pharmacist. US FDA label data does not "
                "confirm approval or availability in India. "
                "Do not use it to decide a dose or change treatment."
            ),
            "medicines": results,
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    except httpx.HTTPStatusError:
        raise HTTPException(
            status_code=502,
            detail="The public medicine information service returned an error.",
        )

    except httpx.RequestError:
        raise HTTPException(
            status_code=503,
            detail="Medicine information is temporarily unavailable. Please try again.",
        )

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Unable to search medicine information right now.",
        )