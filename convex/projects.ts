import { query } from "./_generated/server";
import { v } from "convex/values";

/**
 * Fixed Projects Functions - Works with actual Convex data
 */

// Simple list - no schema assumptions
export const list = query({
  args: {
    limit: v.optional(v.number()),
    status: v.optional(v.string()),
  },
  handler: async (ctx, args) => {
    const limit = args.limit || 100;

    try {
      // @ts-ignore - Dynamic query
      let query = ctx.db.query("projects");

      if (args.status) {
        // @ts-ignore
        query = query.filter((q) => q.eq(q.field("status"), args.status));
      }

      const projects = await query.take(limit);

      return {
        status: "success",
        projects: projects,
        total: projects.length,
      };
    } catch (error) {
      return {
        status: "error",
        message: String(error),
      };
    }
  },
});

// Count projects
export const count = query({
  args: {},
  handler: async (ctx) => {
    try {
      // @ts-ignore
      const all = await ctx.db.query("projects").collect();

      // Count by status
      const byStatus: Record<string, number> = {};
      for (const project of all) {
        const status = (project as any).status || "unknown";
        byStatus[status] = (byStatus[status] || 0) + 1;
      }

      return {
        status: "success",
        total: all.length,
        byStatus: byStatus,
      };
    } catch (error) {
      return {
        status: "error",
        message: String(error),
      };
    }
  },
});

// Search by project name
export const search = query({
  args: {
    query: v.string(),
  },
  handler: async (ctx, args) => {
    try {
      // @ts-ignore
      const all = await ctx.db.query("projects").collect();

      const searchLower = args.query.toLowerCase();
      const matches = all.filter((project: any) => {
        const name = project.project_name || project.name || "";
        return name.toLowerCase().includes(searchLower);
      });

      return {
        status: "success",
        projects: matches,
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
