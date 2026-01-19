/**
 * GET /api/foto/evaluations
 * Returns all foto evaluations with optional filtering
 */

import type { NextApiRequest, NextApiResponse } from 'next';
import { sql } from '@/lib/neon';
import { log } from '@/lib/logger';

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const startTime = Date.now();

  try {
    const { feedback_sent, limit = '100', offset = '0' } = req.query;

    const limitNum = parseInt(limit as string);
    const offsetNum = parseInt(offset as string);
    const feedbackFilter = feedback_sent === 'true';

    // Query using tagged template literals
    const rows = await sql`
      SELECT
        dr_number,
        overall_status,
        average_score,
        total_steps,
        passed_steps,
        step_results,
        markdown_report,
        feedback_sent,
        evaluation_date
      FROM foto_ai_reviews
      WHERE feedback_sent = ${feedbackFilter}
      ORDER BY evaluation_date DESC
      LIMIT ${limitNum}
      OFFSET ${offsetNum}
    `;

    const duration = Date.now() - startTime;

    log.info('FotoEvaluations', `Retrieved ${rows.length} evaluations`);

    return res.status(200).json({
      success: true,
      data: rows,
      meta: {
        limit: limitNum,
        offset: offsetNum,
        returned: rows.length
      },
      duration_ms: duration
    });

  } catch (error: any) {
    const duration = Date.now() - startTime;

    log.error('FotoEvaluations', 'Failed', { error: error.message });

    return res.status(500).json({
      success: false,
      error: 'Failed to fetch evaluations',
      message: error.message,
      duration_ms: duration
    });
  }
}
