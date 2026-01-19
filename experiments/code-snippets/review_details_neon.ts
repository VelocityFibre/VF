/**
 * GET /api/foto-reviews/[jobId]
 * Get review details for a specific DR from Neon database
 */

import type { NextApiRequest, NextApiResponse } from 'next';
import { neon } from '@neondatabase/serverless';

const sql = neon(process.env.DATABASE_URL!);

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  if (req.method !== 'GET') {
    return res.status(405).json({
      success: false,
      error: 'Method not allowed'
    });
  }

  const startTime = Date.now();

  try {
    const { jobId } = req.query;

    if (!jobId || typeof jobId !== 'string') {
      return res.status(400).json({
        success: false,
        error: 'Job ID is required'
      });
    }

    // Query evaluation by DR number (jobId = dr_number)
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
        feedback_sent_at,
        evaluation_date,
        created_at,
        updated_at
      FROM foto_ai_reviews
      WHERE dr_number = ${jobId}
      LIMIT 1
    `;

    if (rows.length === 0) {
      return res.status(404).json({
        success: false,
        error: 'Review not found',
        message: `No evaluation found for DR ${jobId}`
      });
    }

    const review = rows[0];

    // Transform to expected format
    const transformedReview = {
      job_id: review.dr_number,
      dr_number: review.dr_number,
      overall_status: review.overall_status,
      average_score: parseFloat(review.average_score),
      total_steps: review.total_steps,
      passed_steps: review.passed_steps,
      step_results: Array.isArray(review.step_results)
        ? review.step_results
        : JSON.parse(review.step_results || '[]'),
      ai_generated_feedback: review.markdown_report || '',
      edited_feedback: null,  // Not tracked yet
      status: review.feedback_sent ? 'sent' : 'pending_review',
      feedback_sent: review.feedback_sent,
      feedback_sent_at: review.feedback_sent_at,
      evaluation_date: review.evaluation_date,
      created_at: review.created_at,
      updated_at: review.updated_at,
      // Additional fields
      project: 'Unknown',
      reviewer_id: null,
      reviewer_name: null,
      reviewed_at: null,
      rejection_reason: null
    };

    const duration = Date.now() - startTime;

    return res.status(200).json({
      success: true,
      data: transformedReview,
      duration_ms: duration
    });

  } catch (error: any) {
    const duration = Date.now() - startTime;

    console.error('Error fetching review details:', error);

    return res.status(500).json({
      success: false,
      error: 'Failed to fetch review details',
      message: error.message,
      duration_ms: duration
    });
  }
}
