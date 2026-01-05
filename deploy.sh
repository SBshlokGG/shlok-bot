#!/bin/bash

echo "🚀 Railway Deployment Script"
echo "=============================="
echo ""

# Check if git is initialized
if [ ! -d .git ]; then
    echo "📝 Initializing git repository..."
    git init
    git add .
    git commit -m "Initial bot deployment"
    echo "✅ Git repository created"
else
    echo "✅ Git repository already exists"
fi

echo ""
echo "📋 Your files are ready for Railway deployment!"
echo ""
echo "Next steps:"
echo "1. Go to https://railway.app"
echo "2. Sign up (free)"
echo "3. Create new project → Empty Project"
echo "4. You'll get a Railway git URL"
echo "5. Run this command with YOUR Railway URL:"
echo ""
echo "   git remote add railway <YOUR_RAILWAY_GIT_URL>"
echo "   git push railway main"
echo ""
echo "6. In Railway dashboard → Variables → Add BOT_TOKEN"
echo "7. Wait for deployment (2-3 min)"
echo ""
echo "That's it! Your bot will be live 24/7 ✨"
