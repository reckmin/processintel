# Setup Guide: SSH & GPG

This guide explains how to configure **SSH access** and **GPG commit signing**, which are **mandatory** for contributing to this project.
The setup is required **once per computer**.

---

## SSH Key Setup 


### Step 1: Generate an SSH Key

Generate a new SSH key using the modern `ed25519` algorithm and explicitly specify the file path:

```bash
ssh-keygen -t ed25519 -f ~/.ssh/<filename>
```

###  Step 2: Add the SSH Key to the SSH Agent

Start the SSH agent:
```bash
eval "$(ssh-agent -s)"
```

Add your SSH private key:
```bash
ssh-add ~/.ssh/<filename>
```
### Step 3: Add the SSH Key to Github

Copy your public SSH key:
```bash
cat ~/.ssh/<filename>.pub
```
- Open your Github account
- Go to Settings -> SSH and GPG Keys
- Paste the key and save

Never upload the private key.
Only the .pub file belongs in your account settings.

## GPG Key Setup

GPG is used to cryptographically sign commits and verify authorship.
All commits must be signed.

### Step 1: Generate a GPG Key
```bash
gpg --full-generate-key
```

Recommended options:

- Key type: RSA and RSA
- Key size: 4096
- Email: the same email you use for Git commits
- Expiration: your choice (or none)

### Step 2: Add the GPG Key to Github

List your keys and copy the key ID:
```bash
gpg --list-secret-keys --keyid-format=long
```

Export your public GPG key:
```bash
gpg --armor --export YOUR_KEY_ID
```

- Open Settings -> SSH and GPG Keys in Github
- Paste the exported key and save

### Step 3: Configure Git to Sign Commits

Enable commit signing globally:
```bash
git config --global commit.gpgsign true
git config --global user.signingkey YOUR_KEY_ID
```


### Step 4: Verify Commit Signing

Create a test commit and verify the signature:
```bash
git log --show-signature -1
```

You should see a valid GPG signature.


### Common Problems

#### Configure pinentry

GPG uses a helper program called pinentry to request your key's passphrase.
This usually works automatically, but some environments require explicit configuration.

You may need this step if signing fails with errors like:
```bash
gpg: signing failed: Inappropriate ioctl for device
```

Edit (or create):
`~/.gnupg/gpg-agent.conf`

Add the pinentry program to use to the config.

Example (macOS, Homebrew):
```
pinentry-program /opt/homebrew/bin/pinentry-mac
```
Example (Gnome):
```
pinentry-program /usr/bin/pinentry-gnome3
```

Restart the GPG agent:
```
gpgconf --kill gpg-agent
```

#### GPG Client Not found by git

If you see an error message like:
```
gpg: signing failed: No secret key
```
or Git cannot find the GPG client, you may need to explicitly configure which GPG program Git should use.

Set the path to your GPG executable with:
```bash
git config --global gpg.program [PATH_TO_GPG]
```

Example (Linux):
```bash
git config --global gpg.program "/usr/bin/gpg"
```

