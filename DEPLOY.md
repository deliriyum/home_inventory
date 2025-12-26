# Deploy to Render - Step by Step Guide

This guide will help you deploy your Home Inventory Sales App to Render so you can access it from your mobile device anywhere!

## Prerequisites

1. A GitHub account
2. Your Anthropic API key (from https://console.anthropic.com/)
3. This repository pushed to GitHub

## Step-by-Step Deployment

### 1. Push Code to GitHub (if not already done)

First, make sure your code is on GitHub:

```bash
# Check current remote
git remote -v

# If you need to change the remote to your actual GitHub repo:
git remote set-url origin https://github.com/YOUR-USERNAME/home_inventory.git

# Push the code
git push -u origin claude/home-inventory-sales-app-Lg6yr
```

### 2. Create Render Account

1. Go to https://render.com
2. Click "Get Started for Free"
3. Sign up with your GitHub account (easiest option)
4. Authorize Render to access your GitHub repositories

### 3. Create New Web Service

1. From your Render dashboard, click **"New +"** button
2. Select **"Web Service"**
3. Connect your GitHub repository:
   - Click "Connect account" if needed
   - Find and select your `home_inventory` repository
   - Click "Connect"

### 4. Configure the Service

Render should auto-detect the `render.yaml` configuration, but if it asks for details:

- **Name**: `home-inventory-app` (or whatever you prefer)
- **Region**: Choose closest to you
- **Branch**: `claude/home-inventory-sales-app-Lg6yr` (or `main` if you merged)
- **Runtime**: Python 3
- **Build Command**: `./build.sh`
- **Start Command**: `gunicorn app:app`
- **Instance Type**: Free

### 5. Add Environment Variables

This is the MOST IMPORTANT step:

1. Scroll down to **"Environment Variables"**
2. Click **"Add Environment Variable"**
3. Add the following:

   ```
   Key: ANTHROPIC_API_KEY
   Value: your_actual_api_key_here
   ```

4. Render will auto-generate `FLASK_SECRET_KEY` for you

### 6. Deploy!

1. Click **"Create Web Service"**
2. Render will start building your app (takes 2-5 minutes)
3. Watch the build logs for any errors
4. Once you see "Your service is live 🎉", you're done!

### 7. Access Your App

You'll get a URL like: `https://home-inventory-app.onrender.com`

- Bookmark this URL
- Add it to your phone's home screen for easy access
- Share it only with people you trust (no authentication yet!)

## Using the App from Mobile

1. Open the URL in your mobile browser
2. Click "Add New Item"
3. Use your phone's camera to upload photos
4. Let AI analyze and identify items
5. Track your inventory on the go!

## Important Notes

### Free Tier Limitations

- **Cold Starts**: App spins down after 15 min of inactivity
  - First load after inactivity takes ~30-60 seconds
  - After that, it's fast!

- **Ephemeral Storage**:
  - Your database and images reset when you redeploy
  - For persistent storage, upgrade to paid tier ($7/month with persistent disk)
  - OR switch to Railway after testing

### Data Persistence Workaround

If you need to keep your data on the free tier:

1. Regularly export your database:
   - Download `home_inventory.db` from Render's Shell
   - Keep backups locally

2. Or switch to Railway for better free-tier persistence

## Troubleshooting

### Build Failed

Check the build logs for errors:
- Make sure `ANTHROPIC_API_KEY` is set correctly
- Verify all files are committed and pushed to GitHub

### App Won't Start

- Check the logs in Render dashboard
- Make sure environment variables are set
- Try manual deploy from Render dashboard

### Images Not Uploading

- Free tier has limited storage
- Images might be lost on redeploy
- Consider upgrading or using external image storage (Cloudinary)

### AI Analysis Not Working

- Verify `ANTHROPIC_API_KEY` is correct
- Check you have credits in your Anthropic account
- Look at logs for specific error messages

## Updating Your App

When you make changes to your code:

```bash
git add .
git commit -m "Description of changes"
git push
```

Render will automatically rebuild and redeploy!

## Next Steps

Once you're comfortable with Render:

1. **Add Authentication** - Protect your app with a password
2. **Switch to Railway** - Better persistence on free tier
3. **Add Custom Domain** - Use your own domain name
4. **Set up Backups** - Regular database backups
5. **Add Email Notifications** - Get alerts when items sell

## Cost Estimate

**Render Free Tier:**
- Web Service: FREE (with limitations)
- Persistent Disk: $1/month (if you want data persistence)

**Anthropic API:**
- ~$0.01-0.05 per item analyzed
- If you analyze 100 items = ~$1-5 total

**Total monthly cost for light use: $0-2**

---

Need help? Check the logs in your Render dashboard first!
