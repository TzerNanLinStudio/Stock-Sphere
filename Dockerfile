FROM ubuntu:22.04

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Asia/Taipei
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /workspace

# Update package lists and install required software
RUN apt-get update && apt-get install -y \
    mysql-server \
    mysql-client \
    python3 \
    python3-pip \
    python3-venv \
    python3-full \
    sudo \
    curl \
    wget \
    git \
    vim \
    nano \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements.txt file to the /tmp directory in the container
COPY requirements.txt /tmp/requirements.txt

# Upgrade pip and install Python dependencies from requirements.txt
RUN pip3 install --upgrade pip && \
    pip3 install -r /tmp/requirements.txt

# Configure MySQL with no password for root
RUN service mysql start && \
    sleep 5 && \
    mysql -e "ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY ''; FLUSH PRIVILEGES;" && \
    service mysql stop

# Expose ports
EXPOSE 3306 8000

# Create startup script
RUN echo '#!/bin/bash\n\
# Set color output\n\
RED="\\033[0;31m"\n\
GREEN="\\033[0;32m"\n\
YELLOW="\\033[1;33m"\n\
BLUE="\\033[0;34m"\n\
NC="\\033[0m"\n\
\n\
# Start MySQL service\n\
echo -e "${YELLOW}Starting MySQL service...${NC}"\n\
service mysql start\n\
sleep 3\n\
\n\
# Check MySQL status\n\
if service mysql status >/dev/null 2>&1; then\n\
    echo -e "${GREEN}✓ MySQL service started${NC}"\n\
    MYSQL_VERSION=$(mysql --version | awk "{print \\$3}" | cut -d"," -f1)\n\
    echo -e "${GREEN}✓ MySQL version: ${MYSQL_VERSION}${NC}"\n\
else\n\
    echo -e "${RED}✗ MySQL service failed to start${NC}"\n\
fi\n\
\n\
# Check Python and packages\n\
PYTHON_VERSION=$(python3 --version)\n\
echo -e "${GREEN}✓ ${PYTHON_VERSION}${NC}"\n\
\n\
# Check installed packages\n\
echo -e "${YELLOW}Checking installed Python packages...${NC}"\n\
\n\
if python3 -c "import mysql.connector" >/dev/null 2>&1; then\n\
    echo -e "${GREEN}✓ mysql-connector-python${NC}"\n\
else\n\
    echo -e "${RED}✗ mysql-connector-python${NC}"\n\
fi\n\
\n\
exec bash\n\
' > /start.sh && chmod +x /start.sh

# Create 'helpme' command
RUN echo '#!/bin/bash\n\
echo ""\n\
echo "Common commands for this development environment:" \n\
echo "----------------------------------------"\n\
echo "python3 app/main.py      # Run main application"\n\
echo "python3 test/run_tests.py # Execute test scripts"\n\
echo "mysql -u root           # Login to MySQL (no password)"\n\
echo "service mysql status    # Check MySQL service status"\n\
echo "black .                  # Format all Python files"\n\
echo "black --check .          # Check formatting without changes"\n\
echo "pip3 list               # View installed Python packages"\n\
echo "----------------------------------------"\n\
echo ""\n\
' > /usr/local/bin/helpme && chmod +x /usr/local/bin/helpme

# Set startup command
CMD ["/start.sh"]
