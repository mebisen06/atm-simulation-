import express from 'express';
import { createServer as createViteServer } from 'vite';
import { spawn } from 'child_process';
import path from 'path';
import fs from 'fs';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

async function startServer() {
  const app = express();
  const PORT = Number(process.env.PORT) || 3000;
  const isProd = process.env.NODE_ENV === 'production';

  app.use(express.json());

  // API endpoint: Health & Engine Environment
  app.get('/api/status', (req, res) => {
    const pythonCheck = spawn('python3', ['-c', 'import simpy, numpy, pandas, scipy; print(simpy.__version__)']);
    let simpyVer = '';
    pythonCheck.stdout.on('data', (d) => { simpyVer += d.toString(); });
    pythonCheck.on('close', (code) => {
      res.json({
        status: 'online',
        engine: 'SimPy Discrete Event Engine',
        pythonReady: code === 0,
        simpyVersion: simpyVer.trim() || '4.1.2',
        milestone: 'Milestone 1 — Core Architecture & SimPy Engine',
        project: 'ATMFlow Intelligence',
        team: [
          { name: 'Meet Bisen', roll: 'BTCD25O1081' },
          { name: 'Moully Acharya', roll: 'BTCD25O1084' },
          { name: 'Nishita Narwal', roll: 'BTCD25O1088' },
        ],
        course: 'Solving Problems Using Modelling and Simulation (NEC00091)'
      });
    });
  });

  // API endpoint: Execute Simulation Engine
  app.post('/api/run-simulation', (req, res) => {
    const {
      atms = 3,
      duration = 7200,
      rate = 1.5,
      seed = 42,
      policy = 'pooled_fifo',
      arrival = 'homogeneous',
      patience = null
    } = req.body;

    const args = [
      path.resolve(__dirname, 'ATMFlow_Intelligence/run_simulation.py'),
      '--atms', String(atms),
      '--duration', String(duration),
      '--rate', String(rate),
      '--seed', String(seed),
      '--policy', String(policy),
      '--arrival', String(arrival),
    ];

    if (patience !== null && patience !== undefined && Number(patience) > 0) {
      args.push('--patience', String(patience));
    }

    const env = { ...process.env, PYTHONPATH: path.resolve(__dirname, 'ATMFlow_Intelligence') };
    const py = spawn('python3', args, { env });

    let stdout = '';
    let stderr = '';

    py.stdout.on('data', (d) => { stdout += d.toString(); });
    py.stderr.on('data', (d) => { stderr += d.toString(); });

    py.on('close', (code) => {
      if (code !== 0) {
        return res.status(500).json({ error: 'Simulation failed', stderr, stdout });
      }

      // Read output JSON
      let jsonPath = path.resolve(__dirname, 'ATMFlow_Intelligence/data/simulation_results.json');
      if (!fs.existsSync(jsonPath)) {
        jsonPath = path.resolve(__dirname, 'data/simulation_results.json');
      }

      if (fs.existsSync(jsonPath)) {
        try {
          const raw = fs.readFileSync(jsonPath, 'utf8');
          const data = JSON.parse(raw);
          return res.json({ success: true, consoleOutput: stdout, ...data });
        } catch (e) {
          return res.status(500).json({ error: 'Failed to parse simulation output', details: String(e), stdout, stderr });
        }
      }

      return res.status(500).json({ error: 'Simulation output file not found', stdout, stderr });
    });
  });

  // API endpoint: Run Pytest Suite
  app.post('/api/run-pytest', (req, res) => {
    const env = { ...process.env, PYTHONPATH: path.resolve(__dirname, 'ATMFlow_Intelligence') };
    const py = spawn('python3', ['-m', 'pytest', path.resolve(__dirname, 'ATMFlow_Intelligence/tests/test_simulation.py')], { env });

    let stdout = '';
    let stderr = '';

    py.stdout.on('data', (d) => { stdout += d.toString(); });
    py.stderr.on('data', (d) => { stderr += d.toString(); });

    py.on('close', (code) => {
      res.json({
        success: code === 0,
        exitCode: code,
        stdout,
        stderr,
      });
    });
  });

  // API endpoint: Run Milestone 1 Unittest Suite
  app.post('/api/run-tests', (req, res) => {
    const testPath = path.resolve(__dirname, 'ATMFlow_Intelligence/tests/test_milestone1.py');
    const env = { ...process.env, PYTHONPATH: path.resolve(__dirname, 'ATMFlow_Intelligence') };
    const py = spawn('python3', [testPath], { env });

    let stdout = '';
    let stderr = '';

    py.stdout.on('data', (d) => { stdout += d.toString(); });
    py.stderr.on('data', (d) => { stderr += d.toString(); });

    py.on('close', (code) => {
      res.json({
        success: code === 0,
        exitCode: code,
        stdout,
        stderr,
      });
    });
  });

  // API endpoint: Run Experiment Suite
  app.post('/api/run-experiment', (req, res) => {
    const { expId = 1 } = req.body;
    const codeStr = `
from experiments.experiment_runner import ExperimentRunner
import json
if ${expId} == 1:
    res = ExperimentRunner.run_experiment_1_atm_count()
elif ${expId} == 2:
    res = ExperimentRunner.run_experiment_2_arrival_rate()
else:
    res = ExperimentRunner.run_experiment_3_service_time()
print(json.dumps(res))
`;
    const env = { ...process.env, PYTHONPATH: path.resolve(__dirname, 'ATMFlow_Intelligence') };
    const py = spawn('python3', ['-c', codeStr], { env });

    let stdout = '';
    let stderr = '';

    py.stdout.on('data', (d) => { stdout += d.toString(); });
    py.stderr.on('data', (d) => { stderr += d.toString(); });

    py.on('close', (code) => {
      if (code !== 0) {
        return res.status(500).json({ success: false, stderr });
      }
      try {
        const data = JSON.parse(stdout);
        res.json({ success: true, data });
      } catch (e) {
        res.json({ success: false, raw: stdout, parseError: String(e) });
      }
    });
  });

  if (!isProd) {
    const vite = await createViteServer({
      server: { middlewareMode: true },
      appType: 'spa',
    });
    app.use(vite.middlewares);
  } else {
    app.use(express.static(path.resolve(__dirname, 'dist')));
    app.get('*', (req, res) => {
      res.sendFile(path.resolve(__dirname, 'dist', 'index.html'));
    });
  }

  app.listen(PORT, '0.0.0.0', () => {
    console.log(`[ATMFlow] Server running on http://0.0.0.0:${PORT}`);
  });
}

startServer();
