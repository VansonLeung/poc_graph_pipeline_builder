#!/usr/bin/env node
"use strict"

/**
 * ct1-4-rag-analytics
 * --------------------
 * Stress test covering:
 *   • Massive, chunked documents with explicit metadata JSON.
 *   • Custom vector embeddings supplied per chunk.
 *   • Explicit inter-document relationships inside Neo4j.
 *   • Comprehensive RAG searches showing expected vs actual hits.
 *   • Post-ingest analytics snapshot (no cleanup to allow manual inspection).
 *
 * Flags:
 *   --plan   : Print the ingestion plan (index + documents) and exit.
 *   --list   : Provided by the shared runner to list test IDs/groups.
 */

const BASE_URL = process.env.API_BASE_URL ?? "http://localhost:19800/api"
const GROUPS = ["setup", "ingest", "graph", "search", "analytics"]
const INDEX_PREFIX = process.env.CT14_INDEX_PREFIX ?? "ct14_rag"
const VECTOR_DIMENSION = Number(process.env.CT14_VECTOR_DIMENSION ?? 1536)

const { logger } = require("./utils/logger")
const { createHttpClient } = require("./utils/httpClient")
const { parseSelectionArgs, runSuite } = require("./utils/runner")

const plan = buildPlan()
const argv = process.argv.slice(2)
const selection = parseSelectionArgs(argv, GROUPS)

if (selection.remainingArgs.includes("--plan")) {
  printPlan(plan)
  process.exit(0)
}

const http = createHttpClient(BASE_URL)
const neo4j = createNeo4jClient()

const ctx = {
  baseUrl: BASE_URL,
  http,
  plan,
  indexName: plan.indexName,
  vectorDimension: VECTOR_DIMENSION,
  docs: [],
  docHeads: new Map(),
  pendingEdges: [],
  ingestStats: { chunks: 0, characters: 0 },
  relationshipsCreated: 0,
  neo4j,
}

const tests = [
  {
    id: 1,
    group: "setup",
    name: "Create dedicated ct1-4 index",
    run: async (context) => {
      const payload = {
        name: context.indexName,
        description: "ct1-4 RAG analytics index",
        dimension: context.vectorDimension,
      }
      try {
        const created = await context.http.post("/indexes", payload)
        return `Index ready: ${created.name} (dimension=${created.dimension ?? context.vectorDimension})`
      } catch (error) {
        if (String(error.message).includes("Index already exists")) {
          return `Index reused: ${context.indexName}`
        }
        throw error
      }
    },
  },
  {
    id: 2,
    group: "ingest",
    name: "Insert massive chunked documents with metadata + embeddings",
    run: async (context) => {
      let chunkCounter = 0
      let charCounter = 0
      for (const docSpec of context.plan.documents) {
        for (let chunkIdx = 0; chunkIdx < docSpec.chunkCount; chunkIdx += 1) {
          const content = buildChunkContent(docSpec, chunkIdx)
          const metadata = buildMetadata(docSpec, chunkIdx, content.length)
          context.pendingEdges.push(
            ...buildPendingEdges(docSpec, chunkIdx)
          )
          const embedding = generateVector(`${docSpec.logicalDoc}-${chunkIdx}`, context.vectorDimension)
          const response = await context.http.post(
            `/indexes/${context.indexName}/documents`,
            {
              content,
              metadata,
              embedding,
            }
          )
          chunkCounter += 1
          charCounter += content.length
          context.docs.push({
            docId: response.doc_id,
            logicalDoc: docSpec.logicalDoc,
            chunkIndex: chunkIdx,
            metadata,
          })
          if (chunkIdx === 0) {
            context.docHeads.set(docSpec.logicalDoc, response.doc_id)
          }
        }
      }
      context.ingestStats = { chunks: chunkCounter, characters: charCounter }
      await bumpDocumentOrder(context, ["AtlasContinuum", "ConstellationRiskMemo", "PulseTelemetryLedger"])
      const approxKb = (charCounter / 1024).toFixed(1)
      return `Inserted ${chunkCounter} chunk documents totaling ~${approxKb} KB.`
    },
  },
  {
    id: 3,
    group: "graph",
    name: "Establish inter-document relationships",
    run: async (context) => {
      if (!context.pendingEdges.length) {
        return "No pending relationships declared in plan"
      }
      const edges = materializeEdges(context)
      if (!edges.length) {
        throw new Error("Unable to map logical docs to doc IDs for relationships")
      }
      const result = await context.neo4j.run(
        `UNWIND $edges AS edge
         MATCH (i:RAGIndex {name: $index})-[:HAS_DOCUMENT]->(source:RAGDocument {doc_id: edge.source})
         MATCH (i:RAGIndex {name: $index})-[:HAS_DOCUMENT]->(target:RAGDocument {doc_id: edge.target})
         MERGE (source)-[rel:RELATES_TO {rel_type: edge.rel_type}]->(target)
         ON CREATE SET rel.reason = edge.reason, rel.created_at = timestamp()
         RETURN count(rel) AS relationships`,
        { index: context.indexName, edges }
      )
      const created = result.data?.[0]?.row?.[0] ?? 0
      context.relationshipsCreated = created
      return `Created/confirmed ${created} RELATES_TO relationship(s).`
    },
  },
  {
    id: 4,
    group: "search",
    name: "Validate RAG responses (expected vs actual)",
    run: async (context) => {
      const cases = buildSearchCases(context)
      const summaries = []
      for (const scenario of cases) {
        const result = await context.http.post("/search", {
          index_name: context.indexName,
          query: scenario.query,
          keywords: scenario.keywords,
          top_k: scenario.topK,
        })
        const actualDocs = dedupeLogicalDocs(result.chunks)
        const missing = scenario.expected.filter((doc) => !actualDocs.includes(doc))
        const extras = actualDocs.filter((doc) => !scenario.expected.includes(doc))
        summaries.push({ label: scenario.label, expected: scenario.expected, actual: actualDocs, missing, extras })
        logger.detail(
          `[${scenario.label}] expected=${scenario.expected.join(", ")} | actual=${actualDocs.join(", ") || "<none>"}`
        )
        if (missing.length) {
          throw new Error(`Search scenario '${scenario.label}' missing docs: ${missing.join(", ")}`)
        }
      }
      context.searchSummaries = summaries
      return `Verified ${summaries.length} search scenario(s).`
    },
  },
  {
    id: 5,
    group: "analytics",
    name: "Capture post-ingest analytics snapshot (no cleanup)",
    run: async (context) => {
      const docStats = await context.neo4j.run(
        `MATCH (i:RAGIndex {name: $index})-[:HAS_DOCUMENT]->(d:RAGDocument)
         RETURN count(d) AS chunks`,
        { index: context.indexName }
      )
      const relStats = await context.neo4j.run(
        `MATCH (i:RAGIndex {name: $index})-[:HAS_DOCUMENT]->(:RAGDocument)-[r:RELATES_TO]->(:RAGDocument)
         RETURN count(r) AS rels`,
        { index: context.indexName }
      )
      const sampleRels = await context.neo4j.run(
        `MATCH (i:RAGIndex {name: $index})-[:HAS_DOCUMENT]->(s:RAGDocument)-[r:RELATES_TO]->(t:RAGDocument)
         RETURN s.doc_id AS source, t.doc_id AS target, r.rel_type AS rel_type, r.reason AS reason
         LIMIT 5`,
        { index: context.indexName }
      )
      const chunkCount = docStats.data?.[0]?.row?.[0] ?? 0
      const relCount = relStats.data?.[0]?.row?.[0] ?? 0
      logger.detail(`Chunk documents stored    : ${chunkCount}`)
      logger.detail(`RELATES_TO relationships  : ${relCount}`)
      if (sampleRels.data?.length) {
        logger.detail("Sample inter-document edges:")
        sampleRels.data.forEach((row) => {
          const [source, target, relType, reason] = row.row
          logger.detail(`  ${source} -[${relType}]-> ${target} (${reason})`)
        })
      }
      logger.warn("Cleanup intentionally skipped. Use ct1-2-db-clean if you need to tear down the graph later.")
      return `Analytics captured for index ${context.indexName}`
    },
  },
]

runSuite({
  suiteName: "ct1-4 RAG deep dive",
  tests,
  selection,
  context: ctx,
}).catch((error) => {
  logger.error(`Unexpected failure: ${error.message}`)
  process.exit(1)
})

// ---------------------------------------------------------------------------
// Helpers

function buildPlan() {
  const suffix = Math.random().toString(36).slice(2, 6)
  const indexName = `${INDEX_PREFIX}_${suffix}`
  const documents = [
    {
      logicalDoc: "PulseTelemetryLedger",
      title: "Pulse Telemetry Operational Ledger",
      chunkCount: 4,
      chunkLength: 200,
      baseTopic: "pulse telemetry metrics and diagnostics",
      keywordTag: "pulse telemetry metrics",
      partition: "pulse",
      topics: ["pulse", "telemetry", "metrics"],
      relationships: [{ target: "ConstellationRiskMemo", relType: "ALERTS", reason: "Diagnostics escalate to risk memo" }],
    },
    {
      logicalDoc: "ConstellationRiskMemo",
      title: "Constellation Risk Governance Memo",
      chunkCount: 3,
      chunkLength: 240,
      baseTopic: "constellation risk governance and mitigation",
      keywordTag: "constellation risk governance",
      partition: "constellation",
      topics: ["constellation", "risk", "governance"],
      relationships: [{ target: "AtlasContinuum", relType: "DEPENDS_ON", reason: "Needs atlas funding envelope" }],
    },
    {
      logicalDoc: "AtlasContinuum",
      title: "Atlas Continuum Expansion Compendium",
      chunkCount: 5,
      chunkLength: 220,
      baseTopic: "atlas expansion program logistics",
      keywordTag: "atlas expansion logistics telemetry",
      partition: "atlas",
      topics: ["atlas", "expansion", "telemetry"],
      relationships: [{ target: "PulseTelemetryLedger", relType: "FEEDS", reason: "Telemetry metrics fuel atlas commitments" }],
    },
  ]
  return { indexName, documents }
}

function printPlan(planData) {
  logger.heading("ct1-4 ingestion plan")
  logger.info(`Index: ${planData.indexName}`)
  planData.documents.forEach((doc) => {
    logger.info(
      `- ${doc.logicalDoc}: ${doc.chunkCount} chunk(s), topics=${doc.topics.join(", ")}, relationships=${doc.relationships
        .map((rel) => `${rel.relType}->${rel.target}`)
        .join(" | ")}`
    )
  })
}

async function bumpDocumentOrder(context, logicalDocOrder) {
  for (const logicalDoc of logicalDocOrder) {
    const headChunk = context.docs.find((doc) => doc.logicalDoc === logicalDoc && doc.chunkIndex === 0)
    if (!headChunk) {
      continue
    }
    const metadata = { ...headChunk.metadata, touch_revision: new Date().toISOString() }
    await context.http.put(
      `/indexes/${context.indexName}/documents/${headChunk.docId}`,
      { metadata }
    )
    headChunk.metadata = metadata
  }
}

function buildChunkContent(docSpec, chunkIdx) {
  const header = `# ${docSpec.title} | chunk ${chunkIdx + 1}/${docSpec.chunkCount}\n\n`
  const sentences = []
  for (let i = 0; i < docSpec.chunkLength; i += 1) {
    sentences.push(
      `Section ${chunkIdx + 1}.${i + 1} elaborates on ${docSpec.baseTopic}, tying ${docSpec.keywordTag} narratives ` +
        `to chunk marker ${chunkIdx + 1}-${i + 1} while cross-referencing ${docSpec.topics.join("/")}.`
    )
  }
  return header + sentences.join(" ")
}

function buildMetadata(docSpec, chunkIdx, contentLength) {
  return {
    logical_doc: docSpec.logicalDoc,
    title: docSpec.title,
    chunk_index: chunkIdx,
    chunk_count: docSpec.chunkCount,
    chunk_label: `chunk-${chunkIdx + 1}-of-${docSpec.chunkCount}`,
    chunk_length: contentLength,
    chunk_strategy: "synthetic deterministic chunking",
    partition: docSpec.partition,
    topics: docSpec.topics,
    keywords: docSpec.keywordTag.split(" "),
    mass_document: true,
    metadata_version: "ct1-4",
    json_struct: {
      approvals: ["nav", "ops", chunkIdx % 2 === 0 ? "risk" : "finance"],
      scoring: {
        relevance: Number((0.82 + chunkIdx * 0.01).toFixed(3)),
        confidence: Number((0.9 - chunkIdx * 0.015).toFixed(3)),
      },
      references: docSpec.relationships.map((rel) => ({ target: rel.target, relation: rel.relType })),
    },
  }
}

function buildPendingEdges(docSpec, chunkIdx) {
  if (chunkIdx !== 0 || !Array.isArray(docSpec.relationships)) {
    return []
  }
  return docSpec.relationships.map((rel) => ({
    sourceLogicalDoc: docSpec.logicalDoc,
    targetLogicalDoc: rel.target,
    relType: rel.relType,
    reason: rel.reason,
  }))
}

function materializeEdges(context) {
  const edges = []
  for (const edge of context.pendingEdges) {
    const sourceDocId = context.docHeads.get(edge.sourceLogicalDoc)
    const targetDocId = context.docHeads.get(edge.targetLogicalDoc)
    if (!sourceDocId || !targetDocId) {
      logger.warn(
        `Skipped edge ${edge.sourceLogicalDoc} -> ${edge.targetLogicalDoc} (missing doc head).`
      )
      continue
    }
    edges.push({
      source: sourceDocId,
      target: targetDocId,
      rel_type: edge.relType,
      reason: edge.reason,
    })
  }
  return edges
}

function buildSearchCases(context) {
  return [
    {
      label: "Atlas + telemetry synergy",
      query: "Atlas Continuum expansion plan consumes pulse telemetry metrics",
      keywords: ["atlas", "continuum", "telemetry"],
      topK: 6,
      expected: ["AtlasContinuum"],
    },
    {
      label: "Risk memo escalation",
      query: "constellation risk memo referencing atlas funding",
      keywords: ["risk", "constellation", "atlas"],
      topK: 6,
      expected: ["ConstellationRiskMemo"],
    },
    {
      label: "Telemetry alerts",
      query: "pulse telemetry diagnostics that alert constellation governance",
      keywords: ["telemetry", "alerts", "governance"],
      topK: 6,
      expected: ["PulseTelemetryLedger"],
    },
  ]
}

function dedupeLogicalDocs(chunks = []) {
  const seen = new Set()
  for (const chunk of chunks) {
    const logicalDoc = chunk?.metadata?.logical_doc
    if (logicalDoc) {
      seen.add(logicalDoc)
    }
  }
  return Array.from(seen)
}

function createNeo4jClient() {
  const uri = process.env.NEO4J_HTTP_URI ?? "http://localhost:7474"
  const database = process.env.NEO4J_DATABASE ?? "neo4j"
  const username = process.env.NEO4J_USERNAME ?? "neo4j"
  const password = process.env.NEO4J_PASSWORD ?? "password"
  const endpoint = `${uri.replace(/\/$/, "")}/db/${database}/tx/commit`
  const authHeader = `Basic ${Buffer.from(`${username}:${password}`).toString("base64")}`

  return {
    async run(statement, parameters = {}) {
      const response = await fetch(endpoint, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: authHeader,
        },
        body: JSON.stringify({ statements: [{ statement, parameters }] }),
      })
      const payload = await response.json()
      if (payload.errors?.length) {
        const [error] = payload.errors
        throw new Error(`${error.code}: ${error.message}`)
      }
      return payload.results?.[0] ?? { columns: [], data: [] }
    },
  }
}

function generateVector(seedText, dimension) {
  const seed = seedText.split("").reduce((acc, char) => acc + char.charCodeAt(0), 0)
  const random = mulberry32(seed)
  const vector = []
  for (let i = 0; i < dimension; i += 1) {
    vector.push(Number((random() * 2 - 1).toFixed(6)))
  }
  return vector
}

function mulberry32(a) {
  let t = a >>> 0
  return function () {
    t += 0x6d2b79f5
    t = Math.imul(t ^ (t >>> 15), t | 1)
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61)
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
}
