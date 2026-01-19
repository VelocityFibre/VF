/**
 * GET /api/foto-reviews/pending
 * Returns pending foto reviews from Neon database (foto_ai_reviews table)
 * Replaces antigravity API proxy with direct Neon queries
 */

import type { NextApiRequest, NextApiResponse } from 'next';
import { neon } from '@neondatabase/serverless';

// Initialize SQL client once
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
    // Parse query parameters
    const {
      status = 'pending_review',
      project,
      search,
      page = '1',
      limit = '20'
    } = req.query;

    const pageNum = parseInt(page as string);
    const limitNum = parseInt(limit as string);
    const offset = (pageNum - 1) * limitNum;

    // Build WHERE conditions
    const conditions: string[] = [];

    // Status mapping: pending_review = feedback_sent false, sent = feedback_sent true
    if (status === 'pending_review') {
      conditions.push('feedback_sent = false');
    } else if (status === 'sent') {
      conditions.push('feedback_sent = true');
    }
    // Note: 'approved' and 'rejected' statuses not tracked in current schema

    // Search by DR number
    if (search && typeof search === 'string') {
      conditions.push(`dr_number ILIKE '%${search}%'`);
    }

    // Project filter (not in current schema, but leaving for future)
    if (project && typeof project === 'string') {
      // conditions.push(`project = '${project}'`);
    }

    const whereClause = conditions.length > 0
      ? `WHERE ${conditions.join(' AND ')}`
      : '';

    // Get total count using tagged template
    const countResult = status === 'pending_review'
      ? await sql`SELECT COUNT(*) as total FROM foto_ai_reviews WHERE feedback_sent = false`
      : status === 'sent'
      ? await sql`SELECT COUNT(*) as total FROM foto_ai_reviews WHERE feedback_sent = true`
      : await sql`SELECT COUNT(*) as total FROM foto_ai_reviews`;

    const total = parseInt(countResult[0].total);

    // Get paginated reviews using tagged template
    const reviews = status === 'pending_review'
      ? await sql`
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
          WHERE feedback_sent = false
          ORDER BY evaluation_date DESC
          LIMIT ${limitNum}
          OFFSET ${offset}
        `
      : status === 'sent'
      ? await sql`
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
          WHERE feedback_sent = true
          ORDER BY evaluation_date DESC
          LIMIT ${limitNum}
          OFFSET ${offset}
        `
      : await sql`
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
          ORDER BY evaluation_date DESC
          LIMIT ${limitNum}
          OFFSET ${offset}
        `;

    // Transform to expected format
    const transformedReviews = reviews.map((review: any) => ({
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
      edited_feedback: null, // Not tracked yet
      status: review.feedback_sent ? 'sent' : 'pending_review',
      feedback_sent: review.feedback_sent,
      feedback_sent_at: review.feedback_sent_at,
      evaluation_date: review.evaluation_date,
      created_at: review.created_at,
      updated_at: review.updated_at,
      // Additional fields expected by component
      project: 'Unknown',
      reviewer_id: null,
      reviewer_name: null,
      reviewed_at: null,
      rejection_reason: null
    }));

    const duration = Date.now() - startTime;

    return res.status(200).json({
      success: true,
      data: {
        reviews: transformedReviews,
        total,
        page: pageNum,
        limit: limitNum,
        totalPages: Math.ceil(total / limitNum)
      },
      duration_ms: duration
    });

  } catch (error: any) {
    const duration = Date.now() - startTime;

    console.error('Error fetching pending reviews:', error);

    return res.status(500).json({
      success: false,
      error: 'Failed to fetch pending reviews',
      message: error.message,
      duration_ms: duration
    });
  }
}
