import mysql from 'mysql2'
import dotenv from 'dotenv'

dotenv.config()

const pool = mysql.createPool({
        host: process.env.MYSQL_HOST ?? '127.0.0.1',
        user: process.env.MYSQL_USER ?? 'Michael',
        password: process.env.MYSQL_PASSWORD ?? 'hogbog89',
        database: process.env.MYSQL_DATABASE ?? 'cadet_tracker',
        waitForConnections: true,
        connectionLimit: 10,
        queueLimit: 0
}).promise();

// Centralized SQL strings the Flutter app (or API layer) will need.
// Keep these organized and parameterized (use `?` placeholders).
export const SQL = {
    // Cadets
    cadet_get_by_id: `SELECT cadet_id, cap_id, first_name, last_name, date_of_birth FROM cadet WHERE cadet_id = ?`,
    cadet_list: `SELECT cadet_id, cap_id, first_name, last_name, date_of_birth FROM cadet ORDER BY last_name, first_name LIMIT 200`,
    cadet_search: `SELECT cadet_id, cap_id, first_name, last_name, date_of_birth FROM cadet WHERE CONCAT(first_name, ' ', last_name) LIKE ? OR CAST(cap_id AS CHAR) LIKE ? ORDER BY last_name, first_name LIMIT 200`,
    cadet_insert: `INSERT INTO cadet (cap_id, first_name, last_name, date_of_birth) VALUES (?, ?, ?, ?)` ,
    cadet_update: `UPDATE cadet SET cap_id = COALESCE(?, cap_id), first_name = COALESCE(?, first_name), last_name = COALESCE(?, last_name), date_of_birth = COALESCE(?, date_of_birth) WHERE cadet_id = ?`,
    cadet_delete: `DELETE FROM cadet WHERE cadet_id = ?`,

    // Reports
    report_list: `SELECT report_id, cadet_cadet_id, report_type, description, Incident_date, resolved, resolved_by FROM report ORDER BY Incident_date DESC LIMIT 500`,
    report_get: `SELECT report_id, cadet_cadet_id, report_type, description, Incident_date, resolved, resolved_by FROM report WHERE report_id = ?`,
    report_insert: `INSERT INTO report (cadet_cadet_id, report_type, description, created_by, Incident_date, resolved, resolved_by) VALUES (?, ?, ?, NULL, ?, ?, ?)`,
    report_update: `UPDATE report SET report_type = COALESCE(?, report_type), description = COALESCE(?, description), Incident_date = COALESCE(?, Incident_date), resolved = COALESCE(?, resolved), resolved_by = COALESCE(?, resolved_by) WHERE report_id = ?`,
    report_delete: `DELETE FROM report WHERE report_id = ?`,

    // Positions
    position_list: 'SELECT position_id, position_name, line, level FROM `position` ORDER BY position_id',
    position_get: 'SELECT position_id, position_name, line, level FROM `position` WHERE position_id = ?',
    position_insert: 'INSERT INTO `position` (position_name, line, level) VALUES (?, ?, ?)',
    position_update: 'UPDATE `position` SET position_name = ?, line = ?, level = ? WHERE position_id = ?',
    position_delete: 'DELETE FROM `position` WHERE position_id = ?',
    position_unlink_cadets: `DELETE FROM position_has_cadet WHERE position_position_id = ?`,
    position_assign_cadet: `INSERT INTO position_has_cadet (position_position_id, cadet_cadet_id) VALUES (?, ?)`,
    position_unassign_cadet: `DELETE FROM position_has_cadet WHERE position_position_id = ? AND cadet_cadet_id = ?`,
    cadet_positions: 'SELECT p.position_id, p.position_name, p.line, p.level FROM position_has_cadet phc JOIN `position` p ON phc.position_position_id = p.position_id WHERE phc.cadet_cadet_id = ?',

    // Ranks & Requirements
    rank_list: 'SELECT rank_id, rank_name, rank_order FROM `rank` ORDER BY rank_order ASC',
    requirements_for_rank: `SELECT r.requirement_id, r.requirement_name, r.description FROM rank_has_requirement rr JOIN requirement r ON rr.rank_requirement_requirement_id = r.requirement_id WHERE rr.rank_rank_id = ? ORDER BY r.requirement_id`,
    requirement_insert: `INSERT INTO requirement (requirement_name, description) VALUES (?, ?)`,
    rank_requirement_link: `INSERT INTO rank_has_requirement (rank_rank_id, rank_requirement_requirement_id) VALUES (?, ?)`,
    rank_requirement_unlink: `DELETE FROM rank_has_requirement WHERE rank_rank_id = ? AND rank_requirement_requirement_id = ?`,
    requirement_delete: `DELETE FROM requirement WHERE requirement_id = ?`,

    // Helpful joins / profile queries
    cadet_full_profile: `SELECT c.cadet_id, c.cap_id, c.first_name, c.last_name, c.date_of_birth,
        (SELECT COUNT(*) FROM report r WHERE r.cadet_cadet_id = c.cadet_id) AS report_count
        FROM cadet c WHERE c.cadet_id = ?`,
    cadet_reports: `SELECT report_id, report_type, description, Incident_date, resolved FROM report WHERE cadet_cadet_id = ? ORDER BY Incident_date DESC`,
};

// Execution helpers
async function query(sql, params = []) {
    const [rows] = await pool.query(sql, params);
    return rows;
}

async function execute(sql, params = []) {
    const [res] = await pool.execute(sql, params);
    return res;
}

// Cadet helpers
export async function getCadetById(id) {
    return await query(SQL.cadet_get_by_id, [id]);
}

export async function listCadets() {
    return await query(SQL.cadet_list);
}

export async function searchCadets(q) {
    const like = `%${q}%`;
    return await query(SQL.cadet_search, [like, like]);
}

export async function createCadet({ cap_id, first_name, last_name, date_of_birth }) {
    const [res] = await pool.execute(SQL.cadet_insert, [cap_id, first_name, last_name, date_of_birth]);
    return { insertId: res.insertId };
}

export async function updateCadet(id, { cap_id, first_name, last_name, date_of_birth }) {
    const [res] = await pool.execute(SQL.cadet_update, [cap_id ?? null, first_name ?? null, last_name ?? null, date_of_birth ?? null, id]);
    return { affectedRows: res.affectedRows };
}

export async function deleteCadet(id) {
    const [res] = await pool.execute(SQL.cadet_delete, [id]);
    return { affectedRows: res.affectedRows };
}

// Reports helpers
export async function listReports() {
    return await query(SQL.report_list);
}

export async function getReport(id) {
    return await query(SQL.report_get, [id]);
}

export async function createReport({ cadet_cadet_id, report_type, description, Incident_date, resolved = 0, resolved_by = null }) {
    const [res] = await pool.execute(SQL.report_insert, [cadet_cadet_id, report_type, description, Incident_date, resolved, resolved_by]);
    return { insertId: res.insertId };
}

export async function updateReport(id, { report_type, description, Incident_date, resolved, resolved_by }) {
    const [res] = await pool.execute(SQL.report_update, [report_type ?? null, description ?? null, Incident_date ?? null, resolved ?? null, resolved_by ?? null, id]);
    return { affectedRows: res.affectedRows };
}

export async function deleteReport(id) {
    const [res] = await pool.execute(SQL.report_delete, [id]);
    return { affectedRows: res.affectedRows };
}

// Positions helpers
export async function listPositions() {
    return await query(SQL.position_list);
}

export async function getPosition(id) {
    return await query(SQL.position_get, [id]);
}

export async function createPosition({ position_name, line, level }) {
    const [res] = await pool.execute(SQL.position_insert, [position_name, line, level]);
    return { insertId: res.insertId };
}

export async function updatePosition(id, { position_name, line, level }) {
    const [res] = await pool.execute(SQL.position_update, [position_name, line, level, id]);
    return { affectedRows: res.affectedRows };
}

export async function deletePosition(id) {
    // unlink cadets first, then delete position in a transaction
    const conn = await pool.getConnection();
    try {
        await conn.beginTransaction();
        await conn.query(SQL.position_unlink_cadets, [id]);
        const [res] = await conn.query(SQL.position_delete, [id]);
        await conn.commit();
        return { affectedRows: res.affectedRows };
    } catch (err) {
        await conn.rollback();
        throw err;
    } finally {
        conn.release();
    }
}

export async function assignCadetToPosition(position_id, cadet_id) {
    const [res] = await pool.execute(SQL.position_assign_cadet, [position_id, cadet_id]);
    return { insertId: res.insertId };
}

export async function unassignCadetFromPosition(position_id, cadet_id) {
    const [res] = await pool.execute(SQL.position_unassign_cadet, [position_id, cadet_id]);
    return { affectedRows: res.affectedRows };
}

export async function listCadetPositions(cadet_id) {
    return await query(SQL.cadet_positions, [cadet_id]);
}

// Ranks & Requirements helpers
export async function listRanks() {
    return await query(SQL.rank_list);
}

export async function listRequirementsForRank(rank_id) {
    return await query(SQL.requirements_for_rank, [rank_id]);
}

export async function createRequirement({ requirement_name, description, rank_id = null }) {
    const conn = await pool.getConnection();
    try {
        await conn.beginTransaction();
        const [r] = await conn.query(SQL.requirement_insert, [requirement_name, description]);
        const reqId = r.insertId;
        if (rank_id) {
            await conn.query(SQL.rank_requirement_link, [rank_id, reqId]);
        }
        await conn.commit();
        return { requirement_id: reqId };
    } catch (err) {
        await conn.rollback();
        throw err;
    } finally {
        conn.release();
    }
}

export async function unlinkRequirementFromRank(rank_id, req_id) {
    const [res] = await pool.execute(SQL.rank_requirement_unlink, [rank_id, req_id]);
    return { affectedRows: res.affectedRows };
}

export async function deleteRequirement(req_id) {
    const [res] = await pool.execute(SQL.requirement_delete, [req_id]);
    return { affectedRows: res.affectedRows };
}

// Profile helpers
export async function getCadetFullProfile(id) {
    const profile = await query(SQL.cadet_full_profile, [id]);
    const reports = await query(SQL.cadet_reports, [id]);
    const positions = await listCadetPositions(id);
    return { profile: profile?.[0] ?? null, reports, positions };
}

export default {
    pool,
    SQL,
    query,
    execute
};