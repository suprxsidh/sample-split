#!/bin/bash

echo "=================================="
echo "   FairShare - Start Options"
echo "=================================="
echo ""
echo "1) Local only (http://localhost:8080)"
echo "2) Local network (http://192.168.x.x:8080)"
echo "3) Public URL via Cloudflare Tunnel"
echo ""
read -p "Choose option (1/2/3): " choice

case $choice in
    1)
        echo "Starting on localhost:8080..."
        source venv/bin/activate
        python app.py
        ;;
    2)
        echo "Finding your local IP..."
        LOCAL_IP=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}')
        echo "Your local IP: $LOCAL_IP"
        echo "Friends on same WiFi can access: http://$LOCAL_IP:8080"
        echo ""
        echo "Starting server..."
        source venv/bin/activate
        python app.py
        ;;
    3)
        echo "Starting server and Cloudflare Tunnel..."
        source venv/bin/activate
        python app.py &
        sleep 3
        echo ""
        echo "Starting tunnel..."
        cloudflared tunnel --url http://localhost:8080 2>&1 | while read line; do
            if echo "$line" | grep -q "Visit it at"; then
                echo "$line"
            fi
        done
        ;;
    *)
        echo "Invalid option"
        ;;
esac
