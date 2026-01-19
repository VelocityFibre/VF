import { query, mutation } from "./_generated/server";
import { v } from "convex/values";

/**
 * Sync Management Functions for Neon → Convex Integration
 *
 * Tracks synchronization status and provides sync metadata
 */

// ============================================================================
// QUERIES (Read Operations)
// ============================================================================

/**
 * Get synchronization statistics
 * Returns sync status by table and overall metrics
 */
export const getSyncStats = query({
  args: {},
  handler: async (ctx) => {
    const allSyncRecords = await ctx.db.query("syncRecords").collect();

    // Group by table
    const byTable: Record<string, any> = {};

    for (const record of allSyncRecords) {
      if (!byTable[record.tableName]) {
        byTable[record.tableName] = {
          total: 0,
          successful: 0,
          failed: 0,
          pending: 0,
          lastSync: null as number | null,
        };
      }

      byTable[record.tableName].total++;
      byTable[record.tableName][record.syncStatus]++;

      // Track most recent sync
      if (
        !byTable[record.tableName].lastSync ||
        record.lastSyncedAt > byTable[record.tableName].lastSync
      ) {
        byTable[record.tableName].lastSync = record.lastSyncedAt;
      }
    }

    // Find overall last sync time
    let lastSync: number | null = null;
    for (const record of allSyncRecords) {
      if (!lastSync || record.lastSyncedAt > lastSync) {
        lastSync = record.lastSyncedAt;
      }
    }

    return {
      status: "success",
      totalMappings: allSyncRecords.length,
      byTable: byTable,
      lastSync: lastSync,
    };
  },
});

/**
 * Get last sync time for a specific table or overall
 */
export const getLastSyncTime = query({
  args: {
    tableName: v.optional(v.string()),
  },
  handler: async (ctx, args) => {
    let query = ctx.db.query("syncRecords");

    if (args.tableName) {
      const records = await query
        .withIndex("by_table", (q) => q.eq("tableName", args.tableName))
        .collect();

      if (records.length === 0) {
        return {
          status: "success",
          tableName: args.tableName,
          lastSync: null,
          message: "No sync records found for this table",
        };
      }

      const lastSync = Math.max(...records.map((r) => r.lastSyncedAt));

      return {
        status: "success",
        tableName: args.tableName,
        lastSync: lastSync,
        recordCount: records.length,
      };
    }

    // Get overall last sync
    const allRecords = await query.collect();

    if (allRecords.length === 0) {
      return {
        status: "success",
        lastSync: null,
        message: "No sync records found",
      };
    }

    const lastSync = Math.max(...allRecords.map((r) => r.lastSyncedAt));

    return {
      status: "success",
      lastSync: lastSync,
      totalRecords: allRecords.length,
    };
  },
});

/**
 * Get sync record by Neon ID
 * Useful for checking if a Neon record has been synced
 */
export const getSyncRecord = query({
  args: {
    tableName: v.string(),
    neonId: v.string(),
  },
  handler: async (ctx, args) => {
    const record = await ctx.db
      .query("syncRecords")
      .withIndex("by_neon_id", (q) => q.eq("neonId", args.neonId))
      .filter((q) => q.eq(q.field("tableName"), args.tableName))
      .first();

    if (!record) {
      return {
        status: "error",
        message: "Sync record not found",
      };
    }

    return {
      status: "success",
      syncRecord: record,
    };
  },
});

/**
 * Get all sync records for a table
 */
export const getSyncRecordsByTable = query({
  args: {
    tableName: v.string(),
    limit: v.optional(v.number()),
  },
  handler: async (ctx, args) => {
    const limit = args.limit || 100;

    const records = await ctx.db
      .query("syncRecords")
      .withIndex("by_table", (q) => q.eq("tableName", args.tableName))
      .take(limit);

    return {
      status: "success",
      records: records,
      total: records.length,
    };
  },
});

// ============================================================================
// MUTATIONS (Write Operations)
// ============================================================================

/**
 * Record a sync operation
 * Creates or updates a sync record when data is synced from Neon
 */
export const recordSync = mutation({
  args: {
    tableName: v.string(),
    neonId: v.string(),
    convexId: v.string(),
    syncStatus: v.union(v.literal("success"), v.literal("failed"), v.literal("pending")),
    errorMessage: v.optional(v.string()),
  },
  handler: async (ctx, args) => {
    const now = Date.now();

    // Check if sync record already exists
    const existing = await ctx.db
      .query("syncRecords")
      .withIndex("by_neon_id", (q) => q.eq("neonId", args.neonId))
      .filter((q) => q.eq(q.field("tableName"), args.tableName))
      .first();

    if (existing) {
      // Update existing record
      await ctx.db.patch(existing._id, {
        convexId: args.convexId,
        lastSyncedAt: now,
        syncStatus: args.syncStatus,
        errorMessage: args.errorMessage,
      });

      return {
        status: "success",
        message: "Sync record updated",
        syncRecordId: existing._id,
      };
    }

    // Create new sync record
    const syncRecordId = await ctx.db.insert("syncRecords", {
      tableName: args.tableName,
      neonId: args.neonId,
      convexId: args.convexId,
      lastSyncedAt: now,
      syncStatus: args.syncStatus,
      errorMessage: args.errorMessage,
    });

    return {
      status: "success",
      message: "Sync record created",
      syncRecordId: syncRecordId,
    };
  },
});

/**
 * Clear sync records for a table
 * Useful for resetting sync state
 */
export const clearSyncRecords = mutation({
  args: {
    tableName: v.string(),
  },
  handler: async (ctx, args) => {
    if (!args.tableName) {
      return {
        status: "error",
        message: "tableName is required",
      };
    }

    const records = await ctx.db
      .query("syncRecords")
      .withIndex("by_table", (q) => q.eq("tableName", args.tableName))
      .collect();

    for (const record of records) {
      await ctx.db.delete(record._id);
    }

    return {
      status: "success",
      message: `Cleared ${records.length} sync records for table: ${args.tableName}`,
      deletedCount: records.length,
    };
  },
});

// ============================================================================
// ALIASES
// ============================================================================

export const getStats = getSyncStats;
export const getLastSync = getLastSyncTime;
