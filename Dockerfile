# Sử dụng Python image chính thức, phiên bản 3.10-slim
FROM python:3.10-slim-bullseye

# Thiết lập biến môi trường
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# Cài đặt TeX Live (bản đầy đủ) và Poppler-utils (để chuyển PDF->SVG/PNG)
# Đây là lớp nền tảng mạnh mẽ nhất
RUN apt-get update && apt-get install -y --no-install-recommends \
    texlive-full \
    poppler-utils \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Thiết lập thư mục làm việc
WORKDIR /app

# Cài đặt Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code của ứng dụng
COPY . .

# Mở cổng 5000
EXPOSE 5000

# Chạy ứng dụng bằng Gunicorn cho môi trường production
# --workers 2: Sử dụng 2 tiến trình để xử lý request đồng thời
# --timeout 120: Tăng timeout lên 120 giây vì biên dịch LaTeX có thể mất thời gian
CMD ["gunicorn", "--workers", "2", "--timeout", "120", "--bind", "0.0.0.0:5000", "app:app"]