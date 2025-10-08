# Sử dụng Python image chính thức, phiên bản 3.10-slim
FROM python:3.10-slim-bullseye

# Thiết lập biến môi trường để tránh lỗi và giúp log tốt hơn
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on

# Cài đặt các công cụ hệ thống cần thiết (LaTeX và Poppler)
# Chạy tất cả trong một lớp để tối ưu
RUN apt-get update && apt-get install -y --no-install-recommends \
    texlive-full \
    poppler-utils \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# ================================================================
# === BƯỚC THÊM VÀO: Khởi tạo font cache của lualatex ===
# Chạy một lần lualatex "nháp" để nó xây dựng cache font hệ thống.
# Điều này giúp lần chạy thực tế đầu tiên (khi có request) nhanh hơn nhiều.
RUN lualatex -interaction=nonstopmode -halt-on-error -output-directory=/tmp "\\documentclass{article}\\begin{document}Cache\\end{document}"
# ================================================================

# Thiết lập thư mục làm việc bên trong container
WORKDIR /app

# Copy file requirements trước để tận dụng Docker cache
COPY requirements.txt .

# Cài đặt các thư viện Python
RUN pip install -r requirements.txt

# Copy toàn bộ source code của ứng dụng vào thư mục làm việc
COPY . .

# Mở cổng 5000 để Render có thể kết nối vào
EXPOSE 5000

# Lệnh để khởi động server Gunicorn khi container chạy
CMD ["gunicorn", "--workers", "2", "--threads", "4", "--timeout", "120", "--bind", "0.0.0.0:5000", "app:app"]