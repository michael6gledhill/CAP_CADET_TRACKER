import mysql from 'mysql2/promise';
import fs from 'fs';
import path from 'path';
import dotenv from 'dotenv';

// load .env if present
const envPath = path.resolve(process.cwd(), '.env');
if (fs.existsSync(envPath)) dotenv.config({ path: envPath });

const pool = mysql.createPool({
  host: process.env.MYSQL_HOST || '127.0.0.1',
  user: process.env.MYSQL_USER || process.env.USER || 'Michael',
  password: process.env.MYSQL_PASSWORD || process.env.PASSWORD || 'hogbog89',
  database: process.env.MYSQL_DATABASE || 'cadet_tracker',
  port: process.env.MYSQL_PORT ? parseInt(process.env.MYSQL_PORT, 10) : 3306,
  waitForConnections: true,
  connectionLimit: 10,
  queueLimit: 0,
});

async function query(sql, params = []) {
  const [rows] = await pool.query(sql, params);
  return rows;
}

async function execute(sql, params = []) {
  const [res] = await pool.execute(sql, params);
  return res;
}

// Cadets
async function listCadets() {
  return await query('SELECT cadet_id, cap_id, first_name, last_name, date_of_birth FROM cadet ORDER BY last_name, first_name LIMIT 1000');
}

async function searchCadets(q) {
  const like = `%${q}%`;
  return await query('SELECT cadet_id, cap_id, first_name, last_name, date_of_birth FROM cadet WHERE CONCAT(first_name, " ", last_name) LIKE ? OR CAST(cap_id AS CHAR) LIKE ? ORDER BY last_name, first_name LIMIT 200', [like, like]);
}

async function getCadetById(id) {
  return await query('SELECT * FROM cadet WHERE cadet_id = ?', [id]);
}

async function createCadet(obj) {
  const keys = Object.keys(obj || {});
  if (keys.length === 0) return { insertId: null };
  const cols = keys.map(k => `\`${k}\``).join(',');
  const placeholders = keys.map(() => '?').join(',');
  const vals = keys.map(k => obj[k]);
  return await execute(`INSERT INTO cadet (${cols}) VALUES (${placeholders})`, vals);
}

async function updateCadet(id, obj) {
  const keys = Object.keys(obj || {});
  if (keys.length === 0) return { affectedRows: 0 };
  const setClause = keys.map(k => `\`${k}\` = ?`).join(',');
  const vals = keys.map(k => obj[k]);
  vals.push(id);
  return await execute(`UPDATE cadet SET ${setClause} WHERE cadet_id = ?`, vals);
}

async function deleteCadet(id) {
  return await execute('DELETE FROM cadet WHERE cadet_id = ?', [id]);
}

// Reports
async function listReports() {
  return await query('SELECT report_id, cadet_cadet_id, report_type, Incident_date, resolved FROM report ORDER BY Incident_date DESC LIMIT 500');
}

async function createReport(obj) {
  const keys = Object.keys(obj || {});
  const cols = keys.map(k => `\`${k}\``).join(',');
  const placeholders = keys.map(() => '?').join(',');
  const vals = keys.map(k => obj[k]);
  return await execute(`INSERT INTO report (${cols}) VALUES (${placeholders})`, vals);
}

async function deleteReport(id) {
  return await execute('DELETE FROM report WHERE report_id = ?', [id]);
}

// Positions
async function listPositions() {
  return await query('SELECT position_id, position_name, line, level FROM `position` ORDER BY position_id');
}

async function createPosition(obj) {
  const keys = Object.keys(obj || {});
  const cols = keys.map(k => `\`${k}\``).join(',');
  const placeholders = keys.map(() => '?').join(',');
  const vals = keys.map(k => obj[k]);
  return await execute(`INSERT INTO ` + '`position`' + ` (${cols}) VALUES (${placeholders})`, vals);
}

async function updatePosition(id, obj) {
  const keys = Object.keys(obj || {});
  if (keys.length === 0) return { affectedRows: 0 };
  const setClause = keys.map(k => `\`${k}\` = ?`).join(',');
  const vals = keys.map(k => obj[k]);
  vals.push(id);
  return await execute(`UPDATE ` + '`position`' + ` SET ${setClause} WHERE position_id = ?`, vals);
}

async function deletePosition(id) {
  // first unlink cadets, then delete the position
  await execute('DELETE FROM position_has_cadet WHERE position_position_id = ?', [id]);
  return await execute('DELETE FROM `position` WHERE position_id = ?', [id]);
}

// Ranks & Requirements
async function listRanks() {
  return await query('SELECT rank_id, rank_name FROM `rank` ORDER BY rank_order ASC');
}

async function listRequirementsForRank(rankId) {
  return await query(`
    SELECT r.requirement_id, r.requirement_name, r.description
    FROM rank_has_requirement rr
    JOIN requirement r ON rr.rank_requirement_requirement_id = r.requirement_id
    WHERE rr.rank_rank_id = ?
    ORDER BY r.requirement_id
  `, [rankId]);
}

async function createRequirement(obj) {
  const keys = Object.keys(obj || {});
  const cols = keys.map(k => `\`${k}\``).join(',');
  const placeholders = keys.map(() => '?').join(',');
  const vals = keys.map(k => obj[k]);
  const res = await execute(`INSERT INTO requirement (${cols}) VALUES (${placeholders})`, vals);
  // Optionally link to rank if rank_id provided
  if (obj.rank_id) {
    await execute('INSERT INTO rank_has_requirement (rank_rank_id, rank_requirement_requirement_id) VALUES (?, ?)', [obj.rank_id, res.insertId]);
  }
  return { requirement_id: res.insertId };
}

async function unlinkRequirementFromRank(rankId, reqId) {
  return await execute('DELETE FROM rank_has_requirement WHERE rank_rank_id = ? AND rank_requirement_requirement_id = ?', [rankId, reqId]);
}

// Profile
async function getCadetFullProfile(id) {
  const cadetRows = await query('SELECT cadet_id, cap_id, first_name, last_name, date_of_birth FROM cadet WHERE cadet_id = ?', [id]);
  const cadet = cadetRows[0] ?? null;
  const reports = await query('SELECT report_id, report_type, description, Incident_date, resolved FROM report WHERE cadet_cadet_id = ? ORDER BY Incident_date DESC', [id]);
  const positions = await query(`SELECT p.position_id, p.position_name, phc.position_has_cadet_id FROM position_has_cadet phc JOIN \
    \`position\` p ON phc.position_position_id = p.position_id WHERE phc.cadet_cadet_id = ?`, [id]);
  return { cadet, reports, positions };
}

// Cadet helpers: ranks, requirements, capid lookup --------------------------------
async function listCadetRanks(cadetId) {
  return await query('SELECT rank_rank_id FROM rank_has_cadet WHERE cadet_cadet_id = ?', [cadetId]);
}

async function listCadetCompletedRequirements(cadetId) {
  // Assumes a cadet_has_requirement table with columns cadet_cadet_id and requirement_requirement_id
  return await query('SELECT requirement_requirement_id FROM cadet_has_requirement WHERE cadet_cadet_id = ?', [cadetId]);
}

async function toggleCadetRequirement(cadetId, reqId, completed) {
  if (completed) {
    // insert if not exists
    return await execute('INSERT IGNORE INTO cadet_has_requirement (cadet_cadet_id, requirement_requirement_id, completed_date) VALUES (?, ?, NOW())', [cadetId, reqId]);
  } else {
    return await execute('DELETE FROM cadet_has_requirement WHERE cadet_cadet_id = ? AND requirement_requirement_id = ?', [cadetId, reqId]);
  }
}

async function findCadetByCapId(capId) {
  return await query('SELECT cadet_id, cap_id, first_name, last_name, date_of_birth FROM cadet WHERE cap_id = ?', [capId]);
}

// Inspections: store aggregate score, inspection row, and link to cadet -----------------
async function listInspectionsForCadet(cadetId) {
  // This joins inspection, inspection_score and cadet_has_inspection if those tables exist with expected columns.
  return await query(`
    SELECT i.inspection_id, i.Inspection_date AS date, s.score AS total_score, i.rating, i.comments
    FROM inspection i
    LEFT JOIN inspection_score s ON i.inspection_score_idinspection_score = s.inspection_score_id
    LEFT JOIN cadet_has_inspection chi ON chi.inspection_inspection_id = i.inspection_id
    WHERE chi.cadet_cadet_id = ?
    ORDER BY i.Inspection_date DESC
  `, [cadetId]);
}
async function createInspection(payload) {
  // payload expected: { cadet_id, inspector_capid, date, total_score, rating, comments }
  const { cadet_id, inspector_capid, date, total_score, rating, comments } = payload || {};
  // insert aggregate score first
  const resScore = await execute('INSERT INTO inspection_score (category, score) VALUES (?, ?)', ['aggregate', total_score || 0]);
  const scoreId = resScore.insertId;
  const resIns = await execute('INSERT INTO inspection (inspection_score_idinspection_score, Inspector_capid, Inspection_date, rating, comments) VALUES (?, ?, ?, ?, ?)', [scoreId, inspector_capid || null, date || new Date(), rating || null, comments || null]);
  const insId = resIns.insertId;
  if (cadet_id) {
    await execute('INSERT INTO cadet_has_inspection (cadet_cadet_id, inspection_inspection_id) VALUES (?, ?)', [cadet_id, insId]);
  }
  return { inspection_id: insId, inspection_score_id: scoreId };
}

async function deleteInspection(id) {
  // try to remove linking row(s) then inspection and score
  const rows = await query('SELECT inspection_score_idinspection_score FROM inspection WHERE inspection_id = ?', [id]);
  const scoreId = rows?.[0]?.inspection_score_idinspection_score ?? null;
  await execute('DELETE FROM cadet_has_inspection WHERE inspection_inspection_id = ?', [id]);
  await execute('DELETE FROM inspection WHERE inspection_id = ?', [id]);
  if (scoreId) await execute('DELETE FROM inspection_score WHERE inspection_score_id = ?', [scoreId]);
  return { deleted: true };
}
export default {
  query,
  execute,
  listCadets,
  searchCadets,
  getCadetById,
  createCadet,
  updateCadet,
  deleteCadet,
  listReports,
  createReport,
  deleteReport,
  listPositions,
  createPosition,
  updatePosition,
  deletePosition,
  listRanks,
  listRequirementsForRank,
  createRequirement,
  unlinkRequirementFromRank,
  getCadetFullProfile,
  listCadetRanks,
  listCadetCompletedRequirements,
  toggleCadetRequirement,
  findCadetByCapId,
  listInspectionsForCadet,
  createInspection,
  deleteInspection,
};
