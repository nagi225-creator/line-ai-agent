"""
LINE自動応答AIエージェント - メインアプリケーション
FastAPIベースのWebhookサーバー
"""
import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException, Header
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

# 環境変数を読み込み
load_dotenv()

from config import get_settings
from app.database import db
from app.knowledge_base import knowledge_base
from app.ai_engine import initialize_ai_engine, ai_engine
from app.line_handler import initialize_line_handler, line_handler
from app.lstep_client import initialize_lstep_client, lstep_client

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """アプリケーションのライフサイクル管理"""
    # 起動時の初期化
    logger.info("Initializing application...")
    
    settings = get_settings()
    
    # データベース初期化
    await db.initialize()
    logger.info("Database initialized")
    
    # ナレッジベース読み込み
    knowledge_base.load()
    logger.info(f"Knowledge base loaded: {len(knowledge_base.success_cases)} cases, {len(knowledge_base.faqs)} FAQs")
    
    # AIエンジン初期化
    initialize_ai_engine(
        api_key=settings.openai_api_key,
        model=settings.openai_model
    )
    logger.info("AI engine initialized")
    
    # Lステップ連携初期化（設定がある場合のみ）
    if settings.lstep_enabled:
        initialize_lstep_client(
            api_key=settings.lstep_api_key,
            account_id=settings.lstep_account_id
        )
        logger.info("Lstep client initialized")
    else:
        logger.info("Lstep integration disabled (API key not configured)")
    
    # LINE Handler初期化
    initialize_line_handler(
        channel_access_token=settings.line_channel_access_token,
        channel_secret=settings.line_channel_secret,
        ai_mode_tag=settings.lstep_ai_mode_tag
    )
    logger.info("LINE handler initialized")
    
    logger.info("Application startup complete!")
    
    yield
    
    # シャットダウン時のクリーンアップ
    logger.info("Application shutdown")


# FastAPIアプリケーション
app = FastAPI(
    title="LINE自動応答AIエージェント",
    description="SnsClub LINE公式アカウント用 AI自動応答システム",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/")
async def root():
    """ヘルスチェック"""
    return {
        "status": "ok",
        "message": "LINE AI Agent is running",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    """詳細ヘルスチェック"""
    settings = get_settings()
    return {
        "status": "healthy",
        "components": {
            "database": "ok",
            "knowledge_base": {
                "success_cases": len(knowledge_base.success_cases),
                "faqs": len(knowledge_base.faqs)
            },
            "ai_engine": "ok" if ai_engine else "not initialized",
            "line_handler": "ok" if line_handler else "not initialized",
            "lstep_integration": {
                "enabled": settings.lstep_enabled,
                "ai_mode_tag": settings.lstep_ai_mode_tag,
                "status": "ok" if lstep_client else "disabled"
            }
        }
    }


@app.post("/webhook")
async def webhook(
    request: Request,
    x_line_signature: str = Header(None)
):
    """LINE Webhook エンドポイント"""
    if not x_line_signature:
        raise HTTPException(status_code=400, detail="Missing X-Line-Signature header")
    
    body = await request.body()
    body_str = body.decode('utf-8')
    
    logger.info(f"Received webhook: {body_str[:200]}...")
    
    try:
        if line_handler:
            # 署名検証
            if not line_handler.verify_signature(body_str, x_line_signature):
                raise HTTPException(status_code=400, detail="Invalid signature")
            
            # Webhookを処理
            line_handler.handler.handle(body_str, x_line_signature)
            
        return JSONResponse(content={"status": "ok"})
        
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/customers/{user_id}")
async def get_customer(user_id: str):
    """顧客情報を取得（管理用API）"""
    customer = await db.get_customer(user_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer.model_dump()


@app.get("/api/customers/{user_id}/messages")
async def get_customer_messages(user_id: str, limit: int = 50):
    """顧客の会話履歴を取得（管理用API）"""
    messages = await db.get_conversation_history(user_id, limit=limit)
    return [msg.model_dump() for msg in messages]


@app.get("/api/knowledge/cases")
async def get_success_cases():
    """成功事例一覧を取得"""
    return [case.model_dump() for case in knowledge_base.success_cases]


@app.get("/api/knowledge/faqs")
async def get_faqs():
    """FAQ一覧を取得"""
    return [faq.model_dump() for faq in knowledge_base.faqs]


if __name__ == "__main__":
    import uvicorn
    
    settings = get_settings()
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
