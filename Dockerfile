# Sử dụng Python image chính thức, phiên bản 3.10-slim
FROM python:3.10-slim-bullseye

# Thiết lập biến môi trường
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on

# Cài đặt các gói LaTeX cần thiết thay vì texlive-full
# và các công cụ hệ thống khác
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Các gói LaTeX cốt lõi
    texlive-luatex \
    texlive-fonts-recommended \
    texlive-lang-vietnamese \
    # Các gói cho đồ họa và toán học
    texlive-pictures \
    texlive-latex-extra \
    # Công cụ chuyển đổi PDF
    poppler-utils \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Thiết lập thư mục làm việc
WORKDIR /app

# Copy và cài đặt requirements
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy source code
COPY . .

# Mở cổng 5000
EXPOSE 5000

# Lệnh khởi động server Gunicorn
CMD ["gunicorn", "--workers", "2", "--threads", "4", "--timeout", "120", "--bind", "0.0.0.0:5000", "app:app"]