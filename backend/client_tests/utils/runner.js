"use strict"

const { logger } = require("./logger")

function parseSelectionArgs(argv, knownGroups = []) {
  const idSet = new Set()
  const groupSet = new Set()
  let listOnly = false
  const remaining = []
  const groupLookup = new Set(knownGroups)

  const parseIds = (value) => {
    value
      .split(",")
      .map((token) => token.trim())
      .filter(Boolean)
      .forEach((token) => {
        const id = Number(token)
        if (!Number.isNaN(id)) {
          idSet.add(id)
        }
      })
  }

  for (const arg of argv) {
    if (arg === "--list") {
      listOnly = true
      continue
    }
    if (arg.startsWith("--tests=")) {
      parseIds(arg.split("=")[1])
      continue
    }
    if (arg.startsWith("--groups=")) {
      arg
        .split("=")[1]
        .split(",")
        .map((token) => token.trim())
        .filter(Boolean)
        .forEach((token) => groupSet.add(token))
      continue
    }
    if (/^\d+(,\d+)*$/.test(arg)) {
      parseIds(arg)
      continue
    }
    if (groupLookup.has(arg)) {
      groupSet.add(arg)
      continue
    }
    remaining.push(arg)
  }

  return { idSet, groupSet, listOnly, remainingArgs: remaining }
}

async function runSuite({ suiteName, tests, selection, context = {}, cleanup }) {
  if (!Array.isArray(tests) || tests.length === 0) {
    throw new Error("No tests supplied to runSuite")
  }

  if (selection.listOnly) {
    logger.heading(`${suiteName} — available tests`)
    tests.forEach((test) => logger.info(`${test.id}. [${test.group}] ${test.name}`))
    return
  }

  const selected = tests.filter((test) => {
    const idMatch = selection.idSet.size === 0 || selection.idSet.has(test.id)
    const groupMatch = selection.groupSet.size === 0 || selection.groupSet.has(test.group)
    return idMatch && groupMatch
  })

  if (selected.length === 0) {
    logger.warn("No tests matched the provided filters. Use --list to inspect available IDs/groups.")
    return
  }

  logger.heading(`${suiteName} — running ${selected.length} test(s)`)

  const suiteStart = Date.now()
  let hasFailure = false

  for (const [index, test] of selected.entries()) {
    const label = `[${index + 1}/${selected.length}] ${test.id}. [${test.group}] ${test.name}`
    logger.step(label)
    const testStart = Date.now()
    try {
      const detail = await test.run(context)
      const duration = ((Date.now() - testStart) / 1000).toFixed(2)
      logger.success(`✔ ${test.name} (${duration}s)`)
      if (detail) {
        logger.detail(detail)
      }
    } catch (error) {
      hasFailure = true
      logger.error(`✖ ${test.name} failed: ${error.message}`)
      break
    }
  }

  const totalDuration = ((Date.now() - suiteStart) / 1000).toFixed(2)
  if (!hasFailure) {
    logger.success(`Suite completed in ${totalDuration}s`)
  }

  if (typeof cleanup === "function") {
    try {
      await cleanup(context, { hasFailure })
    } catch (cleanupError) {
      logger.warn(`Cleanup encountered an issue: ${cleanupError.message}`)
    }
  }

  if (hasFailure) {
    process.exitCode = 1
  }
}

module.exports = {
  parseSelectionArgs,
  runSuite,
}
