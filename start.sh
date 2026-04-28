#!/bin/bash

# AutoStream Quick Start Script
# This script sets up and starts the entire AutoStream platform

set -e

echo "🚀 AutoStream Real-Time Vehicle Data Platform"
echo "================================================"
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed. Please install Docker Desktop.${NC}"
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    if ! docker compose version &> /dev/null; then
        echo -e "${RED}❌ docker-compose is not available.${NC}"
        exit 1
    fi
    DC="docker compose"
else
    DC="docker-compose"
fi

# Create environment files if they don't exist
echo -e "${YELLOW}📝 Setting up environment files...${NC}"

for service in simulator processor api-service; do
    if [ ! -f "$service/.env" ]; then
        cp "$service/.env.example" "$service/.env"
        echo -e "${GREEN}✓ Created $service/.env${NC}"
    fi
done

# Start services
echo -e "${YELLOW}🐳 Starting Docker services...${NC}"
$DC up -d

# Wait for services to be ready
echo -e "${YELLOW}⏳ Waiting for services to start (30 seconds)...${NC}"
sleep 30

# Health checks
echo -e "${YELLOW}🏥 Performing health checks...${NC}"

# Check API
if curl -s http://localhost:8000/health > /dev/null; then
    echo -e "${GREEN}✓ API Service is healthy${NC}"
else
    echo -e "${RED}❌ API Service is not responding${NC}"
fi

# Check Prometheus
if curl -s http://localhost:9090/-/healthy > /dev/null; then
    echo -e "${GREEN}✓ Prometheus is healthy${NC}"
else
    echo -e "${RED}❌ Prometheus is not responding${NC}"
fi

# Check Grafana
if curl -s http://localhost:3000/api/health > /dev/null; then
    echo -e "${GREEN}✓ Grafana is healthy${NC}"
else
    echo -e "${RED}❌ Grafana is not responding${NC}"
fi

echo ""
echo -e "${GREEN}✅ AutoStream Platform is running!${NC}"
echo ""
echo "📊 Access services at:"
echo "  API Documentation:  ${GREEN}http://localhost:8000/docs${NC}"
echo "  Prometheus:         ${GREEN}http://localhost:9090${NC}"
echo "  Grafana:            ${GREEN}http://localhost:3000${NC} (admin/admin)"
echo ""
echo "🔑 Default API Credentials:"
echo "  Username: admin"
echo "  Password: admin123"
echo ""
echo "📝 Quick start commands:"
echo "  View logs:          $DC logs -f"
echo "  Stop services:      $DC down"
echo "  Restart services:   $DC restart"
echo ""
echo "📚 Documentation:"
echo "  API Docs:      docs/API.md"
echo "  Architecture:  docs/ARCHITECTURE.md"
echo "  Troubleshoot:  docs/TROUBLESHOOTING.md"
echo ""
echo "🧪 Run tests:"
echo "  pytest tests/ -v"
echo ""
echo "For more help, see README.md"
