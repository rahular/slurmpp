from fastapi import APIRouter, Depends, HTTPException, status

from app.core.cache import cache
from app.core.exceptions import slurm_unavailable
from app.dependencies import CurrentUser, get_current_user
from app.slurm.client import get_client
from app.slurm.models import JobSubmitRequest, JobSubmitResponse

router = APIRouter(prefix="/api/v1/jobs", tags=["jobs"])


@router.post("/submit", response_model=JobSubmitResponse, status_code=status.HTTP_201_CREATED)
async def submit_job(
    req: JobSubmitRequest,
    current_user: CurrentUser = Depends(get_current_user),
):
    # Validate time limit (max 30 days)
    if req.time_limit_seconds > 30 * 24 * 3600:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"message": "Time limit exceeds 30 days", "code": "INVALID_TIME_LIMIT"},
        )
    if req.num_nodes < 1 or req.num_cpus_per_task < 1:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"message": "Nodes and CPUs must be >= 1", "code": "INVALID_RESOURCES"},
        )

    try:
        client = get_client()
        job_id = await client.submit_job(req, as_user=current_user.username)
        cache.invalidate_prefix("jobs:")
        cache.invalidate("cluster:overview")
        return JobSubmitResponse(job_id=job_id)
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"message": str(e), "code": "SUBMIT_FAILED"},
        )
    except Exception as e:
        raise slurm_unavailable()
