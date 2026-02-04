# -*- coding: UTF-8 -*-
from fastapi import APIRouter
import hashlib
import json
import uuid
import requests
from throttled import Throttled, per_sec, MemoryStore

from constants import VolcengineASRResponseStatusCode, AsrTaskStatus
from models import FileNameRequest
from core.exceptions import BusinessException, ExternalServiceException
from core.response import success_response, APIResponse
from config.log import get_logger
import env
from utils.s3 import generate_download_url

router = APIRouter(prefix="/audio", tags=["Audio"])
logger = get_logger(__name__)
STORE = MemoryStore()


def generate_local_uuid():
    """生成本地UUID"""
    mac = uuid.getnode()
    mac_address = ":".join(("%012X" % mac)[i : i + 2] for i in range(0, 12, 2))
    md5_obj = hashlib.md5(mac_address.encode("utf-8"))
    return md5_obj.hexdigest()


@router.post("/transcription-tasks", response_model=APIResponse)
async def create_transcription_task(request: FileNameRequest):
    """创建音频转写任务

    RESTful路径: POST /api/v1/audio/transcription-tasks
    """
    logger.info(f"Creating transcription task for file: {request.filename}")

    try:
        submit_url = "https://openspeech.bytedance.com/api/v3/auc/bigmodel/submit"
        download_url = generate_download_url(request.filename)

        data = {
            "user": {
                "uid": generate_local_uuid(),
            },
            "audio": {"format": "mp3", "url": download_url},
            "request": {"model_name": "bigmodel", "enable_itn": True},
        }

        headers = {
            "Content-Type": "application/json",
            "X-Api-App-Key": env.AUC_APP_ID,
            "X-Api-Access-Key": env.AUC_ACCESS_TOKEN,
            "X-Api-Resource-Id": env.AUC_CLUSTER_ID,
            "X-Api-Request-Id": str(uuid.uuid4()),
            "X-Api-Sequence": "-1",
        }

        with Throttled(
            key=env.AUC_APP_ID, store=STORE, quota=per_sec(limit=100, burst=100)
        ):
            response = requests.post(submit_url, data=json.dumps(data), headers=headers)

        response.raise_for_status()
        
        # 新版 API 状态码在 headers 中
        status_code = response.headers.get("X-Api-Status-Code")
        message = response.headers.get("X-Api-Message", "")
        task_id = headers["X-Api-Request-Id"]  # 使用请求时的 UUID 作为 task_id

        if status_code != "20000000":
            logger.error(f"ASR service returned error: {status_code} - {message}")
            raise ExternalServiceException(
                "Volcengine ASR", f"Submit task failed: {message}"
            )

        logger.info(f"Transcription task created successfully with ID: {task_id}")

        return success_response(
            data={"task_id": task_id}, message="Transcription task created successfully"
        )

    except requests.RequestException as e:
        logger.error(f"Request failed when creating transcription task: {str(e)}")
        raise ExternalServiceException("Volcengine ASR", f"Request failed: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error when creating transcription task: {str(e)}")
        raise BusinessException(f"Failed to create transcription task: {str(e)}")


@router.get("/transcription-tasks/{task_id}", response_model=APIResponse)
async def get_transcription_task(task_id: str):
    """获取音频转写任务状态

    RESTful路径: GET /api/v1/audio/transcription-tasks/{task_id}
    """
    logger.info(f"Querying transcription task status: {task_id}")

    try:
        query_url = "https://openspeech.bytedance.com/api/v3/auc/bigmodel/query"

        headers = {
            "Content-Type": "application/json",
            "X-Api-App-Key": env.AUC_APP_ID,
            "X-Api-Access-Key": env.AUC_ACCESS_TOKEN,
            "X-Api-Resource-Id": env.AUC_CLUSTER_ID,
            "X-Api-Request-Id": task_id,  # 使用提交时的 task_id
            "X-Api-Sequence": "-1",
        }

        with Throttled(
            key=env.AUC_APP_ID, store=STORE, quota=per_sec(limit=100, burst=100)
        ):
            response = requests.post(query_url, json={}, headers=headers)

        response.raise_for_status()
        
        # 获取状态码
        status_code = response.headers.get("X-Api-Status-Code")
        message = response.headers.get("X-Api-Message", "")
        
        # 20000000 表示成功
        if status_code == "20000000":
            resp = response.json()
            
            # 新版 API 响应格式：{"result": {"text": "...", "utterances": [...]}}
            if "result" in resp and "utterances" in resp["result"]:
                utterances = resp["result"]["utterances"]
                result = [
                    {
                        "start_time": utterance["start_time"],
                        "end_time": utterance["end_time"],
                        "text": utterance["text"],
                    }
                    for utterance in utterances
                ]

                logger.info(f"Transcription task {task_id} completed successfully")

                return success_response(
                    data={"status": AsrTaskStatus.FINISHED.value, "result": result},
                    message="Transcription completed",
                )
            else:
                # 可能还在处理中
                logger.info(f"Transcription task {task_id} is still running")
                return success_response(
                    data={"status": AsrTaskStatus.RUNNING.value, "result": None},
                    message="Transcription in progress",
                )
        
        # 其他状态码表示失败或进行中
        elif status_code in ["20000001", "20000002"]:  # 进行中的状态码
            logger.info(f"Transcription task {task_id} is still running")
            return success_response(
                data={"status": AsrTaskStatus.RUNNING.value, "result": None},
                message="Transcription in progress",
            )
        else:
            logger.error(f"Transcription task {task_id} failed with code: {status_code} - {message}")
            return success_response(
                data={"status": AsrTaskStatus.FAILED.value, "result": None},
                message="Transcription failed",
            )

    except requests.RequestException as e:
        logger.error(
            f"Request failed when querying transcription task {task_id}: {str(e)}"
        )
        raise ExternalServiceException(
            "Volcengine ASR", f"Query request failed: {str(e)}"
        )
    except Exception as e:
        logger.error(
            f"Unexpected error when querying transcription task {task_id}: {str(e)}"
        )
        raise BusinessException(f"Failed to query transcription task: {str(e)}")
