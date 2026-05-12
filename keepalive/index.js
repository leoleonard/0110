#!/usr/bin/env node
import { spawn } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import { platform } from 'node:os';

const __dirname = dirname(fileURLToPath(import.meta.url));
const SCRIPT_PATH = join(__dirname, 'keepalive.ps1');

const MAX_RESTARTS = 5;
const RESTART_BACKOFF_MS = 2000;

function parseArgs(argv) {
    const opts = { interval: 60, quiet: false };
    for (let i = 0; i < argv.length; i++) {
        const a = argv[i];
        if (a === '--interval' || a === '-i') {
            const n = parseInt(argv[++i], 10);
            if (!Number.isFinite(n) || n < 1) {
                console.error(`Invalid --interval value: ${argv[i]}`);
                process.exit(2);
            }
            opts.interval = n;
        } else if (a === '--quiet' || a === '-q') {
            opts.quiet = true;
        } else if (a === '--help' || a === '-h') {
            printHelp();
            process.exit(0);
        } else {
            console.error(`Unknown argument: ${a}`);
            printHelp();
            process.exit(2);
        }
    }
    return opts;
}

function printHelp() {
    console.log(`laptop-teams-keepalive

Usage:
  node index.js [--interval <seconds>] [--quiet]

Options:
  -i, --interval <n>  Seconds between mouse jiggles (default 60)
  -q, --quiet         Suppress per-tick log lines
  -h, --help          Show this help

Press Ctrl+C to stop.`);
}

function startWorker(opts) {
    const args = [
        '-NoProfile',
        '-ExecutionPolicy', 'Bypass',
        '-File', SCRIPT_PATH,
        '-IntervalSeconds', String(opts.interval),
    ];
    if (opts.quiet) args.push('-Quiet');
    return spawn('powershell.exe', args, { stdio: 'inherit', windowsHide: true });
}

function main() {
    if (platform() !== 'win32') {
        console.error('This app is Windows-only (uses PowerShell + Win32 APIs).');
        process.exit(1);
    }

    const opts = parseArgs(process.argv.slice(2));

    console.log(`laptop-teams-keepalive starting`);
    console.log(`  pid:      ${process.pid}`);
    console.log(`  interval: ${opts.interval}s`);
    console.log(`  quiet:    ${opts.quiet}`);
    console.log(`Press Ctrl+C to stop.\n`);

    let child = null;
    let shuttingDown = false;
    let restarts = 0;

    const shutdown = () => {
        if (shuttingDown) return;
        shuttingDown = true;
        if (child && !child.killed) {
            child.kill();
        }
    };

    process.on('SIGINT', shutdown);
    process.on('SIGTERM', shutdown);

    const launch = () => {
        child = startWorker(opts);

        child.on('exit', (code, signal) => {
            if (shuttingDown) {
                process.exit(0);
            }
            console.error(`worker exited (code=${code}, signal=${signal})`);
            if (restarts >= MAX_RESTARTS) {
                console.error(`max restarts (${MAX_RESTARTS}) reached, giving up`);
                process.exit(1);
            }
            restarts++;
            console.error(`restarting in ${RESTART_BACKOFF_MS}ms (attempt ${restarts}/${MAX_RESTARTS})`);
            setTimeout(launch, RESTART_BACKOFF_MS);
        });

        child.on('error', (err) => {
            console.error(`failed to spawn powershell: ${err.message}`);
        });
    };

    launch();
}

main();
