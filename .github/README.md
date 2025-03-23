# GitHub Actions Deployment Guide

This project can be automatically deployed to GitHub Pages using GitHub Actions. The workflow will:
1. Connect to a MongoDB database via SSH tunnel
2. Collect ArXiv papers and enrich them with Twitter mentions
3. Generate HTML visualizations
4. Deploy the visualizations to GitHub Pages

## Required GitHub Secrets

To set up automatic deployment, you need to add the following secrets to your GitHub repository:

### SSH Connection
- `SSH_PRIVATE_KEY`: The private SSH key for connecting to the MongoDB server (must not have a passphrase)
- `SSH_KNOWN_HOSTS`: The SSH known hosts entry for the MongoDB server (run `ssh-keyscan hostname` to get this)
- `SSH_HOST`: The hostname or IP address of the MongoDB server
- `SSH_PORT`: The SSH port of the MongoDB server (usually 22)
- `SSH_USER`: The SSH username for authentication

### MongoDB Connection (Optional, defaults provided)
- `MONGO_HOST`: The hostname that MongoDB listens on inside the server (defaults to "localhost")
- `MONGO_PORT`: The port that MongoDB listens on (defaults to "27017")

### Environment Variables
- `ENV_FILE`: The entire contents of your .env file which should include:
  ```
  MONGODB_USER=your_mongodb_username
  MONGODB_PASSWORD=your_mongodb_password
  TWITTER_AUTH_TOKEN=your_twitter_auth_token
  TWITTER_CT0_TOKEN=your_twitter_ct0_token
  ```

## Setting Up GitHub Pages

1. Go to your repository's Settings > Pages
2. Under "Source," select "GitHub Actions"
3. The workflow will automatically deploy to the gh-pages branch

## SSH Key and Known Hosts Generation

If you need to generate a new SSH key for GitHub Actions:

```bash
# Generate a key without a passphrase
ssh-keygen -t rsa -b 4096 -C "github-actions" -f github-actions -N ""

# Display the private key (add this as SSH_PRIVATE_KEY secret)
cat github-actions

# Display the public key (add this to the MongoDB server's authorized_keys)
cat github-actions.pub
```

### Generating SSH Known Hosts

To securely connect to your MongoDB server, you'll need to capture its SSH host keys:

```bash
# Basic usage (replace with your MongoDB server hostname or IP)
ssh-keyscan your-mongodb-server-hostname

# If your SSH server uses a non-standard port
ssh-keyscan -p 22 your-mongodb-server-hostname

# Hash the hostname for added security (recommended)
ssh-keyscan -H your-mongodb-server-hostname

# Example for a server at mongo.example.com
ssh-keyscan -H mongo.example.com
```

The output will look like:
```
# mongo.example.com:22 SSH-2.0-OpenSSH_8.9p1 Ubuntu-3ubuntu0.1
|1|SoMeHaSh=|AnotherHashPart= ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQC6Dks9...
```

Copy the entire output and add it as the `SSH_KNOWN_HOSTS` secret in your GitHub repository.

## Customizing the Deployment

- The workflow runs on every push to `main` or `master` branch
- It also runs automatically every 12 hours
- You can manually trigger a run from the Actions tab
- The collection is limited to 5 papers per run to avoid rate limits