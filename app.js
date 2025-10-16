import express from 'express';
import cors from 'cors';
import bodyParser from 'body-parser';
import db from './database.js';

const app = express();
app.use(cors());
app.use(bodyParser.json());

const port = process.env.PORT || 5057;

app.get('/', (_req, res) => res.json({ ok: true, service: 'CAP_CADET_TRACKER Node API' }));

app.get('/api/test', async (_req, res) => {
	try {
		const rows = await db.query('SELECT 1 as ok');
		res.json({ ok: rows[0].ok });
	} catch (err) {
		res.status(500).json({ error: err?.message ?? String(err) });
	}
});

// Cadets
app.get('/api/cadets', async (req, res) => {
	try {
		const rows = await db.listCadets();
		res.json(rows);
	} catch (err) {
		res.status(500).json({ error: err?.message ?? String(err) });
	}
});

app.get('/api/cadets/search', async (req, res) => {
	try {
		const q = req.query.q?.toString() ?? '';
		const rows = q ? await db.searchCadets(q) : await db.listCadets();
		res.json(rows);
	} catch (err) {
		res.status(500).json({ error: err?.message ?? String(err) });
	}
});

app.get('/api/cadets/:id', async (req, res) => {
	try {
		const id = parseInt(req.params.id, 10);
		const rows = await db.getCadetById(id);
		if (!rows || rows.length === 0) return res.status(404).json({ error: 'Not found' });
		res.json(rows[0]);
	} catch (err) {
		res.status(500).json({ error: err?.message ?? String(err) });
	}
});

app.post('/api/cadets', async (req, res) => {
	try {
		const body = req.body;
		const r = await db.createCadet(body);
		// normalize response to { cadet_id }
		res.json({ cadet_id: r.insertId ?? r.cadet_id ?? null });
	} catch (err) {
		res.status(500).json({ error: err?.message ?? String(err) });
	}
});

app.put('/api/cadets/:id', async (req, res) => {
	try {
		const id = parseInt(req.params.id, 10);
		const body = req.body;
		const r = await db.updateCadet(id, body);
		res.json(r);
	} catch (err) {
		res.status(500).json({ error: err?.message ?? String(err) });
	}
});

app.delete('/api/cadets/:id', async (req, res) => {
	try {
		const id = parseInt(req.params.id, 10);
		const r = await db.deleteCadet(id);
		res.json(r);
	} catch (err) {
		res.status(500).json({ error: err?.message ?? String(err) });
	}
});

// Reports
app.get('/api/reports', async (_req, res) => {
	try {
		const rows = await db.listReports();
		res.json(rows);
	} catch (err) {
		res.status(500).json({ error: err?.message ?? String(err) });
	}
});

app.post('/api/reports', async (req, res) => {
	try {
		const body = req.body;
		const r = await db.createReport(body);
		res.json({ report_id: r.insertId ?? r.report_id ?? null });
	} catch (err) {
		res.status(500).json({ error: err?.message ?? String(err) });
	}
});

app.delete('/api/reports/:id', async (req, res) => {
	try {
		const id = parseInt(req.params.id, 10);
		const r = await db.deleteReport(id);
		res.json(r);
	} catch (err) {
		res.status(500).json({ error: err?.message ?? String(err) });
	}
});

// Positions
app.get('/api/positions', async (_req, res) => {
	try {
		const rows = await db.listPositions();
		res.json(rows);
	} catch (err) {
		res.status(500).json({ error: err?.message ?? String(err) });
	}
});

app.post('/api/positions', async (req, res) => {
	try {
		const body = req.body;
		const r = await db.createPosition(body);
		res.json({ position_id: r.insertId ?? r.position_id ?? null });
	} catch (err) {
		res.status(500).json({ error: err?.message ?? String(err) });
	}
});

app.put('/api/positions/:id', async (req, res) => {
	try {
		const id = parseInt(req.params.id, 10);
		const body = req.body;
		const r = await db.updatePosition(id, body);
		res.json(r);
	} catch (err) {
		res.status(500).json({ error: err?.message ?? String(err) });
	}
});

app.delete('/api/positions/:id', async (req, res) => {
	try {
		const id = parseInt(req.params.id, 10);
		const r = await db.deletePosition(id);
		res.json(r);
	} catch (err) {
		res.status(500).json({ error: err?.message ?? String(err) });
	}
});

// Requirements & Ranks
app.get('/api/ranks', async (_req, res) => {
	try {
		const rows = await db.listRanks();
		res.json(rows);
	} catch (err) {
		res.status(500).json({ error: err?.message ?? String(err) });
	}
});

app.get('/api/requirements', async (req, res) => {
	try {
		const rank_id = parseInt(req.query.rank_id ?? req.query.rank ?? -1, 10);
		if (isFinite(rank_id) && rank_id > 0) {
			const rows = await db.listRequirementsForRank(rank_id);
			res.json(rows);
		} else {
			res.status(400).json({ error: 'rank_id required' });
		}
	} catch (err) {
		res.status(500).json({ error: err?.message ?? String(err) });
	}
});

app.post('/api/requirements', async (req, res) => {
	try {
		const body = req.body;
		const r = await db.createRequirement(body);
		// db.createRequirement returns { requirement_id }
		res.json({ requirement_id: r.requirement_id ?? r.insertId ?? null });
	} catch (err) {
		res.status(500).json({ error: err?.message ?? String(err) });
	}
});

app.delete('/api/requirements/unlink', async (req, res) => {
	try {
		const rank_id = parseInt(req.query.rank_id, 10);
		const req_id = parseInt(req.query.req_id, 10);
		if (!rank_id || !req_id) return res.status(400).json({ error: 'rank_id and req_id required' });
		const r = await db.unlinkRequirementFromRank(rank_id, req_id);
		res.json(r);
	} catch (err) {
		res.status(500).json({ error: err?.message ?? String(err) });
	}
});

// Profile
app.get('/api/cadets/:id/profile', async (req, res) => {
	try {
		const id = parseInt(req.params.id, 10);
		const p = await db.getCadetFullProfile(id);
		res.json(p);
	} catch (err) {
		res.status(500).json({ error: err?.message ?? String(err) });
	}
});

// Diagnostic
app.get('/api/diag', async (_req, res) => {
	try {
		const rows = await db.query('SELECT DATABASE() AS db');
		res.json({ ok: true, database: rows?.[0]?.db ?? null });
	} catch (err) {
		res.status(500).json({ error: err?.message ?? String(err) });
	}
});

// start server after verifying DB connectivity
async function startServer() {
	try {
		console.log('Checking DB connection...');
		const r = await db.query('SELECT 1 AS ok');
		if (!r || r.length === 0) throw new Error('DB test returned no rows');
		console.log('DB connection OK');
		app.listen(port, '127.0.0.1', () => console.log(`API listening on http://127.0.0.1:${port}`));
	} catch (err) {
		console.error('Failed to connect to database:', err?.message ?? err);
		process.exitCode = 2;
	}
}

startServer();

// Run: npm install express cors body-parser mysql2 dotenv
// Then: node app.js
