# ENVIRONMENT_LOCK.md

## Runtime Environment（鎖定，不得自行更改）
- OS: Debian 12 (LXC)
- Python: 3.11.x
- PostgreSQL: 15.x
- Virtualenv: venv

## Python Dependencies
- 所有 Python 套件版本以 `requirements.txt` 為準
- 禁止在未更新 requirements.txt 的情況下新增或升級套件
- 禁止引入 async SQLAlchemy、asyncpg、Celery、Redis（除非明確指示）

## Development Rules
- Cursor 不得指示重建 LXC 或修改系統層環境
- 若功能需要新套件，必須先說明原因並請求允許
