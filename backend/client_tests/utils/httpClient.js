"use strict"

const { logger } = require("./logger")

function createHttpClient(baseUrl, options = {}) {
  const baseHeaders = options.headers || { "Content-Type": "application/json" }

  async function request(method, path, body, requestOptions = {}) {
    const url = `${baseUrl}${path}`
    const headers = { ...baseHeaders, ...(requestOptions.headers || {}) }
    logger.detail(`HTTP ${method} ${url}`)
    const response = await fetch(url, {
      method,
      headers,
      body: body ? JSON.stringify(body) : undefined,
    })

    if (response.status === 204) {
      logger.detail(`← ${response.status} (no content)`)
      return null
    }

    const text = await response.text()
    let data = null
    if (text) {
      try {
        data = JSON.parse(text)
      } catch (err) {
        const snippet = text.length > 200 ? `${text.slice(0, 197)}...` : text
        const message = `Failed to parse JSON from ${url}: ${err.message}. Body snippet: ${snippet}`
        logger.error(message)
        throw new Error(message)
      }
    }

    if (!response.ok) {
      const detail = data?.detail || response.statusText
      const message = `${response.status} ${response.statusText}: ${detail}`
      logger.error(message)
      throw new Error(message)
    }

    logger.detail(`← ${response.status} OK`)
    return data
  }

  return {
    get: (path, opts) => request("GET", path, undefined, opts),
    post: (path, body, opts) => request("POST", path, body, opts),
    put: (path, body, opts) => request("PUT", path, body, opts),
    patch: (path, body, opts) => request("PATCH", path, body, opts),
    delete: (path, opts) => request("DELETE", path, undefined, opts),
  }
}

module.exports = { createHttpClient }
