# Windows + MT5 Installation Guide (Parallels VM)

## Part 1: Install Windows on Parallels

### Step 1.1: Open Parallels
1. Open **Parallels Desktop** from Applications
2. Click **"Install Windows"** or **"+"** button

### Step 1.2: Choose Windows
1. Select **"Install Windows from image file"** (if you have ISO)
2. Or select **"Download Windows"** to get Windows 10/11

### Step 1.3: Configure VM
| Setting | Recommended Value |
|---------|-------------------|
| RAM | 4 GB (4096 MB) minimum |
| CPU | 2 cores |
| Disk | 60 GB minimum |
| Graphics | 2 GB |

### Step 1.4: Complete Installation
1. Wait for Windows to install (15-30 minutes)
2. Create Windows account (local account is fine)
3. Install Parallels Tools when prompted

---

## Part 2: Install MetaTrader 5 (MT5)

### Step 2.1: Download MT5
1. Open **Microsoft Edge** in Windows VM
2. Go to: https://www.metatrader5.com/en/download
3. Click **"Download for Windows"**

### Step 2.2: Install MT5
1. Find `mt5setup.exe` in Downloads
2. Double-click to run
3. Click **Next** → **Next** → **Install**
4. Wait for installation to complete
5. Click **Finish**

### Step 2.3: Launch MT5
1. Find **MetaTrader 5** in Windows Start Menu
2. Click to open

---

## Part 3: Create MT5 Demo Account

### Step 3.1: Start MT5
1. MT5 will show "MetaTrader 5 - Trading Platform"
2. Click **"Next"** or **"Cancel"** to skip initial wizard

### Step 3.2: Open Demo Account
1. Go to **File** → **Open an Account**
2. Or click **"Create a Demo Account"** button
3. Search for broker: **MetaQuotes-Demo** (or any broker)

### Step 3.3: Fill Account Details
| Field | Value |
|-------|-------|
| Server | MetaQuotes-Demo |
| Deposits | 10,000 (or your choice) |
| Currency | USD |
| Leverage | 1:100 (or your choice) |

4. Fill your details:
   - First Name: Your name
   - Last Name: Your surname
   - Email: your@email.com
   - Phone: Your phone number

5. Check **"I agree..."** terms
6. Click **"Next"**

### Step 3.4: Account Created
1. Note your **Login ID** and **Password**
2. Click **"Finish"**
3. MT5 will connect and show your demo account

---

## Part 4: Install MT5 EA (Socket Client)

### Step 4.1: Get the EA File
**On Mac**, the file is at:
```
/Users/link/Desktop/MT5SocketClient.mq5
```

**Transfer to Windows:**
1. In Parallels, drag the file from Mac Desktop to Windows Desktop
2. Or use shared folder

### Step 4.2: Copy to MT5 Folder
1. Press `Win + R`
2. Type: `%APPDATA%\MetaQuotes\Terminal`
3. Press Enter
4. Open the folder with random letters (e.g., `C2A3B4...`)
5. Open `MQL5\Experts\`
6. Copy `MT5SocketClient.mq5` here

### Step 4.3: Compile in MetaEditor
1. In MT5, press `F4` (opens MetaEditor)
2. In Navigator (left side), expand **Expert Advisors**
3. Right-click **MT5SocketClient**
4. Click **Compile**
5. Should show: `"MT5SocketClient.mq5" - 0 error(s), 0 warning(s)`

---

## Part 5: Configure MT5 for Connection

### Step 5.1: Enable WebRequest
1. In MT5, go to **Tools** → **Options**
2. Or press `Ctrl + O`
3. Click **Expert Advisors** tab
4. ☑️ Check **"Allow WebRequest for listed URL"**
5. Click **Add**
6. Enter: `http://192.168.0.160:1111`
7. Click **OK**

### Step 5.2: Get Your Mac's IP
**On Mac**, open Terminal and run:
```bash
ipconfig getifaddr en0
```
Note the IP address (e.g., `192.168.0.160`)

---

## Part 6: Attach EA to Chart

### Step 6.1: Open Chart
1. In MT5, go to **File** → **New Chart**
2. Select a symbol (e.g., **EURUSD**)

### Step 6.2: Attach EA
1. Press `Ctrl + N` to open Navigator
2. Expand **Expert Advisors**
3. Drag **MT5SocketClient** to the chart

### Step 6.3: Configure EA Inputs
In the EA properties window:

| Input | Value |
|-------|-------|
| ServerAddress | `192.168.0.160` (your Mac IP) |
| ServerPort | `1111` |

Under **Common** tab:
- ☑️ Allow live trading
- ☑️ Allow DLL imports

Click **OK**

### Step 6.4: Verify Connection
1. Look at EA face (top-right of chart)
   - 🟢 Green = Connected
   - 🔴 Red = Disconnected

2. Check **Experts** tab (bottom of MT5)
   - Should see: `Connected to Python server at 192.168.0.160:1111`

---

## Part 7: Test Connection (Back on Mac)

### Step 7.1: Check Docker Logs
```bash
docker logs -f mt5-bridge
```

Should see:
```
MT5 EA connected from ('192.168.x.x', xxxxx)
```

### Step 7.2: Verify MT5 Bridge
If EA is connected, you're ready!

---

## Quick Checklist

- [ ] Windows installed on Parallels
- [ ] MT5 downloaded and installed
- [ ] Demo account created (Login: 5048779453)
- [ ] MT5SocketClient.mq5 copied to MQL5\Experts\
- [ ] EA compiled in MetaEditor
- [ ] WebRequest enabled with Mac IP
- [ ] EA attached to chart with correct settings
- [ ] Docker bridge running on Mac
- [ ] Connection verified

---

## Commands Reference

**Start MT5 Bridge (Mac Terminal):**
```bash
cd ~/TestLab/Other/Market/mt5_third_parties
docker compose up -d
docker logs -f mt5-bridge
```

**Stop MT5 Bridge:**
```bash
docker compose -f ~/TestLab/Other/Market/mt5_third_parties/docker-compose.yml down
```

**Restart MT5 Bridge:**
```bash
docker compose -f ~/TestLab/Other/Market/mt5_third_parties/docker-compose.yml restart
```
