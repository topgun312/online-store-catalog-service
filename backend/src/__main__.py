import uvicorn
from loguru import logger

from src.config import settings

if __name__ == '__main__':
    if settings.LOG_TO_FILE:
        logger.add(
            settings.LOG_FILE,
            format='{time} {level} {message}',
            level='DEBUG',
            rotation='10 MB',
            compression='zip',
            serialize=True,
        )

    uvicorn.run(app='src.main:app', host='0.0.0.0', port=8000, reload=True)  # noqa: S104
