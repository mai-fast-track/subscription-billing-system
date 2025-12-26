"""
FastAPI application entry point
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware

from app.api.v1 import api_router
from app.core.config import settings
from app.core.database import db_manager
from app.core.logger import logger, setup_logging
from app.core.yookassa_manager import yookassa_manager

# logging.basicConfig(
#     level=logging.INFO,
#     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
#     stream=sys.stdout,
#     force=True
# )
# logger = logging.getLogger(__name__)

setup_logging()

# try:
#     yookassa_manager.configure()
#     logger.info("✅ Yookassa initialized")
# except Exception as e:
#     logger.error(f"❌ Yookassa init failed: {e}", exc_info=True)
#     raise


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # ===== STARTUP =====
    logger.info("Starting up FastAPI application...")
    try:
        # Инициализация БД
        from app.core.database import init_database

        init_database(debug=settings.DEBUG)

        # Инициализация админки (после инициализации БД)
        from app.core.admin import create_admin

        create_admin(app)
        logger.info("Admin panel initialized at /admin")

        # Инициализация YooKassa SDK
        if not settings.YOOKASSA_SHOP_ID or not settings.YOOKASSA_SECRET_KEY:
            raise RuntimeError("YOOKASSA_SHOP_ID / YOOKASSA_SECRET_KEY not set")

        yookassa_manager.configure()
        logger.info(
            f"YooKassa configuration initialized: account_id={str(settings.YOOKASSA_SHOP_ID)}, secret_key={settings.YOOKASSA_SECRET_KEY}"
        )
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        raise

    yield

    # ===== SHUTDOWN =====
    logger.info("Shutting down FastAPI application...")
    try:
        await db_manager.close()
        logger.info("Application shut down successfully")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


app = FastAPI(
    title="Billing Core API",
    description="Subscription billing system with payment processing",
    version="1.0.0",
    lifespan=lifespan,
)

# Session middleware для админки
app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)

# # CORS middleware
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=settings.CORS_ORIGINS,
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# Include routers
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    return {"message": "Billing Core API", "version": "1.0.0"}


@app.post("/")
async def root_post():
    """Обработчик POST на корневой путь для отладки webhook"""

    from app.core.logger import logger

    logger.warning("POST запрос получен на корневой путь / вместо /api/v1/payments/webhook")
    logger.warning("Проверьте настройки в личном кабинете Юкассы - должен быть указан полный путь!")
    return {
        "error": "Webhook endpoint находится по адресу /api/v1/payments/webhook",
        "message": "Укажите в настройках Юкассы полный URL: https://your-domain.ngrok.io/api/v1/payments/webhook",
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
