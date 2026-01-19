"use strict";
Object.defineProperty(exports, "__esModule", { value: true });

exports.default = async function handler(req, res) {
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

  } catch (error) {
    console.error('Error fetching history:', error);

    return res.status(500).json({
      success: false,
      error: 'Failed to fetch history',
      message: error.message
    });
  }
}