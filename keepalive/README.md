# laptop-teams-keepalive

Keeps a **Windows** laptop awake and your **Microsoft Teams** status as "Available"
(instead of slipping to Away/Idle) by combining two tricks:

1. Calls the Win32 `SetThreadExecutionState` API with `ES_SYSTEM_REQUIRED |
   ES_DISPLAY_REQUIRED | ES_CONTINUOUS` to tell Windows not to sleep or blank
   the display.
2. Jiggles the mouse 1 pixel every N seconds so that Teams sees user input and
   keeps your presence as Available (Teams flips you to Away after ~5 min of no
   input, which sleep prevention alone does **not** stop).

No native node-gyp deps. Just Node.js + the built-in PowerShell that ships with
Windows.

## Requirements

- Windows 10 or 11
- Node.js >= 16 (`node --version`)
- PowerShell 5.1+ (built into Windows) or PowerShell 7

## Quick start

```powershell
cd keepalive
node index.js
```

You should see something like:

```
laptop-teams-keepalive starting
  pid:      12345
  interval: 60s
  quiet:    false
Press Ctrl+C to stop.

[14:01:02] sleep prevention armed (interval=60s)
[14:01:02] jiggled
[14:02:02] jiggled
```

Press **Ctrl+C** to stop. The PowerShell worker's `finally` block releases the
sleep-prevention flag, so power behavior returns to normal immediately.

## Options

```
node index.js [--interval <seconds>] [--quiet]

  -i, --interval <n>  Seconds between mouse jiggles (default 60)
  -q, --quiet         Suppress per-tick log lines
  -h, --help          Show help
```

Examples:

```powershell
# Jiggle every 30 seconds
node index.js --interval 30

# Silent mode
node index.js --quiet
```

## Run at login (Task Scheduler)

1. Open **Task Scheduler** -> **Create Task**.
2. **General** tab: name it `Keepalive`. Run only when user is logged on.
   Do **not** check "Run with highest privileges" - admin is not required.
3. **Triggers** -> New -> Begin the task: *At log on* -> your user.
4. **Actions** -> New ->
   - Program/script: `node`
   - Add arguments: `index.js --quiet`
   - Start in: full path to your `keepalive` folder, e.g.
     `C:\Users\you\code\keepalive`
5. **Conditions** tab: uncheck "Start the task only if the computer is on AC
   power" if you want it to run on battery too.
6. Save. Right-click the task -> **Run** to test it.

## Troubleshooting

- **"running scripts is disabled on this system"** - the Node supervisor passes
  `-ExecutionPolicy Bypass` to PowerShell, so this should not happen. If it
  does, run PowerShell as your user (not admin) and execute:
  `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.
- **Mouse jiggle interferes with what you're doing** - increase `--interval`.
  Teams' idle timeout is roughly 5 minutes, so anything <= 240 seconds is safe.
- **Verify sleep prevention is active** - in another terminal run
  `powercfg /requests`. You should see `powershell.exe` listed under
  `SYSTEM` and `DISPLAY`. After Ctrl+C, those should disappear.
- **Status still goes Away** - confirm Teams is the desktop client, not just
  the web app in a background tab (background tabs throttle input events).
