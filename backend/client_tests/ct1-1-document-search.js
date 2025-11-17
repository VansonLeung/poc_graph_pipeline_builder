#!/usr/bin/env node
"use strict"

/**
 * Client-side sanity checks for the FastAPI backend.
 *
 * Features:
 *  - Selective execution by test index: `node ct1-1-document-search.js 1,3,5`
 *  - Group execution: `node ct1-1-document-search.js --groups=indexes,documents`
 *  - Full run (default) covers indexes, documents, and search endpoints.
 */

const BASE_URL = process.env.API_BASE_URL ?? "http://localhost:19800/api"
const GROUPS = ["indexes", "documents", "search", "cleanup"]

const { logger } = require("./utils/logger")
const { createHttpClient } = require("./utils/httpClient")
const { parseSelectionArgs, runSuite } = require("./utils/runner")

const argv = process.argv.slice(2)
const selection = parseSelectionArgs(argv, GROUPS)
const http = createHttpClient(BASE_URL)

const ctx = {
	baseUrl: BASE_URL,
	http,
	indexName: process.env.CLIENT_TEST_INDEX || `client_test_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`,
	documentPayload: {
		content: "GraphRAG client test document.",
		metadata: { source: "client_test", topic: "graph" },
	},
	createdDocId: null,
}

const tests = [
	{
		id: 1,
		group: "indexes",
		name: "Create test index",
		run: async (context) => {
			const payload = {
				name: context.indexName,
				description: "Client test index",
				dimension: 1536,
			}
			try {
				await context.http.post("/indexes", payload)
			} catch (err) {
				if (!String(err.message).includes("Index already exists")) {
					throw err
				}
			}
			return `Index ready: ${context.indexName}`
		},
	},
	{
		id: 2,
		group: "indexes",
		name: "List indexes",
		run: async (context) => {
			const indexes = await context.http.get("/indexes")
			const names = indexes.map((idx) => idx.name)
			if (!names.includes(context.indexName)) {
				throw new Error(`Expected index ${context.indexName} in listing`)
			}
			return `${indexes.length} indexes available`
		},
	},
	{
		id: 3,
		group: "indexes",
		name: "Update index description",
		run: async (context) => {
			const payload = { description: `Updated at ${new Date().toISOString()}` }
			const updated = await context.http.put(`/indexes/${context.indexName}`, payload)
			return `Index description: ${updated.description}`
		},
	},
	{
		id: 4,
		group: "documents",
		name: "Create document",
		run: async (context) => {
			const doc = await context.http.post(`/indexes/${context.indexName}/documents`, context.documentPayload)
			context.createdDocId = doc.doc_id
			return `Document created: ${context.createdDocId}`
		},
	},
	{
		id: 5,
		group: "documents",
		name: "List documents",
		run: async (context) => {
			const docs = await context.http.get(`/indexes/${context.indexName}/documents`)
			if (!docs.find((doc) => doc.doc_id === context.createdDocId)) {
				throw new Error(`Document ${context.createdDocId} not found in index ${context.indexName}`)
			}
			return `${docs.length} document(s) found`
		},
	},
	{
		id: 6,
		group: "documents",
		name: "Update document",
		run: async (context) => {
			const payload = {
				content: `${context.documentPayload.content} (updated)`,
				metadata: { ...context.documentPayload.metadata, updated: true },
			}
			const doc = await context.http.put(`/indexes/${context.indexName}/documents/${context.createdDocId}`, payload)
			return `Document updated: ${doc.doc_id}`
		},
	},
	{
		id: 7,
		group: "search",
		name: "Search documents",
		run: async (context) => {
			const result = await context.http.post("/search", {
				index_name: context.indexName,
				query: "graph",
				keywords: ["graph"],
				top_k: 3,
			})
			logger.detail(`Search response: ${JSON.stringify(result)}`)
			if (!result.chunks?.length) {
				throw new Error("Expected search results, got none")
			}
			return `${result.chunks.length} chunk(s) retrieved`
		},
	},
	{
		id: 8,
		group: "cleanup",
		name: "Delete document",
		run: async (context) => {
			if (!context.createdDocId) {
				return "No document to delete"
			}
			await context.http.delete(`/indexes/${context.indexName}/documents/${context.createdDocId}`)
			context.createdDocId = null
			return "Document deleted"
		},
	},
	{
		id: 9,
		group: "cleanup",
		name: "Delete test index",
		run: async (context) => {
			await context.http.delete(`/indexes/${context.indexName}`)
			return "Index deleted"
		},
	},
]

runSuite({
	suiteName: "ct1-1 document search",
	tests,
	selection,
	context: ctx,
	cleanup: async () => {
		// Ensure we leave no residual index/document if cleanup tests were skipped.
		try {
			if (ctx.createdDocId) {
				await ctx.http.delete(`/indexes/${ctx.indexName}/documents/${ctx.createdDocId}`)
				logger.detail("Cleanup removed residual document")
			}
			await ctx.http.delete(`/indexes/${ctx.indexName}`)
			logger.detail("Cleanup removed residual index")
		} catch (err) {
			logger.warn(`Cleanup skipped or failed: ${err.message}`)
		}
	},
}).catch((error) => {
	logger.error(`Unexpected error: ${error.message}`)
	process.exit(1)
})
