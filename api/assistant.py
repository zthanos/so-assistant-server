from inspect import getmembers
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel
from app.logger import get_logger
from app.diagrams.generate_diagrams import generate_c4_diagram as c4_diagram



# Το prefix περιέχει ήδη το {project_id}
router = APIRouter(prefix="/assistant", tags=["Assistant"])
logger = get_logger()


class SequenceToC4Request(BaseModel):
    content: str
    c4_type: int  # 1 για System Context, 2 για Container




@router.post("/c4diagram", response_model=dict)
async def generate_c4_diagram(request: SequenceToC4Request):
    logger.info(f"request: {request}")
    try:
        response = c4_diagram(request.content, request.c4_type)
        logger.info("============================")
        logger.debug(response)
        logger.info("============================")
        return {
            "diagram": "diagram",
            "explanation": "explanation"
        }
    except ValueError as e:
        logger.error(e)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=500, detail="Internal server error")

   



    