# Dockerfile cho LaTeX Rendering Service (Python + Flask)

# Giai đoạn 1: Builder - Cài đặt tất cả dependencies
FROM python:3.10-slim-bullseye AS builder

# Thiết lập biến môi trường
ENV DEBIAN_FRONTEND=noninteractive \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100

# Cài đặt TeX Live và các công cụ cần thiết
# Sử dụng texlive-latex-extra và texlive-fonts-extra để có các gói phổ biến
RUN apt-get update && apt-get install -y --no-install-recommends \
    texlive-latex-extra \
    texlive-fonts-extra \
    texlive-luatex \
    poppler-utils \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Thiết lập thư mục làm việc
WORKDIR /app

# Cài đặt Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# =========================================================================
# Giai đoạn 2: Final - Image cuối cùng, nhẹ hơn
# =========================================================================
FROM python:3.10-slim-bullseye

# Thiết lập biến môi trường
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1

# Cài đặt các thư viện hệ thống tối thiểu cần thiết để chạy
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpoppler-cpp0v5 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy các file thực thi và thư viện đã được cài đặt từ giai đoạn builder
COPY --from=builder /usr/lib/ /usr/lib/
COPY --from=builder /usr/share/texlive /usr/share/texlive
COPY --from=builder /usr/local/bin/ /usr/local/bin/
COPY --from=builder /usr/bin/lualatex /usr/bin/lualatex
COPY --from=builder /usr/bin/pdftocairo /usr/bin/pdftocairo
COPY --from=builder /app /app

# Copy source code ứng dụng (đã được copy trong bước trên nhưng copy lại để chắc chắn)
COPY app.py ./
COPY scheduler.py ./

EXPOSE 5000

# Chạy ứng dụng bằng Gunicorn
CMD ["gunicorn", "--workers", "2", "--threads", "4", "--timeout", "120", "--bind", "0.0.0.0:5000", "app:app"]