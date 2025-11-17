#!/usr/bin/env node
"use strict"

/**
 * Utility script for cleaning a Neo4j database via the HTTP transactional API.
 *
 * Usage examples:
 *   node backend/client_tests/ct1-2-db-clean.js --status
 *   node backend/client_tests/ct1-2-db-clean.js --graph --force
 *   node backend/client_tests/ct1-2-db-clean.js --graph --indexes --constraints --force
 *   NEO4J_HTTP_URI=http://localhost:7474 node ... --graph --force
 *
 * Flags:
 *   --status         Show node/relationship/index counts without deleting anything
 *   --graph          Delete all nodes and relationships (MATCH (n) DETACH DELETE n)
 *   --indexes        Drop all indexes returned by SHOW INDEXES
 *   --constraints    Drop all constraints returned by SHOW CONSTRAINTS
 *   --dry-run        Print planned actions without executing write statements
 *   --force          Skip the confirmation prompt (required for destructive runs)
 */

const readline = require("node:readline/promises")
const { stdin: input, stdout: output } = require("node:process")

const HTTP_URI = process.env.NEO4J_HTTP_URI ?? "http://localhost:7474"
const DATABASE = process.env.NEO4J_DATABASE ?? "neo4j"
const USERNAME = process.env.NEO4J_USERNAME ?? "neo4j"
const PASSWORD = process.env.NEO4J_PASSWORD ?? "password"

const endpoint = `${HTTP_URI.replace(/\/$/, "")}/db/${DATABASE}/tx/commit`

const args = new Set(process.argv.slice(2))
const actions = {
  status: args.has("--status"),
  graph: args.has("--graph"),
  indexes: args.has("--indexes"),
  constraints: args.has("--constraints"),
  dryRun: args.has("--dry-run"),
  force: args.has("--force"),
}

if (!actions.status && !actions.graph && !actions.indexes && !actions.constraints) {
  console.log("No actions specified. Use --status or --graph/--indexes/--constraints.\nUse --help in the file header for examples.")
  process.exit(0)
}

async function runStatement(statement) {
  const res = await fetch(endpoint, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Basic ${Buffer.from(`${USERNAME}:${PASSWORD}`).toString("base64")}`,
    },
    body: JSON.stringify({ statements: [{ statement }] }),
  })
  const payload = await res.json()
  if (payload.errors?.length) {
    const [error] = payload.errors
    throw new Error(`${error.code}: ${error.message}`)
  }
  return payload.results?.[0] ?? { columns: [], data: [] }
}

async function showStatus() {
  const nodeResult = await runStatement("MATCH (n) RETURN count(n) AS nodes")
  const relResult = await runStatement("MATCH ()-[r]->() RETURN count(r) AS relationships")
  const indexes = await fetchNames("SHOW INDEXES")
  const constraints = await fetchNames("SHOW CONSTRAINTS")
  console.log("Current database status:")
  console.log(`  Nodes         : ${nodeResult.data[0]?.row?.[0] ?? 0}`)
  console.log(`  Relationships : ${relResult.data[0]?.row?.[0] ?? 0}`)
  console.log(`  Indexes       : ${indexes.length}`)
  console.log(`  Constraints   : ${constraints.length}`)
}

async function fetchNames(statement) {
  const result = await runStatement(statement)
  const nameIndex = result.columns.indexOf("name")
  if (nameIndex === -1) {
    return []
  }
  return result.data.map((row) => row.row[nameIndex])
}

async function deleteGraph() {
  if (actions.dryRun) {
    console.log("[dry-run] MATCH (n) DETACH DELETE n")
    return
  }
  console.log("Deleting all nodes and relationships...")
  await runStatement("MATCH (n) DETACH DELETE n")
  console.log("Graph cleared.")
}

async function dropIndexes() {
  const names = await fetchNames("SHOW INDEXES")
  if (names.length === 0) {
    console.log("No indexes to drop.")
    return
  }
  for (const name of names) {
    const cypher = `DROP INDEX ${wrapName(name)}`
    if (actions.dryRun) {
      console.log(`[dry-run] ${cypher}`)
    } else {
      console.log(`Dropping index ${name}...`)
      await runStatement(cypher)
    }
  }
  console.log("Indexes dropped.")
}

async function dropConstraints() {
  const names = await fetchNames("SHOW CONSTRAINTS")
  if (names.length === 0) {
    console.log("No constraints to drop.")
    return
  }
  for (const name of names) {
    const cypher = `DROP CONSTRAINT ${wrapName(name)}`
    if (actions.dryRun) {
      console.log(`[dry-run] ${cypher}`)
    } else {
      console.log(`Dropping constraint ${name}...`)
      await runStatement(cypher)
    }
  }
  console.log("Constraints dropped.")
}

function wrapName(name) {
  return name.includes("`") ? name : `\`${name}\``
}

async function confirmDanger() {
  if (actions.dryRun || actions.force) {
    return true
  }
  const rl = readline.createInterface({ input, output })
  const answer = await rl.question(
    "This will modify the Neo4j database. Type 'yes' to continue (or anything else to abort): "
  )
  rl.close()
  const ok = answer.trim().toLowerCase() === "yes"
  if (!ok) {
    console.log("Aborted.")
  }
  return ok
}

async function main() {
  console.log(`Target: ${HTTP_URI} (database=${DATABASE})`)
  if (actions.status) {
    await showStatus()
    if (!(actions.graph || actions.indexes || actions.constraints)) {
      return
    }
    console.log("")
  }

  if (actions.graph || actions.indexes || actions.constraints) {
    const confirmed = await confirmDanger()
    if (!confirmed) {
      process.exit(0)
    }
  }

  if (actions.graph) {
    await deleteGraph()
  }
  if (actions.indexes) {
    await dropIndexes()
  }
  if (actions.constraints) {
    await dropConstraints()
  }

  if (actions.graph || actions.indexes || actions.constraints) {
    console.log("\nCleanup completed. Use --status to verify the result.")
  }
}

main().catch((error) => {
  console.error("Database clean-up failed:", error.message)
  process.exit(1)
})