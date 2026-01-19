/**
 * GET /api/foto-reviews/[jobId]/history
 * Get approval history for a specific DR
 * Currently returns empty array - history not tracked yet in new system
 */

import type { NextApiRequest, NextApiResponse } from 'next';

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

  try {
    const { jobId } = req.query;

    if (!jobId || typeof jobId !== 'string') {
      return res.status(400).json({
        success: false,
        error: 'Job ID is required'
      });
    }

    // TODO: Implement history tracking in database schema
    // For now, return empty array
    return res.status(200).json({
      success: true,
      data: []
    });

  } catch (error: any) {
    console.error('Error fetching history:', error);

    return res.status(500).json({
      success: false,
      error: 'Failed to fetch history',
      message: error.message
    });
  }
}
