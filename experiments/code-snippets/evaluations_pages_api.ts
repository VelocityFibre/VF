/**
 * GET /api/foto/evaluations
 * Returns all foto evaluations with optional filtering
 * Pages Router API (Hostinger VPS)
 */

import type { NextApiRequest, NextApiResponse } from 'next';
import { sql } from '@/lib/neon';
import { log } from '@/lib/logger';

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  // Only allow GET
  if (req.method !== 'GET') {
    return res.status(405).json({
      success: false,
      error: 'Method not allowed'
    });
  }

  const startTime = Date.now();

  try {
    log.info('FotoEvaluations', 'Fetching all evaluations');

    // Parse query parameters
    const { feedback_sent, status, limit = '100', offset = '0' } = req.query;

    const conditions: string[] = [];
    const params: any[] = [];
    let paramIndex = 1;

    if (feedback_sent !== undefined) {
      conditions.push(`feedback_sent = $${paramIndex++}`);
      params.push(feedback_sent === 'true');
    }

    if (status && typeof status === 'string') {
      conditions.push(`overall_status = $${paramIndex++}`);
      params.push(status);
    }

    const whereClause = conditions.length > 0
      ? `WHERE ${conditions.join(' AND ')}`
      : '';

    // Query evaluations
    const query = `
      SELECT
        dr_number,
        overall_status,
        average_score,
        total_steps,
        passed_steps,
        step_results,
        markdown_report,
        feedback_sent,
        evaluation_date,
        created_at,
        updated_at
      FROM foto_evaluations
      ${whereClause}
      ORDER BY evaluation_date DESC
      LIMIT $${paramIndex++}
      OFFSET $${paramIndex}
    `;

    params.push(parseInt(limit as string), parseInt(offset as string));

    const result = await sql(query, params);
    const evaluations = result.rows;

    // Get total count
    const countQuery = `
      SELECT COUNT(*) as total
      FROM foto_evaluations
      ${whereClause}
    `;

    const countResult = await sql(
      countQuery,
      params.slice(0, params.length - 2) // Remove limit and offset
    );
    const total = parseInt(countResult.rows[0].total);

    const duration = Date.now() - startTime;

    log.info('FotoEvaluations', `Retrieved ${evaluations.length} evaluations in ${duration}ms`);

    return res.status(200).json({
      success: true,
      data: evaluations,
      meta: {
        total,
        limit: parseInt(limit as string),
        offset: parseInt(offset as string),
        returned: evaluations.length
      },
      duration_ms: duration
    });

  } catch (error: any) {
    const duration = Date.now() - startTime;

    log.error('FotoEvaluations', 'Failed to fetch evaluations', {
      error: error.message,
      stack: error.stack,
      duration_ms: duration
    });

    return res.status(500).json({
      success: false,
      error: 'Failed to fetch evaluations',
      message: error.message,
      duration_ms: duration
    });
  }
}
