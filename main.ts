import { app, BrowserWindow } from 'electron';
import { spawn } from 'child_process';
import type { ChildProcessWithoutNullStreams } from 'node:child_process';
import path from 'node:path';
import http from 'http';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

let djangoServerProcess: ChildProcessWithoutNullStreams | null = null;
let djangoBrowserProcess: ChildProcessWithoutNullStreams | null = null;

function startDjangoCommand(args: string[], label: string): ChildProcessWithoutNullStreams {
  let backendDir;
  if (!app.isPackaged) {
    backendDir = path.join(__dirname, 'backend');
  } else {
    backendDir = path.join(process.resourcesPath, "app.asar.unpacked", 'backend');
  }

  const isWin = process.platform === 'win32';
  
  const pythonPath = isWin
    ? path.join(backendDir, '.venv', 'Scripts', 'python.exe')
    : path.join(backendDir, '.venv', 'bin', 'python');

  const processInstance = spawn(pythonPath, args, {
    cwd: backendDir,
    shell: isWin, 
    detached: true
  });

  processInstance.stdout.on('data', (data) => {
    console.log(`[${label}]: ${data.toString()}`);
  });

  processInstance.stderr.on('data', (data) => {
    console.warn(`[${label} STDERR]: ${data.toString()}`);
  });

  processInstance.on('error', (err) => {
    console.error(`Failed to start ${label}:`, err);
  });

  return processInstance;
}

function waitForDjangoPort(url: string, timeout = 10000): Promise<void> {
  const start = Date.now();

  return new Promise((resolve, reject) => {
    const check = () => {
      http.get(url, () => resolve()).on('error', () => {
        if (Date.now() - start > timeout) {
          reject(new Error('Django server did not start in time'));
        } else {
          setTimeout(check, 200);
        }
      });
    };
    check();
  });
}

function createWindow() {
  const win = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  if (!app.isPackaged) {
    win.loadURL('http://localhost:5173');
    win.webContents.openDevTools({ mode: 'detach' });
  } else {
    const indexPath = path.join(app.getAppPath(), 'dist', 'index.html');
    win.loadFile(indexPath);
  }
}

app.whenReady().then(async () => {
  try {
    console.log('Starting Django Server...');
    
    djangoServerProcess = startDjangoCommand(['manage.py', 'runserver', '--noreload'], 'Django-Server');
    djangoBrowserProcess = startDjangoCommand(['manage.py', 'run_browser'], 'Django-Browser');
    await waitForDjangoPort("http://127.0.0.1:8000")

    createWindow();
  } catch (err) {
    console.error('Startup error:', err);
  }
});

function killProcess(proc: ChildProcessWithoutNullStreams | null) {
  if (!proc) return;

  try {
    process.kill(-proc.pid);
  } catch (e) {
    try {
      proc.kill();
    } catch {}
  }
}

app.on('window-all-closed', () => {
  killProcess(djangoServerProcess);
  killProcess(djangoBrowserProcess);
  app.quit();
});