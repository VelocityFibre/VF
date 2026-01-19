import { query } from "./_generated/server";
import { v } from "convex/values";

/**
 * Fixed Contractors Functions - Works with actual Convex data
 */

// Simple list - no schema assumptions
export const list = query({
  args: {
    limit: v.optional(v.number()),
    activeOnly: v.optional(v.boolean()),
  },
  handler: async (ctx, args) => {
    const limit = args.limit || 100;

    try {
      // @ts-ignore - Dynamic query
      let query = ctx.db.query("contractors");

      if (args.activeOnly) {
        // @ts-ignore
        query = query.filter((q) => q.eq(q.field("is_active"), true));
      }

      const contractors = await query.take(limit);

      return {
        status: "success",
        contractors: contractors,
        total: contractors.length,
      };
    } catch (error) {
      return {
        status: "error",
        message: String(error),
      };
    }
  },
});

// Count contractors
export const count = query({
  args: {},
  handler: async (ctx) => {
    try {
      // @ts-ignore
      const all = await ctx.db.query("contractors").collect();
      // @ts-ignore
      const active = all.filter((c) => c.is_active === true);

      return {
        status: "success",
        total: all.length,
        active: active.length,
        inactive: all.length - active.length,
      };
    } catch (error) {
      return {
        status: "error",
        message: String(error),
      };
    }
  },
});

// Search by company name
export const search = query({
  args: {
    query: v.string(),
  },
  handler: async (ctx, args) => {
    try {
      // @ts-ignore
      const all = await ctx.db.query("contractors").collect();

      const searchLower = args.query.toLowerCase();
      const matches = all.filter((contractor: any) => {
        const name = contractor.company_name || "";
        return name.toLowerCase().includes(searchLower);
      });

      return {
        status: "success",
        contractors: matches,
        total: matches.length,
      };
    } catch (error) {
      return {
        status: "error",
        message: String(error),
      };
    }
  },
});

// Aliases
export const listAll = list;
export const getAll = list;
export const getStats = count;
