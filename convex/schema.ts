import { defineSchema, defineTable } from "convex/server";
import { v } from "convex/values";

/**
 * Convex Database Schema for VF Agent Workforce
 *
 * Defines the structure for:
 * - Tasks: Project/workflow tasks
 * - Contractors: Contractor/vendor information
 * - Projects: Project tracking
 * - SyncRecords: Neon → Convex sync metadata
 */

export default defineSchema({
  // Tasks Collection - Flexible schema to match existing data
  tasks: defineTable({
    title: v.string(),
    description: v.optional(v.string()),
    status: v.string(), // More flexible
    priority: v.optional(v.string()), // Optional and flexible
    assignedTo: v.optional(v.string()),
    dueDate: v.optional(v.number()),
    createdAt: v.optional(v.number()), // Optional
    updatedAt: v.optional(v.number()), // Optional
    tags: v.optional(v.array(v.string())),
    category: v.optional(v.string()), // Found in existing data
  })
    .index("by_status", ["status"]),

  // Contractors Collection
  contractors: defineTable({
    company_name: v.string(),
    status: v.optional(v.string()),
    is_active: v.boolean(),
    email: v.optional(v.string()),
    phone: v.optional(v.string()),
    address: v.optional(v.string()),
    contact_person: v.optional(v.string()),
    neon_id: v.optional(v.string()), // Reference to Neon database ID
    created_at: v.optional(v.number()),
    updated_at: v.optional(v.number()),
    synced_at: v.optional(v.string()), // ISO string from sync
  })
    .index("by_active", ["is_active"])
    .index("by_neon_id", ["neon_id"])
    .index("by_name", ["company_name"]),

  // Projects Collection
  projects: defineTable({
    name: v.string(),
    description: v.optional(v.string()),
    status: v.string(), // Make more flexible to match existing data
    contractor_id: v.optional(v.id("contractors")),
    start_date: v.optional(v.number()),
    end_date: v.optional(v.number()),
    budget: v.optional(v.number()),
    location: v.optional(v.string()),
    neon_id: v.optional(v.string()), // Reference to Neon database ID
    created_at: v.optional(v.number()),
    updated_at: v.optional(v.number()),
    synced_at: v.optional(v.string()), // ISO string from sync
  })
    .index("by_status", ["status"])
    .index("by_contractor", ["contractor_id"])
    .index("by_neon_id", ["neon_id"]),

  // Sync Records - Track Neon → Convex synchronization
  syncRecords: defineTable({
    tableName: v.string(), // "contractors", "projects", etc.
    neonId: v.string(), // ID in Neon database
    convexId: v.string(), // ID in Convex database
    lastSyncedAt: v.number(),
    syncStatus: v.union(
      v.literal("success"),
      v.literal("failed"),
      v.literal("pending")
    ),
    errorMessage: v.optional(v.string()),
  })
    .index("by_table", ["tableName"])
    .index("by_neon_id", ["neonId"])
    .index("by_last_synced", ["lastSyncedAt"]),
});
