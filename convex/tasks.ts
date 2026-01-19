import { query, mutation } from "./_generated/server";
import { v } from "convex/values";

/**
 * Task Management Functions for Convex Agent
 *
 * Provides CRUD operations for tasks with intelligent querying
 * and statistics generation.
 */

// ============================================================================
// QUERIES (Read Operations)
// ============================================================================

/**
 * List all tasks
 * Returns tasks with pagination support and sorting
 */
export const listTasks = query({
  args: {
    limit: v.optional(v.number()),
    status: v.optional(v.string()),
    priority: v.optional(v.string()),
  },
  handler: async (ctx, args) => {
    let tasksQuery = ctx.db.query("tasks").order("desc");

    // Filter by status if provided
    if (args.status) {
      tasksQuery = tasksQuery.filter((q) => q.eq(q.field("status"), args.status));
    }

    // Filter by priority if provided
    if (args.priority) {
      tasksQuery = tasksQuery.filter((q) => q.eq(q.field("priority"), args.priority));
    }

    // Apply limit
    const limit = args.limit || 100;
    const tasks = await tasksQuery.take(limit);

    return {
      status: "success",
      tasks: tasks,
      total: tasks.length,
    };
  },
});

/**
 * Get a specific task by ID
 */
export const getTask = query({
  args: { taskId: v.id("tasks") },
  handler: async (ctx, args) => {
    const task = await ctx.db.get(args.taskId);

    if (!task) {
      return {
        status: "error",
        message: "Task not found",
      };
    }

    return {
      status: "success",
      task: task,
    };
  },
});

/**
 * Search tasks by title or description
 */
export const searchTasks = query({
  args: { query: v.string() },
  handler: async (ctx, args) => {
    const allTasks = await ctx.db.query("tasks").collect();

    // Simple search - filter by keyword in title or description
    const query = args.query.toLowerCase();
    const matchingTasks = allTasks.filter(
      (task) =>
        task.title.toLowerCase().includes(query) ||
        (task.description && task.description.toLowerCase().includes(query))
    );

    return {
      status: "success",
      tasks: matchingTasks,
      total: matchingTasks.length,
      query: args.query,
    };
  },
});

/**
 * Get task statistics
 * Returns counts by status, priority, and totals
 */
export const getTaskStats = query({
  args: {},
  handler: async (ctx) => {
    const allTasks = await ctx.db.query("tasks").collect();

    // Count by status
    const byStatus = {
      pending: 0,
      in_progress: 0,
      completed: 0,
      blocked: 0,
    };

    // Count by priority
    const byPriority = {
      low: 0,
      medium: 0,
      high: 0,
      urgent: 0,
    };

    for (const task of allTasks) {
      // Count status
      if (task.status in byStatus) {
        byStatus[task.status as keyof typeof byStatus]++;
      }

      // Count priority
      if (task.priority in byPriority) {
        byPriority[task.priority as keyof typeof byPriority]++;
      }
    }

    return {
      status: "success",
      total: allTasks.length,
      byStatus: byStatus,
      byPriority: byPriority,
    };
  },
});

// ============================================================================
// MUTATIONS (Write Operations)
// ============================================================================

/**
 * Add a new task
 */
export const addTask = mutation({
  args: {
    title: v.string(),
    description: v.optional(v.string()),
    status: v.optional(
      v.union(
        v.literal("pending"),
        v.literal("in_progress"),
        v.literal("completed"),
        v.literal("blocked")
      )
    ),
    priority: v.optional(
      v.union(
        v.literal("low"),
        v.literal("medium"),
        v.literal("high"),
        v.literal("urgent")
      )
    ),
    assignedTo: v.optional(v.string()),
    dueDate: v.optional(v.number()),
    tags: v.optional(v.array(v.string())),
  },
  handler: async (ctx, args) => {
    const now = Date.now();

    const taskId = await ctx.db.insert("tasks", {
      title: args.title,
      description: args.description,
      status: args.status || "pending",
      priority: args.priority || "medium",
      assignedTo: args.assignedTo,
      dueDate: args.dueDate,
      tags: args.tags,
      createdAt: now,
      updatedAt: now,
    });

    return {
      status: "success",
      message: "Task created successfully",
      taskId: taskId,
    };
  },
});

/**
 * Update an existing task
 */
export const updateTask = mutation({
  args: {
    taskId: v.id("tasks"),
    title: v.optional(v.string()),
    description: v.optional(v.string()),
    status: v.optional(
      v.union(
        v.literal("pending"),
        v.literal("in_progress"),
        v.literal("completed"),
        v.literal("blocked")
      )
    ),
    priority: v.optional(
      v.union(
        v.literal("low"),
        v.literal("medium"),
        v.literal("high"),
        v.literal("urgent")
      )
    ),
    assignedTo: v.optional(v.string()),
    dueDate: v.optional(v.number()),
    tags: v.optional(v.array(v.string())),
  },
  handler: async (ctx, args) => {
    const { taskId, ...updates } = args;

    // Check if task exists
    const existingTask = await ctx.db.get(taskId);
    if (!existingTask) {
      return {
        status: "error",
        message: "Task not found",
      };
    }

    // Update task with timestamp
    await ctx.db.patch(taskId, {
      ...updates,
      updatedAt: Date.now(),
    });

    return {
      status: "success",
      message: "Task updated successfully",
      taskId: taskId,
    };
  },
});

/**
 * Delete a task
 */
export const deleteTask = mutation({
  args: { taskId: v.id("tasks") },
  handler: async (ctx, args) => {
    // Check if task exists
    const task = await ctx.db.get(args.taskId);
    if (!task) {
      return {
        status: "error",
        message: "Task not found",
      };
    }

    // Delete the task
    await ctx.db.delete(args.taskId);

    return {
      status: "success",
      message: "Task deleted successfully",
    };
  },
});

// ============================================================================
// ALIASES (for backward compatibility with different naming conventions)
// ============================================================================

export const list = listTasks;
export const getAll = listTasks;
export const add = addTask;
export const create = addTask;
export const get = getTask;
export const getById = getTask;
export const update = updateTask;
export const remove = deleteTask;
export const search = searchTasks;
export const stats = getTaskStats;
export const getStats = getTaskStats;
