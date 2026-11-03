import React, { useState, useEffect } from 'react';
import { Play, Users, CheckCircle, Clock, Server, Activity, AlertTriangle, Loader2, TrendingUp, Zap, BarChart2 } from 'lucide-react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from 'recharts';

interface ATMInfo {
  atm_id: string;
  status: string;
  total_customers_served: number;
  total_busy_time: number;
  utilization: number;
  cash_balance: number;
}

interface SimulationSummary {
  total_arrived: number;
  completed: number;
  abandoned: number;
  avg_waiting_time_sec: number;
  time_weighted_queue_length: number;
  average_atm_utilization: number;
  throughput_per_hour: number;
}

interface SimulationData {
  summary: SimulationSummary;
  atm_metrics: ATMInfo[];
  queue_history?: Array<[number, number]>;
}

export default function App() {
  const [numAtms, setNumAtms] = useState<number>(3);
  const [durationMinutes, setDurationMinutes] = useState<number>(120);
  const [arrivalRate, setArrivalRate] = useState<number>(1.5);
  const [randomSeed, setRandomSeed] = useState<number>(42);

  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<SimulationData | null>(null);

  // Execute simulation on mount with default settings
  useEffect(() => {
    executeSimulation(3, 120, 1.5, 42);
  }, []);

  const executeSimulation = async (atms: number, durationMins: number, rate: number, seed: number) => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch('/api/run-simulation', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          atms: Number(atms),
          duration: Number(durationMins) * 60,
          rate: Number(rate),
          seed: Number(seed),
          policy: 'pooled_fifo',
          arrival: 'homogeneous',
        }),
      });

      const data = await res.json();

      if (!res.ok || data.error) {
        throw new Error(data.error || data.stderr || 'Simulation execution failed');
      }

      if (data.summary && data.atm_metrics) {
        setResults({
          summary: data.summary,
          atm_metrics: data.atm_metrics,
          queue_history: data.queue_history,
        });
      } else {
        throw new Error('Simulation response did not contain expected summary dataset.');
      }
    } catch (err: any) {
      console.error('Simulation execution error:', err);
      setError(err.message || 'Failed to connect to simulation backend.');
    } finally {
      setLoading(false);
    }
  };

  const handleRunClick = () => {
    executeSimulation(numAtms, durationMinutes, arrivalRate, randomSeed);
  };

  // Recharts Queue History dataset mapping
  const queueChartData = results?.queue_history
    ? results.queue_history.map(([timeSec, qLen]) => ({
        timeMin: Number((timeSec / 60.0).toFixed(1)),
        queueLength: qLen,
      }))
    : [];

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 font-sans antialiased">
      {/* Clean Premium Header */}
      <header className="bg-white border-b border-slate-200/80 sticky top-0 z-20 shadow-2xs">
        <div className="max-w-6xl mx-auto px-4 py-4 flex flex-wrap items-center justify-between gap-4">
          <div>
            <h1 className="text-xl font-bold text-slate-900 tracking-tight flex items-center gap-2.5">
              <span className="w-3.5 h-3.5 rounded-full bg-blue-600 inline-block shadow-xs" />
              ATMFlow Intelligence
            </h1>
            <p className="text-xs text-slate-500 font-medium mt-0.5">
              ATM Transaction & Queue Simulation
            </p>
          </div>

          {/* Simple Status Indicator */}
          <div className="flex items-center gap-2">
            <span className="px-3 py-1.5 rounded-full bg-emerald-50 border border-emerald-200/80 text-emerald-700 text-xs font-semibold flex items-center gap-2 shadow-2xs">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              SimPy Engine Ready
            </span>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-6xl mx-auto px-4 py-8 space-y-8">

        {/* Error Alert */}
        {error && (
          <div className="p-4 rounded-xl bg-red-50 border border-red-200 text-red-800 flex items-start gap-3 shadow-xs">
            <AlertTriangle className="w-5 h-5 text-red-600 shrink-0 mt-0.5" />
            <div>
              <div className="font-bold text-sm">Simulation Error</div>
              <p className="text-xs text-red-700 mt-0.5">{error}</p>
            </div>
          </div>
        )}

        {/* 1. SIMULATION CONFIGURATION */}
        <section className="bg-white border border-slate-200/80 rounded-2xl p-6 shadow-xs">
          <div className="border-b border-slate-100 pb-4 mb-6">
            <h2 className="text-base font-bold text-slate-900 tracking-tight flex items-center gap-2">
              <span className="w-6 h-6 rounded-md bg-blue-50 text-blue-600 font-bold text-xs flex items-center justify-center">1</span>
              Simulation Configuration
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Set customer arrival parameters and click <strong className="text-slate-700">Run Simulation</strong>.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5 mb-6">
            {/* Setting 1: Number of ATMs */}
            <div className="space-y-2 bg-slate-50/70 p-4 rounded-xl border border-slate-100">
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider">
                Number of ATMs
              </label>
              <div className="flex items-center gap-3 pt-1">
                <input
                  type="range"
                  min="1"
                  max="10"
                  value={numAtms}
                  onChange={(e) => setNumAtms(Number(e.target.value))}
                  className="w-full accent-blue-600 cursor-pointer"
                />
                <span className="text-base font-extrabold font-mono text-blue-600 bg-white px-3 py-1 rounded-lg border border-slate-200 min-w-[45px] text-center shadow-2xs">
                  {numAtms}
                </span>
              </div>
            </div>

            {/* Setting 2: Simulation Duration */}
            <div className="space-y-2 bg-slate-50/70 p-4 rounded-xl border border-slate-100">
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider">
                Duration (Minutes)
              </label>
              <input
                type="number"
                min="10"
                max="480"
                step="10"
                value={durationMinutes}
                onChange={(e) => setDurationMinutes(Number(e.target.value))}
                className="w-full bg-white border border-slate-300 rounded-lg px-3 py-1.5 text-sm font-semibold text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            {/* Setting 3: Arrival Rate */}
            <div className="space-y-2 bg-slate-50/70 p-4 rounded-xl border border-slate-100">
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider">
                Arrival Rate (cust/min)
              </label>
              <input
                type="number"
                min="0.1"
                max="10.0"
                step="0.1"
                value={arrivalRate}
                onChange={(e) => setArrivalRate(Number(e.target.value))}
                className="w-full bg-white border border-slate-300 rounded-lg px-3 py-1.5 text-sm font-semibold text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            {/* Setting 4: Random Seed */}
            <div className="space-y-2 bg-slate-50/70 p-4 rounded-xl border border-slate-100">
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider">
                Random Seed
              </label>
              <input
                type="number"
                value={randomSeed}
                onChange={(e) => setRandomSeed(Number(e.target.value))}
                className="w-full bg-white border border-slate-300 rounded-lg px-3 py-1.5 text-sm font-semibold text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>

          {/* Prominent Run Button */}
          <button
            onClick={handleRunClick}
            disabled={loading}
            className="w-full py-3.5 px-6 bg-blue-600 hover:bg-blue-700 text-white font-bold text-sm rounded-xl shadow-xs transition flex items-center justify-center gap-2 disabled:opacity-50 cursor-pointer"
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Executing Simulation Engine...
              </>
            ) : (
              <>
                <Play className="w-4 h-4 fill-current" />
                Run Simulation
              </>
            )}
          </button>
        </section>


        {/* 2. SIMULATION RESULTS */}
        <section className="bg-white border border-slate-200/80 rounded-2xl p-6 shadow-xs space-y-6">
          <div className="border-b border-slate-100 pb-4 flex justify-between items-center">
            <div>
              <h2 className="text-base font-bold text-slate-900 tracking-tight flex items-center gap-2">
                <span className="w-6 h-6 rounded-md bg-blue-50 text-blue-600 font-bold text-xs flex items-center justify-center">2</span>
                Simulation Results
              </h2>
              <p className="text-xs text-slate-500 mt-0.5">
                Key performance metrics calculated directly from the SimPy engine.
              </p>
            </div>
            {loading && (
              <span className="text-xs font-semibold text-blue-600 bg-blue-50 px-3 py-1 rounded-full border border-blue-200 flex items-center gap-1.5 animate-pulse">
                <Loader2 className="w-3.5 h-3.5 animate-spin" /> Simulating...
              </span>
            )}
          </div>

          {/* 6 Clean KPI Cards */}
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
            {/* KPI 1: Total Arrived */}
            <div className="p-4 rounded-xl bg-slate-50/80 border border-slate-200/60 space-y-1">
              <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider flex items-center gap-1">
                <Users className="w-3.5 h-3.5 text-blue-600" /> Total Arrived
              </span>
              <div className="text-2xl font-black text-slate-900 tracking-tight pt-1">
                {loading ? <Loader2 className="w-5 h-5 animate-spin text-slate-400" /> : (results ? results.summary.total_arrived : '—')}
              </div>
            </div>

            {/* KPI 2: Completed */}
            <div className="p-4 rounded-xl bg-emerald-50/50 border border-emerald-200/60 space-y-1">
              <span className="text-[11px] font-bold text-emerald-800 uppercase tracking-wider flex items-center gap-1">
                <CheckCircle className="w-3.5 h-3.5 text-emerald-600" /> Completed
              </span>
              <div className="text-2xl font-black text-emerald-950 tracking-tight pt-1">
                {loading ? <Loader2 className="w-5 h-5 animate-spin text-emerald-600" /> : (results ? results.summary.completed : '—')}
              </div>
            </div>

            {/* KPI 3: Avg Wait Time */}
            <div className="p-4 rounded-xl bg-amber-50/50 border border-amber-200/60 space-y-1">
              <span className="text-[11px] font-bold text-amber-900 uppercase tracking-wider flex items-center gap-1">
                <Clock className="w-3.5 h-3.5 text-amber-600" /> Avg Wait Time
              </span>
              <div className="text-2xl font-black text-amber-950 tracking-tight pt-1">
                {loading ? (
                  <Loader2 className="w-5 h-5 animate-spin text-amber-600" />
                ) : results ? (
                  <>
                    {(results.summary.avg_waiting_time_sec / 60.0).toFixed(2)}
                    <span className="text-xs font-medium text-amber-800 ml-1">m</span>
                  </>
                ) : (
                  '—'
                )}
              </div>
            </div>

            {/* KPI 4: Avg Queue Length */}
            <div className="p-4 rounded-xl bg-slate-50/80 border border-slate-200/60 space-y-1">
              <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider flex items-center gap-1">
                <BarChart2 className="w-3.5 h-3.5 text-blue-600" /> Avg Queue Lq
              </span>
              <div className="text-2xl font-black text-slate-900 tracking-tight pt-1">
                {loading ? (
                  <Loader2 className="w-5 h-5 animate-spin text-slate-400" />
                ) : results ? (
                  results.summary.time_weighted_queue_length.toFixed(2)
                ) : (
                  '—'
                )}
              </div>
            </div>

            {/* KPI 5: ATM Utilization */}
            <div className="p-4 rounded-xl bg-slate-50/80 border border-slate-200/60 space-y-1">
              <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider flex items-center gap-1">
                <Activity className="w-3.5 h-3.5 text-blue-600" /> Utilization
              </span>
              <div className="text-2xl font-black text-slate-900 tracking-tight pt-1">
                {loading ? (
                  <Loader2 className="w-5 h-5 animate-spin text-slate-400" />
                ) : results ? (
                  <>
                    {(results.summary.average_atm_utilization * 100.0).toFixed(1)}
                    <span className="text-xs font-medium text-slate-500 ml-0.5">%</span>
                  </>
                ) : (
                  '—'
                )}
              </div>
            </div>

            {/* KPI 6: Throughput */}
            <div className="p-4 rounded-xl bg-slate-50/80 border border-slate-200/60 space-y-1">
              <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider flex items-center gap-1">
                <Zap className="w-3.5 h-3.5 text-blue-600" /> Throughput
              </span>
              <div className="text-2xl font-black text-slate-900 tracking-tight pt-1">
                {loading ? (
                  <Loader2 className="w-5 h-5 animate-spin text-slate-400" />
                ) : results ? (
                  <>
                    {results.summary.throughput_per_hour.toFixed(1)}
                    <span className="text-xs font-medium text-slate-500 ml-0.5">/h</span>
                  </>
                ) : (
                  '—'
                )}
              </div>
            </div>
          </div>

          {/* Queue Length Line Chart */}
          <div className="pt-2 border-t border-slate-100">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-xs font-bold text-slate-800 flex items-center gap-1.5 uppercase tracking-wider">
                <TrendingUp className="w-3.5 h-3.5 text-blue-600" />
                Queue Length Over Time (Lq)
              </h3>
            </div>

            {loading ? (
              <div className="h-56 bg-slate-50 rounded-xl border border-dashed border-slate-200 flex items-center justify-center text-slate-400 text-xs">
                <Loader2 className="w-4 h-4 animate-spin mr-2 text-blue-600" />
                Generating queue trajectory...
              </div>
            ) : queueChartData.length > 0 ? (
              <div className="bg-slate-50/50 p-3 rounded-xl border border-slate-100 h-56">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={queueChartData} margin={{ top: 10, right: 15, left: -15, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                    <XAxis
                      dataKey="timeMin"
                      tick={{ fontSize: 10, fill: '#64748b' }}
                      unit=" m"
                      tickLine={false}
                    />
                    <YAxis
                      allowDecimals={false}
                      tick={{ fontSize: 10, fill: '#64748b' }}
                      tickLine={false}
                    />
                    <Tooltip
                      formatter={(value: any) => [`${value} customers`, 'Queue Length']}
                      labelFormatter={(label) => `Time: ${label} mins`}
                      contentStyle={{ backgroundColor: '#ffffff', borderRadius: '8px', borderColor: '#e2e8f0', fontSize: '11px' }}
                    />
                    <Line
                      type="stepAfter"
                      dataKey="queueLength"
                      stroke="#2563eb"
                      strokeWidth={2}
                      dot={false}
                      activeDot={{ r: 3 }}
                      name="Queue Length"
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <div className="h-56 bg-slate-50 rounded-xl border border-dashed border-slate-200 flex items-center justify-center text-slate-400 text-xs">
                No simulation data available.
              </div>
            )}
          </div>
        </section>


        {/* 3. ATM STATUS */}
        <section className="bg-white border border-slate-200/80 rounded-2xl p-6 shadow-xs">
          <div className="border-b border-slate-100 pb-4 mb-6">
            <h2 className="text-base font-bold text-slate-900 tracking-tight flex items-center gap-2">
              <span className="w-6 h-6 rounded-md bg-blue-50 text-blue-600 font-bold text-xs flex items-center justify-center">3</span>
              ATM Status
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Individual operational metrics for each ATM server.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {results && results.atm_metrics.map((atm, idx) => {
              const isBusy = atm.status === 'BUSY';
              return (
                <div
                  key={atm.atm_id || idx}
                  className="p-4 rounded-xl border bg-white border-slate-200/80 shadow-2xs space-y-3"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-slate-900 text-sm flex items-center gap-2 font-mono">
                      <Server className="w-3.5 h-3.5 text-slate-400" />
                      ATM {idx + 1}
                    </span>

                    {/* Status Badge */}
                    <span
                      className={`px-2.5 py-0.5 rounded-full text-[11px] font-bold uppercase tracking-wider flex items-center gap-1.5 ${
                        isBusy
                          ? 'bg-amber-100 text-amber-800 border border-amber-300'
                          : 'bg-emerald-100 text-emerald-800 border border-emerald-300'
                      }`}
                    >
                      <span className={`w-1.5 h-1.5 rounded-full ${isBusy ? 'bg-amber-600' : 'bg-emerald-600'}`} />
                      {isBusy ? 'Busy' : 'Available'}
                    </span>
                  </div>

                  <div className="space-y-1.5 text-xs pt-2 border-t border-slate-100">
                    <div className="flex justify-between text-slate-600">
                      <span>Customers Served:</span>
                      <span className="font-bold text-slate-900 font-mono">{atm.total_customers_served}</span>
                    </div>

                    <div className="flex justify-between text-slate-600">
                      <span>Utilization:</span>
                      <span className="font-bold text-blue-600 font-mono">
                        {(atm.utilization * 100.0).toFixed(1)}%
                      </span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </section>

      </main>

      {/* Footer */}
      <footer className="border-t border-slate-200 bg-white py-4 text-center text-xs text-slate-400 font-medium">
        ATMFlow Intelligence • ATM Transaction & Queue Simulation
      </footer>
    </div>
  );
}
