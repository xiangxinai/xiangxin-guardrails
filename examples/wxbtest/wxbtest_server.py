
import re
import copy
import uuid
import uvicorn
import os
import json
import time
import requests
import logging
import httpx
from datetime import datetime
from dotenv import load_dotenv
from argparse import ArgumentParser
from contextlib import asynccontextmanager
from logging.handlers import TimedRotatingFileHandler
from pydantic import BaseModel, Field
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Any, Dict, List, Literal, Optional, Union, Annotated, ClassVar
import qianfan
from xiangxinai import XiangxinAI


load_dotenv()

qianfan_ak = os.getenv("QIANFAN_AK", "")
qianfan_sk = os.getenv("QIANFAN_SK", "")
qianfan_chat_client = qianfan.ChatCompletion(ak=qianfan_ak, sk=qianfan_sk)

# 初始化xiangxinai客户端
xiangxinai_api_key = os.getenv("XIANGXINAI_API_KEY", "")
xiangxinai_client = XiangxinAI(xiangxinai_api_key) if xiangxinai_api_key else None


def _gc(forced: bool = False):
    import gc
    gc.collect()

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    _gc(forced=True)


app = FastAPI(lifespan=lifespan, openapi_url=None, docs_url=None, redoc_url=None)
security = HTTPBearer()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class UnicornException(Exception):
    def __init__(self, status_code: int, content: dict):
        self.status_code = status_code
        self.content = content

@app.exception_handler(UnicornException)
async def unicorn_exception_handler(request: Request, exc: UnicornException):
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.content,
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    print("validation_exception_handler", exc.errors())
    return JSONResponse(
        status_code=400,
        content={
            "error": {
                "message": "参数验证错误",
                "type": "invalid_request_error",
                "code": "invalid_params",
            }
        },
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    if exc.detail == "Not authenticated":
        return JSONResponse(
            status_code=401,
            content={
                "error": {
                    "message": "请求的API密钥不正确",
                    "type": "invalid_request_error",
                    "code": "invalid_api_key",
                }
            },
        )
    else:
        return JSONResponse(
            status_code=403,
            content={
                "error": {
                    "message": "请求处理网络异常",
                    "type": "invalid_request_error",
                    "code": "invalid_network",
                }
            },
        )

def _check_authorization(api_key):
    if not api_key or api_key not in API_KEY_ARRAY:
        raise UnicornException(
            status_code=401,
            content={
                "error": {
                    "message": "请求的API密钥不正确",
                    "type": "invalid_request_error",
                    "code": "invalid_api_key",
                }
            },
        )
    return api_key


def _check_model(model, allow_models):
    if not model or not allow_models or model not in allow_models:
        raise UnicornException(
            status_code=403,
            content={
                "error": {
                    "message": "请求的模型无权限",
                    "type": "invalid_request_error",
                    "code": "invalid_model",
                }
            },
        )
    return model

class ChatMessage(BaseModel):
    role: Literal["user", "model"]
    content: list | str | dict

class ChatCompletionRequest(BaseModel):
    model: str
    dialogue: List[ChatMessage]
    stream: Optional[bool] = False
    max_tokens: Optional[int] = 0

class ChatCompletionResponseStreamChoice(BaseModel):
    delta: Optional[str]
    finish_reason: Optional[str]

class ChatCompletionResponse(BaseModel):
    id: str
    status: str
    reason: str
    # model: str
    # object: Literal["chat.completion", "chat.completion.chunk", "chat.completion.async"]
    # created: Optional[int] = Field(default_factory=lambda: int(time.time()))
    content: Optional[str]
    # choices: Optional[List[ChatCompletionResponseStreamChoice]]


API_KEY_ARRAY = [
    "xxai-sk-E3TkDWsFQvQBYGHSSJYMXMWtfbszmQ2crvjnFNurV78dc", # 备案网信测试
]

ALLOW_MODEL_DICT = {
    "text": "Xiangxin-3-text",
}
ALLOW_MODEL_ARRARY = list(ALLOW_MODEL_DICT.values())

_TEXT_COMPLETION_CMD = object()

def _is_json(myjson):
    try:
        json.loads(myjson)
    except ValueError:
        return False
    return True

def get_logger(name):
    log_path = os.getenv("LOGS_DIR", "logs")
    logger = logging.getLogger(name)
    # 判断目录是否存在，存在不创建，不存在则创建log目录
    if os.path.exists(log_path):
        pass
    else:
        os.mkdir(log_path)
    # 设置日志基础级别
    logger.setLevel(logging.DEBUG)
    # 日志格式
    formatter = "%(asctime)s wxbrecord [%(levelname)s] %(message)s '%(name)s'"

    log_formatter = logging.Formatter(formatter)
    # 控制台日志
    # console_handler = logging.StreamHandler()
    # console_handler.setFormatter(log_formatter)

    # info日志文件名
    info_file_name = (
        "access." + time.strftime("%Y%m%d", time.localtime(time.time())) + ".log"
    )

    """
    #实例化TimedRotatingFileHandler
    # filename：日志文件名
    # when：日志文件按什么切分。'S'-秒；'M'-分钟；'H'-小时；'D'-天；'W'-周
    #       这里需要注意，如果选择 D-天，那么这个不是严格意义上的'天'，是从你
    #       项目启动开始，过了24小时，才会重新创建一个新的日志文件，如果项目重启，
    #       这个时间就会重置。选择'MIDNIGHT'-是指过了凌晨12点，就会创建新的日志
    # interval是时间间隔
    # backupCount：是保留日志个数。默认的0是不会自动删除掉日志。如果超过这个个数，就会自动删除  
    """
    info_handler = TimedRotatingFileHandler(
        filename=log_path + "/" + info_file_name,
        when="MIDNIGHT",
        interval=1,
        encoding="utf-8",
    )
    # 设置文件里写入的格式
    info_handler.setFormatter(log_formatter)
    info_handler.setLevel(logging.DEBUG)
    # 添加日志处理器
    logger.addHandler(info_handler)
    # logger.addHandler(console_handler)
    return logger


def close_logger(logger):
    for handler in logger.handlers[:]:
        handler.close()
        logger.removeHandler(handler)

async def predict_error(content: dict):
    chunk_error_json = json.dumps(content, ensure_ascii=False)
    yield f"data: {chunk_error_json}\n\n"
    yield "data: [DONE]\n\n"

def chunk_in_segments(text, segments=10):
    segment_length = len(text) # segments
    if segment_length == 0:
        segment_length = 1
    result = []
    start = 0
    for i in range(segments):
        # 计算结束位置
        end = start + segment_length
        if i == segments - 1:
            end = len(text)
        # print(start, end, text[start:end])
        result.append(text[start:end])
        start = end
    return result

def get_chat_messages(system_prompt, userLastQuery, history):
    messages = []
    max_length = 1000
    if system_prompt:
        system_message = {"role": "system", "content": system_prompt}
        messages.insert(0, system_message)

    if history and len(history) > 0:
        # 保留最后两对
        history_trimmed = history[-2:]
        history_trimmed = [[truncate_text(pair[0], pair[1], max_length), pair[1][:max_length]] for pair in history_trimmed]

        for pair in history_trimmed:
            messages.append({
                "role": "user",
                "content": pair[0]
            })
            messages.append({
                "role": "assistant",
                "content": pair[1]
            })

    content = (
f"""---
我的问题：
{userLastQuery}
---

请回复我的问题。回答一定忠于原文，简洁但不丢信息，不要胡乱编造。我的问题或指令是什么语种，你就用什么语种回复。

你的回复：
"""
    )

    new_message = {"role": "user", "content": userLastQuery}
    # new_message = {"role": "user", "content": content}
    messages.append(new_message)

    return messages

def truncate_text(text1, text2, max_length=1000):
    combined_length = len(text1) + len(text2)
    if combined_length > max_length:
        excess_length = combined_length - max_length
        if excess_length <= 0:
            text1 = text1[:10]
        else:
            text1 = text1[:excess_length]
    return text1

async def predict(res_id, logger, endpoint, messages, temperature, max_output_tokens):
    supported = False
    if not supported:
        completionRes = ChatCompletionResponse(
            id=res_id,
            status="failed",
            reason="not_supported_stream",
            content="",
            choices=[{
                "delta": "",
                "finish_reason": "stop"
            }]
        )
        logger.info(f"response failed {completionRes.model_dump_json()}")
        yield f"data: {completionRes.model_dump_json()}\n\n"
        return

    try:
        resp = qianfan_chat_client.do(
            stream=True,
            endpoint=endpoint,
            messages=messages,
            temperature=temperature,
            max_output_tokens=max_output_tokens
        )
        
        all_text = ""
        for row in resp:
            row_text = row["body"]["result"]
            is_end = row["body"]["is_end"]

            all_text += row_text

            if not is_end:
                completionRes = ChatCompletionResponse(
                    id=res_id,
                    status="success",
                    reason="success",
                    content=row_text,
                    choices=[{
                        "delta": row_text,
                        "finish_reason": ""
                    }]
                )
            else:
                completionRes = ChatCompletionResponse(
                    id=res_id,
                    status="success",
                    reason="success",
                    content="",
                    choices=[{
                        "delta": "",
                        "finish_reason": "stop"
                    }]
                )

            yield f"data: {completionRes.model_dump_json()}\n\n"
        
        completionStreamRes = ChatCompletionResponse(
            id=res_id,
            status="success",
            reason="success",
            content="",
            choices=[{
                "delta": all_text,
                "finish_reason": "stop"
            }]
        )
        logger.info(f"response stream success {completionStreamRes.model_dump_json()}")

    except Exception as e:
        print('predict Exception', e)
        completionRes = ChatCompletionResponse(
            id=res_id,
            status="failed",
            reason="service_exception",
            content="",
            choices=[{
                "delta": "",
                "finish_reason": "stop"
            }]
        )
        logger.info(f"response failed {completionRes.model_dump_json()}")
        yield f"data: {completionRes.model_dump_json()}\n\n"


def dialogue_to_messages(dialogue):
    """
    将dialogue结构转换为messages结构
    按顺序处理：先找到第一个role为user的消息，然后依次处理
    role为user保持不变，role为model改为assistant，其他角色忽略
    """
    messages = []
    
    for msg in dialogue:
        role = msg.role
        content = msg.content
        
        if isinstance(content, str):
            content = content.strip()
        
        if role == "user":
            messages.append({"role": "user", "content": content})
        elif role == "model":
            messages.append({"role": "assistant", "content": content})
        # 忽略其他角色
    
    return messages

def check_conversation_safety(messages, logger):
    """
    使用xiangxinai检查对话安全性
    直接使用messages格式
    返回: (is_safe, suggest_answer, category)
    """
    if not xiangxinai_client:
        logger.warning("xiangxinai客户端未初始化，跳过安全检查")
        return True, None, None
    
    try:
        response = xiangxinai_client.check_conversation(messages)
        logger.debug(f"xiangxinai检查结果: {response.overall_risk_level}")
        
        if response.overall_risk_level != "no_risk":
            # 发现了风险，返回护栏代答
            suggest_answer = response.suggest_answer if hasattr(response, 'suggest_answer') else "作为一名AI助手，我无法回答您提出的这个问题。"
            return False, suggest_answer, response.all_categories[0]
        else:
            return True, None, None
            
    except Exception as e:
        logger.error(f"xiangxinai安全检查异常: {e}")
        # 异常情况下默认安全
        return True, None, None

def check_answer_safety(messages, answer, logger):
    """
    使用xiangxinai检查模型回答的安全性
    将模型回答添加到messages的最后进行检查
    返回: (is_safe, suggest_answer, category)
    """
    if not xiangxinai_client:
        logger.warning("xiangxinai客户端未初始化，跳过回答安全检查")
        return True, None, None
    
    # 创建包含模型回答的完整messages（不修改原始messages）
    messages_with_answer = messages.copy()
    messages_with_answer.append({"role": "assistant", "content": answer})
    
    try:
        response = xiangxinai_client.check_conversation(messages_with_answer)
        logger.debug(f"xiangxinai回答检查结果: {response.overall_risk_level}")
        
        if response.overall_risk_level != "no_risk":
            suggest_answer = response.suggest_answer if hasattr(response, 'suggest_answer') else "作为一名AI助手，我无法回答您提出的这个问题。"
            return False, suggest_answer, response.all_categories[0]
        else:
            return True, None, None
            
    except Exception as e:
        logger.error(f"xiangxinai回答安全检查异常: {e}")
        return True, None, None

def dialogue_chat(request):
    stream = request.stream
    max_output_tokens = request.max_tokens if request.max_tokens else None
    temperature=0.1
    api_model_name="ernie-lite-8k"

    request_json = request.model_dump_json()
    request_data = json.loads(request_json)

    # 一次性将dialogue转换为messages格式，后续流程都使用这个messages
    messages = dialogue_to_messages(request.dialogue)

    res_id = f"dialogue-{uuid.uuid1().hex}"

    current_date = datetime.now().date()
    formatted_date = current_date.strftime("%Y%m%d")

    logger = get_logger(res_id)
    logger.info(f"messages {json.dumps(messages, ensure_ascii=False)}")

    # 使用xiangxinai进行输入安全检查
    is_safe, suggest_answer, category = check_conversation_safety(messages, logger)
    if not is_safe:
        completionRes = ChatCompletionResponse(
            id=res_id,
            status="failed",
            reason=category,
            content=suggest_answer,
            # choices=[]
        )
        logger.info(f"response failed {completionRes.model_dump_json()}")
        return completionRes

    # 直接使用转换后的messages进行模型调用
    chat_messages = messages

    if not stream:
        try:
            resp = qianfan_chat_client.do(
                endpoint=api_model_name,
                messages=chat_messages,
                temperature=temperature,
                max_output_tokens=max_output_tokens
            )

            if resp.code == 200 and resp.body:
                answer = resp.body["result"]

                # 检查模型回答的安全性（使用同一个messages）
                answer_is_safe, answer_suggest, answer_category = check_answer_safety(messages, answer, logger)
                if not answer_is_safe:
                    completionRes = ChatCompletionResponse(
                        id=res_id,
                        status="failed",
                        reason=answer_category,
                        content=answer_suggest,
                        # choices=[]
                    )
                    logger.info(f"response failed {completionRes.model_dump_json()}")
                    return completionRes

                completionRes = ChatCompletionResponse(
                    id=res_id,
                    status="success",
                    reason="success",
                    content=answer,
                    # choices=[]
                )
                logger.info(f"response success {completionRes.model_dump_json()}")
                close_logger(logger)

                return completionRes
            else:
                completionRes = ChatCompletionResponse(
                    id=res_id,
                    status="failed",
                    reason="service_exception",
                    content="",
                    # choices=[],
                )
                logger.warn(f"response failed {completionRes.model_dump_json()}")

                return completionRes
        except Exception as e:
            logger.error(f"error {e}")

            completionRes = ChatCompletionResponse(
                id=res_id,
                status="failed",
                reason="service_exception",
                content="",
                # choices=[],
            )
            logger.warn(f"response failed {completionRes.model_dump_json()}")
    else:
        generate = predict(
            res_id,
            logger=logger, 
            endpoint=api_model_name,
            messages=chat_messages,
            temperature=temperature,
            max_output_tokens=max_output_tokens
        )
        return StreamingResponse(generate, media_type="text/event-stream")
        pass


@app.post("/v1/dialogue", response_model=ChatCompletionResponse)
def create_chat_completion(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    request: ChatCompletionRequest,
) -> Any:
    api_key = credentials.credentials
    _check_authorization(api_key)
    _check_model(
        request.model,
        [ALLOW_MODEL_DICT["text"]],
    )

    result = None
    if request.model == ALLOW_MODEL_DICT["text"]:
        result = dialogue_chat(request)
        pass

    return result

def _get_args():
    server_name = os.getenv("DEFAULT_SERVER_NAME")
    server_port = os.getenv("DEFAULT_SERVER_PORT")

    parser = ArgumentParser()
    parser.add_argument(
        "--server-name",
        type=str,
        default=server_name,
        help="server name. Default: 127.0.0.1, which is only visible from the local computer."
        " If you want other computers to access your server, use 0.0.0.0 instead.",
    )
    parser.add_argument(
        "--server-port", type=int, default=server_port, help="server port."
    )

    args = parser.parse_args()
    return args


if __name__ == "__main__":
    args = _get_args()

    uvicorn.run("__main__:app", host=args.server_name, port=args.server_port, workers=2)
