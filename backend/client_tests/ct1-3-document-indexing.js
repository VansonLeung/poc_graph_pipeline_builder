#!/usr/bin/env node
"use strict"

/**
 * ct1-3-document-indexing
 * -----------------------
 * High-volume client test that:
 *   1. Creates multiple indexes.
 *   2. Inserts multiple long documents per index (simulated chunks).
 *   3. Searches each index to prove partitioning (no cross-contamination).
 *   4. Searches individual doc topics to confirm chunk coverage.
 *
 * Flags:
 *   --plan   : print the generated plan (indexes/documents) and exit.
 *   --keep   : skip cleanup (retain created indexes/documents).
 */

const BASE_URL = process.env.API_BASE_URL ?? "http://localhost:19800/api"
const INDEX_PREFIX = process.env.CT13_INDEX_PREFIX ?? `ct13_${Date.now().toString(36)}`
const DEFAULT_CHUNK_LENGTH = Number(process.env.CT13_CHUNK_LENGTH ?? 80)

const args = new Set(process.argv.slice(2))

const plan = buildPlan()
const context = {
  createdIndexes: [],
}

function buildPlan() {
  const suffix = Math.random().toString(36).slice(2, 6)
  return [
    {
      name: `${INDEX_PREFIX}_alpha_${suffix}`,
      keyword: "alpha partition",
      documents: [
        {
          logicalDoc: "AlphaStrategy",
          queryToken: "alpha strategy insights",
          chunkCount: 3,
          chunkLength: DEFAULT_CHUNK_LENGTH,
        },
        {
          logicalDoc: "AlphaRoadmap",
          queryToken: "alpha roadmap milestones",
          chunkCount: 2,
          chunkLength: DEFAULT_CHUNK_LENGTH,
        },
      ],
    },
    {
      name: `${INDEX_PREFIX}_beta_${suffix}`,
      keyword: "beta partition",
      documents: [
        {
          logicalDoc: "BetaResearch",
          queryToken: "beta research findings",
          chunkCount: 4,
          chunkLength: DEFAULT_CHUNK_LENGTH,
        },
        {
          logicalDoc: "BetaLaunch",
          queryToken: "beta launch checklist",
          chunkCount: 2,
          chunkLength: DEFAULT_CHUNK_LENGTH,
        },
      ],
    },
  ]
}

if (args.has("--plan")) {
  console.log("Planned indexes/documents:")
  for (const spec of plan) {
    console.log(`- ${spec.name} (keyword='${spec.keyword}')`)
    for (const doc of spec.documents) {
      console.log(`    • ${doc.logicalDoc}: ${doc.chunkCount} chunk(s), query='${doc.queryToken}'`)
    }
  }
  process.exit(0)
}

async function callApi(method, path, body) {
  const response = await fetch(`${BASE_URL}${path}`, {
    method,
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined,
  })
  const text = await response.text()
  let data = null
  if (text) {
    try {
      data = JSON.parse(text)
    } catch (err) {
      const snippet = text.length > 120 ? `${text.slice(0, 117)}...` : text
      throw new Error(`Failed to parse JSON response from ${path}: ${err.message}. Body snippet: ${snippet}`)
    }
  }
  if (!response.ok) {
    const detail = data?.detail || response.statusText
    throw new Error(`${response.status} ${response.statusText}: ${detail}`)
  }
  return data
}

async function ensureIndex(name) {
  const payload = {
    name,
    description: `ct1-3 test index ${name}`,
    dimension: 1536,
  }
  try {
    await callApi("POST", "/indexes", payload)
    context.createdIndexes.push(name)
    console.log(`Created index ${name}`)
  } catch (error) {
    if (!String(error.message).includes("Index already exists")) {
      throw error
    }
    console.log(`Index ${name} already existed; reusing`)
  }
}

function buildChunkContent(spec, chunkIndex, keyword) {
  const header = `# ${spec.logicalDoc} / chunk ${chunkIndex + 1}\n\n`
  const sentences = []
  for (let i = 0; i < spec.chunkLength; i += 1) {
    sentences.push(
      `${spec.logicalDoc} passage ${chunkIndex + 1}-${i + 1} discusses ${spec.queryToken} and ${keyword} ` +
        `while referencing chunk marker ${chunkIndex + 1}.${i + 1}.`
    )
  }
  return header + sentences.join(" ")
}

async function populateDocuments(spec) {
  for (const doc of spec.documents) {
    for (let chunkIdx = 0; chunkIdx < doc.chunkCount; chunkIdx += 1) {
      const content = buildChunkContent(doc, chunkIdx, spec.keyword)
      const metadata = {
        source: spec.name,
        logical_doc: doc.logicalDoc,
        chunk_index: chunkIdx,
        partition_keyword: spec.keyword,
        query_token: doc.queryToken,
      }
      const payload = { content, metadata }
      await callApi("POST", `/indexes/${spec.name}/documents`, payload)
    }
    console.log(`Inserted ${doc.chunkCount} chunk(s) for ${doc.logicalDoc} in ${spec.name}`)
  }
}

async function verifyPartition(spec) {
  const result = await callApi("POST", "/search", {
    index_name: spec.name,
    query: spec.keyword,
    keywords: spec.keyword.split(" "),
    top_k: 5,
  })
  if (!result.chunks?.length) {
    throw new Error(`Partition search for ${spec.name} returned no chunks`)
  }
  const contamination = result.chunks.filter((chunk) => chunk.metadata?.source !== spec.name)
  if (contamination.length) {
    throw new Error(`Partition check failed: found chunks from other indexes (${contamination.length})`)
  }
  console.log(`Partition verified for ${spec.name} (${result.chunks.length} chunk(s)).`)
}

async function verifyChunkCoverage(spec) {
  for (const doc of spec.documents) {
    const result = await callApi("POST", "/search", {
      index_name: spec.name,
      query: doc.queryToken,
      keywords: doc.queryToken.split(" "),
      top_k: doc.chunkCount + 2,
    })
    const chunks = (result.chunks ?? []).filter(
      (chunk) => chunk.metadata?.logical_doc === doc.logicalDoc
    )
    const uniqueChunks = new Set(chunks.map((chunk) => chunk.metadata?.chunk_index))
    if (uniqueChunks.size < doc.chunkCount) {
      throw new Error(
        `Chunk coverage failed for ${doc.logicalDoc} in ${spec.name}: expected ${doc.chunkCount}, got ${uniqueChunks.size}`
      )
    }
    console.log(
      `Chunk coverage verified for ${doc.logicalDoc} (${uniqueChunks.size}/${doc.chunkCount} chunk(s) surfaced).`
    )
  }
}

async function cleanup() {
  if (args.has("--keep")) {
    console.log("--keep specified; skipping cleanup.")
    return
  }
  for (const name of context.createdIndexes) {
    try {
      await callApi("DELETE", `/indexes/${name}`)
      console.log(`Deleted index ${name}`)
    } catch (error) {
      console.warn(`Failed to delete index ${name}: ${error.message}`)
    }
  }
}

async function main() {
  console.log(`API base: ${BASE_URL}`)

  for (const spec of plan) {
    await ensureIndex(spec.name)
    await populateDocuments(spec)
  }

  for (const spec of plan) {
    await verifyPartition(spec)
  }

  for (const spec of plan) {
    await verifyChunkCoverage(spec)
  }

  console.log("All ct1-3 checks passed.")
  // await cleanup()
}

main().catch((error) => {
  console.error("ct1-3-document-indexing failed:", error.message)
  process.exit(1)
})