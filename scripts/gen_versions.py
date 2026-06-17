import os, shutil, json, datetime

ROOT = "D:\\大论文"
VERSIONS_DIR = os.path.join(ROOT, "版本迭代")
SRC_BACKEND = os.path.join(ROOT, "backend", "app")
SRC_FRONTEND = os.path.join(ROOT, "frontend", "src")

os.makedirs(VERSIONS_DIR, exist_ok=True)

def copy_dir(src, dst):
    if os.path.exists(dst):
        shutil.rmtree(dst)
    shutil.copytree(src, dst)

def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

def ensure_dir(path):
    os.makedirs(path, exist_ok=True)

# ============================================================
# VERSION 4: 当前完整版本 (Current Complete Version)
# ============================================================
def create_v4():
    v4_dir = os.path.join(VERSIONS_DIR, "v4_完整版本")
    ensure_dir(v4_dir)

    # Copy backend/app
    dst_backend = os.path.join(v4_dir, "backend", "app")
    if os.path.exists(dst_backend):
        shutil.rmtree(dst_backend)
    shutil.copytree(SRC_BACKEND, dst_backend)

    # Copy frontend/src
    dst_frontend = os.path.join(v4_dir, "frontend", "src")
    if os.path.exists(dst_frontend):
        shutil.rmtree(dst_frontend)
    shutil.copytree(SRC_FRONTEND, dst_frontend)

    # Copy docker-compose
    shutil.copy2(os.path.join(ROOT, "docker-compose.yml"), os.path.join(v4_dir, "docker-compose.yml"))
    shutil.copy2(os.path.join(ROOT, "backend", "requirements.txt"), os.path.join(v4_dir, "backend", "requirements.txt"))
    shutil.copy2(os.path.join(ROOT, ".gitignore"), os.path.join(v4_dir, ".gitignore"))
    shutil.copy2(os.path.join(ROOT, "PROJECT_STATE.md"), os.path.join(v4_dir, "PROJECT_STATE.md"))

    # Copy experiment scripts
    dst_exp = os.path.join(v4_dir, "scripts", "experiment")
    ensure_dir(dst_exp)
    for f in ["dataset.py", "results.json", "experiment_export.json"]:
        src = os.path.join(ROOT, "scripts", "experiment", f)
        if os.path.exists(src):
            shutil.copy2(src, dst_exp)

    write_file(os.path.join(v4_dir, "README.md"), """# VulnForge - v4 完整版本 (Final Version)

## 状态: 全部完成

### 功能
- Backend API: 16 routes, 完整 CRUD
- Scanner Engine: nuclei/dalfox/ffuf/sqlmap 全部调通
- LLM Analysis: Zero-shot / Few-shot / Chain-of-Thought
- Frontend: React + Ant Design, 6 pages, 图表可视化
- Docker: PostgreSQL, Redis, Juice Shop, DVWA, WebGoat
- Experiment: 72 curated findings, McNemar's test, Stratified analysis
- Real Scans: 14 findings (Juice Shop 5 + DVWA 9)

### 已修复 Bug (9个)
1. DVWA 登录 CSRF session 错配
2. Nuclei localhost 跳过
3. Dalfox --header vs --headers
4. GBK 编码
5. SQLMap 在 DVWA 不工作
6. Parser 参数数量不匹配
7. BOM 编码 (26个文件)
8. 后端子进程无超时
9. E2E pipeline 从未验证
""")

    print("  v4 完成")

create_v4()
print("All versions created")
