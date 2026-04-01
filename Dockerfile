FROM python:3.11-slim

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制代码
COPY . .

# 暴露端口
EXPOSE 8000

# 抖音云要求 run.sh 在 /opt/application/
RUN mkdir -p /opt/application && cp run.sh /opt/application/run.sh && chmod +x /opt/application/run.sh

# 启动命令
CMD ["/opt/application/run.sh"]
