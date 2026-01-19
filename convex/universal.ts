import { query } from "./_generated/server";
import { v } from "convex/values";

/**
 * Universal Query Functions for ALL Tables
 *
 * These functions work with any table in the database,
 * giving agents access to all 30+ FibreFlow tables.
 */

/**
 * Universal list function - works with any table
 */
export const listFromTable = query({
  args: {
    tableName: v.string(),
    limit: v.optional(v.number()),
  },
  handler: async (ctx, args) => {
    const limit = args.limit || 100;

    try {
      // @ts-ignore - Dynamic table access
      const results = await ctx.db
        .query(args.tableName)
        .take(limit);

      return {
        status: "success",
        tableName: args.tableName,
        data: results,
        total: results.length,
      };
    } catch (error) {
      return {
        status: "error",
        tableName: args.tableName,
        error: String(error),
        message: `Table '${args.tableName}' might not exist or is empty`,
      };
    }
  },
});

/**
 * Universal get by ID function
 */
export const getFromTable = query({
  args: {
    tableName: v.string(),
    id: v.id("_any"),
  },
  handler: async (ctx, args) => {
    try {
      // @ts-ignore - Dynamic table access
      const record = await ctx.db.get(args.id);

      if (!record) {
        return {
          status: "error",
          message: "Record not found",
        };
      }

      return {
        status: "success",
        tableName: args.tableName,
        data: record,
      };
    } catch (error) {
      return {
        status: "error",
        error: String(error),
      };
    }
  },
});

/**
 * Universal count function
 */
export const countInTable = query({
  args: {
    tableName: v.string(),
  },
  handler: async (ctx, args) => {
    try {
      // @ts-ignore - Dynamic table access
      const results = await ctx.db.query(args.tableName).collect();

      return {
        status: "success",
        tableName: args.tableName,
        count: results.length,
      };
    } catch (error) {
      return {
        status: "error",
        tableName: args.tableName,
        error: String(error),
      };
    }
  },
});

/**
 * Universal paginated query
 */
export const queryTable = query({
  args: {
    tableName: v.string(),
    offset: v.optional(v.number()),
    limit: v.optional(v.number()),
  },
  handler: async (ctx, args) => {
    const offset = args.offset || 0;
    const limit = args.limit || 50;

    try {
      // @ts-ignore - Dynamic table access
      const allResults = await ctx.db.query(args.tableName).collect();
      const paginatedResults = allResults.slice(offset, offset + limit);

      return {
        status: "success",
        tableName: args.tableName,
        data: paginatedResults,
        offset: offset,
        limit: limit,
        total: allResults.length,
        hasMore: offset + limit < allResults.length,
      };
    } catch (error) {
      return {
        status: "error",
        tableName: args.tableName,
        error: String(error),
      };
    }
  },
});

/**
 * Get sample data from any table (first 5 records)
 */
export const sampleTable = query({
  args: {
    tableName: v.string(),
  },
  handler: async (ctx, args) => {
    try {
      // @ts-ignore - Dynamic table access
      const results = await ctx.db.query(args.tableName).take(5);

      return {
        status: "success",
        tableName: args.tableName,
        sample: results,
        count: results.length,
      };
    } catch (error) {
      return {
        status: "error",
        tableName: args.tableName,
        error: String(error),
      };
    }
  },
});

// Create specific wrappers for common FibreFlow tables
// BOQs
export const listBOQs = query({
  args: { limit: v.optional(v.number()) },
  handler: async (ctx, args) => {
    const limit = args.limit || 100;
    // @ts-ignore
    const results = await ctx.db.query("boqs").take(limit);
    return { status: "success", data: results, total: results.length };
  },
});

// RFQs
export const listRFQs = query({
  args: { limit: v.optional(v.number()) },
  handler: async (ctx, args) => {
    const limit = args.limit || 100;
    // @ts-ignore
    const results = await ctx.db.query("rfqs").take(limit);
    return { status: "success", data: results, total: results.length };
  },
});

// Quotes
export const listQuotes = query({
  args: { limit: v.optional(v.number()) },
  handler: async (ctx, args) => {
    const limit = args.limit || 100;
    // @ts-ignore
    const results = await ctx.db.query("quotes").take(limit);
    return { status: "success", data: results, total: results.length };
  },
});

// Materials
export const listMaterials = query({
  args: { limit: v.optional(v.number()) },
  handler: async (ctx, args) => {
    const limit = args.limit || 100;
    // @ts-ignore
    const results = await ctx.db.query("materials").take(limit);
    return { status: "success", data: results, total: results.length };
  },
});

// Equipment
export const listEquipment = query({
  args: { limit: v.optional(v.number()) },
  handler: async (ctx, args) => {
    const limit = args.limit || 100;
    // @ts-ignore
    const results = await ctx.db.query("equipment").take(limit);
    return { status: "success", data: results, total: results.length };
  },
});

// Meetings
export const listMeetings = query({
  args: { limit: v.optional(v.number()) },
  handler: async (ctx, args) => {
    const limit = args.limit || 100;
    // @ts-ignore
    const results = await ctx.db.query("meetings").take(limit);
    return { status: "success", data: results, total: results.length };
  },
});

// Clients
export const listClients = query({
  args: { limit: v.optional(v.number()) },
  handler: async (ctx, args) => {
    const limit = args.limit || 100;
    // @ts-ignore
    const results = await ctx.db.query("clients").take(limit);
    return { status: "success", data: results, total: results.length };
  },
});

// VPS Servers
export const listVPSServers = query({
  args: { limit: v.optional(v.number()) },
  handler: async (ctx, args) => {
    const limit = args.limit || 100;
    // @ts-ignore
    const results = await ctx.db.query("vps_servers").take(limit);
    return { status: "success", data: results, total: results.length };
  },
});
