# Sử dụng Python image chính thức, phiên bản 3.10-slim-bookworm
FROM python:3.10-slim-bookworm

# Thiết lập biến môi trường
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    TEXMFHOME=/root/texmf

# Cài đặt các gói LaTeX cần thiết và công cụ hệ thống
RUN apt-get update && apt-get install -y --no-install-recommends \
    texlive-luatex \
    texlive-xetex \
    texlive-fonts-recommended \
    texlive-fonts-extra \
    texlive-lang-other \
    texlive-pictures \
    texlive-pstricks \
    texlive-latex-extra \
    texlive-science \
    poppler-utils \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Khởi tạo tlmgr user mode và cài packages contrib
RUN mkdir -p /root/texmf && \
    tlmgr init-usertree && \
    tlmgr --usermode repository https://ctan.math.illinois.edu/systems/texlive/tlnet && \
    tlmgr --usermode install tkz-tab tkz-euclide tikz-3dplot

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
CMD ["gunicorn", "--worker-class=gevent", "--workers", "2", "--threads", "4", "--timeout", "180", "--bind", "0.0.0.0:5000", "app:app"]